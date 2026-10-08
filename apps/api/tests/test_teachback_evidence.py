import json
from copy import deepcopy
from unittest.mock import AsyncMock
import pytest
from app.api.routes_learning import TeachBackRequest
from app.tutor.learning_extensions import create_teach_back,model_teach_back
from app.tutor.teachback_evidence import original_spans,parse_review
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
