import { parseAgentRun, phaseLabels, stepLabels, runLabels } from "@/lib/agent-run";

export function AgentRunReceipt({value,disconnected=false}:{value:unknown;disconnected?:boolean}) {
  const run = parseAgentRun(value);
  if (!run) return null;
  return <details className="my-3 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] text-[var(--text-secondary)]">
    <summary className="min-h-12 cursor-pointer px-3 py-3 text-base sm:text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-olive-600">
      本轮过程 · {disconnected && run.status==="running" ? "连接已结束，状态待同步" : runLabels[run.status]}
    </summary>
    <div className="px-3 pb-3 text-base sm:text-sm leading-relaxed">
      <p className="mb-2">记录任务执行状态。数学结论是否得到验证，请看回答中的核验标注。</p>
      <ol className="space-y-1.5">
        {run.steps.map(step=><li key={step.seq} className="flex flex-wrap items-baseline justify-between gap-x-3">
          <span>{step.seq}. {phaseLabels[step.phase]}{step.round!==undefined ? `（第 ${step.round+1} 轮）` : ""}</span>
          <span className="text-[var(--text-muted)]">{stepLabels[step.status]}{step.duration_ms!==undefined ? ` · ${(step.duration_ms/1000).toFixed(1)} 秒` : ""}</span>
        </li>)}
      </ol>
      {run.truncated && <p className="mt-2">过程较长，仅展示前 64 个事件。</p>}
      {run.status==="interrupted" && <p className="mt-2">连接中断后没有收到完成记录；重新提问会开始新的一轮。</p>}
      <p className="mt-3 break-all font-mono text-xs text-[var(--text-muted)]">记录编号 {run.run_id}</p>
    </div>
  </details>;
}
