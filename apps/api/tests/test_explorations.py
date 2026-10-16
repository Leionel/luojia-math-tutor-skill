"""Private GS exploration regression; all execution is offline and deterministic."""

import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import routes_explorations
from app.auth import Principal, get_principal
from app.main_deps import get_learning_workspace
from app.tutor.explorations import (
    Explorations,
    Create,
    Execute,
    EditGraph,
    PersonalGraph,
    Revise,
    RestoreGraph,
    GS,
    matrix_evidence,
    proposal,
    CourseSource,
    NoteSource,
)
from app.tutor.learning_workspace import digest
from app.tutor.learning_context import resolve_learning_context, LinearContextRef
from test_learning_workspace import workspace


def created(w):
    w.repository.ensure_user("alice")
    return Explorations(w).create(
        "alice",
        Create(
            request_id="exploration",
            title="GS条件",
            claim="不严格对角占优就必定发散吗？",
        ),
    )


def execution(revision=1, id="run"):
    return Execute(
        request_id=id,
        expected_revision=revision,
        tasks=proposal()["tasks"],
        prediction="第二组也可能收敛，要比较误差矩阵。",
        metrics=["residual", "spectral_radius"],
        confirmed=True,
    )


def test_frozen_r5_g03_and_evidence_boundaries(workspace):
    cases = json.loads(
        (Path(__file__).resolve().parents[3] / "evaluation/r5/cases-v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert (
        "[[1,2],[0.1,1]]"
        in next(c for c in cases["cases"] if c["id"] == "G03")["prompt"]
    )
    e = matrix_evidence(GS(matrix=[[1, 2], [0.1, 1]], rhs=[1, 1], initial=[0, 0]))
    assert e["spectral_radius_exact"] == "1/5" and e["is_counterexample_to_necessity"]
    assert e["review_state"] == "deterministic_rule_not_human_review"
    assert not matrix_evidence(GS(matrix=[[1, 2], [2, 1]], rhs=[1, 1], initial=[0, 0]))[
        "rho_less_than_one"
    ]
    assert (
        matrix_evidence(
            GS(
                matrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                rhs=[1, 1, 1],
                initial=[0, 0, 0],
            )
        )["status"]
        == "unknown"
    )


def test_vertical_graph_run_claim_restore_without_mastery(workspace):
    s = Explorations(workspace)
    v = created(workspace)
    graph = PersonalGraph(
        nodes=[{"id": "a", "label": "严格行对角占优"}, {"id": "b", "label": "GS收敛"}],
        edges=[
            {
                "id": "e",
                "source": "a",
                "target": "b",
                "relation": "implies",
                "reason": "私人待验证判断",
            }
        ],
    )
    v = s.update(
        "alice",
        v["id"],
        "graph",
        EditGraph(request_id="graph", expected_revision=1, graph=graph),
    )
    v = s.update("alice", v["id"], "run", execution(2))
    assert (
        v["revision"] == 3
        and len(v["runs"]) == 2
        and v["help_exposure"]
        and not v["independent_success"]
    )
    for ref in v["runs"]:
        context = resolve_learning_context(workspace, "alice", LinearContextRef(**ref))
        assert (
            context["ref"]["record_id"] == ref["record_id"]
            and context["linear_check"]["matrix_specific"]["status"]
            == "deterministic_calculation"
        )
        assert (
            workspace.get("alice", "numerical_lab", ref["record_id"])["exploration_id"]
            == v["id"]
        )
    v = s.update(
        "alice",
        v["id"],
        "revise",
        Revise(
            request_id="claim",
            expected_revision=3,
            claim="缺少充分条件不能推出发散。",
            reason="第二组谱半径1/5小于1。",
        ),
    )
    assert v["history"][0]["claim"] == "不严格对角占优就必定发散吗？"
    v = s.update(
        "alice",
        v["id"],
        "restore_graph",
        RestoreGraph(request_id="undo", expected_revision=4, target_revision=1),
    )
    assert (
        not v["graph"]["nodes"]
        and len(v["runs"]) == 2
        and v["claim"] == "缺少充分条件不能推出发散。"
    )
    assert workspace.repository.list_mastery("alice") == []


def test_replay_conflict_and_concurrent_revision(workspace):
    s = Explorations(workspace)
    v = created(workspace)
    assert s.update("alice", v["id"], "run", execution()) == s.update(
        "alice", v["id"], "run", execution()
    )
    assert (
        len(
            workspace.store.learning_records(
                "alice", workspace.course_id, "numerical_lab"
            )
        )
        == 2
    )
    with pytest.raises(ValueError):
        s.update("alice", v["id"], "run", execution(2))
    with pytest.raises(ValueError):
        s.update("alice", v["id"], "run", execution(1, "other"))

    def update(i):
        try:
            return s.update(
                "alice",
                v["id"],
                "revise",
                Revise(
                    request_id=f"cas-{i}",
                    expected_revision=2,
                    claim=f"新主张{i}",
                    reason="并发测试",
                ),
            )["revision"]
        except ValueError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(update, [1, 2]))
    assert sorted(map(str, result)) == ["3", "conflict"]


def test_private_sources_stale_and_official_state_unchanged(workspace):
    s = Explorations(workspace)
    v = created(workspace)
    official = workspace.store.load_graph(workspace.course_id)
    doc = workspace.repository.insert_document("private.md", "alice", "# 私人材料")
    source = workspace.document("alice", doc)
    ref = dict(
        kind="reading",
        source_id=doc,
        source_hash=source["source_hash"],
        section_id="0",
        start=0,
        end=len(source["sections"][0]["quote"]),
        graph_revision=None,
    )
    s.update(
        "alice",
        v["id"],
        "graph",
        EditGraph(
            request_id="bind",
            expected_revision=1,
            graph=PersonalGraph(
                nodes=[{"id": "mine", "label": "个人条件", "source_ref": ref}], edges=[]
            ),
        ),
    )
    assert workspace.store.load_graph(workspace.course_id) == official
    with pytest.raises(KeyError):
        s.get("bob", v["id"])
    with workspace.repository.connect() as conn:
        conn.execute("update documents set markdown=? where id=?", ("# changed", doc))
    assert s.view("alice", s.get("alice", v["id"]))["reference_health"] == [
        {"node_id": "mine", "state": "unavailable_or_changed"}
    ]
    with pytest.raises(ValueError):
        s.update("alice", v["id"], "run", execution(2))
    assert not workspace.store.learning_records(
        "alice", workspace.course_id, "numerical_lab"
    )


def test_course_note_and_history_chat_references(workspace):
    s = Explorations(workspace)
    v = created(workspace)
    unit = next(iter(workspace.course.graph_repo.units))
    assert (
        s.bind(
            "alice",
            CourseSource(
                kind="course", unit_id=unit, graph_revision=workspace.revision()
            ),
        )["ref"]["unit_id"]
        == unit
    )
    with pytest.raises(ValueError):
        s.bind(
            "alice", CourseSource(kind="course", unit_id=unit, graph_revision="stale")
        )
    note = workspace.repository.save_note("alice", "prior", "数学", "个人笔记")
    with pytest.raises(KeyError):
        s.bind(
            "bob", NoteSource(kind="note", note_id=note, source_hash=digest("个人笔记"))
        )
    assert (
        s.bind(
            "alice",
            NoteSource(kind="note", note_id=note, source_hash=digest("个人笔记")),
        )["review_state"]
        == "personal_unreviewed"
    )
    v = s.update("alice", v["id"], "run", execution())
    session = workspace.repository.create_session("alice", "数学")["session_id"]
    workspace.repository.add_message(
        session,
        "assistant",
        "计算讨论",
        learning_meta={"learning_context": {"ref": v["runs"][0]}},
    )
    assert s.view("alice", v)["linked_chats"][0]["id"] == session
    assert (
        workspace.repository.sessions_for_run_refs("bob", [v["runs"][0]["record_id"]])
        == []
    )


def test_help_lock_and_auth_block_cached_read_and_replay(workspace):
    s = Explorations(workspace)
    v = created(workspace)
    s.update("alice", v["id"], "run", execution())
    workspace.new_assessment("alice")
    with pytest.raises(ValueError):
        s.view("alice", s.get("alice", v["id"]))
    with pytest.raises(ValueError):
        s.update("alice", v["id"], "run", execution())
    app = FastAPI()
    app.include_router(routes_explorations.router)
    app.dependency_overrides[get_learning_workspace] = lambda: workspace
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    with TestClient(app) as client:
        assert client.get("/api/explorations/proposal").status_code == 409
        assert client.get("/api/explorations/exploration").status_code == 409
        app.dependency_overrides[get_principal] = lambda: Principal("alice", False)
        assert client.get("/api/explorations").status_code == 401


def test_atomic_failure_rolls_back_runs(workspace, monkeypatch):
    s = Explorations(workspace)
    v = created(workspace)
    original = workspace.save

    def fail(owner, kind, id, data):
        if kind == "exploration":
            raise RuntimeError("fixture disk failure")
        return original(owner, kind, id, data)

    monkeypatch.setattr(workspace, "save", fail)
    with pytest.raises(RuntimeError):
        s.update("alice", v["id"], "run", execution())
    assert (
        workspace.store.learning_records("alice", workspace.course_id, "numerical_lab")
        == []
    )
    assert s.get("alice", v["id"])["revision"] == 1


def test_http_schema_ownership_receipt_and_persistent_reload(workspace):
    from app.knowledge.course_store import CourseStore
    from app.knowledge.course_service import CourseService
    from app.tutor.learning_workspace import LearningWorkspace

    app = FastAPI()
    app.include_router(routes_explorations.router)
    app.dependency_overrides[get_learning_workspace] = lambda: workspace
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    workspace.repository.ensure_user("alice")
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/explorations",
                json={"request_id": "http", "title": "GS", "claim": "   "},
            ).status_code
            == 422
        )
        response = client.post(
            "/api/explorations",
            json={"request_id": "http", "title": "GS", "claim": "非对角占优一定发散？"},
        )
        assert response.status_code == 201
        assert (
            client.post(
                "/api/explorations/http/graph",
                json={
                    "request_id": "bad-graph",
                    "expected_revision": 1,
                    "graph": {
                        "nodes": [],
                        "edges": [
                            {
                                "id": "e",
                                "source": "a",
                                "target": "b",
                                "relation": "implies",
                                "reason": "非法端点",
                            }
                        ],
                    },
                },
            ).status_code
            == 422
        )
        body = execution().model_dump()
        for patch in [
            {"confirmed": False},
            {"tasks": [{**body["tasks"][0], "method": "jacobi"}]},
            {"independent_success": True},
        ]:
            assert (
                client.post(
                    "/api/explorations/http/runs", json={**body, **patch}
                ).status_code
                == 422
            )
        response = client.post("/api/explorations/http/runs", json=body)
        assert response.status_code == 200 and len(response.json()["runs"]) == 2
        assert (
            client.post("/api/explorations/http/runs", json=body).json()["revision"]
            == 2
        )
        app.dependency_overrides[get_principal] = lambda: Principal("bob", True)
        assert client.get("/api/explorations/http").status_code == 404
        assert client.get("/api/explorations").json()["items"] == []
        assert client.post("/api/explorations/http/runs", json=body).status_code == 404
    # A new database connection must reconstruct saved process without memory state.
    path = workspace.store._conn.execute("PRAGMA database_list").fetchone()[2]
    reopened = CourseStore(path)
    try:
        service = Explorations(
            LearningWorkspace(CourseService(store=reopened), workspace.repository)
        )
        saved = service.view("alice", service.get("alice", "http"))
        assert (
            saved["revision"] == 2
            and len(saved["runs"]) == 2
            and saved["history"][1]["payload"]["prediction"] == body["prediction"]
        )
    finally:
        reopened.close()


def test_chat_recomputes_matrix_evidence_instead_of_trusting_saved_label(workspace):
    s = Explorations(workspace)
    v = created(workspace)
    v = s.update("alice", v["id"], "run", execution())
    ref = v["runs"][1]
    run = workspace.get("alice", "numerical_lab", ref["record_id"])
    run["matrix_evidence"]["spectral_radius_exact"] = "999"
    workspace.save("alice", "numerical_lab", ref["record_id"], run)
    with pytest.raises(ValueError, match="矩阵证据"):
        resolve_learning_context(workspace, "alice", LinearContextRef(**ref))


def test_r6_keeps_r5_material_frozen_and_holdout_unallocated():
    import hashlib

    root = Path(__file__).resolve().parents[3]
    freeze = json.loads(
        (root / "evaluation/r5/r6-freeze-v1.json").read_text(encoding="utf-8")
    )
    for filename, expected in freeze["files"].items():
        assert hashlib.sha256((root / filename).read_bytes()).hexdigest() == expected
    material = json.loads(
        (root / "evaluation/r5/cases-v1.json").read_text(encoding="utf-8")
    )
    assert material["split"] == "development"
    assert (
        freeze["real_scores"] is None
        and freeze["heldout_status"] == "unallocated_independent_author_required"
    )
