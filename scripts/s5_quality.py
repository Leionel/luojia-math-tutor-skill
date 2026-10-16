"""Offline S5 report contracts. No app imports, network clients or model execution."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

METRICS = (
    'task_completed', 'mathematically_correct', 'appropriate_abstention',
    'inappropriate_abstention', 'checker_coverage', 'verification_overclaim',
    'first_error_localized', 'counterexample_valid', 'routing_valid',
    'tool_decision_valid', 'action_valid', 'help_violation', 'false_success',
)
VIOLATIONS = {'verification_overclaim', 'help_violation', 'false_success'}
FAILURES = {
    'INPUT_AMBIGUOUS', 'ROUTE_WRONG', 'CONTEXT_MISSING', 'CONTEXT_STALE',
    'CONTEXT_TRUNCATED', 'TOOL_MISSED', 'TOOL_UNNECESSARY', 'TOOL_ARGS',
    'TOOL_FAILED', 'MATH_CALCULATION', 'ASSUMPTION_MISSING', 'THEOREM_MISAPPLIED',
    'LOGIC_GAP', 'COUNTEREXAMPLE_INVALID', 'VERIFICATION_OVERCLAIM',
    'ANSWER_LEAKAGE', 'EVIDENCE_CONFLICT', 'ACTION_INVALID', 'OUTCOME_UNLINKED',
    'PROTOCOL', 'DELIVERY', 'ORACLE_UNKNOWN', 'BUDGET_STOP', 'PROVIDER_UNSUPPORTED',
}
SOURCES = {'fixed_fixture', 'component_check', 'recorded_run'}
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z')
SHA = re.compile(r'[a-f0-9]{64}\Z')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    if path.stat().st_size > 2_000_000:
        raise ValueError('input exceeds 2MB limit')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON field')
            result[key] = value
        return result
    value = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    if not isinstance(value, dict):
        raise ValueError('input must be a JSON object')
    return value


def valid_id(value) -> bool:
    return isinstance(value, str) and ID.fullmatch(value) is not None


def valid_sha(value) -> bool:
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def validate_manifest(manifest: dict) -> list[dict]:
    if manifest.get('version') != 's5-manifest-v1':
        raise ValueError('unsupported manifest version')
    if manifest.get('split') not in {'development', 'runner_fixture'}:
        raise ValueError('confirmation is not enabled in S5.1')
    cases = manifest.get('cases')
    if not isinstance(cases, list) or not cases or len(cases) > 100:
        raise ValueError('manifest needs 1..100 cases')
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or not valid_id(case.get('id')) or case['id'] in seen:
            raise ValueError('invalid or duplicate case ID')
        seen.add(case['id'])
        if case.get('kind') not in {'single_run', 'episode'}:
            raise ValueError('unknown case kind')
        runs = case.get('planned_runs')
        if type(runs) is not int or not 1 <= runs <= 10 or (case['kind'] == 'single_run' and runs != 1):
            raise ValueError('invalid planned run count')
        if not valid_sha(case.get('input_sha256')) or not valid_sha(case.get('rubric_sha256')):
            raise ValueError('input and rubric hashes required')
        applicable = case.get('applicable')
        if not isinstance(applicable, dict) or set(applicable) != set(METRICS):
            raise ValueError('fixed metric applicability required')
        if any(type(v) is not bool for v in applicable.values()) or not applicable['task_completed']:
            raise ValueError('invalid applicability')
        if case.get('gold_status') not in {'pending', 'author_reviewed_only', 'independently_reviewed', 'synthetic_fixture'}:
            raise ValueError('unknown gold status')
        stage_ids = case.get('required_stage_ids')
        if stage_ids is not None and (case['kind'] != 'episode' or manifest['split'] != 'runner_fixture' or not isinstance(stage_ids,list) or not 1<=len(stage_ids)<=30 or any(not valid_id(x) for x in stage_ids) or len(set(stage_ids))!=len(stage_ids)):
            raise ValueError('invalid episode stage contract')
        expectation = case.get('runtime_expectation')
        if expectation is not None:
            if manifest['split'] != 'runner_fixture' or not isinstance(expectation, dict) or set(expectation) != {
                    'is_correct','eligible_learning_evidence','origin','mastery_writes','mistake_writes'}:
                raise ValueError('invalid runtime expectation')
            if expectation['is_correct'] is not None and type(expectation['is_correct']) is not bool:
                raise ValueError('invalid expected verdict')
            if type(expectation['eligible_learning_evidence']) is not bool or not valid_id(expectation['origin']):
                raise ValueError('invalid expected eligibility/origin')
            if any(type(expectation[k]) is not int or expectation[k] < 0 for k in ('mastery_writes','mistake_writes')):
                raise ValueError('invalid expected write count')
        if case['gold_status'] == 'synthetic_fixture' and manifest['split'] != 'runner_fixture':
            raise ValueError('synthetic gold cannot enter development quality cases')
    return cases


def index_records(envelope: dict | None, version: str, manifest_hash: str, allowed: set[str]) -> dict:
    if envelope is None:
        return {}
    if envelope.get('version') != version or envelope.get('manifest_sha256') != manifest_hash:
        raise ValueError('record version or manifest hash mismatch')
    records = envelope.get('records')
    if not isinstance(records, list):
        raise ValueError('records must be a list')
    result = {}
    for row in records:
        if not isinstance(row, dict) or row.get('case_id') not in allowed or row['case_id'] in result:
            raise ValueError('unexpected or duplicate record ID')
        result[row['case_id']] = row
    return result


def summarize(rows: list[dict], source: str) -> dict:
    cohort = [r for r in rows if r['evidence_source'] == source and r['run_status'] != 'not_run']
    output = {}
    for metric in METRICS:
        applicable = [r for r in cohort if r['applicable'][metric]]
        scored = [r for r in applicable if r['ratings'][metric] is not None]
        numerator = sum(r['ratings'][metric] is True for r in scored)
        output[metric] = {
            'numerator': numerator, 'denominator': len(applicable),
            'scored': len(scored), 'unscored': len(applicable) - len(scored),
            'rate': numerator / len(applicable) if applicable and len(scored) == len(applicable) else None,
        }
    return output



def runtime_facts(record: dict | None, source: str | None) -> dict | None:
    facts = record.get('runtime_facts') if record else None
    if facts is None:
        return None
    keys = {'isolated_initial_state', 'metadata_restored_equal', 'input_bound',
            'execution_status', 'origin', 'scope', 'is_correct', 'eligible_learning_evidence',
            'mastery_writes', 'mistake_writes', 'route'}
    if source != 'fixed_fixture' or not isinstance(facts, dict) or set(facts) != keys:
        raise ValueError('runtime facts only support the declared fixed fixture schema')
    for key in ('isolated_initial_state', 'metadata_restored_equal', 'input_bound', 'eligible_learning_evidence'):
        if type(facts[key]) is not bool:
            raise ValueError('invalid runtime boolean')
    if facts['is_correct'] is not None and type(facts['is_correct']) is not bool:
        raise ValueError('invalid runtime verdict')
    for key in ('mastery_writes', 'mistake_writes'):
        if type(facts[key]) is not int or not 0 <= facts[key] <= 100:
            raise ValueError('invalid runtime write count')
    for key in ('execution_status', 'origin', 'scope', 'route'):
        if not valid_id(facts[key]):
            raise ValueError('unsafe runtime label')
    return dict(facts)



def episode_facts(record: dict | None, source: str | None) -> dict | None:
    facts=record.get('episode_facts') if record else None
    if facts is None:return None
    keys={'isolated_initial_state','actual_runs','run_refs','turn_input_hashes','stages','confirmation_origin','content_review'}
    if source!='fixed_fixture' or not isinstance(facts,dict) or set(facts)!=keys:
        raise ValueError('invalid episode observation schema')
    if type(facts['isolated_initial_state']) is not bool or type(facts['actual_runs']) is not int or not 1<=facts['actual_runs']<=10:
        raise ValueError('invalid episode state/run count')
    if not isinstance(facts['run_refs'],list) or len(facts['run_refs'])!=facts['actual_runs'] or any(not valid_id(x) for x in facts['run_refs']):
        raise ValueError('invalid episode run references')
    if len(set(facts['run_refs']))!=len(facts['run_refs']):raise ValueError('duplicate episode run reference')
    if not isinstance(facts['turn_input_hashes'],list) or len(facts['turn_input_hashes'])!=facts['actual_runs'] or any(not valid_sha(x) for x in facts['turn_input_hashes']):
        raise ValueError('invalid turn input hashes')
    stages=facts['stages']
    if not isinstance(stages,list) or not 1<=len(stages)<=30:raise ValueError('episode stages required')
    for stage in stages:
        if not isinstance(stage,dict) or set(stage)!={'id','passed','http_status'} or not valid_id(stage['id']) or type(stage['passed']) is not bool:
            raise ValueError('invalid stage observation')
        if type(stage['http_status']) is not int or not 100<=stage['http_status']<=599:raise ValueError('invalid stage HTTP status')
    if len({x['id'] for x in stages})!=len(stages):raise ValueError('duplicate stage observation')
    if facts['confirmation_origin']!='synthetic_user_http_request' or facts['content_review']!='pending':
        raise ValueError('synthetic user cannot certify content quality')
    return {**facts,'stages':[dict(x) for x in stages]}


def build_report(manifest: dict, manifest_hash: str, observations: dict | None = None,
                 reviews: dict | None = None, *, dry_run: bool = False) -> dict:
    cases = validate_manifest(manifest)
    allowed = {c['id'] for c in cases}
    observed = index_records(observations, 's5-observations-v1', manifest_hash, allowed)
    reviewed = index_records(reviews, 's5-reviews-v1', manifest_hash, allowed)
    provenance = observations.get('capture_provenance') if observations else None
    if provenance is not None:
        keys = {'kind', 'network', 'database', 'model_response', 'persistence', 'source_sha256'}
        if not isinstance(provenance, dict) or set(provenance) != keys or provenance['kind'] not in {'owned_offline_graph_fixture','owned_offline_episode_fixture'}:
            raise ValueError('unsupported capture provenance')
        persistence={'owned_offline_graph_fixture':'graph metadata projection saved by harness',
                     'owned_offline_episode_fixture':'asgi_stream_saved_by_orchestrator'}[provenance['kind']]
        if (provenance['network'], provenance['database'], provenance['model_response'], provenance['persistence']) != (
            'denied','fresh_temp_per_case','fixed',persistence):
            raise ValueError('invalid runtime provenance labels')
        hashes = provenance['source_sha256']
        if not isinstance(hashes, dict) or not hashes or any(
                not isinstance(path, str) or not re.fullmatch(r'apps/api/app/[A-Za-z0-9_/-]+\.py', path) or not valid_sha(h)
                for path, h in hashes.items()):
            raise ValueError('invalid captured source hashes')
    if dry_run and (observations is not None or reviews is not None):
        raise ValueError('dry-run cannot consume observations or ratings')
    rows = []
    for case in cases:
        obs = observed.get(case['id'])
        review = reviewed.get(case['id'])
        status = 'not_run' if obs is None else obs.get('run_status')
        if status not in {'completed', 'failed', 'not_run'}:
            raise ValueError('invalid run status')
        if obs is not None and obs.get('input_sha256') != case['input_sha256']:
            raise ValueError('observation input hash mismatch')
        source = None if obs is None or status == 'not_run' else obs.get('evidence_source')
        if source is not None and source not in SOURCES:
            raise ValueError('unknown evidence source')
        if status != 'not_run' and source is None:
            raise ValueError('executed record needs an evidence source')
        if source == 'recorded_run' and manifest['split'] != 'development':
            raise ValueError('recorded runs cannot enter fixture report')
        if status != 'not_run' and (not valid_sha(obs.get('response_sha256')) or not valid_id(obs.get('run_ref'))):
            raise ValueError('executed record needs response hash and safe run reference')
        reason = 'dry_run' if dry_run else 'observation_not_supplied'
        if obs is not None and status == 'not_run':
            reason = obs.get('not_run_reason')
            if reason not in {'budget_stop', 'gold_pending', 'provider_unsupported', 'cancelled', 'fixture_not_supplied'}:
                raise ValueError('explicit not-run reason required')
        ratings = {m: None for m in METRICS}
        review_status = 'pending'
        primary_failure = None
        if review is not None:
            if obs is None or status == 'not_run':
                raise ValueError('cannot score an unexecuted case')
            if review.get('response_sha256') != obs['response_sha256'] or review.get('rubric_sha256') != case['rubric_sha256']:
                raise ValueError('review response or rubric hash mismatch')
            role = review.get('reviewer_role')
            if role not in {'author', 'independent', 'synthetic_fixture'} or not valid_id(review.get('reviewer_id')):
                raise ValueError('reviewer provenance required')
            if (source == 'fixed_fixture') != (role == 'synthetic_fixture'):
                raise ValueError('fixture ratings must remain synthetic')
            if source != 'fixed_fixture' and case['gold_status'] in {'pending', 'synthetic_fixture'}:
                raise ValueError('quality rubric is not reviewed')
            scores = review.get('ratings')
            if not isinstance(scores, dict) or set(scores) != set(METRICS):
                raise ValueError('complete rating schema required')
            for metric, value in scores.items():
                if value is not None and type(value) is not bool:
                    raise ValueError('rating must be boolean or pending')
                if not case['applicable'][metric] and value is not None:
                    raise ValueError('N/A metric cannot be scored')
            if scores['appropriate_abstention'] is True and scores['inappropriate_abstention'] is True:
                raise ValueError('conflicting abstention ratings')
            primary_failure = review.get('primary_failure')
            if primary_failure is not None and primary_failure not in FAILURES:
                raise ValueError('unknown primary failure')
            ratings = dict(scores)
            review_status = role
        rows.append({
            'case_id': case['id'], 'kind': case['kind'], 'applicable': case['applicable'],
            'gold_status': case['gold_status'], 'run_status': status, 'evidence_source': source,
            'input_sha256': case['input_sha256'], 'rubric_sha256': case['rubric_sha256'],
            'response_sha256': obs.get('response_sha256') if obs and status != 'not_run' else None,
            'run_ref': obs.get('run_ref') if obs and status != 'not_run' else None,
            'not_run_reason': reason if status == 'not_run' else None,
            'review_status': review_status, 'ratings': ratings, 'primary_failure': primary_failure,
            'runtime_facts': runtime_facts(obs, source),
            'runtime_expectation': case.get('runtime_expectation'),
            'episode_facts': episode_facts(obs,source),'required_stage_ids':case.get('required_stage_ids'),
            'planned_runs':case['planned_runs'],
        })
    if any(r['runtime_facts'] or r['episode_facts'] for r in rows) and provenance is None:
        raise ValueError('runtime facts require captured source provenance')
    runtime_violations = []
    for row in rows:
        facts = row['runtime_facts']
        if facts is None:
            continue
        reasons = [key for key in ('isolated_initial_state', 'metadata_restored_equal', 'input_bound') if not facts[key]]
        if facts['eligible_learning_evidence'] and (facts['origin'] != 'student_claim' or facts['is_correct'] is None):
            reasons.append('eligibility_without_student_verdict')
        if not facts['eligible_learning_evidence'] and (facts['mastery_writes'] or facts['mistake_writes']):
            reasons.append('ineligible_learning_write')
        expectation = row['runtime_expectation']
        if expectation:
            reasons += ['expectation_mismatch:' + key for key,value in expectation.items() if facts[key] != value]
        if reasons:
            runtime_violations.append({'case_id': row['case_id'], 'reasons': reasons})
    episode_violations=[]
    for row in rows:
        facts=row['episode_facts']
        if facts is None:continue
        if row['kind']!='episode' or provenance['kind']!='owned_offline_episode_fixture':
            raise ValueError('episode source does not match record kind')
        reasons=[]
        if not facts['isolated_initial_state']:reasons.append('initial_state_not_clean')
        if facts['actual_runs']!=row['planned_runs']:reasons.append('run_count_mismatch')
        if [s['id'] for s in facts['stages']]!=row['required_stage_ids']:reasons.append('stage_sequence_mismatch')
        reasons += ['stage_failed:'+s['id'] for s in facts['stages'] if not s['passed']]
        if reasons:episode_violations.append({'case_id':row['case_id'],'reasons':reasons})
    executed = sum(r['run_status'] != 'not_run' for r in rows)
    complete = observations is None or set(observed) == allowed
    missing = sorted(allowed - set(observed)) if observations is not None else []
    violations = [r['case_id'] for r in rows if any(r['ratings'][m] is True for m in VIOLATIONS)]
    clusters = {}
    for row in rows:
        code = row['primary_failure']
        if code:
            clusters.setdefault(code, []).append({'case_id': row['case_id'], 'evidence_source': row['evidence_source']})
    return {
        'report_version': 's5-quality-v1', 'scope': 'offline_report_contracts',
        'mode': 'dry_run' if dry_run else 'offline_replay', 'split': manifest['split'],
        'manifest_sha256': manifest_hash, 'planned_cases': len(cases), 'executed_cases': executed,
        'execution_coverage': executed / len(cases), 'report_complete': complete,
        'missing_observation_ids': missing, 'cases': rows,
        'not_run_cases': [r['case_id'] for r in rows if r['run_status'] == 'not_run'],
        'quality': summarize(rows, 'recorded_run'),
        'component_check': summarize(rows, 'component_check'),
        'fixture_contract': summarize(rows, 'fixed_fixture'),
        'violating_cases': violations, 'failure_clusters': clusters,
        'acceptance': 'blocked_by_violation' if any(r['case_id'] in violations and r['evidence_source'] == 'recorded_run' for r in rows) else 'pending_quality_review',
        'runtime_violations': runtime_violations,
        'episode_violations':episode_violations,
        'episode_contract_status':('failed' if episode_violations else 'passed_content_pending') if any(r['episode_facts'] for r in rows) else 'not_run',
        'runtime_contract_status': ('failed' if runtime_violations else 'passed') if any(r['runtime_facts'] for r in rows) else 'not_run',
        'fixture_violating_cases': [r['case_id'] for r in rows if r['case_id'] in violations and r['evidence_source'] == 'fixed_fixture'],
        'confirmation_status': 'pending_second_reviewer_and_sealed_cases',
        'run_provenance': observations.get('capture_provenance') if observations else None,
        'usage': {'requests_sent_by_runner': 0, 'tokens': None, 'cost': None},
        'limitations': ['Offline replay does not run models or prove teaching outcomes.',
                        'Fixture and component results are excluded from model quality.',
                        'Reviewer identity/role is declared by the supplied review file, not authenticated.',
                        'Pending scores remain in the fixed denominator; no aggregate pass score.'],
    }


def render_markdown(report: dict) -> str:
    """Interpretation from validated observations, never invented model/teaching gains."""
    rows = report['cases']
    recorded = [r for r in rows if r['evidence_source'] == 'recorded_run' and r['run_status'] != 'not_run']
    fixed = [r for r in rows if r['evidence_source'] == 'fixed_fixture' and r['run_status'] != 'not_run']
    facts = [r for r in rows if r['runtime_facts']]
    lines = [
        '# S5 离线诊断报告', '',
        '## 可以得出的结论', '',
        f"计划 {report['planned_cases']} 个 case，执行观察 {report['executed_cases']} 个，记录完整性：{'完整' if report['report_complete'] else '缺失'}。执行覆盖不等于任务完成率。",
        f"真实执行记录回放 {len(recorded)} 个；固定响应 fixture {len(fixed)} 个。fixture 单列，不进入模型质量分母。",
    ]
    if not recorded:
        lines += ['', '**目前不能判断真实模型的数学正确率、教学效果或改进幅度。** 缺少已运行且已复核的真实模型样本，不能用 fixture 通过替代。']
    if facts:
        lines += ['', f"实际编译图/固定worker采集 {len(facts)} 个公开合成请求，状态合同：{report['runtime_contract_status']}。每个 case 从独立临时库开始；模型回复固定，检索被隔离。保存检查仅覆盖 harness 保存的图状态投影，不替代真实 HTTP/SSE 或多轮行为验收。", '',
                  '| case | 核验状态 | 正误 | 学习资格 | mastery / mistake写入 | 保存恢复一致 |',
                  '|---|---|---|---|---|---|']
        for row in facts:
            f = row['runtime_facts']
            verdict = '未确定' if f['is_correct'] is None else ('正确候选' if f['is_correct'] else '错误候选')
            lines.append(f"| {row['case_id']} | {f['execution_status']} / {f['origin']} | {verdict} | {f['eligible_learning_evidence']} | {f['mastery_writes']} / {f['mistake_writes']} | {f['metadata_restored_equal']} |")
        lines += ['', '错误候选允许更新普通掌握度估计，并不意味着给学生加分；参考计算与范围不足不应写入学习证据。rejected/unknown 表示未确定，不表示学生答案错误。']
    episodes=[r for r in rows if r['episode_facts']]
    if episodes:
        lines += ['','## 两条完整流程的工程证据','',f"流程合同：{report['episode_contract_status']}。固定模型与合成Principal只证明ASGI/状态衔接，不证明真实认证、真实模型内容或真人独立表现。",'',
                  '| episode | 阶段 | 观察HTTP状态 | 工程期望成立 |','|---|---|---|---|']
        for row in episodes:
            for stage in row['episode_facts']['stages']:
                lines.append(f"| {row['case_id']} | {stage['id']} | {stage['http_status']} | {stage['passed']} |")
        lines += ['','409/404可能是正确拦截，不能把所有非200都算失败。普通矩阵聊天的输入绑定来自实际保存的用户消息；该分支未请求自动单步核验，不声称checker核对过矩阵候选。']
    if report.get('content_review'):
        lines += ['','## 内容准备与审核状态','',f"已准备{report['content_review']['prepared_cases']}道公开development题的独立解答和逐题rubric；状态agent_prepared_only。真人作者审核和独立二审仍pending。精确Fraction检查只支撑算术witness，不是回答语义评分、形式证明或teacher gold。"]
    lines += ['', '## 数学与行为评分的分母', '',
              '| 指标 | true数量 / 适用且已执行 | 已评分 | 未评分 | 比例 |',
              '|---|---|---|---|---|']
    for key in ('task_completed','mathematically_correct','appropriate_abstention','inappropriate_abstention','checker_coverage','verification_overclaim','help_violation','false_success'):
        m = report['quality'][key]
        rate = '未确定' if m['rate'] is None else f"{m['rate']:.1%}"
        lines.append(f"| {key} | {m['numerator']} / {m['denominator']} | {m['scored']} | {m['unscored']} | {rate} |")
    lines += ['', '适用性在 manifest 中预先固定。未评分保留在分母，分数不齐时比例为空；未运行保留在计划任务表。弃权不能自动算正确，核验越界/帮助泄露/无依据成功独立列出。当前核验越界为 case 级指标，尚未采集 claim 级发生次数；两者不可混用。', '',
              '## 逐题待补证据', '', '| case | 执行 | gold | 评分来源 | 下一项证据 |', '|---|---|---|---|---|']
    for row in rows:
        reason = ('先复核逐题解答与rubric' if row['gold_status'] == 'pending' else
                  '补执行观察' if row['run_status'] == 'not_run' else
                  'fixture只用于工程合同' if row['evidence_source'] == 'fixed_fixture' else
                  '补适用项评分' if any(row['ratings'][k] is None and row['applicable'][k] for k in METRICS) else
                  '作者评分待独立复核' if row['review_status'] == 'author' else '保留证据，核对声明的复核来源')
        lines.append(f"| {row['case_id']} | {row['run_status']} | {row['gold_status']} | {row['review_status']} | {reason} |")
    lines += ['', '## 失败归因与启动条件', '']
    actual_clusters = {k:[x for x in values if x['evidence_source'] == 'recorded_run'] for k,values in report['failure_clusters'].items()}
    actual_clusters = {k:v for k,v in actual_clusters.items() if v}
    if actual_clusters:
        for code, items in sorted(actual_clusters.items()):
            lines.append(f"- {code}：{len(items)} 个真实回放case；归因来自提供的人工评分，尚需同初始状态的单因素对照。")
    else:
        lines += ['尚无人工复核的真实模型失败簇。合成fixture中故意注入的违规不代表当前产品缺陷；此时不能根据标签数量决定增加ProofState或更多Agent。']
    lines += ['', '1. 先补8道development草案的独立解答、域/量词、必要与禁止结论；作者复核完成才接受质量评分。',
              '2. 补采集adapter的路由、引用、调用和动作证据，验证2条完整流程；runtime fixture这里只覆盖4类单请求状态。',
              '3. 明确供应商准入和费用上限后再运行小规模真实模型；保存输入、答复、版本和评分依据摘要。',
              '4. 对确认的失败，从相同初始状态分别补必要context或修正tool结果，再决定局部修复；不能只看最后一次成功。',
              '5. 4道独立确认候选须由真实复核者审核并封存；用于调优后转为dev，不能继续称未见题。', '',
              '## 证据边界与溯源', '',
              f"Manifest SHA256：`{report['manifest_sha256']}`。当前报告工具HEAD：`{report.get('report_builder_sha') or 'unknown'}`；该快照不自动等于被回放运行的源码。",
              '实际fixture采集源码摘要在run_provenance中；手工导入recorded_run的源版本若未提供，保持未知。reviewer身份/角色由文件声明，工具没有认证其真实身份。',
              'E0协议通过、fixture工程通过、人工数学评分、真实模型执行和真人学习收益是不同证据，不相加成一个准确率。当前报告不推断跨题型泛化或教学收益。', '']
    return '\n'.join(lines)
