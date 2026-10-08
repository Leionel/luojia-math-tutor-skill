import pytest
from app.tutor.learning_context import CodeContextRef,resolve_learning_context
from app.tutor.learning_extensions import submit_code,STATIC_RULE_VERSION,ASSIGNMENT_ID,TEMPLATE
from app.api.routes_learning import CodeRequest
from test_reference_upgrade import ws,app_client,parse


def saved_code(ws,id="code1",previous=None):
    saved=submit_code(ws[0],"alice",CodeRequest(request_id=id,assignment_id=ASSIGNMENT_ID,code=TEMPLATE,previous_id=previous))
    index=next(i for i,f in enumerate(saved['findings']) if f['kind']=='update_sign')
    return saved,CodeContextRef(kind='code_static',record_id=id,code_hash=saved['code_hash'],static_rule_version=STATIC_RULE_VERSION,selected_finding=index)


def test_code_ref_bound_to_saved_version_and_real_line(ws):
    saved,ref=saved_code(ws);snap=resolve_learning_context(ws[0],'alice',ref)
    assert snap['finding']==saved['findings'][ref.selected_finding]
    assert snap['start_line']<=snap['finding']['line']<=snap['end_line']
    assert snap['code_excerpt']=='\n'.join(saved['code'].split('\n')[snap['start_line']-1:snap['end_line']])
    assert not snap['code_executed'] and not snap['manual_trace_is_program_output']
    second,_=saved_code(ws,'code2','code1')
    assert second['previous_id']=='code1' and ws[0].get('alice','code_submission','code1')==saved
    with pytest.raises(KeyError):resolve_learning_context(ws[0],'bob',ref)


@pytest.mark.parametrize('field,value',[('code_hash','f'*64),('static_rule_version','old'),('selected_finding',29)])
def test_code_ref_rejects_forged_locator(ws,field,value):
    _,ref=saved_code(ws)
    with pytest.raises(ValueError):resolve_learning_context(ws[0],'alice',ref.model_copy(update={field:value}))


def test_code_ref_legacy_is_not_reaudited_or_given_current_version(ws):
    saved,ref=saved_code(ws);saved.pop('static_rule_version');ws[0].save('alice','code_submission',saved['id'],saved)
    with pytest.raises(ValueError):resolve_learning_context(ws[0],'alice',ref)
    snap=resolve_learning_context(ws[0],'alice',ref.model_copy(update={'static_rule_version':None}))
    assert snap['static_rule_version']=='legacy_unversioned'
    assert ws[0].get('alice','code_submission',saved['id'])==saved


def test_code_ref_rejects_changed_code_and_invalid_line(ws):
    saved,ref=saved_code(ws);saved['findings'][ref.selected_finding]['line']=10000
    ws[0].save('alice','code_submission',saved['id'],saved)
    with pytest.raises(ValueError):resolve_learning_context(ws[0],'alice',ref)
    saved['code']='print("changed")';ws[0].save('alice','code_submission',saved['id'],saved)
    with pytest.raises(ValueError):resolve_learning_context(ws[0],'alice',ref)


def test_static_chat_no_execution_or_grade_and_help_lock(ws,monkeypatch):
    _,ref=saved_code(ws);client,tutor=app_client(ws,monkeypatch)
    session=ws[0].repository.create_session('alice','数值分析')['session_id']
    response=client.post('/api/tutor/stream',json={'session_id':session,'user_id':'alice','message':'解释静态提示，不执行代码','learning_context':ref.model_dump()})
    assert any(name=='done' for name,_ in parse(response.text))
    meta=ws[0].repository.list_messages(session)[-1]['learning_meta']
    assert meta['learning_context']['code_executed'] is False and meta['is_correct'] is None
    assert not meta.get('tutor_artifacts') and ws[0].repository.list_mastery('alice')==[]
    ws[0].new_assessment('alice')
    assert client.post('/api/tutor/context',json=ref.model_dump()).status_code==409
