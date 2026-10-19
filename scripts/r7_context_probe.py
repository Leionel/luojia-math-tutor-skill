"""Measure existing context behavior; never manufacture a ContextPlan benefit."""
import argparse
import asyncio
import json
from pathlib import Path
from r5_quality import ROOT
from r64_capture import isolate, seed_history, OWNER
from r7_native_capture import capture_case, protocol_fixture
from r7_quality import ReviewedReplayPolicy, write
from s5_quality import digest


async def capture(target):
    rows=[]
    for name,question in (
        ('long_session','Newton 初值怎样影响局部收敛条件？'),
        ('similar_concepts','Newton 导数为零时为什么不能更新？'),
        ('conflicting_sources','Newton 任意初值都能收敛吗？请核对初值条件。'),
    ):
        def seed(w):
            history=seed_history(w,'newton',False)
            if name=='conflicting_sources':
                from app.tutor.explorations import Explorations,Revise
                s=Explorations(w);v=s.get(OWNER,'prior')
                s.update(OWNER,'prior','revise',Revise(request_id='student-dissent',expected_revision=v['revision'],
                    claim='我仍猜测Newton任意初值都收敛',reason='学生与课程条件意见相反，未经数学审核'))
                history['exploration']=w.store.learning_records(OWNER,w.course_id,'exploration')
            return history
        case=dict(id=name,prompt=question)
        if name=='long_session':
            case['prior_turns']=[dict(role='user' if i%2==0 else 'assistant',
                content=f'历史轮次{i}：'+('合成背景，不构成数学事实。'*150)) for i in range(30)]
        path=target.parent/(target.stem+'-artifacts')/(name+'.json');path.parent.mkdir(parents=True,exist_ok=True)
        result=await capture_case(case,path,policy=ReviewedReplayPolicy(max_output_tokens=1536),
            underlying=protocol_fixture(),key='offline-fixture',setup=seed,native_tools=False)
        meta=(result.get('saved') or {}).get('learning_meta') or {}
        rows.append(dict(case_id=name,status=result['status'],selected_context=meta.get('personal_context',[]),
            model_payload_bytes=[len(json.dumps(c['payload'],ensure_ascii=False).encode()) for c in result['calls']],
            local_warmup_ms=result.get('pair_local_retrieval_warmup_ms'),
            actual_input_tokens=None,condition_completeness_rating=None,independent_math_reviewed=False,
            artifact_ref=path.relative_to(target.parent).as_posix(),artifact_sha256=digest(path)))
    data=dict(version='r7-existing-context-measurement-v1',records=rows,provider_requests=0,
        conclusion='bounded source views measured; no demonstrated truncation-related mathematical failure; no new ContextPlan/RAG call',
        model_quality=None)
    write(target,data);return data


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    target=a.output.resolve()
    if not target.is_relative_to(ROOT/'results') or target.exists() or (target.parent/(target.stem+'-artifacts')).exists():p.error('new results output required')
    isolate();target.parent.mkdir(parents=True,exist_ok=True);data=asyncio.run(capture(target))
    print(json.dumps([(r['case_id'],r['status'],len(r['selected_context'])) for r in data['records']]))
