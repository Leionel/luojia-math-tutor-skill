"use client";
import {useEffect, useState} from "react";
import type {NumericalRun} from "@/lib/numerical-lab";
import {learningButton} from "./learning-shell";

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
  return <section aria-label="逐步观察数值实验" className="mt-5 rounded-xl bg-[var(--bg-tertiary)] p-4">
    <h3 className="text-lg font-semibold">第 {row.k} 步 · {linear ? "残差变化" : "误差估计变化"}</h3>
    <svg viewBox="0 0 620 200" role="img" aria-label={`${linear ? "残差" : "误差估计"}的对数趋势，第${step}步`} className="mt-4 w-full text-olive-600 dark:text-olive-400">
      <path d="M45 20V175H580" stroke="currentColor" fill="none" opacity=".4"/>
      <line x1="45" x2="575" y1={y(run.task.tolerance)} y2={y(run.task.tolerance)} stroke="currentColor" strokeDasharray="4 4"/>
      <polyline points={points(run.rows)} fill="none" stroke="currentColor" opacity=".2" strokeWidth="2"/>
      <polyline points={points(run.rows.slice(0, step+1))} fill="none" stroke="currentColor" strokeWidth="3"/>
      {comparison && <polyline points={points(comparison.rows)} fill="none" stroke="currentColor" strokeDasharray="6 4" strokeWidth="2" className="text-cinnabar-600 dark:text-cinnabar-300"/>}
      <text x="46" y="195" fill="currentColor" fontSize="13">k=0</text><text x="550" y="195" fill="currentColor" fontSize="13">k={maxK}</text>
    </svg>
    <p className="text-sm leading-6 text-[var(--text-secondary)]">纵轴采用对数尺度，零值绘于 10⁻¹⁶；横向虚线为阈值。{comparison ? "朱红虚线为同一问题的对照。" : "淡线为全部参考步骤。"}步数不是相同计算成本，趋势不替代条件判断。</p>
    <label className="mt-4 block" htmlFor="numerical-step">选择观察步骤</label>
    <input id="numerical-step" type="range" min={0} max={Math.max(last, 1)} step={1} value={step} disabled={last === 0} onChange={e => move(Number(e.target.value))} className="h-12 w-full accent-olive-700"/>
    <div className="flex flex-wrap gap-2"><button className={learningButton} disabled={step === 0} onClick={() => move(step-1)}>上一步</button><button className={learningButton} disabled={last === 0} onClick={() => {if (playing && step < last) setPlaying(false); else {if (step === last) setStep(0); setPlaying(true);}}}>{playing && step < last ? "暂停" : "播放"}</button><button className={learningButton} disabled={step === last} onClick={() => move(step+1)}>下一步</button></div>
    {onDiscuss && <button type="button" className={`${learningButton} mt-3`} onClick={()=>onDiscuss(step)}>讨论第 {row.k} 步</button>}
    <dl className="mt-5 grid grid-cols-2 gap-4 text-base"><div className="col-span-2"><dt>{linear ? "近似解向量" : "积分近似值"}</dt><dd className="mt-1 break-all font-mono">{row.vector ? `[${row.vector.map(v => v.toPrecision(7)).join(", ")}]` : row.value?.toPrecision(10)}</dd></div><div><dt>{linear ? "绝对残差" : "误差估计"}</dt><dd className="mt-1 font-mono">{format(metric(row))}</dd></div><div><dt>{linear ? "相邻步差" : "函数求值次数"}</dt><dd className="mt-1 font-mono">{linear ? format(row.step) : row.work}</dd></div>{row.error_bound !== null && <div className="col-span-2"><dt>解误差界公式的浮点值（不含舍入误差）</dt><dd className="mt-1 font-mono">{format(row.error_bound)}</dd></div>}</dl>
  </section>;
}
