import asyncio
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.config import Settings
from app.memory.repository import Repository
from app.memory.migrations import _migration_006_agent_runs
from app.tutor.answer_guard import AnswerDeliveryError, guard_report
from test_orchestrator import make_orchestrator, parse_event, QuickWorkflow


@pytest.fixture
def store(tmp_path):
    repo = Repository(Settings(database_url=f"sqlite:///{tmp_path/'runs.db'}"))
    session = repo.create_session("student-one","综合")
    return repo,session["session_id"],"student-one"


def start(store):
    repo,session,owner=store
    run_id=str(uuid4())
    repo.start_agent_run(run_id,session,owner,"teaching-v2.4","delivery-v1")
    return run_id


def test_steps_are_monotonic_bounded_and_whitelisted(store):
    repo,session,owner=store; run=start(store)
    for seq in range(1,68):
        event={"seq":seq,"phase":"tool","status":"succeeded","duration_ms":2,
               "code":"private","stdout":"sk-private","prompt":"private","reasoning":"private"}
        assert repo.append_agent_run_step(run,owner,event)
        assert not repo.append_agent_run_step(run,owner,event)
    record=repo.get_agent_run(run,session,owner)
    assert record["seq"]==67 and len(record["steps"])==64 and record["truncated"]
    assert "private" not in json.dumps(record)
    assert record["usage"] is None
    assert not repo.append_agent_run_step(run,"another-user",{"seq":68,"phase":"tool","status":"started"})


def test_owner_and_session_are_checked_at_creation_and_read(store):
    repo,session,owner=store; run=start(store)
    with pytest.raises(ValueError):
        repo.start_agent_run(str(uuid4()),session,"other","v","v")
    assert repo.get_agent_run(run,session,"other") is None
    assert repo.get_agent_run(run,"wrong-session",owner) is None
    assert repo.list_agent_runs(session,"other",False)==[]


def test_explicit_retry_links_owned_terminal_without_replaying_history(store):
    repo,session,owner=store; parent=start(store)
    repo.finish_agent_run(parent,owner,"cancelled")
    child=str(uuid4())
    repo.start_agent_run(child,session,owner,"v","v",parent,"deepseek-v4-flash")
    record=repo.get_agent_run(child,session,owner)
    assert record["parent_run_id"]==parent and record["model_alias"]=="deepseek-v4-flash"
    assert record["seq"]==0 and record["steps"]==[] and repo.list_messages(session)==[]
    with pytest.raises(ValueError):repo.start_agent_run(str(uuid4()),session,owner,"v","v",child)
    with pytest.raises(ValueError):repo.start_agent_run(str(uuid4()),session,owner,"v","v",str(uuid4()))
    assert len(repo.list_agent_runs(session,owner,False))==2


def test_concurrent_terminal_is_immutable_and_late_steps_rejected(store):
    repo,session,owner=store; run=start(store)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda status:repo.finish_agent_run(run,owner,status),["cancelled","failed"]))
    assert sum(results)==1
    terminal=repo.get_agent_run(run,session,owner)["status"]
    assert not repo.finish_agent_run(run,owner,"succeeded")
    assert repo.get_agent_run(run,session,owner)["status"]==terminal
    assert not repo.append_agent_run_step(run,owner,{"seq":1,"phase":"model","status":"succeeded"})


def test_answer_and_terminal_commit_together_and_failure_rolls_back(store):
    repo,session,owner=store; run=start(store)
    with repo.connect() as conn:
        conn.execute("""create trigger fail_run_finish before update of status on agent_runs
                     begin select raise(abort,'injected commit failure'); end""")
    with pytest.raises(sqlite3.IntegrityError):
        repo.add_message(session,"assistant","candidate",agent_run_finish={"run_id":run,"user_id":owner,"status":"succeeded"})
    assert repo.list_messages(session)==[]
    assert repo.get_agent_run(run,session,owner)["status"]=="running"
    with repo.connect() as conn: conn.execute("drop trigger fail_run_finish")
    message=repo.add_message(session,"assistant","answer",agent_run_finish={"run_id":run,"user_id":owner,"status":"succeeded"})
    assert repo.get_agent_run(run,session,owner)["message_id"]==message
    with pytest.raises(ValueError):
        repo.add_message(session,"assistant","duplicate",agent_run_finish={"run_id":run,"user_id":owner,"status":"succeeded"})
    assert len(repo.list_messages(session))==1


def test_restart_only_recovers_expired_leases_and_never_replays(store):
    repo,session,owner=store; stale=start(store); active=start(store)
    expired=(datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat()
    with repo.connect() as conn: conn.execute("update agent_runs set updated_at=? where id=?",(expired,stale))
    assert repo.recover_stale_agent_runs()==1
    assert repo.get_agent_run(stale,session,owner)["status"]=="interrupted"
    assert repo.get_agent_run(active,session,owner)["status"]=="running"
    repo.heartbeat_agent_run(active,owner)
    assert repo.recover_stale_agent_runs()==0 and repo.list_messages(session)==[]


def test_old_database_backup_migration_and_transactional_ddl(store,tmp_path):
    repo,session,owner=store
    message=repo.add_message(session,"user","preserved old history")
    with repo.connect() as conn:
        conn.execute("drop table agent_runs"); conn.execute("delete from schema_migrations where version=6")
    backup=tmp_path/'before-migration.db'
    with sqlite3.connect(repo.db_path) as source, sqlite3.connect(backup) as target: source.backup(target)
    upgraded=Repository(Settings(database_url=f"sqlite:///{repo.db_path}"))
    assert upgraded.list_messages(session)[0]["id"]==message
    with sqlite3.connect(backup) as conn:
        assert conn.execute("select count(*) from schema_migrations where version=6").fetchone()[0]==0
        # Inject an index-name conflict after table creation; all new DDL rolls back.
        conn.execute("create index agent_runs_owner_session on sessions(id)")
        with pytest.raises(sqlite3.OperationalError): _migration_006_agent_runs(conn)
        conn.rollback()
        assert conn.execute("select name from sqlite_master where name='agent_runs'").fetchone() is None


@pytest.mark.asyncio
async def test_success_and_guard_failure_persist_real_sqlite_receipts(store):
    repo,session,owner=store; runner=make_orchestrator(QuickWorkflow()); runner.repository=repo
    events=[parse_event(e) async for e in runner.stream_reply(session,owner,"什么是导数")]
    done=next(data for name,data in events if name=="done")
    record=repo.list_agent_runs(session,owner)[0]
    assert record["status"]=="succeeded" and record["message_id"]==done["message_id"]
    class Withheld:
        async def ainvoke(self,state,config):
            raise AnswerDeliveryError(guard_report("withheld",("student_code_execution_claim",),1))
    runner.workflow=Withheld()
    events=[parse_event(e) async for e in runner.stream_reply(session,owner,"什么是导数")]
    assert not any(name=="done" for name,_ in events)
    meta=repo.list_messages(session)[-1]["learning_meta"]
    assert meta["answer_guard"]["status"]=="withheld" and meta["agent_run"]["status"]=="failed"
    assert repo.list_agent_runs(session,owner)[-1]["status"]=="failed"


@pytest.mark.asyncio
async def test_cancel_and_explicit_close_cleanup_before_durable_terminal(store):
    repo,session,owner=store; cleaned=asyncio.Event(); started=asyncio.Event()
    class Blocking:
        async def ainvoke(self,state,config):
            started.set()
            try: await asyncio.Event().wait()
            finally: cleaned.set()
    runner=make_orchestrator(Blocking());runner.repository=repo
    stream=runner.stream_reply(session,owner,"解释导数")
    await anext(stream);await anext(stream);await anext(stream)
    await asyncio.wait_for(started.wait(),1)
    await stream.aclose()
    assert cleaned.is_set()
    records=repo.list_agent_runs(session,owner)
    assert records[0]["status"]=="cancelled" and records[0]["message_id"] is None
    assert repo.list_messages(session)==[]


def test_routes_hide_foreign_runs_and_refresh_cancel_receipt(store):
    from app.api.routes_sessions import router
    from app.auth import Principal,get_principal
    from app.main_deps import get_repository,get_app_settings
    repo,session,owner=store; run=start(store);repo.finish_agent_run(run,owner,"cancelled")
    app=FastAPI();app.include_router(router)
    app.dependency_overrides[get_repository]=lambda:repo
    app.dependency_overrides[get_app_settings]=lambda:Settings(auth_required=False)
    app.dependency_overrides[get_principal]=lambda:Principal(owner,True,"student")
    with TestClient(app) as client:
        assert client.get(f"/api/sessions/{session}/runs/{run}").json()["status"]=="cancelled"
        item=client.get(f"/api/sessions/{session}/messages").json()["items"][0]
        assert item["learning_meta"]["agent_run"]["status"]=="cancelled"
        app.dependency_overrides[get_principal]=lambda:Principal("other",True,"student")
        assert client.get(f"/api/sessions/{session}/runs/{run}").status_code==404
        assert client.get(f"/api/sessions/{session}/runs").status_code==404


def test_demo_legacy_message_read_never_leaks_cached_foreign_receipts(store):
    from app.api.routes_sessions import router
    from app.auth import Principal,get_principal
    from app.main_deps import get_repository,get_app_settings
    repo,session,owner=store;run=start(store)
    repo.add_message(session,"assistant","legacy body",learning_meta={"agent_run":{"run_id":run}},
                     agent_run_finish={"run_id":run,"user_id":owner,"status":"succeeded"})
    app=FastAPI();app.include_router(router)
    app.dependency_overrides[get_repository]=lambda:repo
    app.dependency_overrides[get_app_settings]=lambda:Settings(auth_required=False)
    app.dependency_overrides[get_principal]=lambda:Principal("demo-user",False,"student")
    with TestClient(app) as client:
        # Preserve the existing public-demo conversation API, but require
        # ownership for the new execution receipt, including cached copies.
        items=client.get(f"/api/sessions/{session}/messages").json()["items"]
        assert "agent_run" not in items[0]["learning_meta"]
        assert client.get(f"/api/sessions/{session}/runs/{run}").status_code==404


@pytest.mark.asyncio
async def test_storage_failure_is_error_without_done_or_completed_answer(store,monkeypatch):
    repo,session,owner=store;runner=make_orchestrator(QuickWorkflow());runner.repository=repo
    def fail(*args,**kwargs):raise sqlite3.OperationalError("private database details")
    monkeypatch.setattr(repo,"add_message",fail)
    events=[parse_event(e) async for e in runner.stream_reply(session,owner,"什么是导数")]
    assert events[-1][0]=="error" and events[-1][1]["code"]=="execution_record_failed"
    assert not any(name=="done" for name,_ in events)
    assert repo.list_agent_runs(session,owner)[0]["status"]=="failed"
    assert "private" not in json.dumps(repo.list_agent_runs(session,owner))


def test_session_delete_cascades_and_truncate_does_not_resurrect_answer(store):
    repo,session,owner=store;run=start(store)
    message=repo.add_message(session,"assistant","answer",agent_run_finish={"run_id":run,"user_id":owner,"status":"succeeded"})
    # Run starts before answer timestamp. Truncation must also remove associated runs.
    repo.truncate_messages_after(session,message)
    assert repo.list_messages(session)==[]
    assert repo.list_agent_runs(session,owner)==[]
    start(store);repo.delete_session(session)
    assert repo.list_agent_runs(session,owner,False)==[]


@pytest.mark.asyncio
async def test_compiled_graph_emits_phase_receipts_and_guard_repair(store):
    from app.config import get_settings
    from app.tutor.graph import TutorWorkflow
    repo,session,owner=store
    workflow=TutorWorkflow(get_settings().model_copy(update={"database_url":f"sqlite:///{repo.db_path}"}),repo)
    responses=iter(["我已运行你的代码。","这里是静态阅读建议，没有执行你的代码。"])
    async def stream(*args,**kwargs):
        yield {"type":"content","content":next(responses)}
    workflow.llm.stream=stream
    runner=make_orchestrator(workflow.workflow);runner.repository=repo
    events=[parse_event(e) async for e in runner.stream_reply(session,owner,"什么是导数？")]
    assert events[-1][0]=="done"
    run=repo.list_agent_runs(session,owner)[0]
    assert {step["phase"] for step in run["steps"]}>={"routing","context","generation","model","guard","delivery"}
    assert not any(step["phase"]=="vision" for step in run["steps"])
    assert [step["seq"] for step in run["steps"]]==list(range(1,len(run["steps"])+1))
    metadata=repo.list_messages(session)[-1]["learning_meta"]
    assert metadata["answer_guard"]["status"]=="repaired"
    assert not metadata["verified"] and metadata["is_correct"] is None
    assert "静态阅读建议" not in json.dumps(run,ensure_ascii=False)


@pytest.mark.asyncio
async def test_task_cancellation_persists_cancelled_and_failed_start_creates_no_work(store,monkeypatch):
    repo,session,owner=store; started=asyncio.Event();cleaned=asyncio.Event()
    class Blocking:
        async def ainvoke(self,state,config):
            started.set()
            try: await asyncio.Event().wait()
            finally: cleaned.set()
    runner=make_orchestrator(Blocking());runner.repository=repo
    stream=runner.stream_reply(session,owner,"解释导数")
    await anext(stream);await anext(stream);await anext(stream)
    task=asyncio.create_task(anext(stream));await started.wait();task.cancel()
    with pytest.raises(asyncio.CancelledError):await task
    assert cleaned.is_set() and repo.list_agent_runs(session,owner)[0]["status"]=="cancelled"
    started.clear()
    def broken(*args):raise sqlite3.OperationalError("private start failure")
    monkeypatch.setattr(repo,"start_agent_run",broken)
    events=[parse_event(e) async for e in runner.stream_reply(session,owner,"解释导数")]
    assert events[-1][0]=="error" and not started.is_set()


@pytest.mark.asyncio
async def test_cancel_during_commit_preserves_durable_success(store,monkeypatch):
    import threading
    repo,session,owner=store;committed=threading.Event();release=threading.Event()
    original=repo.add_message
    def slow(*args,**kwargs):
        result=original(*args,**kwargs)
        committed.set();release.wait(2)
        return result
    monkeypatch.setattr(repo,"add_message",slow)
    runner=make_orchestrator(QuickWorkflow());runner.repository=repo
    async def consume():
        return [event async for event in runner.stream_reply(session,owner,"什么是导数")]
    task=asyncio.create_task(consume())
    assert await asyncio.to_thread(committed.wait,2)
    task.cancel();release.set()
    with pytest.raises(asyncio.CancelledError):await task
    record=repo.list_agent_runs(session,owner)[0]
    assert record["status"]=="succeeded" and record["message_id"]==repo.list_messages(session)[0]["id"]


@pytest.mark.asyncio
@pytest.mark.parametrize("spec_version",["2.3","2.4"])
async def test_asgi_disconnect_cancels_buffered_model_without_next_chunk(store,spec_version):
    from app.api.tutor_streaming import TutorStreamingResponse
    repo,session,owner=store; started=asyncio.Event();cleaned=asyncio.Event()
    class Blocking:
        async def ainvoke(self,state,config):
            started.set()
            try: await asyncio.Event().wait()
            finally: cleaned.set()
    runner=make_orchestrator(Blocking());runner.repository=repo
    response=TutorStreamingResponse(runner.stream_reply(session,owner,"解释导数"),media_type="text/event-stream")
    frames=[]
    async def receive():
        await started.wait()
        return {"type":"http.disconnect"}
    async def send(message):frames.append(message)
    await asyncio.wait_for(response({"type":"http","asgi":{"spec_version":spec_version}},receive,send),3)
    assert cleaned.is_set()
    assert repo.list_agent_runs(session,owner)[0]["status"]=="cancelled"
    assert not any(b"event: done" in frame.get("body",b"") for frame in frames)


@pytest.mark.asyncio
async def test_asgi_success_returns_terminal_and_closes_disconnect_listener(store):
    from app.api.tutor_streaming import TutorStreamingResponse
    repo,session,owner=store; runner=make_orchestrator(QuickWorkflow());runner.repository=repo
    listener_closed=asyncio.Event();frames=[]
    async def receive():
        try:await asyncio.Event().wait()
        finally:listener_closed.set()
    async def send(message):frames.append(message)
    response=TutorStreamingResponse(runner.stream_reply(session,owner,"导数"))
    await asyncio.wait_for(response({"type":"http","asgi":{"spec_version":"2.4"}},receive,send),3)
    assert listener_closed.is_set()
    assert repo.list_agent_runs(session,owner)[0]["status"]=="succeeded"
    assert sum(b"event: done" in frame.get("body",b"") for frame in frames)==1
