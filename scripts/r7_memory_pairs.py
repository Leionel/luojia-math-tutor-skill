"""Same-history private on/off capture through native ASGI with fixed wire replies."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from r5_quality import ROOT, sha
from r64_capture import isolate, seed_history, normalize_prompt
from r7_quality import ReviewedReplayPolicy, write
from r7_native_capture import capture_case, protocol_fixture
from s5_quality import digest


async def capture(target):
    rows=[]
    for scenario, question in (
        ('paraphrase', '牛顿法换个出发点会怎样？'),
        ('same_method_unrelated', 'Newton 导数为零时为什么不能更新？'),
        ('stale_source', 'Newton 换初值还需要什么条件？'),
    ):
        pair=[]
        for enabled in (False,True):
            arm='on' if enabled else 'off'; case=dict(id=scenario+'-'+arm,prompt=question)
            path=target.parent/(target.stem+'-artifacts')/(case['id']+'.json');path.parent.mkdir(parents=True,exist_ok=True)
            data=await capture_case(case,path,policy=ReviewedReplayPolicy(max_output_tokens=1536),
                underlying=protocol_fixture(),key='offline-fixture',
                setup=lambda w:seed_history(w,'newton',scenario=='stale_source'),memory_enabled=enabled,native_tools=False)
            meta=(data.get('saved') or {}).get('learning_meta') or {}
            row=dict(scenario=scenario,arm=arm,status=data['status'],
                selected=meta.get('personal_context',[]),history_sha256=sha(data['history']),
                normalized_inputs_sha256=sha([normalize_prompt(c['payload']['messages']) for c in data['calls']]),
                model_reply_sha256=sha([c['response'] for c in data['calls']]),
                input_utf8_bytes=sum(len(json.dumps(c['payload'],ensure_ascii=False).encode()) for c in data['calls']),
                saved_decision=meta.get('teaching_decision'),
                actual_behavior=(data.get('saved') or {}).get('content'),
                artifact_ref=path.relative_to(target.parent).as_posix(),artifact_sha256=digest(path),
                provider_requests=0,quality=None,token_usage=None)
            rows.append(row);pair.append(row)
        pair[0]['input_projection_matched']=pair[1]['input_projection_matched']=(
            pair[0]['normalized_inputs_sha256']==pair[1]['normalized_inputs_sha256'] and
            pair[0]['history_sha256']==pair[1]['history_sha256'])
    report=dict(version='r7-memory-native-wire-pairs-v1',records=rows,
        scope='protocol and context intervention; fixed neutral replies; no model-quality benefit',
        controlled='same shared memory rule; tools disabled both arms; native routing/client/retrieval/guard/save retained',
        matched_pairs=sum(r['arm']=='on' and r['input_projection_matched'] for r in rows),
        quality_delta=None,confidence_interval=None,independent_math_reviewed=False,provider_requests=0)
    write(target,report);return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    target=a.output.resolve()
    if (not target.is_relative_to(ROOT/'results') or target.exists()
            or (target.parent/(target.stem+'-artifacts')).exists()):p.error('new results output required')
    isolate();target.parent.mkdir(parents=True,exist_ok=True);data=asyncio.run(capture(target))
    print(json.dumps({'matched_pairs':data['matched_pairs'],'rows':len(data['records']),'quality_delta':None}))


if __name__=='__main__':main()
