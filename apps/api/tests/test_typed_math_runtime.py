import asyncio
import hashlib
import json
import subprocess

import httpx
import pytest

from app.agents.typed_tools import ToolCall, ToolRuntime, run_fixed_worker, validate_call
from app.config import get_settings
from app.knowledge.course_service import CourseService
from app.knowledge.course_store import CourseStore
from app.llm.capabilities import tools_available
from app.llm.completion_protocol import ModelCompletionError
from app.llm.openai_compatible import OpenAICompatibleClient
from app.memory.repository import Repository
from app.tutor.graph import TutorWorkflow
from app.tutor.orchestrator import TutorOrchestrator


def native_settings(**extra):
    settings = get_settings().model_copy(update={"typed_math_tools_enabled": True, "llm_api_key": "offline-fixture", **extra})
    base, resolved = settings.resolve_request(None)
    settings.llm_capabilities_json = json.dumps({settings.llm_model: {
        "resolved_model": resolved,
        "base_url_sha256": hashlib.sha256(base.rstrip('/').encode()).hexdigest(),
        "source": "offline_fixture", "checked_at": "2026-10-03T00:00:00+00:00",
        "tool_calls": True, "streaming": True, "stream_usage": True,
        "input_token_limit": 32000, "output_token_limit": 4096}})
    return settings


@pytest.fixture
def isolated_course(monkeypatch):
    course = CourseService(store=CourseStore(None))
    monkeypatch.setattr("app.knowledge.course_service.get_course_service", lambda *args: course)
    yield course
    course.store.close()


def call(expression="x^2", call_id="call_1"):
    return ToolCall(call_id=call_id, name="math_differentiate", arguments={"version": "v1", "expression": expression})


def frame(delta, finish=None):
    return 'data: '+json.dumps({"choices": [{"delta": delta, "finish_reason": finish}]})+'\n\n'


def native_request(expression="x^2", ending="tool_calls"):
    args = json.dumps({"version": "v1", "expression": expression})
    return frame({"tool_calls": [{"index": 0, "id": "call_1", "type": "function",
                                 "function": {"name": "math_differentiate", "arguments": args[:14]}}]}) + frame({"tool_calls": [{"index": 0, "function": {"arguments": args[14:]}}]}, ending)


@pytest.mark.parametrize("expression", ["__import__('os')", "x.__class__", "x[0]", "lambda:x", "sum(x)", "sin(x,x)", "x**x", "x**9", "x**-9", "1e999", "[x]", "True", "x**(2+2)", "("*30+'x'+")"*30, "9"*33])
def test_symbolic_attack_budget(expression):
    # Parentheses alone do not increase the AST depth; use nested calls instead.
    if expression.startswith('('*30): expression = 'sin('*15+'x'+')'*15
    with pytest.raises((ValueError, SyntaxError, OverflowError)):
        validate_call(call(expression))


@pytest.mark.parametrize("args", [{"version": "v2", "expression": "x"}, {"expression": "x", "owner": "victim"}, {"expression": "x", "source": "print(2)"}, {"expression": 2}])
def test_unknown_tool_fields_never_spawn(args, monkeypatch):
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: pytest.fail("invalid arguments spawned"))
    with pytest.raises(ValueError):
        validate_call(ToolCall(call_id="c", name="math_differentiate", arguments=args))


@pytest.mark.asyncio
async def test_fixed_derivative_and_numerical_worker():
    c = call('sin(x)+x^2')
    derivative = await run_fixed_worker(c, validate_call(c))
    assert derivative.status == "succeeded" and derivative.data["derivative"] == "2*x + cos(x)"
    assert not derivative.data["whole_answer_verified"] and derivative.data["assumptions"]
    c = ToolCall(call_id="n", name="numerical_run", arguments={"task": {
        "domain": "linear_system", "matrix": [[4, 1], [1, 3]], "rhs": [1, 2], "initial": [0, 0], "limit": 30}})
    numerical = await run_fixed_worker(c, validate_call(c))
    assert numerical.status == "succeeded" and numerical.data["evidence_scope"] == "floating_point_residual"
    assert numerical.data["rows"][-1]["residual"] <= 1e-6


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["cancel", "timeout", "output"])
async def test_actual_child_is_reaped(mode, monkeypatch):
    from app.agents import typed_tools
    real_spawn = subprocess.Popen
    children = []
    def spawn(*args, **kwargs):
        child = real_spawn(*args, **kwargs); children.append(child); return child
    monkeypatch.setattr(typed_tools.subprocess, "Popen", spawn)
    if mode == "output": monkeypatch.setattr(typed_tools, "MAX_OUTPUT", 32)
    c = call()
    task = asyncio.create_task(run_fixed_worker(c, validate_call(c), timeout=0.001 if mode == "timeout" else 10))
    for _ in range(300):
        if children: break
        await asyncio.sleep(0.01)
    assert children
    if mode == "cancel":
        task.cancel()
        with pytest.raises(asyncio.CancelledError): await asyncio.wait_for(task, 5)
    else:
        result = await asyncio.wait_for(task, 15)
        assert result.status == ("timeout" if mode == "timeout" else "failed")
        assert result.error_code == ("tool_timeout" if mode == "timeout" else "tool_output_budget")
    assert children[0].poll() is not None


@pytest.mark.asyncio
async def test_tool_policy_budget_duplicate_and_probe(isolated_course, monkeypatch):
    runtime = ToolRuntime("u", "server-run")
    first = await runtime.execute(call())
    assert first["status"] == "succeeded"
    assert (await runtime.execute(call())) == first
    assert (await runtime.execute(call(call_id="other")))["status"] == "rejected"
    conflict = ToolRuntime("u", "other-run")
    await conflict.execute(call())
    assert (await conflict.execute(call("x^3")))["status"] == "rejected"
    isolated_course.store.save_learning_record("u", isolated_course.course_id, "assessment", "pending", {"state": "in_progress"})
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: pytest.fail("policy rejection spawned"))
    assert (await ToolRuntime("u", "r").execute(call()))["status"] == "rejected"
    events = isolated_course.store.list_events("u", isolated_course.course_id)
    assert len([e for e in events if e["event_type"] == "hint_exposed"]) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("body,code", [(native_request(ending=None), "model_stream_incomplete"),
    (native_request(ending="length"), "model_output_truncated"), (native_request(ending="stop"), "model_response_invalid"),
    (native_request().replace('call_1', 'bad/id'), "model_response_invalid"),
    (native_request().replace('math_differentiate', 'shell'), "model_response_invalid")])
async def test_partial_or_invalid_native_calls_cannot_execute(body, code):
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))) as http:
        client = OpenAICompatibleClient(native_settings()); client.get_http_client = lambda: http
        with pytest.raises(ModelCompletionError) as error: await client.tool_turn([])
        assert error.value.code == code


def test_unknown_capability_and_wrong_endpoint_stay_disabled():
    assert not tools_available(get_settings())
    settings = native_settings(); assert tools_available(settings)
    manifest = json.loads(settings.llm_capabilities_json)
    manifest[settings.llm_model]["base_url_sha256"] = "other"
    settings.llm_capabilities_json = json.dumps(manifest)
    assert not tools_available(settings)


@pytest.mark.asyncio
async def test_native_graph_guard_and_sqlite_delivery(tmp_path, isolated_course, monkeypatch):
    settings = native_settings(database_url=f'sqlite:///{tmp_path}/sessions.db')
    repo = Repository(settings)
    session = repo.create_session('u', 'numerical')
    requests = []
    def response(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, text=native_request() if len(requests)==1 else frame({"content": "对 x² 求导得到 2x；仅核对该表达式，仍需检查定义域与整体推导。"}, "stop"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as http:
        monkeypatch.setattr(OpenAICompatibleClient, 'get_http_client', classmethod(lambda cls: http))
        orchestrator = TutorOrchestrator(settings, repo)
        events = [e async for e in orchestrator.stream_reply(session['session_id'], 'u', '什么是导数？')]
    assert len(requests)==2 and requests[1]['messages'][-2]['role']=='tool'
    assert requests[1]['messages'][-2]['tool_call_id']=='call_1'
    assert any('event: done' in e for e in events)
    answer = repo.list_messages(session['session_id'])[-1]
    assert answer['learning_meta']['answer_guard']['status']=='passed'
    assert answer['learning_meta']['agent_run']['status']=='succeeded'
    assert isolated_course.store.learning_records('u', isolated_course.course_id, 'lab') == []
    assert not answer['learning_meta']['verified']


@pytest.mark.asyncio
@pytest.mark.parametrize('kind',['duplicate_arguments','parallel','oversized','after_terminal'])
async def test_native_envelope_budgets_fail_closed(kind):
    args='{"expression":"x","expression":"x^2"}' if kind=='duplicate_arguments' else json.dumps({'expression':'x'})
    parts=[{'index':0,'id':'c','type':'function','function':{'name':'math_differentiate','arguments':args}}]
    if kind=='parallel': parts.append({**parts[0],'index':1,'id':'c2'})
    body=frame({'tool_calls':parts},'tool_calls')
    if kind=='oversized': body='data: '+('a'*131073)+'\n\n'
    if kind=='after_terminal': body+=frame({'content':'late'},'stop')
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,text=body))) as http:
        client=OpenAICompatibleClient(native_settings());client.get_http_client=lambda:http
        with pytest.raises(ModelCompletionError) as error: await client.tool_turn([])
        assert error.value.code=='model_response_invalid'


@pytest.mark.asyncio
async def test_argument_correction_is_bounded_and_tool_spans_have_causal_parent(tmp_path,isolated_course,monkeypatch):
    from test_call_observation import usage_frame
    settings=native_settings(database_url=f'sqlite:///{tmp_path}/store.db')
    repo=Repository(settings);session=repo.create_session('u','math')['session_id'];requests=[]
    def response(request):
        requests.append(json.loads(request.content));n=len(requests)
        body=native_request('x^9' if n==1 else 'x^2').replace('call_1',f'call_{n}') if n<3 else frame({'content':'x² 的导数为 2x，仅核对这一表达式。'},'stop')
        return httpx.Response(200,text=body+usage_frame())
    async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as http:
        monkeypatch.setattr(OpenAICompatibleClient,'get_http_client',classmethod(lambda cls:http))
        events=[e async for e in TutorOrchestrator(settings,repo).stream_reply(session,'u','什么是导数？')]
    assert any('event: done' in e for e in events) and len(requests)==3
    assert requests[-1]['tool_choice']=='none'
    run=repo.list_agent_runs(session,'u')[0]
    model_ends={s['span_id']:s for s in run['steps'] if s['phase']=='model' and s.get('span_id') and s['status']!='started'}
    tools=[s for s in run['steps'] if s.get('tool_name') and s['status']!='started']
    assert [s['status'] for s in tools]==['degraded','succeeded']
    assert all(s['parent_id'] in model_ends and s['tool_call_id']==model_ends[s['parent_id']]['tool_call_id'] for s in tools)
    assert run['usage']['model_requests']==3 and run['usage']['known_tokens']['total_tokens']==45


@pytest.mark.asyncio
async def test_probe_started_during_actual_worker_withholds_result(isolated_course,monkeypatch):
    from app.agents import typed_tools
    original=typed_tools.run_fixed_worker
    async def worker(*args):
        result=await original(*args)
        assert result.status=='succeeded'
        isolated_course.store.save_learning_record('u',isolated_course.course_id,'assessment','pending',{'state':'in_progress'})
        return result
    monkeypatch.setattr(typed_tools,'run_fixed_worker',worker)
    result=await ToolRuntime('u','r').execute(call())
    assert result['error_code']=='tool_policy_rejected' and result['data'] is None
    assert isolated_course.store.list_events('u',isolated_course.course_id)==[]


@pytest.mark.asyncio
async def test_integral_sampling_counterexample_keeps_estimate_scope():
    from app.tutor.answer_guard import check_delivery
    c=ToolCall(call_id='n',name='numerical_run',arguments={'task':{'domain':'integration','method':'simpson',
        'expression':'sin(16*pi*x)^2','intervals':4,'limit':4}})
    result=(await run_fixed_worker(c,validate_call(c))).public(c)
    assert result['status']=='succeeded' and result['data']['evidence_scope']=='quadrature_error_estimate'
    # The true integral is 1/2; zero-valued sampling is not an error certificate.
    assert result['data']['rows'][-1]['value']<1e-10
    assert 'integration_scope_claim' in check_delivery('积分误差已被严格保证。',tool_evidence=[result]).violations
    assert check_delivery('积分误差尚未得到严格保证，须更换网格再核对。',tool_evidence=[result]).passed
