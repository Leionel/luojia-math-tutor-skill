"""Owner-scoped resumption receipts; student reports never discharge premises."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, TypeAdapter

from app.tutor.learning_actions import LearningActions, PreviewActionRequest
from app.tutor.learning_context import ReferenceContext, resolve_learning_context
from app.tutor.learning_workspace import digest

RESUMPTION_VERSION = "resumption-summary-v1"
RESUMPTION_KIND = "resumption_summary"
REF_ADAPTER = TypeAdapter(ReferenceContext)


def _now():
    return datetime.now(timezone.utc).isoformat()


class ResumeActionRef(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    session_id: str = Field(min_length=1, max_length=100)
    message_id: str = Field(min_length=1, max_length=100)
    artifact_id: str = Field(min_length=1, max_length=100)


class LearningResumptionService:
    def __init__(self, workspace):
        self.workspace = workspace
        self.store = workspace.store
        self.course_id = workspace.course_id

    def _source(self, owner, claim_ref):
        # Same ownership, version, activity lineage, range and help checks as Chat.
        return resolve_learning_context(self.workspace, owner, REF_ADAPTER.validate_python(claim_ref))

    def _save(self, owner, task_id, record):
        if len(json.dumps(record, ensure_ascii=False, allow_nan=False).encode()) > 262144:
            raise ValueError("接续摘要超过256KiB预算，请缩短原话或步骤。")
        self.store.save_learning_record(owner, self.course_id, RESUMPTION_KIND, task_id, record)
        return record

    def save_summary(self, owner, task_id, claim_ref, student_claim_text, completed_steps,
                     experiment_parameters, pending_conditions, explanation_preference="socratic",
                     inferred_claim_status=None, tutor_reason="", suggested_proposal=None, help_exposed=False):
        if not isinstance(task_id, str) or not 1 <= len(task_id) <= 100:
            raise ValueError("任务标识范围不符。")
        if not 1 <= len(student_claim_text.strip()) <= 2000:
            raise ValueError("学生原话长度必须在1到2000字符之间。")
        if explanation_preference not in {"socratic", "direct"}:
            raise ValueError("解释偏好不可确认。")
        if len(completed_steps) > 20 or len(pending_conditions) > 10 or any(
                not isinstance(s, str) or not s.strip() or len(s) > 500 for s in [*completed_steps, *pending_conditions]):
            raise ValueError("步骤或条件超过文本预算。")
        if inferred_claim_status not in {None, "supported", "partially_supported", "contradicted", "unknown"} or len(tutor_reason) > 500:
            raise ValueError("摘要推断范围不符。")
        with self.store.transaction():
            snapshot = self._source(owner, claim_ref)
            params = snapshot.get("parameters", {})
            if any(key not in params or params[key] != value for key, value in experiment_parameters.items()):
                raise ValueError("实验参数与已保存来源不同。")
            facts = {"claim_ref": snapshot["ref"], "student_claim_text": student_claim_text,
                "completed_steps": completed_steps, "experiment_parameters": params,
                "explanation_preference": explanation_preference}
            inferences = {"pending_conditions": pending_conditions, "inferred_claim_status": inferred_claim_status,
                "tutor_reason": tutor_reason, "last_suggested_proposal": suggested_proposal}
            old = self.store.learning_record(owner, self.course_id, RESUMPTION_KIND, task_id)
            if old and old.get("status") == "cleared":
                raise ValueError("该任务已被用户清除，请为新任务使用新标识。")
            if old and old["facts"]["claim_ref"] != facts["claim_ref"]:
                raise ValueError("任务来源不能替换，请为另一来源建立新任务。")
            if old and old["facts"] == facts and old["inferences"] == inferences:
                return old
            now = _now()
            record = {"version": RESUMPTION_VERSION, "task_id": task_id, "owner": owner,
                "status": "active", "facts": facts, "inferences": inferences,
                "created_at": old["created_at"] if old else now, "updated_at": now,
                "revision_count": old["revision_count"] + 1 if old else 0,
                "help_exposed": True, "mastery_certified": False,
                "facts_scope": "saved_reference_and_student_reports_not_verified_steps",
                "inferences_scope": "unreviewed_summary_not_authority",
                "processed_requests": old.get("processed_requests", {}) if old else {},
                "supplements": old.get("supplements", []) if old else [],
                "preview_id": old.get("preview_id") if old else None}
            return self._save(owner, task_id, record)

    def get_summary(self, owner, task_id):
        record = self.store.learning_record(owner, self.course_id, RESUMPTION_KIND, task_id)
        if not record:
            raise KeyError(task_id)
        if record.get("owner") != owner:
            raise PermissionError("无权访问其他用户的学习任务。")
        return record

    def update_corrections(self, owner, task_id, explanation_preference=None, corrected_claim_text=None):
        with self.store.transaction():
            record = self.verify_and_resume(owner, task_id)
            if explanation_preference is not None:
                if explanation_preference not in {"socratic", "direct"}:
                    raise ValueError("解释偏好不可确认。")
                record["facts"]["explanation_preference"] = explanation_preference
            if corrected_claim_text is not None:
                if not 1 <= len(corrected_claim_text.strip()) <= 2000:
                    raise ValueError("修正原话长度必须在1到2000字符之间。")
                record["facts"]["student_claim_text"] = corrected_claim_text.strip()
                record["inferences"] = {"pending_conditions": [], "inferred_claim_status": None,
                    "tutor_reason": "原话已更正，条件与建议需重新评定。", "last_suggested_proposal": None}
                record["status"] = "active"
            record["revision_count"] += 1
            record["updated_at"] = _now()
            return self._save(owner, task_id, record)

    def clear_summary(self, owner, task_id):
        with self.store.transaction():
            record = self.get_summary(owner, task_id)
            # Content-free tombstone prevents late requests from recreating the task.
            return self._save(owner, task_id, {"version": RESUMPTION_VERSION, "task_id": task_id,
                "owner": owner, "status": "cleared", "updated_at": _now(),
                "revision_count": record["revision_count"] + 1, "mastery_certified": False})

    def verify_and_resume(self, owner, task_id):
        record = self.get_summary(owner, task_id)
        if record.get("status") == "cleared":
            raise ValueError("该任务已被用户清除，无法接续。")
        self._source(owner, record["facts"]["claim_ref"])
        return record

    def resume_step(self, owner, task_id, request_id, supplemented_condition,
                    changed_parameter_value=None, action_ref=None, prediction=None):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", request_id):
            raise ValueError("请求标识范围不符。")
        if not 1 <= len(supplemented_condition.strip()) <= 1000:
            raise ValueError("请提供1到1000字符的条件补充说明。")
        value = TypeAdapter(FiniteFloat).validate_python(changed_parameter_value) if changed_parameter_value is not None else None
        action = ResumeActionRef.model_validate(action_ref) if action_ref is not None else None
        with self.store.transaction():
            record = self.verify_and_resume(owner, task_id)
            processed = record["processed_requests"]
            fingerprint = digest([supplemented_condition, value, prediction, action.model_dump() if action else None,
                                  record["facts"]["claim_ref"], record["facts"]["student_claim_text"]])
            actions = LearningActions(self.workspace, self.workspace.repository)
            proposal = None
            if action:
                if record["facts"]["claim_ref"]["kind"] != "root_lab":
                    raise ValueError("当前接续预览仅支持Newton实验。")
                proposal, snapshot = actions._proposal(owner, action.session_id, action.message_id, action.artifact_id,
                    REF_ADAPTER.validate_python(record["facts"]["claim_ref"]))
                actions._unexpired(proposal)
            if request_id in processed:
                receipt = processed[request_id]
                if receipt["fingerprint"] != fingerprint:
                    raise ValueError("同一请求标识不能更改补充说明、原话或参数。")
                return receipt["result"]
            if len(processed) >= 20:
                raise ValueError("本任务接续操作已达20次上限。")
            preview = None
            if value is not None:
                if not action or not proposal:
                    raise ValueError("预览需要已交付的当前实验操作卡片。")
                if record.get("preview_id"):
                    raise ValueError("本任务的一次接续预览已完成，请回实验台继续观察。")
                if value == snapshot["parameters"]["initial_value"]:
                    raise ValueError("对照初值必须与原实验不同。")
                preview = actions.preview(owner, action.session_id, action.message_id, action.artifact_id,
                    PreviewActionRequest(context=record["facts"]["claim_ref"], prediction=prediction,
                        parameters={**proposal["parameters"], "initial_value": value},
                        request_id=f"resume-{digest([task_id, request_id])[:48]}"))
            elif action:
                raise ValueError("未选择预览参数，不能提交操作卡片。")
            pending = record["inferences"]["pending_conditions"]
            record["supplements"].append({"text": supplemented_condition, "status": "student_reported_unverified", "at": _now()})
            record["status"] = "supplemented"
            record["revision_count"] += 1
            record["updated_at"] = _now()
            if preview:
                record["preview_id"] = preview["id"]
            result = {"status": "preview_ready" if preview else "supplement_recorded", "task_id": task_id,
                "request_id": request_id, "supplemented_condition": supplemented_condition,
                "supplement_status": "student_reported_unverified", "preview": preview,
                "remaining_pending_conditions": pending, "mastery_certified": False}
            processed[request_id] = {"fingerprint": fingerprint, "result": result}
            self._save(owner, task_id, record)
            return result
