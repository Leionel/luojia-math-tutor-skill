import { parseAgentRun, receiptSteps, phaseLabels, stepLabels, runLabels, toolLabels, modelStageLabels } from "@/lib/agent-run";

export function AgentRunReceipt({value,disconnected=false}:{value:unknown;disconnected?:boolean}) {
  const run = parseAgentRun(value);
  if (!run) return null;
  const steps=receiptSteps(run.steps);
  return <details className="my-3 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] text-[var(--text-secondary)]">
    <summary className="min-h-12 cursor-pointer px-3 py-3 text-base sm:text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-olive-600">
      本轮过程 · {disconnected && run.status==="running" ? "连接已结束，状态待同步" : runLabels[run.status]}
    </summary>
    <div className="px-3 pb-3 text-base sm:text-sm leading-relaxed">
      <p className="mb-2">记录任务执行状态。数学结论是否得到验证，请看回答中的核验标注。</p>
      <ol className="space-y-1.5">
        {steps.map((step,index)=><li key={step.seq} className={`flex flex-wrap items-baseline justify-between gap-x-3 ${step.tool_name?"border-l-2 border-olive-500 pl-2":""}`}>
          <span>{index+1}. {step.tool_name?toolLabels[step.tool_name]:step.model_stage?`模型 · ${modelStageLabels[step.model_stage]}`:phaseLabels[step.phase]}{step.round!==undefined ? `（第 ${step.round+1} 轮）` : ""}</span>
          <span className="text-[var(--text-muted)]">{stepLabels[step.status]}{step.duration_ms!==undefined ? ` · ${(step.duration_ms/1000).toFixed(1)} 秒` : ""}{step.first_content_ms!==undefined?` · 首个正文片段 ${(step.first_content_ms/1000).toFixed(2)} 秒`:""}{step.error_code?` · ${step.error_code}`:""}</span>
        </li>)}
      </ol>
      {run.usage && <div className="mt-3 space-y-1 border-t border-[var(--border-subtle)] pt-3">
        <div className="mb-2 grid grid-cols-2 gap-2">
          <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-secondary)] px-3 py-2"><p className="text-xs text-[var(--text-muted)]">模型请求</p><p className="font-mono text-lg tabular-nums text-[var(--text-primary)]">{run.usage.model_requests}<span className="ml-1 text-xs">次</span></p></div>
          <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-secondary)] px-3 py-2"><p className="text-xs text-[var(--text-muted)]">用量已报告</p><p className="font-mono text-lg tabular-nums text-[var(--text-primary)]">{run.usage.reported_requests}<span className="mx-1 text-xs">/</span>{run.usage.model_requests}<span className="ml-1 text-xs">次</span></p></div>
        </div>
        <p>{run.usage.coverage==="partial"?"已知部分合计":"已报告用量合计"} {run.usage.known_tokens.total_tokens} tokens（输入 {run.usage.known_tokens.prompt_tokens} / 输出 {run.usage.known_tokens.completion_tokens}）</p>
        <p>{run.usage.cost?`费用估算 ${run.usage.cost.currency} ${run.usage.cost.amount} · 价格版本 ${run.usage.cost.price_version}${run.usage.cost_status==="partial"?" · 仅已知部分":""}`:"费用未知：尚无可用的完整计价依据。"}</p>
        {run.usage.coverage==="partial" && <p>缺失用量没有按零补齐；失败和修复请求也计入调用次数。</p>}
      </div>}
      {run.truncated && <p className="mt-2">过程较长，仅展示前 64 个事件。</p>}
      {run.status==="interrupted" && <p className="mt-2">连接中断后没有收到完成记录；重新提问会开始新的一轮。</p>}
      <p className="mt-3 break-all font-mono text-xs text-[var(--text-muted)]">记录编号 {run.run_id}</p>
    </div>
  </details>;
}
