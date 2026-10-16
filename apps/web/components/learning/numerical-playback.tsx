"use client";
import {useEffect, useState} from "react";
import type {NumericalRun} from "@/lib/numerical-lab";

const format = (value: number | null) => value === null ? "—" : value.toExponential(5);

export function NumericalPlayback({run, comparison, onDiscuss, initialStep=0}: {run: NumericalRun; comparison?: NumericalRun; onDiscuss?:(step:number)=>void; initialStep?:number}) {
  const [step, setStep] = useState(()=>Number.isInteger(initialStep)&&initialStep>=0&&initialStep<run.rows.length?initialStep:0);
  const [playing, setPlaying] = useState(false);
  const last = run.rows.length - 1;
  useEffect(() => {
    if (!playing || step >= last) return;
    const timer = setTimeout(() => setStep(value => value + 1), 700);
    return () => clearTimeout(timer);
  }, [playing, step, last]);
  const row = run.rows[step];
  if (!row) return null;
  const linear = run.task.domain === "linear_system";
  const metric = (r: NumericalRun["rows"][number]) => linear ? r.residual : r.error_estimate;
  const all = [...run.rows, ...(comparison?.rows ?? [])].map(metric).filter((v): v is number => v !== null);
  const logs = all.map(v => Math.log10(Math.max(v, 1e-16)));
  const low = Math.min(...logs, Math.log10(run.task.tolerance));
  const high = Math.max(...logs, low + 1);
  const maxK = Math.max(last, (comparison?.rows.length ?? 1) - 1, 1);
  const y = (value: number) => 165 - (Math.log10(Math.max(value, 1e-16)) - low) / (high - low) * 135;
  const points = (rows: NumericalRun["rows"]) => rows.filter(r => metric(r) !== null).map(r => `${45+r.k/maxK*530},${y(metric(r)!)}`).join(" ");
  function move(value: number) { setPlaying(false); setStep(value); }
  const quietButton="min-h-11 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] px-4 text-sm transition-colors hover:border-olive-500/50 hover:bg-olive-500/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-olive-600 disabled:opacity-35";
  return <section aria-label="逐步观察数值实验" className="mt-7 overflow-hidden rounded-2xl border border-olive-500/20 bg-[var(--bg-card)] shadow-[0_12px_35px_-30px_rgba(22,29,19,.45)]">
    <div className="flex flex-wrap items-end justify-between gap-3 border-b border-[var(--border-subtle)] px-5 py-5 sm:px-6">
      <div><p className="font-mono text-[11px] tracking-[.2em] text-olive-700 dark:text-olive-300">TRAJECTORY / 逐步回看</p><h3 className="mt-2 font-title text-xl font-semibold">{linear ? "残差如何变化" : "误差估计如何变化"}</h3></div>
      <div className="rounded-xl border border-olive-500/20 bg-olive-500/5 px-4 py-2 text-right"><p className="text-[11px] text-[var(--text-muted)]">当前步骤</p><p className="font-mono text-lg font-semibold tabular-nums text-olive-800 dark:text-olive-200">{String(row.k).padStart(2,"0")} <span className="text-sm font-normal text-[var(--text-muted)]">/ {String(last).padStart(2,"0")}</span></p></div>
    </div>
    <div className="p-4 sm:p-6"><div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] p-3 sm:p-5">
      <svg viewBox="0 0 620 210" role="img" aria-label={`${linear ? "残差" : "误差估计"}的对数趋势，第${step}步`} className="w-full text-olive-700 dark:text-olive-300">
        {[45,90,135].map(gy=><line key={gy} x1="45" x2="575" y1={gy} y2={gy} stroke="currentColor" opacity=".09" strokeDasharray="2 6"/>)}
        <path d="M45 20V175H580" stroke="currentColor" fill="none" opacity=".35"/>
        <line x1="45" x2="575" y1={y(run.task.tolerance)} y2={y(run.task.tolerance)} stroke="currentColor" strokeDasharray="5 5" opacity=".7"/>
        <polyline points={points(run.rows)} fill="none" stroke="currentColor" opacity=".18" strokeWidth="2"/>
        <polyline points={points(run.rows.slice(0, step+1))} fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"/>
        {metric(row)!==null&&<circle cx={45+row.k/maxK*530} cy={y(metric(row)!)} r="5" fill="currentColor"/>}
        {comparison && <polyline points={points(comparison.rows)} fill="none" stroke="currentColor" strokeDasharray="6 4" strokeWidth="2" className="text-cinnabar-600 dark:text-cinnabar-300"/>}
        <text x="46" y="199" fill="currentColor" fontSize="12">k=0</text><text x="542" y="199" fill="currentColor" fontSize="12">k={maxK}</text>
      </svg>
      <div className="flex flex-wrap gap-x-5 gap-y-1 border-t border-[var(--border-subtle)] pt-3 text-xs text-[var(--text-secondary)]"><span>实线 · 已回看的步骤</span><span>虚线 · 设定阈值</span>{comparison&&<span>朱砂虚线 · 对照实验</span>}</div>
    </div>
    <p className="mt-3 text-xs leading-6 text-[var(--text-secondary)]">纵轴为对数尺度，零值绘于 10⁻¹⁶。淡线展示完整参考计算；步数不代表相同成本，趋势也不替代条件判断。</p>
    <label className="mt-5 block text-sm font-medium" htmlFor="numerical-step">选择观察步骤 <span className="font-mono text-olive-700 dark:text-olive-300">k = {row.k}</span></label>
    <input id="numerical-step" type="range" min={0} max={Math.max(last, 1)} step={1} value={step} disabled={last === 0} onChange={e => move(Number(e.target.value))} className="mt-1 h-12 w-full accent-olive-700"/>
    <div className="flex flex-wrap items-center gap-2"><button type="button" className={quietButton} disabled={step === 0} onClick={() => move(step-1)}>上一步</button><button type="button" className="min-h-11 rounded-lg bg-olive-700 px-5 text-sm font-medium text-paper-50 hover:bg-olive-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-olive-600 disabled:opacity-40" disabled={last === 0} onClick={() => {if (playing && step < last) setPlaying(false); else {if (step === last) setStep(0); setPlaying(true);}}}>{playing && step < last ? "暂停" : "播放迭代"}</button><button type="button" className={quietButton} disabled={step === last} onClick={() => move(step+1)}>下一步</button>{onDiscuss&&<button type="button" className="ml-auto min-h-11 text-sm text-olive-700 underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-olive-600 dark:text-olive-300" onClick={()=>onDiscuss(step)}>和小珞讨论这一步 →</button>}</div>
    <dl className="mt-6 grid gap-3 sm:grid-cols-2"><div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] p-4 sm:col-span-2"><dt className="text-xs text-[var(--text-muted)]">{linear ? "近似解向量" : "积分近似值"}</dt><dd className="mt-2 break-all font-mono text-xl tabular-nums">{row.vector ? `[${row.vector.map(v => v.toPrecision(7)).join(", ")}]` : row.value?.toPrecision(10)}</dd></div><div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] p-4"><dt className="text-xs text-[var(--text-muted)]">{linear ? "绝对残差" : "误差估计"}</dt><dd className="mt-2 font-mono text-base tabular-nums">{format(metric(row))}</dd></div><div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] p-4"><dt className="text-xs text-[var(--text-muted)]">{linear ? "相邻步差" : "函数求值次数"}</dt><dd className="mt-2 font-mono text-base tabular-nums">{linear ? format(row.step) : row.work}</dd></div>{row.error_bound !== null && <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] p-4 sm:col-span-2"><dt className="text-xs text-[var(--text-muted)]">解误差界公式的浮点值（不含舍入误差）</dt><dd className="mt-2 font-mono text-base tabular-nums">{format(row.error_bound)}</dd></div>}</dl></div>
  </section>;
}
