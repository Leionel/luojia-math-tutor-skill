"""Durable, owner-scoped execution receipts; never store model or student payloads."""
import json
import math
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
    return clean


def public_run(row):
    return {"version": RUN_VERSION, "scope": "execution_only", "run_id": row["id"],
            "status": row["status"], "seq": row["seq"], "steps": json.loads(row["steps"]),
            "truncated": bool(row["truncated"]), "message_id": row["message_id"],
            "created_at": row["created_at"], "updated_at": row["updated_at"],
            "prompt_version": row["prompt_version"], "guard_version": row["guard_version"],
            "usage": None, "model_alias": row["model_alias"], "parent_run_id": row["parent_run_id"]}


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
        truncated = bool(row["truncated"]) or len(steps) >= MAX_STEPS
        if len(steps) < MAX_STEPS:
            steps.append({"seq":row["seq"]+1,"phase":"delivery","status":status if status in STEP_STATUSES else "failed"})
        return conn.execute("""update agent_runs set status=?,message_id=?,updated_at=?,seq=?,steps=?,truncated=?
                    where id=? and user_id=? and status='running' and seq=?""",
                    (status,message_id,datetime.now(timezone.utc).isoformat(),row["seq"]+1,json.dumps(steps),int(truncated),
                     run_id,user_id,row["seq"])).rowcount == 1

    def finish_agent_run(self, run_id, user_id, status):
        with self.connect() as conn:
            return self._finish_agent_run(conn,run_id,user_id,status)

    def recover_stale_agent_runs(self, lease_seconds=120):
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=lease_seconds)).isoformat()
        with self.connect() as conn:
            return conn.execute("""update agent_runs set status='interrupted',updated_at=?
                    where status='running' and updated_at<?""",
                    (datetime.now(timezone.utc).isoformat(),cutoff)).rowcount

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
