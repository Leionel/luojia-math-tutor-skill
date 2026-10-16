"""Protocol and delivery tests use deterministic fixtures, never model quality gold."""
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.auth import Principal, get_principal
from app.api.routes_tutor import router
from app.config import Settings
from app.main_deps import get_app_settings, get_learning_workspace, get_orchestrator, get_repository
from app.api.routes_sessions import router as sessions_router
from app.tutor.orchestrator import TutorOrchestrator
from app.tutor.teaching_decision import resolve_decision, source_bundle, bind_ui, visible_answer, decision_prompt
from app.tutor.intent_router import Intent
from test_learning_workspace import workspace
from test_learning_context import saved, reference, saved_claim, saved_linear


def state(snapshot=None, **patch):
    return {"message":"第三步比第二步小，所以一定收敛。", "mode":"socratic", "intent":Intent.CHECK_STUDENT_STEP,
            "hint_level":0, "pedagogical_action":"ask_question", "learning_context":snapshot, **patch}


def envelope(**patch):
    decision={"claim_ref":"claim:current", "evidence_refs":[], "known_conditions":[],
        "missing_conditions":["函数、迭代方法、初值、所比较的量"], "claim_status":"unknown",
        "action":"ask_missing_condition", "disclosure":"scaffolded", "reason":"比较量与前提尚未给出，先补条件。", "assessments":[]}
    ui=patch.pop("ui", [{"component":"ConditionChecklist", "evidence_ref":"claim:current"}])
    return "[TEACHING_DECISION]"+json.dumps({**decision,**patch},ensure_ascii=False)+"[/TEACHING_DECISION]"+"[INTELLIGENT_UI]"+json.dumps(ui,ensure_ascii=False)+"[/INTELLIGENT_UI][OUTPUT]请说明函数、迭代方法、初值，并说明比较的是误差、残差还是迭代值。"


def test_unknown_is_not_wrong_and_ui_is_model_selected():
    decision,ui=resolve_decision(envelope(),state())
    assert decision["status"]=="accepted" and decision["claim_status"]=="unknown"
    assert ui["selections"][0]["component"]=="ConditionChecklist"
    assert "TEACHING_DECISION" not in visible_answer(envelope())
    assert "LearningUI" in bind_ui(ui,"run-a","answer")["response"]


@pytest.mark.parametrize("patch",[
    {"evidence_refs":["fabricated:source"]}, {"claim_ref":"old:claim"}, {"disclosure":"full"},
    {"claim_status":"supported"}, {"action":"correct_claim"}, {"missing_conditions":[]},
    {"tool":"execute_python"}, {"known_conditions":["x"*501]},
])
def test_invalid_decisions_downgrade_without_authorizing_actions(patch):
    decision,ui=resolve_decision(envelope(**patch),state())
    assert decision["status"]=="fallback" and ui is None


@pytest.mark.parametrize("ui",[
    [{"component":"UnknownButton","evidence_ref":"claim:current"}],
    [{"component":"ConditionChecklist","evidence_ref":"invented"}],
    [{"component":"ConditionChecklist","evidence_ref":"claim:current","url":"https://evil.invalid"}],
    [{"component":"RunTraceChart","evidence_ref":"claim:current"}],
    [{"component":"ConditionChecklist","evidence_ref":"claim:current"}]*5,
])
def test_bad_ui_keeps_decision_and_markdown(ui):
    decision,artifact=resolve_decision(envelope(ui=ui),state())
    assert decision["status"]=="accepted" and artifact is None and decision["ui_status"]=="fallback"


def test_local_correct_and_mixed_claims_do_not_force_question(workspace):
    _,_,ref=saved_claim(workspace)
    from app.tutor.learning_context import resolve_learning_context
    snapshot=resolve_learning_context(workspace,"alice",ref)
    local=envelope(evidence_refs=["context:exact_check"],known_conditions=["固定函数与初值"],missing_conditions=[],claim_status="supported",action="confirm_local")
    decision,_=resolve_decision(local,state(snapshot))
    assert decision["status"]=="accepted" and decision["action"]=="confirm_local"
    mixed=envelope(evidence_refs=["context:exact_check"],missing_conditions=[],claim_status="partially_supported",action="correct_claim",assessments=[
        {"claim":"x₁=1", "status":"supported", "evidence_refs":["context:exact_check"]},
        {"claim":"任意初值都收敛", "status":"contradicted", "evidence_refs":["context:exact_check"]}])
    decision,_=resolve_decision(mixed,state(snapshot))
    assert decision["status"]=="accepted" and len(decision["assessments"])==2
    _,artifact=resolve_decision(envelope(ui=[{"component":"ParameterCompare","evidence_ref":"context:parameters"}]),state(snapshot))
    assert artifact is None, "selected saved claim never grants preview"


@pytest.mark.parametrize("method",["jacobi","gauss_seidel"])
def test_linear_decision_preserves_real_update_order_scope(workspace,method):
    from app.tutor.learning_context import resolve_learning_context
    _,ref=saved_linear(workspace,method)
    snapshot=resolve_learning_context(workspace,"alice",ref)
    decision,_=resolve_decision(envelope(evidence_refs=["context:linear_check"],missing_conditions=[],claim_status="supported",action="confirm_local"),state(snapshot))
    assert decision["status"]=="accepted"
    source=next(s for s in decision["sources"] if s["id"]=="context:linear_check")
    assert source["data"]["method"]==method and not source["data"]["error_bound_includes_roundoff"]


def test_direct_mode_cannot_be_coerced_into_prediction_or_clarification():
    target=state(mode="direct")
    assert decision_prompt(target)["disclosure"]=="full"
    invalid,_=resolve_decision(envelope(),target)
    valid,_=resolve_decision(envelope(disclosure="full",action="explain"),target)
    assert invalid["status"]=="fallback" and valid["status"]=="accepted"


def test_source_hash_changes_with_claim_and_revision(workspace):
    _,_,ref=saved_claim(workspace)
    from app.tutor.learning_context import resolve_learning_context
    snapshot=resolve_learning_context(workspace,"alice",ref)
    first=source_bundle(state(snapshot))
    other=json.loads(json.dumps(snapshot));other["student_claim"]["text"]="我修订了结论"
    assert source_bundle(state(other))["source_hash"]!=first["source_hash"]
    assert source_bundle(state(message="另一个主张"))["source_hash"]!=source_bundle(state())["source_hash"]


def test_asgi_delivery_persists_ui_once_and_keeps_real_reference_and_mastery(workspace,monkeypatch):
    run=saved(workspace,request_id="r3-asgi")
    session=workspace.repository.create_session("alice","数值分析")["session_id"]
    settings=Settings(database_url=f"sqlite:///{workspace.repository.db_path}",teaching_decision_enabled=True)
    tutor=TutorOrchestrator(settings,workspace.repository)
    calls=[]
    async def collect(messages,*args,**kwargs):
        calls.append(messages)
        return envelope(ui=[{"component":"RunTraceChart","evidence_ref":"context:rows"},{"component":"ParameterCompare","evidence_ref":"context:parameters"},{"component":"PredictionForm","evidence_ref":"context:parameters"}])
    monkeypatch.setattr(tutor.workflow_owner,"_collect_model_response",collect)
    app=FastAPI();app.include_router(router);app.include_router(sessions_router)
    app.dependency_overrides[get_learning_workspace]=lambda:workspace
    app.dependency_overrides[get_orchestrator]=lambda:tutor
    app.dependency_overrides[get_repository]=lambda:workspace.repository
    app.dependency_overrides[get_app_settings]=lambda:settings
    app.dependency_overrides[get_principal]=lambda:Principal("alice",True)
    with TestClient(app) as client:
        response=client.post("/api/tutor/stream",json={"session_id":session,"user_id":"alice","message":"请核对这次实验的条件", "learning_context":reference(run).model_dump(),"web_search_mode":"off"})
        history=client.get(f"/api/sessions/{session}/messages").json()["items"]
    assert response.status_code==200 and "event: done" in response.text
    assert response.text.count("event: intelligent_ui\n")==1
    assert len(calls)==1, "no new planner model call"
    saved_reply=history[-1]
    meta=saved_reply["learning_meta"]
    assert meta["teaching_decision"]["status"]=="accepted"
    assert meta["intelligent_ui"]["context_ref"]==reference(run).model_dump()
    assert meta["agent_run"]["message_id"]==saved_reply["id"]
    assert "TEACHING_DECISION" not in saved_reply["content"]
    assert not meta["verified"] and meta["is_correct"] is None and meta["mastery_delta"]==0
    assert workspace.repository.list_mastery("alice")==[]
    assert meta["tutor_artifacts"][0]["context"]==reference(run).model_dump()


def test_offer_experiment_proposal_rules_and_artifact_link(workspace):
    from app.tutor.learning_context import resolve_learning_context
    from app.tutor.learning_actions import root_proposal
    run = saved(workspace, request_id="r3-exp-test")
    ref = reference(run)
    snapshot = resolve_learning_context(workspace, "alice", ref)
    # 1. 有效的初值对照实验建议
    valid_proposal = {
        "question_to_test": "测试当初值选为 x0=-2 时是否能摆脱 0->1->0 循环收敛",
        "changed_parameter": "initial_value",
        "suggested_value": -2.0,
        "candidate_values": [1.5],
        "observable": "观察切线是否收敛至实根 ~ -1.769",
    }
    valid_msg = envelope(
        action="offer_experiment",
        claim_status="partially_supported",
        evidence_refs=["context:parameters"],
        missing_conditions=[],
        reason="初值处于局部振荡吸引子，建议对照实验。",
        experiment_proposal=valid_proposal,
        ui=[{"component": "ParameterCompare", "evidence_ref": "context:parameters"}],
    )
    decision, ui = resolve_decision(valid_msg, state(snapshot))
    assert decision["status"] == "accepted"
    assert decision["action"] == "offer_experiment"
    assert decision["experiment_proposal"]["suggested_value"] == -2.0
    assert ui is not None and ui["status"] == "validated"

    # root_proposal 承载建议初值
    artifact = root_proposal(snapshot, "trace-123", decision["experiment_proposal"])
    assert artifact["suggested_parameters"]["initial_value"] == -2.0
    assert artifact["experiment_proposal"]["question_to_test"] == valid_proposal["question_to_test"]

    # 2. 缺少 proposal -> 降级为 fallback (missing_experiment_proposal)
    no_proposal_msg = envelope(
        action="offer_experiment",
        claim_status="partially_supported",
        evidence_refs=["context:parameters"],
        missing_conditions=[],
        reason="建议实验但未说明改什么。",
        ui=[{"component": "ParameterCompare", "evidence_ref": "context:parameters"}],
    )
    dec_fallback1, _ = resolve_decision(no_proposal_msg, state(snapshot))
    assert dec_fallback1["status"] == "fallback"
    assert dec_fallback1["reason_code"] == "missing_experiment_proposal"

    # 3. 建议参数与原初值完全相同 -> 降级 (experiment_parameter_unchanged)
    same_param_proposal = {**valid_proposal, "suggested_value": snapshot["parameters"]["initial_value"]}
    same_msg = envelope(
        action="offer_experiment",
        claim_status="partially_supported",
        evidence_refs=["context:parameters"],
        missing_conditions=[],
        reason="建议对照实验。",
        experiment_proposal=same_param_proposal,
        ui=[{"component": "ParameterCompare", "evidence_ref": "context:parameters"}],
    )
    dec_fallback2, _ = resolve_decision(same_msg, state(snapshot))
    assert dec_fallback2["status"] == "fallback"
    assert dec_fallback2["reason_code"] == "experiment_parameter_unchanged"

    # 4. 非 offer_experiment 却附带 proposal -> 降级 (unrequested_experiment_proposal)
    unreq_msg = envelope(
        action="confirm_local",
        claim_status="supported",
        evidence_refs=["context:parameters"],
        missing_conditions=[],
        reason="局部正确",
        experiment_proposal=valid_proposal,
        ui=[{"component": "ParameterCompare", "evidence_ref": "context:parameters"}],
    )
    dec_fallback3, _ = resolve_decision(unreq_msg, state(snapshot))
    assert dec_fallback3["status"] == "fallback"
    assert dec_fallback3["reason_code"] == "unrequested_experiment_proposal"


def test_newton_inquiry_full_cycle_experiment_and_revision(workspace):
    from app.tutor.learning_actions import root_proposal, LearningActions, PreviewActionRequest, RootPreviewParameters, SavePreviewRequest
    from app.tutor.learning_context import resolve_learning_context, NewtonActivityClaimRef
    from app.tutor.newton_activity import ACTIVITY_ID, ACTIVITY_VERSION

    # 1. 学生在 Newton 探究活动中提交预测、观察振荡反例，并提交解释
    activity, run, ref = saved_claim(workspace)
    snapshot = resolve_learning_context(workspace, "alice", ref)
    assert snapshot["student_claim"]["kind"] == "explanation"
    assert "任意初值都收敛" in snapshot["student_claim"]["text"]

    # 2. 助教对该解释给出教学决策：指出推广有误并提出受控单变量对照实验（x0 从 0 变为 -2.0）
    exp_proposal = {
        "question_to_test": "改变初值是否能打破周期振荡并收敛到根？",
        "changed_parameter": "initial_value",
        "suggested_value": -2.0,
        "candidate_values": [-2.0, 1.5],
        "observable": "观察迭代是否跳出 {0, 1} 循环并单调逼近负实根",
    }
    msg = envelope(
        action="offer_experiment",
        claim_status="partially_supported",
        evidence_refs=["context:parameters", "context:rows"],
        missing_conditions=[],
        reason="初值 0 导致切线交替循环，建议在收敛域内初值 -2 处做对照实验。",
        experiment_proposal=exp_proposal,
        ui=[],
    )
    decision, _ = resolve_decision(msg, state(snapshot))
    assert decision["status"] == "accepted"
    assert decision["action"] == "offer_experiment"
    assert decision["experiment_proposal"]["suggested_value"] == -2.0

    # 3. 生成动作卡片，检验单变量对照实验提案内置于卡片
    session = workspace.repository.create_session("alice", "数值分析")["session_id"]
    agent_run_id = "run-newton-e2e"
    workspace.repository.start_agent_run(agent_run_id, session, "alice", "v", "v")
    proposal_card = root_proposal(snapshot, agent_run_id, decision["experiment_proposal"])
    assert proposal_card["experiment_proposal"] == exp_proposal
    assert proposal_card["suggested_parameters"]["initial_value"] == -2.0
    assert proposal_card["context"]["activity_claim"] is not None

    message = workspace.repository.add_message(
        session,
        "assistant",
        "建议进行初值对照实验。",
        learning_meta={"answer_guard": {"status": "passed"}, "tutor_artifacts": [proposal_card]},
        agent_run_finish={"run_id": agent_run_id, "user_id": "alice", "status": "succeeded"},
    )

    # 4. 学生执行受控预览
    actions = LearningActions(workspace, workspace.repository)
    preview_req = PreviewActionRequest(
        context=ref,
        parameters=RootPreviewParameters(**{**proposal_card["parameters"], "initial_value": -2.0}),
        request_id="preview-req-1",
        prediction="预计新初值会避开0与1的循环，但数值观察还不能证明一般收敛。",
    )
    with pytest.raises(ValueError, match="预测"):
        actions.preview("alice", session, message, proposal_card["artifact_id"], preview_req.model_copy(update={"prediction": None}))
    with pytest.raises(ValueError, match="只改变初值"):
        actions.preview("alice", session, message, proposal_card["artifact_id"], preview_req.model_copy(update={
            "parameters": preview_req.parameters.model_copy(update={"tolerance": preview_req.parameters.tolerance / 10})}))
    preview_res = actions.preview("alice", session, message, proposal_card["artifact_id"], preview_req)
    assert preview_res["parameters"]["initial_value"] == -2.0
    assert preview_res["student_prediction"] == preview_req.prediction
    assert preview_res["prediction_timing"] == "before_preview"
    # 验证确实收敛到了约 -1.769292 的负实根
    assert abs(preview_res["rows"][-1]["x"] - (-1.769292)) < 1e-4

    # 5. 学生填写观察并保存该实验
    save_req = SavePreviewRequest(
        context=ref,
        preview_id="preview-req-1",
        preview_hash=preview_res["input_hash"],
        observation="初值取 -2 时跳出了 0 和 1 之间的循环，收敛到负实根。",
    )
    saved_run = actions.save("alice", session, message, proposal_card["artifact_id"], save_req)
    assert saved_run["prediction_timing"] == "after_preview"

    # 6. 学生回到活动提交第 1 次修订
    activity.revise(
        "alice",
        "revise-a1",
        run["id"],
        run["input_hash"],
        "初值极度影响收敛。在 0 处切线交替循环振荡，而在根附近的初值 -2 处能够收敛到实根。",
    )
    revised_claim_ref = NewtonActivityClaimRef(
        activity_id=ACTIVITY_ID,
        activity_version=ACTIVITY_VERSION,
        claim_kind="revision",
        request_id="revise-a1",
        revision_count=1,
    )
    revised_context_ref = reference(run, activity_claim=revised_claim_ref)
    revised_snapshot = resolve_learning_context(workspace, "alice", revised_context_ref)
    assert revised_snapshot["student_claim"]["kind"] == "revision"

    # 7. 助教接收修订，教学决策做出 confirm_local 确认完成闭环
    confirm_msg = envelope(
        action="confirm_local",
        claim_status="supported",
        evidence_refs=["context:parameters", "context:rows"],
        missing_conditions=[],
        reason="修订准确区分了初值对收敛性的影响，并结合实验修正了原论断。",
        ui=[],
    )
    confirm_decision, _ = resolve_decision(confirm_msg, state(revised_snapshot))
    assert confirm_decision["status"] == "accepted"
    assert confirm_decision["action"] == "confirm_local"
    assert confirm_decision["claim_status"] == "supported"



