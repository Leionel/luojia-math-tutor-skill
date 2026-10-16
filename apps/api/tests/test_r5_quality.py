"""R5 engineering evidence must remain separate from model-quality evidence."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from r5_quality import load_cases,metric_summary,fairness,validate_capture,sha,policy_boundary


def material():return load_cases(ROOT/'evaluation/r5/cases-v1.json')


def fixture_rows():
    return [{'case_id':c['id'],'arm':a,'input_sha256':c['input_sha256'],'rubric_sha256':c['rubric_sha256'],
        'evidence_source':'fixed_fixture','status':'completed','response_text':'fixed','response_sha256':hashlib.sha256(b'fixed').hexdigest(),
        'fresh_state':True,'fresh_state_hash':'same','fixture_model':'same','fixture_body_sha256':'same','generation_hash':'same','budget_hash':'same',
        'model_calls':[{'kind':'generation_fixture'}]}
        for c in material()['cases'] for a in ('D0','D1','D2')]


def test_r5_material_has_24_reviewable_cases_and_no_invented_holdout():
    m=material();assert len(m['cases'])==24
    assert len(m['holdout_register']['slots'])==6
    assert all(c['rubric']['independent_review']=='pending' for c in m['cases'])
    assert all(x['prompt'] is None for x in m['holdout_register']['slots'])


@pytest.mark.parametrize('change',['input','rubric','fake_gold','holdout'])
def test_r5_material_rejects_drift_or_fake_review(tmp_path,change):
    m=material()
    if change=='input':m['cases'][0]['prompt']+=' changed'
    if change=='rubric':m['cases'][0]['rubric']['allowed_conclusions'].append('new')
    if change=='fake_gold':m['cases'][0]['rubric']['independent_review']='complete';m['cases'][0]['rubric_sha256']=sha(m['cases'][0]['rubric'])
    if change=='holdout':m['holdout_register']['slots'][0]['prompt']='public fake holdout'
    p=tmp_path/'cases.json';p.write_text(json.dumps(m,ensure_ascii=False),encoding='utf-8')
    with pytest.raises(ValueError):load_cases(p)


def test_r5_no_review_and_failure_do_not_shrink_quality_denominators():
    rows=fixture_rows();rows[0]['status']='failed';rows[0]['response_text']=None
    s=metric_summary(material(),rows)
    assert s['D0']['mathematical_correctness']['planned']==24
    assert s['D0']['mathematical_correctness']['completed']==23
    assert s['D0']['mathematical_correctness']['failed']==1
    assert s['D0']['mathematical_correctness']['unscored']==24
    assert s['D0']['mathematical_correctness']['real_model_rate'] is None
    assert s['D0']['mathematical_correctness']['synthetic_rate'] is None


def test_r5_duplicate_wrong_hash_and_na_scores_fail_closed():
    m=material();rows=fixture_rows()
    with pytest.raises(ValueError):validate_capture(m,rows+[rows[0]])
    bad=deepcopy(rows);bad[0]['rubric_sha256']='wrong'
    with pytest.raises(ValueError):validate_capture(m,bad)
    c=m['cases'][0];r=rows[0]
    review={'kind':'synthetic_report_test','case_id':c['id'],'arm':'D0','response_sha256':r['response_sha256'],
        'rubric_sha256':r['rubric_sha256'],'metrics':{'valid_step_misjudgment':False}}
    with pytest.raises(ValueError):metric_summary(m,rows,[review])


def test_r5_synthetic_scores_never_become_real_model_scores():
    m=material();rows=fixture_rows();reviews=[]
    for r in rows:
        c=next(c for c in m['cases'] if c['id']==r['case_id'])
        reviews.append({'kind':'synthetic_report_test','case_id':r['case_id'],'arm':r['arm'],
            'response_sha256':r['response_sha256'],'rubric_sha256':r['rubric_sha256'],
            'metrics':{k:True for k,v in c['applicability'].items() if v}})
    s=metric_summary(m,rows,reviews)
    assert s['D2']['mathematical_correctness']['synthetic_rate']==1
    assert s['D2']['mathematical_correctness']['real_model_rate'] is None


def test_r5_fairness_and_existing_policy_comparison_do_not_certify_superiority():
    rows=fixture_rows();assert all(x['engineering_pair_matched'] for x in fairness(material(),rows))
    rows[0]['fixture_model']='other'
    assert not fairness(material(),rows)[0]['engineering_pair_matched']
    rows=fixture_rows();rows[0]['model_calls']=[]
    assert 'native_branch_bypassed_controlled_generation' in fairness(material(),rows)[0]['reasons']
    assert policy_boundary()['verdict']=='retain_baseline'


def test_r5_real_asgi_capture_preserves_arm_interventions_and_unknown(tmp_path):
    target=ROOT/'results/r5-test-capture'/f'{tmp_path.name}.json'
    done=subprocess.run([sys.executable,str(ROOT/'scripts/eval_r5.py'),'--offline','--case','E01','--output',str(target)],
        cwd=ROOT,capture_output=True,timeout=70)
    # Selection leaves the other planned cases explicitly not_run.
    assert done.returncode==1
    data=json.loads(target.read_text(encoding='utf-8'))
    rows=[r for r in data['records'] if r['case_id']=='E01']
    assert len(rows)==3 and all(r['status']=='completed' for r in rows)
    assert data['completed_runs']==3 and data['real_model_quality_scored']==0
    assert data['network_guard']['denied_attempts']==[]
    assert rows[0]['tool_receipts'][0]['is_correct'] is None
    assert rows[1]['tool_receipts'][0]['is_correct'] is False
    assert rows[2]['tool_receipts'][0]['is_correct'] is False
    artifacts=[]
    for r in rows[:2]:
        artifact=target.parent/r['artifact_ref']
        assert hashlib.sha256(artifact.read_bytes()).hexdigest()==r['artifact_sha256']
        artifacts.append(json.loads(artifact.read_text(encoding='utf-8')))
    d0=artifacts[0]['model_calls'][-1]['input_messages'];d1=artifacts[1]['model_calls'][-1]['input_messages']
    assert len(d0)==2 and len(d1)==3
    assert d0[0]==d1[0] and d0[-1]==d1[-1]
    assert '当前有限数学检查回执' in d1[1]['content']
    assert all(not x['real_model_comparable'] for x in data['fairness'])
