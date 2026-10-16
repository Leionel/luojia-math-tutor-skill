export type RunStatus = "running" | "succeeded" | "clarification" | "failed" | "cancelled" | "interrupted";
export const phaseLabels = {routing:"确认任务",vision:"核对图片",context:"读取学习上下文",review:"核对学习步骤",generation:"组织回答",model:"生成候选回答",tool:"计算工具",guard:"检查交付表述",delivery:"回答交付"};
export const stepLabels = {started:"开始",succeeded:"完成",degraded:"未充分确认",failed:"未完成",cancelled:"已停止",clarification:"等待补充"};
export const runLabels: Record<RunStatus,string> = {running:"正在进行",succeeded:"回答已保存",clarification:"等待你补充",failed:"本轮未完成",cancelled:"本轮已停止",interrupted:"本轮中断"};
export type RunUsage = {version:"usage-v1";model_attempts:number;model_requests:number;reported_requests:number;coverage:"complete"|"partial";known_tokens:{prompt_tokens:number;completion_tokens:number;total_tokens:number};cost:{amount:string;currency:"USD"|"CNY";price_version:string;scope:"reported_plain_tokens_estimate"}|null;cost_status:"complete"|"partial"|"unavailable"};
export const toolLabels = {numerical_run:"数值参考计算",math_differentiate:"单变量求导"};
export const modelStageLabels = {generation:"组织回答",routing:"确认任务",review:"审查推导",guard_repair:"修复交付表述",vision:"解析图片",embedding:"检索向量"};
export function parseRunUsage(value:unknown):RunUsage|null {
  if(!value||typeof value!=="object")return null;
  const u=value as Record<string,unknown>, t=u.known_tokens as Record<string,unknown>|undefined;
  const count=(v:unknown)=>typeof v==="number"&&Number.isSafeInteger(v)&&v>=0&&v<=10_000_000_000;
  if(u.version!=="usage-v1"||!count(u.model_attempts)||!count(u.model_requests)||!count(u.reported_requests)||
    (u.reported_requests as number)>(u.model_requests as number)||(u.model_requests as number)>(u.model_attempts as number)||
    (u.coverage==="complete"&&u.reported_requests!==u.model_requests)||
    !["complete","partial"].includes(String(u.coverage))||!t||![t.prompt_tokens,t.completion_tokens,t.total_tokens].every(count)||
    (t.prompt_tokens as number)+(t.completion_tokens as number)!==t.total_tokens)return null;
  let cost:RunUsage["cost"]=null;
  const c=u.cost as Record<string,unknown>|null;
  if(c&&typeof c.amount==="string"&&/^\d{1,10}(?:\.\d{1,8})?$/.test(c.amount)&&["USD","CNY"].includes(String(c.currency))&&
     typeof c.price_version==="string"&&/^\d{4}-\d{2}-\d{2}(?:-v\d{1,3})?$/.test(c.price_version)&&c.scope==="reported_plain_tokens_estimate")
    cost={amount:c.amount,currency:c.currency as "USD"|"CNY",price_version:c.price_version,scope:"reported_plain_tokens_estimate"};
  return {version:"usage-v1",model_attempts:u.model_attempts as number,model_requests:u.model_requests as number,reported_requests:u.reported_requests as number,
    coverage:u.coverage as RunUsage["coverage"],known_tokens:{prompt_tokens:t.prompt_tokens as number,completion_tokens:t.completion_tokens as number,total_tokens:t.total_tokens as number},cost,
    cost_status:cost&&(u.cost_status==="complete"||u.cost_status==="partial")?u.cost_status:"unavailable"};
}
export type AgentRun = {
  version:"run-v1"; scope:"execution_only"; run_id:string; status:RunStatus; seq:number;
  steps:Array<{seq:number;phase:keyof typeof phaseLabels;status:keyof typeof stepLabels;duration_ms?:number;round?:number;span_id?:string;parent_id?:string;call_id?:string;tool_call_id?:string;tool_name?:keyof typeof toolLabels;model_stage?:keyof typeof modelStageLabels;first_content_ms?:number;request_sent?:boolean;error_code?:string}>;
  truncated:boolean; message_id?:string|null; created_at?:string; updated_at?:string;
  prompt_version?:string; guard_version?:string; usage:RunUsage|null; model_alias:string|null; parent_run_id?:string|null;
};
export function receiptSteps(steps:AgentRun["steps"]):AgentRun["steps"] {
  const lastSpanSeq=new Map(steps.filter(step=>step.span_id).map(step=>[step.span_id,step.seq]));
  return steps.filter((step,index)=>step.span_id?lastSpanSeq.get(step.span_id)===step.seq:
    step.status!=="started"||!steps.slice(index+1).some(later=>!later.span_id&&later.phase===step.phase&&later.round===step.round&&later.status!=="started"));
}
export function parseAgentRun(value: unknown): AgentRun | undefined {
  if (!value || typeof value!=="object") return;
  const run = value as Record<string,unknown>;
  if (run.version!=="run-v1" || run.scope!=="execution_only" || typeof run.run_id!=="string" ||
      !/^[a-f0-9-]{36}$/.test(run.run_id) || typeof run.status!=="string" || !Object.hasOwn(runLabels,run.status) ||
      !Number.isInteger(run.seq) || (run.seq as number)<0 || !Array.isArray(run.steps) || run.steps.length>64) return;
  const steps:AgentRun["steps"]=[];
  for (const value of run.steps) {
    if (!value || typeof value!=="object") return;
    const step=value as Record<string,unknown>;
    if (!Number.isInteger(step.seq) || (step.seq as number)<1 || (step.seq as number)>(run.seq as number) ||
        typeof step.phase!=="string" || !Object.hasOwn(phaseLabels,step.phase) ||
        typeof step.status!=="string" || !Object.hasOwn(stepLabels,step.status) ||
        (steps.length && (step.seq as number)<=steps[steps.length-1].seq)) return;
    const extra:Partial<AgentRun["steps"][number]>={};
    for(const k of ["span_id","call_id","tool_call_id"] as const)if(typeof step[k]==="string"&&/^[a-f0-9]{32}$/.test(step[k]))extra[k]=step[k];
    if(typeof step.parent_id==="string"&&/^[a-f0-9-]{32,36}$/.test(step.parent_id))extra.parent_id=step.parent_id;
    if(typeof step.tool_name==="string"&&Object.hasOwn(toolLabels,step.tool_name))extra.tool_name=step.tool_name as keyof typeof toolLabels;
    if(typeof step.model_stage==="string"&&Object.hasOwn(modelStageLabels,step.model_stage))extra.model_stage=step.model_stage as keyof typeof modelStageLabels;
    if(typeof step.first_content_ms==="number"&&Number.isFinite(step.first_content_ms)&&step.first_content_ms>=0)extra.first_content_ms=step.first_content_ms;
    if(typeof step.request_sent==="boolean")extra.request_sent=step.request_sent;
    if(typeof step.error_code==="string"&&/^(?:model|tool|call)_[a-z_]{1,50}$/.test(step.error_code))extra.error_code=step.error_code;
    steps.push({...extra,seq:step.seq as number,phase:step.phase as keyof typeof phaseLabels,status:step.status as keyof typeof stepLabels,
      ...(typeof step.duration_ms==="number" && Number.isFinite(step.duration_ms) && step.duration_ms>=0 ? {duration_ms:step.duration_ms}:{}),
      ...(typeof step.round==="number" && Number.isInteger(step.round) && step.round>=0 && step.round<=4 ? {round:step.round}:{})});
  }
  return {version:"run-v1",scope:"execution_only",run_id:run.run_id,status:run.status as RunStatus,seq:run.seq as number,
    steps,truncated:run.truncated===true,message_id:typeof run.message_id==="string"?run.message_id:null,
    created_at:typeof run.created_at==="string"?run.created_at:undefined,usage:parseRunUsage(run.usage),
    model_alias:typeof run.model_alias==="string" && /^[a-z0-9.-]{1,64}$/.test(run.model_alias) ? run.model_alias:null,
    parent_run_id:typeof run.parent_run_id==="string" && /^[a-f0-9-]{36}$/.test(run.parent_run_id) ? run.parent_run_id:null};
}
export function mergeAgentRun(current:unknown,next:unknown):AgentRun|undefined {
  const incoming=parseAgentRun(next), previous=parseAgentRun(current);
  if (!incoming) return previous;
  if (!previous || previous.run_id!==incoming.run_id) return incoming;
  if (previous.status!=="running" || incoming.seq<previous.seq) return previous;
  return incoming;
}
