import asyncio
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.auth import Principal, get_principal
from app.config import Settings
from app.api.routes_tutor import router
from app.main_deps import get_learning_workspace
from app.tutor.learning_context import LearningContextRef, NewtonActivityClaimRef, resolve_learning_context
from app.tutor.newton_activity import NewtonActivity, ACTIVITY_ID, ACTIVITY_VERSION
from app.tutor.orchestrator import TutorOrchestrator
from app.tutor.prompt_builder import build_messages
from app.math_tools.verifier import VerifyResult
from app.tutor.intent_router import Intent
from app.math_tools.root_runner import LabRequest
from app.math_tools.numerical_lab import LinearTask, check_result, run_numerical
from app.tutor.learning_context import LinearContextRef
from test_learning_workspace import workspace
from test_orchestrator import parse_event


def saved(workspace, function="x^3-2*x+2", initial=0, request_id="context-run"):
    return workspace.lab("alice", LabRequest(attempt={"method":"newton", "function":function,
                         "initial_value":initial, "goal":"residual"},
                         prediction="观察是否循环", request_id=request_id, max_iterations=100))


def reference(run, **patch):
    return LearningContextRef(kind="root_lab", record_id=run["id"], **{
        k:run[k] for k in ("input_hash", "runner_version", "graph_revision")}, **patch)


def saved_claim(workspace):
    activity = NewtonActivity(workspace)
    activity.predict("alice", "predict-a1", "我猜会逐渐收敛", "导数非零")
    state = activity.reveal("alice", "reveal-a1", "observe")
    run = state["run"]
    activity.explain("alice", "explain-a1", run["id"], run["input_hash"],
                     "x₁=1 是对的，所以任意初值都收敛。")
    claim = NewtonActivityClaimRef(activity_id=ACTIVITY_ID, activity_version=ACTIVITY_VERSION,
                                   claim_kind="explanation", request_id="explain-a1", revision_count=0)
    return activity, run, reference(run, activity_claim=claim)


def saved_linear(workspace, method="jacobi", matrix=None, rhs=None, limit=1):
    task=LinearTask(method=method, matrix=matrix or [[4,1],[1,3]], rhs=rhs or [1,2],
                    initial=[0,0], limit=limit, tolerance=1e-12)
    record={**run_numerical(task),"id":f"linear-{method}","source_hash":"a"*64,"prediction":"预计收敛"}
    workspace.save("alice","numerical_lab",record["id"],record)
    ref=LinearContextRef(kind="linear_lab",record_id=record["id"],source_hash=record["source_hash"],
                         schema_version="numerical-lab-v1",selected_step=1)
    return record,ref


@pytest.mark.parametrize("method,expected",[("jacobi",[0.25,2/3]),("gauss_seidel",[0.25,7/12])])
def test_a3_linear_reference_rechecks_update_order_and_keeps_help_boundary(workspace,method,expected):
    _,ref=saved_linear(workspace,method)
    before=workspace.store.list_events("alice",workspace.course_id)
    snapshot=resolve_learning_context(workspace,"alice",ref)
    assert snapshot["linear_check"]["expected_vector"]==pytest.approx(expected)
    assert snapshot["linear_check"]["condition_sufficient"] is True
    assert snapshot["linear_check"]["error_bound_includes_roundoff"] is False
    assert snapshot["independent_success"] is False
    assert workspace.store.list_events("alice",workspace.course_id)==before
    assert workspace.repository.list_mastery("alice")==[]
    with pytest.raises(KeyError):resolve_learning_context(workspace,"bob",ref)


def test_a3_linear_small_residual_does_not_become_same_sized_solution_error(workspace):
    record,ref=saved_linear(workspace,matrix=[[1,0],[0,1e-8]],rhs=[1,1e-8])
    snapshot=resolve_learning_context(workspace,"alice",ref)
    task=LinearTask.model_validate(record["task"])
    assert check_result(task,[1,0])["residual"]==pytest.approx(1e-8)
    assert max(abs(a-b) for a,b in zip([1,0],[1,1]))==1
    assert snapshot["linear_check"]["residual_infinity"]==0
    assert snapshot["linear_check"]["error_bound"]==0
    _,unknown_ref=saved_linear(workspace,method="gauss_seidel",matrix=[[1,2],[2,1]],limit=2)
    unknown=resolve_learning_context(workspace,"alice",unknown_ref)["linear_check"]
    assert unknown["condition_sufficient"] is False
    assert unknown["error_bound"] is None and unknown["unknown_reason"]


def test_a3_tampered_or_stale_linear_trajectory_fails_before_prompt(workspace):
    record,ref=saved_linear(workspace)
    record["rows"][1]["vector"][1]=0.5
    workspace.save("alice","numerical_lab",record["id"],record)
    with pytest.raises(ValueError,match="轨迹与参数"):
        resolve_learning_context(workspace,"alice",ref)
    record["rows"][1]["vector"][1]=2/3
    workspace.save("alice","numerical_lab",record["id"],record)
    with pytest.raises(ValueError,match="版本"):
        resolve_learning_context(workspace,"alice",ref.model_copy(update={"source_hash":"b"*64}))


def test_a3_linear_prompt_keeps_student_claim_separate_from_reference(workspace):
    _,ref=saved_linear(workspace,method="gauss_seidel")
    snapshot=resolve_learning_context(workspace,"alice",ref)
    messages=build_messages("离线固定教学指令","第二分量也是 2/3，对吗？",Intent.CHECK_STUDENT_STEP,
        "数值分析",[],VerifyResult(False,None,"本轮未触发自动验证。"),None,"socratic",
        learning_context=snapshot)
    developer=next(item["content"] for item in messages if item["role"]=="developer")
    runtime=json.loads(developer.split("[RUNTIME_CONTEXT]\n",1)[1].split("\n[/RUNTIME_CONTEXT]",1)[0])
    assert "linear_review_rule" in runtime and "不等于解误差" in runtime["linear_review_rule"]
    assert runtime["learning_task"]["linear_check"]["expected_vector"]==pytest.approx([0.25,7/12])
    assert runtime["learning_task"]["independent_success"] is False
    assert messages[-1]["content"]=="第二分量也是 2/3，对吗？"


def test_selected_activity_claim_is_server_read_and_stale_versions_fail_closed(workspace):
    activity, run, ref = saved_claim(workspace)
    plain = resolve_learning_context(workspace, "alice", reference(run))
    assert "student_claim" not in plain and "exact_check" not in plain
    before = workspace.store.list_events("alice", workspace.course_id)
    snap = resolve_learning_context(workspace, "alice", ref)
    assert snap["student_claim"]["text"] == "x₁=1 是对的，所以任意初值都收敛。"
    assert snap["student_claim"]["review_status"] == "unreviewed"
    assert snap["student_claim"]["evidence_kind"] == "student_process"
    assert snap["exact_check"]["scope"].startswith("仅对本题")
    assert snap["independent_success"] is False
    assert workspace.store.list_events("alice", workspace.course_id) == before
    assert workspace.repository.list_mastery("alice") == []
    with pytest.raises(KeyError): resolve_learning_context(workspace, "bob", ref)
    with pytest.raises(ValueError, match="版本"):
        resolve_learning_context(workspace, "alice", ref.model_copy(update={"input_hash": "0"*64}))
    with pytest.raises(ValueError, match="选择"):
        resolve_learning_context(workspace, "alice", ref.model_copy(update={"activity_claim":
            ref.activity_claim.model_copy(update={"request_id": "wrong"})}))
    activity.revise("alice", "revise-a1", run["id"], run["input_hash"], "现在只知道这个初值发生往复。")
    with pytest.raises(ValueError, match="修订版本"):
        resolve_learning_context(workspace, "alice", ref)
    revised_ref = reference(run, activity_claim=NewtonActivityClaimRef(
        activity_id=ACTIVITY_ID, activity_version=ACTIVITY_VERSION, claim_kind="revision",
        request_id="revise-a1", revision_count=1))
    revised = resolve_learning_context(workspace, "alice", revised_ref)
    assert revised["student_claim"]["text"].startswith("现在只知道")
    workspace.new_assessment("alice")
    with pytest.raises(ValueError, match="参考帮助"):
        resolve_learning_context(workspace, "alice", revised_ref)


def test_a2_offline_d0_d1_prompts_share_the_same_claim_and_only_d1_has_exact_check(workspace):
    _, _, ref = saved_claim(workspace)
    d1 = resolve_learning_context(workspace, "alice", ref)
    d0 = {key: value for key, value in d1.items() if key != "exact_check"}
    def runtime(snapshot):
        messages = build_messages("离线固定教学指令", "请检查我选中的解释。", Intent.CHECK_STUDENT_STEP,
            "数值分析", [], VerifyResult(False, None, "本轮未触发自动验证。"), None, "socratic",
            pedagogical_action="ask_question", learning_context=snapshot)
        developer = next(item["content"] for item in messages if item["role"] == "developer")
        return json.loads(developer.split("[RUNTIME_CONTEXT]\n", 1)[1].split("\n[/RUNTIME_CONTEXT]", 1)[0])
    direct, tool_enhanced = runtime(d0), runtime(d1)
    assert direct["learning_task"]["student_claim"] == tool_enhanced["learning_task"]["student_claim"]
    assert direct["learning_task"]["rows"] == tool_enhanced["learning_task"]["rows"]
    assert "exact_check" not in direct["learning_task"]
    assert tool_enhanced["learning_task"]["exact_check"]["scope"].startswith("仅对本题")
    assert direct["intent"] == tool_enhanced["intent"] == "check_student_step"


def test_activity_claim_http_ref_never_accepts_browser_supplied_text(workspace):
    activity, run, ref = saved_claim(workspace)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_learning_workspace] = lambda: workspace
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    with TestClient(app) as client:
        payload = ref.model_dump(mode="json")
        assert client.post("/api/tutor/context", json=payload).json()["student_claim"]["text"].startswith("x₁=1")
        assert client.post("/api/tutor/context", json={**payload, "student_claim": {"text": "伪造"}}).status_code == 422
        forged = {**payload, "activity_claim": {**payload["activity_claim"], "text": "伪造"}}
        assert client.post("/api/tutor/context", json=forged).status_code == 422
        app.dependency_overrides[get_principal] = lambda: Principal("bob", True)
        assert client.post("/api/tutor/context", json=payload).status_code == 404
        app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
        activity.revise("alice", "revise-http", run["id"], run["input_hash"], "现在知道局部条件还需核对。")
        assert client.post("/api/tutor/context", json=payload).status_code == 409


@pytest.mark.asyncio
async def test_selected_claim_reaches_teacher_as_unreviewed_text_without_grading(workspace, monkeypatch):
    _, _, ref = saved_claim(workspace)
    session = workspace.repository.create_session("alice", "数值分析")["session_id"]
    tutor = TutorOrchestrator(Settings(database_url=f"sqlite:///{workspace.repository.db_path}"), workspace.repository)
    workflow = tutor.workflow_owner
    async def no_hits(*args, **kwargs): return None
    monkeypatch.setattr(workflow.context_collector, "_course_graph_pack", no_hits)
    monkeypatch.setattr(workflow.context_collector, "_budgeted_local_pack", no_hits)
    prompts = []
    async def response(messages, *args, **kwargs):
        prompts.append(messages)
        return "x₁=1 有精确代入支持；任意初值收敛不能由此推出。请检查局部定理条件。"
    monkeypatch.setattr(workflow, "_collect_model_response", response)
    events = [parse_event(e) async for e in tutor.stream_reply(
        session, "alice", "请检查我选中的解释。", learning_context=ref, learning_workspace=workspace)]
    assert any(name == "done" for name, _ in events)
    prompt = "\n".join(item["content"] for turn in prompts for item in turn)
    assert "x₁=1 是对的，所以任意初值都收敛" in prompt
    assert "student_claim 是服务器从学生明确选中的活动版本读取的原话" in prompt
    assert "f(0)=2" in prompt
    meta = tutor.repository.list_messages(session)[-1]["learning_meta"]
    assert meta["intent"] == "check_student_step"
    assert meta["learning_context"]["student_claim"]["review_status"] == "unreviewed"
    assert not meta.get("tutor_artifacts")
    assert meta["verified"] is False and meta["is_correct"] is None
    assert workspace.repository.list_mastery("alice") == []


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
    monkeypatch.setattr("app.agents.code_executor.execute_python_result",forbidden)
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
