"""One versioned Newton participation activity; reference work is never mastery evidence."""
from datetime import datetime, timezone
from hashlib import sha256

from app.math_tools.root_runner import LabRequest, RUNNER_VERSION
from app.tutor.help_boundary import assert_reference_help_allowed

ACTIVITY_ID = "newton-cycle-v1"
ACTIVITY_VERSION = "newton-participation-v1"
KIND = "newton_activity"
PROBLEM = {"function": "x^3-2*x+2", "derivative": "3*x^2-2", "initial_value": 0,
           "method": "newton", "goal": "residual", "tolerance": 1e-6, "max_iterations": 8}
EXACT_CHECK = {
    "scope": "仅对本题函数、标准牛顿法和 x₀=0 的精确代数判断",
    "steps": ["f(0)=2，f'(0)=-2，所以 x₁=0-2/(-2)=1。",
              "f(1)=1，f'(1)=1，所以 x₂=1-1/1=0。"],
    "conclusion": "两个迭代点的导数均非零，精确更新往复于 0 和 1；局部收敛定理不保证这个初值收敛。数值轨迹本身不是一般二周期的证明。",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class NewtonActivity:
    def __init__(self, workspace):
        self.workspace = workspace
        self.store = workspace.store
        self.course_id = workspace.course_id

    def _record(self, owner):
        return self.store.learning_record(owner, self.course_id, KIND, ACTIVITY_ID)

    def _save(self, owner, record):
        self.store.save_learning_record(owner, self.course_id, KIND, ACTIVITY_ID, record)

    def state(self, owner):
        with self.store.transaction():
            record = self._record(owner)
            if record and record.get("reveal"):
                assert_reference_help_allowed(owner, self.workspace.course)
            if not record:
                return {"id": ACTIVITY_ID, "version": ACTIVITY_VERSION, "problem": PROBLEM,
                        "phase": "predict", "prediction": None, "reveal": None,
                        "explanation": None, "revisions": [], "run": None,
                        "answer_exposed": False, "independent_success": False}
            if record.get("version") != ACTIVITY_VERSION:
                raise ValueError("活动版本已变化，请联系管理员核对旧记录。")
            run = None
            if record.get("run_ref"):
                ref = record["run_ref"]
                run = self.workspace.get(owner, "lab", ref["id"])
                if any(run.get(key) != ref[key] for key in ("id", "input_hash", "runner_version", "graph_revision")):
                    raise ValueError("参考实验版本不匹配，请停止使用这份记录。")
            return {**record, "problem": PROBLEM, "run": run,
                    "context_current": bool(run and run["runner_version"] == RUNNER_VERSION
                                            and run["graph_revision"] == self.workspace.revision()),
                    "exact_check": EXACT_CHECK if record.get("answer_exposure") or record.get("explanation") else None,
                    "answer_exposed": bool(record.get("answer_exposure")),
                    "independent_success": False}

    def predict(self, owner, request_id, text, reason):
        with self.store.transaction():
            old = self._record(owner)
            if old:
                prior = old.get("prediction")
                if prior and prior["request_id"] == request_id and prior["text"] == text and prior["reason"] == reason:
                    return self.state(owner)
                raise ValueError("预测已提交，原文不能覆盖。")
            self._save(owner, {"id": ACTIVITY_ID, "version": ACTIVITY_VERSION, "phase": "predicted",
                               "prediction_choice": "submitted",
                               "prediction": {"text": text, "reason": reason, "request_id": request_id, "at": _now()},
                               "reveal": None, "run_ref": None, "answer_exposure": None,
                               "explanation": None, "revisions": [], "evidence_kind": "student_process"})
            return self.state(owner)

    def reveal(self, owner, request_id, mode):
        with self.store.transaction():
            assert_reference_help_allowed(owner, self.workspace.course)
            record = self._record(owner)
            if record is None and mode != "answer":
                raise ValueError("请先提交预测，或选择直接看答案。")
            if record is None:
                record = {"id": ACTIVITY_ID, "version": ACTIVITY_VERSION, "phase": "skipped",
                          "prediction_choice": "skipped",
                          "prediction": None, "reveal": None, "run_ref": None, "answer_exposure": None,
                          "explanation": None, "revisions": [], "evidence_kind": "student_process"}
            if record["reveal"] is not None:
                if record["reveal"]["request_id"] == request_id and record["reveal"]["mode"] == mode:
                    return self.state(owner)
                if mode != "answer":
                    raise ValueError("参考实验已展示，请恢复已有活动。")
                exposure = record.get("answer_exposure")
                if exposure and exposure["request_id"] != request_id:
                    raise ValueError("完整答案已展示，请恢复已有活动。")
                record["answer_exposure"] = exposure or {"request_id": request_id, "at": _now()}
                self._save(owner, record)
                return self.state(owner)
            prediction = record["prediction"]["text"] if record["prediction"] else "学生跳过预测；此处为参考实验，不是学生作答"
            lab_request = LabRequest(attempt={"method": "newton", "function": PROBLEM["function"],
                                              "initial_value": 0, "goal": "residual",
                                              "tolerance": PROBLEM["tolerance"]},
                                     max_iterations=PROBLEM["max_iterations"], prediction=prediction,
                                     request_id=f"newton-{sha256(request_id.encode()).hexdigest()}")
            run = self.workspace.lab(owner, lab_request)
            record.update(phase="observed", run_ref={key: run[key] for key in
                                                       ("id", "input_hash", "runner_version", "graph_revision")},
                          reveal={"request_id": request_id, "mode": mode, "at": _now(),
                                  "evidence_kind": "reference_help"})
            if mode == "answer":
                record["answer_exposure"] = {"request_id": request_id, "at": _now()}
            self._save(owner, record)
            return self.state(owner)

    def explain(self, owner, request_id, run_id, input_hash, text):
        with self.store.transaction():
            record = self._record(owner)
            if not record or not record["reveal"] or not record["run_ref"]:
                raise ValueError("请先观察参考实验。")
            if record["run_ref"]["id"] != run_id or record["run_ref"]["input_hash"] != input_hash:
                raise ValueError("解释与当前实验不匹配。")
            old = record.get("explanation")
            if old:
                if old["request_id"] == request_id and old["text"] == text:
                    return self.state(owner)
                raise ValueError("解释已提交，原文不能覆盖。")
            record["explanation"] = {"text": text, "request_id": request_id, "at": _now(),
                                     "run_id": run_id, "input_hash": input_hash}
            record["phase"] = "explained"
            self._save(owner, record)
            return self.state(owner)

    def revise(self, owner, request_id, run_id, input_hash, text):
        with self.store.transaction():
            record = self._record(owner)
            if not record or not record["prediction"] or not record["explanation"]:
                raise ValueError("先提交预测、观察与解释，再修订原观点。")
            if record["run_ref"]["id"] != run_id or record["run_ref"]["input_hash"] != input_hash:
                raise ValueError("修订与当前实验不匹配。")
            for old in record["revisions"]:
                if old["request_id"] == request_id:
                    if old["text"] != text:
                        raise ValueError("同一请求标识不能更改修订内容。")
                    return self.state(owner)
            if len(record["revisions"]) >= 5:
                raise ValueError("本活动已保存五次修订，请回看原文。")
            record["revisions"].append({"text": text, "request_id": request_id, "at": _now(),
                                        "run_id": run_id, "input_hash": input_hash})
            record["phase"] = "revised"
            self._save(owner, record)
            return self.state(owner)
