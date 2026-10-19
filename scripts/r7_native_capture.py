"""Native ASGI -> PolicyRouter/Teacher/tools/Guard -> SQLite capture.

--offline exercises wire parsing with explicitly synthetic protocol responses.
--prepare writes a not-run manifest. --live requires a separately approved
dynamic-input envelope; it never replays a frozen Teacher answer or routes by ID.
"""
import argparse
import asyncio
from contextlib import contextmanager, ExitStack
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

import httpx
from r5_quality import ROOT, sha, load_cases
from r7_quality import ReviewedReplayPolicy, write
from s5_budget import BudgetLedger, BudgetRejected
from s5_quality import digest, load_json

PROFILE = 'r7-native-capture-v1'
CASE_IDS = ('E06', 'E08', 'E10', 'N01', 'N02', 'N03', 'N04', 'G03', 'Q03')
BODY = '协议冒烟回复：受控计算仅为局部参考，当前主张与条件仍须核对。'


@contextmanager
def capture_workspace(directory):
    """Keep synthetic databases with receipts; background writes outlive cancellation."""
    from app.config import Settings
    from app.knowledge.course_service import CourseService
    from app.knowledge.course_store import CourseStore
    from app.memory.repository import Repository
    from app.tutor.learning_workspace import LearningWorkspace
    directory.mkdir(parents=True, exist_ok=True)
    settings=Settings(database_url='sqlite:///'+str(directory/'sessions.db'),llm_api_key='offline-fixture')
    w=LearningWorkspace(CourseService(store=CourseStore(directory/'course.db')),Repository(settings))
    w.repository.ensure_user('r64-synthetic')
    try: yield w,settings
    finally: w.store.close()


def sources():
    paths = [*(ROOT/'apps/api/app').rglob('*.py'), Path(__file__),
             ROOT/'scripts/r7_quality.py', ROOT/'scripts/s5_budget.py',
             ROOT/'scripts/r64_capture.py', ROOT/'evaluation/r63/cases.json',
             ROOT/'evaluation/r5/cases-v1.json', ROOT/'evaluation/r64/rubric-v1.json']
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def manifest():
    cases = load_cases(ROOT/'evaluation/r5/cases-v1.json')['cases']
    cases = [{k: c[k] for k in ('id', 'prompt', 'input_sha256', 'rubric_sha256')}
             for c in cases if c['id'] in CASE_IDS]
    question = '第三步比第二步小，能说明一定收敛吗？'
    cases.append(dict(id='C3-comparison', prompt=question,
                      input_sha256=hashlib.sha256(question.encode()).hexdigest(),
                      rubric_sha256=None, rubric='comparison quantity unknown; never invent residual/error/iterate'))
    for id, question, history in (
        ('C3-advice-gs','GS 不严格行对角占优就一定发散吗？我想检验必要条件与充分条件的区别。',None),
        ('C3-advice-newton','初值0在0和1间循环，负初值这次残差达标；原来任意初值都收敛的关系需要修订。接下来如何解释局部收敛条件？','newton'),
        ('C3-advice-missing','第三步比第二步小，能说明一定收敛吗？',None),
    ):
        cases.append(dict(id=id,prompt=question,input_sha256=hashlib.sha256(question.encode()).hexdigest(),
            kind='exploration_advice',synthetic_history=history,rubric_sha256=None,
            rubric='C3 development review pending; no invented comparison quantity; coherent editable proposal; no automatic execution'))
    return dict(version=PROFILE, cases=cases, source_sha256=sources(),
                split='public_development_agent_prepared_only', independent_review=None,
                planned=len(cases), completed=0, quality=None, usage=None, actual_cost=None,
                provider_requests=0, max_requests_per_case=6, max_output_tokens=1536,
                scope='native D2 collection, not D0/D1 single-factor quality comparison',
                admission='external_blocked_specific_authorization_and_math_review',
                native_path=['ASGI', 'native fast/policy routing', 'context/review', 'native tools if selected',
                             'TeachingDecision', 'AnswerGuard and repair', 'SSE', 'SQLite'])


def approve(plan, grant):
    if grant.get('manifest_sha256') != sha(plan):
        raise BudgetRejected('manifest_mismatch')
    for name, expected in plan['source_sha256'].items():
        if digest(ROOT/name) != expected:
            raise BudgetRejected('source_drift')
    for field in ('authorization_ref', 'outbound_data_authorization_ref', 'independent_math_review_ref', 'provider',
                  'author_review_ref', 'model_version', 'stream_tool_capability_review_ref',
                  'price_source', 'all_billable_items_upper_bound_review_ref', 'token_bound_review_ref'):
        if not isinstance(grant.get(field), str) or not grant[field].strip():
            raise BudgetRejected('missing_'+field)
    if grant.get('synthetic_dynamic_context_authorized') is not True or grant.get('all_billable_items_bounded') is not True:
        raise BudgetRejected('dynamic_context_or_cost_not_authorized')
    # The bound includes serialized roles, tools and dynamic tool/model continuations.
    # It must be certified for the actual tokenizer/model, not guessed from bytes.
    if not (type(grant.get('max_input_tokens')) is int and 1 <= grant['max_input_tokens'] <= 131072
            and type(grant.get('max_request_bytes')) is int and 1 <= grant['max_request_bytes'] <= 131072
            and type(grant.get('tokens_per_utf8_byte_upper')) in (int, float)
            and math.isfinite(grant['tokens_per_utf8_byte_upper']) and grant['tokens_per_utf8_byte_upper'] > 0
            and type(grant.get('wrapper_tokens_upper')) is int and grant['wrapper_tokens_upper'] >= 0):
        raise BudgetRejected('reviewed_input_bound_required')
    policy = ReviewedReplayPolicy(endpoint=grant['endpoint'], model=grant['model'],
        max_requests=grant['max_requests'], max_cost=grant['max_cost'], currency=grant['currency'],
        per_request_upper_cost=grant['per_request_upper_cost'], max_output_tokens=grant['max_output_tokens'])
    policy.validate()
    if (policy.max_requests > len(plan['cases'])*plan['max_requests_per_case']
            or policy.max_output_tokens > plan['max_output_tokens']):
        raise BudgetRejected('request_count_exceeds_plan')
    return policy


class CaptureTransport(httpx.AsyncBaseTransport):
    def __init__(self, underlying, policy, rows, save, *, ledger=None, grant=None):
        self.underlying, self.policy, self.rows, self.save = underlying, policy, rows, save
        self.ledger, self.grant = ledger, grant
        self.denials = []

    async def handle_async_request(self, request):
        try:
            p = json.loads(request.content)
            if request.method != 'POST' or str(request.url) != self.policy.endpoint or len(self.rows) >= 6:
                raise BudgetRejected('destination_or_per_case_budget')
            cap = p.get('max_tokens', p.get('max_completion_tokens'))
            if p.get('model') != self.policy.model or type(cap) is not int or not 0 < cap <= self.policy.max_output_tokens:
                raise BudgetRejected('model_or_output_cap')
            if any(k in p for k in ('enable_search', 'enable_thinking', 'output_config')):
                raise BudgetRejected('unsupported_billable_feature')
            if self.grant:
                upper = math.ceil(len(request.content)*self.grant['tokens_per_utf8_byte_upper']) + self.grant['wrapper_tokens_upper']
                if len(request.content) > self.grant['max_request_bytes'] or upper > self.grant['max_input_tokens']:
                    raise BudgetRejected('input_budget')
            row = dict(payload=p, payload_sha256=sha(p), status='reserved_before_send',
                       response=None, usage=None, actual_cost=None)
            from app.llm.call_observation import current_call_id
            row['model_call_id']=current_call_id()
            if self.ledger:
                row['reservation_id'] = self.ledger.reserve(sha(p))
            self.rows.append(row); self.save()  # persisted before the actual send
        except Exception as exc:
            self.denials.append(type(exc).__name__); self.save(); raise
        start = time.monotonic()
        try:
            async def send():
                response = await self.underlying.handle_async_request(request)
                chunks=[];size=0
                async for chunk in response.aiter_bytes():
                    size+=len(chunk)
                    if size>262144:
                        await response.aclose();raise BudgetRejected('response_budget')
                    chunks.append(chunk)
                headers={k:v for k,v in response.headers.items()
                         if k.lower() not in {'content-encoding','content-length','transfer-encoding'}}
                await response.aclose()
                return httpx.Response(response.status_code,headers=headers,content=b''.join(chunks),request=request)
            response = await asyncio.wait_for(send(), 45)
            if len(response.content) > 262144 or 300 <= response.status_code < 400:
                raise BudgetRejected('response_budget_or_redirect')
            row.update(status='response_received', http_status=response.status_code,
                       response=response.text, response_sha256=hashlib.sha256(response.content).hexdigest())
            from app.llm.call_observation import reported_usage
            try:
                usage=response.json().get('usage')
            except (ValueError,AttributeError):
                usage=None
                for line in response.text.splitlines():
                    if line.startswith('data:'):
                        try: frame=json.loads(line[5:]);usage=frame.get('usage',usage)
                        except (ValueError,AttributeError):pass
            row['usage']=reported_usage(usage) if self.grant else None
            if self.ledger: self.ledger.finish(row['reservation_id'], 'response_received')
            return response
        except BaseException as exc:
            row.update(status='failed', failure_type=type(exc).__name__)
            if self.ledger: self.ledger.finish(row['reservation_id'], 'failed')
            raise
        finally:
            row['latency_ms'] = round((time.monotonic()-start)*1000, 3); self.save()

    async def aclose(self):
        await self.underlying.aclose()


def protocol_fixture(*, corrupt=False):
    """Protocol-only responses; never uses case ID/gold and never earns a score."""
    def frame(delta, reason):
        return 'data: '+json.dumps({'choices': [{'delta': delta, 'finish_reason': reason}]})+'\n\n'
    def response(request):
        p = json.loads(request.content); messages = p['messages']
        if not p['stream']:
            if '数学探索助教' in messages[0]['content']:
                return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(dict(
                    decision=dict(claim_ref='claim:current',evidence_refs=['claim:current','context:personal_relations'],
                        known_conditions=[],missing_conditions=[],claim_status='unknown',action='explain',
                        disclosure='scaffolded',reason='仅协议冒烟，不作数学判断',assessments=[]),
                    suggested_graph={'nodes':[],'edges':[]},follow_up=BODY))},'finish_reason':'stop'}]})
            elif '数学教学路由器' in messages[0]['content']:
                text = json.dumps(dict(intent='concept', action='explain', confidence=0.95, uncertain=False))
            else:
                text = json.dumps(dict(verified=False, is_correct=None, summary='协议夹具，不作数学判断'))
            return httpx.Response(200, json={'choices': [{'message': {'content': text}, 'finish_reason': 'stop'}]})
        repair = '只修复最后一条回答的交付违规' in messages[-1].get('content', '')
        if p.get('tools') and not any(m['role']=='tool' for m in messages):
            delta = {'tool_calls': [{'index': 0, 'id': 'fixture_call', 'type': 'function',
                'function': {'name': 'math_differentiate', 'arguments': json.dumps({'version': 'v1', 'expression': 'x^2'})}}]}
            return httpx.Response(200, text=frame(delta, 'tool_calls')+'data: [DONE]\n\n')
        decision = dict(claim_ref='claim:current', evidence_refs=['claim:current'], known_conditions=[],
            missing_conditions=[], claim_status='unknown', action='explain', disclosure='scaffolded',
            reason='只检查协议可达性', assessments=[])
        text = BODY if repair else '[TEACHING_DECISION]'+json.dumps(decision)+'[/TEACHING_DECISION][OUTPUT]'+(
            '我已经运行了你的Python代码。' if corrupt else BODY)
        return httpx.Response(200, text=frame({'content': text}, 'stop')+'data: [DONE]\n\n')
    return httpx.MockTransport(response)


async def capture_case(case, target, *, policy, underlying, key, grant=None, ledger=None,
                       setup=None, memory_enabled=True, native_tools=True):
    from fastapi import FastAPI
    from app.api import routes_tutor, routes_explorations
    from app.auth import Principal, get_principal
    from app.main_deps import get_app_settings, get_learning_workspace, get_orchestrator
    from app.llm.openai_compatible import OpenAICompatibleClient
    from app.tutor.orchestrator import TutorOrchestrator
    from r64_capture import OWNER
    artifact = dict(case=case, calls=[], sse=None, saved=None, runs=[], quality=None,
                    confirmation='no student experiment auto-confirmation', source_sha256=sources(),
                    evidence_source='live_native_application' if grant else 'offline_wire_fixture')
    save = lambda: write(target, artifact)
    transport = CaptureTransport(underlying, policy, artifact['calls'], save, ledger=ledger, grant=grant)
    with capture_workspace(target.with_suffix('.data')) as (w, settings), ExitStack() as bindings:
        bindings.enter_context(patch('app.knowledge.course_service.get_course_service',return_value=w.course))
        bindings.enter_context(patch('app.knowledge.evidence_builder.get_course_service',return_value=w.course))
        from app.knowledge.evidence_builder import CourseEvidenceBuilder
        artifact['course_binding_verified']=CourseEvidenceBuilder().service is w.course
        if setup:
            artifact['history'] = setup(w)
        settings.llm_model = 'custom:'+policy.endpoint.rsplit('/chat/completions', 1)[0]+'|'+policy.model
        settings.llm_api_key = key; settings.typed_math_tools_enabled = True
        settings.llm_capabilities_json = json.dumps({settings.llm_model: dict(resolved_model=policy.model,
            base_url_sha256=hashlib.sha256(policy.endpoint.rsplit('/chat/completions', 1)[0].encode()).hexdigest(),
            source='operator_verified' if grant else 'offline_fixture', checked_at='2026-10-18T00:00:00Z',
            tool_calls=native_tools, streaming=True, stream_usage=False, input_token_limit=131072,
            output_token_limit=policy.max_output_tokens)})
        tutor = TutorOrchestrator(settings, w.repository)
        if setup:
            # Paired studies must not compare a cold first arm with a warm second
            # arm. Keep this measured local-only warmup outside the task latency.
            start=time.perf_counter()
            await tutor.workflow_owner.context_collector._collect_local_hits(dict(
                message=case['prompt'],subject='数值分析',user_id=OWNER,task_type=None))
            artifact['pair_local_retrieval_warmup_ms']=round((time.perf_counter()-start)*1000,3)
            # Explicit paired-study intervention: identical memory-use instruction
            # in both arms. Production defaults and P0 native capture stay untouched.
            from r64_capture import MEMORY_RULE
            base = tutor.workflow_owner._build_base_messages
            def shared_prompt(*args, **kwargs):
                messages = base(*args, **kwargs)
                for m in messages:
                    if m.get('role')=='developer' and m['content'].startswith('[RUNTIME_CONTEXT]\n'):
                        value=json.loads(m['content'].split('\n',1)[1].rsplit('\n',1)[0])
                        value.setdefault('personal_context',[]); value['personal_recall_rule']=MEMORY_RULE
                        m['content']='[RUNTIME_CONTEXT]\n'+json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n[/RUNTIME_CONTEXT]'
                return messages
            tutor.workflow_owner._build_base_messages = shared_prompt
        session = w.repository.create_session(OWNER, '数值分析')['session_id']
        for turn in case.get('prior_turns', []):
            w.repository.add_message(session,turn['role'],turn['content'])
        app = FastAPI(); app.include_router(routes_tutor.router); app.include_router(routes_explorations.router)
        for dep, val in ((get_app_settings, settings), (get_learning_workspace, w),
                         (get_orchestrator, tutor), (get_principal, Principal(OWNER, True))):
            app.dependency_overrides[dep] = (lambda v=val: lambda: v)()
        async with httpx.AsyncClient(transport=transport, follow_redirects=False) as model_http:
            from app.tutor.personal_recall import select_personal_context
            original_send = httpx.AsyncClient.send
            async def guarded_send(client, request, *args, **kwargs):
                if isinstance(client._transport, (CaptureTransport, httpx.ASGITransport)):
                    return await original_send(client, request, *args, **kwargs)
                raise BudgetRejected('unapproved_secondary_http')
            with patch.object(OpenAICompatibleClient, 'get_http_client', classmethod(lambda cls: model_http)), \
                 patch.object(httpx.AsyncClient, 'send', guarded_send), \
                 patch.object(httpx.Client, 'send', side_effect=BudgetRejected('unapproved_sync_http')), \
                 patch('app.tutor.personal_recall.select_personal_context',
                       side_effect=select_personal_context if memory_enabled else lambda *a, **k: []):
                # These are infrastructure bindings. No route, model method, tool, Guard or saving node is mocked.
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://testserver') as client:
                    try:
                        if case.get('kind')=='exploration_advice':
                            from app.tutor.explorations import Explorations,Create,Revise
                            service=Explorations(w)
                            if case.get('synthetic_history'):
                                from r64_capture import seed_history
                                artifact['history']=seed_history(w,case['synthetic_history'],False)
                                v=service.get(OWNER,'prior')
                                v=service.update(OWNER,'prior','revise',Revise(request_id='current-question',
                                    expected_revision=v['revision'],claim=case['prompt'],reason='公开C3重测输入'))
                            else:
                                v=service.create(OWNER,Create(request_id='current',title='C3建议复测',claim=case['prompt']))
                            response=await asyncio.wait_for(client.post(f"/api/explorations/{v['id']}/advice",
                                json={'expected_revision':v['revision']}),60)
                            artifact['advice']=response.json(); artifact['saved']=service.get(OWNER,v['id'])
                            artifact['status']='completed' if response.status_code==200 and artifact['advice'].get('status')=='suggested_not_executed' and not transport.denials else 'failed'
                        else:
                            response = await asyncio.wait_for(client.post('/api/tutor/stream', json=dict(
                                session_id=session, user_id=OWNER, message=case['prompt'], subject='数值分析',
                                mode='socratic', reasoning_effort='off', web_search_mode='off')), 120)
                            artifact['sse'] = response.text
                            saved = w.repository.list_messages(session)
                            artifact['saved'] = saved[-1] if saved else None
                            artifact['runs'] = w.repository.list_agent_runs(session, OWNER)
                            artifact['status'] = 'completed' if (response.status_code==200 and
                                'event: done' in response.text and 'event: error' not in response.text and
                                artifact['saved'] and artifact['saved']['role']=='assistant' and not transport.denials) else 'failed'
                    except (Exception, asyncio.CancelledError) as exc:
                        artifact.update(status='failed', failure_type=type(exc).__name__)
                await tutor.workflow_owner.stop_background_worker()
        artifact['denials'] = transport.denials
        artifact['model_call_failures']=[i for i,c in enumerate(artifact['calls'])
            if c['status']!='response_received' or c.get('http_status',500)>=400]
        artifact['model_span_failures']=[s for r in artifact['runs'] for s in r.get('steps',[])
            if s.get('phase')=='model' and s.get('status') in {'failed','cancelled','degraded'}]
        sent={c['model_call_id'] for c in artifact['calls']}
        artifact['untransmitted_auxiliary_spans']=[s for s in artifact['model_span_failures']
            if s.get('model_stage')=='embedding' and s.get('call_id') not in sent]
        primary=[s for s in artifact['model_span_failures'] if s not in artifact['untransmitted_auxiliary_spans']]
        if artifact['model_call_failures'] or primary:
            artifact['application_delivery_status']=artifact.get('status')
            artifact['status']='failed'
            artifact['failure_code']='UPSTREAM_MODEL_FAILURE'
        artifact['provider_requests'] = len(artifact['calls']) if grant else 0
        artifact['model_adapter_requests'] = len(artifact['calls'])
        save()
    return artifact


async def run(plan, target, grant=None, key=None):
    policy = approve(plan, grant) if grant else ReviewedReplayPolicy(max_requests=12, max_output_tokens=1536)
    ledger = BudgetLedger(ROOT/'results/r7/native-budgets'/(sha(grant)+'.sqlite'), policy) if grant else None
    cases = plan['cases'] if grant else [dict(id='wire-tool', prompt='第三步比第二步小，能说明一定收敛吗？'),
        dict(id='wire-repair', prompt='我想先了解导数的含义。'),
        dict(id='wire-advice',prompt='第三步比第二步小，能说明一定收敛吗？',kind='exploration_advice')]
    report = dict(version=PROFILE, evidence_source='live_native_application' if grant else 'offline_wire_fixture',
                  source_sha256=sources(), manifest_sha256=sha(plan), planned=len(cases),
                  records=[dict(case_id=c['id'], status='not_run', quality=None) for c in cases],
                  quality=None, usage=None, actual_cost=None, provider_requests=0,
                  independent_math_reviewed=False, live_model_observed=False,
                  provider=grant['provider'] if grant else None,model=policy.model,
                  model_version=grant['model_version'] if grant else None,
                  engineering_verified=False, user_task_observed=False, learning_gain_supported=False)
    write(target, report)
    for case, row in zip(cases, report['records']):
        path = target.parent/(target.stem+'-artifacts')/(case['id']+'.json'); path.parent.mkdir(parents=True, exist_ok=True)
        underlying = httpx.AsyncHTTPTransport(retries=0) if grant else protocol_fixture(corrupt=case['id']=='wire-repair')
        result = await capture_case(case, path, policy=policy, underlying=underlying,
                                    key=key or 'offline-fixture', grant=grant, ledger=ledger)
        row.update(status=result['status'], artifact_ref=path.relative_to(target.parent).as_posix(),
                   artifact_sha256=digest(path), model_adapter_requests=result['model_adapter_requests'])
        report['provider_requests'] += result['provider_requests']; write(target, report)
        if grant and any(c.get('http_status')==200 for c in result['calls']):report['live_model_observed']=True
        if row['status'] != 'completed': break
    report['engineering_verified'] = not grant and all(r['status']=='completed' for r in report['records'])
    report.update(completed=sum(r['status']=='completed' for r in report['records']),
                  failed=sum(r['status']=='failed' for r in report['records']),
                  not_run=sum(r['status']=='not_run' for r in report['records']))
    if ledger:
        budget=ledger.snapshot();budget.update(scope='native_application_http',live_ready=True,
            pending=[],usage_coverage='per-call receipts; absent usage remains unknown')
        report['budget']=budget
    write(target, report); return report


def main():
    p = argparse.ArgumentParser(description=__doc__); mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true'); mode.add_argument('--offline', action='store_true')
    mode.add_argument('--live', type=Path); p.add_argument('--approval', type=Path); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); target = a.output.resolve()
    if (not target.is_relative_to(ROOT/'results') or target.exists()
            or (target.parent/(target.stem+'-artifacts')).exists()): p.error('new results output required')
    key = os.environ.pop('R7_NATIVE_API_KEY', '')
    from r64_capture import isolate
    isolate(); target.parent.mkdir(parents=True, exist_ok=True)
    plan = load_json(a.live) if a.live else manifest()
    if a.prepare: write(target, plan); return 0
    if a.approval and not a.live: p.error('--approval is only valid with --live')
    grant = load_json(a.approval) if a.live and a.approval else None
    if a.live and (not grant or not key): p.error('explicit approval and temporary R7_NATIVE_API_KEY required')
    if a.live: approve(plan, grant)  # before constructing the real network transport
    report = asyncio.run(run(plan, target, grant, key))
    print(json.dumps({k: report[k] for k in ('completed', 'failed', 'not_run', 'provider_requests', 'quality')}))
    return 0 if not report['failed'] else 1


if __name__ == '__main__': raise SystemExit(main())
