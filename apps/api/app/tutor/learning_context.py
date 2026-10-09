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
    activity_claim: "NewtonActivityClaimRef | None" = None


class NewtonActivityClaimRef(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    activity_id: Literal["newton-cycle-v1"]
    activity_version: Literal["newton-participation-v1"]
    claim_kind: Literal["explanation", "revision"]
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    revision_count: int = Field(ge=0, le=5)


LearningContextRef.model_rebuild()


def _saved_newton_claim(workspace, owner: str, run: dict, ref: NewtonActivityClaimRef) -> dict:
    from app.tutor.newton_activity import ACTIVITY_ID, ACTIVITY_VERSION, EXACT_CHECK, KIND, PROBLEM

    record = workspace.store.learning_record(owner, workspace.course_id, KIND, ACTIVITY_ID)
    if not record or record.get("version") != ACTIVITY_VERSION:
        raise ValueError("活动版本已变化，请重新打开活动。")
    run_ref = record.get("run_ref")
    if not isinstance(run_ref, dict) or any(run_ref.get(key) != run.get(key) for key in
                                            ("id", "input_hash", "runner_version", "graph_revision")):
        raise ValueError("活动与实验版本不匹配，请重新打开活动。")
    if record.get("prediction_choice") != "submitted" or not record.get("reveal"):
        raise ValueError("尚无可讨论的独立预测与观察。")
    revisions = record.get("revisions")
    if not isinstance(revisions, list) or len(revisions) != ref.revision_count:
        raise ValueError("活动修订版本已变化，请重新选择原话。")
    if ref.claim_kind == "explanation":
        claim = record.get("explanation")
    else:
        claim = next((item for item in revisions if isinstance(item, dict) and
                      item.get("request_id") == ref.request_id), None)
    if not isinstance(claim, dict) or claim.get("request_id") != ref.request_id:
        raise ValueError("所选解释或修订已变化，请重新选择。")
    if claim.get("run_id") != run["id"] or claim.get("input_hash") != run["input_hash"]:
        raise ValueError("学生原话与当前实验不匹配。")
    words = claim.get("text")
    if not isinstance(words, str) or not 1 <= len(words) <= 2000 or not words.strip():
        raise ValueError("学生原话范围不可确认。")
    params = run.get("parameters") or {}
    if any(params.get(key) != PROBLEM[key] for key in
           ("function", "initial_value", "method", "goal", "tolerance")):
        raise ValueError("本题精确核对不能用于另一实验。")
    return {
        "student_claim": {"kind": ref.claim_kind, "text": words, "request_id": ref.request_id,
                          "review_status": "unreviewed", "evidence_kind": "student_process",
                          "revision_count": ref.revision_count, "help_exposed": bool(record.get("answer_exposure"))},
        "exact_check": EXACT_CHECK,
    }


def _resolve_root_context(workspace, owner: str, ref: LearningContextRef) -> dict:
    with workspace.store.transaction():
        assert_reference_help_allowed(owner, workspace.course)
        run = workspace.get(owner, "lab", ref.record_id)
        from app.tutor.newton_activity import ACTIVITY_ID, KIND
        activity = workspace.store.learning_record(owner, workspace.course_id, KIND, ACTIVITY_ID)
        if activity and (activity.get("run_ref") or {}).get("id") == ref.record_id:
            revealed = activity.get("revealed_step")
            if revealed is not None and not activity.get("answer_exposure") and revealed < len(run["rows"]) - 1:
                raise ValueError("活动仍在逐步观察中；请揭示完轨迹后再引用完整实验。")
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
        if ref.activity_claim:
            snapshot.update(_saved_newton_claim(workspace, owner, run, ref.activity_claim))
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
    problem_text: str | None = Field(default=None, min_length=1, max_length=1000)
    claimed_known: list[int] = Field(default_factory=list, max_length=10)
    condition_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class IntegrationContextRef(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["integration_lab"]
    record_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    schema_version: Literal["numerical-lab-v1"]
    selected_step: int | None = Field(default=None, ge=0, le=100)


class CodeContextRef(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["code_static"]
    record_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    code_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    static_rule_version: str | None = Field(default=None, max_length=80)
    selected_finding: int | None = Field(default=None, ge=0, le=29)


class TeachBackContextRef(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["teach_back"]
    record_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    condition_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    graph_revision: str = Field(min_length=1, max_length=160)
    condition_id: str = Field(min_length=1, max_length=100)


ReferenceContext = Annotated[LearningContextRef | LinearContextRef | IntegrationContextRef | ReadingContextRef | CodeContextRef | TeachBackContextRef, Field(discriminator="kind")]


def _bounded(snapshot):
    if len(json.dumps(snapshot,ensure_ascii=False,allow_nan=False).encode())>8192:
        raise ValueError("引用超出8KiB预算，请选择较短范围；必要条件未被截断。")
    return snapshot


def resolve_learning_context(workspace,owner:str,ref:ReferenceContext) -> dict:
    if ref.kind=="root_lab":return _resolve_root_context(workspace,owner,ref)
    with workspace.store.transaction():
        assert_reference_help_allowed(owner,workspace.course)
        common={"version":"learning-context-v1","ref":ref.model_dump(),"evidence_kind":"reference_help","independent_success":False}
        if ref.kind == "teach_back":
            from app.tutor.learning_workspace import digest
            saved = workspace.get(owner, "teach_back", ref.record_id)
            unit = next((item for item in workspace.reading_units() if item["id"] == saved.get("unit_id")), None)
            if (not unit or saved.get("evidence_version") != "teachback-evidence-v1"
                    or saved.get("source_hash") != ref.source_hash or unit["source_hash"] != ref.source_hash
                    or saved.get("condition_hash") != ref.condition_hash
                    or digest(unit["conditions"]) != ref.condition_hash
                    or saved.get("graph_revision") != ref.graph_revision
                    or unit["graph_revision"] != ref.graph_revision):
                raise ValueError("讲回来源或条件版本已变化，请回原记录核对。")
            condition = next((row for row in saved.get("conditions", [])
                              if row.get("condition_id") == ref.condition_id), None)
            if not condition or condition["condition"] not in unit["conditions"]:
                raise ValueError("选中的讲回条件已变化，请重新选择。")
            return _bounded({**common, "title": "已保存讲回 · 条件追问", "unit_id": saved["unit_id"],
                "content_review_status": saved["content_review_status"],
                "source_quote": saved["source_quote"], "student_text": saved["text"],
                "condition": condition, "model_status": saved["model_status"],
                "parent_id": saved.get("parent_id"), "scope": "selected_condition_only_unverified_no_mastery"})
        if ref.kind=='code_static':
            from app.tutor.learning_workspace import digest
            from app.tutor.learning_extensions import ASSIGNMENT_ID
            saved=workspace.get(owner,'code_submission',ref.record_id)
            code=saved.get('code')
            if not isinstance(code,str) or saved.get('code_hash')!=ref.code_hash or digest(code)!=ref.code_hash:
                raise ValueError('已保存代码版本不符，请重新打开。')
            if saved.get('assignment_id')!=ASSIGNMENT_ID or saved.get('static_rule_version')!=ref.static_rule_version or saved.get('code_executed') is not False:
                raise ValueError('作业或静态规则范围不可确认。')
            findings=saved.get('findings')
            if not isinstance(findings,list) or len(findings)>30:raise ValueError('静态提示记录不符。')
            finding=None
            lines=code.split('\n');start=0;end=len(lines)
            if ref.selected_finding is not None:
                if ref.selected_finding>=len(findings):raise ValueError('选中的静态提示不存在。')
                finding=findings[ref.selected_finding]
                if not isinstance(finding,dict) or not isinstance(finding.get('message'),str) or not isinstance(finding.get('kind'),str):raise ValueError('静态提示内容不可确认。')
                line=finding.get('line')
                if line is not None:
                    if type(line) is not int or not 1<=line<=len(lines):raise ValueError('静态提示行号不符。')
                    start=max(0,line-4);end=min(len(lines),line+3)
            return _bounded({**common,'title':'已保存代码的静态提示','assignment_id':saved['assignment_id'],
                'static_rule_version':saved.get('static_rule_version') or 'legacy_unversioned','finding':finding,
                'code_excerpt':'\n'.join(lines[start:end]),'start_line':start+1,'end_line':end,'total_lines':len(lines),
                'previous_id':saved.get('previous_id'),'code_executed':False,'manual_trace_is_program_output':False,
                'scope':'static_hint_only_not_algorithm_correctness'})
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
            snapshot={**common,"title":title,"source_kind":source_kind,
                      "content_review_status":unit["review_status"] if unit else "uploaded_unreviewed",
                      "citation":citation}
            if ref.problem_text is not None or ref.claimed_known or ref.condition_hash is not None:
                if not unit or not ref.problem_text or not ref.problem_text.strip() or ref.condition_hash != unit["condition_hash"]:
                    raise ValueError("当前来源没有可绑定的条件卡，或条件卡版本已变化。")
                indices=ref.claimed_known
                if len(indices)!=len(set(indices)) or any(index<0 or index>=len(unit["conditions"]) for index in indices):
                    raise ValueError("所选条件编号不可确认。")
                conditions=[{"index":index,"condition":condition,
                             "status":"student_reported_known_unverified" if index in indices else "unknown"}
                            for index,condition in enumerate(unit["conditions"])]
                next_question=(f"题目中哪里给出了“{conditions[0]['condition']}”的依据？" if len(indices)==len(conditions) else
                               f"题目是否给出“{next(row['condition'] for row in conditions if row['status']=='unknown')}”？请指出原句或说明仍未知。")
                snapshot["condition_review"]={"card_hash":unit["condition_hash"],"card_status":unit["review_status"],
                    "problem_text":ref.problem_text,"conditions":conditions,"next_question":next_question,
                    "scope":"student_marked_premises_not_mathematical_verification","verified":False}
            return _bounded(snapshot)
        from app.math_tools.numerical_lab import LinearTask, IntegrationTask, linear_reference
        run=workspace.get(owner,'numerical_lab',ref.record_id)
        if run.get('source_hash')!=ref.source_hash or run.get('schema_version')!=ref.schema_version:
            raise ValueError("实验版本不符，请重新打开已保存实验。")
        task=(IntegrationTask if ref.kind=='integration_lab' else LinearTask).model_validate(run.get('task'))
        rows=run.get('rows')
        if not isinstance(rows,list) or not 1<=len(rows)<=task.limit+1 or run.get('independent_success') is not False:
            raise ValueError("保存记录范围不可确认，请重新运行。")
        finite=lambda n:type(n) in {int,float} and math.isfinite(n) and abs(n)<=1e100
        if ref.kind=='integration_lab':
            if run.get('evidence_scope')!='quadrature_error_estimate' or not run.get('conditions') or not isinstance(run.get('stop_detail'),str):
                raise ValueError('积分估计的条件与停止范围缺失。')
            if not all(isinstance(x,str) for x in run['conditions']):raise ValueError('积分条件记录不符。')
            work=0
            for i,row in enumerate(rows):
                if not isinstance(row,dict) or type(row.get('k')) is not int or row['k']!=i or not finite(row.get('value')):
                    raise ValueError('积分细分行或近似值不可确认。')
                if type(row.get('work')) is not int or not work<=row['work']<=8193:raise ValueError('函数求值成本不可确认。')
                work=row['work']
                if any(row.get(k) is not None for k in ('vector','residual','error_bound')):raise ValueError('不能将积分估计混同残差或严格误差界。')
                for key in ('step','error_estimate'):
                    if row.get(key) is not None and (not finite(row[key]) or row[key]<0):raise ValueError('积分误差估计不可确认。')
                if task.method!='adaptive_simpson':
                    if type(row.get('intervals')) is not int or row['intervals']!=task.intervals*2**i or row['intervals']>4096:
                        raise ValueError('均匀细分分段记录不符。')
                    if i>0 and row.get('error_estimate') is None:raise ValueError('后续积分估计缺失。')
                elif row.get('error_estimate') is None:raise ValueError('自适应积分估计缺失。')
            if ref.selected_step is not None and ref.selected_step>=len(rows):raise ValueError('所选细分不存在。')
            selected=set(range(min(3,len(rows))))|set(range(max(0,len(rows)-3),len(rows)))
            if ref.selected_step is not None:selected.update(range(max(0,ref.selected_step-2),min(len(rows),ref.selected_step+3)))
            return _bounded({**common,'title':'数值积分参考实验','task':task.model_dump(),
                'rows':[{k:row[k] for k in ('k','value','step','error_estimate','work','intervals') if k in row} for i,row in enumerate(rows) if i in selected],
                'conditions':run['conditions'],'evidence_scope':run['evidence_scope'],'stop_detail':run['stop_detail'],
                'estimate_is_bound':False,'total_rows':len(rows),'omitted_rows':len(rows)-len(selected)})
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
        # A saved trajectory is reference help, but its mathematical fields must
        # still match the saved task before they enter a student-claim discussion.
        recalculated=linear_reference(task)
        if (len(recalculated['rows'])!=len(rows) or run.get('status')!=recalculated['status']
                or run.get('condition_sufficient')!=recalculated['condition_sufficient']):
            raise ValueError('线性实验计算版本不可确认，请重新运行。')
        for actual, expected in zip(rows,recalculated['rows']):
            if actual['work']!=expected['work']:
                raise ValueError('线性实验轨迹与参数不一致，请重新运行。')
            for key in ('vector','residual','step','error_bound'):
                left,right=actual.get(key),expected[key]
                if isinstance(right,list):
                    matches=isinstance(left,list) and len(left)==len(right) and all(
                        math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12) for a,b in zip(left,right))
                else:
                    matches=(left is None and right is None) or (finite(left) and right is not None
                             and math.isclose(left,right,rel_tol=1e-12,abs_tol=1e-12))
                if not matches:raise ValueError('线性实验轨迹与参数不一致，请重新运行。')
        selected=set(range(min(3,len(rows))))|set(range(max(0,len(rows)-3),len(rows)))
        if ref.selected_step is not None:selected.update(range(max(0,ref.selected_step-2),min(len(rows),ref.selected_step+3)))
        conditions=run.get('conditions');scope=run.get('evidence_scope');stop=run.get('stop_detail')
        if (conditions!=recalculated['conditions'] or scope!='floating_point_residual'
                or stop!=recalculated['stop_detail']):
            raise ValueError('保存的条件与停止范围缺失。')
        checked_index=ref.selected_step if ref.selected_step is not None else len(rows)-1
        checked=recalculated['rows'][checked_index]
        linear_check={"scope":"saved_linear_iteration_floating_point","method":task.method,
            "checked_step":checked_index,"expected_vector":checked['vector'],
            "residual_infinity":checked['residual'],"condition_sufficient":recalculated['condition_sufficient'],
            "error_bound":checked['error_bound'],"error_bound_includes_roundoff":False,
            "unknown_reason":None if recalculated['condition_sufficient'] else
                "未证严格行对角占优；不能仅凭这条充分条件判断收敛，也不能从残差直接推出同数值的解误差。"}
        return _bounded({**common,"title":"线性方程组参考实验","task":task.model_dump(),
            "rows":[{k:row[k] for k in ('k','vector','residual','step','error_bound','work')} for i,row in enumerate(rows) if i in selected],
            "conditions":conditions,"evidence_scope":scope,"stop_detail":stop,"linear_check":linear_check,
            "total_rows":len(rows),"omitted_rows":len(rows)-len(selected)})
