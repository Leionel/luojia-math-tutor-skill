"""Fixed root-lab actions over delivered proposals, not model-selected code."""
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat

from app.math_tools.root_runner import LabRequest, run_reference
from app.tutor.learning_context import LearningContextRef, resolve_learning_context
from app.tutor.learning_workspace import digest


class RootPreviewParameters(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    initial_value: FiniteFloat = Field(ge=-1e25, le=1e25)
    tolerance: FiniteFloat = Field(gt=0, le=1)
    max_iterations: int = Field(ge=1, le=100)


class PreviewActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    context: LearningContextRef
    parameters: RootPreviewParameters
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")


class SavePreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    context: LearningContextRef
    preview_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    preview_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    observation: str = Field(min_length=1, max_length=1000, pattern=r"\S")


def root_proposal(snapshot, run_id):
    now = datetime.now(timezone.utc)
    return {
        "version": "tutor-artifact-v1", "kind": "root_parameter_proposal",
        "artifact_id": str(uuid4()), "run_id": run_id, "origin": "server",
        "context": snapshot["ref"], "action": "preview_root_lab",
        "parameters": {"initial_value": snapshot["parameters"]["initial_value"],
                       "tolerance": snapshot["parameters"]["tolerance"],
                       "max_iterations": snapshot["max_iterations"]},
        "created_at": now.isoformat(), "expires_at": (now+timedelta(days=1)).isoformat(),
        "evidence_kind": "reference_help", "independent_success": False,
        "preview_budget": 3,
    }


class LearningActions:
    # One fixed service map; there is no dynamic import or arbitrary tool name.
    def __init__(self, workspace, repository):
        self.workspace, self.repository = workspace, repository
        self.store, self.course_id = workspace.store, workspace.course_id

    def _proposal(self, owner, session, message, artifact, context=None):
        proposal = self.repository.get_delivered_artifact(owner, session, message, artifact)
        if proposal is None or proposal.get("version") != "tutor-artifact-v1" or proposal.get("action") != "preview_root_lab":
            raise KeyError("artifact")
        ref = LearningContextRef.model_validate(proposal["context"])
        if context is not None and context != ref:
            raise ValueError("当前实验与卡片引用不同，请回到卡片原实验或重新提问。")
        snapshot = resolve_learning_context(self.workspace, owner, ref)
        return proposal, snapshot

    @staticmethod
    def _unexpired(proposal):
        if datetime.now(timezone.utc) >= datetime.fromisoformat(proposal["expires_at"]):
            raise ValueError("这张操作卡片已过期，请重新讨论当前实验。")

    def state(self, owner, session, message, artifact):
        with self.store.transaction():
            proposal, _ = self._proposal(owner, session, message, artifact)
            state = self.store.learning_record(owner, self.course_id, "learning_action", artifact)
            expired = datetime.now(timezone.utc) >= datetime.fromisoformat(proposal["expires_at"])
            if state:
                return {**state, "state": "expired" if expired and state["state"] != "saved" else state["state"], "preview": self.store.learning_record(owner, self.course_id, "lab_preview", state["preview_ids"][-1]),
                        "saved_run": self.store.learning_record(owner, self.course_id, "lab", state.get("saved_run_id", ""))}
            return {"id": artifact, "state": "expired" if expired else "proposed", "preview_ids": [], "used_help": 0,
                    "preview_budget": proposal["preview_budget"], "preview": None, "saved_run": None}

    def preview(self, owner, session, message, artifact, request: PreviewActionRequest):
        with self.store.transaction():
            proposal, snapshot = self._proposal(owner, session, message, artifact, request.context)
            self._unexpired(proposal)
            shape_hash = digest({"session": session, "message": message, "artifact": artifact,
                                 "context": request.context.model_dump(), "parameters": request.parameters.model_dump()})
            old = self.store.learning_record(owner, self.course_id, "lab_preview", request.request_id)
            if old:
                if old["input_hash"] != shape_hash:
                    raise ValueError("同一预览请求标识不能更改参数。")
                return old
            state = self.store.learning_record(owner, self.course_id, "learning_action", artifact) or {
                "id": artifact, "state": "proposed", "preview_ids": [], "used_help": 0,
                "preview_budget": proposal["preview_budget"], "saved_run_id": None}
            if state["state"] == "saved":
                raise ValueError("这张卡片已经保存，请基于新的实验继续讨论。")
            if len(state["preview_ids"]) >= state["preview_budget"]:
                raise ValueError("本张卡片的三次预览已用完，请回到实验台或重新提问。")
            params = {**snapshot["parameters"], "initial_value": request.parameters.initial_value,
                      "tolerance": request.parameters.tolerance}
            lab_request = LabRequest(attempt=params, max_iterations=request.parameters.max_iterations,
                                     prediction="参考参数预览（未填写学生预测）", request_id=request.request_id)
            computed = run_reference(lab_request)
            self._proposal(owner, session, message, artifact, request.context)
            result = {**computed, "id": request.request_id, "input_hash": shape_hash,
                      "context": request.context.model_dump(), "parameters": lab_request.attempt.model_dump(),
                      "max_iterations": request.parameters.max_iterations, "artifact_id": artifact,
                      "session_id": session, "message_id": message, "created_at": datetime.now(timezone.utc).isoformat()}
            if len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode()) > 65536:
                raise ValueError("预览输出超出预算，本次未保存。")
            self.workspace.save(owner, "lab_preview", request.request_id, result)
            state = {**state, "state": "previewed", "preview_ids": [*state["preview_ids"], request.request_id],
                     "used_help": state["used_help"]+3}
            self.workspace.save(owner, "learning_action", artifact, state)
            self.workspace.course.overlay_store.record_process_event(
                f"root-preview:{owner}:{request.request_id}", owner, self.course_id, [], event_type="hint_exposed",
                help_level=3, metadata={"origin":"root_lab_preview", "function": params["function"],
                                       "task_hash": digest("".join(params["function"].replace("**","^").split())),
                                       "session_id":session, "artifact_id":artifact, "reference_id":request.context.record_id,
                                       "evidence_kind":"reference_help"})
            return result

    def save(self, owner, session, message, artifact, request: SavePreviewRequest):
        with self.store.transaction():
            proposal, _ = self._proposal(owner, session, message, artifact, request.context)
            self._unexpired(proposal)
            state = self.store.learning_record(owner, self.course_id, "learning_action", artifact)
            preview = self.store.learning_record(owner, self.course_id, "lab_preview", request.preview_id)
            if not state or not preview or preview["artifact_id"] != artifact or preview["input_hash"] != request.preview_hash:
                raise ValueError("预览不存在或已变化，请重新核对参数。")
            if preview["session_id"] != session or preview["message_id"] != message:
                raise KeyError("preview")
            if state["preview_ids"][-1] != request.preview_id:
                raise ValueError("已有更新的预览，请保存最新版本。")
            saved = self.workspace.lab(owner, LabRequest(attempt=preview["parameters"],
                max_iterations=preview["max_iterations"], prediction=request.observation,
                request_id=f"saved-{digest([session,artifact,request.preview_id])[:48]}"))
            if saved["rows"] != preview["rows"]:
                raise ValueError("计算结果已变化，请重新预览。")
            saved.update(prediction_timing="after_preview", linked_preview_id=request.preview_id)
            self.workspace.save(owner, "lab", saved["id"], saved)
            self.workspace.save(owner, "learning_action", artifact, {**state, "state":"saved", "saved_run_id":saved["id"]})
            return saved
