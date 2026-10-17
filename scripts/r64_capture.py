"""R6.4 offline adapters over existing exploration APIs and compiled Chat workflow."""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch
from r5_quality import ROOT, sha
from s5_quality import load_json, digest

OWNER='r64-synthetic'
BODY='离线固定回复，仅检查编排。请核对本题条件与计算范围；此回复不提供模型数学成绩。'
MEMORY_RULE='仅在personal_context有相关选取时联系旧判断，保留原话、修订、来源和计算范围；私人意见不补成本题已知条件；没有选取时不提旧记忆。'


def isolate():
    for key in list(os.environ):
        if 'KEY' in key or 'TOKEN' in key or key.startswith(('LLM_','MINERU_','DATABASE_','COURSE_')):os.environ.pop(key,None)
    os.environ['LUOJIA_NO_DOTENV']='1';sys.path.insert(0,str(ROOT/'apps/api'))


@contextmanager
def offline_network():
    import httpx
    from starlette.testclient import _TestClientTransport
    denied=[];original=httpx.Client.send
    def send(client, request, *args, **kwargs):
        if isinstance(client._transport,_TestClientTransport) and request.url.host=='testserver':return original(client,request,*args,**kwargs)
        denied.append('HTTP');raise RuntimeError('R64 external HTTP prohibited')
    def block(*args,**kwargs):denied.append('socket');raise RuntimeError('R64 external network prohibited')
    async def async_block(*args,**kwargs):denied.append('async_HTTP');raise RuntimeError('R64 external HTTP prohibited')
    with patch.object(httpx.Client,'send',send),patch.object(httpx.AsyncClient,'send',async_block),patch.object(socket.socket,'connect',block),patch.object(socket,'create_connection',block):yield denied


@contextmanager
def workspace():
    from app.config import Settings
    from app.knowledge.course_store import CourseStore
    from app.knowledge.course_service import CourseService
    from app.memory.repository import Repository
    from app.tutor.learning_workspace import LearningWorkspace
    with tempfile.TemporaryDirectory(prefix='r64-') as directory:
        settings=Settings(database_url=f"sqlite:///{Path(directory)/'sessions.db'}",llm_api_key='offline-fixture',
                          typed_math_tools_enabled=False,teaching_decision_enabled=True)
        w=LearningWorkspace(CourseService(store=CourseStore(str(Path(directory)/'course.db'))),Repository(settings))
        w.repository.ensure_user(OWNER)
        try:yield w,settings
        finally:w.store.close()


def fixed_decision():
    return {'claim_ref':'claim:current','evidence_refs':['claim:current'],'known_conditions':[],
            'missing_conditions':['本题主张成立所需的条件'],'claim_status':'unknown','action':'ask_missing_condition',
            'disclosure':'scaffolded','reason':BODY,'assessments':[],'experiment_proposal':None}


def fixture_plan(domain,claim):
    cases=load_json(ROOT/'evaluation/r63/cases.json')['cases']
    p=deepcopy(next(c['plan'] for c in cases if c['id']==domain));p['claim_to_test']=claim
    if domain=='integration':
        for task,n in zip(p['tasks'],(4,6)):task.update(expression='sin(8*pi*x)^2',intervals=n,limit=1,tolerance=1e-6)
        p.update(question_to_test='改变初始网格检查振荡混叠',observable='近似值、细分估计与求值次数',
                 mathematical_reason='同一光滑振荡函数在不同网格下可能出现混叠；数值对照不证明严格界。')
    return p


def save_artifact(output, group, id, value):
    path=output.parent/(output.stem+'-artifacts')/group/(id+'.json');path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'artifact_ref':path.relative_to(output.parent).as_posix(),'artifact_sha256':digest(path)}


async def capture_explorations(cases, output):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api import routes_explorations
    from app.auth import Principal,get_principal
    from app.main_deps import get_app_settings,get_learning_workspace
    from app.llm.openai_compatible import OpenAICompatibleClient
    rows=[]
    for case in cases:
        row={'case_id':case['id'],'domain':case['domain'],'role':case['role'],'input_sha256':case['input_sha256'],
             'evidence_source':'fixed_fixture','status':'failed','quality':None,'usage':None,'actual_cost':None,'provider_requests':0}
        with workspace() as (w,settings):
            denied=[]
            app=FastAPI();app.include_router(routes_explorations.router)
            for dep,value in ((get_app_settings,settings),(get_learning_workspace,w),(get_principal,Principal(OWNER,True))):app.dependency_overrides[dep]=(lambda v=value:lambda:v)()
            calls=[]
            async def model(self,messages,**kwargs):
                if calls:raise RuntimeError('one fixture generation per exploration')
                result={'decision':fixed_decision(),'suggested_graph':{'nodes':[],'edges':[]},'follow_up':BODY}
                if case['fixture_plan_case']:
                    result['decision'].update(action='offer_experiment',experiment_proposal=fixture_plan(case['domain'],case['prompt']))
                raw=json.dumps(result,ensure_ascii=False);calls.append({'messages':deepcopy(messages),'kwargs':kwargs,'output':raw,'input_sha256':sha(messages)})
                return raw
            try:
                with patch.object(OpenAICompatibleClient,'chat_completion',model),TestClient(app) as client,offline_network() as denied:
                    value=client.post('/api/explorations',json={'request_id':case['id'],'title':'R64工程夹具','claim':case['prompt']}).json()
                    response=client.post(f"/api/explorations/{case['id']}/advice",json={'expected_revision':value['revision']})
                    advice=response.json();row.update(http_status=response.status_code,advice_status=advice.get('status'),model_calls=len(calls))
                    if response.status_code!=200 or advice.get('status')!='suggested_not_executed':raise ValueError('advice protocol unavailable')
                    plan=advice['decision'].get('experiment_proposal');runs=[]
                    if plan:
                        execution=client.post(f"/api/explorations/{case['id']}/runs",json={'request_id':'fixture-confirmed','expected_revision':advice['exploration']['revision'],
                            'tasks':plan['tasks'],'plan':plan,'prediction':'采集器参数检查，不是学生预测','metrics':['value'] if case['domain']=='integration' else ['residual'],'confirmed':True})
                        if execution.status_code!=200:raise ValueError('runner rejected proposed parameters')
                        runs=execution.json()['history'][-1]['payload']['runs']
                    artifact={'case':case,'model_calls':calls,'advice':advice,'runs':runs,'confirmation_origin':'offline_harness_not_student','network_denied':denied}
                    row.update(status='completed',plan_offered=plan is not None,real_local_runner_count=len(runs),**save_artifact(output,'explorations',case['id'],artifact))
            except Exception as exc:
                row.update(failure_code='PROTOCOL',failure_type=type(exc).__name__,failure_detail=str(exc)[:200],
                           **save_artifact(output,'explorations',case['id'],{'calls':calls,'failure':str(exc),'network_denied':denied}))
            if denied:row.update(status='failed',failure_code='PROTOCOL',network_denied=denied)
        rows.append(row)
    return rows


def seed_history(w,domain,stale):
    from app.tutor.explorations import Explorations,Create,EditGraph,PersonalGraph,Execute,Revise
    from app.tutor.learning_workspace import digest as content_hash
    source=next(c for c in load_json(ROOT/'evaluation/r63/cases.json')['cases'] if c['id']==domain)
    names={'gs':('严格行对角占优','GS收敛'),'newton':('初值','Newton收敛'),'integration':('误差估计','严格误差界')}[domain]
    note_session=w.repository.create_session(OWNER,'数值分析')['session_id']
    note_id=w.repository.save_note(OWNER,note_session,'原条件','R64合成来源；非教材事实')
    # IDs and dates are fixed across paired databases; no prior-arm response is shared.
    with w.repository.connect() as db:db.execute('update notes set id=? where id=?',('r64-source',note_id))
    service=Explorations(w)
    v=service.create(OWNER,Create(request_id='prior',title=domain,claim=source['claim']))
    graph={'nodes':[{'id':'premise','label':names[0],'source_ref':{'kind':'note','note_id':'r64-source','source_hash':content_hash('R64合成来源；非教材事实')}},{'id':'conclusion','label':names[1]}],
           'edges':[{'id':'relation','source':'premise','target':'conclusion','relation':'related','reason':'我曾忽略适用条件，需要结合修订再检查'}]}
    v=service.update(OWNER,'prior','graph',EditGraph(request_id='graph',expected_revision=1,graph=PersonalGraph.model_validate(graph)))
    v=service.update(OWNER,'prior','run',Execute(request_id='prior-run',expected_revision=2,tasks=source['plan']['tasks'],prediction=source['prediction'],metrics=['value'] if domain=='integration' else ['residual'],confirmed=True))
    v=service.update(OWNER,'prior','revise',Revise(request_id='revise',expected_revision=3,claim=source['revised_claim'],reason=source['revision_reason']))
    if stale:
        with w.repository.connect() as db:db.execute('update notes set content=? where id=?',('已变更，旧哈希失效','r64-source'))
    def fixed_dates(item):
        if isinstance(item,list):return [fixed_dates(x) for x in item]
        if isinstance(item,dict):return {k:('2026-10-17T00:00:00+00:00' if k in {'at','created_at','updated_at','decided_at'} else fixed_dates(v)) for k,v in item.items()}
        return item
    history={kind:fixed_dates(w.store.learning_records(OWNER,w.course_id,kind)) for kind in ('exploration','lab','numerical_lab')}
    for kind,records in history.items():
        for record in records:w.save(OWNER,kind,record['id'],record)
    history['notes']=[{'id':n['id'],'content':n['content'],'subject':n['subject']} for n in w.repository.list_notes(OWNER)]
    return history


def normalize_prompt(messages):
    result=deepcopy(messages)
    for m in result:
        for marker in ('RUNTIME_CONTEXT','NODE_CONTEXT'):
            prefix=f'[{marker}]\n';suffix=f'\n[/{marker}]'
            if not isinstance(m.get('content'),str) or not m['content'].startswith(prefix):continue
            value=json.loads(m['content'][len(prefix):-len(suffix)])
            if marker=='RUNTIME_CONTEXT':value.pop('personal_context',None)
            else:
                bundle=(value.get('teaching_decision') or {}).get('sources')
                if bundle:
                    bundle.pop('source_hash',None);bundle['sources']=[s for s in bundle['sources'] if not s['id'].startswith('personal:')]
            m['content']=prefix+json.dumps(value,ensure_ascii=False,sort_keys=True)+suffix
    return result


async def capture_private_pairs(output):
    from app.tutor.orchestrator import TutorOrchestrator
    import app.tutor.personal_recall as recall
    rows=[];original_selector=recall.select_personal_context
    questions={'gs':'什么是GS收敛条件？严格行对角占优怎样使用？','newton':'什么是Newton收敛条件？初值怎样影响？','integration':'什么是积分误差估计？它与严格误差界有什么区别？'}
    unrelated={'gs':questions['newton'],'newton':questions['integration'],'integration':questions['gs']}
    for domain in questions:
        for scenario in ('related','unrelated','stale_source'):
            for enabled in (False,True):
                id=f'{domain}-{scenario}';arm='P1' if enabled else 'P0'
                row={'case_id':id,'arm':arm,'domain':domain,'scenario':scenario,'evidence_source':'fixed_fixture','status':'failed','quality':None,'usage':None,'actual_cost':None,'provider_requests':0}
                with workspace() as (w,settings),offline_network() as denied:
                    calls=[]
                    try:
                        history=seed_history(w,domain,scenario=='stale_source');row['history_sha256']=sha(history)
                        question=unrelated[domain] if scenario=='unrelated' else questions[domain];row['input_sha256']=hashlib.sha256(question.encode()).hexdigest()
                        tutor=TutorOrchestrator(settings,w.repository);workflow=tutor.workflow_owner
                        async def no_hits(*a,**kw):return None,0.0
                        workflow.context_collector._collect_local_hits=no_hits
                        workflow.schedule_semantic_enrichment=lambda *a,**kw:None
                        base=workflow._build_base_messages
                        def shared_prompt(*args,**kwargs):
                            messages=base(*args,**kwargs)
                            for m in messages:
                                if m.get('role')=='developer' and m['content'].startswith('[RUNTIME_CONTEXT]\n'):
                                    value=json.loads(m['content'].split('\n',1)[1].rsplit('\n',1)[0]);value.setdefault('personal_context',[]);value['personal_recall_rule']=MEMORY_RULE
                                    m['content']='[RUNTIME_CONTEXT]\n'+json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n[/RUNTIME_CONTEXT]'
                            return messages
                        workflow._build_base_messages=shared_prompt
                        async def model(messages,*args,**kwargs):
                            if calls:raise RuntimeError('one fixture generation per private arm')
                            d=fixed_decision();raw='[TEACHING_DECISION]'+json.dumps(d,ensure_ascii=False)+'[/TEACHING_DECISION][OUTPUT]'+BODY
                            calls.append({'messages':deepcopy(messages),'configuration':kwargs,'output':raw});return raw
                        workflow._collect_model_response=model
                        session=w.repository.create_session(OWNER,'数值分析')['session_id']
                        with patch.object(recall,'select_personal_context',original_selector if enabled else lambda *a,**kw:[]),patch('app.knowledge.course_service.get_course_service',return_value=w.course),patch('app.knowledge.targeted_retrieval.infer_target_goal',return_value=None):
                            events=[e async for e in tutor.stream_reply(session,OWNER,question,learning_workspace=w,reasoning_effort='off')]
                        saved=w.repository.list_messages(session)[-1];meta=saved.get('learning_meta') or {};selected=meta.get('personal_context',[])
                        if not calls or not any('event: done\n' in e for e in events) or any('event: error\n' in e for e in events):raise ValueError('Chat did not complete controlled generation')
                        if bool(selected)!=(enabled and scenario=='related'):raise ValueError('unexpected selection for scenario')
                        artifact={'question':question,'history':history,'selected_context':selected,'model_calls':calls,'sse':events,'saved':saved,
                                  'network_denied':denied,'quality':None,'scope':'fixture_orchestration_only'}
                        row.update(status='completed',selected_count=len(selected),model_calls=len(calls),
                            model='same-neutral-offline-fixture-v1',generation_sha256=sha({'effort':'off','max_requests':1,'max_output_tokens':1536}),
                            normalized_prompt_sha256=sha(normalize_prompt(calls[0]['messages'])),
                            prompt_sha256=sha(calls[0]['messages']),response_sha256=hashlib.sha256(saved['content'].encode()).hexdigest(),
                            **save_artifact(output,'private',id+'-'+arm,artifact))
                    except Exception as exc:
                        row.update(failure_code='PROTOCOL',failure_type=type(exc).__name__,failure_detail=str(exc)[:200],
                                   **save_artifact(output,'private',id+'-'+arm,{'calls':calls,'failure':str(exc),'network_denied':denied}))
                    if denied:row.update(status='failed',network_denied=denied)
                rows.append(row)
    return rows
