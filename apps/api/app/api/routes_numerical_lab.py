"""Owner-scoped numerical experiments; no grades or student program execution."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, TypeAdapter

from app.auth import Principal, get_principal
from app.api.routes_learning import workspace
from app.math_tools.numerical_lab import NumericalTask, check_result, run_numerical
from app.tutor.learning_workspace import digest

router = APIRouter(prefix="/api/numerical-lab", tags=["numerical-lab"])
TaskAdapter = TypeAdapter(NumericalTask)


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    task: NumericalTask
    prediction: str = Field(default="", max_length=2000)


class CheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: list[Annotated[FiniteFloat, Field(ge=-1e100, le=1e100)]] = Field(min_length=1, max_length=8)
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


def require_reference_access(service, owner):
    for assessment in service.store.learning_records(owner, service.course_id, "assessment"):
        if assessment.get("state") == "in_progress":
            raise HTTPException(409, "请先完成当前自检，再运行参考实验")
    for event in service.store.list_events(owner, service.course_id):
        if event["event_type"] == "probe_issued":
            episode = service.store.load_episode(event["payload"]["episode_id"])
            if episode and not any(a["acknowledged"] for a in episode["attempts"]):
                raise HTTPException(409, "请先提交当前独立检验，再运行参考实验")


def owned_run(service, owner, run_id):
    try:
        return service.get(owner, "numerical_lab", run_id)
    except KeyError as exc:
        raise HTTPException(404, "实验不存在或无权访问") from exc


@router.get("/runs")
def list_runs(principal: Principal = Depends(get_principal)):
    service = workspace()
    require_reference_access(service, principal.user_id)
    records = service.store.learning_records(principal.user_id, service.course_id, "numerical_lab")
    return {"runs": records[-30:]}


@router.get("/runs/{run_id}")
def get_run(run_id: str, principal: Principal = Depends(get_principal)):
    service = workspace()
    require_reference_access(service, principal.user_id)
    return owned_run(service, principal.user_id, run_id)


@router.post("/runs")
def create_run(body: RunRequest, principal: Principal = Depends(get_principal)):
    service = workspace()
    with service.store.transaction():
        require_reference_access(service, principal.user_id)
        old = service.store.learning_record(principal.user_id, service.course_id, "numerical_lab", body.request_id)
        source_hash = digest(body.model_dump())
        if old:
            if old["source_hash"] != source_hash:
                raise HTTPException(409, "同一请求标识不能修改实验参数")
            return old
        try:
            result = run_numerical(body.task)
        except (ValueError, ArithmeticError) as exc:
            raise HTTPException(422, "无法完成数值实验，请检查定义域、参数和数值范围") from exc
        result.update(id=body.request_id, prediction=body.prediction, source_hash=source_hash,
                      created_at=datetime.now(timezone.utc).isoformat())
        return service.save(principal.user_id, "numerical_lab", body.request_id, result)


@router.post("/runs/{run_id}/check")
def check_run(run_id: str, body: CheckRequest, principal: Principal = Depends(get_principal)):
    service = workspace()
    with service.store.transaction():
        require_reference_access(service, principal.user_id)
        saved = owned_run(service, principal.user_id, run_id)
        if saved["source_hash"] != body.source_hash:
            raise HTTPException(409, "实验版本不一致，请重新打开保存的实验")
        try:
            feedback = check_result(TaskAdapter.validate_python(saved["task"]), body.answer)
        except (ValueError, ArithmeticError) as exc:
            raise HTTPException(422, "答案维数或数值范围不符") from exc
        return {"run_id": run_id, "source_hash": saved["source_hash"], "independent_success": False, **feedback}
