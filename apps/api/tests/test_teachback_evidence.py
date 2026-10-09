import json
from copy import deepcopy
from unittest.mock import AsyncMock
import pytest
from app.api.routes_learning import TeachBackRequest
from app.tutor.learning_extensions import create_teach_back,model_teach_back
from app.tutor.teachback_evidence import original_spans,parse_review
from app.tutor.learning_context import TeachBackContextRef,resolve_learning_context
from app.tutor.prompt_builder import build_messages
from app.tutor.intent_router import Intent
from app.math_tools.verifier import VerifyResult
from app.tutor.orchestrator import TutorOrchestrator
from app.config import Settings
from test_orchestrator import parse_event
from app.llm.openai_compatible import OpenAICompatibleClient
from test_reference_upgrade import ws


def teach(ws,id='teach1',text='📘导数不能为零；但不是所有初值都保证局部收敛。',parent=None):
    unit=next(u for u in ws[0].reading_units() if u['id']=='NA_NEWTON')
    return create_teach_back(ws[0],'alice',TeachBackRequest(request_id=id,unit_id=unit['id'],source_hash=unit['source_hash'],text=text,evidence={0:'导数不能为零'},parent_id=parent))


def payload(result):
    return {'opinions':[{'condition_id':r['condition_id'],'judgment':'unknown','evidence':None,'note':'无法确认这条条件的解释是否完整。','followup':'请补一句该条件不满足时会怎样。'} for r in result['conditions']]}


def test_original_spans_keep_unicode_repeated_text_and_old_version(ws):
    text='📘导数不能为零；导数不能为零。';first=teach(ws,text=text)
    spans=first['conditions'][0]['student_spans']
    assert len(spans)==2 and spans[0]['start']==1
    assert all(text[s['start']:s['end']]==s['quote'] for s in spans)
    child=teach(ws,'teach2',text+'初值还须足够接近。',first['id'])
    assert child['parent_id']==first['id'] and ws[0].get('alice','teach_back',first['id'])==first
    assert first['content_review_status']=='development_card' and not child['independent_success']


@pytest.mark.parametrize('invalid',['forged_quote','outside','missing_condition','duplicate','no_support_span','unknown_id','extra_grade'])
def test_model_judgment_requires_real_quote_and_complete_condition_set(ws,invalid):
    result=teach(ws);data=payload(result)
    if invalid in {'forged_quote','outside'}:data['opinions'][0]['evidence']={'start':0,'end':999 if invalid=='outside' else 1,'quote':'伪造'}
    if invalid=='missing_condition':data['opinions'].pop()
    if invalid=='duplicate':data['opinions'].append(data['opinions'][0])
    if invalid=='no_support_span':data['opinions'][0]['judgment']='supported'
    if invalid=='unknown_id':data['opinions'][0]['condition_id']='other-source:0'
    if invalid=='extra_grade':data['grade']=100
    with pytest.raises(ValueError):parse_review(json.dumps(data),result)


def test_paraphrase_and_negation_are_not_keyword_scores(ws):
    result=teach(ws);data=payload(result)
    start=result['text'].index('但不是')
    data['opinions'][1].update(judgment='supported',evidence={'start':start,'end':len(result['text']),'quote':result['text'][start:]})
    parsed=parse_review(json.dumps(data),result)
    assert parsed[result['conditions'][1]['condition_id']]['verified'] is False
    assert parsed[result['conditions'][1]['condition_id']]['evidence']['quote'].startswith('但不是')


def test_selected_condition_chat_reference_is_owner_scoped_and_unverified(ws):
    saved=teach(ws)
    ref=TeachBackContextRef(kind='teach_back',record_id=saved['id'],source_hash=saved['source_hash'],
        condition_hash=saved['condition_hash'],graph_revision=saved['graph_revision'],
        condition_id=saved['conditions'][0]['condition_id'])
    snapshot=resolve_learning_context(ws[0],'alice',ref)
    assert snapshot['student_text']==saved['text']
    assert snapshot['condition']['student_spans']==saved['conditions'][0]['student_spans']
    assert snapshot['model_status']=='self_review' and snapshot['independent_success'] is False
    with pytest.raises(KeyError):resolve_learning_context(ws[0],'bob',ref)
    with pytest.raises(ValueError):resolve_learning_context(ws[0],'alice',ref.model_copy(update={'condition_hash':'b'*64}))
    with pytest.raises(ValueError):resolve_learning_context(ws[0],'alice',ref.model_copy(update={'condition_id':'NA_NEWTON:99'}))
    prompt=build_messages('tutor','这条条件我该怎么补充？',Intent.CONCEPT,'数值分析',[],
        VerifyResult(False,None,'本轮未触发自动验证。'),None,'socratic',learning_context=snapshot)
    runtime=prompt[-2]['content']
    assert 'teach_back_rule' in runtime and '未经真人核验' in runtime
    assert ws[0].repository.list_mastery('alice')==[]


@pytest.mark.asyncio
async def test_teach_back_condition_stream_keeps_source_and_does_not_grade(ws,monkeypatch):
    workspace=ws[0]
    saved=teach(ws)
    ref=TeachBackContextRef(kind='teach_back',record_id=saved['id'],source_hash=saved['source_hash'],
        condition_hash=saved['condition_hash'],graph_revision=saved['graph_revision'],
        condition_id=saved['conditions'][0]['condition_id'])
    session=workspace.repository.create_session('alice','数值分析')['session_id']
    tutor=TutorOrchestrator(Settings(database_url=f'sqlite:///{workspace.repository.db_path}'),workspace.repository)
    workflow=tutor.workflow_owner
    async def no_hits(*args,**kwargs):return None
    monkeypatch.setattr(workflow.context_collector,'_course_graph_pack',no_hits)
    monkeypatch.setattr(workflow.context_collector,'_budgeted_local_pack',no_hits)
    prompts=[]
    async def response(messages,*args,**kwargs):
        prompts.extend(messages)
        return '请解释导数在迭代点为零时为什么不能直接使用更新式。'
    monkeypatch.setattr(workflow,'_collect_model_response',response)
    events=[parse_event(item) async for item in tutor.stream_reply(session,'alice','请围绕这项条件追问。',
        learning_context=ref,learning_workspace=workspace)]
    assert any(name=='done' for name,_ in events)
    assert 'teach_back_rule' in '\n'.join(item['content'] for item in prompts)
    meta=tutor.repository.list_messages(session)[-1]['learning_meta']
    assert meta['learning_context']['ref']==ref.model_dump()
    assert meta['learning_context']['condition']['student_quote']=='导数不能为零'
    assert meta['verified'] is False and meta['is_correct'] is None and meta['mastery_delta']==0
    assert workspace.repository.list_mastery('alice')==[]


@pytest.mark.asyncio
async def test_review_persists_bound_unverified_feedback_and_no_grade(ws,monkeypatch):
    result=teach(ws);mock=AsyncMock(return_value=json.dumps(payload(result)))
    monkeypatch.setattr(OpenAICompatibleClient,'chat_completion',mock)
    reviewed=await model_teach_back(ws[0],'alice',result,ws[1].model_copy(update={'llm_api_key':'test-only'}))
    assert reviewed['model_status']=='model_review'
    assert all(not r['model_evidence']['verified'] for r in reviewed['conditions'])
    assert ws[0].repository.list_mastery('alice')==[]
    assert json.loads(mock.call_args.args[0][1]['content'])['student_text']==result['text']


@pytest.mark.asyncio
async def test_invalid_feedback_falls_back_and_late_help_lock_does_not_deliver(ws,monkeypatch):
    result=teach(ws);mock=AsyncMock(return_value='未绑定任何原句的夸奖')
    monkeypatch.setattr(OpenAICompatibleClient,'chat_completion',mock)
    settings=ws[1].model_copy(update={'llm_api_key':'test-only'})
    failed=await model_teach_back(ws[0],'alice',result,settings)
    assert failed['model_status']=='unavailable' and failed['model_commentary']==''
    async def locked(*args,**kwargs):
        ws[0].new_assessment('alice');return json.dumps(payload(result))
    mock.side_effect=locked
    with pytest.raises(ValueError):await model_teach_back(ws[0],'alice',failed,settings)
    current=ws[0].get('alice','teach_back',result['id'])
    assert not current['model_commentary'] and all('model_evidence' not in r for r in current['conditions'])
