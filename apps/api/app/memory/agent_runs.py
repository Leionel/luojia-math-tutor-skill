"""Durable, owner-scoped execution receipts; never store model or student payloads."""
import json
import math
import re
from datetime import datetime, timedelta, timezone

RUN_VERSION = "run-v1"
MAX_STEPS = 64
TERMINAL = {"succeeded", "clarification", "failed", "cancelled", "interrupted"}
PHASES = {"routing", "vision", "context", "review", "generation", "model", "tool", "guard", "delivery"}
STEP_STATUSES = {"started", "succeeded", "degraded", "failed", "cancelled", "clarification"}
ERROR_CODES = {"workflow_failed", "answer_withheld", "answer_guard_unavailable", "model_timeout",
               "model_unreachable", "model_auth_failed", "generation_failed", "execution_record_failed",
               "root_attempt_invalid", "model_not_configured", "model_stream_incomplete", "model_output_truncated",
               "model_output_filtered", "model_tool_call_unsupported", "model_response_invalid",
               "model_provider_error", "model_empty_output", "code_rejected", "tool_timeout", "tool_unavailable"}
ERROR_CODES |= {"model_tool_budget", "tool_parameters_invalid", "tool_input_budget", "tool_output_budget",
                "tool_worker_failed", "tool_empty_result", "tool_policy_rejected", "call_cancelled", "call_failed", "call_interrupted"}


def clean_step(step):
    # Explicit allowlist at the persistence boundary, including nested fields.
    if step.get("phase") not in PHASES or step.get("status") not in STEP_STATUSES:
        raise ValueError("invalid execution step")
    clean = {"seq": int(step["seq"]), "phase": step["phase"], "status": step["status"]}
    duration = step.get("duration_ms")
    if isinstance(duration, (float, int)) and math.isfinite(duration) and duration >= 0:
        clean["duration_ms"] = round(min(duration, 86400000), 2)
    if isinstance(step.get("round"), int) and 0 <= step["round"] <= 4:
        clean["round"] = step["round"]
    if isinstance(step.get("error_code"),str) and step["error_code"] in ERROR_CODES:
        clean["error_code"] = step["error_code"]
    for key in ("span_id", "call_id", "tool_call_id"):
        if isinstance(step.get(key), str) and re.fullmatch(r"[a-f0-9]{32}", step[key]): clean[key] = step[key]
    if isinstance(step.get("parent_id"), str) and re.fullmatch(r"[a-f0-9]{32}|[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", step["parent_id"]):
        clean["parent_id"] = step["parent_id"]
    for key in ("started_at", "ended_at"):
        try:
            date = datetime.fromisoformat(step[key])
            if date.tzinfo is not None: clean[key] = date.isoformat()
        except (KeyError, TypeError, ValueError): pass
    if isinstance(step.get("tool_name"),str) and step["tool_name"] in {"numerical_run", "math_differentiate"}: clean["tool_name"] = step["tool_name"]
    if isinstance(step.get("model_stage"),str) and step["model_stage"] in {"generation", "routing", "review", "guard_repair", "vision", "embedding"}: clean["model_stage"] = step["model_stage"]
    from app.config import MODEL_CATALOG, PROVIDER_BASE_URLS
    if isinstance(step.get("model_alias"),str) and step["model_alias"] in MODEL_CATALOG: clean["model_alias"] = step["model_alias"]
    if isinstance(step.get("provider"),str) and step["provider"] in {*PROVIDER_BASE_URLS, "unknown"} and step["provider"] != "custom": clean["provider"] = step["provider"]
    from app.llm.call_observation import reported_usage
    if step.get("phase") == "model" and clean.get("span_id"):
        if type(step.get("request_sent")) is bool: clean["request_sent"] = step["request_sent"]
        usage = reported_usage(step.get("usage"))
        if step.get("status") != "started":
            clean.update(usage=usage, usage_source="provider_reported" if usage is not None else "missing")
        fee = step.get("cost")
        if isinstance(fee,dict) and usage is not None and fee.get("scope")=="reported_plain_tokens_estimate" and isinstance(fee.get("currency"),str) and fee["currency"] in {"USD","CNY"}:
            from decimal import Decimal, InvalidOperation
            try:
                amount = Decimal(fee["amount"])
                if amount.is_finite() and 0 <= amount <= 200000000 and re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:-v\d{1,3})?",fee["price_version"]):
                    clean["cost"] = {"amount":str(amount), "currency":fee["currency"], "price_version":fee["price_version"], "scope":fee["scope"]}
            except (ValueError,TypeError,KeyError,InvalidOperation): pass
        first = step.get("first_content_ms")
        if type(first) in (int,float) and math.isfinite(first) and 0 <= first <= 86400000: clean["first_content_ms"] = round(first,2)
        cap = step.get("capability")
        if isinstance(cap,dict) and isinstance(cap.get("source"),str) and cap["source"] in {"unknown", "operator_verified", "offline_fixture"}:
            projected = {"source":cap["source"], "checked_at":None}
            for k in ("tool_calls", "stream_usage", "streaming"):
                projected[k] = cap.get(k) if type(cap.get(k)) is bool else None
            for k in ("input_token_limit", "output_token_limit"):
                projected[k] = cap.get(k) if type(cap.get(k)) is int and 1 <= cap[k] <= 1000000 else None
            try:
                date = datetime.fromisoformat(cap["checked_at"])
                if date.tzinfo is not None: projected["checked_at"] = date.isoformat()
            except (KeyError, TypeError, ValueError): pass
            clean["capability"] = projected
    return clean


def close_open_spans(steps, status, seq):
    closed = {s.get("span_id") for s in steps if s["status"] != "started"}
    for step in list(steps):
        if step.get("span_id") and step["span_id"] not in closed:
            if len(steps) >= MAX_STEPS: break
            seq += 1
            steps.append(clean_step({**step, "seq":seq, "status":"cancelled" if status=="cancelled" else "failed",
                "ended_at":datetime.now(timezone.utc).isoformat(), "error_code":"call_interrupted"}))
            closed.add(step["span_id"])
    return seq


def public_run(row):
    from app.llm.call_observation import usage_summary
    return {"version": RUN_VERSION, "scope": "execution_only", "run_id": row["id"],
            "status": row["status"], "seq": row["seq"], "steps": json.loads(row["steps"]),
            "truncated": bool(row["truncated"]), "message_id": row["message_id"],
            "created_at": row["created_at"], "updated_at": row["updated_at"],
            "prompt_version": row["prompt_version"], "guard_version": row["guard_version"],
            "usage": usage_summary(json.loads(row["steps"]), bool(row["truncated"])), "model_alias": row["model_alias"], "parent_run_id": row["parent_run_id"]}


class AgentRunRepository:
    def start_agent_run(self, run_id, session_id, user_id, prompt_version, guard_version, parent_run_id=None, model_alias=None):
        from app.config import MODEL_CATALOG
        model_alias = model_alias if model_alias in MODEL_CATALOG else None
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            owner = conn.execute("select user_id from sessions where id=?", (session_id,)).fetchone()
            if owner is None or owner[0] != user_id:
                raise ValueError("execution session unavailable")
            if parent_run_id:
                parent = conn.execute("select status from agent_runs where id=? and session_id=? and user_id=?",
                                      (parent_run_id,session_id,user_id)).fetchone()
                if parent is None or parent[0] == "running":
                    raise ValueError("parent execution unavailable")
            conn.execute("""insert into agent_runs(id,session_id,user_id,status,seq,steps,truncated,
                         prompt_version,guard_version,created_at,updated_at,parent_run_id,model_alias)
                         values(?,?,?,'running',0,'[]',0,?,?,?,?,?,?)""",
                         (run_id,session_id,user_id,prompt_version,guard_version,now,now,parent_run_id,model_alias))

    def append_agent_run_step(self, run_id, user_id, step):
        clean = clean_step(step)
        with self.connect() as conn:
            row = conn.execute("select * from agent_runs where id=? and user_id=?", (run_id,user_id)).fetchone()
            if row is None or row["status"] != "running" or clean["seq"] != row["seq"] + 1:
                return False
            steps = json.loads(row["steps"])
            truncated = len(steps) >= MAX_STEPS
            if not truncated:
                steps.append(clean)
            return conn.execute("""update agent_runs set seq=?,steps=?,truncated=?,updated_at=?
                    where id=? and user_id=? and status='running' and seq=?""",
                    (clean["seq"], json.dumps(steps), int(truncated or row["truncated"]),
                     datetime.now(timezone.utc).isoformat(), run_id,user_id,row["seq"])).rowcount == 1

    def heartbeat_agent_run(self, run_id, user_id):
        with self.connect() as conn:
            conn.execute("update agent_runs set updated_at=? where id=? and user_id=? and status='running'",
                         (datetime.now(timezone.utc).isoformat(),run_id,user_id))

    @staticmethod
    def _finish_agent_run(conn, run_id, user_id, status, message_id=None):
        if status not in TERMINAL:
            raise ValueError("invalid execution terminal")
        row = conn.execute("select seq,steps,truncated from agent_runs where id=? and user_id=? and status='running'",
                           (run_id,user_id)).fetchone()
        if row is None:
            return False
        steps = json.loads(row["steps"])
        seq = close_open_spans(steps, status, row["seq"])
        truncated = bool(row["truncated"]) or len(steps) >= MAX_STEPS
        if len(steps) < MAX_STEPS:
            steps.append({"seq":seq+1,"phase":"delivery","status":status if status in STEP_STATUSES else "failed"})
        return conn.execute("""update agent_runs set status=?,message_id=?,updated_at=?,seq=?,steps=?,truncated=?
                    where id=? and user_id=? and status='running' and seq=?""",
                    (status,message_id,datetime.now(timezone.utc).isoformat(),seq+1,json.dumps(steps),int(truncated),
                     run_id,user_id,row["seq"])).rowcount == 1

    def finish_agent_run(self, run_id, user_id, status):
        with self.connect() as conn:
            return self._finish_agent_run(conn,run_id,user_id,status)

    def recover_stale_agent_runs(self, lease_seconds=120):
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=lease_seconds)).isoformat()
        with self.connect() as conn:
            rows = conn.execute("select id,user_id from agent_runs where status='running' and updated_at<?", (cutoff,)).fetchall()
            return sum(self._finish_agent_run(conn, row["id"], row["user_id"], "interrupted") for row in rows)

    def list_agent_runs(self, session_id, user_id, terminal_only=True):
        with self.connect() as conn:
            rows = conn.execute("select * from agent_runs where session_id=? and user_id=? and hidden=0" +
                                (" and status!='running'" if terminal_only else "") + " order by created_at",
                                (session_id,user_id)).fetchall()
        return [public_run(row) for row in rows]

    def get_agent_run(self, run_id, session_id, user_id):
        with self.connect() as conn:
            row = conn.execute("select * from agent_runs where id=? and session_id=? and user_id=?",
                               (run_id,session_id,user_id)).fetchone()
        return public_run(row) if row else None
