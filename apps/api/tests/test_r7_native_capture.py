"""Native wire/application capture, not synthetic mathematical quality scores."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from r7_native_capture import manifest, approve
from s5_budget import BudgetRejected


@pytest.mark.asyncio
async def test_provider_failure_is_not_hidden_by_native_router_clarification(tmp_path):
    import httpx
    from r7_native_capture import capture_case
    from r7_quality import ReviewedReplayPolicy
    result=await capture_case({'id':'upstream-failed','prompt':'第三步比第二步小，能说明一定收敛吗？'},
        tmp_path/'failed.json',policy=ReviewedReplayPolicy(),key='fixture',
        underlying=httpx.MockTransport(lambda request:httpx.Response(503,json={'error':'synthetic outage'})))
    assert result['status']=='failed' and result['failure_code']=='UPSTREAM_MODEL_FAILURE'
    assert result['model_call_failures']==[0]
    assert result['provider_requests']==0 and result['quality'] is None


def test_native_live_requires_fresh_exact_manifest_and_independent_review():
    plan=manifest()
    with pytest.raises(BudgetRejected,match='manifest_mismatch'):
        approve(plan,{})
    from r5_quality import sha
    with pytest.raises(BudgetRejected,match='missing_authorization_ref'):
        approve(plan,{'manifest_sha256':sha(plan)})
    assert all(c.get('rubric_sha256') or c.get('rubric') for c in plan['cases'])


def test_actual_asgi_wire_tool_guard_repair_and_advice_are_persisted():
    (ROOT/'results').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='r7-native-test-',dir=ROOT/'results') as directory:
        target=Path(directory)/'report.json'
        assert target.resolve().is_relative_to((ROOT/'results').resolve())
        env={k:v for k,v in os.environ.items() if 'KEY' not in k and 'TOKEN' not in k}
        env.update(LUOJIA_NO_DOTENV='1',PYTHONUTF8='1')
        done=subprocess.run([sys.executable,str(ROOT/'scripts/r7_native_capture.py'),'--offline','--output',str(target)],
                            env=env,cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=90)
        assert done.returncode==0,done.stderr
        data=json.loads(target.read_text(encoding='utf8'))
        assert data['engineering_verified'] and data['provider_requests']==0 and data['quality'] is None
        artifacts={r['case_id']:json.loads((target.parent/r['artifact_ref']).read_text(encoding='utf8')) for r in data['records']}
        tool=artifacts['wire-tool']
        assert '数学教学路由器' in tool['calls'][0]['payload']['messages'][0]['content']
        evidence=next(json.loads(m['content']) for c in tool['calls'] for m in c['payload']['messages'] if m['role']=='tool')
        assert evidence['status']=='succeeded' and evidence['data']['derivative']=='2*x'
        assert artifacts['wire-repair']['saved']['learning_meta']['answer_guard']['status']=='repaired'
        assert artifacts['wire-advice']['saved']['revision']==2
        assert artifacts['wire-advice']['saved']['runs']==[]  # proposal never auto-runs a student experiment
        assert all(a['status']=='completed' for a in artifacts.values())
        assert all(a['course_binding_verified'] for a in artifacts.values())
