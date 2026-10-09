import type {LabRun,NewtonActivityState,RootParameters,TeachBack} from "./learning-api";
import type {NumericalRun,LinearTask,IntegrationTask,NumericalRow} from "./numerical-lab";
export type NewtonActivityClaimRef={activity_id:"newton-cycle-v1";activity_version:"newton-participation-v1";claim_kind:"explanation"|"revision";request_id:string;revision_count:number};
export type RootContextRef={kind:"root_lab";record_id:string;input_hash:string;runner_version:string;graph_revision:string;selected_step:number|null;activity_claim?:NewtonActivityClaimRef};
export type LinearContextRef={kind:"linear_lab";record_id:string;source_hash:string;schema_version:"numerical-lab-v1";selected_step:number|null};
export type IntegrationContextRef=Omit<LinearContextRef,"kind">&{kind:"integration_lab"};
export type CodeContextRef={kind:"code_static";record_id:string;code_hash:string;static_rule_version:string|null;selected_finding:number|null};
export type ReadingContextRef={kind:"reading";source_id:string;source_hash:string;section_id:string|null;start:number;end:number;graph_revision:string|null;problem_text?:string|null;claimed_known?:number[];condition_hash?:string|null};
export type TeachBackContextRef={kind:"teach_back";record_id:string;source_hash:string;condition_hash:string;graph_revision:string;condition_id:string};
export type LearningContextRef=RootContextRef|LinearContextRef|IntegrationContextRef|ReadingContextRef|CodeContextRef|TeachBackContextRef;
type BaseSnapshot={version:"learning-context-v1";title:string;evidence_kind:"reference_help";independent_success:false};
export type RootSnapshot=BaseSnapshot&{ref:RootContextRef;parameters:RootParameters;rows:LabRun["rows"];total_rows:number;omitted_rows:number;stop_detail:string;diagnosis_summary:string;max_iterations:number;iteration_budget_source:"saved"|"legacy_default";student_claim?:{kind:"explanation"|"revision";text:string;request_id:string;review_status:"unreviewed";evidence_kind:"student_process";revision_count:number;help_exposed:boolean};exact_check?:{scope:string;steps:string[];conclusion:string}};
export type LinearSnapshot=BaseSnapshot&{ref:LinearContextRef;task:LinearTask;rows:NumericalRow[];total_rows:number;omitted_rows:number;stop_detail:string;conditions:string[];evidence_scope:string;linear_check:{scope:"saved_linear_iteration_floating_point";method:"jacobi"|"gauss_seidel";checked_step:number;expected_vector:number[];residual_infinity:number;condition_sufficient:boolean;error_bound:number|null;error_bound_includes_roundoff:false;unknown_reason:string|null}};
export type IntegrationSnapshot=Omit<LinearSnapshot,"ref"|"task"|"linear_check">&{ref:IntegrationContextRef;task:IntegrationTask;estimate_is_bound:false};
export type ReadingSnapshot=BaseSnapshot&{ref:ReadingContextRef;source_kind:string;content_review_status:string;citation:{quote:string;start:number;end:number;conditions:string[]};condition_review?:{card_hash:string;card_status:string;problem_text:string;conditions:{index:number;condition:string;status:"student_reported_known_unverified"|"unknown"}[];next_question:string;scope:string;verified:false}};
export type CodeSnapshot=BaseSnapshot&{ref:CodeContextRef;assignment_id:string;static_rule_version:string;finding:{kind:string;line:number|null;message:string}|null;code_excerpt:string;start_line:number;end_line:number;total_lines:number;code_executed:false;manual_trace_is_program_output:false};
export type TeachBackSnapshot=BaseSnapshot&{ref:TeachBackContextRef;unit_id:string;content_review_status:string;source_quote:string;student_text:string;condition:TeachBack["conditions"][number];model_status:string;parent_id:string|null;scope:string};
export type LearningTaskSnapshot=RootSnapshot|LinearSnapshot|IntegrationSnapshot|ReadingSnapshot|CodeSnapshot|TeachBackSnapshot;
export function rootContextRef(run:LabRun,step:number|null=null):RootContextRef {
 if(!/^[a-f0-9]{64}$/.test(run.input_hash)||!run.runner_version||!run.graph_revision)throw Error("实验缺少版本信息，请重新运行后讨论。");
 checkStep(step,run.rows.length);
 return {kind:"root_lab",record_id:run.id,input_hash:run.input_hash,runner_version:run.runner_version,graph_revision:run.graph_revision,selected_step:step};
}
export function newtonActivityContextRef(activity:NewtonActivityState,kind:"explanation"|"revision",requestId:string):RootContextRef {
 const run=activity.run;
 if(!run||!activity.context_current||activity.id!=="newton-cycle-v1"||activity.version!=="newton-participation-v1")throw Error("活动或计算版本已变化，请重新打开后选择原话。");
 const claim=kind==="explanation"?activity.explanation:activity.revisions.find(item=>item.request_id===requestId);
 if(!claim||claim.request_id!==requestId||claim.run_id!==run.id||claim.input_hash!==run.input_hash)throw Error("所选解释或修订不可确认。");
 return {...rootContextRef(run,run.rows.length-1),activity_claim:{activity_id:activity.id,activity_version:activity.version,claim_kind:kind,request_id:requestId,revision_count:activity.revisions.length}};
}
function checkStep(step:number|null,length:number){if(step!==null&&(!Number.isInteger(step)||step<0||step>=length))throw Error("所选迭代步骤不存在。");}
export function linearContextRef(run:NumericalRun,step:number|null=null):LinearContextRef {
 if(run.task.domain!=="linear_system"||run.schema_version!=="numerical-lab-v1"||!/^[a-f0-9]{64}$/.test(run.source_hash))throw Error("实验缺少兼容版本，请重新运行后讨论。");
 checkStep(step,run.rows.length);return {kind:"linear_lab",record_id:run.id,source_hash:run.source_hash,schema_version:"numerical-lab-v1",selected_step:step};
}
export function selectionRange(text:string,start:number,end:number){return {start:Array.from(text.slice(0,start)).length,end:Array.from(text.slice(0,end)).length};}
export function referenceHref(s:LearningTaskSnapshot){const r=s.ref;return r.kind==="teach_back"?`/teach-back?id=${encodeURIComponent(r.record_id)}&condition=${encodeURIComponent(r.condition_id)}`:r.kind==="code_static"?`/code-workshop?id=${encodeURIComponent(r.record_id)}`:r.kind==="reading"?`/reading?${r.section_id===null?`unit=${encodeURIComponent(r.source_id)}`:`document=${encodeURIComponent(r.source_id)}&section=${encodeURIComponent(r.section_id)}`}${r.problem_text?"#reading-discussion":""}`:r.kind==="root_lab"&&r.activity_claim?`/lab?activity=newton-cycle-v1&run=${encodeURIComponent(r.record_id)}&claim=${encodeURIComponent(r.activity_claim.request_id)}${r.selected_step===null?"":`&step=${r.selected_step}`}#newton-activity`:`/${r.kind==="root_lab"?"lab":"numerical-lab"}?id=${encodeURIComponent(r.record_id)}${r.selected_step===null?"":`&step=${r.selected_step}`}`;}
export function referenceDescription(s:LearningTaskSnapshot){return "condition" in s?`条件 ${s.condition.condition_id} · ${s.model_status==="model_review"?"模型意见未核验":"待进一步核对"}`:"student_claim" in s&&s.student_claim?`${s.student_claim.kind==="explanation"?"已保存解释":"已保存修订"} · ${s.student_claim.help_exposed?"主动跳过看答案":"未记录主动跳过"} · 尚未经数学审核`:"code_excerpt" in s?`静态规则 ${s.static_rule_version} · 第 ${s.start_line}–${s.end_line} 行 · 代码未执行`:"parameters" in s?`f(x) = ${s.parameters.function} · x₀=${s.parameters.initial_value}`:"task" in s?`${s.task.method} · ${s.task.domain==="linear_system"?`${s.task.matrix.length}阶方程组`:`∫[${s.task.left}, ${s.task.right}] ${s.task.expression} · 误差估计，非严格界`}${s.ref.selected_step===null?"":` · 第 ${s.ref.selected_step} 步`}`:`原文字符 ${s.citation.start}–${s.citation.end} · ${s.citation.quote.slice(0,100)}`;}
export function labChatKey(owner:string,id:string){return `luojia_lab_chat:${owner}:${id}`;}
export function referenceChatKey(owner:string,r:LearningContextRef){return r.kind==="teach_back"?`luojia_reference_chat:${owner}:teach-back:${r.record_id}:${r.condition_id}`:r.kind==="code_static"?`luojia_reference_chat:${owner}:code:${r.record_id}:${r.code_hash}`:r.kind==="root_lab"&&r.activity_claim?`luojia_reference_chat:${owner}:newton-activity:${r.record_id}:${r.activity_claim.request_id}:${r.activity_claim.revision_count}`:r.kind==="root_lab"?labChatKey(owner,r.record_id):(r.kind==="linear_lab"||r.kind==="integration_lab")?`luojia_reference_chat:${owner}:${r.kind==="linear_lab"?"linear":"integration"}:${r.record_id}:${r.source_hash}`:`luojia_reference_chat:${owner}:reading:${r.source_id}:${r.source_hash}:${r.section_id??"course"}${r.problem_text?`:${JSON.stringify([r.start,r.end,r.condition_hash,r.problem_text,r.claimed_known])}`:""}`;}
export function teachBackContextRef(saved:TeachBack,conditionId:string):TeachBackContextRef{
 if(saved.evidence_version!=="teachback-evidence-v1"||!/^[a-f0-9]{64}$/.test(saved.source_hash)||!/^[a-f0-9]{64}$/.test(saved.condition_hash??"")||!saved.graph_revision||!saved.conditions.some(c=>c.condition_id===conditionId))throw Error("讲回来源或条件版本不可确认，请重新打开记录。");
 return {kind:"teach_back",record_id:saved.id,source_hash:saved.source_hash,condition_hash:saved.condition_hash!,graph_revision:saved.graph_revision,condition_id:conditionId};
}
export function studyRequested(message:string){return ["今天学什么","今天的任务","查看当前任务","查看学习计划","继续上次任务","继续学习的任务"].includes(message.trim().replace(/[？?。！!]+$/u,"").trim());}
/** Restore a locator only when its owner-scoped source is still the same version. */
export function restoreReadingReference(raw: string | null, source: Omit<ReadingContextRef, "kind" | "start" | "end" | "problem_text" | "claimed_known">, length: number, conditionCount=0): ReadingContextRef | null {
  if (!raw) return null;
  try {
    const ref = JSON.parse(raw) as ReadingContextRef;
    if (ref.kind !== "reading" || ref.source_id !== source.source_id || ref.source_hash !== source.source_hash || ref.section_id !== source.section_id || ref.graph_revision !== source.graph_revision || !Number.isInteger(ref.start) || !Number.isInteger(ref.end) || ref.start < 0 || ref.end <= ref.start || ref.end > length) return null;
    if(ref.problem_text!==undefined&&ref.problem_text!==null){
      if(!source.condition_hash||ref.condition_hash!==source.condition_hash||ref.problem_text.trim().length===0||ref.problem_text.length>1000||!Array.isArray(ref.claimed_known)||new Set(ref.claimed_known).size!==ref.claimed_known.length||ref.claimed_known.some(i=>!Number.isInteger(i)||i<0||i>=conditionCount))return null;
      return {kind:"reading",...source,start:ref.start,end:ref.end,problem_text:ref.problem_text,claimed_known:ref.claimed_known,condition_hash:source.condition_hash};
    }
    return {kind: "reading", ...source, start: ref.start, end: ref.end};
  } catch { return null; }
}

export function numericalContextRef(run:NumericalRun,step:number|null=null):LinearContextRef|IntegrationContextRef {
 if(run.task.domain==="linear_system")return linearContextRef(run,step);
 if(run.schema_version!=="numerical-lab-v1"||!/^[a-f0-9]{64}$/.test(run.source_hash))throw Error("实验版本不可确认，请重新运行后讨论。");
 checkStep(step,run.rows.length);return {kind:"integration_lab",record_id:run.id,source_hash:run.source_hash,schema_version:"numerical-lab-v1",selected_step:step};
}

export function codeContextRef(saved:{id:string;code_hash:string;static_rule_version?:string;findings:unknown[]},finding:number|null):CodeContextRef {
 if(!/^[a-f0-9]{64}$/.test(saved.code_hash)||finding!==null&&(!Number.isInteger(finding)||finding<0||finding>=saved.findings.length))throw Error("已保存代码或提示版本不可确认。");
 return {kind:"code_static",record_id:saved.id,code_hash:saved.code_hash,static_rule_version:saved.static_rule_version??null,selected_finding:finding};
}

export function verifiedReferenceSession(cached:string|null,items:{id:string;user_id:string}[],owner:string):string|undefined{
 return cached&&items.some(item=>item.id===cached&&item.user_id===owner)?cached:undefined;
}
