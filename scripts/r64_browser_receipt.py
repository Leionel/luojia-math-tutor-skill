"""Bind actual Playwright CLI observations and screenshots; never human scores."""
import argparse
import json
from pathlib import Path
from r5_quality import ROOT
from s5_quality import digest
from r64_quality import build_report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();target=args.output.resolve()
    if target.exists() or not target.is_relative_to(ROOT/'results'):parser.error('new results output required')
    raw=args.log.read_bytes();text=raw.decode('utf-16' if raw[:2]==b'\xff\xfe' else 'utf-8-sig').replace('\r\n','\n')
    data=json.loads(text.split('### Result\n',1)[1].split('\n### Ran',1)[0])
    # CLI output is a declaration of observed automation, not an attestation system.
    data['source_sha256']={p.relative_to(ROOT).as_posix():digest(p) for p in [
        *sorted((ROOT/'apps/web/app').rglob('*.tsx')),*sorted((ROOT/'apps/web/components').rglob('*.tsx')),
        *sorted((ROOT/'apps/web/lib').glob('*.ts')),*sorted((ROOT/'scripts').glob('r64_ui*.cjs')),
        ROOT/'scripts/r61_ui_fixture.py',ROOT/'scripts/r3_ui_fixture.py']}
    log=args.log.resolve().relative_to(ROOT).as_posix()
    for task in data['tasks']:
        task['artifact_refs']=[{'path':p,'sha256':digest(ROOT/p)} for p in [*task['artifact_refs'],log]]
    build_report(browser=data)
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'tasks':[(t['task_id'],t['status']) for t in data['tasks']],'human_participants':0}))


if __name__=='__main__':main()
