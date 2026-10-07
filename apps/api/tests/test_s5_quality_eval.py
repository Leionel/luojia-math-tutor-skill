"""Offline S5.1 report integrity, denominator and CLI boundary regressions."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('s5_quality_contract', ROOT / 'scripts/s5_quality.py')
quality = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quality)
BASE = ROOT / 'evaluation/s5'


def inputs():
    manifest = quality.load_json(BASE / 'runner-fixture-manifest.json')
    obs = quality.load_json(BASE / 'runner-fixture-observations.json')
    reviews = quality.load_json(BASE / 'runner-fixture-reviews.json')
    return manifest, quality.digest(BASE / 'runner-fixture-manifest.json'), obs, reviews


def test_fixture_separation_and_fixed_denominators():
    report = quality.build_report(*inputs())
    assert report['planned_cases'] == 4 and report['executed_cases'] == 3
    metric = report['fixture_contract']['mathematically_correct']
    assert metric == {'numerator': 1, 'denominator': 3, 'scored': 2, 'unscored': 1, 'rate': None}
    assert report['quality']['mathematically_correct']['denominator'] == 0
    assert report['quality']['mathematically_correct']['rate'] is None
    assert report['not_run_cases'] == ['fixture-budget-stop']
    assert report['fixture_violating_cases'] == ['fixture-violation']
    assert report['acceptance'] == 'pending_quality_review'


def test_development_plan_is_not_a_run_or_gold():
    manifest = quality.load_json(BASE / 'manifest.json')
    report = quality.build_report(manifest, quality.digest(BASE / 'manifest.json'))
    assert report['planned_cases'] == 8 and report['executed_cases'] == 0
    assert len(report['not_run_cases']) == 8
    assert all(r['gold_status'] == 'pending' for r in report['cases'])
    assert report['quality']['task_completed']['rate'] is None


@pytest.mark.parametrize('mutation', ['manifest_version', 'duplicate_case', 'empty_case', 'confirmation',
    'applicability_missing', 'bool_run_count', 'synthetic_in_dev', 'observation_version',
    'manifest_hash', 'input_hash', 'duplicate_observation', 'unexpected_observation',
    'bad_run_status', 'source_missing', 'bad_source', 'response_missing', 'unsafe_run_ref',
    'score_unrun', 'rubric_hash', 'response_hash', 'missing_reviewer', 'fixture_human_role',
    'rating_number', 'na_scored', 'conflicting_abstention', 'bad_failure_code', 'not_run_without_reason'])
def test_malformed_contracts_fail_closed(mutation):
    m,h,o,r=inputs()
    if mutation=='manifest_version':m['version']='old'
    elif mutation=='duplicate_case':m['cases'].append(deepcopy(m['cases'][0]))
    elif mutation=='empty_case':m['cases']=[]
    elif mutation=='confirmation':m['split']='confirmation'
    elif mutation=='applicability_missing':del m['cases'][0]['applicable']['action_valid']
    elif mutation=='bool_run_count':m['cases'][0]['planned_runs']=True
    elif mutation=='synthetic_in_dev':m['split']='development'
    elif mutation=='observation_version':o['version']='old'
    elif mutation=='manifest_hash':o['manifest_sha256']='0'*64
    elif mutation=='input_hash':o['records'][0]['input_sha256']='0'*64
    elif mutation=='duplicate_observation':o['records'].append(deepcopy(o['records'][0]))
    elif mutation=='unexpected_observation':o['records'][0]['case_id']='unknown'
    elif mutation=='bad_run_status':o['records'][0]['run_status']='success'
    elif mutation=='source_missing':del o['records'][0]['evidence_source']
    elif mutation=='bad_source':o['records'][0]['evidence_source']='live'
    elif mutation=='response_missing':del o['records'][0]['response_sha256']
    elif mutation=='unsafe_run_ref':o['records'][0]['run_ref']='https://private.example/key'
    elif mutation=='score_unrun':r['records'][0]['case_id']='fixture-budget-stop'
    elif mutation=='rubric_hash':r['records'][0]['rubric_sha256']='0'*64
    elif mutation=='response_hash':r['records'][0]['response_sha256']='0'*64
    elif mutation=='missing_reviewer':del r['records'][0]['reviewer_id']
    elif mutation=='fixture_human_role':r['records'][0]['reviewer_role']='independent'
    elif mutation=='rating_number':r['records'][0]['ratings']['task_completed']=1
    elif mutation=='na_scored':r['records'][0]['ratings']['action_valid']=True
    elif mutation=='conflicting_abstention':r['records'][0]['ratings'].update(appropriate_abstention=True,inappropriate_abstention=True)
    elif mutation=='bad_failure_code':r['records'][0]['primary_failure']='unverified-cause'
    elif mutation=='not_run_without_reason':del o['records'][-1]['not_run_reason']
    with pytest.raises(ValueError):quality.build_report(m,h,o,r)


def test_missing_case_retained_and_report_incomplete():
    m,h,o,r=inputs();o['records'].pop();report=quality.build_report(m,h,o,r)
    assert not report['report_complete']
    assert report['missing_observation_ids']==['fixture-budget-stop']
    assert len(report['cases'])==4


def test_failed_run_stays_in_quality_denominator_and_hard_violation():
    m,h,o,r=inputs();m['split']='development'
    for case in m['cases']:case['gold_status']='author_reviewed_only'
    for row in o['records']:
        if row['run_status']!='not_run':row['evidence_source']='recorded_run'
    for review in r['records']:review.update(reviewer_role='author',reviewer_id='author-declared')
    o['records'][1]['run_status']='failed'
    report=quality.build_report(m,h,o,r)
    assert report['quality']['mathematically_correct']['denominator']==3
    assert report['quality']['mathematically_correct']['unscored']==1
    assert report['acceptance']=='blocked_by_violation'
    assert report['confirmation_status'].startswith('pending')


def test_dry_run_rejects_consumed_observations():
    with pytest.raises(ValueError):quality.build_report(*inputs(),dry_run=True)


def test_episode_budget_uses_runs_not_case_count():
    m,h,_,_=inputs();m['cases'][0].update(kind='episode',planned_runs=3)
    report=quality.build_report(m,h,dry_run=True)
    assert report['executed_cases']==0
    assert sum(c['planned_runs'] for c in m['cases'])==6


@pytest.mark.parametrize('content',['{"x":1,"x":2}','{"x":NaN}','[]'])
def test_json_boundary(tmp_path,content):
    path=tmp_path/'bad.json';path.write_text(content,encoding='utf-8')
    with pytest.raises(ValueError):quality.load_json(path)


@pytest.mark.parametrize('mode',['--offline','--dry-run'])
def test_cli_no_network_plan(tmp_path,mode):
    output=tmp_path/'report.json'
    proc=subprocess.run([sys.executable,str(ROOT/'scripts/eval_tutor_quality.py'),mode,'--output',str(output)],
                        cwd=tmp_path,capture_output=True,text=True,timeout=20)
    assert proc.returncode==0,proc.stderr
    report=json.loads(output.read_text(encoding='utf-8'))
    assert report['usage']['requests_sent_by_runner']==0
    assert report['preflight']['worst_case_requests_without_probe']==48
    assert report['preflight']['live_ready'] is False
    assert report['executed_cases']==0 and report['source_sha256']


def test_cli_live_flag_is_unavailable(tmp_path):
    proc=subprocess.run([sys.executable,str(ROOT/'scripts/eval_tutor_quality.py'),'--live'],
                        capture_output=True,text=True,timeout=20)
    assert proc.returncode==2
    assert not (tmp_path/'report.json').exists()


def test_profile_rejects_credentials_and_nonfinite_cost(tmp_path):
    for payload in [
        {'endpoint':'https://secret.example','api_key':'not-a-real-key'},
        {'version':'s5-plan-profile-v1','model_label':'example','endpoint_sha256':'0'*64,
         'max_requests':48,'currency':'CNY','max_cost':float('inf')},
    ]:
        profile=tmp_path/'profile.json';profile.write_text(json.dumps(payload),encoding='utf-8')
        output=tmp_path/'out.json'
        proc=subprocess.run([sys.executable,str(ROOT/'scripts/eval_tutor_quality.py'),'--dry-run',
                            '--profile',str(profile),'--output',str(output)],capture_output=True,text=True,timeout=20)
        assert proc.returncode==2 and not output.exists()
        assert 'secret.example' not in proc.stderr and 'api_key' not in proc.stderr

@pytest.fixture(scope='module')
def captured_report(tmp_path_factory):
    folder=tmp_path_factory.mktemp('s5-capture-test')
    output=folder/'runtime.json';md=folder/'runtime.md'
    proc=subprocess.run([sys.executable,str(ROOT/'scripts/eval_tutor_quality.py'),'--offline',
        '--manifest',str(BASE/'runtime-fixture-manifest.json'),'--capture-fixtures',
        '--output',str(output),'--markdown-output',str(md)],capture_output=True,text=True,timeout=110)
    assert proc.returncode==0,proc.stderr
    return json.loads(output.read_text(encoding='utf-8')),md.read_text(encoding='utf-8')


@pytest.mark.parametrize('case_id,verdict,eligible,mastery,mistake',[
    ('runtime-correct',True,True,1,0),('runtime-incorrect',False,True,1,1),
    ('runtime-reference',None,False,0,0),('runtime-unknown',None,False,0,0),
])
def test_actual_graph_fixtures_have_independent_states_and_bound_results(captured_report,case_id,verdict,eligible,mastery,mistake):
    report,_=captured_report
    row=next(r for r in report['cases'] if r['case_id']==case_id)
    facts=row['runtime_facts']
    assert facts['is_correct'] is verdict and facts['eligible_learning_evidence'] is eligible
    assert facts['mastery_writes']==mastery and facts['mistake_writes']==mistake
    assert facts['input_bound'] and facts['metadata_restored_equal'] and facts['isolated_initial_state']
    assert report['runtime_contract_status']=='passed'
    assert report['quality']['mathematically_correct']['rate'] is None
    assert report['run_provenance']['network']=='denied'
    assert report['report_builder_sha'] and report['run_provenance']['source_sha256']


def test_markdown_interprets_fixture_evidence_without_quality_gain(captured_report):
    report,md=captured_report
    assert '不能判断真实模型的数学正确率' in md
    assert '错误候选允许更新普通掌握度估计' in md
    assert '不能根据标签数量决定增加ProofState' in md
    assert '真实模型失败簇' in md
    assert '100%' not in md
    assert len(report['cases'])==4


def test_unqualified_learning_write_is_reported_not_averaged(captured_report):
    report,_=captured_report
    manifest=quality.load_json(BASE/'runtime-fixture-manifest.json')
    observations={'version':'s5-observations-v1','manifest_sha256':quality.digest(BASE/'runtime-fixture-manifest.json'),
                  'capture_provenance':report['run_provenance'],'records':[]}
    for row in report['cases']:
        observations['records'].append({k:deepcopy(row[k]) for k in ['case_id','input_sha256','run_status','evidence_source','response_sha256','run_ref','runtime_facts']})
    ref=next(r for r in observations['records'] if r['case_id']=='runtime-reference')
    ref['runtime_facts']['mastery_writes']=1
    result=quality.build_report(manifest,observations['manifest_sha256'],observations)
    assert result['runtime_contract_status']=='failed'
    assert result['runtime_violations']==[{'case_id':'runtime-reference','reasons':['ineligible_learning_write','expectation_mismatch:mastery_writes']}]
    assert result['quality']['mathematically_correct']['denominator']==0


def test_untrusted_provenance_cannot_publish_endpoint_or_key(captured_report):
    report,_=captured_report
    manifest=quality.load_json(BASE/'runtime-fixture-manifest.json')
    obs={'version':'s5-observations-v1','manifest_sha256':quality.digest(BASE/'runtime-fixture-manifest.json'),
         'records':[],'capture_provenance':{**report['run_provenance'],'endpoint':'https://secret.invalid'}}
    with pytest.raises(ValueError):quality.build_report(manifest,obs['manifest_sha256'],obs)


def test_runtime_capture_cannot_execute_development_or_dry_run(tmp_path):
    for args in [
        ['--offline','--capture-fixtures'],
        ['--dry-run','--capture-fixtures','--manifest',str(BASE/'runtime-fixture-manifest.json')],
    ]:
        out=tmp_path/'invalid.json'
        proc=subprocess.run([sys.executable,str(ROOT/'scripts/eval_tutor_quality.py'),*args,'--output',str(out)],
                            capture_output=True,text=True,timeout=20)
        assert proc.returncode==2 and not out.exists()


def test_all_unknown_cannot_pass_normal_capability_fixture(captured_report):
    report,_=captured_report
    manifest=quality.load_json(BASE/'runtime-fixture-manifest.json')
    obs={'version':'s5-observations-v1','manifest_sha256':quality.digest(BASE/'runtime-fixture-manifest.json'),
         'capture_provenance':report['run_provenance'],'records':[]}
    for row in report['cases']:
        record={k:deepcopy(row[k]) for k in ['case_id','input_sha256','run_status','evidence_source','response_sha256','run_ref','runtime_facts']}
        record['runtime_facts'].update(is_correct=None,eligible_learning_evidence=False,origin='none',mastery_writes=0,mistake_writes=0)
        obs['records'].append(record)
    result=quality.build_report(manifest,obs['manifest_sha256'],obs)
    assert result['runtime_contract_status']=='failed'
    assert any(x['case_id']=='runtime-correct' for x in result['runtime_violations'])
