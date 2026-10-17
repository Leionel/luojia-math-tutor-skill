"""R6.4 report extension; reuse S5 strict readers and R5 capture verification."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
from r5_quality import ROOT, sha, load_cases
from s5_quality import load_json, digest

MATERIAL=ROOT/'evaluation/r64'


def load_material():
    freeze=load_json(MATERIAL/'freeze-v1.json')
    for name,expected in freeze['files'].items():
        if digest(ROOT/name)!=expected:raise ValueError('frozen material drift: '+name)
    legacy=load_cases(ROOT/'evaluation/r5/cases-v1.json')
    cases=load_json(MATERIAL/'cases-v1.json');protocol=load_json(MATERIAL/'protocol-v1.json');rubric=load_json(MATERIAL/'rubric-v1.json')
    if cases['version']!='r64-cases-v1' or len(cases['cases'])!=15 or len({c['id'] for c in cases['cases']})!=15:raise ValueError('fixed 15-case denominator required')
    for c in cases['cases']:
        if c['split']!='public_development' or c['review_status']!='agent_prepared_only' or c['independent_review'] is not None or c['quality_ratings'] is not None:raise ValueError('cannot manufacture reviewed holdout/gold')
        if c['input_sha256']!=hashlib.sha256(c['prompt'].encode()).hexdigest() or c['rubric_sha256']!=digest(MATERIAL/'rubric-v1.json'):raise ValueError('case/rubric binding mismatch')
    if cases['holdout_register']!=legacy['holdout_register']:raise ValueError('legacy holdout register changed')
    return protocol,cases,rubric


def provenance():
    def git(*args):
        r=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,timeout=10);return r.stdout.strip() if r.returncode==0 else None
    paths=[*(ROOT/'apps/api/app').rglob('*.py'),*(ROOT/'scripts').glob('*r64*.py'),*(ROOT/'scripts').glob('r64*.cjs'),*(ROOT/'evaluation/r64').glob('*v1.json')]
    return {'git_sha':git('rev-parse','HEAD'),'working_tree_dirty':bool(git('status','--porcelain')),
            'source_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)},'legacy_freeze_verified':True}


def planned_private():
    return {(f'{d}-{s}',a) for d in ('gs','newton','integration') for s in ('related','unrelated','stale_source') for a in ('P0','P1')}


def controlled_pairs(rows):
    seen={}
    for r in rows:
        key=(r['case_id'],r['arm'])
        if key in seen or key not in planned_private():raise ValueError('duplicate/unplanned private observation')
        seen[key]=r
    result=[]
    for id in sorted({k[0] for k in planned_private()}):
        pair=[seen.get((id,a)) for a in ('P0','P1')];reasons=[]
        if any(r is None or r['status']!='completed' for r in pair):reasons.append('missing_or_failed_arm')
        else:
            for key in ('input_sha256','history_sha256','generation_sha256','model','normalized_prompt_sha256'):
                if not pair[0].get(key) or pair[0][key]!=pair[1].get(key):reasons.append('mismatched_'+key)
        result.append({'case_id':id,'planned_arms':2,'completed_arms':sum(r is not None and r['status']=='completed' for r in pair),
            'input_control_matched':not reasons,'confounds':reasons,'real_quality_comparable':False,
            'quality_delta':None,'confidence_interval':None,'improvement_observed':None})
    return result


def counts(rows,planned):
    if any(r.get('status') not in {'completed','failed','not_run'} for r in rows):raise ValueError('unknown execution status')
    complete=sum(r.get('status')=='completed' for r in rows);failed=sum(r.get('status')=='failed' for r in rows)
    if complete+failed>planned:raise ValueError('observations exceed denominator')
    return {'planned':planned,'completed':complete,'failed':failed,'not_run':planned-complete-failed,'human_reviewed':0,'quality':None}


def verify_artifacts(rows,report_path):
    base=Path(report_path).resolve().parent
    for r in rows:
        if not r.get('artifact_ref'):continue
        path=(base/r['artifact_ref']).resolve()
        if not path.is_relative_to(base) or digest(path)!=r['artifact_sha256']:raise ValueError('artifact changed or escapes report directory')
        artifact=load_json(path)
        if r['status']=='completed':
            if 'case' in artifact:
                if artifact['case']['id']!=r['case_id'] or artifact['case']['input_sha256']!=r['input_sha256']:raise ValueError('artifact belongs to another exploration')
            elif sha(artifact['history'])!=r['history_sha256'] or hashlib.sha256(artifact['question'].encode()).hexdigest()!=r['input_sha256'] or len(artifact['selected_context'])!=r['selected_count']:raise ValueError('artifact belongs to another private observation')


def paired_review_summary(observations,reviews,rubric_hash):
    """Descriptive caller-supplied recordings, not authenticated live execution.

    No fixture can acquire a real quality score, even with a fabricated review.
    This supplements the existing S5 hash/quote review contract for paired deltas.
    """
    indexed={};review_index={};planned={k[0] for k in planned_private()}
    for o in observations:
        key=(o['case_id'],o['arm'])
        if key in indexed or key not in planned_private():raise ValueError('duplicate/unplanned observation')
        indexed[key]=o
    dimensions=load_json(MATERIAL/'rubric-v1.json')['dimensions']
    for r in reviews:
        key=(r['case_id'],r['arm']);o=indexed.get(key)
        if key in review_index or o is None or o.get('evidence_source')!='recorded_run':raise ValueError('only non-fixture caller-supplied recordings can receive human ratings')
        if not all(r.get(k) for k in ('reviewer_id','reviewed_at','review_evidence_ref')):raise ValueError('unsigned human review')
        if not isinstance(r.get('failure_codes'),list) or not isinstance(r.get('disagreement_resolution'),str) or not r['disagreement_resolution'].strip():raise ValueError('failure codes and disagreement disposition required')
        if r['input_sha256']!=o['input_sha256'] or r['response_sha256']!=hashlib.sha256(o['response_text'].encode()).hexdigest() or r['rubric_sha256']!=rubric_hash:raise ValueError('review hashes changed')
        if set(r['ratings'])!=set(dimensions):raise ValueError('all rubric dimensions required')
        for v in r['ratings'].values():
            rating=v.get('rating')
            if rating is None:
                if v.get('status') not in {'not_reviewed','not_applicable'} or not v.get('reason'):raise ValueError('null must distinguish unreviewed and N/A')
            elif type(rating) is not int or rating not in (0,1,2) or not v.get('quote') or v['quote'] not in o['response_text'] or not v.get('basis'):raise ValueError('rating needs exact response evidence and mathematical basis')
        review_index[key]=r
    output={};n_planned=len(planned)
    control={}
    for id in planned:
        pair=[indexed.get((id,a)) for a in ('P0','P1')]
        reasons=[]
        if any(o is None for o in pair):reasons.append('missing_arm')
        else:
            for key in ('input_sha256','history_sha256','generation_sha256','model','normalized_prompt_sha256'):
                if not pair[0].get(key) or pair[0][key]!=pair[1].get(key):reasons.append('mismatched_'+key)
        control[id]=reasons
    for dim in dimensions:
        differences=[]
        for id in sorted({k[0] for k in indexed}):
            off,on=review_index.get((id,'P0')),review_index.get((id,'P1'))
            if off and on and not control[id]:
                a,b=off['ratings'][dim]['rating'],on['ratings'][dim]['rating']
                if a is not None and b is not None:differences.append({'case_id':id,'P1_minus_P0':b-a})
        n=len(differences);mean=sum(d['P1_minus_P0'] for d in differences)/n if n else None
        # Paired scores lie in [-2,2]; a conservative bound stays wide for small n.
        radius=4*math.sqrt(math.log(2/0.05)/(2*n)) if n else None
        output[dim]={'planned_pairs':n_planned,'scored_pairs':n,'unscored_pairs':n_planned-n,'raw_differences':differences,'mean_delta':mean,
                     'interval_95':None if n==0 else [max(-2,mean-radius),min(2,mean+radius)],
                     'uncertainty':'bounded Hoeffding interval; assumes independent paired items; no population/generalization claim for public dev cases'}
    return {'scope':'descriptive_caller_supplied_recordings_not_authenticated','real_execution_verified':False,'pair_confounds':control,'dimensions':output}


def build_report(explorations=(),private=(),legacy=None,browser=None):
    protocol,cases,rubric=load_material();pairing=controlled_pairs(private)
    for row in private:
        if row.get('evidence_source')!='fixed_fixture' or any(row.get(k) is not None for k in ('quality','usage','actual_cost')) or row.get('provider_requests')!=0:raise ValueError('offline private capture cannot claim live quality/usage')
    expected={c['id']:c for c in cases['cases']};seen=set()
    for row in explorations:
        if row['case_id'] in seen or row['case_id'] not in expected or row.get('input_sha256')!=expected[row['case_id']]['input_sha256']:raise ValueError('duplicate/unplanned exploration or changed input')
        if row.get('evidence_source')!='fixed_fixture' or any(row.get(k) is not None for k in ('quality','usage','actual_cost')) or row.get('provider_requests')!=0:raise ValueError('offline capture cannot claim live quality/usage')
        seen.add(row['case_id'])
    legacy_counts={'planned':72,'completed':0,'failed':0,'not_run':72,'human_reviewed':0,'quality':None}
    if legacy:legacy_counts=counts(legacy['records'],72)
    e0={'legacy':legacy_counts,'exploration':counts(explorations,15),'private_context':counts(private,18),'pair_input_control':pairing,
        'evidence_source':'offline_functional_only','quality':None,'usage':None,'actual_cost':None}
    e1={'planned':105,'completed':0,'failed':0,'not_run':105,'human_reviewed':0,'quality':None,'usage':None,'actual_cost':None,
        'model':None,'model_version':None,'provider':None,'status':'blocked_live_admission_and_independent_review',
        'planned_by_track':{'legacy_D0_D1_D2':72,'exploration':15,'private_pairs':18},
        'private_pair_quality':{'planned_pairs':9,'scored_pairs':0,'difference':None,'interval':None},'failure_denominator_policy':'all planned cases retained'}
    tasks=browser['tasks'] if browser else []
    if browser and (browser.get('version')!='r64-browser-v1' or browser.get('participant_type')!='agent_automation' or browser.get('human_participants')!=0):raise ValueError('cannot promote browser automation to human task study')
    ids=[t['task_id'] for t in tasks]
    if len(ids)!=len(set(ids)) or set(ids)-set(protocol['E2_tasks']):raise ValueError('duplicate/unplanned browser tasks')
    if browser:
        sources=browser.get('source_sha256',{})
        if not sources or any(not (ROOT/p).resolve().is_relative_to(ROOT.resolve()) or digest(ROOT/p)!=h for p,h in sources.items()):raise ValueError('browser receipt source changed or absent')
        for task in tasks:
            if task.get('status')=='completed' and (not task.get('steps') or not task.get('artifact_refs')):raise ValueError('completed browser task needs steps and evidence')
            for artifact in task.get('artifact_refs',[]):
                path=(ROOT/artifact['path']).resolve()
                if not path.is_relative_to(ROOT.resolve()) or digest(path)!=artifact['sha256']:raise ValueError('browser artifact changed or escapes workspace')
    e2={'automation':{**counts(tasks,5),'tasks':tasks,'execution_source':'actual_browser' if browser else None},
        'human':{'planned_tasks':5,'participants':0,'completed':0,'status':'not_run_no_participants_or_consent','completion_rate':None}}
    e3={'planned':12,'completed':0,'not_run':12,'status':'blocked_no_independent_items_participants_or_delay','quality':None,'help_free_transfer_score':None,'delayed_score':None}
    failures=[]
    for track,rows in (('exploration',explorations),('private',private)):
        failures.extend({'track':track,'case_id':r['case_id'],'arm':r.get('arm'),'code':r.get('failure_code','PROTOCOL'),'artifact_ref':r.get('artifact_ref')} for r in rows if r['status']=='failed')
    failures.extend({'track':'private_control','case_id':p['case_id'],'code':'PAIR_CONFOUNDED','reasons':p['confounds']} for p in pairing if p['confounds'] and p['completed_arms'])
    failures.extend({'track':'browser','case_id':t['task_id'],'code':'UI_TASK','detail':t.get('failure')} for t in tasks if t['status']=='failed')
    return {'version':'r64-report-v1','protocol_sha256':digest(MATERIAL/'protocol-v1.json'),'provenance':provenance(),
        'levels':{'E0':e0,'E1':e1,'E2':e2,'E3':e3},'materials':{'public_case_slots':39,'unique_public_prompts':len({c['input_sha256'] for c in [*load_cases(ROOT/'evaluation/r5/cases-v1.json')['cases'],*cases['cases']]}),'independently_reviewed_holdout':0,'holdout_slots_unallocated':6,'engineering_fixture_cases':3,'review_status':'agent_prepared_only'},
        'outbound':{'provider_requests':0,'usage':None,'actual_cost':None,'live_transport_enabled':False},
        'records':{'exploration':list(explorations),'private':list(private)},'failures':failures,
        'r7_decision':{'verdict':'repair_quality_first','mathematical_or_learning_improvement_observed':None,
            'reason':'No authorized comparable real-model observations, independent human ratings or human transfer results; E0/E2 automation cannot establish improvement'},
        'legacy_comparison':None if not legacy else {'matched_cases':legacy['matched_ablation_cases'],'planned_cases':24,'confounds':legacy['non_comparable_cases'],'adapter':legacy.get('r64_routing_adapter')}}


def markdown(data):
    e=data['levels'];lines=['# R6.4 可复现评测报告','','本次没有真实模型、数学人工评分或真人参与；不产生模型质量或学习收益结论。','',
        '| 层级 | 计划 | 实际完成 | 失败 | 未运行 | 质量 |','|---|---:|---:|---:|---:|---|']
    for label,row in [('E0 legacy',e['E0']['legacy']),('E0 exploration',e['E0']['exploration']),('E0 private',e['E0']['private_context']),('E1',e['E1']),('E2 automation',e['E2']['automation']),('E3',e['E3'])]:
        lines.append(f"| {label} | {row['planned']} | {row['completed']} | {row.get('failed',0)} | {row['not_run']} | 未评分 |")
    lines += ['',f"个人上下文配对：输入控制匹配 {sum(p['input_control_matched'] for p in e['E0']['pair_input_control'])}/9；真实质量差异和置信范围均为 null。",'',
        'E2 真人参与者 0；自动化任务不算真人成功率。E3 无独立迁移/延迟题与参与者，12 个计划测量保留未运行。','',
        'R7：先修质量，维持三类场景范围。缺少真实模型配对、独立审核与真人结果，不能据离线通过扩大结论。','',
        '## 不可比/失败记录','']
    lines += [json.dumps(f,ensure_ascii=False) for f in data['failures']]
    return '\n'.join(lines)+'\n'
