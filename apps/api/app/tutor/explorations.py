"""Private GS explorations over existing records, never an official graph writer."""

from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from app.math_tools.numerical_lab import run_numerical
from app.math_tools.exploration_tasks import GS, NewtonTask, ExplorationTask
from app.math_tools.root_runner import LabRequest
from app.math_tools.root_finding import RootAttempt
from app.tutor.learning_context import ReadingContextRef, resolve_learning_context
from app.tutor.learning_workspace import digest
from app.tutor.help_boundary import assert_reference_help_allowed

ID = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")]
Text = Annotated[str, Field(min_length=1, max_length=2000)]
KIND = "exploration"
VERSION = "gs-exploration-v1"


def now():
    return datetime.now(timezone.utc).isoformat()


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "claim", "reason", "title", "label", "prediction", check_fields=False
    )
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("文字内容不能为空白")
        return value


class CourseSource(Strict):
    kind: Literal["course"]
    unit_id: ID
    graph_revision: str = Field(min_length=1, max_length=160)


class NoteSource(Strict):
    kind: Literal["note"]
    note_id: ID
    source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


Source = Annotated[
    ReadingContextRef | CourseSource | NoteSource, Field(discriminator="kind")
]


class PersonalNode(Strict):
    id: ID
    label: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    source_ref: Source | None = None


class PersonalEdge(Strict):
    id: ID
    source: ID
    target: ID
    relation: Literal["implies", "supports", "challenges", "related", "unknown"]
    reason: str = Field(min_length=1, max_length=1000)


class PersonalGraph(Strict):
    nodes: list[PersonalNode] = Field(max_length=20)
    edges: list[PersonalEdge] = Field(max_length=30)

    @model_validator(mode="after")
    def endpoints(self):
        ids = {n.id for n in self.nodes}
        if len(ids) != len(self.nodes) or len({e.id for e in self.edges}) != len(
            self.edges
        ):
            raise ValueError("私人节点或关系标识重复")
        if any(
            e.source not in ids or e.target not in ids or e.source == e.target
            for e in self.edges
        ):
            raise ValueError("关系须连接两个当前私人节点")
        return self


class Create(Strict):
    request_id: ID
    title: str = Field(min_length=1, max_length=160)
    claim: Text
    origin_session_id: ID | None = None


class Command(Strict):
    request_id: ID
    expected_revision: int = Field(ge=1)


class Revise(Command):
    claim: Text
    reason: Text


class EditGraph(Command):
    graph: PersonalGraph


class RestoreGraph(Command):
    target_revision: int = Field(ge=1)


class SaveAdvice(Command):
    advice: dict


class AdviceFeedback(Command):
    reason: Text


class Execute(Command):
    tasks: list[ExplorationTask] = Field(min_length=1, max_length=2)
    prediction: Text
    metrics: list[Literal["residual", "step", "spectral_radius"]] = Field(
        min_length=1, max_length=3
    )
    confirmed: Literal[True]


def matrix_evidence(task: GS):
    """Exact 2x2 error-matrix calculation for the supplied decimal coefficients.

    This is a fixed mathematical rule, not a judgment of arbitrary student prose.
    Float trajectory/error bounds are deliberately kept separate.
    """
    if len(task.matrix) != 2:
        return {
            "status": "unknown",
            "scope": "matrix_specific",
            "reason": "首版仅为二阶 GS 提供精确谱半径计算；此处只展示有限轨迹。",
        }
    a, b = map(lambda x: Fraction(str(x)), task.matrix[0])
    c, d = map(lambda x: Fraction(str(x)), task.matrix[1])
    rho = abs(b * c / (a * d))
    dominant = abs(a) > abs(b) and abs(d) > abs(c)
    return {
        "status": "deterministic_calculation",
        "scope": "specified_decimal_rational_matrix",
        "iteration_matrix": [["0", str(-b / a)], ["0", str(b * c / (a * d))]],
        "spectral_radius_exact": str(rho),
        "spectral_radius_display": float(rho),
        "strict_row_dominant": dominant,
        "rho_less_than_one": rho < 1,
        "is_counterexample_to_necessity": rho < 1 and not dominant,
        "statement_scope": "对这个输入矩阵，精确误差迭代矩阵 B=−(D+L)⁻¹U。ρ(B)<1 是该线性定常迭代对任意初始误差趋于零的判据；输入按显示的十进制有理数解释。有限浮点轨迹本身不能证明一般命题，也不是学生掌握证明。",
        "review_state": "deterministic_rule_not_human_review",
    }


def proposal():
    base = {
        "method": "gauss_seidel",
        "rhs": [1, 1],
        "initial": [0, 0],
        "tolerance": 1e-6,
        "limit": 80,
    }
    return {
        "schema_version": VERSION,
        "origin": "deterministic_template",
        "status": "suggested_not_executed",
        "question": "严格行对角占优是充分条件；缺少它是否就一定发散？",
        "tasks": [
            GS(matrix=[[4, 1], [1, 3]], **base).model_dump(),
            GS(matrix=[[1, 2], [0.1, 1]], **base).model_dump(),
        ],
        "metrics": ["residual", "step", "spectral_radius"],
        "notice": "这是可修改的规则模板，不是模型已运行的实验。请先写预测，再确认执行；不执行学生 Python。",
    }


class Explorations:
    def __init__(self, workspace):
        self.w = workspace

    def get(self, owner, id):
        value = self.w.get(owner, KIND, id)
        if value.get("schema_version") != VERSION:
            raise ValueError("探索版本不可读")
        return value

    def bind(self, owner, ref):
        if ref.kind == "reading":
            value = resolve_learning_context(self.w, owner, ref)
            return {
                "ref": ref.model_dump(),
                "title": value["title"],
                "review_state": value["content_review_status"],
                "evidence_scope": "source_excerpt",
            }
        if ref.kind == "course":
            if ref.graph_revision != self.w.revision():
                raise ValueError("课程版本已变化，请重新选择来源")
            # The store, not a stale in-memory graph copy, is authoritative.
            saved = self.w.store.load_graph(self.w.course_id)
            units = (saved or {}).get("data", {}).get("units", [])
            unit = next((u for u in units if u["id"] == ref.unit_id), None)
            if not unit:
                raise KeyError("course source")
            return {
                "ref": ref.model_dump(),
                "title": unit["title"],
                "review_state": unit.get("review_status", "unknown"),
                "evidence_scope": "official_course_reference_not_personal_claim",
            }
        notes = self.w.repository.list_notes(owner)
        note = next((n for n in notes if n["id"] == ref.note_id), None)
        if not note:
            raise KeyError("note source")
        if digest(note["content"]) != ref.source_hash:
            raise ValueError("笔记版本已变化，请重新选择")
        return {
            "ref": ref.model_dump(),
            "title": note["subject"],
            "review_state": "personal_unreviewed",
            "evidence_scope": "personal_note",
        }

    def graph_sources(self, owner, graph):
        return {
            node.id: self.bind(owner, node.source_ref)
            for node in graph.nodes
            if node.source_ref is not None
        }

    def view(self, owner, value):
        assert_reference_help_allowed(owner, self.w.course)
        result = deepcopy(value)
        # A stale/deleted source remains a historical locator; never auto-rebind it.
        health = []
        for node in value["graph"]["nodes"]:
            if node.get("source_ref"):
                try:
                    self.bind(owner, PersonalNode(**node).source_ref)
                except (KeyError, ValueError):
                    health.append(
                        {"node_id": node["id"], "state": "unavailable_or_changed"}
                    )
        for run in value["runs"]:
            current = self.w.store.learning_record(
                owner, self.w.course_id, "lab" if run["kind"] == "root_lab" else "numerical_lab", run["record_id"]
            )
            hash_key = "input_hash" if run["kind"] == "root_lab" else "source_hash"
            if not current or current[hash_key] != run[hash_key]:
                health.append(
                    {"run_id": run["record_id"], "state": "unavailable_or_changed"}
                )
        result["linked_chats"] = self.w.repository.sessions_for_run_refs(
            owner, [value["id"], *[r["record_id"] for r in value["runs"]]]
        )
        origin = value.get("origin_session_id")
        session = next((s for s in self.w.repository.list_sessions(owner) if s["id"] == origin), None)
        if session and not any(s["id"] == origin for s in result["linked_chats"]):
            result["linked_chats"].insert(0, {"id": origin, "title": session["title"]})
        result["reference_health"] = health
        return result

    def create(self, owner, body):
        assert_reference_help_allowed(owner, self.w.course)
        if body.origin_session_id and not any(s["id"] == body.origin_session_id for s in self.w.repository.list_sessions(owner)):
            raise KeyError("session")
        with self.w.store.transaction():
            old = self.w.store.learning_record(
                owner, self.w.course_id, KIND, body.request_id
            )
            if old:
                if old["create_hash"] not in {digest(body.model_dump()), digest(body.model_dump(exclude_none=True))}:
                    raise ValueError("请求标识已用于不同的探索")
                return self.view(owner, old)
            timestamp = now()
            value = {
                "id": body.request_id,
                "owner_id": owner,
                "course_id": self.w.course_id,
                "schema_version": VERSION,
                "create_hash": digest(body.model_dump()),
                "title": body.title,
                "claim": body.claim,
                "origin_session_id": body.origin_session_id,
                "claim_status": "unreviewed_student_claim",
                "revision": 1,
                "created_at": timestamp,
                "updated_at": timestamp,
                "graph": {"nodes": [], "edges": []},
                "source_bindings": {},
                "runs": [],
                "history": [],
                "receipts": {},
                "help_exposure": False,
                "independent_success": False,
            }
            self.record(value, "created", {"claim": body.claim})
            self.w.save(owner, KIND, value["id"], value)
            return self.view(owner, value)

    def record(self, value, action, payload):
        value["history"].append(
            {
                "revision": value["revision"],
                "at": now(),
                "action": action,
                "payload": payload,
                "graph": deepcopy(value["graph"]),
                "claim": value["claim"],
                "claim_status": "unreviewed_student_claim",
            }
        )

    def update(self, owner, id, action, body):
        assert_reference_help_allowed(owner, self.w.course)
        with self.w.store.transaction():
            value = self.get(owner, id)
            key = body.request_id
            fingerprint = digest({"action": action, "body": body.model_dump()})
            if key in value["receipts"]:
                if value["receipts"][key] != fingerprint:
                    raise ValueError("操作标识已用于不同内容")
                return self.view(owner, value)
            if body.expected_revision != value["revision"]:
                raise ValueError("探索已在其他页面更新；草稿保留，请重新读取后核对")
            if len(value["history"]) >= 100:
                raise ValueError("本探索已达到100次保存预算，请另建探索")
            payload = {}
            if action == "advice":
                value["advice"] = body.advice
                payload = body.advice
            elif action == "reject_relation":
                payload = {"reason": body.reason, "advice_revision": value.get("advice", {}).get("based_on_revision")}
            elif action == "revise":
                value["claim"] = body.claim
                payload = {"claim": body.claim, "reason": body.reason}
            elif action in ("graph", "restore_graph"):
                if action == "restore_graph":
                    prior = next(
                        (
                            r
                            for r in value["history"]
                            if r["revision"] == body.target_revision
                        ),
                        None,
                    )
                    if not prior:
                        raise KeyError("revision")
                    graph = PersonalGraph(**prior["graph"])
                    payload = {"target_revision": body.target_revision}
                else:
                    graph = body.graph
                value["source_bindings"] = self.graph_sources(owner, graph)
                value["graph"] = graph.model_dump()
            elif action == "run":
                assert_reference_help_allowed(owner, self.w.course)
                self.graph_sources(owner, PersonalGraph(**value["graph"]))
                if len(value["runs"]) + len(body.tasks) > 10:
                    raise ValueError("本探索最多保存10次计算，请另建探索")
                outputs = []
                for index, task in enumerate(body.tasks):
                    run_id = f"exp_{digest([owner,id,key,index])[:32]}"
                    if isinstance(task, NewtonTask):
                        result = self.w.lab(owner, LabRequest(
                            request_id=run_id, prediction=body.prediction[:1000], max_iterations=task.limit,
                            attempt=RootAttempt(method="newton", function=task.function,
                                                initial_value=task.initial_value, tolerance=task.tolerance, goal="residual")))
                        result["exploration_id"] = id
                        self.w.save(owner, "lab", run_id, result)
                        ref = {"kind": "root_lab", "record_id": run_id, "input_hash": result["input_hash"],
                               "runner_version": result["runner_version"], "graph_revision": result["graph_revision"], "selected_step": None}
                        value["runs"].append(ref)
                        outputs.append({"ref": ref, "task": task.model_dump(), "status": result["stop_reason"],
                                        "rows": result["rows"], "stop_detail": result["stop_detail"],
                                        "evidence_scope": "finite_newton_trajectory", "next_question": result["diagnosis"]["next_probe"]})
                        continue
                    run_body = {
                        "request_id": run_id,
                        "task": task.model_dump(),
                        "prediction": body.prediction,
                    }
                    result = run_numerical(task)
                    result.update(
                        id=run_id,
                        prediction=body.prediction,
                        source_hash=digest(run_body),
                        created_at=now(),
                        exploration_id=id,
                    )
                    result["matrix_evidence"] = matrix_evidence(task)
                    self.w.save(owner, "numerical_lab", run_id, result)
                    ref = {
                        "kind": "linear_lab",
                        "record_id": run_id,
                        "source_hash": result["source_hash"],
                        "schema_version": "numerical-lab-v1",
                        "selected_step": None,
                    }
                    value["runs"].append(ref)
                    outputs.append(
                        {
                            "ref": ref,
                            "task": task.model_dump(),
                            "matrix_evidence": result["matrix_evidence"],
                            "status": result["status"],
                            "rows": result["rows"],
                            "evidence_scope": result["evidence_scope"],
                        }
                    )
                value["help_exposure"] = True
                payload = {
                    "prediction": body.prediction,
                    "metrics": body.metrics,
                    "runs": outputs,
                    "proposal_origin": "student_confirmed_parameters",
                    "evidence_scope": "computed_observation_and_matrix_specific_calculation",
                    "independent_success": False,
                }
            else:
                raise ValueError("不支持的探索操作")
            value["revision"] += 1
            value["updated_at"] = now()
            value["receipts"][key] = fingerprint
            self.record(value, action, payload)
            self.w.save(owner, KIND, id, value)
            return self.view(owner, value)
