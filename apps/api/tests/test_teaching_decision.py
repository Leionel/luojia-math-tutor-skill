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
