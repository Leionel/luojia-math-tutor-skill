"""Thin adapters: original runners and original lab record/reference protocols."""
from datetime import datetime, timezone
from app.math_tools.exploration_tasks import GS, NewtonTask
from app.math_tools.numerical_lab import run_numerical
from app.math_tools.root_runner import LabRequest
from app.math_tools.root_finding import RootAttempt
from app.tutor.learning_workspace import digest


def run_exploration_task(workspace, owner, exploration_id, run_id, task, prediction):
    if isinstance(task, NewtonTask):
        result = workspace.lab(owner, LabRequest(request_id=run_id, prediction=prediction[:1000], max_iterations=task.limit,
            attempt=RootAttempt(method="newton", function=task.function, initial_value=task.initial_value,
                                tolerance=task.tolerance, goal="residual")))
        result["exploration_id"] = exploration_id
        workspace.save(owner, "lab", run_id, result)
        ref = {"kind": "root_lab", "record_id": run_id, "input_hash": result["input_hash"],
               "runner_version": result["runner_version"], "graph_revision": result["graph_revision"], "selected_step": None}
        return {"ref": ref, "task": task.model_dump(), "status": result["stop_reason"], "rows": result["rows"],
                "stop_detail": result["stop_detail"], "conditions": [], "evidence_scope": "finite_newton_trajectory",
                "next_question": result["diagnosis"]["next_probe"]}
    result = run_numerical(task)
    result.update(id=run_id, prediction=prediction,
                  source_hash=digest({"request_id": run_id, "task": task.model_dump(), "prediction": prediction}),
                  created_at=datetime.now(timezone.utc).isoformat(), exploration_id=exploration_id)
    if isinstance(task, GS):
        from app.tutor.explorations import matrix_evidence
        result["matrix_evidence"] = matrix_evidence(task)
    workspace.save(owner, "numerical_lab", run_id, result)
    ref = {"kind": "integration_lab" if task.domain == "integration" else "linear_lab", "record_id": run_id,
           "source_hash": result["source_hash"], "schema_version": result["schema_version"], "selected_step": None}
    return {"ref": ref, **{k: result[k] for k in ("task", "status", "rows", "stop_detail", "conditions", "evidence_scope", "matrix_evidence") if k in result}}
