"""S5.2 bound content, unsigned review and real ASGI episode regressions."""
from copy import deepcopy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
ROOT=Path(__file__).resolve().parents[3]
SCRIPTS=ROOT/'scripts'
sys.path.insert(0,str(SCRIPTS))
import s5_content as content
import s5_quality as quality
BASE=ROOT/'evaluation/s5'


def test_eight_cases_have_specific_derivations_and_no_human_gold():
    packet=content.validate_content(BASE/'manifest.json')
    assert len(packet['cases'])==8
    assert all(len(c['independent_solution'])>=2 for c in packet['cases'])
    assert all(c['preparation']['human_author_review']=='pending' and c['preparation']['independent_human_review']=='pending' for c in packet['cases'])
    manifest=quality.load_json(BASE/'manifest.json')
    assert sum(c['applicable']['checker_coverage'] for c in manifest['cases'])==2
    domain=next(c for c in packet['cases'] if c['id']=='dev-premise')
    assert domain['rubric']['capability_boundary']['tool_support']=='unsupported_extra_premise'
    assert domain['rubric']['capability_boundary']['learning_qualification']=='none'


def test_exact_witness_checks_do_not_use_app_checker():
    result=content.exact_math_checks()
    assert result['passed'] and len(result['checks'])==7
    A=[[3,1],[1,2]];x=[1,2];b=[5,5]
    assert [sum(Fraction(A[i][j])*x[j] for j in range(2))-b[i] for i in range(2)]==[0,0]
    assert result['facts']['linear_residual']==['0','0']
    assert result['facts']['alternate_solution']==['-1','2']
    assert result['facts']['cycle']==['0','1','0']
    assert 'no app checker' in result['method']


def test_review_worksheet_is_unsigned_and_cannot_be_imported_as_scores():
    packet=content.prepare_review_packet(BASE/'manifest.json')
    assert packet['reviewer_id'] is None and packet['reviewer_role'] is None
    assert all(row['response_sha256'] is None for row in packet['records'])
    assert all(c['satisfied'] is None for row in packet['records'] for c in row['required'])
    manifest=quality.load_json(BASE/'manifest.json')
    with pytest.raises(ValueError):quality.build_report(manifest,quality.digest(BASE/'manifest.json'),reviews=packet)


@pytest.mark.parametrize('change',['file_hash','input_hash','rubric_hash','duplicate_id','missing_case','revision','human_promotion','path_escape'])
def test_content_drift_or_fake_gold_is_rejected(tmp_path,change):
    manifest=quality.load_json(BASE/'manifest.json');packet=quality.load_json(BASE/'development-content-v1.json')
    if change=='file_hash':manifest['content_sha256']='0'*64
    elif change=='input_hash':manifest['cases'][0]['input_sha256']='0'*64
    elif change=='rubric_hash':manifest['cases'][0]['rubric_sha256']='0'*64
    elif change=='duplicate_id':packet['cases'][1]['id']=packet['cases'][0]['id']
    elif change=='missing_case':packet['cases'].pop()
    elif change=='revision':manifest['content_revision']='new-version'
    elif change=='human_promotion':manifest['cases'][0]['gold_status']='independently_reviewed'
    elif change=='path_escape':manifest['content_file']='../outside.json'
    cp=tmp_path/'development-content-v1.json';cp.write_text(json.dumps(packet,ensure_ascii=False),encoding='utf-8')
    if change!='file_hash':manifest['content_sha256']=quality.digest(cp)
    mp=tmp_path/'manifest.json';mp.write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(ValueError):content.validate_content(mp)


def test_cli_cannot_overwrite_bound_inputs(tmp_path):
    packet=quality.load_json(BASE/'manifest.json')
    cp=tmp_path/'development-content-v1.json';cp.write_bytes((BASE/'development-content-v1.json').read_bytes())
    mp=tmp_path/'manifest.json';mp.write_text(json.dumps(packet),encoding='utf-8');before=mp.read_bytes()
    proc=subprocess.run([sys.executable,str(SCRIPTS/'eval_tutor_quality.py'),'--offline','--manifest',str(mp),'--output',str(mp)],capture_output=True,text=True,timeout=20)
    assert proc.returncode==2 and mp.read_bytes()==before


@pytest.fixture(scope='module')
def episodes(tmp_path_factory):
    folder=tmp_path_factory.mktemp('s5-2-episodes');out=folder/'episodes.json';md=folder/'episodes.md'
    proc=subprocess.run([sys.executable,str(SCRIPTS/'eval_tutor_quality.py'),'--offline','--capture-episodes',
        '--manifest',str(BASE/'episode-fixture-manifest.json'),'--output',str(out),'--markdown-output',str(md)],capture_output=True,text=True,timeout=110)
    assert proc.returncode==0,proc.stderr
    return json.loads(out.read_text(encoding='utf-8')),md.read_text(encoding='utf-8')


@pytest.mark.parametrize('case_id,count',[('episode-newton-reference',1),('episode-linear-revision',2)])
def test_real_asgi_sse_episodes_preserve_confirmation_and_input(episodes,case_id,count):
    report,md=episodes
    row=next(r for r in report['cases'] if r['case_id']==case_id);facts=row['episode_facts']
    assert facts['actual_runs']==count and len(set(facts['run_refs']))==count
    assert facts['isolated_initial_state'] and all(x['passed'] for x in facts['stages'])
    assert report['episode_contract_status']=='passed_content_pending'
    assert report['quality']['mathematically_correct']['rate'] is None
    assert report['run_provenance']['persistence']=='asgi_stream_saved_by_orchestrator'
    assert '未请求自动单步核验' in md and '409/404可能是正确拦截' in md


def replay(report):
    manifest=quality.load_json(BASE/'episode-fixture-manifest.json')
    obs={'version':'s5-observations-v1','manifest_sha256':quality.digest(BASE/'episode-fixture-manifest.json'),
        'capture_provenance':deepcopy(report['run_provenance']),
        'records':[{k:deepcopy(row[k]) for k in ['case_id','input_sha256','run_status','evidence_source','response_sha256','run_ref','episode_facts']} for row in report['cases']]}
    return manifest,obs


@pytest.mark.parametrize('change',['missing_stage','wrong_order','wrong_run_count','save_failed'])
def test_episode_bad_sequence_or_write_is_not_averaged(episodes,change):
    m,o=replay(episodes[0]);f=o['records'][0]['episode_facts']
    if change=='missing_stage':f['stages'].pop()
    elif change=='wrong_order':f['stages'].reverse()
    elif change=='wrong_run_count':m['cases'][0]['planned_runs']=2
    elif change=='save_failed':next(x for x in f['stages'] if x['id']=='explicit_save')['passed']=False
    report=quality.build_report(m,o['manifest_sha256'],o)
    assert report['episode_contract_status']=='failed' and report['episode_violations']
    assert report['quality']['mathematically_correct']['denominator']==0


@pytest.mark.parametrize('change',['duplicate_stage','bad_http_status','fake_content_review','duplicate_run','wrong_capture_kind'])
def test_episode_schema_does_not_admit_fake_confirmation(episodes,change):
    m,o=replay(episodes[0]);f=o['records'][0]['episode_facts']
    if change=='duplicate_stage':f['stages'].append(deepcopy(f['stages'][0]))
    elif change=='bad_http_status':f['stages'][0]['http_status']=True
    elif change=='fake_content_review':f['content_review']='teacher_gold_passed'
    elif change=='duplicate_run':o['records'][1]['episode_facts']['run_refs']*=0
    elif change=='wrong_capture_kind':o['capture_provenance'].update(kind='owned_offline_graph_fixture',persistence='graph metadata projection saved by harness')
    with pytest.raises(ValueError):quality.build_report(m,o['manifest_sha256'],o)


def test_episode_capture_cannot_run_arbitrary_development_cases(tmp_path):
    out=tmp_path/'bad.json'
    proc=subprocess.run([sys.executable,str(SCRIPTS/'eval_tutor_quality.py'),'--offline','--capture-episodes','--output',str(out)],capture_output=True,text=True,timeout=20)
    assert proc.returncode==2 and not out.exists()

@pytest.mark.parametrize('change',['wrong_manifest','wrong_input','duplicate','extra_secret_field','response_too_long','not_run_with_response'])
def test_recording_adapter_rejects_stale_or_sensitive_schema(tmp_path,change):
    m=quality.load_json(BASE/'manifest.json');case=m['cases'][0]
    row={'case_id':case['id'],'input_sha256':case['input_sha256'],'run_status':'completed','run_ref':'synthetic-import-test',
         'response_text':'合成导入合同测试，不是真实模型运行。','not_run_reason':None}
    packet={'version':'s5-recorded-answers-v1','manifest_sha256':quality.digest(BASE/'manifest.json'),'records':[row]}
    if change=='wrong_manifest':packet['manifest_sha256']='0'*64
    elif change=='wrong_input':row['input_sha256']='0'*64
    elif change=='duplicate':packet['records'].append(deepcopy(row))
    elif change=='extra_secret_field':row['api_key']='not-a-real-secret'
    elif change=='response_too_long':row['response_text']='a'*32769
    elif change=='not_run_with_response':row.update(run_status='not_run',not_run_reason='budget_stop')
    path=tmp_path/'recorded.json';path.write_text(json.dumps(packet),encoding='utf-8')
    with pytest.raises(ValueError):content.recorded_answers_to_observations(BASE/'manifest.json',path)


def test_recording_adapter_hashes_answer_and_keeps_missing_cases(tmp_path):
    m=quality.load_json(BASE/'manifest.json');case=m['cases'][0]
    raw='合成导入样本；不表示真实模型质量。'
    packet={'version':'s5-recorded-answers-v1','manifest_sha256':quality.digest(BASE/'manifest.json'),'records':[
        {'case_id':case['id'],'input_sha256':case['input_sha256'],'run_status':'completed','run_ref':'synthetic-import-test','response_text':raw,'not_run_reason':None}]}
    path=tmp_path/'recorded.json';path.write_text(json.dumps(packet),encoding='utf-8')
    obs=content.recorded_answers_to_observations(BASE/'manifest.json',path)
    assert raw not in json.dumps(obs,ensure_ascii=False)
    report=quality.build_report(m,obs['manifest_sha256'],obs)
    assert not report['report_complete'] and len(report['missing_observation_ids'])==7
    assert report['quality']['task_completed']['unscored']==1 and report['quality']['task_completed']['rate'] is None
