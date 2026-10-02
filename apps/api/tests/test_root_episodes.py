import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.auth import Principal, get_principal
from app.config import Settings
from app.knowledge.course_service import CourseService
from app.knowledge.course_store import CourseStore
from app.math_tools.root_finding import RootAttempt
from app.memory.repository import Repository
from app.tutor.orchestrator import TutorOrchestrator
from app.tutor.root_diagnostics import RootEpisodeService, RootSubmission


def newton(n=2, start=1.0, steps=5):
    xs = [start]
    for _ in range(steps):
        xs.append((xs[-1] + n / xs[-1]) / 2)
    return dict(method="newton", function=f"x^2-{n}", iterates=xs, interval=[1, 2] if n < 4 else [2, 3])


@pytest.fixture
def service(tmp_path):
    return RootEpisodeService(CourseService(store=CourseStore(tmp_path / "course.db")))


def submit(service, data, identity="first", episode=None):
    return service.submit("student-1", "session-1", RootSubmission(attempt=RootAttempt(**data), attempt_id=identity, episode_id=episode))


def ack(service, report):
    return service.acknowledge("student-1", "session-1", report["episode_id"], report["attempt_id"], report["feedback_id"])


def units(service):
    return service.overlay.get_course_overlay("student-1", "numerical_analysis")["units"]


def test_hint_revision_ack_restart_and_replay(service, tmp_path):
    wrong = submit(service, dict(method="newton", function="x^2-2", iterates=[1, 3]))
    assert wrong["error_step"] == 1 and wrong["case_id"]
    assert not any(u["failure_count"] for u in units(service).values())
    assert ack(service, wrong)["outcome"] == "failed"
    corrected = submit(service, newton(), "revision", wrong["episode_id"])
    assert corrected["complete"] and corrected["outcome"] == "unknown"
    assert ack(service, corrected)["outcome"] == "assisted_success"
    assert ack(service, corrected)["status"] == "duplicate"
    before = units(service)
    assert any(u["assisted_success_count"] == 1 for u in before.values())
    assert not any(u["independent_evidence_count"] for u in before.values())
    restarted = RootEpisodeService(CourseService(store=CourseStore(tmp_path / "course.db")))
    assert units(restarted) == before
    replay = restarted.replay("student-1", "session-1", wrong["episode_id"])
    assert {e["event_type"] for e in replay["events"]} >= {"attempt", "revision", "verifier_evidence", "diagnosis", "hint_exposed", "outcome"}
    assert "report" not in str(replay["events"])
    assert submit(restarted, newton(), "revision", wrong["episode_id"])["delivery"] == "acknowledged"


def test_pending_delivery_and_unknown_never_count_as_success(service):
    good = submit(service, newton())
    with pytest.raises(ValueError):
        service.start_probe("student-1", "session-1", good["episode_id"])
    assert not any(u["independent_evidence_count"] or u["assisted_success_count"] for u in units(service).values())
    unknown = submit(service, dict(method="newton", function="x^2-2"), "unknown")
    assert ack(service, unknown)["outcome"] == "unknown"
    assert not any(u["failure_count"] for u in units(service).values())


def test_server_probe_initial_value_no_guess_and_no_leaked_steps(service):
    practice = submit(service, newton())
    assert ack(service, practice)["outcome"] == "observed_success"
    probe = service.start_probe("student-1", "session-1", practice["episode_id"])
    assert service.start_probe("student-1", "session-1", practice["episode_id"])["episode_id"] == probe["episode_id"]
    extra_practice = submit(service, newton(), "extra-practice"); ack(service, extra_practice)
    reserved = service.start_probe("student-1", "session-1", extra_practice["episode_id"])
    assert reserved["challenge"]["function"] != probe["challenge"]["function"]
    challenge = probe["challenge"]
    with pytest.raises(ValueError):
        submit(service, {**challenge, "iterates": [3 ** .5]}, "guess", probe["episode_id"])
    xs = newton(3, challenge["initial_value"])["iterates"]
    result = submit(service, {**challenge, "iterates": xs}, "probe", probe["episode_id"])
    assert result["complete"] and result["evidence"] == {} and result["trace"] == [] and not result["next_probe"]
    assert ack(service, result)["outcome"] == "independent_probe_success"
    assert units(service)["NA_NEWTON"]["independent_evidence_count"] == 1
    assert service.overlay.get_case_state("student-1", "numerical_analysis", "CASE_NEWTON_DERIVATION").independent_transfer_status == "probe_observed"


def test_probe_revision_does_not_claim_independence(service):
    good = submit(service, newton()); ack(service, good)
    probe = service.start_probe("student-1", "session-1", good["episode_id"])
    bad = submit(service, {**probe["challenge"], "iterates": [1, 3]}, "p1", probe["episode_id"])
    ack(service, bad)
    correct = submit(service, {**probe["challenge"], "iterates": newton(3)["iterates"]}, "p2", probe["episode_id"])
    assert ack(service, correct)["outcome"] == "assisted_success"
    assert not units(service)["NA_NEWTON"]["independent_evidence_count"]
    another = submit(service, newton(), "another-practice"); ack(service, another)
    next_probe = service.start_probe("student-1", "session-1", another["episode_id"])
    assert next_probe["challenge"]["function"] != probe["challenge"]["function"]


def test_pending_hints_reserve_budget_even_without_ack(service):
    episode = None
    for i in range(6):
        result = submit(service, dict(method="newton", function="x^2-2", iterates=[1, 3]), str(i), episode)
        episode = result["episode_id"]
        assert result["remaining_help"] == max(0, 2-i)
        if i >= 3:
            assert result["evidence"] == {} and result["trace"] == [] and not result["next_probe"]
    replay = service.replay("student-1", "session-1", episode)
    assert replay["used_help"] == 0


def test_transaction_rollback_and_invalid_event_do_not_leave_counts(service, monkeypatch):
    def broken(*args, **kwargs): raise RuntimeError("disk write failed")
    monkeypatch.setattr(service.store, "save_episode", broken)
    with pytest.raises(RuntimeError): submit(service, newton())
    assert service.store.list_events("student-1", "numerical_analysis") == []
    assert units(service) == {}
    with pytest.raises(ValueError):
        service.overlay.record_process_event("bad", "student-1", "numerical_analysis", ["NA_NEWTON"], event_type="outcome")
    assert service.store.event_record("bad") is None


def test_concurrent_duplicate_and_distinct_requests_do_not_lose_counts(service, tmp_path):
    other = RootEpisodeService(CourseService(store=CourseStore(tmp_path / "course.db")))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda s: submit(s, newton()), [service, other]))
    assert results[0]["episode_id"] == results[1]["episode_id"]
    assert max(u["attempt_count"] for u in units(service).values()) == 1
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda pair: submit(pair[0], newton(), pair[1]), [(service, "two"), (other, "three")]))
    assert max(u["attempt_count"] for u in units(service).values()) == 3
    with pytest.raises(ValueError): submit(service, {**newton(), "iterates": [1, 3]})
    with pytest.raises(KeyError): service.replay("student-2", "session-1", results[0]["episode_id"])
    with pytest.raises(KeyError): service.replay("student-1", "other-session", results[0]["episode_id"])


# Ten fixed production graph/SSE episodes, including three legal alternatives.
EPISODES = [
    (dict(method="newton", function="x^2-2", iterates=[1, 3]), "contradicted"),
    (dict(method="newton", function="x^2-2", iterates=[0, 1]), "contradicted"),
    (dict(method="newton", function="x^3-2*x+2", iterates=[1, 0, 1]), "contradicted"),
    (dict(method="newton", function="x^2-2", iterates=[1, "NaN"]), "contradicted"),
    (dict(method="bisection", function="x^2-2", brackets=[[1, 2], [1.5, 2]]), "contradicted"),
    (dict(method="newton", function="x^2-2"), "inconclusive"),
    (dict(method="newton", function="x^2-2", iterates=[1, 1.5], stop_reason="iteration_limit"), "inconclusive"),
    (dict(method="newton", function="x^2-2", iterates=[1, 1.25], variant="damped", damping=.5), "supported"),
    (dict(method="newton", function="(x-1)^2", iterates=[2, 1], variant="modified", multiplicity=2, goal="residual"), "supported"),
    (dict(method="bisection", function="x^2-4", iterates=[2], brackets=[[2, 3]]), "supported"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("data,status", EPISODES)
async def test_production_graph_stream_episodes(data, status, service, monkeypatch, tmp_path):
    monkeypatch.setattr("app.knowledge.course_service.get_course_service", lambda *args: service.course)
    # Graph imports the service locally; any model/network call is an error.
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'messages.db'}")
    repo = Repository(settings)
    session = repo.create_session("student-1", "auto")["session_id"]
    runner = TutorOrchestrator(settings, repo)
    runner.workflow_owner.llm.chat_completion = AsyncMock(side_effect=AssertionError("root path must not call model"))
    async def forbidden(*args, **kwargs):
        raise AssertionError("root path must not call model")
        yield
    runner.workflow_owner.llm.stream = forbidden
    request = RootSubmission(attempt=RootAttempt(**data), attempt_id="workflow").model_dump(mode="json")
    events = [e async for e in runner.stream_reply(session, "student-1", "核对过程", root_submission=request)]
    assert any("event: done" in e for e in events), events
    assert not any("event: error" in e for e in events), events
    meta = repo.list_messages(session)[-1]["learning_meta"]
    assert meta["verification_kind"] == "root_oracle"
    assert meta["root_diagnosis"]["status"] == status
    assert meta["root_diagnosis"]["outcome"] == "unknown"
    runner.workflow_owner.llm.chat_completion.assert_not_called()


def test_authenticated_overlay_and_outcome_isolation(service, monkeypatch):
    from app.main import app
    monkeypatch.setattr("app.api.routes_courses.get_course_service", lambda *args: service.course)
    app.dependency_overrides[get_principal] = lambda: Principal("student-1", True)
    try:
        with TestClient(app) as client:
            assert client.get("/api/courses/users/student-2/numerical_analysis/overlay").status_code == 403
            assert client.get("/api/courses/numerical_analysis/graph?student_id=student-2").status_code == 403
            response = client.post("/api/courses/users/student-1/numerical_analysis/events", json={"event_id":"fabricated", "event_type":"attempt", "unit_ids":["NA_NEWTON"], "is_success":True, "is_independent":True})
            assert response.status_code == 403, response.text
            assert client.get("/api/courses/numerical_analysis/candidates").status_code == 403
            assert client.get("/api/courses/numerical_analysis/revisions").status_code == 403
            cases = client.get("/api/courses/numerical_analysis/cases").json()["cases"]
            for case in cases:
                assert case["possible_actions"] == []
                assert all(set(probe) <= {"probe_id", "id", "type", "question"} for probe in case["diagnostic_probes"])
                if case["disclosure_policy"] != "direct": assert case["reasoning_signature"] == []
            result = client.post("/api/courses/numerical_analysis/cases/match", json={"query":"牛顿法初值发散"}).json()
            assert not result.get("diagnostic_probe") or set(result["diagnostic_probe"]) <= {"probe_id", "id", "type", "question"}
    finally:
        app.dependency_overrides.pop(get_principal, None)


def test_ack_and_replay_http_require_owned_session_and_feedback(service, monkeypatch, tmp_path):
    from app.main import app
    from app.api import routes_root_diagnostics as routes
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'auth.db'}")
    repo = Repository(settings)
    session = repo.create_session("student-1", "auto")["session_id"]
    other = repo.create_session("student-2", "auto")["session_id"]
    report = service.submit("student-1", session, RootSubmission(attempt=RootAttempt(**newton()), attempt_id="http"))
    monkeypatch.setattr(routes, "get_repository", lambda: repo)
    monkeypatch.setattr(routes, "get_app_settings", lambda: settings)
    monkeypatch.setattr(routes, "get_course_service", lambda *args: service.course)
    app.dependency_overrides[get_principal] = lambda: Principal("student-1", True)
    payload = dict(session_id=session, episode_id=report["episode_id"], attempt_id=report["attempt_id"], feedback_id=report["feedback_id"])
    try:
        with TestClient(app) as client:
            assert client.post("/api/root-diagnostics/ack", json={**payload, "session_id":other}).status_code == 404
            assert client.post("/api/root-diagnostics/ack", json={**payload, "feedback_id":"forged"}).status_code == 404
            assert client.post("/api/root-diagnostics/ack", json={**payload, "is_success":True}).status_code == 422
            assert client.post("/api/root-diagnostics/ack", json=payload).json()["outcome"] == "observed_success"
            assert client.post("/api/root-diagnostics/ack", json=payload).json()["status"] == "duplicate"
            assert client.get(f"/api/root-diagnostics/episodes/{report['episode_id']}?session_id={other}").status_code == 404
    finally:
        app.dependency_overrides.pop(get_principal, None)


@pytest.mark.asyncio
async def test_cancel_during_transaction_retains_pending_outcome(service, monkeypatch, tmp_path):
    import threading
    from app.tutor.graph import TutorWorkflow
    monkeypatch.setattr("app.knowledge.course_service.get_course_service", lambda *args:service.course)
    started, release = threading.Event(), threading.Event()
    original = RootEpisodeService.submit
    def held(self, *args, **kwargs):
        started.set()
        assert release.wait(5)
        return original(self, *args, **kwargs)
    monkeypatch.setattr(RootEpisodeService, "submit", held)
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'cancel.db'}")
    workflow = TutorWorkflow(settings, Repository(settings))
    task = asyncio.create_task(workflow.root_diagnostic_node({"user_id":"student-1", "session_id":"session-1", "message":"过程", "root_submission":RootSubmission(attempt=RootAttempt(**newton()), attempt_id="cancel").model_dump(mode="json")}, {}))
    assert await asyncio.to_thread(started.wait, 5)
    task.cancel(); release.set()
    with pytest.raises(asyncio.CancelledError): await task
    events = service.store.list_events("student-1", "numerical_analysis")
    assert any(e["event_type"] == "delivery_failed" for e in events)
    assert not any(e["event_type"] == "outcome" for e in events)
    assert not any(u["assisted_success_count"] or u["independent_evidence_count"] for u in units(service).values())


@pytest.mark.parametrize("bad", [row[0] for row in EPISODES[:7]])
def test_error_revision_control_pairs(service, bad):
    wrong = submit(service, bad)
    ack(service, wrong)
    if bad["method"] == "bisection":
        a, b = 1.0, 2.0
        brackets = [[a, b]]
        for _ in range(20):
            m = (a+b)/2
            if (a*a-2)*(m*m-2) <= 0: b = m
            else: a = m
            brackets.append([a, b])
        corrected = {**bad, "brackets":brackets, "stop_reason":"bracket"}
    elif bad["function"] == "x^3-2*x+2":
        xs = [-2.0]
        for _ in range(5):
            x = xs[-1]; xs.append(x - (x**3-2*x+2)/(3*x*x-2))
        corrected = {**bad, "iterates":xs, "interval":[-2,-1]}
    else:
        corrected = newton()
    result = submit(service, corrected, "repair", wrong["episode_id"])
    assert result["complete"], result
    assert ack(service, result)["outcome"] == "assisted_success"
    # Identical valid process without prior help is a legal control.
    control = submit(service, corrected, "control")
    assert control["status"] == "supported" and control["complete"]
    assert ack(service, control)["outcome"] == "observed_success"


@pytest.mark.parametrize("bad,corrected", [
    (dict(method="newton",function="x^2-2",variant="damped",damping=1e-8,iterates=[1,1.000000005],stop_reason="step"),newton()),
    (dict(method="newton",function="0.00000001*(x-10)",iterates=[0],stop_reason="residual"),dict(method="newton",function="0.00000001*(x-10)",iterates=[0,10],interval=[0,20])),
    (dict(method="bisection",function="x^2-4",brackets=[[3,4]]),dict(method="bisection",function="x^2-4",brackets=[[2,3]],iterates=[2])),
    (dict(method="bisection",function="x^2-4",brackets=[[1,3]],stop_reason="bracket"),dict(method="bisection",function="x^2-4",brackets=[[1,3],[1,2]],iterates=[2],stop_reason="bracket")),
    (dict(method="fixed_point",function="x^2-2",phi="(x+2/x)/2",iterates=[1,1.25]),{**newton(),"method":"fixed_point","phi":"(x+2/x)/2"}),
    (dict(method="fixed_point",function="x",phi="2*x",iterates=[.1,.2,.4]),dict(method="fixed_point",function="x",phi="0.5*x",iterates=[.1*2**(-k) for k in range(21)],interval=[-1,1])),
])
def test_remaining_family_revision_and_legal_control(service,bad,corrected):
    wrong=submit(service,bad);ack(service,wrong)
    result=submit(service,corrected,"repair",wrong["episode_id"])
    assert result["complete"], result
    assert ack(service,result)["outcome"]=="assisted_success"
    assert submit(service,corrected,"control")["complete"]


def test_interrupted_delivery_retries_without_outcome_or_duplicate_event(service):
    good=submit(service,newton())
    service.delivery_interrupted("student-1","session-1",good["episode_id"],good["attempt_id"])
    service.delivery_interrupted("student-1","session-1",good["episode_id"],good["attempt_id"])
    events=service.replay("student-1","session-1",good["episode_id"])["events"]
    assert len([e for e in events if e["event_type"]=="delivery_failed"])==1
    assert not any(e["event_type"]=="outcome" for e in events)
    assert submit(service,newton())["feedback_id"]==good["feedback_id"]
    assert ack(service,good)["outcome"]=="observed_success"
    assert max(u["attempt_count"] for u in units(service).values())==1


@pytest.mark.asyncio
async def test_oracle_failure_stream_preserves_unknown(service,monkeypatch,tmp_path):
    monkeypatch.setattr("app.knowledge.course_service.get_course_service",lambda *args:service.course)
    monkeypatch.setattr("app.math_tools.root_expression.RootExpression.evaluate",lambda *args,**kwargs:(_ for _ in ()).throw(RuntimeError("offline failure")))
    settings=Settings(database_url=f"sqlite:///{tmp_path / 'failure.db'}")
    repo=Repository(settings);session=repo.create_session("student-1","auto")["session_id"]
    runner=TutorOrchestrator(settings,repo)
    events=[e async for e in runner.stream_reply(session,"student-1","核对",root_submission=RootSubmission(attempt=RootAttempt(**newton()),attempt_id="failure").model_dump(mode="json"))]
    assert any("event: done" in e for e in events)
    report=repo.list_messages(session)[-1]["learning_meta"]["root_diagnosis"]
    assert report["status"]=="tool_error" and not report["complete"]
    assert service.acknowledge("student-1",session,report["episode_id"],report["attempt_id"],report["feedback_id"])["outcome"]=="unknown"
    assert not any(u["failure_count"] for u in units(service).values())
