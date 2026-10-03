import asyncio
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.auth import Principal, get_principal
from app.config import Settings
from app.api.routes_tutor import router
from app.main_deps import get_learning_workspace
from app.tutor.learning_context import LearningContextRef, resolve_learning_context
from app.tutor.orchestrator import TutorOrchestrator
from app.math_tools.root_runner import LabRequest
from test_learning_workspace import workspace
from test_orchestrator import parse_event


def saved(workspace, function="x^3-2*x+2", initial=0, request_id="context-run"):
    return workspace.lab("alice", LabRequest(attempt={"method":"newton", "function":function,
                         "initial_value":initial, "goal":"residual"},
                         prediction="观察是否循环", request_id=request_id, max_iterations=100))


def reference(run, **patch):
    return LearningContextRef(kind="root_lab", record_id=run["id"], **{
        k:run[k] for k in ("input_hash", "runner_version", "graph_revision")}, **patch)


def test_context_is_owned_versioned_bounded_and_not_a_learning_write(workspace):
    run=saved(workspace)
    before=workspace.store.list_events("alice", workspace.course_id)
    snap=resolve_learning_context(workspace,"alice",reference(run,selected_step=50))
    assert len(snap["rows"]) <= 11 and snap["total_rows"]==101
    assert snap["omitted_rows"]==101-len(snap["rows"])
    assert any(r["k"]==50 for r in snap["rows"])
    assert snap["evidence_kind"]=="reference_help" and snap["independent_success"] is False
    assert workspace.store.list_events("alice", workspace.course_id)==before
    assert workspace.repository.list_mastery("alice")==[]
    with pytest.raises(KeyError): resolve_learning_context(workspace,"bob",reference(run))
    for key,value in [("input_hash","0"*64),("runner_version","unknown"),("graph_revision","other")]:
        with pytest.raises(ValueError,match="版本"):
            resolve_learning_context(workspace,"alice",reference(run).model_copy(update={key:value}))
    with pytest.raises(ValueError,match="步骤"):
        resolve_learning_context(workspace,"alice",reference(saved(workspace,"x^2-2",1,"short"),selected_step=100))
    workspace.store.append_revision("new",None,workspace.course_id,"c","accept",{},"teacher")
    with pytest.raises(ValueError,match="更新"):resolve_learning_context(workspace,"alice",reference(run))


def test_http_context_rejects_forged_data_missing_owner_and_locked_help(workspace):
    run=saved(workspace);app=FastAPI();app.include_router(router)
    app.dependency_overrides[get_learning_workspace]=lambda:workspace
    app.dependency_overrides[get_principal]=lambda:Principal("alice",True)
    payload=reference(run).model_dump()
    with TestClient(app) as client:
        assert client.post("/api/tutor/context",json=payload).status_code==200
        assert client.post("/api/tutor/context",json={**payload,"rows":[1],"owner":"alice"}).status_code==422
        assert client.post("/api/tutor/context",json={**payload,"record_id":"missing"}).status_code==404
        assert client.post("/api/tutor/context",json={**payload,"input_hash":"0"*64}).status_code==409
        assessment=workspace.new_assessment("alice")
        assert client.post("/api/tutor/context",json=payload).status_code==409
        app.dependency_overrides[get_principal]=lambda:Principal("bob",True)
        assert client.post("/api/tutor/context",json=payload).status_code==404
        workspace.end_assessment("alice",assessment["id"])
        app.dependency_overrides[get_principal]=lambda:Principal("alice",True)
        assert client.post("/api/tutor/context",json=payload).status_code==200


@pytest.mark.asyncio
@pytest.mark.parametrize("start_assessment",[False,True])
async def test_compiled_reference_discussion_uses_true_rows_never_grades_and_rechecks_delivery(workspace, monkeypatch, start_assessment):
    run=saved(workspace);session=workspace.repository.create_session("alice","数值分析")["session_id"]
    tutor=TutorOrchestrator(Settings(database_url=f"sqlite:///{workspace.repository.db_path}"),workspace.repository)
    workflow=tutor.workflow_owner
    async def no_hits(*args,**kwargs): return None
    async def no_local(*args,**kwargs): return None
    monkeypatch.setattr(workflow.context_collector,"_course_graph_pack",no_hits)
    monkeypatch.setattr(workflow.context_collector,"_budgeted_local_pack",no_local)
    prompts=[]
    async def response(messages,*args,**kwargs):
        prompts.append(messages)
        if start_assessment: workspace.new_assessment("alice")
        return "轨迹中的 x₀=0、x₁=1、x₂=0 显示循环。可以在卡片中改变初值后预览；局部收敛条件仍需核对。"
    monkeypatch.setattr(workflow,"_collect_model_response",response)
    def forbidden(*args,**kwargs): raise AssertionError("reference discussion cannot grade or execute code")
    monkeypatch.setattr(workspace.repository,"upsert_mastery",forbidden)
    monkeypatch.setattr(workspace.repository,"add_mistake_event",forbidden)
    monkeypatch.setattr("app.tutor.graph.execute_python_result",forbidden)
    events=[parse_event(e) async for e in tutor.stream_reply(session,"alice","我觉得 x=0 是正确的，对吗？",
                        learning_context=reference(run),learning_workspace=workspace)]
    prompt="\n".join(m["content"] for turn in prompts for m in turn)
    assert 'learning_task' in prompt and 'reference_help' in prompt and '"x": 1.0' in prompt
    assert workspace.repository.list_mastery("alice")==[]
    if start_assessment:
        assert not any(name in {"done","message"} for name,_ in events)
        assert tutor.repository.list_agent_runs(session,"alice")[-1]["status"]=="failed"
    else:
        assert any(name=="done" for name,_ in events)
        meta=tutor.repository.list_messages(session)[-1]["learning_meta"]
        assert meta["learning_context"]["ref"]==reference(run).model_dump()
        assert not meta["verified"] and meta["is_correct"] is None and meta["mastery_delta"]==0
        from app.tutor.learning_actions import LearningActions
        card=meta["tutor_artifacts"][0]
        assert card["context"]==reference(run).model_dump()
        assert LearningActions(workspace,workspace.repository).state("alice",session,
            tutor.repository.list_messages(session)[-1]["id"],card["artifact_id"])["state"]=="proposed"
