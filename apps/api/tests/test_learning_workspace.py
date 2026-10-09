import json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from app.auth import Principal, get_principal
from app.config import Settings
from app.knowledge.course_service import CourseService
from app.knowledge.course_store import CourseStore
from app.knowledge.review_schedule import advance_review
from app.math_tools.root_finding import RootAttempt
from app.math_tools.root_runner import LabRequest, run_reference
from app.memory.repository import Repository
from app.tutor.learning_workspace import LearningWorkspace, QUESTIONS


@pytest.fixture
def workspace(tmp_path):
    store = CourseStore(str(tmp_path / "course.db"))
    repo = Repository(Settings(database_url=f"sqlite:///{tmp_path / 'sessions.db'}"))
    return LearningWorkspace(CourseService(store=store), repo)


def practice(workspace, owner="alice"):
    today = workspace.plan(owner, 15, "Asia/Hong_Kong")
    task = next(t for t in today["plan"]["tasks"] if t["kind"] == "practice")
    return workspace.start(owner, task["id"])


def attempt_for(task):
    value = task["challenge"]
    xs = [value["initial_value"]]
    n = float(value["function"].split("-")[-1])
    for _ in range(5):
        xs.append((xs[-1] + n / xs[-1]) / 2)
    return RootAttempt(**{**value, "iterates": xs, "stop_reason": "residual"})


def complete(workspace, task, owner="alice", request_id="correct"):
    result = workspace.submit(owner, task["id"], attempt_for(task), request_id)
    feedback = result["feedback"]
    return workspace.acknowledge(owner, task["id"], feedback["attempt_id"], feedback["feedback_id"])


def test_plan_is_read_only_until_post_and_creation_idempotent(workspace):
    assert workspace.today("alice")["plan"] is None
    with ThreadPoolExecutor(4) as pool:
        plans = list(pool.map(lambda _: workspace.plan("alice", 30, "Asia/Hong_Kong"), range(4)))
    assert all(p["plan"]["task_ids"] == plans[0]["plan"]["task_ids"] for p in plans)
    assert len(plans[0]["plan"]["tasks"]) == 3
    assert workspace.today("bob")["plan"] is None


def test_timezone_validation(workspace):
    with pytest.raises(ValueError):
        workspace.today("alice", "Not/A_Timezone")
    assert len(workspace.today("alice", "Pacific/Kiritimati")["local_date"]) == 10


def test_task_retry_resume_owner_and_persistence(workspace):
    task = practice(workspace)
    assert workspace.start("alice", task["id"])["session_id"] == task["session_id"]
    with pytest.raises(KeyError):
        workspace.start("bob", task["id"])
    rows = workspace.store._query("PRAGMA database_list")
    reopened = CourseStore(rows[0][2])
    assert reopened.learning_record("alice", workspace.course_id, "task", task["id"])["session_id"] == task["session_id"]
    reopened.close()


def test_graph_change_preserves_old_task_but_prevents_start(workspace):
    task = practice(workspace)
    workspace.store.append_revision("new-revision", None, workspace.course_id, "candidate", "accept", {}, "teacher")
    assert workspace.today("alice")["plan"]["stale"]
    with pytest.raises(ValueError, match="版本"):
        workspace.start("alice", task["id"])


def test_practice_ack_then_probe_and_new_probe(workspace):
    task = practice(workspace)
    pending = workspace.submit("alice", task["id"], attempt_for(task), "practice")
    assert pending["state"] == "awaiting_check"
    assert workspace.submit("alice", task["id"], attempt_for(task), "practice")["feedback"] == pending["feedback"]
    with pytest.raises(ValueError, match="先确认"):
        workspace.submit("alice", task["id"], attempt_for(task), "premature-revision")
    assert workspace.today("alice")["reviews"] == []
    done = workspace.acknowledge("alice", task["id"], "practice", pending["feedback"]["feedback_id"])
    assert done["state"] == "assisted_complete"
    duplicate = workspace.acknowledge("alice", task["id"], "practice", pending["feedback"]["feedback_id"])
    assert duplicate["feedback"]["summary"] == pending["feedback"]["summary"]
    assert workspace.today("alice")["reviews"][0]["stage"] == -1
    probe = workspace.probe_task("alice", task["id"])
    assert workspace.probe_task("alice", task["id"])["id"] == probe["id"]
    probe_done = complete(workspace, probe, request_id="probe")
    assert probe_done["state"] == "verified_complete"
    review = workspace.today("alice")["reviews"][0]
    assert review["stage"] == 0
    assert review["parent_episode_id"] == probe_done["episode_id"]
    second_probe = workspace.probe_task("alice", probe["id"])
    assert second_probe["challenge"]["function"] != probe["challenge"]["function"]
    complete(workspace, second_probe, request_id="same-study-session")
    assert workspace.today("alice")["reviews"][0]["stage"] == 0


def test_no_client_task_change_or_false_success(workspace):
    task = practice(workspace)
    with pytest.raises(ValueError, match="指定"):
        workspace.submit("alice", task["id"], attempt_for(task).model_copy(update={"function": "x^2-3"}), "bad")
    with pytest.raises(ValueError):
        workspace.probe_task("alice", task["id"])
    bad = attempt_for(task).model_copy(update={"iterates": [1.0, 2.0]})
    result = workspace.submit("alice", task["id"], bad, "bad-process")
    result = workspace.acknowledge("alice", task["id"], "bad-process", result["feedback"]["feedback_id"])
    assert result["state"] == "needs_revision"
    assert workspace.today("alice")["reviews"][0]["stage"] == -1


def test_due_failed_practice_is_revisable_before_issuing_probe(workspace, monkeypatch):
    task = practice(workspace)
    bad = attempt_for(task).model_copy(update={"iterates": [1.0, 2.0]})
    pending = workspace.submit("alice",task["id"],bad,"failed")
    workspace.acknowledge("alice",task["id"],"failed",pending["feedback"]["feedback_id"])
    class Later(datetime):
        @classmethod
        def now(cls,tz=None):
            return super().now(tz)+timedelta(days=2)
    monkeypatch.setattr("app.tutor.learning_workspace.datetime",Later)
    today = workspace.plan("alice",15,"Asia/Hong_Kong")
    assert today["plan"]["tasks"][0]["kind"] == "practice"
    revised = workspace.start("alice",today["plan"]["tasks"][0]["id"])
    done = complete(workspace,revised,request_id="repair")
    assert done["state"] == "assisted_complete"
    assert workspace.probe_task("alice",done["id"])["kind"] == "review"


def test_reading_is_not_learning_success(workspace):
    plan = workspace.plan("alice", 15, "Asia/Hong_Kong")
    task = next(t for t in plan["plan"]["tasks"] if t["kind"] == "reading")
    assert workspace.complete_reading("alice", task["id"])["state"] == "read_complete"
    assert workspace.today("alice")["reviews"] == []


def test_review_unknown_assisted_failure_duplicate_and_intervals():
    now = datetime(2026, 10, 2, tzinfo=timezone.utc)
    assert advance_review(None, "unknown", "e", "s", now) is None
    state = advance_review(None, "observed_success", "practice", "practice", now)
    assert state["stage"] == -1
    for stage, days in enumerate([1, 3, 7, 14, 14]):
        state = advance_review(state, "independent_probe_success", f"p{stage}", f"s{stage}", now)
        assert state["stage"] == min(stage, 3)
        assert datetime.fromisoformat(state["due_at"]) == now + timedelta(days=days)
        assert advance_review(state, "independent_probe_success", f"p{stage}", f"s{stage}", now) == state
    assisted = advance_review(state, "assisted_success", "help", "h", now)
    assert assisted["stage"] == 3
    assert advance_review(assisted, "failed", "fail", "f", now)["stage"] == -1
    repeated_session = advance_review(state, "independent_probe_success", "same-session", "s4", now + timedelta(hours=1))
    assert repeated_session["due_at"] == state["due_at"]


def test_reading_source_hash_notes_idempotent_and_stale(workspace):
    units = workspace.reading_units()
    assert len(units) == 4
    assert "answer" not in units[0]
    unit = units[0]
    note = workspace.save_reading_note("alice", "note", unit["id"], unit["source_hash"], None, "我的理解")
    assert note["quote"] == unit["quote"]
    assert workspace.save_reading_note("alice", "note", unit["id"], unit["source_hash"], None, "我的理解") == note
    with pytest.raises(ValueError):
        workspace.save_reading_note("alice", "note", unit["id"], unit["source_hash"], None, "改内容")
    with pytest.raises(ValueError):
        workspace.condition("alice", unit["id"], 1, "0" * 64)
    assert not workspace.condition("alice", unit["id"], 1, unit["source_hash"])["independent_success"]


def lab_request(function="x^3-2*x+2", **parameters):
    return LabRequest(attempt=RootAttempt(method="newton", function=function, initial_value=0, **parameters), prediction="可能循环", request_id="run")


def test_cycle_and_reference_is_not_independent():
    result = run_reference(lab_request())
    assert [row["x"] for row in result["rows"][:3]] == [0, 1, 0]
    assert result["diagnosis"]["family"] == "newton_cycle"
    assert result["independent_success"] is False
    assert len(result["rows"]) <= 101


def test_bisection_and_fixed_point_reference():
    request = LabRequest(attempt=RootAttempt(method="bisection",function="x^2-2",interval=(1,2),tolerance=1e-4),prediction="区间收缩",request_id="b")
    result = run_reference(request)
    assert result["stop_reason"] == "bracket"
    assert result["diagnosis"]["complete"]
    fixed = LabRequest(attempt=RootAttempt(method="fixed_point",function="cos(x)-x",phi="cos(x)",initial_value=.5,interval=(0,1),goal="residual",tolerance=1e-4),max_iterations=100,prediction="压缩收敛",request_id="f")
    assert run_reference(fixed)["diagnosis"]["complete"]


def test_bisection_residual_goal_does_not_stop_on_small_interval_only():
    request = LabRequest(attempt=RootAttempt(method="bisection",function="1e6*(x^2-2)",interval=(1,2),goal="residual",tolerance=1e-4),max_iterations=60,prediction="残差比区间宽度更严格",request_id="scaled")
    result = run_reference(request)
    assert result["stop_reason"] == "residual"
    assert abs(result["rows"][-1]["fx"]) <= request.attempt.tolerance
    assert result["diagnosis"]["complete"]


@pytest.mark.parametrize("expression", ["__import__('os')", "x.__class__", "x[0]", "x^100", "1/0"])
def test_lab_rejects_code_or_stops_invalid_math(expression):
    try:
        result = run_reference(lab_request(expression))
        assert result["rows"] == []
    except ValueError:
        pass


def test_lab_idempotency_owner_and_probe_help_block(workspace):
    run = workspace.lab("alice", lab_request())
    assert workspace.lab("alice", lab_request()) == run
    with pytest.raises(KeyError):
        workspace.get("bob", "lab", run["id"])
    with pytest.raises(ValueError):
        workspace.lab("alice", lab_request("x^2-3"))
    task = complete(workspace, practice(workspace))
    probe = workspace.probe_task("alice", task["id"])
    with pytest.raises(ValueError, match="独立"):
        workspace.lab("alice", lab_request(probe["challenge"]["function"]).model_copy(update={"request_id": "protected"}))


def test_equivalent_exposed_lab_expression_is_excluded_from_probe_pool(workspace):
    workspace.lab("alice", lab_request("(x)*(x)-3.0"))
    task = complete(workspace, practice(workspace))
    assert workspace.probe_task("alice", task["id"])["challenge"]["function"] != "x^2-3"


def test_assessment_public_keys_first_answers_submission_and_owner(workspace):
    exam = workspace.new_assessment("alice")
    assert workspace.new_assessment("alice")["id"] == exam["id"]
    assert "feedback" not in exam
    assert all(set(q) == {"id", "prompt", "options"} for q in exam["questions"])
    with pytest.raises(KeyError):
        workspace.get("bob", "assessment", exam["id"])
    with pytest.raises(ValueError):
        workspace.submit_assessment("alice", exam["id"])
    for q in QUESTIONS:
        workspace.answer_assessment("alice", exam["id"], q[0], q[3])
        workspace.answer_assessment("alice", exam["id"], q[0], q[3])
        with pytest.raises(ValueError):
            workspace.answer_assessment("alice", exam["id"], q[0], (q[3]+1)%len(q[2]))
    done = workspace.submit_assessment("alice", exam["id"])
    assert done["reference_matches"] == 6
    assert done["score"] == {"correct": 6, "total": 6, "percentage": 100}
    assert not done["independent_success"]
    assert workspace.submit_assessment("alice", exam["id"]) == done
    with pytest.raises(ValueError):
        workspace.answer_assessment("alice", exam["id"], QUESTIONS[0][0], 0)
    assert workspace.today("alice")["reviews"] == []


def test_chapter_reference_math_keys_and_weak_points(workspace):
    from app.math_tools.root_expression import RootExpression
    f = RootExpression("x^2-5")
    update = 2 - f.evaluate(2) / f.evaluate(2, derivative=True)
    assert float(QUESTIONS[2][2][QUESTIONS[2][3]]) == update
    assert float(QUESTIONS[1][2][QUESTIONS[1][3]]) == (1.125-1)/2
    assert QUESTIONS[0][2][QUESTIONS[0][3]] == "区间连续"
    assert QUESTIONS[3][2][QUESTIONS[3][3]] == "满足条件时的局部结论"
    assert QUESTIONS[4][2][QUESTIONS[4][3]] == "还需要误差界条件"
    assert QUESTIONS[5][2][QUESTIONS[5][3]] == "区间不变且一致压缩"
    exam = workspace.new_assessment("alice")
    for q in QUESTIONS:
        workspace.answer_assessment("alice", exam["id"], q[0], (q[3]+1)%len(q[2]))
    done = workspace.submit_assessment("alice", exam["id"])
    assert done["score"]["correct"] == 0
    assert done["review_units"] == ["NA_BISECTION", "NA_NEWTON", "NA_ROOT_FINDING", "NA_FIXED_POINT"]
    assert workspace.plan("alice",15,"Asia/Hong_Kong")["plan"]["tasks"][0]["unit_id"] == "NA_BISECTION"


def test_private_document_slices_and_note_access(workspace):
    original = "# 第一节\n教材原文。\n## 第二节\n更多内容。"
    doc_id = workspace.repository.insert_document("lesson.md", "alice", original)
    doc = workspace.document("alice", doc_id)
    assert "".join(s["quote"] for s in doc["sections"]) == original
    for section in doc["sections"]:
        assert original[section["start"]:section["end"]] == section["quote"]
    with pytest.raises(KeyError):
        workspace.document("bob", doc_id)
    with pytest.raises(KeyError):
        workspace.save_reading_note("bob", "note", doc_id, doc["source_hash"], "0", "无权限")


def test_ended_assessment_is_retained_without_a_grade(workspace):
    exam = workspace.new_assessment("alice")
    workspace.answer_assessment("alice", exam["id"], "continuity", 0)
    ended = workspace.end_assessment("alice", exam["id"])
    assert ended["state"] == "abandoned"
    assert ended["answers"] == {"continuity": 0}
    assert "score" not in ended and "feedback" not in ended
    assert workspace.new_assessment("alice")["id"] != exam["id"]
    with pytest.raises(ValueError):
        workspace.submit_assessment("alice", exam["id"])


@pytest.mark.asyncio
async def test_source_bound_explanation_offline_and_private_access(workspace):
    from app.tutor.reading_explanation import source_excerpt, explain
    unit = next(u for u in workspace.reading_units() if u["id"] == "NA_NEWTON")
    citation = source_excerpt(workspace, "alice", unit["id"], unit["source_hash"], None, 0, 10)
    assert citation["quote"] == unit["quote"][:10]
    result = await explain(workspace,"alice","explain","用了什么条件？",citation,Settings(llm_api_key=""))
    assert result["status"] == "source_only" and not result["independent_success"]
    with pytest.raises(ValueError):
        source_excerpt(workspace,"alice",unit["id"],"0"*64,None,0,10)
    with pytest.raises(ValueError):
        source_excerpt(workspace,"alice",unit["id"],unit["source_hash"],None,0,10000)
    private = workspace.repository.insert_document("private.md","alice","私有原文 🙂")
    doc = workspace.document("alice", private)
    with pytest.raises(KeyError):
        source_excerpt(workspace,"bob",private,doc["source_hash"],"0",0,3)


@pytest.mark.asyncio
async def test_model_explanation_is_unverified_idempotent_and_failure_recoverable(workspace,monkeypatch):
    from unittest.mock import AsyncMock
    from app.tutor.reading_explanation import source_excerpt, explain, OpenAICompatibleClient
    unit=workspace.reading_units()[0]
    citation=source_excerpt(workspace,"alice",unit["id"],unit["source_hash"],None,0,None)
    mocked=AsyncMock(return_value="必须区分残差与根误差。")
    monkeypatch.setattr(OpenAICompatibleClient,"chat_completion",mocked)
    settings=Settings(llm_api_key="offline-test-placeholder")
    result=await explain(workspace,"alice","model","条件？",citation,settings)
    assert result["verification_kind"] == "model_explanation"
    assert not result["independent_success"]
    assert await explain(workspace,"alice","model","条件？",citation,settings) == result
    assert mocked.await_count == 1
    assert mocked.call_args.args[0][0]["role"] == "system"
    assert citation["quote"] in mocked.call_args.args[0][1]["content"]
    with pytest.raises(ValueError):
        await explain(workspace,"alice","model","替换问题",citation,settings)
    mocked.side_effect=TimeoutError("do not expose private provider errors")
    failure=await explain(workspace,"alice","timeout","问题",citation,settings)
    assert failure["status"] == "unavailable"
    assert "private provider" not in failure["answer"]
    assert workspace.store.learning_record("alice",workspace.course_id,"reading_explanation","timeout") is None


def test_outstanding_probe_blocks_reading_explanation(workspace):
    from app.tutor.reading_explanation import source_excerpt
    task=complete(workspace,practice(workspace))
    workspace.probe_task("alice",task["id"])
    unit=workspace.reading_units()[0]
    with pytest.raises(ValueError, match="独立"):
        source_excerpt(workspace,"alice",unit["id"],unit["source_hash"],None,0,None)


@pytest.mark.parametrize("persistent", [False, True])
def test_learning_transaction_rolls_back(tmp_path, persistent):
    store = CourseStore(str(tmp_path / "rollback.db") if persistent else None)
    with pytest.raises(RuntimeError):
        with store.transaction():
            store.save_learning_record("a", "c", "task", "id", {"id": "id"})
            raise RuntimeError("injected")
    assert store.learning_record("a", "c", "task", "id") is None


def test_http_auth_extra_fields_and_cross_owner(workspace, monkeypatch):
    from app.main import app
    from app.api import routes_learning
    monkeypatch.setattr(routes_learning, "workspace", lambda: workspace)
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    try:
        with TestClient(app) as client:
            assert client.post("/api/study/plans", json={"user_id": "bob"}).status_code == 422
            plan = client.post("/api/study/plans", json={"minutes": 15}).json()
            task_id = plan["plan"]["task_ids"][0]
            assert client.post(f"/api/study/tasks/{task_id}/start",json={}).status_code == 200
            exam = client.post("/api/assessments",json={}).json()
            assert client.post(f"/api/assessments/{exam['id']}/answers",json={"question_id":"continuity","option":0,"is_success":True}).status_code == 422
            app.dependency_overrides[get_principal] = lambda: Principal("bob", True)
            assert client.get(f"/api/study/tasks/{task_id}").status_code == 404
            assert client.get(f"/api/assessments/{exam['id']}").status_code == 404
    finally:
        app.dependency_overrides.clear()


def teach_request(workspace, **kwargs):
    from app.api.routes_learning import TeachBackRequest
    unit = next(u for u in workspace.reading_units() if u["id"] == "NA_NEWTON")
    return TeachBackRequest(request_id="explain", unit_id=unit["id"], source_hash=unit["source_hash"],
                            text="导数不能为零，结论还要求初值接近单根。", evidence={0: "导数不能为零"}, **kwargs)


def test_overview_read_only_owner_and_pending_probe_priority(workspace):
    empty = workspace.overview("alice")
    assert empty["plan"] is None and empty["next_task"] is None
    assert empty["recommendation"]["kind"] == "choose_task"
    assert workspace.store.learning_records("alice",workspace.course_id,"plan") == []
    task = complete(workspace, practice(workspace))
    probe = workspace.probe_task("alice",task["id"])
    overview = workspace.overview("alice")
    assert overview["next_task"]["id"] == probe["id"]
    assert overview["recommendation"]["kind"] == "resume_task"
    assert overview["recommendation"] == workspace.overview("alice")["recommendation"]
    assert overview["recommendation"]["href"] == f"/study?task={probe['id']}"
    assert overview["recommendation"]["mastery_claim"] is False
    assert "challenge" not in overview["next_task"]
    assert overview["counts"]["practice"] == 1 and overview["counts"]["independent"] == 0
    assert workspace.overview("bob")["counts"]["practice"] == 0
    pending = workspace.submit("alice",probe["id"],attempt_for(probe),"pending-probe")
    assert workspace.overview("alice")["next_task"]["state"] == "awaiting_check"
    assert workspace.overview("alice")["recommendation"]["kind"] == "confirm_feedback"
    assert workspace.get("alice","task",probe["id"])["state"] == pending["state"]


def test_overview_prior_day_resume_stale_and_training_score(workspace, monkeypatch):
    task = practice(workspace)
    class Later(datetime):
        @classmethod
        def now(cls,tz=None):
            return super().now(tz)+timedelta(days=2)
    monkeypatch.setattr("app.tutor.learning_workspace.datetime",Later)
    assert workspace.overview("alice")["plan"] is None
    assert workspace.overview("alice")["next_task"]["id"] == task["id"]
    exam = workspace.new_assessment("alice")
    workspace.answer_assessment("alice",exam["id"],QUESTIONS[0][0],0)
    overview = workspace.overview("alice")
    assert overview["active_assessment"]["answered"] == 1
    assert overview["recommendation"]["kind"] == "assessment_in_progress"
    assert "answers" not in overview["active_assessment"]
    workspace.end_assessment("alice",exam["id"])
    assert workspace.overview("alice")["active_assessment"] is None
    exam = workspace.new_assessment("alice")
    for q in QUESTIONS:
        workspace.answer_assessment("alice",exam["id"],q[0],q[3])
    workspace.submit_assessment("alice",exam["id"])
    assert workspace.overview("alice")["latest_assessment"]["score"]["percentage"] == 100
    assert workspace.overview("alice")["counts"]["independent"] == 0
    workspace.store.append_revision("changed",None,workspace.course_id,"candidate","accept",{},"teacher")
    overview = workspace.overview("alice")
    assert overview["next_task"] is None and overview["stale_tasks"] == 2
    assert overview["recommendation"]["kind"] == "stale_source"
    assert overview["recommendation"]["href"].startswith("/reading?unit=")


def test_teach_back_source_quote_revision_and_no_mastery(workspace):
    from app.tutor.learning_extensions import create_teach_back
    body = teach_request(workspace)
    first = create_teach_back(workspace,"alice",body)
    assert first["conditions"][0]["student_quote"] == "导数不能为零"
    assert first["conditions"][0]["status"] == "self_mapped_unverified"
    assert first["conditions"][1]["status"] == "needs_followup"
    assert not first["independent_success"] and not first["model_commentary"]
    assert create_teach_back(workspace,"alice",body) == first
    with pytest.raises(ValueError,match="同一"):
        create_teach_back(workspace,"alice",body.model_copy(update={"text": "内容已改变" ,"evidence":{}}))
    child = create_teach_back(workspace,"alice",body.model_copy(update={"request_id":"child","parent_id":first["id"]}))
    assert child["parent_id"] == first["id"]
    assert workspace.get("alice","teach_back",first["id"]) == first
    with pytest.raises(KeyError):
        create_teach_back(workspace,"bob",body.model_copy(update={"request_id":"bob-child","parent_id":first["id"]}))
    assert workspace.today("alice")["reviews"] == []


@pytest.mark.parametrize("updates", [{"source_hash":"0"*64},{"evidence":{0:"伪造原句"}}, {"evidence":{-1:"导数不能为零"}}, {"evidence":{100:"导数不能为零"}}])
def test_teach_back_rejects_stale_and_forged_evidence(workspace, updates):
    from app.tutor.learning_extensions import create_teach_back
    with pytest.raises(ValueError):
        create_teach_back(workspace,"alice",teach_request(workspace).model_copy(update=updates))
    assert workspace.store.learning_records("alice",workspace.course_id,"teach_back") == []


@pytest.mark.asyncio
async def test_teach_back_model_is_unverified_and_failure_hides_details(workspace, monkeypatch):
    from unittest.mock import AsyncMock
    from app.llm.openai_compatible import OpenAICompatibleClient
    from app.tutor.learning_extensions import create_teach_back, model_teach_back
    result = create_teach_back(workspace,"alice",teach_request(workspace))
    assert (await model_teach_back(workspace,"alice",result,Settings(llm_api_key="")))["model_status"] == "self_review"
    mocked = AsyncMock(return_value=json.dumps({"opinions":[{"condition_id":r["condition_id"],"judgment":"unknown","evidence":None,"note":"尚需核对具体条件。","followup":"为什么单根附近可用局部收敛结论？"} for r in result["conditions"]]},ensure_ascii=False))
    monkeypatch.setattr(OpenAICompatibleClient,"chat_completion",mocked)
    reviewed = await model_teach_back(workspace,"alice",result,Settings(llm_api_key="test-only"))
    assert reviewed["model_status"] == "model_review" and not reviewed["independent_success"]
    assert mocked.call_args.args[0][1]["role"] == "user"
    assert workspace.today("alice")["reviews"] == []
    another = create_teach_back(workspace,"alice",teach_request(workspace).model_copy(update={"request_id":"timeout"}))
    mocked.side_effect = TimeoutError("private-provider-detail")
    failed = await model_teach_back(workspace,"alice",another,Settings(llm_api_key="test-only"))
    assert failed["model_status"] == "unavailable" and failed["model_commentary"] == ""
    assert "private-provider-detail" not in str(failed)
    assert workspace.get("alice","teach_back",another["id"])["text"] == another["text"]
    assert workspace.get("alice","teach_back",another["id"])["model_status"] == "unavailable"


def code_request(**kwargs):
    from app.api.routes_learning import CodeRequest
    from app.tutor.learning_extensions import ASSIGNMENT_ID, TEMPLATE
    return CodeRequest(request_id="code-first",assignment_id=ASSIGNMENT_ID,code=TEMPLATE,**kwargs)


def test_static_code_never_executes_and_preserves_versions(workspace, tmp_path):
    from app.tutor.learning_extensions import submit_code
    target = tmp_path/"must-not-exist.txt"
    body = code_request().model_copy(update={"code":f"open({str(target)!r}, 'w').write('executed')"})
    first = submit_code(workspace,"alice",body)
    assert not target.exists() and not first["code_executed"]
    assert "unsupported_operation" in {f["kind"] for f in first["findings"]}
    assert submit_code(workspace,"alice",body) == first
    next_body = code_request().model_copy(update={"request_id":"fixed","previous_id":first["id"]})
    second = submit_code(workspace,"alice",next_body)
    assert second["comparison"]["code_changed"]
    assert workspace.get("alice","code_submission",first["id"])["code"] == body.code
    with pytest.raises(KeyError):
        submit_code(workspace,"bob",next_body.model_copy(update={"request_id":"other"}))
    with pytest.raises(ValueError,match="同一"):
        submit_code(workspace,"alice",body.model_copy(update={"code":"pass"}))


def test_static_code_manual_trace_is_separate_and_no_independent_event(workspace):
    from app.tutor.learning_extensions import submit_code
    task = practice(workspace)
    result = submit_code(workspace,"alice",code_request(iterates=attempt_for(task).iterates,stop_reason="residual"))
    assert result["trace_diagnosis"]["complete"]
    assert not result["independent_success"] and not result["code_executed"]
    # Even a supported manual trace cannot prove the deliberately wrong template runs correctly.
    assert any(f["kind"]=="update_sign" for f in result["findings"])
    assert workspace.today("alice")["reviews"] == []
    with pytest.raises(ValueError,match="初值"):
        submit_code(workspace,"alice",code_request(iterates=[2,1]).model_copy(update={"request_id":"bad-trace"}))


def test_static_syntax_variants_and_structure_budget():
    from app.tutor.learning_extensions import static_findings
    assert static_findings("def solve(:")[0]["kind"] == "syntax"
    variant = "def solve(x0, tol, max_iter):\n    return [x0]\n"
    findings = static_findings(variant)
    assert {f["kind"] for f in findings} == {"iteration", "unused_parameter"}
    with pytest.raises(ValueError,match="结构过大"):
        static_findings("x=0\n"*600)


def test_static_checks_use_solve_scope_not_unrelated_helpers():
    from app.tutor.learning_extensions import static_findings
    unrelated = "def solve(x0, tol, max_iter):\n    def helper(tol, max_iter):\n        for i in range(max_iter):\n            return tol\n    pass\n"
    findings = static_findings(unrelated)
    assert {f["kind"] for f in findings} >= {"return", "iteration", "unused_parameter"}
    assert sum(f["kind"] == "unused_parameter" for f in findings) == 2
    reads = "def solve(x0, tol, max_iter):\n    xs = [x0]\n    for i in range(max_iter):\n        if abs(x0) < tol:\n            break\n    return xs\n"
    assert not any(f["kind"] == "unused_parameter" for f in static_findings(reads))


def test_pending_probe_blocks_teach_back_and_code_help(workspace):
    from app.tutor.learning_extensions import create_teach_back, submit_code
    parent = complete(workspace,practice(workspace))
    workspace.probe_task("alice",parent["id"])
    for action in [lambda:create_teach_back(workspace,"alice",teach_request(workspace)),lambda:submit_code(workspace,"alice",code_request())]:
        with pytest.raises(ValueError,match="独立检验"):
            action()
    assert workspace.overview("alice")["counts"]["teach_backs"] == 0
    assert workspace.overview("alice")["counts"]["code_submissions"] == 0


def test_extensions_http_owner_validation_and_safe_overview(workspace, monkeypatch):
    from app.main import app
    from app.api import routes_learning
    monkeypatch.setattr(routes_learning,"workspace",lambda:workspace)
    app.dependency_overrides[get_principal]=lambda:Principal("alice",True)
    try:
        with TestClient(app) as client:
            r=client.get("/api/learning/overview")
            assert r.status_code==200 and r.json()["access_mode"]=="account"
            assert client.get("/api/learning/overview?timezone=invalid").status_code==409
            assert client.post("/api/teach-back/submissions",json={**teach_request(workspace).model_dump(),"independent_success":True}).status_code==422
            saved=client.post("/api/teach-back/submissions",json=teach_request(workspace).model_dump()).json()
            code=client.post("/api/code-workshop/submissions",json=code_request().model_dump()).json()
            assert client.post("/api/code-workshop/submissions",json={**code_request().model_dump(),"run_code":True}).status_code==422
            app.dependency_overrides[get_principal]=lambda:Principal("bob",True)
            assert client.get(f"/api/teach-back/submissions/{saved['id']}").status_code==404
            assert client.get(f"/api/code-workshop/submissions/{code['id']}").status_code==404
            assert client.get("/api/teach-back/submissions").json()["submissions"]==[]
            assert client.get("/api/code-workshop/submissions").json()["submissions"]==[]
    finally:
        app.dependency_overrides.clear()


def test_shared_help_boundary_owner_probe_exception_and_release(workspace):
    from app.tutor.help_boundary import assert_reference_help_allowed
    from app.tutor.root_diagnostics import RootSubmission
    parent = complete(workspace, practice(workspace))
    probe = workspace.probe_task("alice", parent["id"])
    with pytest.raises(ValueError, match="独立检验"):
        assert_reference_help_allowed("alice", workspace.course)
    assert_reference_help_allowed("bob", workspace.course)
    assert_reference_help_allowed("alice", workspace.course, probe["episode_id"])
    with pytest.raises(ValueError, match="独立检验"):
        workspace.episodes.submit("alice", parent["session_id"], RootSubmission(attempt=attempt_for(parent),attempt_id="other-help"))
    complete(workspace, probe, request_id="independent")
    assert_reference_help_allowed("alice", workspace.course)


@pytest.mark.parametrize("boundary", ["probe", "assessment"])
def test_http_chat_exercises_and_notes_cannot_bypass_pending_help(workspace,monkeypatch,boundary):
    from types import SimpleNamespace
    from app.main import app
    from app.main_deps import get_orchestrator,get_repository,get_app_settings
    from app.knowledge import course_service
    parent = complete(workspace, practice(workspace))
    if boundary == "probe":
        workspace.probe_task("alice",parent["id"])
    else:
        workspace.new_assessment("alice")
    monkeypatch.setattr(course_service,"get_course_service",lambda name:workspace.course)
    async def no_generation(**kwargs):
        raise AssertionError("must block before generation")
        yield ""
    app.dependency_overrides[get_principal]=lambda:Principal("alice",True)
    app.dependency_overrides[get_repository]=lambda:workspace.repository
    app.dependency_overrides[get_app_settings]=lambda:Settings(auth_required=True)
    app.dependency_overrides[get_orchestrator]=lambda:SimpleNamespace(repository=workspace.repository,stream_reply=no_generation)
    doc=workspace.repository.insert_document("synthetic.md","alice", "# synthetic\nmath")
    try:
        with TestClient(app) as client:
            for url,body in [
                ("/api/tutor/stream",{"session_id":parent["session_id"],"user_id":"alice","message":"完整求解 x^2-5","mode":"direct"}),
                ("/api/exercises/similar",{"user_id":"alice","concept":"牛顿法"}),
                ("/api/tutor/notes",{"session_id":parent["session_id"]}),
                ("/api/users/alice/notes/from-document",{"document_id":doc})]:
                response=client.post(url,json=body)
                assert response.status_code==409 and ("独立检验" if boundary == "probe" else "自检") in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("finish", ["submit", "abandon"])
def test_chapter_assessment_locks_reference_help_until_finished(workspace, finish):
    from app.tutor.help_boundary import assert_reference_help_allowed
    assessment = workspace.new_assessment("alice")
    with pytest.raises(ValueError, match="自检"):
        assert_reference_help_allowed("alice", workspace.course)
    assert_reference_help_allowed("bob", workspace.course)
    if finish == "submit":
        for question in QUESTIONS:
            workspace.answer_assessment("alice", assessment["id"], question[0], question[3])
        result = workspace.submit_assessment("alice", assessment["id"])
    else:
        result = workspace.end_assessment("alice", assessment["id"])
    assert not result["independent_success"]
    assert_reference_help_allowed("alice", workspace.course)


@pytest.mark.parametrize("boundary", ["assessment", "probe"])
def test_root_lab_http_new_replay_and_history_respect_help_lock(workspace, monkeypatch, boundary):
    from fastapi import FastAPI
    from app.api import routes_learning
    monkeypatch.setattr(routes_learning, "workspace", lambda: workspace)
    app = FastAPI()
    app.include_router(routes_learning.router)
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    with TestClient(app) as client:
        body = lab_request().model_dump(mode="json")
        saved_response = client.post("/api/root-lab/runs", json=body)
        assert saved_response.status_code == 200
        saved = saved_response.json()
        if boundary == "assessment":
            assessment = workspace.new_assessment("alice")
        else:
            parent = complete(workspace, practice(workspace))
            probe = workspace.probe_task("alice", parent["id"])
        # A saved request retry must not bypass a newly started assessment/probe.
        for response in (
            client.post("/api/root-lab/runs", json={**body, "request_id": "new-help"}),
            client.post("/api/root-lab/runs", json=body),
            client.get(f"/api/root-lab/runs/{saved['id']}"),
            client.get("/api/root-lab/runs"),
        ):
            assert response.status_code == 409
            assert "rows" not in response.json() and "runs" not in response.json()
        assert workspace.store.learning_records("alice", workspace.course_id, "lab") == [saved]
        app.dependency_overrides[get_principal] = lambda: Principal("bob", True)
        assert client.get("/api/root-lab/runs").json() == {"runs": []}
        assert client.get(f"/api/root-lab/runs/{saved['id']}").status_code == 404
        assert client.post("/api/root-lab/runs", json=body).status_code == 200
        app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
        if boundary == "assessment":
            workspace.end_assessment("alice", assessment["id"])
        else:
            complete(workspace, probe, request_id="release-reference-lock")
        assert client.post("/api/root-lab/runs", json=body).json() == saved
        assert client.get(f"/api/root-lab/runs/{saved['id']}").json() == saved
        assert client.get("/api/root-lab/runs").json() == {"runs": [saved]}


def test_reading_excerpt_respects_chapter_assessment_lock(workspace):
    from app.tutor.reading_explanation import source_excerpt
    unit = workspace.reading_units()[0]
    assessment = workspace.new_assessment("alice")
    with pytest.raises(ValueError, match="自检"):
        source_excerpt(workspace, "alice", unit["id"], unit["source_hash"], None, 0, None)
    assert source_excerpt(workspace, "bob", unit["id"], unit["source_hash"], None, 0, None)["quote"]
    workspace.end_assessment("alice", assessment["id"])
    assert source_excerpt(workspace, "alice", unit["id"], unit["source_hash"], None, 0, None)["quote"]
