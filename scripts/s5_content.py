"""S5.2 content bindings and unsigned human review packets; no model scoring."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from fractions import Fraction as F
from s5_quality import digest, load_json, validate_manifest


def validate_content(manifest_path: Path) -> dict | None:
    manifest=load_json(manifest_path)
    cases=validate_manifest(manifest)
    if 'content_file' not in manifest:
        return None
    name=manifest['content_file']
    if not isinstance(name,str) or Path(name).name!=name or not name.endswith('.json'):
        raise ValueError('content must be a sibling JSON file')
    parent=manifest_path.resolve().parent
    path=(parent/name).resolve()
    if path.parent!=parent or digest(path)!=manifest.get('content_sha256'):
        raise ValueError('content file binding mismatch')
    content=load_json(path)
    if content.get('version')!='s5-development-content-v1' or content.get('split')!='development':
        raise ValueError('unsupported content version or split')
    if content.get('revision')!=manifest.get('content_revision'):
        raise ValueError('content revision mismatch')
    entries=content.get('cases')
    if not isinstance(entries,list) or {x.get('id') for x in entries} != {c['id'] for c in cases} or len(entries)!=len(cases):
        raise ValueError('content IDs must exactly match the manifest')
    for case in cases:
        entry=next(x for x in entries if x['id']==case['id'])
        if not isinstance(entry.get('prompt'),str) or not 1<=len(entry['prompt'])<=4096:
            raise ValueError('invalid public draft prompt')
        if hashlib.sha256(entry['prompt'].encode()).hexdigest()!=case['input_sha256'] or entry.get('input_sha256')!=case['input_sha256']:
            raise ValueError('content input hash mismatch')
        rubric=entry.get('rubric')
        if not isinstance(rubric,dict) or rubric.get('version')!='s5-case-rubric-v1':
            raise ValueError('invalid case rubric')
        rh=hashlib.sha256(json.dumps(rubric,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        if rh!=case['rubric_sha256'] or entry.get('rubric_sha256')!=rh:
            raise ValueError('content rubric hash mismatch')
        required=rubric.get('required');forbidden=rubric.get('forbidden')
        if not isinstance(required,list) or not required or not isinstance(forbidden,list) or not forbidden:
            raise ValueError('necessary and forbidden conclusions required')
        for group in [required,forbidden]:
            if any(not isinstance(x,dict) or not isinstance(x.get('id'),str) or not isinstance(x.get('text'),str) for x in group):
                raise ValueError('invalid criterion')
            if len({x['id'] for x in group})!=len(group):raise ValueError('duplicate criterion')
        if entry.get('preparation')!={'status':'agent_prepared_only','prepared_by':'Codex','human_author_review':'pending','independent_human_review':'pending'} or case['gold_status']!='pending':
            raise ValueError('agent packet cannot promote itself to human gold')
        if not isinstance(entry.get('independent_solution'),list) or not entry['independent_solution'] or any(not isinstance(x,str) for x in entry['independent_solution']):
            raise ValueError('independent derivation required')
    return content


def exact_math_checks() -> dict:
    """Independent exact arithmetic for public inputs; not a semantic answer grader."""
    A=((F(3),F(1)),(F(1),F(2)));x=(F(1),F(2));b=(F(5),F(5))
    residual=[sum(A[i][j]*x[j] for j in range(2))-b[i] for i in range(2)]
    singular=((F(1),F(2)),(F(2),F(4)));v=(F(-2),F(1));candidate=(F(1),F(1));rhs=(F(3),F(6))
    null=[sum(singular[i][j]*v[j] for j in range(2)) for i in range(2)]
    first=[sum(singular[i][j]*candidate[j] for j in range(2))-rhs[i] for i in range(2)]
    second=[candidate[j]+v[j] for j in range(2)]
    alternate=[sum(singular[i][j]*second[j] for j in range(2))-rhs[i] for i in range(2)]
    f=lambda n:n*n*n-2*n+2
    df=lambda n:3*n*n-2
    n1=F(0)-f(F(0))/df(F(0));n2=n1-f(n1)/df(n1)
    checks={'linear_residual_zero':residual==[0,0],'linear_determinant_5':A[0][0]*A[1][1]-A[0][1]*A[1][0]==5,
            'singular_nullspace_witness':null==[0,0] and v!=(0,0),
            'two_distinct_solutions':candidate!=tuple(second) and first==alternate==[0,0],
            'newton_cycle_0_1_0':n1==1 and n2==0,'cycle_derivatives_nonzero':df(F(0))==-2 and df(n1)==1,
            'cycle_points_not_roots':f(F(0))!=0 and f(n1)!=0}
    return {'version':'s5-independent-arithmetic-v1','method':'stdlib Fraction, no app checker or root runner',
        'checks':checks,'passed':all(checks.values()),
        'scope':'Exact witness arithmetic only; algebraic/theorem/scope explanations are agent prepared, not human-reviewed or formally proven.',
        'facts':{'linear_residual':[str(n) for n in residual],'null_vector':[str(n) for n in v],
                 'alternate_solution':[str(n) for n in second],'cycle':[str(F(0)),str(n1),str(n2)]}}


def prepare_review_packet(manifest_path: Path) -> dict:
    manifest=load_json(manifest_path);content=validate_content(manifest_path)
    if content is None:raise ValueError('manifest has no bound development content')
    return {'version':'s5-review-worksheet-v1','manifest_sha256':digest(manifest_path),
        'content_sha256':manifest['content_sha256'],'status':'unsigned_human_review_pending',
        'reviewer_id':None,'reviewer_role':None,'method':'Human evidence annotations; not compatible with scored reviews until completed and validated.',
        'records':[{'case_id':e['id'],'input_sha256':e['input_sha256'],'rubric_sha256':e['rubric_sha256'],
            'response_sha256':None,'required':[{'criterion_id':c['id'],'satisfied':None,'response_location':None,'comment':None} for c in e['rubric']['required']],
            'forbidden':[{'criterion_id':c['id'],'observed':None,'response_location':None,'comment':None} for c in e['rubric']['forbidden']],
            'review_status':'pending'} for e in content['cases']]}


def render_content(content: dict) -> str:
    lines=['# S5.2 development题解与逐题rubric','',
        '公开开发材料，由Codex准备并作精确算术自检；真人作者审核、独立二审均未完成。不是封存题或已验收teacher gold。',
        'E1行为与E2数学使用同一批8个case，不相加为16样本。工具弃权与任务弃权分开；checker不支持前提不等于数学结论错误。','']
    for e in content['cases']:
        r=e['rubric'];lines += [f"## {e['id']}",'',e['prompt'],'',f"范围/量词：{r['domain_and_quantifier']}",'','独立解答：','']
        lines += [f"{i+1}. {text}" for i,text in enumerate(e['independent_solution'])]
        lines += ['','必要结论与依据：','']+[f"- {c['id']}：{c['text']}" for c in r['required']]
        lines += ['','禁止结论：','']+[f"- {c['id']}：{c['text']}" for c in r['forbidden']]
        lines += ['',r['allowed_alternatives'],r['score_evidence_rule'],
            f"核验能力：{r['capability_boundary']['tool_support']}；学习资格：{r['capability_boundary']['learning_qualification']}。",
            'review状态：agent_prepared_only；human_author_review=pending；independent_human_review=pending。','']
    return '\n'.join(lines)


def recorded_answers_to_observations(manifest_path: Path, sidecar_path: Path) -> dict:
    """Caller-supplied public-case recordings. No model execution or identity attestation."""
    manifest=load_json(manifest_path);validate_content(manifest_path)
    cases=validate_manifest(manifest);allowed={c['id']:c for c in cases}
    data=load_json(sidecar_path)
    if set(data)!={'version','manifest_sha256','records'} or data['version']!='s5-recorded-answers-v1' or data['manifest_sha256']!=digest(manifest_path):
        raise ValueError('recorded answers envelope mismatch')
    if manifest['split']!='development' or not isinstance(data['records'],list):
        raise ValueError('only development recordings may be replayed')
    records=[];seen=set()
    for row in data['records']:
        keys={'case_id','input_sha256','run_status','run_ref','response_text','not_run_reason'}
        if not isinstance(row,dict) or set(row)!=keys or not isinstance(row['case_id'],str) or row['case_id'] not in allowed or row['case_id'] in seen:
            raise ValueError('recorded answer IDs/schema invalid')
        seen.add(row['case_id']);case=allowed[row['case_id']]
        if row['input_sha256']!=case['input_sha256']:raise ValueError('recording input hash mismatch')
        status=row['run_status']
        if status not in {'completed','failed','not_run'}:raise ValueError('unknown recording status')
        if status=='not_run':
            if row['response_text'] is not None or row['run_ref'] is not None:raise ValueError('unexecuted recording cannot contain a response')
            records.append({k:row[k] for k in ('case_id','input_sha256','run_status','not_run_reason')})
        else:
            from s5_quality import valid_id
            if not valid_id(row['run_ref']) or not isinstance(row['response_text'],str) or not 1<=len(row['response_text'])<=32768 or row['not_run_reason'] is not None:
                raise ValueError('invalid bounded recorded response')
            records.append({'case_id':row['case_id'],'input_sha256':row['input_sha256'],'run_status':status,
                'evidence_source':'recorded_run','run_ref':row['run_ref'],
                'response_sha256':hashlib.sha256(row['response_text'].encode()).hexdigest()})
    return {'version':'s5-observations-v1','manifest_sha256':data['manifest_sha256'],'records':records}
