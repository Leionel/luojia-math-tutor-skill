"""Owned offline D0/D1/D2 application captures. This entry point cannot call a provider."""
import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

from r5_quality import ROOT,load_cases,sha,report,markdown,verify_artifacts
from s5_quality import load_json,digest

PROMPT='你是数学助教。检查学生的原始主张，保留正确的局部步骤，指出最早的问题。区分缺少条件与结论错误，无法确定时说明还需要什么。先给针对性提示，不将模型意见称为严格核验。'
BODY='固定离线回复，仅用于采集编排和来源。请区分当前步骤、整体结论和仍未给出的条件；本 fixture 不提供数学质量评分。'


def events(text):
    result=[]
    for block in text.replace('\r\n','\n').split('\n\n'):
        name=None;parts=[]
        for line in block.splitlines():
            if line.startswith('event:'):name=line[6:].strip()
            elif line.startswith('data:'):parts.append(line[5:].lstrip())
        if name and parts:result.append({'event':name,'data':json.loads('\n'.join(parts))})
    return result


def worker(material_path,output,selected):
    for key in list(os.environ):
        if 'KEY' in key or 'TOKEN' in key or key.startswith(('LLM_','MINERU_','DATABASE_','COURSE_')):os.environ.pop(key,None)
    os.environ['LUOJIA_NO_DOTENV']='1'
    sys.path.insert(0,str(ROOT/'apps/api'))
    from unittest.mock import patch
    import httpx
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from starlette.testclient import _TestClientTransport
    from app.auth import Principal,get_principal
    from app.config import Settings
    from app.main_deps import get_app_settings,get_learning_workspace,get_orchestrator
    from app.memory.repository import Repository
    from app.knowledge.course_service import CourseService
    from app.knowledge.course_store import CourseStore
    from app.math_tools.verifier import VerifyResult
    from app.tutor.learning_workspace import LearningWorkspace
    from app.tutor.orchestrator import TutorOrchestrator
    from app.api import routes_tutor
    import app.tutor.graph as graph
    material=load_cases(material_path)
    arms=load_json(ROOT/'evaluation/r5/arms-v1.json')
    capture_sources={str(Path(__file__)):digest(Path(__file__)),str(ROOT/'scripts/r5_quality.py'):digest(ROOT/'scripts/r5_quality.py'),
        str(material_path):digest(material_path),str(ROOT/'evaluation/r5/arms-v1.json'):digest(ROOT/'evaluation/r5/arms-v1.json')}
    selected_cases=[c for c in material['cases'] if not selected or c['id'] in selected]
    if selected and {c['id'] for c in selected_cases}!=set(selected):raise ValueError('unknown case selection')
    records=[];denied=[]
    original_send=httpx.Client.send
    def send(client,request,*a,**kw):
        if isinstance(client._transport,_TestClientTransport) and request.url.host=='testserver':return original_send(client,request,*a,**kw)
        denied.append('outbound_http');raise RuntimeError('R5 offline capture prohibits HTTP')
    async def deny_async(*a,**kw):denied.append('outbound_async_http');raise RuntimeError('R5 offline capture prohibits HTTP')
    def deny_socket(*a,**kw):denied.append('outbound_socket');raise RuntimeError('R5 offline capture prohibits socket')
    for case in material['cases']:
        for arm in ('D0','D1','D2'):
            row={'case_id':case['id'],'arm':arm,'input_sha256':case['input_sha256'],'rubric_sha256':case['rubric_sha256'],
                'evidence_source':'fixed_fixture','status':'not_run','fixture_model':arms['model_label'],
                'fixture_body_sha256':hashlib.sha256(BODY.encode()).hexdigest(),'generation_hash':sha(arms['generation']),
                'budget_hash':sha({k:v for k,v in arms['generation'].items() if 'max_' in k or 'timeout' in k}),
                'usage':None,'actual_cost':None,'response_text':None,'response_sha256':None,'model_calls':[],
                'not_run_reason':'not_selected','fairness_intervention':arms['arms'][arm]}
            records.append(row)
            if case not in selected_cases:continue
            started=time.monotonic()
            with tempfile.TemporaryDirectory(prefix='r5-run-') as temp:
                folder=Path(temp);settings=Settings(database_url=f"sqlite:///{folder/'student.db'}",llm_api_key='',typed_math_tools_enabled=False,teaching_decision_enabled=arm=='D2')
                repo=Repository(settings);course=CourseService(store=CourseStore(str(folder/'course.db')))
                try:
                    owner='r5-synthetic-student';ws=LearningWorkspace(course,repo)
                    initial={'mastery':repo.list_mastery(owner),'mistakes':repo.list_user_mistakes(owner),'sessions':repo.list_sessions(owner)}
                    row['fresh_state']=all(not value for value in initial.values());row['fresh_state_hash']=sha(initial)
                    session=repo.create_session(owner,case['subject'])['session_id']
                    tutor=TutorOrchestrator(settings,repo);workflow=tutor.workflow_owner
                    workflow.schedule_semantic_enrichment=lambda *a,**kw:None
                    originals=[];receipts=[]
                    collect=workflow.context_collector.collect
                    async def capture_context(state):
                        if arm=='D0':state['verification_mode']='none'
                        value=await collect(state)
                        receipts.append(asdict(value.verifier_result))
                        if arm!='D2':state['verification_mode']='none'
                        return value
                    workflow.context_collector.collect=capture_context
                    if arm!='D2':
                        async def no_hits(*a,**kw):return None,0.0
                        workflow.context_collector._collect_local_hits=no_hits
                        def ordinary(state,history,hits,chunks,verifier,*args,**kwargs):
                            messages=[{'role':'system','content':PROMPT},{'role':'user','content':state['message']}]
                            if arm=='D1':messages.insert(1,{'role':'system','content':'当前有限数学检查回执（仅按范围解释）：'+json.dumps(asdict(verifier),ensure_ascii=False)})
                            return messages
                        workflow._build_base_messages=ordinary
                    async def fixture(messages,*args,**kwargs):
                        if len(row['model_calls'])>=arms['generation']['max_model_calls_per_run']:raise RuntimeError('fixture_call_budget_exceeded')
                        original=deepcopy(messages);originals.append(original)
                        # Structured fixture tests protocol plumbing, not a model's decision ability.
                        response='[OUTPUT] '+BODY
                        if arm=='D2':
                            node=next((m['content'] for m in reversed(messages) if m.get('role')=='developer' and '[NODE_CONTEXT]\n' in m['content']),None)
                            info=json.loads(node.split('[NODE_CONTEXT]\n',1)[1].split('\n[/NODE_CONTEXT]',1)[0]) if node else {}
                            disclosure=(info.get('teaching_decision') or {}).get('disclosure','scaffolded')
                            decision={'claim_ref':'claim:current','evidence_refs':[],'known_conditions':[],'missing_conditions':[],
                                'claim_status':'unknown','action':'explain','disclosure':disclosure,'reason':'固定fixture不裁决数学质量','assessments':[]}
                            response='[TEACHING_DECISION]'+json.dumps(decision,ensure_ascii=False)+'[/TEACHING_DECISION]'+response
                        row['model_calls'].append({'kind':'generation_fixture','input_messages':original,'input_sha256':sha(original),
                            'raw_output':response,'output_sha256':hashlib.sha256(response.encode()).hexdigest(),'usage':None,'provider_requests':0})
                        return response
                    async def review(messages,*a,**kw):
                        if len(row['model_calls'])>=arms['generation']['max_model_calls_per_run']:raise RuntimeError('fixture_call_budget_exceeded')
                        response='{"verified":false,"is_correct":null,"summary":"固定审查fixture：不产生数学真值"}'
                        row['model_calls'].append({'kind':'review_fixture','input_messages':deepcopy(messages),'input_sha256':sha(messages),'raw_output':response,'usage':None,'provider_requests':0})
                        return response
                    workflow._collect_model_response=fixture
                    workflow.llm.chat_completion=review;tutor.llm.chat_completion=review
                    app=FastAPI();app.include_router(routes_tutor.router)
                    for dep,value in ((get_principal,Principal(owner,True)),(get_app_settings,settings),(get_learning_workspace,ws),(get_orchestrator,tutor)):
                        app.dependency_overrides[dep]=(lambda v=value:lambda:v)()
                    from contextlib import ExitStack
                    with ExitStack() as stack:
                        stack.enter_context(patch('app.knowledge.course_service.get_course_service',return_value=course))
                        if arm!='D2':
                            for name in ('build_teacher_prompt','build_examiner_prompt'):
                                stack.enter_context(patch.object(graph,name,lambda state:state['messages']))
                            stack.enter_context(patch('app.tutor.proof_tutor.build_proof_tutor_prompt',lambda state:state['messages']))
                        with TestClient(app) as client:
                            stack.enter_context(patch.object(httpx.Client,'send',send));stack.enter_context(patch.object(httpx.AsyncClient,'send',deny_async))
                            stack.enter_context(patch.object(socket.socket,'connect',deny_socket));stack.enter_context(patch.object(socket,'create_connection',deny_socket))
                            response=client.post('/api/tutor/stream',json={'session_id':session,'user_id':owner,'message':case['prompt'],
                                'subject':case['subject'],'mode':'socratic','web_search_mode':'off','reasoning_effort':arms['generation']['reasoning_effort']})
                    captured=events(response.text);saved=repo.list_messages(session)
                    row['sse_events']=captured;row['http_status']=response.status_code
                    body=saved[-1] if saved else {}
                    row['response_text']=body.get('content','') if body.get('role')=='assistant' else ''
                    row['response_sha256']=hashlib.sha256(row['response_text'].encode()).hexdigest()
                    row['saved_metadata']=body.get('learning_meta') or {};row['tool_receipts']=receipts
                    row['status']='completed' if response.status_code==200 and row['response_text'] and any(e['event']=='done' for e in captured) and not any(e['event']=='error' for e in captured) else 'failed'
                    row['not_run_reason']=None
                    row['failure_events']=[e for e in captured if e['event']=='error']
                    row['learning_writes']={'mastery_rows':len(repo.list_mastery(owner)),'mistake_rows':len(repo.list_user_mistakes(owner))}
                except Exception as exc:
                    row['status']='failed';row['failure_type']=type(exc).__name__;row['failure_detail']=str(exc)[:300];row['not_run_reason']=None
                finally:
                    row['latency_ms']=round((time.monotonic()-started)*1000,2)
                    course.store.close()
            # Reuse S5's bounded reader: full per-run inputs live in hashed
            # artifacts instead of duplicating them in the aggregate report.
            artifact=output.parent/(output.stem+'-artifacts')/case['id']/(arm+'.json')
            artifact.parent.mkdir(parents=True,exist_ok=True)
            artifact.write_text(json.dumps(deepcopy(row),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            row['artifact_ref']=artifact.relative_to(output.parent).as_posix()
            row['artifact_sha256']=digest(artifact)
            row['sse_event_types']=[e['event'] for e in row.pop('sse_events',[])]
            meta=row.pop('saved_metadata',{})
            row['decision_status']=(meta.get('teaching_decision') or {}).get('status')
            for call in row['model_calls']:
                call.pop('input_messages',None)
                call['input_artifact_ref']=row['artifact_ref']
            row['latency_threshold_exceeded']=row['latency_ms']>arms['generation']['latency_observation_threshold_seconds']*1000
            # Save partial evidence after each run; failures are not dropped.
            output.write_text(json.dumps({'records':records,'capture_complete':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result=report(material,records)
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
    result.update(network_guard={'denied_attempts':denied,'successful_outbound_requests':0},arms_sha256=digest(ROOT/'evaluation/r5/arms-v1.json'),
        source_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT/'apps/api/app').rglob('*.py'))},
        capture_script_sha256=capture_sources[str(Path(__file__))],material_file_sha256=capture_sources[str(material_path)],capture_complete=True,
        capture_source_sha256={Path(p).relative_to(ROOT).as_posix():value for p,value in capture_sources.items()},
        capture_git_sha=revision.stdout.strip() if revision.returncode==0 else None,
        capture_sources_unchanged=all(digest(Path(p))==value for p,value in capture_sources.items()),
        caveats=['Synthetic Principal, no JWT acceptance','Fresh state does not test personalization','No real model or reviewed quality scores'])
    result['engineering_passed']=result['engineering_passed'] and not denied and result['capture_sources_unchanged']
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'results/r5/offline.json')
    parser.add_argument('--case',action='append',default=[])
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();target=args.output.resolve()
    if not target.is_relative_to((ROOT/'results').resolve()) or target.suffix!='.json':parser.error('output must be JSON inside results/')
    target.parent.mkdir(parents=True,exist_ok=True)
    material=ROOT/'evaluation/r5/cases-v1.json';load_cases(material)
    if args.worker:worker(material,target,args.case);return 0
    env={k:v for k,v in os.environ.items() if 'KEY' not in k and 'TOKEN' not in k}
    env.update(LUOJIA_NO_DOTENV='1',PYTHONUTF8='1')
    command=[sys.executable,str(Path(__file__)),'--offline','--worker','--output',str(target)]
    for case in args.case:command.extend(['--case',case])
    try:
        done=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
    except subprocess.TimeoutExpired:
        print('R5 capture timed out; partial records remain, no quality conclusion');return 2
    if done.returncode:
        (target.parent/'capture-error.log').write_bytes(done.stderr)
        print('R5 capture failed; inspect capture-error.log; no quality conclusion');return 2
    data=load_json(target)
    verify_artifacts(target)
    target.with_suffix('.md').write_text(markdown(data),encoding='utf-8')
    print(f"R5 fixed fixtures: {data['completed_runs']}/{data['planned_runs']} completed; capture_passed={data['engineering_passed']}; matched ablations={data['matched_ablation_cases']}/24; real quality scores=0")
    return 0 if data['engineering_passed'] else 1


if __name__=='__main__':raise SystemExit(main())
