"""Server-resolved reference context; never submitted student evidence."""
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.math_tools.root_runner import RUNNER_VERSION
from app.tutor.help_boundary import assert_reference_help_allowed


class LearningContextRef(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["root_lab"]
    record_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    runner_version: str = Field(min_length=1, max_length=80)
    graph_revision: str = Field(min_length=1, max_length=160)
    selected_step: int | None = Field(default=None, ge=0, le=100)


def resolve_learning_context(workspace, owner: str, ref: LearningContextRef) -> dict:
    with workspace.store.transaction():
        assert_reference_help_allowed(owner, workspace.course)
        run = workspace.get(owner, "lab", ref.record_id)
        if any(run.get(k) != getattr(ref, k) for k in
               ("input_hash", "runner_version", "graph_revision")):
            raise ValueError("实验版本已变化，请重新打开实验后引用。")
        if run["runner_version"] != RUNNER_VERSION or run["graph_revision"] != workspace.revision():
            raise ValueError("教材或计算规则已更新，请重新运行实验后讨论。")
        if run["parameters"]["method"] != "newton":
            raise ValueError("本批实验讨论先支持 Newton；其他方法仍可在实验台使用。")
        rows = run["rows"]
        if ref.selected_step is not None and ref.selected_step >= len(rows):
            raise ValueError("所选迭代步骤不存在。")
        chosen = set(range(min(3, len(rows)))) | set(range(max(0, len(rows)-3), len(rows)))
        if ref.selected_step is not None:
            chosen.update(range(max(0, ref.selected_step-2), min(len(rows), ref.selected_step+3)))
        snapshot = {
            "version": "learning-context-v1", "ref": ref.model_dump(),
            "title": "Newton 求根参考实验", "evidence_kind": "reference_help",
            "independent_success": False, "parameters": run["parameters"],
            "rows": [{k: row[k] for k in ("k", "x", "fx", "step", "bracket")}
                     for i, row in enumerate(rows) if i in chosen],
            "total_rows": len(rows), "omitted_rows": len(rows)-len(chosen),
            "stop_detail": run["stop_detail"][:500],
            "diagnosis_summary": run["diagnosis"]["summary"][:650],
            "max_iterations": run.get("max_iterations", min(100, max(20, len(rows)-1))),
            "iteration_budget_source": "saved" if "max_iterations" in run else "legacy_default",
        }
        # Fail explicitly rather than silently dropping conditions or inventing rows.
        if len(json.dumps(snapshot, ensure_ascii=False, allow_nan=False).encode()) > 8192:
            raise ValueError("实验上下文超过本批预算，请选择较短的表达式或轨迹。")
        return snapshot
