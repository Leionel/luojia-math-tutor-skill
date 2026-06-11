import asyncio
import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.memory.repository import Repository
from app.tutor.orchestrator import TutorOrchestrator


def test_health_route():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_create_session_and_list_messages():
    client = TestClient(app)
    created = client.post("/api/sessions", json={"user_id": "demo-user", "subject": "calculus"})
    assert created.status_code == 200
    session_id = created.json()["session_id"]

    messages = client.get(f"/api/sessions/{session_id}/messages")
    assert messages.status_code == 200
    assert messages.json()["items"] == []


# ── mastery routes ──

def test_mastery_list_empty():
    client = TestClient(app)
    resp = client.get("/api/users/test-mastery-user/mastery")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_mastery_summary_empty():
    client = TestClient(app)
    resp = client.get("/api/users/test-mastery-user/mastery/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_concepts"] == 0
    assert data["average_score"] == 0.0


# ── similar exercises ──

def test_similar_exercises_power_integral():
    client = TestClient(app)
    resp = client.post("/api/exercises/similar", json={
        "concept": "幂函数积分", "difficulty": 1, "count": 2,
    })
    assert resp.status_code == 200
    exercises = resp.json()["exercises"]
    assert len(exercises) >= 1
    assert all("text" in e for e in exercises)


def test_similar_exercises_determinant():
    client = TestClient(app)
    resp = client.post("/api/exercises/similar", json={
        "concept": "二阶行列式", "difficulty": 1, "count": 2,
    })
    assert resp.status_code == 200
    exercises = resp.json()["exercises"]
    assert len(exercises) >= 1


def test_similar_exercises_conditional_probability():
    client = TestClient(app)
    resp = client.post("/api/exercises/similar", json={
        "concept": "条件概率", "difficulty": 1, "count": 2,
    })
    assert resp.status_code == 200
    exercises = resp.json()["exercises"]
    assert len(exercises) >= 1


def test_similar_exercises_partial_integration():
    client = TestClient(app)
    resp = client.post("/api/exercises/similar", json={
        "concept": "分部积分", "difficulty": 2, "count": 1,
    })
    assert resp.status_code == 200
    exercises = resp.json()["exercises"]
    assert len(exercises) >= 1


def test_similar_exercises_unknown_concept_fallback():
    client = TestClient(app)
    resp = client.post("/api/exercises/similar", json={
        "concept": "傅里叶变换", "difficulty": 2, "count": 1,
    })
    assert resp.status_code == 200
    exercises = resp.json()["exercises"]
    assert len(exercises) == 1
    assert "concept" in exercises[0]


# ── tutor SSE meta integration ──

def parse_sse_events(streaming_body: bytes) -> list[dict]:
    """Parse SSE stream into list of {event, data} dicts."""
    events = []
    text = streaming_body.decode("utf-8")
    for block in text.split("\n\n"):
        lines = block.strip().split("\n")
        event = None
        data = None
        for line in lines:
            if line.startswith("event: "):
                event = line[len("event: "):]
            elif line.startswith("data: "):
                data = json.loads(line[len("data: "):])
        if event and data is not None:
            events.append({"event": event, "data": data})
    return events


def test_tutor_sse_opening_precedes_meta_and_message():
    client = TestClient(app)
    session = client.post(
        "/api/sessions",
        json={"user_id": "opening-user", "subject": "calculus"},
    )
    session_id = session.json()["session_id"]

    response = client.post(
        "/api/tutor/stream",
        json={
            "session_id": session_id,
            "user_id": "opening-user",
            "message": "什么是导数？",
            "mode": "socratic",
        },
    )

    events = parse_sse_events(response.read())
    names = [event["event"] for event in events]
    assert names[0] == "opening"
    assert names.index("opening") < names.index("meta")
    assert names.index("opening") < names.index("message")


@pytest.mark.asyncio
async def test_opening_does_not_wait_for_graph():
    class SlowWorkflow:
        async def ainvoke(self, state, config):
            await asyncio.sleep(1)
            return {
                **state,
                "final_output": "",
                "thinking_chain": "",
            }

    orchestrator = TutorOrchestrator.__new__(TutorOrchestrator)
    orchestrator.workflow = SlowWorkflow()
    orchestrator.repository = MagicMock(spec=Repository)
    stream = orchestrator.stream_reply(
        session_id="session-1",
        user_id="user-1",
        message="什么是导数？",
        subject="calculus",
        mode="socratic",
    )

    first_event = await asyncio.wait_for(anext(stream), timeout=0.15)
    await stream.aclose()

    assert first_event.startswith("event: opening")


def test_tutor_sse_meta_contains_mastery_fields():
    """When a student submits a wrong integral step, meta should include mastery fields."""
    client = TestClient(app)
    session = client.post("/api/sessions", json={"user_id": "demo-user", "subject": "calculus"})
    session_id = session.json()["session_id"]

    resp = client.post("/api/tutor/stream", json={
        "session_id": session_id,
        "message": "我算 ∫x² dx = x³，对吗？",
        "mode": "socratic",
        "requested_hint": False,
    })
    assert resp.status_code == 200

    events = parse_sse_events(resp.read())
    meta_events = [e for e in events if e["event"] == "meta"]
    assert len(meta_events) == 1
    meta = meta_events[0]["data"]

    assert "hint_level" in meta
    assert isinstance(meta["hint_level"], int)
    assert "mastery_score" in meta
    assert isinstance(meta["mastery_score"], (int, float))
    assert "mastery_label" in meta
    assert isinstance(meta["mastery_label"], str)
    assert "mastery_delta" in meta
    assert isinstance(meta["mastery_delta"], (int, float))


def test_tutor_sse_meta_verified_wrong_integral():
    """A wrong integral answer should be detected and reported in meta."""
    client = TestClient(app)
    session = client.post("/api/sessions", json={"user_id": "demo-user", "subject": "calculus"})
    session_id = session.json()["session_id"]

    resp = client.post("/api/tutor/stream", json={
        "session_id": session_id,
        "message": "我算 ∫x³ dx = x⁴，对吗？",
        "mode": "socratic",
    })
    assert resp.status_code == 200

    events = parse_sse_events(resp.read())
    meta_events = [e for e in events if e["event"] == "meta"]
    assert len(meta_events) >= 1
    meta = meta_events[0]["data"]

    # The integral is missing division by the new exponent → should be detected as wrong
    assert meta["verified"] is True
    assert meta["is_correct"] is False
    assert meta["mistake"] is not None


def test_tutor_sse_meta_correct_integral():
    """A correct integral answer should be verified."""
    client = TestClient(app)
    session = client.post("/api/sessions", json={"user_id": "demo-user", "subject": "calculus"})
    session_id = session.json()["session_id"]

    # This is actually correct for some integrals, let's test a clear correct answer
    resp = client.post("/api/tutor/stream", json={
        "session_id": session_id,
        "message": "我算 ∫2x dx = x² + C，对吗？",
        "mode": "socratic",
    })
    assert resp.status_code == 200

    events = parse_sse_events(resp.read())
    meta_events = [e for e in events if e["event"] == "meta"]
    assert len(meta_events) >= 1
    meta = meta_events[0]["data"]
    assert meta["verified"] is True


def test_tutor_sse_hint_level_with_hint_request():
    """When user requests a hint, hint_level should be >= LIGHT_HINT (1)."""
    client = TestClient(app)
    session = client.post("/api/sessions", json={"user_id": "demo-user", "subject": "calculus"})
    session_id = session.json()["session_id"]

    resp = client.post("/api/tutor/stream", json={
        "session_id": session_id,
        "message": "请给我下一层提示。",
        "mode": "socratic",
        "requested_hint": True,
    })
    assert resp.status_code == 200

    events = parse_sse_events(resp.read())
    meta_events = [e for e in events if e["event"] == "meta"]
    assert len(meta_events) >= 1
    meta = meta_events[0]["data"]

    assert meta["hint_level"] >= 1, f"Expected hint_level >= 1, got {meta['hint_level']}"


def test_tutor_sse_mastery_update_persists():
    """Mastery should be updated and retrievable via the mastery API after a verified attempt."""
    client = TestClient(app)
    session = client.post("/api/sessions", json={"user_id": "mastery-test-user", "subject": "calculus"})
    session_id = session.json()["session_id"]

    # Submit a wrong answer and consume the streaming response
    stream_resp = client.post("/api/tutor/stream", json={
        "session_id": session_id,
        "user_id": "mastery-test-user",
        "message": "我算 ∫x² dx = x³，对吗？",
        "mode": "socratic",
    })
    stream_resp.read()  # consume SSE stream to trigger side effects

    # Check mastery was recorded
    resp = client.get("/api/users/mastery-test-user/mastery")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    # There should be a mastery entry for 幂函数积分
    concepts = [item["concept"] for item in items]
    assert "幂函数积分" in concepts


def test_tutor_sse_mastery_summary():
    """Mastery summary endpoint should return aggregated stats."""
    client = TestClient(app)
    session = client.post("/api/sessions", json={"user_id": "summary-test-user", "subject": "calculus"})
    session_id = session.json()["session_id"]

    stream_resp = client.post("/api/tutor/stream", json={
        "session_id": session_id,
        "user_id": "summary-test-user",
        "message": "我算 ∫x² dx = x³，对吗？",
        "mode": "socratic",
    })
    stream_resp.read()  # consume SSE stream to trigger side effects

    resp = client.get("/api/users/summary-test-user/mastery/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_concepts"] >= 1
    assert "average_score" in data
    assert "weak_concepts" in data
