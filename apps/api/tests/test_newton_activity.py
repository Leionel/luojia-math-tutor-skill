"""Offline activity contract: student process and reference help stay separate."""
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_learning import router
from app.auth import Principal, get_principal
from app.config import Settings
from app.knowledge.course_service import CourseService
from app.knowledge.course_store import CourseStore
from app.main_deps import get_learning_workspace
from app.math_tools.root_runner import LabRequest
from app.memory.repository import Repository
from app.tutor.learning_workspace import LearningWorkspace


@pytest.fixture
def activity(tmp_path):
    course_path = tmp_path / "course.db"
    course = CourseService(store=CourseStore(str(course_path)))
    repo = Repository(Settings(database_url=f"sqlite:///{tmp_path / 'students.db'}"))
    workspace = LearningWorkspace(course, repo)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_learning_workspace] = lambda: workspace
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    return TestClient(app), app, workspace, course_path


BASE = "/api/root-lab/activity/newton-cycle-v1"


def test_prediction_observation_explanation_revision_and_restore(activity):
    client, app, workspace, course_path = activity
    initial = client.get(BASE)
    assert initial.status_code == 200
    assert initial.json()["phase"] == "predict"
    assert initial.json()["run"] is None
    assert "0 → 1 → 0" not in json.dumps(initial.json(), ensure_ascii=False)
    assert "往复" not in json.dumps(initial.json(), ensure_ascii=False)
    assert client.post(BASE + "/reveal", json={"request_id": "early", "mode": "observe"}).status_code == 409

    prediction = {"request_id": "predict-1", "text": "我猜会靠近某个根", "reason": "初值处导数不为零"}
    assert client.post(BASE + "/predict", json=prediction).json()["prediction"]["text"] == prediction["text"]
    assert client.post(BASE + "/predict", json=prediction).status_code == 200
    assert client.post(BASE + "/predict", json={**prediction, "text": "改写"}).status_code == 409
    exposed = client.post(BASE + "/reveal", json={"request_id": "observe-1", "mode": "observe"})
    assert exposed.status_code == 200
    state = exposed.json()
    run = state["run"]
    assert [row["x"] for row in run["rows"]] == [0]
    assert state["revealed_step"] == 0 and state["observation_complete"] is False
    assert "往复" not in json.dumps(state, ensure_ascii=False)
    assert run["stop_reason"] == "pending" and run["diagnosis"]["status"] == "unknown"
    assert run["runner_version"] and run["input_hash"]
    assert state["exact_check"] is None and state["answer_exposed"] is False
    assert state["reveal"]["evidence_kind"] == "reference_help"
    assert client.post(BASE + "/reveal", json={"request_id": "observe-1", "mode": "observe"}).json()["run"]["id"] == run["id"]
    assert len(workspace.store.learning_records("alice", workspace.course_id, "lab")) == 1

    written = {"request_id": "explain-1", "run_id": run["id"], "input_hash": run["input_hash"],
               "text": "观察到返回初值；局部定理不能推广到任意初值。"}
    assert client.post(BASE + "/explain", json=written).status_code == 409
    assert client.get(BASE).json()["run"]["rows"] == run["rows"]
    step = client.post(BASE + "/step", json={"request_id": "step-1", "expected_step": 0}).json()
    assert [row["x"] for row in step["run"]["rows"]] == [0, 1]
    assert "往复" not in json.dumps(step, ensure_ascii=False)
    assert client.post(BASE + "/step", json={"request_id": "step-1", "expected_step": 0}).json()["revealed_step"] == 1
    assert client.post(BASE + "/step", json={"request_id": "step-1", "expected_step": 1}).status_code == 409
    assert client.post(BASE + "/step", json={"request_id": "stale", "expected_step": 0}).status_code == 409
    for index in range(1, 8):
        if step["observation_complete"]:
            break
        step = client.post(BASE + "/step", json={"request_id": f"step-{index+1}", "expected_step": index}).json()
    assert step["observation_complete"] is True
    assert [row["x"] for row in step["run"]["rows"][:3]] == [0, 1, 0]
    assert client.post(BASE + "/explain", json={**written, "input_hash": "0" * 64}).status_code == 409
    explained = client.post(BASE + "/explain", json=written).json()
    assert explained["exact_check"]["steps"] and explained["explanation"]["text"] == written["text"]
    revised = client.post(BASE + "/revise", json={**written, "request_id": "revise-1", "text": "现在认为这个初值出现精确往复。"}).json()
    assert revised["prediction"]["text"] == prediction["text"]
    assert revised["revisions"][0]["text"].startswith("现在认为")
    assert client.post(BASE + "/revise", json={**written, "request_id": "revise-1", "text": "现在认为这个初值出现精确往复。"}).json()["revisions"] == revised["revisions"]
    assert workspace.repository.list_mastery("alice") == []
    assert workspace.store.list_events("alice", workspace.course_id) == []

    reopened = CourseStore(str(course_path))
    restored = LearningWorkspace(CourseService(store=reopened), workspace.repository)
    app.dependency_overrides[get_learning_workspace] = lambda: restored
    assert client.get(BASE).json()["revisions"] == revised["revisions"]
    assert client.get(BASE).json()["run"]["id"] == run["id"]
    app.dependency_overrides[get_principal] = lambda: Principal("bob", True)
    assert client.get(BASE).json()["phase"] == "predict"
    assert client.post(BASE + "/explain", json=written).status_code == 409
    app.dependency_overrides[get_principal] = lambda: Principal("demo-user", False)
    assert client.get(BASE).status_code == 401
    reopened.close()


def test_direct_answer_and_changed_initial_do_not_count_as_independent(activity):
    client, _, workspace, _ = activity
    shown = client.post(BASE + "/reveal", json={"request_id": "skip-1", "mode": "answer"})
    assert shown.status_code == 200
    state = shown.json()
    assert state["prediction"] is None and state["prediction_choice"] == "skipped"
    assert state["answer_exposed"] is True and state["independent_success"] is False
    assert state["exact_check"]["scope"].startswith("仅对本题")
    assert client.post(BASE + "/reveal", json={"request_id": "skip-1", "mode": "answer"}).json()["run"]["id"] == state["run"]["id"]
    changed = workspace.lab("alice", LabRequest(attempt={"method": "newton", "function": "x^3-2*x+2",
                                                       "initial_value": -2, "goal": "residual"},
                                                 max_iterations=8, prediction="试换初值", request_id="changed-initial"))
    assert changed["input_hash"] != state["run"]["input_hash"]
    assert changed["id"] != state["run"]["id"]
    assert "exact_check" not in changed
    assert workspace.repository.list_mastery("alice") == []


def test_partial_activity_cannot_be_recovered_through_generic_lab_routes(activity, monkeypatch):
    client, _, workspace, _ = activity
    monkeypatch.setattr("app.api.routes_learning.workspace", lambda: workspace)
    client.post(BASE + "/predict", json={"request_id": "predict-guard", "text": "先观察", "reason": ""})
    state = client.post(BASE + "/reveal", json={"request_id": "observe-guard", "mode": "observe"}).json()
    run = state["run"]
    assert len(run["rows"]) == 1
    assert len(client.get(f"/api/root-lab/runs/{run['id']}").json()["rows"]) == 1
    assert len(client.get("/api/root-lab/runs").json()["runs"][0]["rows"]) == 1
    replay = client.post("/api/root-lab/runs", json={"attempt": {
        "method": "newton", "function": "x^3-2*x+2", "initial_value": 0,
        "goal": "residual", "tolerance": 1e-6}, "max_iterations": 8,
        "prediction": "先观察", "request_id": run["id"]})
    assert replay.status_code == 200 and len(replay.json()["rows"]) == 1
