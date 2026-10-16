"""Per-request trace recorder with a leased durable terminal, not a graph checkpoint."""
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.memory.agent_runs import RUN_VERSION, MAX_STEPS, clean_step, close_open_spans
from app.llm.call_observation import usage_summary
from app.tutor.answer_guard import GUARD_VERSION
from app.tutor.prompt_policy import PROMPT_VERSION


async def settled_call(function, *args, **kwargs):
    """Repeated cancellation cannot detach a committing SQLite write."""
    task = asyncio.create_task(asyncio.to_thread(function, *args, **kwargs))
    cancelled = False
    while True:
        try:
            return await asyncio.shield(task), cancelled
        except asyncio.CancelledError:
            if task.cancelled():
                raise
            cancelled = True


async def durable_call(function, *args, **kwargs):
    result, cancelled = await settled_call(function, *args, **kwargs)
    if cancelled:
        raise asyncio.CancelledError
    return result


class RunTrace:
    def __init__(self, repository, session_id, user_id, parent_run_id=None, model_alias=None):
        self.repository, self.session_id, self.user_id = repository, session_id, user_id
        self.run_id = str(uuid4())
        self.parent_run_id = parent_run_id
        from app.config import MODEL_CATALOG
        self.model_alias = model_alias if model_alias in MODEL_CATALOG else None
        self.started = False
        self.status = "running"
        self.seq = 0
        self.steps = []
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.lock = asyncio.Lock()

    async def start(self):
        try:
            await durable_call(self.repository.start_agent_run,self.run_id,self.session_id,self.user_id,PROMPT_VERSION,GUARD_VERSION,self.parent_run_id,self.model_alias)
        except asyncio.CancelledError:
            saved = await asyncio.to_thread(self.repository.get_agent_run,self.run_id,self.session_id,self.user_id)
            self.started = isinstance(saved,dict)
            raise
        else:
            self.started = True

    def snapshot(self, status=None, message_id=None):
        return {"version": RUN_VERSION,"scope":"execution_only","run_id":self.run_id,
                "status":status or self.status,"seq":self.seq,"steps":[dict(step) for step in self.steps],
                "truncated":self.seq > MAX_STEPS,"created_at":self.created_at,"updated_at":self.updated_at,
                "message_id":message_id,"prompt_version":PROMPT_VERSION,"guard_version":GUARD_VERSION,
                "usage":usage_summary(self.steps,self.seq > MAX_STEPS),"model_alias":self.model_alias,"parent_run_id":self.parent_run_id}

    async def step(self, phase, status, **fields):
        async with self.lock:
            if self.status != "running":
                return
            clean = clean_step({"seq":self.seq+1,"phase":phase,"status":status,**fields})
            accepted, cancelled = await settled_call(self.repository.append_agent_run_step,self.run_id,self.user_id,clean)
            if accepted is False:
                raise RuntimeError("execution sequence unavailable")
            self.seq += 1
            if len(self.steps) < MAX_STEPS:
                self.steps.append(clean)
            self.updated_at = datetime.now(timezone.utc).isoformat()
            if cancelled:
                raise asyncio.CancelledError

    def finish_args(self, status):
        return {"run_id":self.run_id,"user_id":self.user_id,"status":status}

    def terminal_snapshot(self,status):
        snapshot = self.snapshot(status)
        snapshot["seq"] = close_open_spans(snapshot["steps"], status, snapshot["seq"])
        snapshot["seq"] += 1
        if len(snapshot["steps"]) < MAX_STEPS:
            snapshot["steps"].append({"seq":snapshot["seq"],"phase":"delivery","status":status})
        snapshot["truncated"] = snapshot["seq"] > MAX_STEPS
        snapshot["usage"] = usage_summary(snapshot["steps"], snapshot["truncated"])
        return snapshot

    def committed(self,status):
        terminal = self.terminal_snapshot(status)
        self.seq,self.steps,self.status = terminal["seq"],terminal["steps"],status

    async def finish(self, status):
        if self.started and self.status == "running":
            await durable_call(self.repository.finish_agent_run,self.run_id,self.user_id,status)
            # The database terminal is authoritative if a concurrent completion won.
            saved = await asyncio.to_thread(self.repository.get_agent_run,self.run_id,self.session_id,self.user_id)
            self.status = saved["status"] if isinstance(saved,dict) else status
            if isinstance(saved,dict):
                self.seq,self.steps = saved["seq"],saved["steps"]

    async def heartbeat(self):
        while True:
            await asyncio.sleep(30)
            await durable_call(self.repository.heartbeat_agent_run,self.run_id,self.user_id)
