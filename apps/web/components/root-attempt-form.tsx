"use client";
import { useState } from "react";
import type { RootAttemptInput, RootSubmission } from "@/lib/api";

export function RootAttemptForm({ initial, disabled, onSubmit, onClose, instruction }: {
  initial?: Partial<RootSubmission>; disabled: boolean; onSubmit: (submission: RootSubmission) => void;
  onClose: () => void; instruction?: string;
}) {
  const seed = initial?.attempt;
  const [method, setMethod] = useState<RootAttemptInput["method"]>(seed?.method || "newton");
  const [fn, setFn] = useState(seed?.function || "");
  const [iterates, setIterates] = useState(JSON.stringify(seed?.iterates || []));
  const [brackets, setBrackets] = useState(JSON.stringify(seed?.brackets || []));
  const [interval, setInterval] = useState(seed?.interval?.join(",") || "");
  const [phi, setPhi] = useState(seed?.phi || "");
  const [goal, setGoal] = useState<"root_error" | "residual">(seed?.goal || "root_error");
  const [tolerance, setTolerance] = useState(String(seed?.tolerance ?? 1e-6));
  const [stop, setStop] = useState<RootAttemptInput["stop_reason"]>(seed?.stop_reason || "none");
  const [advanced, setAdvanced] = useState(JSON.stringify({variant:seed?.variant || "standard", damping:seed?.damping || 1, multiplicity:seed?.multiplicity || 1, derivative:seed?.derivative || null, update:seed?.update || null}, null, 2));
  const [error, setError] = useState("");
  const probe = !!instruction;
  function submit(event: React.FormEvent) {
    event.preventDefault();
    try {
      const attempt: RootAttemptInput = {...JSON.parse(advanced), method, function:fn.trim(), iterates:JSON.parse(iterates), brackets:JSON.parse(brackets), interval:interval.trim() ? interval.split(",").map(Number) : null, phi:phi.trim() || null, goal, tolerance:Number(tolerance), stop_reason:stop};
      if (!attempt.function || !Array.isArray(attempt.iterates) || !Array.isArray(attempt.brackets) || !Number.isFinite(attempt.tolerance)) throw new Error("请核对函数、JSON 数组与容差。");
      if (attempt.interval && (attempt.interval.length !== 2 || !attempt.interval.every(Number.isFinite))) throw new Error("区间须为两个数，例如 1,2。");
      if (probe && seed) Object.assign(attempt, {method:seed.method,function:seed.function,interval:seed.interval,goal:seed.goal,tolerance:seed.tolerance,variant:seed.variant,initial_value:seed.initial_value,derivative:null,update:null,damping:1,multiplicity:1});
      onSubmit({attempt, attempt_id:crypto.randomUUID(), episode_id:initial?.episode_id});
    } catch (e) { setError(e instanceof Error ? e.message : "输入格式无效。"); }
  }
  const control = "w-full min-w-0 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] px-2 py-2 text-sm";
  return <form onSubmit={submit} className="mx-auto max-w-4xl max-h-[65dvh] overflow-y-auto rounded-xl border border-olive-500/30 bg-[var(--bg-card)] p-4 space-y-3">
    <div className="flex justify-between"><strong>{probe ? "独立探针" : initial?.episode_id ? "修订求根过程" : "提交求根过程"}</strong><button type="button" onClick={onClose}>关闭</button></div>
    {instruction && <p className="text-sm">{instruction} 初值 x₀={seed?.initial_value}。</p>}
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <label>方法<select disabled={probe || !!initial?.episode_id} className={control} value={method} onChange={e=>setMethod(e.target.value as typeof method)}><option value="newton">Newton</option><option value="bisection">二分法</option><option value="fixed_point">不动点迭代</option></select></label>
      <label>函数 f(x)<input disabled={probe || !!initial?.episode_id} required className={control} value={fn} placeholder="x^2-2" onChange={e=>setFn(e.target.value)}/></label>
      <label>目标<select disabled={probe || !!initial?.episode_id} className={control} value={goal} onChange={e=>setGoal(e.target.value as typeof goal)}><option value="root_error">根误差上界</option><option value="residual">只要求残差</option></select></label>
      <label>容差<input disabled={probe || !!initial?.episode_id} className={control} value={tolerance} onChange={e=>setTolerance(e.target.value)}/></label>
    </div>
    <label className="block">迭代值（JSON 数组）<textarea className={`${control} font-mono`} rows={2} value={iterates} onChange={e=>setIterates(e.target.value)} placeholder='[1,1.5,1.4166666667]'/></label>
    <label className="block">收敛或有根区间（可选）<input disabled={probe} className={control} value={interval} onChange={e=>setInterval(e.target.value)} placeholder="1,2"/></label>
    {method === "bisection" && <label className="block">区间轨迹（JSON 数组）<textarea className={control} value={brackets} onChange={e=>setBrackets(e.target.value)} placeholder="[[1,2],[1,1.5]]"/></label>}
    {method === "fixed_point" && <label className="block">迭代函数 g(x)<input className={control} value={phi} onChange={e=>setPhi(e.target.value)} placeholder="(x+2/x)/2"/></label>}
    <label className="block">停止依据<select className={control} value={stop} onChange={e=>setStop(e.target.value as typeof stop)}><option value="none">尚未停止</option><option value="step">步长</option><option value="residual">残差</option><option value="bracket">区间误差界</option><option value="exact">认为已得到根</option><option value="iteration_limit">达到迭代上限</option></select></label>
    {!probe && <details><summary>导数、更新公式或合法变体</summary><textarea aria-label="求根变体参数" className={`${control} font-mono`} rows={5} value={advanced} onChange={e=>setAdvanced(e.target.value)}/><p className="text-xs">update 可用 x、f、df；variant 可为 standard/damped/modified。只核对表达式，不执行程序。</p></details>}
    {error && <p role="alert" className="text-cinnabar-600">{error}</p>}
    <button disabled={disabled} className="min-h-11 rounded bg-olive-700 text-paper-50 px-4 py-2" type="submit">验证我的过程</button>
  </form>;
}
