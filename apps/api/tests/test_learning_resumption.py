"""Real saved sources, delivered actions and adversarial resumption requests."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import Principal, get_principal
from app.api.routes_learning import router
from app.main_deps import get_learning_workspace
from app.tutor.learning_resumption import LearningResumptionService
from test_learning_workspace import workspace
from test_learning_actions import delivered


def setup_task(workspace, **changes):
    _, session, message, proposal = delivered(workspace)
    payload = dict(task_id="resume-task", claim_ref=proposal["context"], student_claim_text="单步成立但收敛条件未知",
        completed_steps=["已观察轨迹"], experiment_parameters={}, pending_conditions=["初值足够接近单根"],
        help_exposed=False)
    payload.update(changes)
    service = LearningResumptionService(workspace)
    service.save_summary("alice", **payload)
    action = dict(session_id=session, message_id=message, artifact_id=proposal["artifact_id"])
    return service, payload, action


def test_save_uses_canonical_source_and_marks_reports_unverified(workspace):
    service, body, _ = setup_task(workspace)
    record = service.get_summary("alice", body["task_id"])
    assert record["help_exposed"] and record["mastery_certified"] is False
    assert record["facts"]["experiment_parameters"]["function"]
    assert record["facts_scope"] == "saved_reference_and_student_reports_not_verified_steps"
    assert service.save_summary("alice", **body) == record
    with pytest.raises(KeyError):
        service.get_summary("bob", body["task_id"])


@pytest.mark.parametrize("ref", [{}, {"kind": "newton_activity"}, {"kind": "root_lab", "record_id": "missing"}])
def test_invalid_or_unimplemented_reference_is_rejected(workspace, ref):
    with pytest.raises(ValueError):
        setup_task(workspace, claim_ref=ref)


def test_caller_cannot_replace_saved_experiment(workspace):
    with pytest.raises(ValueError, match="参数"):
        setup_task(workspace, experiment_parameters={"function": "x^2-999"})


def test_condition_supplement_does_not_discharge_mathematical_obligation(workspace):
    service, body, _ = setup_task(workspace)
    result = service.resume_step("alice", body["task_id"], "one", "随便输入也不能证明条件")
    assert result["status"] == "supplement_recorded" and result["preview"] is None
    assert result["remaining_pending_conditions"] == body["pending_conditions"]
    record = service.get_summary("alice", body["task_id"])
    assert record["facts"]["completed_steps"] == body["completed_steps"]
    assert record["supplements"][0]["status"] == "student_reported_unverified"


def test_concurrent_preview_is_once_and_has_real_help_receipt(workspace):
    service, body, action = setup_task(workspace)
    def execute(_):
        return service.resume_step("alice", body["task_id"], "one", "初值改为-2，仍需核对条件", -2.0, action)
    with ThreadPoolExecutor(4) as pool:
        results = list(pool.map(execute, range(4)))
    assert all(r == results[0] for r in results)
    preview = results[0]["preview"]
    assert preview["parameters"]["initial_value"] == -2
    assert preview["rows"][1]["x"] == pytest.approx(-1.8)
    assert len(workspace.store.learning_records("alice", workspace.course_id, "lab_preview")) == 1
    assert len(workspace.store.list_events("alice", workspace.course_id)) == 1
    assert not workspace.repository.list_mastery("alice")
    with pytest.raises(ValueError, match="标识"):
        service.resume_step("alice", body["task_id"], "one", "另一个补充", -2.0, action)
    with pytest.raises(ValueError, match="一次"):
        service.resume_step("alice", body["task_id"], "two", "再试一次", -3.0, action)


def test_preview_requires_delivered_action_and_rolls_back_failed_supplement(workspace):
    service, body, action = setup_task(workspace)
    with pytest.raises(ValueError, match="卡片"):
        service.resume_step("alice", body["task_id"], "one", "补充", -2)
    with pytest.raises(KeyError):
        service.resume_step("alice", body["task_id"], "one", "补充", -2, {**action, "message_id": "other"})
    assert service.get_summary("alice", body["task_id"])["supplements"] == []
    assert not workspace.store.learning_records("alice", workspace.course_id, "lab_preview")


def test_cached_replay_rechecks_help_and_source_version(workspace, monkeypatch):
    service, body, action = setup_task(workspace)
    service.resume_step("alice", body["task_id"], "one", "补充", -2, action)
    assessment = workspace.new_assessment("alice")
    with pytest.raises(ValueError, match="自检"):
        service.resume_step("alice", body["task_id"], "one", "补充", -2, action)
    workspace.end_assessment("alice", assessment["id"])
    monkeypatch.setattr(workspace, "revision", lambda: "new-revision")
    with pytest.raises(ValueError, match="更新"):
        service.verify_and_resume("alice", body["task_id"])


def test_correction_invalidates_inference_and_old_replay(workspace):
    service, body, _ = setup_task(workspace)
    service.resume_step("alice", body["task_id"], "one", "补充")
    changed = service.update_corrections("alice", body["task_id"], "direct", "新的原话")
    assert changed["inferences"]["inferred_claim_status"] is None
    assert changed["inferences"]["last_suggested_proposal"] is None
    with pytest.raises(ValueError, match="标识"):
        service.resume_step("alice", body["task_id"], "one", "补充")


def test_clear_scrubs_content_and_cannot_be_revived(workspace):
    service, body, _ = setup_task(workspace)
    service.clear_summary("alice", body["task_id"])
    record = service.get_summary("alice", body["task_id"])
    assert "facts" not in record and "processed_requests" not in record and "inferences" not in record
    with pytest.raises(ValueError, match="清除"):
        service.verify_and_resume("alice", body["task_id"])
    with pytest.raises(ValueError, match="清除"):
        service.save_summary("alice", **body)


def test_http_contracts_and_owned_persistence(workspace):
    service, body, _ = setup_task(workspace)
    app = FastAPI(); app.include_router(router)
    app.dependency_overrides[get_learning_workspace] = lambda: workspace
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    with TestClient(app) as client:
        assert client.post("/api/learning/resumption/save", json=body).status_code == 200
        assert client.post("/api/learning/resumption/save", json={**body, "claim_ref": {}}).status_code == 422
        base = "/api/learning/resumption/resume-task"
        assert client.post(base+"/resume", json={"request_id": "one", "supplemented_condition": "补充"}).json()["status"] == "supplement_recorded"
        assert client.post(base+"/resume", json={"request_id": "one", "supplemented_condition": "不同"}).status_code == 409
        assert client.get(base).json()["task_id"] == body["task_id"]
        app.dependency_overrides[get_principal] = lambda: Principal("bob", True)
        assert client.get(base).status_code == 404
