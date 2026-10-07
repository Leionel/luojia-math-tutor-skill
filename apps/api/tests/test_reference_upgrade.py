"""U01-U03 reference scope, source binding, no-grade and read-only task contracts."""
from copy import deepcopy
from unittest.mock import AsyncMock
from pathlib import Path
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.config import Settings
from app.memory.repository import Repository
from app.knowledge.course_service import CourseService
from app.knowledge.course_store import CourseStore
from app.tutor.learning_workspace import LearningWorkspace,digest
from app.tutor.learning_context import LinearContextRef,ReadingContextRef,resolve_learning_context
from app.tutor.study_summary import read_study_summary,study_requested
from app.math_tools.numerical_lab import LinearTask,run_numerical
from app.tutor.orchestrator import TutorOrchestrator
from app.api import routes_tutor
from app.auth import Principal,get_principal
from app.main_deps import get_app_settings,get_learning_workspace,get_orchestrator

@pytest.fixture
def ws(tmp_path,monkeypatch):
    settings=Settings(database_url=f"sqlite:///{tmp_path/'student.db'}",llm_api_key='')
    repo=Repository(settings);course=CourseService(store=CourseStore(str(tmp_path/'course.db')))
    import app.knowledge.course_service as courses
    monkeypatch.setattr(courses,'get_course_service',lambda *a,**kw:course)
    work=LearningWorkspace(course,repo)
    yield work,settings
    course.store.close()


def linear(ws,id='linear-one',n=2):
    work,_=ws;matrix=[[4.0 if i==j else 0.1 for j in range(n)] for i in range(n)]
    task=LinearTask(matrix=matrix,rhs=[1.0]*n,initial=[0.0]*n,limit=100,tolerance=1e-12)
    value=run_numerical(task);value.update(id=id,source_hash=digest({'task':task.model_dump(),'id':id}),created_at='2026-10-07',prediction='synthetic')
    work.save('alice','numerical_lab',id,value)
    ref=LinearContextRef(kind='linear_lab',record_id=id,source_hash=value['source_hash'],schema_version=value['schema_version'])
    return value,ref


def course_ref(ws):
    work,_=ws;unit=work.reading_units()[0]
    return ReadingContextRef(kind='reading',source_id=unit['id'],source_hash=unit['source_hash'],section_id=None,start=0,end=min(len(unit['quote']),60),graph_revision=unit['graph_revision'])


def app_client(ws,monkeypatch,locked=False):
    work,settings=ws;tutor=TutorOrchestrator(settings,work.repository)
    tutor.workflow_owner.context_collector._collect_local_hits=AsyncMock(return_value=(None,0))
    tutor.workflow_owner.schedule_semantic_enrichment=lambda *a,**kw:None
    async def fixed_stream(*a,**kw):
        if locked:work.new_assessment('alice')
        yield {'type':'content','content':'[OUTPUT] 本轮只讨论服务端提供的来源，条件与范围仍需核对。参考帮助不是独立作答。你想确认哪一处？'}
    tutor.workflow_owner.llm.stream=fixed_stream
    tutor.workflow_owner.llm.chat_completion=AsyncMock(return_value='{"verified":false,"is_correct":null,"error_step":null,"reason":"fixture","summary":"未确认"}')
    app=FastAPI();app.include_router(routes_tutor.router)
    app.dependency_overrides[get_principal]=lambda:Principal('alice',True)
    app.dependency_overrides[get_learning_workspace]=lambda:work
    app.dependency_overrides[get_app_settings]=lambda:settings
    app.dependency_overrides[get_orchestrator]=lambda:tutor
    return TestClient(app),tutor


def parse(text):
    events=[]
    for b in text.replace('\r\n','\n').split('\n\n'):
        name=next((line[6:].strip() for line in b.splitlines() if line.startswith('event:')),None)
        data=next((line[5:].strip() for line in b.splitlines() if line.startswith('data:')),None)
        if name and data:events.append((name,json.loads(data)))
    return events


@pytest.mark.parametrize('n',[2,8])
def test_linear_snapshot_is_owned_bounded_and_keeps_inputs(ws,n):
    work,_=ws;run,ref=linear(ws,n=n)
    selected=min(4,len(run['rows'])-1);snapshot=resolve_learning_context(work,'alice',ref.model_copy(update={'selected_step':selected}))
    assert snapshot['task']==run['task'] and snapshot['conditions']==run['conditions']
    assert any(row['k']==selected for row in snapshot['rows'])
    assert len(snapshot['rows'])<=11 and snapshot['total_rows']-len(snapshot['rows'])==snapshot['omitted_rows']
    assert len(json.dumps(snapshot,ensure_ascii=False).encode())<=8192
    assert work.repository.list_mastery('alice')==[] and work.repository.list_user_mistakes('alice')==[]
    with pytest.raises(KeyError):resolve_learning_context(work,'bob',ref)


@pytest.mark.parametrize('change',['hash','index','schema','dimension','row','numeric','work','conditions','budget','delete'])
def test_linear_stale_corrupt_or_oversized_records_fail_closed(ws,change):
    work,_=ws;run,ref=linear(ws)
    if change=='hash':ref=ref.model_copy(update={'source_hash':'0'*64})
    elif change=='index':ref=ref.model_copy(update={'selected_step':100})
    elif change=='schema':run['schema_version']='other'
    elif change=='dimension':run['task']['rhs']=[1]
    elif change=='row':run['rows'][0]['k']=7
    elif change=='numeric':run['rows'][0]['vector'][0]=float('nan')
    elif change=='work':del run['rows'][0]['work']
    elif change=='conditions':del run['conditions']
    elif change=='budget':run['conditions']=['数据'*6000]
    elif change=='delete':ref=ref.model_copy(update={'record_id':'deleted'})
    with pytest.raises((ValueError,KeyError)):
        work.save('alice','numerical_lab',run['id'],run)
        resolve_learning_context(work,'alice',ref)


def test_reading_public_scope_and_extra_data_are_not_authority(ws,monkeypatch):
    work,_=ws;ref=course_ref(ws);unit=next(u for u in work.reading_units() if u['id']==ref.source_id)
    snapshot=resolve_learning_context(work,'alice',ref)
    assert snapshot['citation']['quote']==unit['quote'][:ref.end]
    for patch in [{'source_hash':'0'*64},{'graph_revision':'different'},{'section_id':'fake'},{'end':len(unit['quote'])+1}]:
        with pytest.raises(ValueError):resolve_learning_context(work,'alice',ref.model_copy(update=patch))
    client,_=app_client(ws,monkeypatch)
    assert client.post('/api/tutor/context',json={**ref.model_dump(),'quote':'forged source'}).status_code==422


def test_private_reading_uses_exact_span_owner_and_full_hash(ws,monkeypatch):
    work,_=ws
    documents={'alice':{'id':'document-one','filename':'same.md','source_hash':'1'*64,'sections':[{'id':'0','title':'原文','quote':'甲📘乙重复乙重复'}]}}
    def document(owner,id):
        if owner not in documents or id!='document-one':raise KeyError(id)
        return documents[owner]
    monkeypatch.setattr(work,'document',document)
    ref=ReadingContextRef(kind='reading',source_id='document-one',source_hash='1'*64,section_id='0',start=5,end=8)
    snap=resolve_learning_context(work,'alice',ref)
    assert snap['citation']['quote']=='乙重复'
    with pytest.raises(KeyError):resolve_learning_context(work,'bob',ref)
    with pytest.raises(ValueError):resolve_learning_context(work,'alice',ref.model_copy(update={'graph_revision':'invented'}))
    documents['alice']['source_hash']='2'*64
    with pytest.raises(ValueError):resolve_learning_context(work,'alice',ref)


@pytest.mark.parametrize('kind',['linear','reading'])
def test_new_context_sse_saved_and_no_math_grade_or_root_actions(ws,monkeypatch,kind):
    work,_=ws;ref=linear(ws)[1] if kind=='linear' else course_ref(ws)
    client,tutor=app_client(ws,monkeypatch);session=work.repository.create_session('alice','数值分析')['session_id']
    r=client.post('/api/tutor/stream',json={'session_id':session,'user_id':'alice','message':'请解释这份引用的范围','learning_context':ref.model_dump()})
    events=parse(r.text)
    assert r.status_code==200 and any(name=='done' for name,_ in events) and not any(name=='error' for name,_ in events)
    saved=work.repository.list_messages(session)[-1]['learning_meta']
    assert saved['learning_context']['ref']==ref.model_dump() and saved['is_correct'] is None
    assert not saved.get('tutor_artifacts') and not saved['step_check']['eligible_learning_evidence']
    assert work.repository.list_mastery('alice')==[] and work.repository.list_user_mistakes('alice')==[]
    tutor.workflow_owner.llm.chat_completion.assert_not_awaited()


@pytest.mark.parametrize('kind',['linear','reading'])
def test_help_lock_blocks_both_contexts_before_and_during_delivery(ws,monkeypatch,kind):
    work,_=ws;ref=linear(ws)[1] if kind=='linear' else course_ref(ws)
    client,_=app_client(ws,monkeypatch,True);session=work.repository.create_session('alice','数值分析')['session_id']
    r=client.post('/api/tutor/stream',json={'session_id':session,'user_id':'alice','message':'解释引用','learning_context':ref.model_dump()})
    events=parse(r.text)
    assert any(name=='error' for name,_ in events) and not any(name=='done' for name,_ in events)
    assert client.post('/api/tutor/context',json=ref.model_dump()).status_code==409
    assert work.repository.list_mastery('alice')==[]


def test_study_read_without_plan_is_model_free_and_does_not_create(ws,monkeypatch):
    work,_=ws;client,tutor=app_client(ws,monkeypatch);session=work.repository.create_session('alice','数值分析')['session_id']
    r=client.post('/api/tutor/stream',json={'session_id':session,'user_id':'alice','message':'今天学什么？','model':'unknown-model'})
    assert any(name=='done' for name,_ in parse(r.text))
    saved=work.repository.list_messages(session)[-1]['learning_meta']
    assert not saved['study_summary']['plan_exists'] and saved['step_check']['execution_status']=='not_requested'
    assert work.store.learning_records('alice',work.course_id,'plan')==[]
    tutor.workflow_owner.llm.chat_completion.assert_not_awaited()


def test_study_read_bound_stale_missing_locked_no_writes(ws,monkeypatch):
    work,_=ws;plan=work.plan('alice',15,'Asia/Hong_Kong')['plan'];id=plan['tasks'][0]['id']
    before=work.store.learning_records('alice',work.course_id,'task')
    summary=read_study_summary(work,'alice')
    assert summary['tasks'][0]['id']==id and read_study_summary(work,'bob')['tasks']==[]
    assert work.store.learning_records('alice',work.course_id,'task')==before
    task=work.get('alice','task',id);task['session_id']='not-owned';work.save('alice','task',id,task)
    assert read_study_summary(work,'alice')['tasks'][0]['state']=='session_unavailable'
    task['graph_revision']='outdated';work.save('alice','task',id,task)
    assert read_study_summary(work,'alice')['tasks'][0]['stale']
    work.new_assessment('alice');summary=read_study_summary(work,'alice')
    assert summary['help_locked'] and summary['tasks'][0]['title']=='当前任务（请回工作区作答）'
    assert all('challenge' not in row and 'reason' not in row for row in summary['tasks'])
    client,tutor=app_client(ws,monkeypatch);session=work.repository.create_session('alice','数值分析')['session_id']
    r=client.post('/api/tutor/stream',json={'session_id':session,'user_id':'alice','message':'继续上次任务'})
    assert any(name=='done' for name,_ in parse(r.text))
    assert work.repository.list_mastery('alice')==[]
    tutor.workflow_owner.llm.chat_completion.assert_not_awaited()


@pytest.mark.parametrize('message,expected',[('今天学什么？',True),('继续上次任务',True),('今天学什么，并证明x=1',False),('今天我算x²=2',False)])
def test_study_command_does_not_swallow_math(message,expected):assert study_requested(message) is expected

def test_previous_unfinished_task_is_read_without_creating_today_plan(ws):
    work,_=ws
    task={'id':'old-task','kind':'practice','state':'needs_revision','title':'待修订','graph_revision':work.revision(),'session_id':None}
    work.save('alice','task','old-task',task)
    summary=read_study_summary(work,'alice')
    assert not summary['plan_exists'] and summary['tasks'][0]['id']=='old-task'
    assert work.store.learning_records('alice',work.course_id,'plan')==[]


def test_missing_task_in_today_plan_stays_visible_as_unavailable(ws):
    work,_=ws;plan=work.plan('alice',15,'Asia/Hong_Kong')['plan'];id=plan['tasks'][0]['id']
    work.store._execute('DELETE FROM learning_records WHERE owner_id=? AND course_id=? AND kind=? AND record_id=?',('alice',work.course_id,'task',id))
    row=read_study_summary(work,'alice')['tasks'][0]
    assert row['id']==id and row['state']=='missing' and row['stale']


def test_reading_does_not_silently_truncate_oversized_quote(ws,monkeypatch):
    work,_=ws
    monkeypatch.setattr(work,'document',lambda *a:{'filename':'synthetic.md','source_hash':'1'*64,'sections':[{'id':'0','title':'source','quote':'文'*5000}]})
    ref=ReadingContextRef(kind='reading',source_id='doc-budget',source_hash='1'*64,section_id='0',start=0,end=5000)
    with pytest.raises(ValueError,match='8KiB'):resolve_learning_context(work,'alice',ref)


def test_task_action_cannot_be_mixed_with_reference_or_forged_summary(ws,monkeypatch):
    work,_=ws;client,tutor=app_client(ws,monkeypatch);session=work.repository.create_session('alice','数值分析')['session_id']
    payload={'session_id':session,'user_id':'alice','message':'今天学什么','study_action':'current_tasks'}
    assert client.post('/api/tutor/stream',json={**payload,'learning_context':course_ref(ws).model_dump()}).status_code==422
    assert client.post('/api/tutor/stream',json={**payload,'study_summary':{'plan_exists':True}}).status_code==422
    assert work.store.learning_records('alice',work.course_id,'plan')==[]
