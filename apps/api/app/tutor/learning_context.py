"""Server-resolved reference context; never submitted student evidence."""
import json
from typing import Literal, Annotated
import math

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


def _resolve_root_context(workspace, owner: str, ref: LearningContextRef) -> dict:
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


class LinearContextRef(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["linear_lab"]
    record_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    schema_version: Literal["numerical-lab-v1"]
    selected_step: int | None = Field(default=None, ge=0, le=100)


class ReadingContextRef(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["reading"]
    source_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    section_id: str | None = Field(default=None, max_length=160)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    graph_revision: str | None = Field(default=None,max_length=160)


ReferenceContext = Annotated[LearningContextRef | LinearContextRef | ReadingContextRef, Field(discriminator="kind")]


def _bounded(snapshot):
    if len(json.dumps(snapshot,ensure_ascii=False,allow_nan=False).encode())>8192:
        raise ValueError("引用超出8KiB预算，请选择较短范围；必要条件未被截断。")
    return snapshot


def resolve_learning_context(workspace,owner:str,ref:ReferenceContext) -> dict:
    if ref.kind=="root_lab":return _resolve_root_context(workspace,owner,ref)
    with workspace.store.transaction():
        assert_reference_help_allowed(owner,workspace.course)
        common={"version":"learning-context-v1","ref":ref.model_dump(),"evidence_kind":"reference_help","independent_success":False}
        if ref.kind=="reading":
            from app.tutor.reading_explanation import source_excerpt
            unit=next((u for u in workspace.reading_units() if u['id']==ref.source_id),None)
            if unit:
                if ref.section_id is not None or ref.graph_revision!=unit['graph_revision']:
                    raise ValueError("课程摘录版本或章节不符，请重新选段。")
                title=unit['title'];source_kind='curated_course_pack'
            else:
                if ref.graph_revision is not None:raise ValueError("上传原文没有课程版本，不能套用课程引用。")
                doc=workspace.document(owner,ref.source_id)
                section=next((x for x in doc['sections'] if x['id']==ref.section_id),None)
                if section is None:raise KeyError('section')
                title=f"{doc['filename'][:80]} · {section['title'][:80]}";source_kind='uploaded_markdown'
            citation=source_excerpt(workspace,owner,ref.source_id,ref.source_hash,ref.section_id,ref.start,ref.end)
            return _bounded({**common,"title":title,"source_kind":source_kind,"content_review_status":unit["review_status"] if unit else "uploaded_unreviewed","citation":citation})
        from app.math_tools.numerical_lab import LinearTask
        run=workspace.get(owner,'numerical_lab',ref.record_id)
        if run.get('source_hash')!=ref.source_hash or run.get('schema_version')!=ref.schema_version:
            raise ValueError("实验版本不符，请重新打开已保存实验。")
        task=LinearTask.model_validate(run.get('task'))
        rows=run.get('rows')
        if not isinstance(rows,list) or not 1<=len(rows)<=task.limit+1 or run.get('independent_success') is not False:
            raise ValueError("保存记录范围不可确认，请重新运行。")
        finite=lambda n:type(n) in {int,float} and math.isfinite(n) and abs(n)<=1e100
        for i,row in enumerate(rows):
            if not isinstance(row,dict) or type(row.get('k')) is not int or row['k']!=i:
                raise ValueError('迭代行不连续，不能引用。')
            if type(row.get('work')) is not int or row['work']<0:raise ValueError('工作量字段缺失或不符。')
            vector=row.get('vector')
            if not isinstance(vector,list) or len(vector)!=len(task.rhs) or not all(finite(n) for n in vector):
                raise ValueError('轨迹向量维数或数值不符。')
            if not finite(row.get('residual')) or row['residual']<0:
                raise ValueError('残差不可确认。')
            if any(row.get(k) is not None and (not finite(row[k]) or row[k]<0) for k in ('step','error_bound')):
                raise ValueError('步差或误差界不可确认。')
        if ref.selected_step is not None and ref.selected_step>=len(rows):raise ValueError('所选迭代不存在。')
        selected=set(range(min(3,len(rows))))|set(range(max(0,len(rows)-3),len(rows)))
        if ref.selected_step is not None:selected.update(range(max(0,ref.selected_step-2),min(len(rows),ref.selected_step+3)))
        conditions=run.get('conditions');scope=run.get('evidence_scope');stop=run.get('stop_detail')
        if not isinstance(conditions,list) or not all(isinstance(x,str) for x in conditions) or not isinstance(scope,str) or not isinstance(stop,str):
            raise ValueError('保存的条件与停止范围缺失。')
        return _bounded({**common,"title":"线性方程组参考实验","task":task.model_dump(),
            "rows":[{k:row[k] for k in ('k','vector','residual','step','error_bound','work')} for i,row in enumerate(rows) if i in selected],
            "conditions":conditions,"evidence_scope":scope,"stop_detail":stop,
            "total_rows":len(rows),"omitted_rows":len(rows)-len(selected)})
