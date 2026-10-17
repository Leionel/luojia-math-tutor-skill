"""Evaluation denominators, admission, paired evidence and real offline wiring."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from r64_quality import build_report, controlled_pairs, load_material, paired_review_summary, verify_artifacts
from s5_quality import digest


def test_unrun_report_keeps_denominators_without_invented_failures_or_scores():
    report=build_report()
    assert not report['failures']
    assert report['levels']['E1']['not_run']==105
    assert report['levels']['E3']['not_run']==12
    assert report['materials']['public_case_slots']==39
    assert report['materials']['unique_public_prompts']==32
    assert report['materials']['independently_reviewed_holdout']==0
    assert report['outbound']==dict(provider_requests=0,usage=None,actual_cost=None,live_transport_enabled=False)


def test_pair_mismatch_and_missing_arm_stay_in_fixed_denominator():
    rows=[dict(case_id='gs-related',arm=a,status='completed',input_sha256='same',history_sha256=a,
               generation_sha256='same',model='same',normalized_prompt_sha256='same') for a in ('P0','P1')]
    pairs=controlled_pairs(rows)
    assert len(pairs)==9
    pair=next(p for p in pairs if p['case_id']=='gs-related')
    assert pair['confounds']==['mismatched_history_sha256']
    assert pair['quality_delta'] is None
    with pytest.raises(ValueError,match='duplicate'):controlled_pairs(rows+[rows[0]])


def test_offline_records_cannot_acquire_live_usage_or_quality():
    row=dict(case_id='gs-related',arm='P0',status='completed',evidence_source='fixed_fixture',provider_requests=0,usage={'tokens':1})
    with pytest.raises(ValueError,match='cannot claim'):build_report(private=[row])


def review_pair():
    _,_,rubric=load_material();rh=digest(ROOT/'evaluation/r64/rubric-v1.json')
    rows=[dict(case_id='gs-related',arm=a,evidence_source='recorded_run',response_text='exact evidence',input_sha256='same',
          history_sha256='same',generation_sha256='same',model='same',normalized_prompt_sha256='same') for a in ('P0','P1')]
    reviews=[dict(case_id=o['case_id'],arm=o['arm'],reviewer_id='test-only',reviewed_at='test',review_evidence_ref='test',
         input_sha256=o['input_sha256'],response_sha256=hashlib.sha256(o['response_text'].encode()).hexdigest(),rubric_sha256=rh,
         failure_codes=[],disagreement_resolution='test fixture, no real review',
         ratings={d:dict(rating=2 if o['arm']=='P0' else 0,quote='exact evidence',basis='synthetic scoring contract test') for d in rubric['dimensions']}) for o in rows]
    return rows,reviews,rh


def test_review_preserves_regression_wide_uncertainty_and_confounds():
    rows,reviews,rh=review_pair();s=paired_review_summary(rows,reviews,rh)
    assert not s['real_execution_verified']
    assert all(d['mean_delta']==-2 and d['interval_95']==[-2,2] for d in s['dimensions'].values())
    assert all(d['planned_pairs']==9 and d['unscored_pairs']==8 for d in s['dimensions'].values())
    rows[1]['history_sha256']='changed'
    s=paired_review_summary(rows,reviews,rh)
    assert all(d['scored_pairs']==0 and d['unscored_pairs']==9 for d in s['dimensions'].values())


@pytest.mark.parametrize('change',['fixture','unsigned','hash','quote','null'])
def test_review_rejects_fixture_or_unbound_ratings(change):
    rows,reviews,rh=review_pair();dim=next(iter(reviews[0]['ratings']))
    if change=='fixture':rows[0]['evidence_source']='fixed_fixture'
    if change=='unsigned':reviews[0]['reviewer_id']=None
    if change=='hash':reviews[0]['input_sha256']='changed'
    if change=='quote':reviews[0]['ratings'][dim]['quote']='invented fragment'
    if change=='null':reviews[0]['ratings'][dim]={'rating':None}
    with pytest.raises(ValueError):paired_review_summary(rows,reviews,rh)


def test_browser_automation_needs_bound_sources_and_cannot_become_human_study():
    browser=dict(version='r64-browser-v1',participant_type='human',human_participants=1,tasks=[])
    with pytest.raises(ValueError,match='cannot promote'):build_report(browser=browser)
    browser.update(participant_type='agent_automation',human_participants=0)
    with pytest.raises(ValueError,match='source changed or absent'):build_report(browser=browser)


def test_real_offline_capture_roundtrip_and_artifact_tamper_detection():
    target=ROOT/'results/r64/tests'/f'{uuid.uuid4().hex}.json'
    result=subprocess.run([sys.executable,str(ROOT/'scripts/eval_r64.py'),'--offline','--capture','--output',str(target)],cwd=ROOT,capture_output=True,timeout=180)
    assert result.returncode==0,result.stderr.decode(errors='replace')[-3000:]
    report=json.loads(target.read_text(encoding='utf-8'))
    assert report['capture_sources_unchanged']
    assert report['levels']['E0']['exploration']['completed']==15
    assert report['levels']['E0']['private_context']['completed']==18
    assert all(p['input_control_matched'] for p in report['levels']['E0']['pair_input_control'])
    assert report['levels']['E1']['quality'] is None
    rows=report['records']['exploration']+report['records']['private']
    verify_artifacts(rows,target)
    for domain in ('gs','newton','integration'):
        chosen=[r for r in report['records']['private'] if r['domain']==domain and r['selected_count']]
        assert [(r['scenario'],r['arm']) for r in chosen]==[('related','P1')]
    assert sum(r['real_local_runner_count'] for r in report['records']['exploration'])==6
    bad=deepcopy(rows[:1]);bad[0]['artifact_sha256']='changed'
    with pytest.raises(ValueError,match='artifact changed'):verify_artifacts(bad,target)
    # Existing evidence must never be overwritten, and no paid transport option exists.
    for flags in (['--offline','--output',str(target)],['--offline','--live']):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/eval_r64.py'),*flags],cwd=ROOT,capture_output=True,timeout=30)
        assert r.returncode!=0
