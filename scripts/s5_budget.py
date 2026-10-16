"""S5.3 offline-only pre-send budget contracts. No real-provider transport is enabled."""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass,asdict
from decimal import Decimal,InvalidOperation
import asyncio,hashlib,json,re,sqlite3
from pathlib import Path
import httpx


class BudgetRejected(ValueError):
    def __init__(self,code):self.code=code;super().__init__(code)


def amount(value) -> Decimal:
    if type(value) not in {str,int,Decimal}:raise BudgetRejected('invalid_amount')
    try:result=Decimal(value)
    except InvalidOperation:raise BudgetRejected('invalid_amount') from None
    if not result.is_finite() or result<0 or result>Decimal('1000000000000') or result.as_tuple().exponent < -12:raise BudgetRejected('invalid_amount')
    return result


@dataclass(frozen=True)
class OfflineBudgetPolicy:
    endpoint:str='https://fixture.invalid/v1/chat/completions'
    model:str='offline-model'
    max_requests:int=51
    currency:str='CNY'
    max_cost:str='10'
    per_request_upper_cost:str='0.01'
    max_output_tokens:int=1000
    price_contract_kind:str='synthetic_fixture'
    all_billable_items_bounded:bool=True

    def validate(self):
        url=httpx.URL(self.endpoint)
        if url.scheme!='https' or not url.host or url.username or url.password or url.query or url.fragment or url.port not in {None,443} or url.raw_path!=b'/v1/chat/completions':
            raise BudgetRejected('endpoint_not_allowed')
        if not isinstance(self.model,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',self.model):raise BudgetRejected('invalid_model')
        if type(self.max_requests) is not int or not 1<=self.max_requests<=10000:raise BudgetRejected('invalid_request_cap')
        if self.currency not in {'CNY','USD'}:raise BudgetRejected('unsupported_currency')
        if amount(self.max_cost)<=0 or amount(self.per_request_upper_cost)<=0:raise BudgetRejected('missing_cost_bound')
        if type(self.max_output_tokens) is not int or not 1<=self.max_output_tokens<=100000:raise BudgetRejected('invalid_output_cap')
        if self.price_contract_kind!='synthetic_fixture' or self.all_billable_items_bounded is not True:
            raise BudgetRejected('provider_cost_bound_not_verified')

    def fingerprint(self):
        self.validate()
        return hashlib.sha256(json.dumps(asdict(self),sort_keys=True).encode()).hexdigest()


class BudgetLedger:
    """SQLite reservation is atomic; cap/policy cannot silently reset on reopening."""
    def __init__(self,path:Path,policy:OfflineBudgetPolicy):
        self.path=Path(path);self.policy=policy;self.policy_hash=policy.fingerprint()
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS budget_state(id INTEGER PRIMARY KEY CHECK(id=1),policy_hash TEXT NOT NULL,requests INTEGER NOT NULL,upper_cost TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS reservations(id INTEGER PRIMARY KEY AUTOINCREMENT,request_hash TEXT NOT NULL,status TEXT NOT NULL);
            ''')
            conn.execute('BEGIN IMMEDIATE')
            row=conn.execute('SELECT policy_hash FROM budget_state WHERE id=1').fetchone()
            if row and row[0]!=self.policy_hash:raise BudgetRejected('ledger_policy_changed')
            if not row:conn.execute('INSERT INTO budget_state VALUES(1,?,0,?)',(self.policy_hash,'0'))
            conn.commit()

    @contextmanager
    def connect(self):
        conn=sqlite3.connect(self.path,timeout=5,isolation_level=None)
        try:yield conn
        finally:conn.close()

    def reserve(self,request_hash:str) -> int:
        if not re.fullmatch('[a-f0-9]{64}',request_hash):raise BudgetRejected('invalid_request_digest')
        if self.policy.fingerprint()!=self.policy_hash:raise BudgetRejected('ledger_policy_changed')
        with self.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=conn.execute('SELECT policy_hash,requests,upper_cost FROM budget_state WHERE id=1').fetchone()
            if row[0]!=self.policy_hash:raise BudgetRejected('ledger_policy_changed')
            if row[1]!=conn.execute('SELECT count(*) FROM reservations').fetchone()[0] or amount(row[2])!=amount(self.policy.per_request_upper_cost)*row[1]:
                raise BudgetRejected('ledger_integrity_mismatch')
            if row[1]>=self.policy.max_requests:raise BudgetRejected('request_budget_exhausted')
            upper=amount(row[2])+amount(self.policy.per_request_upper_cost)
            if upper>amount(self.policy.max_cost):raise BudgetRejected('cost_budget_exhausted')
            conn.execute('UPDATE budget_state SET requests=?,upper_cost=? WHERE id=1',(row[1]+1,str(upper)))
            cur=conn.execute("INSERT INTO reservations(request_hash,status) VALUES(?,'reserved')",(request_hash,))
            conn.commit();return cur.lastrowid

    def finish(self,id:int,status:str):
        if status not in {'response_received','failed','cancelled','redirect_rejected'}:raise BudgetRejected('invalid_terminal_status')
        with self.connect() as conn:
            conn.execute("UPDATE reservations SET status=? WHERE id=? AND status='reserved'",(status,id))

    def snapshot(self):
        with self.connect() as conn:
            requests,upper=conn.execute('SELECT requests,upper_cost FROM budget_state WHERE id=1').fetchone()
            statuses=dict(conn.execute('SELECT status,count(*) FROM reservations GROUP BY status').fetchall())
        return {'version':'s5-budget-ledger-v1','scope':'offline_mock_transport','policy_sha256':self.policy_hash,
            'endpoint_sha256':hashlib.sha256(self.policy.endpoint.encode()).hexdigest(),
            'requests_reserved':requests,'max_requests':self.policy.max_requests,'currency':self.policy.currency,
            'reserved_cost_upper_bound':upper,'max_cost':self.policy.max_cost,'actual_cost':None,
            'usage_coverage':'not_evaluated','statuses':statuses,'refund_policy':'no_refund',
            'live_ready':False,'pending':['real_provider_capability_unverified','billable_upper_bound_unverified','live_not_authorized']}


def strict_object(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise BudgetRejected('duplicate_payload_field')
        result[k]=v
    return result


class OfflineBudgetTransport(httpx.BaseTransport,httpx.AsyncBaseTransport):
    def __init__(self,ledger:BudgetLedger,transport:httpx.MockTransport):
        if type(transport) is not httpx.MockTransport:raise BudgetRejected('real_network_transport_disabled')
        self.ledger=ledger;self.transport=transport

    def prepare(self,request:httpx.Request):
        policy=self.ledger.policy
        expected=httpx.URL(policy.endpoint);url=request.url
        if request.method!='POST' or url!=expected or url.username or url.password:
            raise BudgetRejected('request_destination_not_allowed')
        if not request.content or len(request.content)>65536:raise BudgetRejected('request_bytes_exceeded')
        try:
            data=json.loads(request.content,object_pairs_hook=strict_object,
                            parse_constant=lambda _:(_ for _ in ()).throw(BudgetRejected('nonfinite_payload')))
        except (json.JSONDecodeError,UnicodeDecodeError):raise BudgetRejected('invalid_json') from None
        allowed={'model','messages','max_tokens','max_completion_tokens','stream','stream_options'}
        if not isinstance(data,dict) or set(data)-allowed or data.get('model')!=policy.model:raise BudgetRejected('payload_not_allowed')
        caps=[data[k] for k in ('max_tokens','max_completion_tokens') if k in data]
        if len(caps)!=1 or type(caps[0]) is not int or not 1<=caps[0]<=policy.max_output_tokens:raise BudgetRejected('output_token_bound_required')
        if 'stream' in data and type(data['stream']) is not bool:raise BudgetRejected('invalid_stream_flag')
        if 'stream_options' in data and data['stream_options']!={'include_usage':True}:raise BudgetRejected('invalid_stream_options')
        messages=data.get('messages')
        if not isinstance(messages,list) or not 1<=len(messages)<=64:raise BudgetRejected('invalid_messages')
        if any(not isinstance(m,dict) or set(m)!={'role','content'} or m['role'] not in {'system','user','assistant'} or not isinstance(m['content'],str) for m in messages):
            raise BudgetRejected('only_pure_text_messages_allowed')
        fingerprint=hashlib.sha256((self.ledger.policy_hash+hashlib.sha256(request.content).hexdigest()).encode()).hexdigest()
        return self.ledger.reserve(fingerprint)

    def handle_request(self,request):
        id=self.prepare(request)
        try:
            response=self.transport.handle_request(request)
            if 300<=response.status_code<400:
                self.ledger.finish(id,'redirect_rejected');response.close();raise BudgetRejected('redirect_not_allowed')
            self.ledger.finish(id,'response_received');return response
        except BaseException:
            self.ledger.finish(id,'failed');raise

    async def handle_async_request(self,request):
        # Short serialized local ledger transaction completes before the first await.
        id=self.prepare(request)
        try:
            response=await self.transport.handle_async_request(request)
            if 300<=response.status_code<400:
                self.ledger.finish(id,'redirect_rejected');await response.aclose();raise BudgetRejected('redirect_not_allowed')
            self.ledger.finish(id,'response_received');return response
        except asyncio.CancelledError:
            self.ledger.finish(id,'cancelled');raise
        except BaseException:
            self.ledger.finish(id,'failed');raise

    def close(self):self.transport.close()
    async def aclose(self):await self.transport.aclose()
