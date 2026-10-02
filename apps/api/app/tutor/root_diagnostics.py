"""Server-owned root episodes; explicit delivery ACK precedes success/help counts."""
import hashlib
import json
import math
import re
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.math_tools.root_finding import FAMILIES, ORACLE_VERSION, RootAttempt, diagnose
from app.tutor.prompt_policy import PROMPT_VERSION


class RootSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attempt: RootAttempt
    attempt_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    episode_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,80}$")


def extract_submission(message: str) -> RootSubmission | None:
    match = re.search(r"```root-attempt\s*\n([\s\S]*?)\n```", message)
    if not match:
        return None
    data = json.loads(match[1])
    # JSON may be a bare controlled attempt or an explicit revision envelope.
    if "attempt" not in data:
        data = {"attempt": data, "attempt_id": uuid.uuid4().hex}
    return RootSubmission.model_validate(data)


def feedback_text(report: dict) -> str:
    names = {"supported": "已获得数值支持", "contradicted": "发现过程偏差",
             "inconclusive": "条件不足，尚不能确认", "tool_error": "验证暂不可用"}
    parts = [f"### 求根过程诊断：{names[report['status']]}", report["summary"]]
    if report.get("error_step") is not None:
        parts.append(f"定位步骤：k={report['error_step']}（从0开始）。")
    if report.get("next_probe"):
        parts.append(report["next_probe"])
    parts.append("本反馈只核对受控表达式与已提交轨迹；数值支持不等同一般性数学证明。")
    return "\n\n".join(parts)


class RootEpisodeService:
    def __init__(self, course):
        self.course, self.store, self.overlay = course, course.store, course.overlay_store

    def owned(self, episode_id, student_id, session_id):
        episode = self.store.load_episode(episode_id)
        if not episode or (episode["student_id"], episode["session_id"], episode["course_id"]) != (student_id, session_id, self.course.course_id):
            raise KeyError("Episode not found")
        return episode

    def _new(self, student_id, session_id, kind="practice", challenge=None):
        graph = self.store.load_graph(self.course.course_id) or {}
        return {"episode_id": uuid.uuid4().hex, "student_id": student_id,
                "course_id": self.course.course_id, "session_id": session_id,
                "kind": kind, "challenge": challenge, "attempts": [], "help_budget": 3,
                "used_help": 0, "revision": self.store.latest_revision_id(self.course.course_id) or f"seed:{graph.get('seed_checksum', '')}",
                "graph_generation": graph.get("generation", 0)}

    def submit(self, student_id, session_id, submission: RootSubmission, *, mode="socratic", model=None):
        # All attempt/event/episode writes share the same store transaction.
        with self.store.transaction():
            episode = self.owned(submission.episode_id, student_id, session_id) if submission.episode_id else self._new(student_id, session_id)
            prior = next((a for a in episode["attempts"] if a["attempt_id"] == submission.attempt_id), None)
            encoded = submission.attempt.model_dump(mode="json")
            digest = hashlib.sha256(json.dumps(encoded, sort_keys=True).encode()).hexdigest()
            if prior:
                if prior["input_digest"] != digest:
                    raise ValueError("Attempt id reused with different input")
                return prior["public"]
            # Idempotency for a first request without an episode id.
            identity = f"root:{self.course.course_id}:{student_id}:{session_id}:{submission.attempt_id}"
            old = self.store.event_record(identity)
            if old:
                other = self.owned(old["payload"]["episode_id"], student_id, session_id)
                found = next(a for a in other["attempts"] if a["attempt_id"] == submission.attempt_id)
                if found["input_digest"] != digest:
                    raise ValueError("Attempt id reused with different input")
                return found["public"]
            if len(episode["attempts"]) >= 20:
                raise ValueError("Episode attempt budget exhausted; start a new practice")
            first = not episode["attempts"]
            if not first:
                previous_input = episode["attempts"][0]["input"]
                if any(encoded[k] != previous_input[k] for k in ("method", "function", "goal", "tolerance")):
                    raise ValueError("Revision must keep the same task; start a new episode for a different task")
            if episode["kind"] == "probe":
                for key, value in episode["challenge"].items():
                    if encoded[key] != value:
                        raise ValueError("Independent probe task parameters cannot be changed")
            if episode["kind"] == "probe" and (len(encoded["iterates"]) < 2 or encoded["iterates"][0] != episode["challenge"]["initial_value"]):
                raise ValueError("Probe requires a process beginning at the server-issued initial value")
            report = diagnose(submission.attempt)
            wanted = FAMILIES.get(report["family"])
            method_title = {"newton": "牛顿法", "bisection": "二分法", "fixed_point": "不动点迭代"}[submission.attempt.method]
            case = self.course.graph_repo.case_repo.get_case(wanted) if wanted else None
            query = case.title if case else method_title + " 收敛条件 停机过程"
            match = self.course.case_matcher.match(query, self.course.course_id, {"task_mode": "error_debugging"})
            matched = match.matched_case
            case_id = matched.case_id if matched else None
            units = [uid for uid in (matched.concept_ids if matched else ["NA_NEWTON" if submission.attempt.method == "newton" else "NA_BISECTION" if submission.attempt.method == "bisection" else "NA_FIXED_POINT"]) if uid in self.course.graph_repo.units]
            # Budget counts actual diagnostics delivered, not model-requested hint levels.
            level = 0 if report["complete"] or episode["kind"] == "probe" else min(3 if mode == "direct" else 1, episode["help_budget"] - sum(a["help_level"] for a in episode["attempts"]))
            public_report = dict(report)
            if episode["kind"] == "probe":
                public_report.update(summary="独立探针已核对。" if report["complete"] else "独立探针未达到目标，请核对提交过程。", next_probe="", error_step=None, evidence={}, trace=[], family="probe_result")
            elif not level and not report["complete"]:
                public_report.update(summary="本 episode 的提示预算已用完；本轮仅返回验证状态。", next_probe="", error_step=None, evidence={}, trace=[], family="budget_exhausted")
            if episode["kind"] == "probe":
                case_id, units = "CASE_NEWTON_DERIVATION", ["NA_NEWTON"]
            public = {**public_report, "episode_id": episode["episode_id"], "attempt_id": submission.attempt_id,
                      "feedback_id": uuid.uuid4().hex, "case_id": case_id, "case_decision": match.decision.value,
                      "unit_ids": units, "kind": episode["kind"], "help_level": level,
                      "remaining_help": episode["help_budget"] - sum(a["help_level"] for a in episode["attempts"]) - level,
                      "input": encoded, "delivery": "pending", "outcome": "unknown", "graph_revision": episode["revision"]}
            # Correct practice is an observed result; only a first server-issued probe can be independent.
            helped = any(a["help_level"] > 0 for a in episode["attempts"]) or episode["used_help"] > 0
            classification = "independent_probe" if episode["kind"] == "probe" and first and not helped else "assisted" if helped or episode["kind"] == "probe" and not first else "observed"
            context = {"session_id": session_id, "task_id": episode["episode_id"], "episode_id": episode["episode_id"],
                       "attempt_id": submission.attempt_id, "graph_revision": episode["revision"], "graph_generation": episode["graph_generation"],
                       "oracle_version": ORACLE_VERSION, "prompt_version": PROMPT_VERSION,
                       "tolerance_version": report["tolerance_version"], "model_version": "deterministic-root-feedback-v1", "requested_model": model,
                       "input_digest": digest, "evidence_ref": identity + ":evidence"}
            event_type = "probe" if episode["kind"] == "probe" and first else "attempt" if first else "revision"
            self.overlay.record_process_event(identity, student_id, self.course.course_id, units, case_id, event_type, metadata=context)
            self.overlay.record_process_event(identity + ":evidence", student_id, self.course.course_id, units, case_id, "verifier_evidence", metadata={**context, "report": report})
            self.overlay.record_process_event(identity + ":diagnosis", student_id, self.course.course_id, units, case_id, "diagnosis", metadata={**context, "status": report["status"], "family": report["family"], "error_step": report["error_step"]})
            episode["attempts"].append({"attempt_id": submission.attempt_id, "input": encoded, "input_digest": digest,
                                        "public": public, "report": report, "help_level": level,
                                        "classification": classification, "context": context, "identity": identity,
                                        "acknowledged": False})
            self.store.save_episode(episode)
            return public

    def acknowledge(self, student_id, session_id, episode_id, attempt_id, feedback_id):
        with self.store.transaction():
            episode = self.owned(episode_id, student_id, session_id)
            attempt = next((a for a in episode["attempts"] if a["attempt_id"] == attempt_id and a["public"]["feedback_id"] == feedback_id), None)
            if not attempt:
                raise KeyError("Feedback not found")
            if attempt["acknowledged"]:
                return {"status": "duplicate", "outcome": attempt["public"]["outcome"]}
            public, context = attempt["public"], attempt["context"]
            if attempt["help_level"]:
                self.overlay.record_process_event(attempt["identity"] + ":hint", student_id, self.course.course_id, public["unit_ids"], public["case_id"], "hint_exposed", help_level=attempt["help_level"], metadata=context)
                episode["used_help"] += attempt["help_level"]
            report = attempt["report"]
            success = True if report["complete"] and report["status"] == "supported" else False if report["status"] == "contradicted" else None
            if success is not None:
                classification = attempt["classification"]
                # A delayed earlier ACK cannot retroactively make an exposed probe independent.
                independent = classification == "independent_probe" and episode["used_help"] == 0
                help_level = 1 if classification == "assisted" else 0
                self.overlay.record_process_event(attempt["identity"] + ":outcome", student_id, self.course.course_id, public["unit_ids"], public["case_id"], "outcome", is_success=success, is_independent=independent,
                                                  help_level=help_level, misconception_id=report["family"] if not success else None, metadata={**context, "classification": classification})
                public["outcome"] = "independent_probe_success" if success and independent else "assisted_success" if success and help_level else "observed_success" if success else "failed"
            public["delivery"] = "acknowledged"
            attempt["acknowledged"] = True
            self.store.save_episode(episode)
            return {"status": "recorded", "outcome": public["outcome"]}

    def delivery_interrupted(self, student_id, session_id, episode_id, attempt_id):
        """A transport observation, never a numerical failure or a success."""
        with self.store.transaction():
            episode = self.owned(episode_id, student_id, session_id)
            attempt = next(a for a in episode["attempts"] if a["attempt_id"] == attempt_id)
            if attempt["acknowledged"]:
                return
            self.overlay.record_process_event(attempt["identity"] + ":delivery", student_id, self.course.course_id,
                                              attempt["public"]["unit_ids"], attempt["public"]["case_id"],
                                              "delivery_failed", metadata=attempt["context"])

    def start_probe(self, student_id, session_id, parent_id):
        with self.store.transaction():
            parent = self.owned(parent_id, student_id, session_id)
            if not any(a["acknowledged"] and a["report"]["complete"] for a in parent["attempts"]):
                raise ValueError("Complete and acknowledge practice before starting a probe")
            if parent.get("probe_id"):
                existing = self.owned(parent["probe_id"], student_id, session_id)
                return {"episode_id": existing["episode_id"], "challenge": existing["challenge"], "instruction": "继续此前的独立探针。"}
            normalize = lambda text: "".join(text.replace("**", "^").split())
            seen = {normalize(parent["attempts"][0]["input"]["function"])}
            for event in self.store.list_events(student_id, self.course.course_id):
                if event["event_type"] in ("probe", "probe_issued"):
                    prior_probe = self.store.load_episode(event["payload"]["episode_id"])
                    if prior_probe and prior_probe.get("challenge"):
                        seen.add(normalize(prior_probe["challenge"]["function"]))
            tasks = [(f"x^2-{n}", [float(math.isqrt(n)), float(math.isqrt(n)+1)]) for n in range(3, 51) if math.isqrt(n)**2 != n]
            available = next(((f, b) for f, b in tasks if normalize(f) not in seen), None)
            if not available:
                raise ValueError("Development probe pool exhausted; teacher-reviewed tasks are required")
            function, bounds = available
            challenge = {"method": "newton", "function": function, "interval": bounds, "goal": "root_error", "tolerance": 1e-4, "variant": "standard", "initial_value": bounds[0], "derivative": None, "update": None, "damping": 1.0, "multiplicity": 1}
            episode = self._new(student_id, session_id, "probe", challenge)
            episode["parent_id"] = parent_id
            self.overlay.record_process_event(f"root-probe:{self.course.course_id}:{episode['episode_id']}", student_id, self.course.course_id, [], event_type="probe_issued", metadata={"session_id":session_id, "episode_id":episode["episode_id"], "parent_episode_id":parent_id, "graph_revision":episode["revision"], "oracle_version":ORACLE_VERSION})
            self.store.save_episode(episode)
            parent["probe_id"] = episode["episode_id"]
            self.store.save_episode(parent)
            return {"episode_id": episode["episode_id"], "challenge": challenge, "instruction": "独立探针：请自行计算并提交 Newton 轨迹。此任务不提供逐步提示；只有首个提交的验证成功计为独立证据，不代表迁移能力已验证。"}

    def replay(self, student_id, session_id, episode_id):
        episode = self.owned(episode_id, student_id, session_id)
        # Do not expose private verifier references as a way around help budgets.
        return {"episode_id": episode_id, "kind": episode["kind"], "used_help": episode["used_help"],
                "attempts": [a["public"] for a in episode["attempts"]],
                "events": [{"event_id": e["event_id"], "event_type": e["event_type"], "attempt_id": e["payload"].get("attempt_id"), "evidence_ref": e["payload"].get("evidence_ref")} for e in self.store.list_events(student_id, self.course.course_id, episode_id)]}
