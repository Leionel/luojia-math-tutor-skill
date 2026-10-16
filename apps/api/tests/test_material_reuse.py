"""R5.1 offline vertical contracts; neither parser nor model reaches a provider."""
from unittest.mock import AsyncMock
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.api import routes_uploads, routes_learning, routes_notes, routes_tutor, routes_search, routes_sessions
from app.auth import Principal, get_principal
from app.config import Settings
from app.knowledge.course_service import CourseService
from app.knowledge.course_store import CourseStore
from app.main_deps import get_repository, get_app_settings, get_learning_workspace
from app.memory.repository import Repository
from app.tutor.learning_workspace import LearningWorkspace, digest
from app.tutor.help_boundary import assert_reference_help_allowed
from app.llm.openai_compatible import OpenAICompatibleClient

SOURCE = "# 第一章\n学生原始说明，数学内容未审核。\n\n# 第二章\n差商具有有限极限。\n\n# 附录\n不应进入第二章上下文的独立标记。"

@pytest.fixture
def materials(tmp_path, monkeypatch):
    repo=Repository(Settings(database_url=f"sqlite:///{tmp_path / 'materials.db'}"))
    course=CourseService(store=CourseStore(str(tmp_path/'course.db')))
    workspace=LearningWorkspace(course,repo)
    for user in ('alice','bob'): repo.ensure_user(user)
    app=FastAPI()
    for module in (routes_uploads,routes_learning,routes_notes,routes_tutor,routes_search,routes_sessions):app.include_router(module.router)
    app.dependency_overrides[get_principal]=lambda:Principal('alice',True)
    app.dependency_overrides[get_repository]=lambda:repo
    app.dependency_overrides[get_learning_workspace]=lambda:workspace
    app.dependency_overrides[get_app_settings]=lambda:Settings(auth_required=True)
    monkeypatch.setattr(routes_learning,'workspace',lambda:workspace)
    def guard(owner):
        try:assert_reference_help_allowed(owner,course)
        except ValueError as exc:raise HTTPException(409,str(exc)) from exc
    monkeypatch.setattr(routes_uploads,'ensure_reference_help_allowed',guard)
    monkeypatch.setattr(routes_notes,'ensure_reference_help_allowed',guard)
    monkeypatch.setattr(routes_uploads,'UPLOAD_DIR',tmp_path/'uploads')
    parser=AsyncMock(return_value=SOURCE);model=AsyncMock(return_value='# 抽样笔记\n依据原文。')
    monkeypatch.setattr(routes_uploads,'extract_markdown_agent_api',parser)
    monkeypatch.setattr(OpenAICompatibleClient,'chat_completion',model)
    with TestClient(app) as client:yield client,app,repo,workspace,parser,model
    course.store.close()

def upload(client):
    return client.post('/api/uploads',files={'file':('讲义.pdf',b'%PDF-1.4\n/Type /Page ','application/pdf')})

def reference(client,document_id):
    doc=client.get(f'/api/reading/documents/{document_id}').json()
    section=next(s for s in doc['sections'] if '# 第二章' in s['quote'])
    return dict(kind='reading',source_id=document_id,source_hash=doc['source_hash'],section_id=section['id'],start=0,end=len(section['quote']),graph_revision=None)

def test_one_parse_reused_for_reading_chat_scope_and_note(materials):
    client,_,repo,workspace,parser,model=materials
    response=upload(client);assert response.status_code==200
    doc=response.json()['document_id'];ref=reference(client,doc)
    assert repo.get_document_markdown(doc,'alice')==SOURCE and repo.list_document_chunks(doc)
    assert not repo.list_notes('alice') and not repo.list_user_mistakes('alice')
    assert client.get('/api/uploads/documents').json()['documents'][0]['parse_status']=='ready'
    snap=client.post('/api/tutor/context',json=ref);assert snap.status_code==200
    assert '差商具有有限极限' in snap.json()['citation']['quote'] and '独立标记' not in snap.json()['citation']['quote']
    assert snap.json()['content_review_status']=='uploaded_unreviewed'
    note=client.post('/api/users/alice/notes/from-document',json={'document_id':doc,'source_hash':ref['source_hash']})
    assert note.status_code==200
    assert note.json()['source']['source_hash']==digest(SOURCE)
    assert note.json()['source']['coverage']=='heading_outline_and_sampled_body'
    assert repo.list_notes('alice')[0]['session_id']==f'document:{doc}'
    assert 'luojia-document-source' in repo.list_notes('alice')[0]['content']
    assert parser.await_count==1 and model.await_count==1

def test_note_failure_keeps_source_and_no_false_note(materials):
    client,_,repo,_,parser,model=materials;doc=upload(client).json()['document_id']
    model.side_effect=RuntimeError('offline failure')
    assert client.post('/api/users/alice/notes/from-document',json={'document_id':doc}).status_code==503
    model.side_effect=None;model.return_value=' '
    assert client.post('/api/users/alice/notes/from-document',json={'document_id':doc}).status_code==502
    assert repo.get_document_markdown(doc,'alice')==SOURCE and not repo.list_notes('alice')
    assert client.get(f'/api/reading/documents/{doc}').status_code==200 and parser.await_count==1

def test_owner_hash_bounds_missing_and_deleted_source(materials):
    client,app,repo,_,_,model=materials;doc=upload(client).json()['document_id'];ref=reference(client,doc)
    app.dependency_overrides[get_principal]=lambda:Principal('bob',True)
    assert client.get('/api/uploads/documents').json()['documents']==[]
    assert client.get(f'/api/reading/documents/{doc}').status_code==404
    assert client.post('/api/tutor/context',json=ref).status_code==404
    assert client.post('/api/users/bob/notes/from-document',json={'document_id':doc}).status_code==404
    app.dependency_overrides[get_principal]=lambda:Principal('alice',True)
    assert client.post('/api/tutor/context',json={**ref,'source_hash':'0'*64}).status_code==409
    assert client.post('/api/tutor/context',json={**ref,'end':6001}).status_code in (409,422)
    assert client.post('/api/users/alice/notes/from-document',json={'document_id':doc,'source_hash':'0'*64}).status_code==409
    assert model.await_count==0
    old=repo.insert_document('legacy.pdf','alice')
    assert client.get(f'/api/reading/documents/{old}').status_code==409
    assert next(x for x in client.get('/api/uploads/documents').json()['documents'] if x['id']==old)['parse_status']=='source_missing'
    with repo.connect() as conn:conn.execute('delete from documents where id=?',(doc,))
    assert client.post('/api/tutor/context',json=ref).status_code==404
    app.dependency_overrides[get_principal]=lambda:Principal('alice',False)
    assert client.get('/api/uploads/documents').status_code==401

@pytest.mark.parametrize('failure',['exception','empty','storage'])
def test_parse_and_atomic_store_failures_leave_no_document(materials,failure):
    client,_,repo,_,parser,model=materials
    if failure=='exception':parser.side_effect=RuntimeError('parser timeout')
    elif failure=='empty':parser.return_value=' \n'
    else:
        with repo.connect() as conn:conn.execute("create trigger reject_upload before insert on uploaded_files begin select raise(ABORT, 'disk fixture'); end")
    assert upload(client).status_code in (502,503)
    assert repo.list_documents('alice')==[] and model.await_count==0
    with repo.connect() as conn:assert conn.execute('select count(*) from document_chunks').fetchone()[0]==0

def test_assessment_blocks_upload_read_context_and_note(materials):
    client,_,repo,workspace,parser,model=materials;doc=upload(client).json()['document_id'];ref=reference(client,doc)
    workspace.new_assessment('alice')
    assert client.get(f'/api/reading/documents/{doc}').status_code==409
    assert client.post('/api/tutor/context',json=ref).status_code==409
    assert client.post('/api/users/alice/notes/from-document',json={'document_id':doc}).status_code==409
    assert upload(client).status_code==409 and parser.await_count==1 and model.await_count==0

def test_assessment_started_during_parse_rejects_save(materials):
    client,_,repo,workspace,parser,_=materials
    async def late(_):workspace.new_assessment('alice');return SOURCE
    parser.side_effect=late
    assert upload(client).status_code==409 and repo.list_documents('alice')==[]


@pytest.mark.asyncio
async def test_selected_document_range_reaches_chat_and_persisted_receipt(materials, monkeypatch):
    from app.tutor.orchestrator import TutorOrchestrator
    from app.tutor.learning_context import ReadingContextRef
    client,_,repo,workspace,parser,_=materials
    document_id=upload(client).json()['document_id']
    ref=ReadingContextRef(**reference(client,document_id))
    session=repo.create_session('alice','数值分析')['session_id']
    tutor=TutorOrchestrator(Settings(database_url=f'sqlite:///{repo.db_path}'),repo)
    workflow=tutor.workflow_owner
    async def no_hits(*args,**kwargs):return None
    monkeypatch.setattr(workflow.context_collector,'_course_graph_pack',no_hits)
    monkeypatch.setattr(workflow.context_collector,'_budgeted_local_pack',no_hits)
    prompts=[]
    async def reply(messages,*args,**kwargs):
        prompts.append(messages)
        return '给定选段说明差商有有限极限；请进一步核对可导的定义。'
    monkeypatch.setattr(workflow,'_collect_model_response',reply)
    events=[e async for e in tutor.stream_reply(session,'alice','为什么需要有限极限？',learning_context=ref,learning_workspace=workspace)]
    assert any('event: done' in e for e in events)
    prompt='\n'.join(m['content'] for turn in prompts for m in turn)
    assert '差商具有有限极限' in prompt and '独立标记' not in prompt
    saved=repo.list_messages(session)
    assert saved[0]['content']=='为什么需要有限极限？'
    assert saved[-1]['learning_meta']['learning_context']['ref']==ref.model_dump()
    assert len(saved[-1]['learning_meta']['learning_context']['citation']['quote'])<=6000
    assert parser.await_count==1


def test_search_preserves_history_content_lookup_and_hides_source_metadata(materials):
    client,app,repo,_,_,_=materials
    session=repo.create_session('alice','数学','标题没有检索词')['session_id']
    repo.add_message(session,'user','会话内容唯一检索词R51')
    result=client.get('/api/sessions',params={'user_id':'alice','q':'唯一检索词R51'})
    assert [item['id'] for item in result.json()['items']]==[session]
    document_id=upload(client).json()['document_id']
    generated=client.post('/api/users/alice/notes/from-document',json={'document_id':document_id})
    source_hash=generated.json()['source']['source_hash']
    notes=client.get('/api/search/global',params={'q':'抽样','category':'notes'}).json()['items']
    assert notes and all('luojia-document-source' not in n['content'] and source_hash not in n['content'] for n in notes)
    app.dependency_overrides[get_principal]=lambda:Principal('bob',True)
    assert client.get('/api/sessions',params={'user_id':'bob','q':'唯一检索词R51'}).json()['items']==[]
    assert client.get('/api/search/global',params={'q':'抽样','category':'notes'}).json()['items']==[]
