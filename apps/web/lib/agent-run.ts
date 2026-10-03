export type RunStatus = "running" | "succeeded" | "clarification" | "failed" | "cancelled" | "interrupted";
export const phaseLabels = {routing:"确认任务",vision:"核对图片",context:"读取学习上下文",review:"核对学习步骤",generation:"组织回答",model:"生成候选回答",tool:"计算工具",guard:"检查交付表述",delivery:"回答交付"};
export const stepLabels = {started:"开始",succeeded:"完成",degraded:"未充分确认",failed:"未完成",cancelled:"已停止",clarification:"等待补充"};
export const runLabels: Record<RunStatus,string> = {running:"正在进行",succeeded:"回答已保存",clarification:"等待你补充",failed:"本轮未完成",cancelled:"本轮已停止",interrupted:"本轮中断"};
export type AgentRun = {
  version:"run-v1"; scope:"execution_only"; run_id:string; status:RunStatus; seq:number;
  steps:Array<{seq:number;phase:keyof typeof phaseLabels;status:keyof typeof stepLabels;duration_ms?:number;round?:number}>;
  truncated:boolean; message_id?:string|null; created_at?:string; updated_at?:string;
  prompt_version?:string; guard_version?:string; usage:null; model_alias:string|null; parent_run_id?:string|null;
};
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
    steps.push({seq:step.seq as number,phase:step.phase as keyof typeof phaseLabels,status:step.status as keyof typeof stepLabels,
      ...(typeof step.duration_ms==="number" && Number.isFinite(step.duration_ms) && step.duration_ms>=0 ? {duration_ms:step.duration_ms}:{}),
      ...(typeof step.round==="number" && Number.isInteger(step.round) && step.round>=0 && step.round<=4 ? {round:step.round}:{})});
  }
  return {version:"run-v1",scope:"execution_only",run_id:run.run_id,status:run.status as RunStatus,seq:run.seq as number,
    steps,truncated:run.truncated===true,message_id:typeof run.message_id==="string"?run.message_id:null,
    created_at:typeof run.created_at==="string"?run.created_at:undefined,usage:null,
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
