import math

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.math_tools.numerical_lab import LinearTask, IntegrationTask, run_numerical, check_result


def linear(**updates):
    return LinearTask(**{"matrix": [[4, 1], [2, 3]], "rhs": [1, 2], "initial": [0, 0], **updates})


@pytest.mark.parametrize("method", ["jacobi", "gauss_seidel"])
def test_linear_solution_residual_and_bound(method):
    result = run_numerical(linear(method=method))
    assert result["status"] == "residual_met" and result["condition_sufficient"]
    last = result["rows"][-1]
    assert last["vector"] == pytest.approx([0.1, 0.6], abs=1e-6)
    assert max(abs(a-b) for a, b in zip(last["vector"], [0.1, 0.6])) <= last["error_bound"] + 1e-15
    assert result["independent_success"] is False


def test_gauss_seidel_uses_updated_components_and_initial_solution_stops():
    j = run_numerical(linear(limit=1))["rows"][1]["vector"]
    g = run_numerical(linear(method="gauss_seidel", limit=1))["rows"][1]["vector"]
    assert j == pytest.approx([0.25, 2/3])
    assert g == pytest.approx([0.25, 0.5])
    assert len(run_numerical(linear(initial=[0.1, 0.6]))["rows"]) == 1


def test_missing_sufficient_condition_does_not_claim_divergence_or_error_bound():
    result = run_numerical(linear(matrix=[[1, 2], [2, 1]], limit=3))
    assert result["status"] == "iteration_limit"
    assert not result["condition_sufficient"] and all(r["error_bound"] is None for r in result["rows"])
    assert not check_result(linear(), [0, 0])["matches"]


@pytest.mark.parametrize("updates", [{"matrix": [[1, 0], [0, 0]]}, {"rhs": [1, 2, 3]},
                                      {"initial": [math.nan, 0]}, {"limit": 101}])
def test_linear_invalid_inputs_are_rejected(updates):
    with pytest.raises(ValidationError):
        linear(**updates)


@pytest.mark.parametrize("method", ["trapezoid", "simpson", "adaptive_simpson"])
def test_integration_polynomial_and_evidence_scope(method):
    task = IntegrationTask(method=method, expression="x^2", limit=12)
    result = run_numerical(task)
    assert result["rows"][-1]["value"] == pytest.approx(1/3, abs=2e-6)
    assert result["status"] == "estimated_tolerance_met"
    assert result["evidence_scope"] == "quadrature_error_estimate"
    assert all(row["error_bound"] is None for row in result["rows"])
    assert check_result(task, [1/3])["scope"] == "reference_agreement_only"


def test_simpson_cubic_exact_and_adaptive_refines_nonpolynomial():
    assert run_numerical(IntegrationTask(expression="x^3"))["rows"][-1]["value"] == pytest.approx(0.25)
    result = run_numerical(IntegrationTask(method="adaptive_simpson", expression="exp(x)", limit=100))
    assert len(result["rows"]) > 1
    assert result["rows"][-1]["value"] == pytest.approx(math.e-1, abs=1e-6)
    assert result["rows"][-1]["work"] <= 8193


@pytest.mark.parametrize("expression", ["1/x", "log(x)", "__import__('os')", "x.__class__", "exp(10000)"])
def test_integration_rejects_poles_unsafe_syntax_and_overflow(expression):
    with pytest.raises(ValueError):
        run_numerical(IntegrationTask(expression=expression, left=-1, right=1))


def test_budget_is_explicit_and_simpson_requires_even_intervals():
    result = run_numerical(IntegrationTask(expression="exp(x)", method="trapezoid", limit=1, tolerance=1e-12))
    assert result["status"] == "budget_exhausted"
    with pytest.raises(ValidationError):
        IntegrationTask(intervals=3)


def test_aliasing_can_meet_estimate_without_true_accuracy_and_never_claims_proof():
    task = IntegrationTask(expression="sin(16*pi*x)^2", intervals=4)
    result = run_numerical(task)
    # Integral is 1/2, but nested uniform samples hit zeros. This is a counterexample
    # to treating a Richardson estimate or reference agreement as a certificate.
    assert result["status"] == "estimated_tolerance_met"
    assert abs(result["rows"][-1]["value"] - 0.5) > 0.4
    assert result["evidence_scope"] == "quadrature_error_estimate"
    assert check_result(task, [0.5])["scope"] == "reference_agreement_only"


def test_persisted_experiments_are_owned_idempotent_and_checks_use_saved_version(tmp_path, monkeypatch):
    from app.auth import Principal, get_principal
    from app.api import routes_numerical_lab as routes
    from app.knowledge.course_service import CourseService
    from app.knowledge.course_store import CourseStore
    from app.memory.repository import Repository
    from app.config import Settings
    from app.tutor.learning_workspace import LearningWorkspace
    service = LearningWorkspace(CourseService(store=CourseStore(str(tmp_path/"course.db"))),
                                Repository(Settings(database_url=f"sqlite:///{tmp_path/'sessions.db'}")))
    monkeypatch.setattr(routes, "workspace", lambda: service)
    app = FastAPI(); app.include_router(routes.router)
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True, "student")
    client = TestClient(app)
    body = {"request_id": "experiment-one", "task": linear().model_dump(), "prediction": "预计收敛"}
    saved = client.post("/api/numerical-lab/runs", json=body).json()
    assert client.post("/api/numerical-lab/runs", json=body).json() == saved
    assert service.overview("alice")["counts"]["labs"] == 1
    assert service.overview("bob")["counts"]["labs"] == 0
    assert client.post("/api/numerical-lab/runs", json={**body, "prediction": "更改"}).status_code == 409
    check = {"source_hash": saved["source_hash"], "answer": [0.1, 0.6]}
    assert client.post("/api/numerical-lab/runs/experiment-one/check", json=check).json()["matches"]
    assert client.post("/api/numerical-lab/runs/experiment-one/check", json={**check, "source_hash": "0"*64}).status_code == 409
    app.dependency_overrides[get_principal] = lambda: Principal("bob", True, "student")
    assert client.get("/api/numerical-lab/runs").json()["runs"] == []
    assert client.get("/api/numerical-lab/runs/experiment-one").status_code == 404
    assert client.post("/api/numerical-lab/runs/experiment-one/check", json=check).status_code == 404
    # Existing independent self-check excludes new reference help as well.
    service.save("bob", "assessment", "pending", {"state": "in_progress"})
    assert client.post("/api/numerical-lab/runs", json=body).status_code == 409
    assert client.get("/api/numerical-lab/runs").status_code == 409
    assert client.post("/api/numerical-lab/runs/experiment-one/check", json=check).status_code == 409
