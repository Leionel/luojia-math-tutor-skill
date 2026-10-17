"""Versioned phase-specific offline routing shim around the frozen R5 collector."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
from r5_quality import ROOT, load_cases, report, markdown, verify_artifacts
from s5_quality import load_json, digest


@contextmanager
def routing_fixture(receipts):
    from app.tutor.policy_router import PolicyRouter, PolicyDecision
    from app.tutor.intent_router import ACTION_BY_INTENT
    async def route(self, message, fallback_intent, *args, **kwargs):
        # A protocol fixture, never a case-ID/gold-dependent routing answer.
        result=PolicyDecision(fallback_intent,ACTION_BY_INTENT[fallback_intent],0.95,False)
        receipts.append({"message":message,"origin":"offline_routing_fixture", "intent":result.intent.value,
                         "action":result.action.value,"confidence":result.confidence,"uncertain":False,
                         "provider_requests":0,"usage":None})
        return result
    with patch.object(PolicyRouter,"decide_route",route):yield


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--offline',action='store_true',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--case',action='append',default=[]);a=p.parse_args()
    target=a.output.resolve()
    if (not target.is_relative_to((ROOT/'results').resolve()) or target.suffix!='.json' or target.exists()
        or target.with_suffix('.md').exists() or (target.parent/(target.stem+'-artifacts')).exists()):p.error('new JSON output inside results/ required; preserve prior evidence')
    for key in list(os.environ):
        if 'KEY' in key or 'TOKEN' in key or key.startswith(('LLM_','MINERU_','DATABASE_','COURSE_')):os.environ.pop(key,None)
    os.environ['LUOJIA_NO_DOTENV']='1';sys.path.insert(0,str(ROOT/'apps/api'))
    import eval_r5
    receipts=[];target.parent.mkdir(parents=True,exist_ok=True)
    before=digest(ROOT/'scripts/eval_r5.py')
    with routing_fixture(receipts):eval_r5.worker(ROOT/'evaluation/r5/cases-v1.json',target,a.case)
    data=load_json(target);data['r64_routing_adapter']={"version":"r64-phase-routing-fixture-v1", "receipts":receipts,
        "sha256":digest(Path(__file__)),"legacy_collector_unchanged":digest(ROOT/'scripts/eval_r5.py')==before,
        "native_live_routing_fixed":False,"confound":"offline routing is assigned the deterministic fallback intent; not evidence of routing quality"}
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');verify_artifacts(target)
    target.with_suffix('.md').write_text(markdown(data),encoding='utf-8')
    print(json.dumps({"completed":data['completed_runs'],"planned":data['planned_runs'],"matched":data['matched_ablation_cases'],"quality":None}))
    return 0 if data['engineering_passed'] else 1


if __name__=='__main__':raise SystemExit(main())
