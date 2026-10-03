import asyncio
import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest

from app.config import get_settings
from app.llm.call_observation import observation, reported_usage, usage_summary
from app.llm.completion_protocol import ModelCompletionError
from app.llm.openai_compatible import OpenAICompatibleClient
from app.memory.agent_runs import clean_step
from app.memory.repository import Repository
from app.tutor.orchestrator import TutorOrchestrator
from test_typed_math_runtime import native_settings, native_request, isolated_course, frame


def usage_frame(prompt=10, completion=5, **extra):
    return 'data: '+json.dumps({"choices":[], "usage":{"prompt_tokens":prompt, "completion_tokens":completion,
        "total_tokens":prompt+completion, **extra}})+'\n\n'


@pytest.mark.parametrize("value", [None, {}, [], {"prompt_tokens":True,"completion_tokens":2,"total_tokens":3},
    {"prompt_tokens":-1,"completion_tokens":2,"total_tokens":1},
    {"prompt_tokens":1,"completion_tokens":2,"total_tokens":4},
    {"prompt_tokens":"1","completion_tokens":2,"total_tokens":3}])
def test_invalid_usage_is_missing(value):
    assert reported_usage(value) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("reasoning_only", [False, True])
async def test_usage_and_content_delta_are_not_private_reasoning(reasoning_only):
    events=[]
    async def sink(phase,status,**fields): events.append({"phase":phase,"status":status,"seq":len(events)+1,**fields})
    body=frame({"reasoning_content":"private reasoning"}) + ('' if reasoning_only else frame({"content":"公开解释"})) + frame({},'stop') + usage_frame()
    client=OpenAICompatibleClient(native_settings())
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,text=body))) as http:
        client.get_http_client=lambda:http
        with observation(sink,str(uuid4())):
            if reasoning_only:
                with pytest.raises(ModelCompletionError): _=[v async for v in client.stream([])]
            else: _=[v async for v in client.stream([])]
    terminal=events[-1]
    assert (terminal['first_content_ms'] is None)==reasoning_only
    assert terminal['usage']=={"prompt_tokens":10,"completion_tokens":5,"total_tokens":15}
    assert terminal['usage_source']=='provider_reported' and terminal['request_sent'] is True
    assert "private reasoning" not in json.dumps(events)
    summary=usage_summary(events)
    assert summary['model_requests']==1 and summary['coverage']=='complete'


@pytest.mark.asyncio
async def test_nonstream_is_not_reported_as_stream_ttft():
    events=[]
    async def sink(phase,status,**fields): events.append({"phase":phase,"status":status,"seq":len(events)+1,**fields})
    client=OpenAICompatibleClient(native_settings())
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
        "choices":[{"message":{"content":"正文"},"finish_reason":"stop"}],
        "usage":{"prompt_tokens":2,"completion_tokens":1,"total_tokens":3}}))) as http:
        client.get_http_client=lambda:http
        with observation(sink,str(uuid4())): assert await client.chat_completion([])=='正文'
    assert events[-1]['first_content_ms'] is None
    assert usage_summary(events)['reported_requests']==1


@pytest.mark.asyncio
async def test_guard_repair_usage_and_refresh_match(tmp_path,isolated_course,monkeypatch):
    settings=native_settings(database_url=f'sqlite:///{tmp_path}/store.db',typed_math_tools_enabled=False)
    base,resolved=settings.resolve_request(None)
    settings.llm_prices_json=json.dumps({settings.llm_model:{"resolved_model":resolved,"base_url_sha256":hashlib.sha256(base.rstrip('/').encode()).hexdigest(),
        "currency":"USD","version":"2026-10-03-v1","billing_mode":"plain_input_output","input_per_million":1,"output_per_million":2}})
    repo=Repository(settings); session=repo.create_session('u','calculus')['session_id'];requests=[]
    def response(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200,text=frame({"content":"全部结论已严格数学验证。" if len(requests)==1 else "这里只解释概念，尚未完成数学核验。"},'stop')+(usage_frame() if len(requests)==1 else ''))
    async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as http:
        monkeypatch.setattr(OpenAICompatibleClient,'get_http_client',classmethod(lambda cls:http))
        events=[e async for e in TutorOrchestrator(settings,repo).stream_reply(session,'u','什么是导数？')]
    assert any('event: done' in e for e in events) and len(requests)==2
    message=repo.list_messages(session)[-1]
    run=repo.list_agent_runs(session,'u')[0]
    assert run['usage']==message['learning_meta']['agent_run']['usage']
    assert run['usage']['model_requests']==2 and run['usage']['reported_requests']==1
    assert run['usage']['coverage']=='partial' and run['usage']['known_tokens']['total_tokens']==15
    assert run['usage']['cost']['amount']=='0.00002000' and run['usage']['cost_status']=='partial'
    ends=[s for s in run['steps'] if s.get('span_id') and s['status']!='started']
    assert {'generation','guard_repair'} <= {s['model_stage'] for s in ends}
    assert all(s['parent_id']==run['run_id'] and s.get('ended_at') for s in ends)
    assert not repo.list_agent_runs(session,'other')
    text=json.dumps(run)
    assert 'offline-fixture' not in text and '全部结论' not in text and base not in text and 'pricing' not in text


@pytest.mark.asyncio
async def test_native_tool_failure_repair_never_executes_repair_tools(tmp_path,isolated_course,monkeypatch):
    settings=native_settings(database_url=f'sqlite:///{tmp_path}/store.db')
    repo=Repository(settings); session=repo.create_session('u','calculus')['session_id'];requests=[]
    def response(request):
        requests.append(json.loads(request.content))
        if len(requests)==1: body=native_request('x^9')
        elif len(requests)==2: body=frame({'content':'求导已完成。'},'stop')
        else: body=frame({'content':'该表达式超过工具预算，本轮没有完成求导核验。'},'stop')
        return httpx.Response(200,text=body+usage_frame())
    async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as http:
        monkeypatch.setattr(OpenAICompatibleClient,'get_http_client',classmethod(lambda cls:http))
        events=[e async for e in TutorOrchestrator(settings,repo).stream_reply(session,'u','什么是导数？')]
    assert any('event: done' in e for e in events) and len(requests)==3
    assert 'tools' not in requests[2] and requests[1]['messages'][-2]['tool_call_id']=='call_1'
    run=repo.list_agent_runs(session,'u')[0]
    assert run['usage']['model_requests']==3 and run['usage']['reported_requests']==3
    tools=[s for s in run['steps'] if s.get('tool_name') and s['status']!='started']
    assert len(tools)==1 and tools[0]['status']=='degraded'
    assert tools[0]['error_code']=='tool_parameters_invalid'
    assert not isolated_course.store.list_events('u',isolated_course.course_id)


@pytest.mark.asyncio
async def test_cancelled_model_has_closed_span_and_no_usage():
    events=[];started=asyncio.Event()
    async def sink(phase,status,**fields): events.append({"phase":phase,"status":status,"seq":len(events)+1,**fields})
    class Blocking(httpx.AsyncByteStream):
        async def __aiter__(self):
            started.set();await asyncio.Event().wait();yield b''
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,stream=Blocking()))) as http:
        client=OpenAICompatibleClient(native_settings());client.get_http_client=lambda:http
        async def consume():
            with observation(sink,str(uuid4())): return [v async for v in client.stream([])]
        task=asyncio.create_task(consume());await asyncio.wait_for(started.wait(),2);task.cancel()
        with pytest.raises(asyncio.CancelledError): await task
    assert events[-1]['status']=='cancelled' and events[-1]['ended_at'] and events[-1]['usage'] is None
    assert usage_summary(events)['coverage']=='partial'


def test_restart_closes_open_spans_and_old_receipts_remain_readable(tmp_path):
    settings=get_settings().model_copy(update={'database_url':f'sqlite:///{tmp_path}/store.db'})
    repo=Repository(settings);session=repo.create_session('u','math')['session_id'];run=str(uuid4());span=uuid4().hex
    repo.start_agent_run(run,session,'u','test','test')
    repo.append_agent_run_step(run,'u',{'seq':1,'phase':'model','status':'started','span_id':span,'call_id':span,
        'parent_id':run,'started_at':datetime.now(timezone.utc).isoformat(),'request_sent':True,'prompt':'secret'})
    with repo.connect() as conn: conn.execute('update agent_runs set updated_at=? where id=?',((datetime.now(timezone.utc)-timedelta(seconds=200)).isoformat(),run))
    assert repo.recover_stale_agent_runs()==1
    receipt=repo.get_agent_run(run,session,'u')
    assert receipt['status']=='interrupted'
    assert any(s.get('span_id')==span and s['status']=='failed' for s in receipt['steps'])
    assert receipt['usage']['model_requests']==1 and receipt['usage']['coverage']=='partial'
    assert 'secret' not in json.dumps(receipt)
    old=str(uuid4());repo.start_agent_run(old,session,'u','old','old');repo.finish_agent_run(old,'u','succeeded')
    assert repo.get_agent_run(old,session,'u')['usage'] is None


@pytest.mark.asyncio
async def test_cached_or_reasoning_pricing_stays_unknown():
    settings=native_settings();base,resolved=settings.resolve_request(None)
    settings.llm_prices_json=json.dumps({settings.llm_model:{'resolved_model':resolved,'base_url_sha256':hashlib.sha256(base.rstrip('/').encode()).hexdigest(),
        'currency':'USD','version':'2026-10-03','billing_mode':'plain_input_output','input_per_million':1,'output_per_million':2}})
    events=[]
    async def sink(phase,status,**fields): events.append({'phase':phase,'status':status,'seq':len(events)+1,**fields})
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,text=frame({'content':'解释'},'stop')+usage_frame(prompt_tokens_details={'cached_tokens':3})))) as http:
        client=OpenAICompatibleClient(settings);client.get_http_client=lambda:http
        with observation(sink,str(uuid4())): _=[v async for v in client.stream([])]
    assert usage_summary(events)['cost'] is None and events[-1]['usage']['total_tokens']==15


@pytest.mark.asyncio
async def test_cancel_during_receipt_commit_does_not_lose_sequence(tmp_path,monkeypatch):
    import threading
    from app.tutor.run_trace import RunTrace
    settings=get_settings().model_copy(update={'database_url':f'sqlite:///{tmp_path}/store.db'})
    repo=Repository(settings); session=repo.create_session('u','math')['session_id']
    trace=RunTrace(repo,session,'u');await trace.start()
    entered,release=threading.Event(),threading.Event();original=repo.append_agent_run_step
    def blocked(*args):
        entered.set();assert release.wait(3);return original(*args)
    monkeypatch.setattr(repo,'append_agent_run_step',blocked)
    task=asyncio.create_task(trace.step('model','started'))
    assert await asyncio.to_thread(entered.wait,3)
    task.cancel();await asyncio.sleep(0);task.cancel();await asyncio.sleep(0);release.set()
    with pytest.raises(asyncio.CancelledError): await task
    assert trace.seq==1
    monkeypatch.setattr(repo,'append_agent_run_step',original)
    await trace.step('context','succeeded');await trace.finish('succeeded')
    saved=repo.get_agent_run(trace.run_id,session,'u')
    assert saved['status']=='succeeded' and saved['seq']==3


def test_malformed_nested_receipt_fields_are_projected_out():
    span=uuid4().hex
    step=clean_step({'seq':1,'phase':'model','status':'succeeded','span_id':span,
        'usage':{'prompt_tokens':1,'completion_tokens':2,'total_tokens':3},
        'cost':{'scope':'reported_plain_tokens_estimate','currency':[]},'capability':{'source':[]}})
    assert 'cost' not in step and 'capability' not in step
