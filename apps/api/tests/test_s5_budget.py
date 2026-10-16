"""S5.3 offline transport reservation, concurrency, interruption and persistence."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
import hashlib,importlib.util,json
from pathlib import Path
import sys
import httpx
import pytest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from s5_budget import BudgetLedger,OfflineBudgetPolicy,OfflineBudgetTransport,BudgetRejected,amount


def request(policy,**patch):
    payload={'model':policy.model,'messages':[{'role':'user','content':'synthetic math question'}],'max_tokens':100}
    payload.update(patch)
    return httpx.Request('POST',policy.endpoint,json=payload)


def make(tmp_path,policy=None,handler=None):
    policy=policy or OfflineBudgetPolicy()
    ledger=BudgetLedger(tmp_path/'budget.db',policy)
    calls=[]
    def reply(req):calls.append(req);return httpx.Response(200,json={'usage':None})
    return ledger,OfflineBudgetTransport(ledger,httpx.MockTransport(handler or reply)),calls


def test_52nd_request_is_not_sent(tmp_path):
    ledger,transport,calls=make(tmp_path)
    for _ in range(51):transport.handle_request(request(ledger.policy))
    with pytest.raises(BudgetRejected,match='request_budget_exhausted'):transport.handle_request(request(ledger.policy))
    assert len(calls)==51 and ledger.snapshot()['requests_reserved']==51
    assert Decimal(ledger.snapshot()['reserved_cost_upper_bound'])==Decimal('.51')
    assert ledger.snapshot()['actual_cost'] is None and ledger.snapshot()['live_ready'] is False


def test_concurrent_reservations_cannot_overspend(tmp_path):
    ledger,transport,calls=make(tmp_path,replace(OfflineBudgetPolicy(),max_requests=20,max_cost='0.07'))
    def attempt(_):
        try:transport.handle_request(request(ledger.policy));return True
        except BudgetRejected:return False
    with ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(attempt,range(40)))
    assert sum(results)==len(calls)==7
    assert ledger.snapshot()['requests_reserved']==7 and Decimal(ledger.snapshot()['reserved_cost_upper_bound'])==Decimal('.07')


def test_failure_unknown_usage_and_retry_do_not_refund(tmp_path):
    def fail(req):raise httpx.ConnectError('synthetic failure')
    ledger,transport,_=make(tmp_path,replace(OfflineBudgetPolicy(),max_requests=2),fail)
    for _ in range(2):
        with pytest.raises(httpx.ConnectError):transport.handle_request(request(ledger.policy))
    with pytest.raises(BudgetRejected):transport.handle_request(request(ledger.policy))
    assert ledger.snapshot()['statuses']=={'failed':2}
    assert ledger.snapshot()['requests_reserved']==2


def test_reopen_preserves_cap_and_crash_reservations(tmp_path):
    p=replace(OfflineBudgetPolicy(),max_requests=1)
    ledger=BudgetLedger(tmp_path/'budget.db',p);ledger.reserve('0'*64)
    restored=BudgetLedger(tmp_path/'budget.db',p)
    with pytest.raises(BudgetRejected):restored.reserve('1'*64)
    assert restored.snapshot()['statuses']=={'reserved':1}
    with pytest.raises(BudgetRejected,match='ledger_policy_changed'):BudgetLedger(tmp_path/'budget.db',replace(p,max_requests=2))


def test_mutated_policy_and_corrupt_ledger_fail_closed(tmp_path):
    ledger,transport,calls=make(tmp_path)
    ledger.policy=replace(ledger.policy,max_requests=100)
    with pytest.raises(BudgetRejected):transport.handle_request(request(ledger.policy))
    assert calls==[]
    ledger.policy=OfflineBudgetPolicy()
    with ledger.connect() as conn:conn.execute('UPDATE budget_state SET requests=0,upper_cost=1')
    with pytest.raises(BudgetRejected,match='ledger_integrity_mismatch'):transport.handle_request(request(ledger.policy))
    assert calls==[]


@pytest.mark.parametrize('endpoint',['http://fixture.invalid/v1/chat/completions','https://user:pass@fixture.invalid/v1/chat/completions',
 'https://fixture.invalid/v1/embeddings','https://fixture.invalid:8443/v1/chat/completions',
 'https://fixture.invalid/v1/chat/completions?x=1'])
def test_bad_policy_destinations(endpoint,tmp_path):
    with pytest.raises(BudgetRejected):BudgetLedger(tmp_path/'bad.db',replace(OfflineBudgetPolicy(),endpoint=endpoint))


@pytest.mark.parametrize('patch',[{'model':'other'}, {'max_tokens':1001}, {'max_tokens':True},
 {'max_tokens':None}, {'max_completion_tokens':100}, {'tools':[]}, {'stream':'yes'},
 {'stream_options':{'include_usage':False}}, {'messages':[{'role':'user','content':[{'type':'image_url','image_url':'private'}]}]}])
def test_payload_bounds_reject_before_reservation(tmp_path,patch):
    ledger,transport,calls=make(tmp_path)
    with pytest.raises(BudgetRejected):transport.handle_request(request(ledger.policy,**patch))
    assert not calls and ledger.snapshot()['requests_reserved']==0


@pytest.mark.parametrize('url',['https://other.invalid/v1/chat/completions','https://fixture.invalid/v1/embeddings',
 'https://fixture.invalid/v1/chat/completions?x=1'])
def test_destination_mismatch_cannot_send(tmp_path,url):
    ledger,transport,calls=make(tmp_path)
    req=request(ledger.policy);req.url=httpx.URL(url)
    with pytest.raises(BudgetRejected):transport.handle_request(req)
    assert not calls and ledger.snapshot()['requests_reserved']==0


def test_redirect_is_not_followed_or_refunded(tmp_path):
    calls=[]
    def redirect(req):calls.append(req);return httpx.Response(302,headers={'location':'https://other.invalid'})
    ledger,transport,_=make(tmp_path,handler=redirect)
    with httpx.Client(transport=transport,follow_redirects=True) as client:
        with pytest.raises(BudgetRejected,match='redirect_not_allowed'):client.send(request(ledger.policy))
    assert len(calls)==1 and ledger.snapshot()['statuses']=={'redirect_rejected':1}
    assert ledger.snapshot()['requests_reserved']==1


@pytest.mark.asyncio
async def test_async_cancel_is_reserved_and_reopen_does_not_reset(tmp_path):
    entered=asyncio.Event();gate=asyncio.Event()
    async def wait(req):entered.set();await gate.wait();return httpx.Response(200)
    ledger,transport,_=make(tmp_path,replace(OfflineBudgetPolicy(),max_requests=1),wait)
    task=asyncio.create_task(transport.handle_async_request(request(ledger.policy)))
    await entered.wait();task.cancel()
    with pytest.raises(asyncio.CancelledError):await task
    assert ledger.snapshot()['statuses']=={'cancelled':1}
    with pytest.raises(BudgetRejected):BudgetLedger(tmp_path/'budget.db',ledger.policy).reserve('1'*64)


@pytest.mark.asyncio
async def test_async_success_keeps_unknown_usage_and_reservation(tmp_path):
    ledger,transport,calls=make(tmp_path)
    response=await transport.handle_async_request(request(ledger.policy,stream=True,stream_options={'include_usage':True}))
    assert response.status_code==200 and len(calls)==1
    assert ledger.snapshot()['actual_cost'] is None and ledger.snapshot()['statuses']=={'response_received':1}


@pytest.mark.parametrize('value',['NaN','Infinity','-1','0.0000000000001',True,0.1])
def test_exact_amount_boundary(value):
    with pytest.raises(BudgetRejected):amount(value)


@pytest.mark.parametrize('patch',[{'price_contract_kind':'operator_verified'}, {'all_billable_items_bounded':False},
 {'per_request_upper_cost':'0'},{'currency':'unknown'},{'max_requests':True}])
def test_unknown_provider_fee_contract_cannot_enable_transport(tmp_path,patch):
    with pytest.raises(BudgetRejected):BudgetLedger(tmp_path/'bad.db',replace(OfflineBudgetPolicy(),**patch))


def test_real_network_transport_is_never_enabled(tmp_path):
    ledger=BudgetLedger(tmp_path/'budget.db',OfflineBudgetPolicy())
    with pytest.raises(BudgetRejected,match='real_network_transport_disabled'):OfflineBudgetTransport(ledger,httpx.HTTPTransport())


def test_duplicate_json_and_byte_limits(tmp_path):
    ledger,transport,calls=make(tmp_path)
    for body in [b'{"model":"offline-model","model":"other"}',b'not-json',b'x'*65537]:
        with pytest.raises(BudgetRejected):transport.handle_request(httpx.Request('POST',ledger.policy.endpoint,content=body))
    assert calls==[] and ledger.snapshot()['requests_reserved']==0


def test_terminal_status_cannot_regress_or_expose_prompt(tmp_path):
    ledger,transport,calls=make(tmp_path)
    transport.handle_request(request(ledger.policy))
    ledger.finish(1,'failed')
    snap=ledger.snapshot()
    assert snap['statuses']=={'response_received':1}
    text=json.dumps(snap)
    assert 'synthetic math question' not in text and 'fixture.invalid' not in text and 'offline-model' not in text
