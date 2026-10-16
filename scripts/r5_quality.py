"""R5 contracts reuse S5 JSON/hash tools and existing policy comparison.

No keyword score or fixture response is a real-model quality observation.
"""
import hashlib
from pathlib import Path
import sys

from s5_quality import load_json

ROOT=Path(__file__).resolve().parents[1]
METRICS=('mathematical_correctness','valid_step_misjudgment','error_localization',
         'condition_awareness','unknown_appropriateness','feedback_relevance','evidence_consistency')


def sha(value):
    import json
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def load_cases(path):
    data=load_json(path)
    if data.get('version')!='r5-cases-v1' or data.get('review_status')!='agent_prepared_only':raise ValueError('unsupported material status/version')
    cases=data['cases']
    if not 24<=len(cases)<=30 or len({c['id'] for c in cases})!=len(cases):raise ValueError('invalid fixed case denominator')
    for c in cases:
        if c['split']!='development' or c['input_sha256']!=hashlib.sha256(c['prompt'].encode()).hexdigest() or c['rubric_sha256']!=sha(c['rubric']):raise ValueError('case binding mismatch')
        if c['rubric']['independent_review']!='pending' or c['rubric']['status']!='agent_prepared_only':raise ValueError('cannot manufacture reviewed gold')
        if set(c['applicability'])!=set(METRICS) or any(type(v) is not bool for v in c['applicability'].values()):raise ValueError('invalid metric applicability')
    holdout=data['holdout_register']
    if not holdout['public_content_is_not_holdout'] or any(x['prompt'] is not None or x['rubric'] is not None for x in holdout['slots']):raise ValueError('public drafts are not sealed holdout')
    return data


def validate_capture(material, records):
    expected={(c['id'],a) for c in material['cases'] for a in ('D0','D1','D2')}
    seen=set()
    for row in records:
        key=(row['case_id'],row['arm'])
        if key in seen or key not in expected:raise ValueError('duplicate or unexpected run')
        seen.add(key)
        c=next(c for c in material['cases'] if c['id']==row['case_id'])
        if row['input_sha256']!=c['input_sha256'] or row['rubric_sha256']!=c['rubric_sha256']:raise ValueError('observation bound to wrong material')
        if row['evidence_source']!='fixed_fixture':raise ValueError('this capture cannot admit real model observations')
        if row['status'] not in ('completed','failed','not_run'):raise ValueError('unknown run state')
        if row['status']=='completed' and not row.get('response_text'):raise ValueError('empty completion')
    return expected-seen


def metric_summary(material, records, synthetic_reviews=()):
    """Synthetic labels test aggregation only; never enter a real quality rate."""
    validate_capture(material,records)
    lookup={(r['case_id'],r['arm']):r for r in records}
    reviews={}
    for review in synthetic_reviews:
        key=(review['case_id'],review['arm'])
        if key in reviews or key not in lookup:raise ValueError('duplicate/unexpected synthetic review')
        row=lookup[key]
        if review.get('kind')!='synthetic_report_test' or review['response_sha256']!=row['response_sha256'] or review['rubric_sha256']!=row['rubric_sha256']:raise ValueError('invalid synthetic review binding')
        if row['status']!='completed':raise ValueError('cannot score an uncompleted fixture')
        case=next(c for c in material['cases'] if c['id']==row['case_id'])
        for metric,value in review['metrics'].items():
            if metric not in METRICS or type(value) not in (bool,type(None)) or value is not None and not case['applicability'][metric]:raise ValueError('invalid metric/N/A value')
        reviews[key]=review
    result={}
    for arm in ('D0','D1','D2'):
        result[arm]={}
        for metric in METRICS:
            applicable=[c for c in material['cases'] if c['applicability'][metric]]
            vals=[reviews.get((c['id'],arm),{}).get('metrics',{}).get(metric) for c in applicable]
            scored=[v for v in vals if v is not None]
            result[arm][metric]={'planned':len(applicable),'completed':sum(lookup.get((c['id'],arm),{}).get('status')=='completed' for c in applicable),
                'failed':sum(lookup.get((c['id'],arm),{}).get('status')=='failed' for c in applicable),
                'synthetic_scored':len(scored),'synthetic_true':sum(scored),'unscored':len(applicable)-len(scored),
                'synthetic_rate':sum(scored)/len(applicable) if applicable and len(scored)==len(applicable) else None,
                'real_model_rate':None}
    return result


def fairness(material,records):
    pairs=[]
    for case in material['cases']:
        rows=[r for r in records if r['case_id']==case['id']]
        reasons=[]
        if len(rows)!=3 or any(r['status']!='completed' for r in rows):reasons.append('missing_or_failed_arm')
        for key in ('input_sha256','fresh_state_hash','fixture_model','fixture_body_sha256','generation_hash','budget_hash'):
            if len({r.get(key) for r in rows})!=1 or not all(r.get(key) for r in rows):reasons.append('mismatched_'+key)
        if any(not r.get('fresh_state',False) for r in rows):reasons.append('non_fresh_state')
        generation={r['arm']:any(c.get('kind')=='generation_fixture' for c in r.get('model_calls',[])) for r in rows}
        if len(generation)!=3 or not all(generation.values()):reasons.append('native_branch_bypassed_controlled_generation')
        pairs.append({'case_id':case['id'],'engineering_pair_matched':not reasons,'reasons':reasons,
            'controlled_generation_reached':generation,
            'feature_ablation':True,'same_resource_policy_trial':False,'real_model_comparable':False})
    return pairs


def verify_artifacts(report_path):
    data=load_json(report_path)
    base=report_path.resolve().parent
    count=0
    for row in data['records']:
        if row['status']=='not_run':continue
        path=(base/row['artifact_ref']).resolve()
        if not path.is_relative_to(base) or hashlib.sha256(path.read_bytes()).hexdigest()!=row['artifact_sha256']:raise ValueError('capture artifact missing or changed')
        original=load_json(path)
        for key in ('case_id','arm','input_sha256','rubric_sha256','response_sha256'):
            if original[key]!=row[key]:raise ValueError('artifact belongs to another observation')
        if len(original['model_calls'])!=len(row['model_calls']):raise ValueError('missing model call')
        for call,receipt in zip(original['model_calls'],row['model_calls']):
            if sha(call['input_messages'])!=receipt['input_sha256']:raise ValueError('model input hash mismatch')
        count+=1
    return count


def policy_boundary():
    sys.path.insert(0,str(ROOT/'apps/api'))
    from app.tutor.policy_comparison import PolicyExecutionMetrics,compare_policies
    return compare_policies('R5-fixed-fixture-not-quality',PolicyExecutionMetrics('D1'),PolicyExecutionMetrics('D2')).to_dict()


def report(material,records):
    missing=validate_capture(material,records)
    pairs=fairness(material,records)
    coverage={}
    for arm in ('D0','D1','D2'):
        receipts=[receipt for r in records if r['arm']==arm for receipt in r.get('tool_receipts',[])]
        coverage[arm]={'receipts':len(receipts),'determined_local_claims':sum(r['verified'] and type(r['is_correct']) is bool for r in receipts),
            'eligible_learning_receipts':sum(r['eligible_learning_evidence'] for r in receipts),
            'unknown_or_unrequested':sum(r['is_correct'] is None for r in receipts),
            'meaning':'bounded checker coverage, not model correctness or teaching benefit'}
    return {'version':'r5-offline-report-v1','scope':'engineering_fixture_ablation_only','material_sha256':sha(material),
        'planned_runs':len(material['cases'])*3,'observed_runs':len(records),'completed_runs':sum(r['status']=='completed' for r in records),
        'failed_runs':sum(r['status']=='failed' for r in records),'missing_runs':sorted([list(x) for x in missing]),
        'engineering_passed':not missing and all(r['status']=='completed' for r in records),
        'matched_ablation_cases':sum(x['engineering_pair_matched'] for x in pairs),
        'non_comparable_cases':[x for x in pairs if not x['engineering_pair_matched']],
        'real_model_quality_scored':0,'gold_status':'pending_independent_review','holdout_status':material['holdout_register']['status'],
        'paid_requests':0,'actual_cost':None,'usage_status':'not_applicable_fixed_fixture','live_ready':False,
        'metrics':metric_summary(material,records),'tool_coverage':coverage,'fairness':pairs,'policy_comparison':policy_boundary(),'records':records,
        'conclusion':'Cannot determine whether the mathematical teaching agent outperforms a plain LLM from fixed fixtures.'}


def markdown(data):
    rows=['# R5 离线采集报告','','固定模型回复用于检查编排与证据传递，不计算真实模型数学成绩。','',
        f"计划 {data['planned_runs']} 次，完成 {data['completed_runs']} 次，失败 {data['failed_runs']} 次。",'',
        f"满足三组干预控制的题目：{data['matched_ablation_cases']} / {data['planned_runs']//3}。采集完成与公平对照分别统计。",'',
        '| 组别 | 数学正确性 | 正确步骤误判 | 条件意识 | unknown | 教学反馈 | 证据一致性 |','|---|---|---|---|---|---|---|']
    for arm in ('D0','D1','D2'):rows.append(f'| {arm} | 未评分 | 未评分 | 未评分 | 未评分 | 未评分 | 未评分 |')
    rows+=['','## 逐组执行','','| 案例 | 组别 | 状态 | 调用数 | usage | 耗时 ms |','|---|---|---|---|---|---|']
    rows += [f"| {r['case_id']} | {r['arm']} | {r['status']} | {len(r.get('model_calls',[]))} | 不适用：固定回复 | {r.get('latency_ms','—')} |" for r in data['records']]
    rows+=['','## 公平性与下一步','',
        'D0/D1 使用相同普通教学提示，D1 增加当前数学回执；D2 使用项目原生提示、课程上下文与教学决策。工具与提示长度是消融因素，不是假称完全相同资源。',
        '每次使用独立临时库与相同空初态；这不评价长期个性化。合成身份替代认证，未验 JWT。',
        '完整输入、固定输出、模型调用、SSE、工具及决策回执保存在 JSON 中；usage 与费用不伪造。',
        '24 个公开开发案例均待独立审核；6 个保留题名额尚未由独立作者提供题目。',
        'policy_comparison 保留 baseline：缺少同资源、已审核的真实观察，不能据此采用 D2。',
        '本报告不能回答 Agent 是否胜过普通 LLM；先完成独立审核，再在明确授权和发送前预算控制下接入真实模型。']
    for case in data['non_comparable_cases']:
        rows.append(f"- 不可比较：{case['case_id']}；原因：{', '.join(case['reasons'])}。")
    return '\n'.join(rows)+'\n'
