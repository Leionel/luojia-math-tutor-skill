"""B5 checks a real session across saved workspaces without model or grading claims."""
import pytest

from app.api.routes_learning import CodeRequest
from app.auth import Principal, get_principal
from app.tutor.learning_context import CodeContextRef, resolve_learning_context
from app.tutor.learning_extensions import ASSIGNMENT_ID, STATIC_RULE_VERSION, submit_code
from app.tutor.learning_workspace import QUESTIONS

from test_learning_context import reference, saved as saved_root
from test_reference_upgrade import app_client, course_ref, linear, parse, ws


def test_one_chat_session_resumes_reading_experiment_and_saved_code(ws, monkeypatch):
    work, _ = ws
    client, tutor = app_client(ws, monkeypatch)
    session = work.repository.create_session("alice", "数值分析")["session_id"]
    first = client.post("/api/tutor/stream", json={
        "session_id": session, "user_id": "alice", "message": "今天的任务",
        "study_action": "current_tasks",
    })
    assert first.status_code == 200
    assert any(name == "done" for name, _ in parse(first.text))
    initial = work.repository.list_messages(session)[-1]["learning_meta"]
    assert initial["study_summary"]["read_only"] is True
    assert initial["study_summary"]["recommendation"]["mastery_claim"] is False

    reading = course_ref(ws)
    root = reference(saved_root(work, request_id="b5-root"))
    _, experiment = linear(ws)
    code = ("def solve(x0, tol, max_iter):\n    xs=[x0]\n    x=x0\n"
            "    for _ in range(max_iter):\n        fx=x*x-2\n"
            "        if abs(fx)<=tol:\n            break\n"
            "        x=x-fx/(2*x)\n        xs.append(x)\n    return xs\n")
    saved = submit_code(work, "alice", CodeRequest(
        request_id="b5-code", assignment_id=ASSIGNMENT_ID, code=code))
    index = next(i for i, row in enumerate(saved["findings"])
                 if row["kind"] == "root_error_residual_stop")
    code_ref = CodeContextRef(kind="code_static", record_id=saved["id"],
                              code_hash=saved["code_hash"], static_rule_version=STATIC_RULE_VERSION,
                              selected_finding=index)
    for label, ref in (("教材条件", reading), ("Newton 实验", root),
                       ("线性实验", experiment), ("代码静态线索", code_ref)):
        snapshot = client.post("/api/tutor/context", json=ref.model_dump())
        assert snapshot.status_code == 200, label
        assert snapshot.json()["ref"] == ref.model_dump()
        assert snapshot.json()["independent_success"] is False
        reply = client.post("/api/tutor/stream", json={
            "session_id": session, "user_id": "alice", "message": f"讨论{label}的依据",
            "learning_context": ref.model_dump(),
        })
        assert reply.status_code == 200, label
        assert any(name == "done" for name, _ in parse(reply.text)), label
        meta = work.repository.list_messages(session)[-1]["learning_meta"]
        assert meta["learning_context"]["ref"] == ref.model_dump()
        assert meta["is_correct"] is None and meta["mastery_delta"] == 0
    assert work.repository.list_mastery("alice") == []
    assert work.repository.list_user_mistakes("alice") == []

    # A stale version and another owner cannot resume the saved private objects.
    stale = {**code_ref.model_dump(), "code_hash": "0" * 64}
    assert client.post("/api/tutor/context", json=stale).status_code == 409
    assert client.post("/api/tutor/context", json=experiment.model_dump() | {"source_hash": "0" * 64}).status_code == 409
    tutor_app = client.app
    tutor_app.dependency_overrides[get_principal] = lambda: Principal("bob", True)
    assert client.post("/api/tutor/context", json=code_ref.model_dump()).status_code == 404
    assert client.post("/api/tutor/context", json=experiment.model_dump()).status_code == 404


def test_assessment_stays_locked_then_returns_to_unit_source_not_answer_chat(ws, monkeypatch):
    work, _ = ws
    client, _ = app_client(ws, monkeypatch)
    session = work.repository.create_session("alice", "数值分析")["session_id"]
    exam = work.new_assessment("alice")
    assert "feedback" not in exam
    in_progress = client.post("/api/tutor/stream", json={
        "session_id": session, "user_id": "alice", "message": "今天的任务",
        "study_action": "current_tasks",
    })
    assert any(name == "done" for name, _ in parse(in_progress.text))
    summary = work.repository.list_messages(session)[-1]["learning_meta"]["study_summary"]
    assert summary["help_locked"] is True
    assert summary["recommendation"]["href"] == "/assessment"
    assert client.post("/api/tutor/context", json=course_ref(ws).model_dump()).status_code == 409

    for question in QUESTIONS:
        work.answer_assessment("alice", exam["id"], question[0], question[3])
    done = work.submit_assessment("alice", exam["id"])
    assert work.submit_assessment("alice", exam["id"]) == done
    assert done["score"]["correct"] == len(QUESTIONS)
    assert done["feedback_review_status"] == "development_unreviewed"
    assert all(row["unit_id"] for row in done["feedback"])
    unit_id = done["feedback"][0]["unit_id"]
    unit = next(item for item in work.reading_units() if item["id"] == unit_id)
    source = course_ref(ws).model_copy(update={
        "source_id": unit_id, "source_hash": unit["source_hash"],
        "graph_revision": unit["graph_revision"],
        "end": min(len(unit["quote"]), 60),
    })
    assert client.post("/api/tutor/context", json=source.model_dump()).status_code == 200
    reply = client.post("/api/tutor/stream", json={
        "session_id": session, "user_id": "alice", "message": "解释教材里的这项条件",
        "learning_context": source.model_dump(),
    })
    assert any(name == "done" for name, _ in parse(reply.text))
    meta = work.repository.list_messages(session)[-1]["learning_meta"]
    assert meta["learning_context"]["ref"] == source.model_dump()
    assert meta["learning_context"]["ref"]["kind"] == "reading"
    assert work.repository.list_mastery("alice") == []
