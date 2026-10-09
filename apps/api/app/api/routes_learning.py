"""Authenticated F1–F4 APIs; all records are scoped by server principal."""
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat
from app.auth import Principal, get_principal, get_forwarded_llm_key
from app.main_deps import get_repository, get_app_settings, get_learning_workspace
from app.config import Settings
from app.knowledge.course_service import get_course_service
from app.math_tools.root_finding import RootAttempt
from app.math_tools.root_runner import LabRequest
from app.tutor.learning_workspace import LearningWorkspace
from app.tutor.newton_activity import NewtonActivity
from app.tutor.reading_explanation import source_excerpt, explain
from app.tutor.learning_extensions import assignment, create_teach_back, model_teach_back, submit_code

router = APIRouter(prefix="/api", tags=["learning-workspace"])


def workspace():
    return LearningWorkspace(get_course_service("numerical_analysis"), get_repository())


def invoke(action):
    try:
        return action()
    except KeyError as exc:
        raise HTTPException(404, "记录不存在或无权访问") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlanRequest(Body):
    minutes: Literal[15, 30] = 15
    timezone: str = Field(default="Asia/Hong_Kong", max_length=80)


class AttemptRequest(Body):
    attempt: RootAttempt
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")


class AckRequest(Body):
    attempt_id: str = Field(max_length=80)
    feedback_id: str = Field(max_length=80)


class ConditionRequest(Body):
    option: int = Field(ge=0, le=10)
    source_hash: str = Field(min_length=64, max_length=64)


class AnswerRequest(Body):
    question_id: str = Field(max_length=80)
    option: int = Field(ge=0, le=10)


class NoteRequest(Body):
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    source_id: str = Field(min_length=1, max_length=100)
    source_hash: str = Field(min_length=64, max_length=64)
    section_id: str | None = Field(default=None, max_length=80)
    content: str = Field(min_length=1, max_length=4000)


class ExplanationRequest(Body):
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    source_id: str = Field(min_length=1, max_length=100)
    source_hash: str = Field(min_length=64, max_length=64)
    section_id: str | None = Field(default=None, max_length=80)
    start: int = Field(default=0, ge=0)
    end: int | None = Field(default=None, ge=1)
    question: str = Field(min_length=1, max_length=1000)


class TeachBackRequest(Body):
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    unit_id: str = Field(min_length=1, max_length=80)
    source_hash: str = Field(min_length=64, max_length=64)
    text: str = Field(min_length=1, max_length=4000, pattern=r"\S")
    evidence: dict[int, Annotated[str, Field(min_length=1, max_length=4000)]] = Field(default_factory=dict, max_length=10)
    parent_id: str | None = Field(default=None, max_length=80)


class CodeRequest(Body):
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    assignment_id: str = Field(max_length=80)
    code: str = Field(min_length=1, max_length=8000, pattern=r"\S")
    iterates: list[FiniteFloat] = Field(default_factory=list, max_length=101)
    stop_reason: Literal["residual", "step", "exact", "iteration_limit", "none"] = "none"
    previous_id: str | None = Field(default=None, max_length=80)


class NewtonPredictionRequest(Body):
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    text: str = Field(min_length=1, max_length=1000, pattern=r"\S")
    reason: str = Field(default="", max_length=1000)


class NewtonRevealRequest(Body):
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    mode: Literal["observe", "answer"]


class NewtonStepRequest(Body):
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    expected_step: int = Field(ge=0, le=100)


class NewtonWrittenRequest(Body):
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    run_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    text: str = Field(min_length=1, max_length=2000, pattern=r"\S")


def newton_activity(principal: Principal, service: LearningWorkspace) -> NewtonActivity:
    if not principal.authenticated:
        raise HTTPException(401, "请登录后保存学习活动。")
    return NewtonActivity(service)


@router.get("/root-lab/activity/newton-cycle-v1")
def newton_state(principal: Principal = Depends(get_principal),
                 service: LearningWorkspace = Depends(get_learning_workspace)):
    return invoke(lambda: newton_activity(principal, service).state(principal.user_id))


@router.post("/root-lab/activity/newton-cycle-v1/predict")
def newton_predict(body: NewtonPredictionRequest, principal: Principal = Depends(get_principal),
                   service: LearningWorkspace = Depends(get_learning_workspace)):
    return invoke(lambda: newton_activity(principal, service).predict(principal.user_id, body.request_id, body.text, body.reason))


@router.post("/root-lab/activity/newton-cycle-v1/reveal")
def newton_reveal(body: NewtonRevealRequest, principal: Principal = Depends(get_principal),
                  service: LearningWorkspace = Depends(get_learning_workspace)):
    return invoke(lambda: newton_activity(principal, service).reveal(principal.user_id, body.request_id, body.mode))


@router.post("/root-lab/activity/newton-cycle-v1/step")
def newton_step(body: NewtonStepRequest, principal: Principal = Depends(get_principal),
                service: LearningWorkspace = Depends(get_learning_workspace)):
    return invoke(lambda: newton_activity(principal, service).step(principal.user_id, body.request_id, body.expected_step))


@router.post("/root-lab/activity/newton-cycle-v1/explain")
def newton_explain(body: NewtonWrittenRequest, principal: Principal = Depends(get_principal),
                   service: LearningWorkspace = Depends(get_learning_workspace)):
    return invoke(lambda: newton_activity(principal, service).explain(principal.user_id, body.request_id, body.run_id, body.input_hash, body.text))


@router.post("/root-lab/activity/newton-cycle-v1/revise")
def newton_revise(body: NewtonWrittenRequest, principal: Principal = Depends(get_principal),
                  service: LearningWorkspace = Depends(get_learning_workspace)):
    return invoke(lambda: newton_activity(principal, service).revise(principal.user_id, body.request_id, body.run_id, body.input_hash, body.text))


@router.post("/teach-back/submissions")
async def teach_back(body: TeachBackRequest, principal: Principal = Depends(get_principal),
                     settings: Settings = Depends(get_app_settings), api_key: str | None = Depends(get_forwarded_llm_key)):
    service = workspace()
    saved = invoke(lambda: create_teach_back(service, principal.user_id, body))
    try:
        return await model_teach_back(service, principal.user_id, saved, settings, api_key)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/teach-back/submissions")
def teach_backs(principal: Principal = Depends(get_principal)):
    service = workspace()
    return {"submissions": service.store.learning_records(principal.user_id, service.course_id, "teach_back")[-30:]}


@router.get("/teach-back/submissions/{record_id}")
def teach_back_record(record_id: str, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().get(principal.user_id, "teach_back", record_id))


@router.get("/code-workshop/assignment")
def code_assignment(principal: Principal = Depends(get_principal)):
    from app.tutor.learning_extensions import guard_reference_help
    invoke(lambda: guard_reference_help(workspace(), principal.user_id))
    return assignment()


@router.post("/code-workshop/submissions")
def code_submit(body: CodeRequest, principal: Principal = Depends(get_principal)):
    return invoke(lambda: submit_code(workspace(), principal.user_id, body))


@router.get("/code-workshop/submissions")
def code_submissions(principal: Principal = Depends(get_principal)):
    service = workspace()
    return {"submissions": service.store.learning_records(principal.user_id, service.course_id, "code_submission")[-30:]}


@router.get("/code-workshop/submissions/{record_id}")
def code_record(record_id: str, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().get(principal.user_id, "code_submission", record_id))


@router.post("/reading/explain")
async def reading_explanation(body: ExplanationRequest, principal: Principal = Depends(get_principal),
                              settings: Settings = Depends(get_app_settings), api_key: str | None = Depends(get_forwarded_llm_key)):
    service = workspace()
    citation = invoke(lambda: source_excerpt(service, principal.user_id, body.source_id, body.source_hash, body.section_id, body.start, body.end))
    try:
        return await explain(service, principal.user_id, body.request_id, body.question, citation, settings, api_key)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/reading/notes")
def reading_note(body: NoteRequest, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().save_reading_note(principal.user_id, **body.model_dump()))


@router.get("/reading/notes")
def reading_notes(principal: Principal = Depends(get_principal)):
    return {"notes": workspace().store.learning_records(principal.user_id, "numerical_analysis", "reading_note")[-30:]}


@router.get("/study/today")
def today(timezone: str = "Asia/Hong_Kong", principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().today(principal.user_id, timezone))


@router.get("/learning/overview")
def overview(timezone: str = "Asia/Hong_Kong", principal: Principal = Depends(get_principal)):
    return {**invoke(lambda: workspace().overview(principal.user_id, timezone)),
            "access_mode": "account" if principal.authenticated else "demo"}


@router.post("/study/plans")
def plan(body: PlanRequest, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().plan(principal.user_id, body.minutes, body.timezone))


@router.get("/study/tasks/{task_id}")
def task(task_id: str, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().get(principal.user_id, "task", task_id))


@router.post("/study/tasks/{task_id}/start")
def start(task_id: str, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().start(principal.user_id, task_id))


@router.post("/study/tasks/{task_id}/attempts")
def attempt(task_id: str, body: AttemptRequest, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().submit(principal.user_id, task_id, body.attempt, body.request_id))


@router.post("/study/tasks/{task_id}/ack")
def ack(task_id: str, body: AckRequest, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().acknowledge(principal.user_id, task_id, body.attempt_id, body.feedback_id))


@router.post("/study/tasks/{task_id}/read-complete")
def read_complete(task_id: str, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().complete_reading(principal.user_id, task_id))


@router.post("/study/tasks/{task_id}/probe")
def probe(task_id: str, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().probe_task(principal.user_id, task_id))


@router.get("/reading/units")
def units(principal: Principal = Depends(get_principal)):
    return {"units": workspace().reading_units()}


@router.post("/reading/units/{unit_id}/condition-attempts")
def condition(unit_id: str, body: ConditionRequest, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().condition(principal.user_id, unit_id, body.option, body.source_hash))


@router.get("/reading/documents/{document_id}")
def document(document_id: str, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().document(principal.user_id, document_id))


@router.get("/reading/documents")
def documents(principal: Principal = Depends(get_principal)):
    return {"documents": workspace().repository.list_documents(principal.user_id)}


@router.post("/root-lab/runs")
def lab(body: LabRequest, principal: Principal = Depends(get_principal)):
    service = workspace()
    run = invoke(lambda: service.lab(principal.user_id, body))
    activity = service.store.learning_record(principal.user_id, service.course_id, "newton_activity", "newton-cycle-v1")
    if activity and (activity.get("run_ref") or {}).get("id") == run["id"]:
        return invoke(lambda: NewtonActivity(service).state(principal.user_id)["run"])
    return run


@router.get("/root-lab/runs/{run_id}")
def lab_run(run_id: str, principal: Principal = Depends(get_principal)):
    service = workspace()
    run = invoke(lambda: service.lab_run(principal.user_id, run_id))
    activity = service.store.learning_record(principal.user_id, service.course_id, "newton_activity", "newton-cycle-v1")
    if activity and (activity.get("run_ref") or {}).get("id") == run_id:
        return invoke(lambda: NewtonActivity(service).state(principal.user_id)["run"])
    return run


@router.get("/root-lab/runs")
def lab_runs(principal: Principal = Depends(get_principal)):
    service = workspace()
    runs = invoke(lambda: service.lab_runs(principal.user_id))
    activity = service.store.learning_record(principal.user_id, service.course_id, "newton_activity", "newton-cycle-v1")
    if activity and activity.get("run_ref"):
        activity_id = activity["run_ref"]["id"]
        visible = invoke(lambda: NewtonActivity(service).state(principal.user_id)["run"])
        runs = [visible if run["id"] == activity_id else run for run in runs]
    return {"runs": runs}


@router.post("/assessments")
def new_assessment(principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().new_assessment(principal.user_id))


@router.get("/assessments")
def assessments(principal: Principal = Depends(get_principal)):
    service = workspace()
    return {"assessments": [service.assessment_public(a) for a in service.store.learning_records(principal.user_id, "numerical_analysis", "assessment")[-20:]]}


@router.get("/assessments/{assessment_id}")
def assessment(assessment_id: str, principal: Principal = Depends(get_principal)):
    service = workspace()
    return invoke(lambda: service.assessment_public(service.get(principal.user_id, "assessment", assessment_id)))


@router.post("/assessments/{assessment_id}/answers")
def answer(assessment_id: str, body: AnswerRequest, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().answer_assessment(principal.user_id, assessment_id, body.question_id, body.option))


@router.post("/assessments/{assessment_id}/submit")
def submit(assessment_id: str, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().submit_assessment(principal.user_id, assessment_id))


@router.post("/assessments/{assessment_id}/end")
def end_assessment(assessment_id: str, principal: Principal = Depends(get_principal)):
    return invoke(lambda: workspace().end_assessment(principal.user_id, assessment_id))
