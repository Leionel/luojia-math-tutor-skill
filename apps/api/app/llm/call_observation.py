"""Per-request public spans. Payloads and private reasoning never enter receipts."""
import asyncio
from contextlib import contextmanager, asynccontextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
import time
import hashlib
from uuid import uuid4

from app.config import MODEL_CATALOG, PROVIDER_BASE_URLS
from app.llm.capabilities import capability
from app.llm.pricing import price, cost

_run = ContextVar("llm_observation_run", default=None)
_parent = ContextVar("llm_observation_parent", default=None)
_call = ContextVar("llm_observation_call", default=None)
_stage = ContextVar("llm_observation_stage", default="generation")


@contextmanager
def observation(sink, run_id):
    run_token = _run.set((sink, run_id)); parent_token = _parent.set(run_id)
    try: yield
    finally:
        _parent.reset(parent_token); _run.reset(run_token)


@contextmanager
def model_stage(stage):
    token = _stage.set(stage)
    try: yield
    finally: _stage.reset(token)


def reported_usage(raw):
    if not isinstance(raw, dict): return None
    names = ("prompt_tokens", "completion_tokens", "total_tokens")
    if any(type(raw.get(k)) is not int or not 0 <= raw[k] <= 100000000 for k in names): return None
    if raw["total_tokens"] != raw["prompt_tokens"] + raw["completion_tokens"]: return None
    return {k: raw[k] for k in names}


def usage_received(raw):
    call = _call.get()
    if call is not None:
        parsed = reported_usage(raw)
        # Conflicting usage packets are unknown; never take a convenient maximum.
        if call.get("usage_seen") and call["usage"] != parsed:
            call["usage_conflict"] = True
        call["usage_seen"] = True
        call["usage"] = None if call.get("usage_conflict") else parsed
        for group, token in (("prompt_tokens_details", "cached_tokens"), ("completion_tokens_details", "reasoning_tokens")):
            detail = raw.get(group) if isinstance(raw,dict) else None
            if isinstance(detail,dict) and detail.get(token,0) != 0:
                call["unsupported_token_pricing"] = True


def content_received(text):
    call = _call.get()
    if call is not None and call["first_content_ms"] is None and isinstance(text, str) and text.strip():
        if call.get("request_clock") is not None:
            call["first_content_ms"] = round((time.perf_counter()-call["request_clock"])*1000, 2)


def native_call_received(call_id):
    call = _call.get()
    if call is not None: call["tool_call_id"] = hashlib.sha256(call_id.encode()).hexdigest()[:32]


def current_call_id():
    call = _call.get()
    return call["fields"]["span_id"] if call is not None else None


async def request_dispatched():
    call = _call.get()
    current = _run.get()
    if call is not None and current is not None:
        call["request_sent"] = True
        await current[0]("model", "started", **call["fields"], request_sent=True)
        call["request_clock"] = time.perf_counter()


def call_degraded(code):
    call = _call.get()
    if call is not None:
        call.update(status="degraded", error_code=code)


def safe_identity(settings, model):
    try:
        base, _ = settings.resolve_request(model)
    except ValueError:
        return {"model_alias": None, "provider": "unknown"}
    selected = model or settings.llm_model
    return {"model_alias": selected if selected in MODEL_CATALOG else None,
            "provider": next((name for name, url in PROVIDER_BASE_URLS.items() if url and base.rstrip('/')==url.rstrip('/')), "unknown")}


@asynccontextmanager
async def span(phase, **metadata):
    current = _run.get()
    if current is None:
        yield {}
        return
    sink, run_id = current
    identity = uuid4().hex
    started = datetime.now(timezone.utc).isoformat()
    data = {"clock": time.perf_counter(), "usage": None, "first_content_ms": None, "request_sent":False}
    fields = {"span_id": identity, "parent_id": _parent.get() or run_id,
              "call_id": identity, "started_at": started, **metadata}
    data["fields"] = fields
    await sink(phase, "started", **fields)
    parent_token = _parent.set(identity); call_token = _call.set(data if phase == "model" else _call.get())
    status, code = "succeeded", None
    try:
        yield data
    except asyncio.CancelledError:
        status, code = "cancelled", "call_cancelled"
        raise
    except Exception as exc:
        status = "failed"
        from app.llm.completion_protocol import ModelCompletionError
        code = exc.code if isinstance(exc, ModelCompletionError) else "call_failed"
        raise
    finally:
        _call.reset(call_token); _parent.reset(parent_token)
        ending = {**fields, "ended_at": datetime.now(timezone.utc).isoformat(),
                  "duration_ms": round((time.perf_counter()-data["clock"])*1000, 2),
                  "error_code": data.get("error_code") or code}
        if phase == "model":
            ending.update(usage=data["usage"], usage_source="provider_reported" if data["usage"] is not None else "missing",
                          first_content_ms=data["first_content_ms"], request_sent=data["request_sent"])
            ending["cost"] = None if data.get("unsupported_token_pricing") else cost(data["usage"], metadata.get("pricing"))
            if data.get("tool_call_id"): ending["tool_call_id"] = data["tool_call_id"]
        await sink(phase, data.get("status", status), **ending)


def _model_fields(client, args, kwargs, embedding=False):
    model = kwargs.get("model", args[3] if len(args)>3 else None)
    if embedding:
        return {"provider":"unknown", "model_alias":None, "model_stage":"embedding", "capability":{"source":"unknown"}}
    return {**safe_identity(client.settings, model), "model_stage": _stage.get(),
            "capability": capability(client.settings, model), "pricing":price(client.settings, model)}


def metered_completion(function):
    @wraps(function)
    async def wrapped(*args, **kwargs):
        async with span("model", **_model_fields(args[0], args, kwargs, embedding=function.__name__=="create_embedding")):
            return await function(*args, **kwargs)
    wrapped.__metered__ = True
    return wrapped


def metered_stream(function):
    @wraps(function)
    async def wrapped(*args, **kwargs):
        async with span("model", **_model_fields(args[0], args, kwargs)):
            iterator = function(*args, **kwargs)
            try:
                async for item in iterator:
                    yield item
            finally:
                await iterator.aclose()
    wrapped.__metered__ = True
    return wrapped


def usage_summary(steps, truncated=False):
    begun = {s["span_id"] for s in steps if s.get("span_id") and s["phase"]=="model" and s["status"]=="started"}
    ends = {s["span_id"]:s for s in steps if s.get("span_id") in begun and s["status"]!="started"}
    sent = {s["span_id"] for s in steps if s.get("span_id") in begun and s.get("request_sent") is True}
    known = [s["usage"] for s in ends.values() if reported_usage(s.get("usage")) is not None]
    if not begun: return None
    costs = [s["cost"] for s in ends.values() if s.get("cost")]
    from decimal import Decimal
    compatible = len({(v["currency"],v["price_version"]) for v in costs})==1
    combined = {"amount":str(sum((Decimal(v["amount"]) for v in costs), Decimal(0))),
                "currency":costs[0]["currency"], "price_version":costs[0]["price_version"],
                "scope":"reported_plain_tokens_estimate"} if costs and compatible else None
    return {"version":"usage-v1", "model_attempts":len(begun), "model_requests":len(sent), "reported_requests":len(known),
            "coverage":"complete" if len(known)==len(sent) and len(ends)==len(begun) and not truncated else "partial",
            "known_tokens":{k:sum(u[k] for u in known) for k in ("prompt_tokens","completion_tokens","total_tokens")},
            "cost":combined, "cost_status":"complete" if len(costs)==len(sent) and len(ends)==len(begun) and compatible and not truncated else "partial" if combined else "unavailable"}
