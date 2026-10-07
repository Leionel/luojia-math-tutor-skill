"""S5.2 owned ASGI episodes, synthetic identities and fixed responses; no live network."""
from __future__ import annotations
import hashlib,json,os,sys,tempfile,socket
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCENARIOS={
 'episode-newton-reference':'Newton saved reference -> discussion -> preview -> explicit save -> new reference; stale/owner/help guards',
 'episode-linear-revision':'Numerical chat residual discussion -> revised candidate -> restored per-turn metadata and no learning grades',
}
STAGES={
 'episode-newton-reference':['context_loaded','reply_saved','preview_created','preview_retry','explicit_save','save_retry','new_reference','stale_rejected','owner_rejected','help_locked','reference_not_graded'],
 'episode-linear-revision':['first_reply_saved','second_reply_saved','two_user_turns_preserved','per_turn_input_bound','responses_distinct','saved_meta_matches_sse','no_learning_grade'],
}


def capture(manifest_path:Path,output:Path):
    for key in list(os.environ):
        if 'KEY' in key or 'TOKEN' in key or key.startswith(('LLM_','MINERU_','DATABASE_','COURSE_')):os.environ.pop(key,None)
    os.environ['LUOJIA_NO_DOTENV']='1'
    sys.path.insert(0,str(ROOT/'apps/api'))
    import httpx
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from starlette.testclient import _TestClientTransport
    from app.auth import Principal,get_principal
    from app.config import Settings
    from app.memory.repository import Repository
    from app.knowledge.course_store import CourseStore
    from app.knowledge.course_service import CourseService
    import app.knowledge.course_service as courses
    from app.tutor.learning_workspace import LearningWorkspace
    from app.tutor.learning_context import LearningContextRef
    from app.tutor.orchestrator import TutorOrchestrator
    from app.math_tools.root_runner import LabRequest
    from app.api import routes_tutor
    from app.main_deps import get_learning_workspace,get_orchestrator,get_app_settings
    from s5_quality import load_json,digest,validate_manifest
    original_send=httpx.Client.send
    def send(client,request,*args,**kwargs):
        if isinstance(client._transport,_TestClientTransport) and request.url.host=='testserver':
            return original_send(client,request,*args,**kwargs)
        raise RuntimeError('offline episodes prohibit outbound HTTP')
    async def deny_async(*a,**kw):raise RuntimeError('offline episodes prohibit outbound HTTP')
    httpx.Client.send=send;httpx.AsyncClient.send=deny_async
    manifest=load_json(manifest_path);cases=validate_manifest(manifest)
    if manifest['split']!='runner_fixture' or {c['id'] for c in cases}!=set(SCENARIOS):
        raise ValueError('only the two public episode fixtures may execute')
    records=[]
    def parse_events(text):
        result=[]
        for block in text.replace('\r\n','\n').split('\n\n'):
            name=None;parts=[]
            for line in block.splitlines():
                if line.startswith('event:'):name=line[6:].strip()
                elif line.startswith('data:'):parts.append(line[5:].lstrip())
            if name and parts:result.append((name,json.loads('\n'.join(parts))))
        return result
    for case in cases:
        ident=case['id']
        if hashlib.sha256(SCENARIOS[ident].encode()).hexdigest()!=case['input_sha256']:raise ValueError('scenario hash mismatch')
        with tempfile.TemporaryDirectory(prefix='s5-episode-') as temp:
            folder=Path(temp);settings=Settings(database_url=f"sqlite:///{folder/'student.db'}",llm_api_key='',typed_math_tools_enabled=False)
            repo=Repository(settings);course=CourseService(store=CourseStore(str(folder/'course.db')))
            courses.get_course_service=lambda *a,**kw:course
            try:
                ws=LearningWorkspace(course,repo);owner='s5-episode-student'
                clean=repo.list_mastery(owner)==[] and repo.list_user_mistakes(owner)==[] and ws.store.learning_records(owner,ws.course_id,'lab')==[]
                session=repo.create_session(owner,'数值分析')['session_id'];tutor=TutorOrchestrator(settings,repo)
                async def no_hits(*a,**kw):return None,0.0
                tutor.workflow_owner.context_collector._collect_local_hits=no_hits
                tutor.workflow_owner.schedule_semantic_enrichment=lambda *a,**kw:None
                fixed={'text':'[OUTPUT] 固定离线参考讨论。旧快照保留旧参数；可以预览新初值后明确保存。参考实验不代表学生独立作答；你观察到了什么？'}
                async def stream(*a,**kw):yield {'type':'content','content':fixed['text']}
                async def review(*a,**kw):return '{"verified":false,"is_correct":null,"error_step":null,"reason":"固定离线fixture","summary":"非确定性审查占位"}'
                tutor.workflow_owner.llm.stream=stream;tutor.workflow_owner.llm.chat_completion=review;tutor.llm.chat_completion=review
                app=FastAPI();app.include_router(routes_tutor.router)
                actor={'id':owner}
                app.dependency_overrides[get_principal]=lambda:Principal(actor['id'],True,'student')
                app.dependency_overrides[get_learning_workspace]=lambda:ws
                app.dependency_overrides[get_orchestrator]=lambda:tutor
                app.dependency_overrides[get_app_settings]=lambda:settings
                stages=[];run_refs=[];response_hashes=[];turn_hashes=[]
                def stage(name,passed,status):
                    stages.append({'id':name,'passed':bool(passed),'http_status':status})
                def ref(run):
                    return LearningContextRef(kind='root_lab',record_id=run['id'],**{k:run[k] for k in ('input_hash','runner_version','graph_revision')}).model_dump()
                def reply(client,message,context=None):
                    payload={'session_id':session,'user_id':owner,'message':message,'subject':'calculus' if context else 'linear_algebra'}
                    if context:payload['learning_context']=context
                    result=client.post('/api/tutor/stream',json=payload)
                    events=parse_events(result.text)
                    saved=repo.list_messages(session)[-1]
                    metas=[data for name,data in events if name in {'meta','meta_update'}]
                    ok=result.status_code==200 and any(name=='done' for name,_ in events) and not any(name=='error' for name,_ in events) and saved['role']=='assistant' and bool(metas)
                    response_hashes.append(hashlib.sha256(saved['content'].encode()).hexdigest())
                    turn_hashes.append(hashlib.sha256(message.encode()).hexdigest())
                    run=metas[-1].get('agent_run',{}) if metas else {}
                    run_refs.append(run.get('run_id') or run.get('id') or 'missing-run')
                    return result,saved,metas[-1] if metas else {},ok
                with TestClient(app) as client:
                    # TestClient creates its in-process event loop before connections are denied.
                    original_connect=socket.socket.connect;original_create=socket.create_connection
                    def deny_connect(*a,**kw):raise RuntimeError('offline episodes prohibit sockets')
                    socket.socket.connect=deny_connect;socket.create_connection=deny_connect
                    try:
                        if ident=='episode-newton-reference':
                            initial=ws.lab(owner,LabRequest(attempt={'method':'newton','function':'x^3-2*x+2','initial_value':0,'goal':'residual'},max_iterations=10,prediction='合成fixture观察循环',request_id='episode-initial'))
                            context=ref(initial)
                            got=client.post('/api/tutor/context',json=context)
                            stage('context_loaded',got.status_code==200 and got.json()['ref']==context,got.status_code)
                            response,saved,meta,ok=reply(client,'请根据这个已保存的实验解释轨迹，给我参数预览入口。',context)
                            stage('reply_saved',ok and {k:v for k,v in saved['learning_meta'].items() if k!='agent_run'}=={k:v for k,v in meta.items() if k!='agent_run'},response.status_code)
                            proposals=meta.get('tutor_artifacts') or []
                            if not proposals:raise ValueError('episode did not deliver a guarded server proposal')
                            proposal=proposals[0];base=f"/api/tutor/sessions/{session}/messages/{saved['id']}/artifacts/{proposal['artifact_id']}"
                            payload={'context':context,'parameters':{**proposal['parameters'],'initial_value':-2.0},'request_id':'episode-preview'}
                            p=client.post(base+'/preview',json=payload);preview=p.json()
                            stage('preview_created',p.status_code==200 and abs(preview['rows'][1]['x']-(-1.8))<1e-12 and len(ws.store.learning_records(owner,ws.course_id,'lab'))==1,p.status_code)
                            retry=client.post(base+'/preview',json=payload)
                            stage('preview_retry',retry.status_code==200 and retry.json()==preview and len(ws.store.learning_records(owner,ws.course_id,'lab_preview'))==1,retry.status_code)
                            savebody={'context':context,'preview_id':preview['id'],'preview_hash':preview['input_hash'],'observation':'合成用户显式确认：改变初值后回看轨迹；不计独立成绩。'}
                            s=client.post(base+'/save',json=savebody);new=s.json()
                            stage('explicit_save',s.status_code==200 and new['rows']==preview['rows'] and new.get('linked_preview_id')==preview['id'],s.status_code)
                            retry=client.post(base+'/save',json=savebody)
                            stage('save_retry',retry.status_code==200 and retry.json()==new and len(ws.store.learning_records(owner,ws.course_id,'lab'))==2,retry.status_code)
                            ctxnew=ref(new);got=client.post('/api/tutor/context',json=ctxnew)
                            stage('new_reference',got.status_code==200 and got.json()['parameters']['initial_value']==-2 and got.json()['ref']['record_id']!=context['record_id'],got.status_code)
                            stale=client.post('/api/tutor/context',json={**ctxnew,'input_hash':'0'*64})
                            stage('stale_rejected',stale.status_code==409,stale.status_code)
                            actor['id']='other-student';other=client.get(base);actor['id']=owner
                            stage('owner_rejected',other.status_code==404,other.status_code)
                            assessment=ws.new_assessment(owner);locked=client.post('/api/tutor/context',json=ctxnew)
                            stage('help_locked',locked.status_code==409,locked.status_code);ws.end_assessment(owner,assessment['id'])
                            stage('reference_not_graded',new['independent_success'] is False and repo.list_mastery(owner)==[] and repo.list_user_mistakes(owner)==[] and meta.get('is_correct') is None,200)
                        else:
                            first='A=[[3,1],[1,2]]，b=[5,5]，我算 x=[1,2]。如何核对残差？'
                            second='我把候选 x 改成 [1,1]，请按刚才的 A 和 b 重新核对残差，并说明能确认什么。'
                            fixed['text']='[OUTPUT] 固定离线回复：按 r=Ax-b，原候选[1,2]的残差为[0,0]。这只是代回证据；一般零残差不单独证明唯一性。本例若要说唯一，还需det(A)=5。自动单步核验未覆盖矩阵方程；不计独立成绩。'
                            a,saved1,meta1,ok1=reply(client,first)
                            stage('first_reply_saved',ok1,a.status_code)
                            fixed['text']='[OUTPUT] 固定离线回复：对修改后的[1,1]，Ax=[4,3]，按r=Ax-b得到[-1,-2]，不是原候选的零残差。这里是说明性的精确代回，没有宣称调用工具；自动单步核验未确认你的矩阵候选。'
                            b,saved2,meta2,ok2=reply(client,second)
                            stage('second_reply_saved',ok2,b.status_code)
                            restored=repo.list_messages(session)
                            users=[m['content'] for m in restored if m['role']=='user']
                            stage('two_user_turns_preserved',users==[first,second],200)
                            steps=[meta1.get('step_check',{}),meta2.get('step_check',{})]
                            stage('per_turn_input_bound',[hashlib.sha256(message.encode()).hexdigest() for message in users]==turn_hashes and len(set(turn_hashes))==2,200)
                            stage('responses_distinct',len(set(response_hashes))==2,200)
                            stage('saved_meta_matches_sse',all({k:v for k,v in old.items() if k!='agent_run'}=={k:v for k,v in observed.items() if k!='agent_run'} for old,observed in [(saved1['learning_meta'],meta1),(saved2['learning_meta'],meta2),(restored[-1]['learning_meta'],meta2)]),200)
                            stage('no_learning_grade',repo.list_mastery(owner)==[] and repo.list_user_mistakes(owner)==[] and all(not s.get('eligible_learning_evidence') for s in steps),200)
                    finally:
                        socket.socket.connect=original_connect;socket.create_connection=original_create
                records.append({'case_id':ident,'input_sha256':case['input_sha256'],'run_status':'completed','evidence_source':'fixed_fixture',
                    'response_sha256':hashlib.sha256(json.dumps(response_hashes).encode()).hexdigest(),'run_ref':ident,
                    'episode_facts':{'isolated_initial_state':clean,'actual_runs':len(run_refs),'run_refs':run_refs,'turn_input_hashes':turn_hashes,
                        'stages':stages,'confirmation_origin':'synthetic_user_http_request','content_review':'pending'}})
            finally:course.store.close()
    result={'version':'s5-observations-v1','manifest_sha256':digest(manifest_path),
        'capture_provenance':{'kind':'owned_offline_episode_fixture','network':'denied','database':'fresh_temp_per_case','model_response':'fixed',
            'persistence':'asgi_stream_saved_by_orchestrator','source_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT/'apps/api/app').rglob('*.py'))}},'records':records}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('manifest and output paths required')
    capture(Path(sys.argv[1]),Path(sys.argv[2]))
