"""R6.4 offline protocol extension. No live-provider transport is enabled."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
from r5_quality import ROOT, verify_artifacts as verify_r5
from s5_quality import load_json
from r64_quality import build_report, load_material, markdown, verify_artifacts, provenance


def write_report(target, data):
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    target.with_suffix('.md').write_text(markdown(data),encoding='utf-8')


async def worker(target):
    from r64_capture import isolate, capture_explorations, capture_private_pairs
    isolate();_,cases,_=load_material()
    before=provenance()['source_sha256']
    write_report(target,build_report())
    explorations=await capture_explorations(cases['cases'],target)
    write_report(target,build_report(explorations=explorations))
    private=await capture_private_pairs(target)
    data=build_report(explorations=explorations,private=private)
    data['capture_sources_unchanged']=before==provenance()['source_sha256']
    if not data['capture_sources_unchanged']:data['failures'].append({'track':'capture','code':'SOURCE_DRIFT'})
    write_report(target,data)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--offline',action='store_true',required=True)
    p.add_argument('--capture',action='store_true');p.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    p.add_argument('--output',type=Path,default=ROOT/'results/r64/report.json');p.add_argument('--legacy-report',type=Path);p.add_argument('--browser-receipt',type=Path)
    args=p.parse_args();target=args.output.resolve();load_material()
    if not target.is_relative_to((ROOT/'results').resolve()) or target.suffix!='.json':p.error('JSON output must stay inside results/')
    if target.exists() or not args.worker and (target.with_suffix('.md').exists() or (target.parent/(target.stem+'-artifacts')).exists()):p.error('use a new output path; preserve prior failures')
    target.parent.mkdir(parents=True,exist_ok=True)
    if args.worker:asyncio.run(worker(target));return 0
    write_report(target,build_report())
    if args.capture:
        # The worker alone strips environment keys before importing application code.
        env={k:v for k,v in os.environ.items() if 'KEY' not in k and 'TOKEN' not in k};env.update(LUOJIA_NO_DOTENV='1',PYTHONUTF8='1')
        target.unlink()  # only this newly created no-run output; prior user reports are rejected above
        try:
            done=subprocess.run([sys.executable,str(Path(__file__)),'--offline','--worker','--output',str(target)],cwd=ROOT,env=env,capture_output=True,timeout=180)
            if done.returncode:
                target.with_suffix('.error.log').write_bytes(done.stderr)
        except subprocess.TimeoutExpired:
            done=None
        data=load_json(target) if target.exists() else build_report()
        if done is None or done.returncode:
            data['capture_status']='failed_or_timeout';data['failures'].append({'track':'capture','code':'BUDGET_STOP' if done is None else 'PROTOCOL'})
    else:data=build_report()
    legacy=None
    if args.legacy_report:
        verify_r5(args.legacy_report);legacy=load_json(args.legacy_report)
        if not legacy.get('r64_routing_adapter') or not legacy.get('capture_sources_unchanged'):raise ValueError('need versioned R64 routing capture with unchanged sources')
    browser=load_json(args.browser_receipt) if args.browser_receipt else None
    merged=build_report(data['records']['exploration'],data['records']['private'],legacy,browser)
    merged['capture_status']=data.get('capture_status','completed' if args.capture else 'not_run')
    merged['capture_sources_unchanged']=data.get('capture_sources_unchanged')
    merged['failures'].extend(f for f in data.get('failures',[]) if f.get('track')=='capture')
    verify_artifacts([*merged['records']['exploration'],*merged['records']['private']],target)
    write_report(target,merged)
    print(json.dumps({'report':str(target),'E1':'not_run','quality':None,'r7':merged['r7_decision']['verdict'],'failures':len(merged['failures'])}))
    return 0 if not merged['failures'] else 1


if __name__=='__main__':raise SystemExit(main())
