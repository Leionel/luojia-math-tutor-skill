"""Owned, offline runtime capture: fixed replies, real graph/worker, separate SQLite per case."""
from __future__ import annotations
import asyncio
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
MESSAGES={
 'runtime-correct':'我算 d(x²)/dx=2x，对吗？',
 'runtime-incorrect':'我算 d(sin(x^2))/dx=cos(x^2)，对吗？',
 'runtime-reference':'帮我检查求导 x**2',
 'runtime-unknown':'x 为正数，sqrt(x²)=x 对吗？',
}


def no_network(*args,**kwargs):
    raise RuntimeError('offline runtime capture prohibits network')


async def capture(manifest_path: Path, output: Path):
    # This executable runs only in an owned child, before any app/config import.
    for key in list(os.environ):
        if 'KEY' in key or 'TOKEN' in key or key.startswith(('LLM_', 'MINERU_', 'DATABASE_', 'COURSE_')):
            os.environ.pop(key,None)
    os.environ['LUOJIA_NO_DOTENV']='1'
    sys.path.insert(0,str(ROOT/'apps/api'))
    import httpx
    async def deny_async(*a,**kw):no_network()
    httpx.Client.send=no_network
    httpx.AsyncClient.send=deny_async
    socket.create_connection=no_network
    socket.socket.connect=no_network
    from app.config import Settings
    from app.memory.repository import Repository
    from app.knowledge.course_service import CourseService
    from app.knowledge.course_store import CourseStore
    import app.knowledge.course_service as courses
    from app.tutor.fast_path import route_fast_path
    from app.tutor.graph import TutorWorkflow
    from app.tutor.orchestrator import TutorOrchestrator
    from app.math_tools.verifier import VerifyResult
    from s5_quality import digest, load_json, validate_manifest
    manifest=load_json(manifest_path)
    cases=validate_manifest(manifest)
    if manifest['split']!='runner_fixture' or {c['id'] for c in cases}!=set(MESSAGES):
        raise ValueError('runtime capture only supports its four public synthetic fixtures')
    records=[]
    for case in cases:
        message=MESSAGES[case['id']]
        if case['input_sha256']!=hashlib.sha256(message.encode()).hexdigest():
            raise ValueError('runtime fixture message hash mismatch')
        with tempfile.TemporaryDirectory(prefix='s5-case-') as temp:
            folder=Path(temp)
            settings=Settings(database_url=f"sqlite:///{folder/'student.db'}",llm_api_key='',typed_math_tools_enabled=False)
            repository=Repository(settings)
            course=CourseService(store=CourseStore(str(folder/'course.db')))
            courses.get_course_service=lambda *a,**kw:course
            try:
                session=repository.create_session('s5-synthetic-student','calculus')
                initial_messages=len(repository.list_messages(session['session_id']))
                initial_mastery=repository.get_mastery('s5-synthetic-student','导数')
                writes={'mastery':0,'mistake':0}
                original_mastery=repository.upsert_mastery
                original_mistake=repository.add_mistake_event
                def mastery(*a,**kw):
                    writes['mastery']+=1
                    return original_mastery(*a,**kw)
                def mistake(*a,**kw):
                    writes['mistake']+=1
                    return original_mistake(*a,**kw)
                repository.upsert_mastery=mastery
                repository.add_mistake_event=mistake
                workflow=TutorWorkflow(settings,repository)
                async def no_hits(*a,**kw):return None,0.0
                workflow.context_collector._collect_local_hits=no_hits
                async def fixed_stream(*a,**kw):
                    yield {'type':'content','content':'[OUTPUT] 固定离线回复，仅用于执行链路采集。本步范围请看检查记录；参考计算不是你的独立作答。你用了什么条件？'}
                async def fixed_review(*a,**kw):
                    return '{"verified":false,"is_correct":null,"error_step":null,"reason":"固定fixture不评模型质量","summary":"范围尚未确认"}'
                workflow.llm.stream=fixed_stream
                workflow.llm.chat_completion=fixed_review
                route=route_fast_path(message,mode='socratic',subject='calculus')
                state={'message':message,'session_id':session['session_id'],'user_id':'s5-synthetic-student',
                    'subject':'calculus','mode':'socratic','user_api_key':None,'model':None,'requested_hint':False,
                    'image_urls':None,'intent':route.intent,'detected_subject':route.subject,
                    'pedagogical_action':route.pedagogical_action,'learning_objective':route.learning_objective,
                    'verification_mode':route.verification_mode.value,'confidence':route.confidence,
                    'requires_policy_fallback':route.requires_policy_fallback,'hits':[],'document_chunks':[],
                    'verifier_result':VerifyResult(False,None,'未请求检查'),'verification_result':{},'mistake':None,
                    'concepts':[],'mastery_score':.5,'mastery_delta':0.0,'mastery_label_str':'一般','hint_level':0,
                    'messages':[],'thinking_steps':[],'final_output':'','thinking_chain':'',
                    'metrics':{'llm_call_count':0,'route':''}}
                async def event(*a,**kw):return None
                final=await asyncio.wait_for(workflow.workflow.ainvoke(state,config={'configurable':{
                    'thread_id':session['session_id'],'on_token':event,'on_thinking':event,'on_progress':event}}),20)
                meta=TutorOrchestrator._build_learning_meta(final)
                repository.add_message(session['session_id'],'assistant',final['final_output'],learning_meta=meta)
                restored=repository.list_messages(session['session_id'])[-1]['learning_meta']
                step=meta['step_check']
                records.append({'case_id':case['id'],'input_sha256':case['input_sha256'],'run_status':'completed',
                    'evidence_source':'fixed_fixture','response_sha256':hashlib.sha256(final['final_output'].encode()).hexdigest(),
                    'run_ref':case['id'],'runtime_facts':{
                        'isolated_initial_state':initial_messages==0 and initial_mastery is None,
                        'metadata_restored_equal':restored['step_check']==step,
                        'input_bound':step['input_hash']==case['input_sha256'],
                        'execution_status':step['execution_status'],'origin':step['origin'],'scope':step['scope'],
                        'is_correct':final['verifier_result'].is_correct,'eligible_learning_evidence':step['eligible_learning_evidence'],
                        'mastery_writes':writes['mastery'],'mistake_writes':writes['mistake'],
                        'route':str(final['metrics'].get('route','unknown'))}})
            finally:
                course.store.close()
    source_files=sorted((ROOT/'apps/api/app').rglob('*.py'))
    result={'version':'s5-observations-v1','manifest_sha256':digest(manifest_path),
        'capture_provenance':{'kind':'owned_offline_graph_fixture','network':'denied','database':'fresh_temp_per_case',
                              'model_response':'fixed','persistence':'graph metadata projection saved by harness',
                              'source_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in source_files}},
        'records':records}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('manifest and output paths required')
    asyncio.run(capture(Path(sys.argv[1]),Path(sys.argv[2])))
