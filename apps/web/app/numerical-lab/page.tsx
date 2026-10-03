"use client";
import Link from "next/link";
import {useEffect, useRef, useState} from "react";
import {LearningShell, Notice, learningButton, learningInput, learningPanel} from "@/components/learning/learning-shell";
import {ExperimentNavigation} from "@/components/learning/experiment-navigation";
import {NumericalPlayback} from "@/components/learning/numerical-playback";
import {learningRequest, stableRequestId} from "@/lib/learning-api";
import {getCurrentUserId} from "@/lib/demo-auth";
import {numericMatrix, numericVector, comparableNumerical, discussionDraft, type NumericalTask, type NumericalRun, type NumericalCheck} from "@/lib/numerical-lab";

const methodNames: Record<string, string> = {jacobi: "Jacobi", gauss_seidel: "Gauss–Seidel", trapezoid: "复合梯形", simpson: "复合 Simpson", adaptive_simpson: "自适应 Simpson"};

export default function NumericalLabPage() {
  const [domain, setDomain] = useState<"linear_system" | "integration">("linear_system");
  const [linearMethod, setLinearMethod] = useState<"jacobi" | "gauss_seidel">("jacobi");
  const [integrationMethod, setIntegrationMethod] = useState<"trapezoid" | "simpson" | "adaptive_simpson">("simpson");
  const [matrix, setMatrix] = useState("4 1\n2 3");
  const [rhs, setRhs] = useState("1 2");
  const [initial, setInitial] = useState("0 0");
  const [expression, setExpression] = useState("exp(x)");
  const [left, setLeft] = useState("0");
  const [right, setRight] = useState("1");
  const [intervals, setIntervals] = useState("4");
  const [tolerance, setTolerance] = useState("0.000001");
  const [limit, setLimit] = useState("50");
  const [prediction, setPrediction] = useState("");
  const [runs, setRuns] = useState<NumericalRun[]>([]);
  const [run, setRun] = useState<NumericalRun | null>(null);
  const [compareId, setCompareId] = useState("");
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<NumericalCheck | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [checking, setChecking] = useState(false);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const operation = useRef(false);
  useEffect(() => {
    const controller = new AbortController();
    const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]);
    learningRequest<{runs: NumericalRun[]}>("/numerical-lab/runs", undefined, signal).then(async data => {
      setRuns(data.runs);
      const id = new URLSearchParams(window.location.search).get("id");
      const selected = id ? await learningRequest<NumericalRun>(`/numerical-lab/runs/${encodeURIComponent(id)}`, undefined, signal) : data.runs.at(-1);
      if (!controller.signal.aborted && selected) {setRun(selected); setDomain(selected.task.domain);}
    }).catch(e => {if (!controller.signal.aborted) setError(e.message);}).finally(() => {if (!controller.signal.aborted) setLoading(false);});
    return () => controller.abort();
  }, []);
  const comparison = runs.find(value => value.id === compareId);
  const comparable = run && comparison && comparableNumerical(run, comparison);
  const scalar = (text: string) => numericVector(text, 1)[0];
  function show(value: NumericalRun) {setRun(value); setFeedback(null); setAnswer(""); setCopied(false); setCompareId(""); window.history.replaceState(null, "", `/numerical-lab?id=${encodeURIComponent(value.id)}`);}
  function loadParameters(value: NumericalRun) {
    const task = value.task;
    setDomain(task.domain); setTolerance(String(task.tolerance)); setLimit(String(task.limit)); setPrediction(value.prediction);
    if (task.domain === "linear_system") {
      setLinearMethod(task.method); setMatrix(task.matrix.map(row => row.join(" ")).join("\n"));
      setRhs(task.rhs.join(" ")); setInitial(task.initial.join(" "));
    } else {
      setIntegrationMethod(task.method); setExpression(task.expression); setLeft(String(task.left));
      setRight(String(task.right)); setIntervals(String(task.intervals));
    }
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (operation.current || loading) return;
    operation.current = true; setBusy(true); setError("");
    try {
      const common = {tolerance: scalar(tolerance), limit: scalar(limit)};
      if (!Number.isInteger(common.limit)) throw new Error("预算须为整数");
      const task: NumericalTask = domain === "linear_system" ? {domain, method: linearMethod, matrix: numericMatrix(matrix), rhs: numericVector(rhs), initial: numericVector(initial), ...common} : {domain, method: integrationMethod, expression, left: scalar(left), right: scalar(right), intervals: scalar(intervals), ...common};
      const payload = {task, prediction};
      const requestId = stableRequestId(sessionStorage, `numerical-request:${getCurrentUserId()}`, payload, () => crypto.randomUUID());
      const saved = await learningRequest<NumericalRun>("/numerical-lab/runs", {request_id: requestId, ...payload}, AbortSignal.timeout(15000));
      setRuns(values => [...values.filter(value => value.id !== saved.id), saved].slice(-30)); show(saved);
    } catch (e) {setError(e instanceof Error ? e.message : "请检查输入后重试");}
    finally {operation.current = false; setBusy(false);}
  }
  async function check(event: React.FormEvent) {
    event.preventDefault(); if (!run || operation.current || loading) return;
    operation.current = true; setChecking(true); setFeedback(null); setError("");
    try {setFeedback(await learningRequest<NumericalCheck>(`/numerical-lab/runs/${encodeURIComponent(run.id)}/check`, {source_hash: run.source_hash, answer: numericVector(answer)}, AbortSignal.timeout(15000)));}
    catch (e) {setError(e instanceof Error ? e.message : "核对失败");}
    finally {operation.current = false; setChecking(false);}
  }
  return <LearningShell title="数值实验 · 从迭代到积分" description="先预测，逐步观察，再核对数值依据。求根、线性方程组和数值积分各有自己的验证范围。">
    <ExperimentNavigation active="numerical"/><Notice error={error}/>
    <div className="mb-6 flex flex-wrap gap-3" role="group" aria-label="选择数值任务">{[{id: "linear_system", title: "线性方程组"}, {id: "integration", title: "数值积分"}].map(item => <button key={item.id} disabled={busy || checking || loading} aria-pressed={domain === item.id} className={`${learningButton} ${domain !== item.id ? "opacity-70" : ""}`} onClick={() => {setDomain(item.id as typeof domain); setError("");}}>{item.title}</button>)}</div>
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
      <section className={learningPanel}><h2 className="text-xl font-semibold">{domain === "linear_system" ? "解 Ax = b" : "近似计算定积分"}</h2><p className="mt-2 text-sm text-[var(--text-secondary)]">下方用于新实验。回看历史时，可从右侧载入原参数再改一个变量。</p>
        <p className="my-4 leading-7 text-[var(--text-secondary)]">{domain === "linear_system" ? "观察新分量是否立即参与下一次更新；比较残差与相邻差。默认例子的解为 (0.1, 0.6)，用于校准实验。" : "比较均匀加密与局部细分。默认 exp(x) 在 [0, 1] 的积分为 e−1，可用解析值复核。"}</p>
        <button disabled={busy || checking || loading} className="mb-4 min-h-11 text-olive-700 underline dark:text-olive-300" onClick={() => {if (domain === "linear_system") {setMatrix("1 2\n2 1"); setRhs("1 2"); setInitial("0 0");} else {setExpression("sin(16*pi*x)^2"); setLeft("0"); setRight("1"); setIntervals("4");} setPrediction("");}}>换一个需要警惕的例子</button>
        {domain === "integration" && expression === "sin(16*pi*x)^2" && <p className="mb-4 rounded-lg bg-ochre-600/10 p-3 leading-7">这个例子的真实积分为 1/2，但分段数 4 的采样可能全部落在零点。试着改为 6，再比较结果；估计很小也可能不准确。</p>}
        <form onSubmit={submit} className="space-y-4"><div><label htmlFor="num-method" className="mb-2 block">方法</label><select id="num-method" className={learningInput} value={domain === "linear_system" ? linearMethod : integrationMethod} onChange={e => domain === "linear_system" ? setLinearMethod(e.target.value as typeof linearMethod) : setIntegrationMethod(e.target.value as typeof integrationMethod)}>{(domain === "linear_system" ? ["jacobi", "gauss_seidel"] : ["trapezoid", "simpson", "adaptive_simpson"]).map(method => <option key={method} value={method}>{methodNames[method]}</option>)}</select></div>
          {domain === "linear_system" ? <><div><label htmlFor="num-matrix" className="mb-2 block">矩阵 A（每行一个方程，空格分隔）</label><textarea id="num-matrix" rows={4} required maxLength={1500} value={matrix} onChange={e => setMatrix(e.target.value)} className={`${learningInput} font-mono`}/></div><div><label htmlFor="num-rhs" className="mb-2 block">右端向量 b</label><input id="num-rhs" required maxLength={200} value={rhs} onChange={e => setRhs(e.target.value)} className={learningInput}/></div><div><label htmlFor="num-initial" className="mb-2 block">初始向量 x₀</label><input id="num-initial" required maxLength={200} value={initial} onChange={e => setInitial(e.target.value)} className={learningInput}/></div></> : <><div><label htmlFor="num-expression" className="mb-2 block">被积函数 f(x)</label><input id="num-expression" required maxLength={200} value={expression} onChange={e => setExpression(e.target.value)} className={learningInput}/><p className="mt-2 text-sm leading-6">支持 x、算术、sin / cos / exp / log 等有界解析表达式。</p></div><div className="grid grid-cols-2 gap-3"><div><label htmlFor="num-left">左端点</label><input id="num-left" required value={left} onChange={e => setLeft(e.target.value)} className={learningInput}/></div><div><label htmlFor="num-right">右端点</label><input id="num-right" required value={right} onChange={e => setRight(e.target.value)} className={learningInput}/></div></div><div><label htmlFor="num-intervals">初始分段数（Simpson 须为偶数）</label><input id="num-intervals" required inputMode="numeric" value={intervals} onChange={e => setIntervals(e.target.value)} className={learningInput}/></div></>}
          <div className="grid grid-cols-2 gap-3"><div><label htmlFor="num-tolerance">{domain === "linear_system" ? "绝对残差阈值" : "误差估计阈值"}</label><input id="num-tolerance" required value={tolerance} onChange={e => setTolerance(e.target.value)} className={learningInput}/></div><div><label htmlFor="num-limit">迭代 / 细分预算（1–100）</label><input id="num-limit" required inputMode="numeric" value={limit} onChange={e => setLimit(e.target.value)} className={learningInput}/></div></div>
          <div><label htmlFor="num-prediction" className="mb-2 block">运行前的预测与依据</label><textarea id="num-prediction" required maxLength={2000} rows={3} value={prediction} onChange={e => setPrediction(e.target.value)} className={learningInput} placeholder="预计哪种方法更快？什么条件支持这个判断？"/></div><button type="submit" className={learningButton} disabled={busy || checking || loading || !prediction.trim()}>{busy ? "正在计算并保存…" : "运行并保存参考实验"}</button>
        </form>
      </section>
      <section className={`min-w-0 ${learningPanel}`}><h2 className="text-xl font-semibold">保存的实验与数值核对</h2>
        <label className="mb-2 mt-4 block" htmlFor="num-history">回看历史实验</label><select id="num-history" disabled={busy || checking || loading} value={run?.id ?? ""} className={learningInput} onChange={e => {const value = runs.find(r => r.id === e.target.value); if (value) show(value);}}><option value="" disabled>尚未选择实验</option>{runs.map(value => <option key={value.id} value={value.id}>{methodNames[value.task.method]} · {value.created_at.slice(0, 19).replace("T", " ")} UTC · {value.prediction.slice(0, 20)}</option>)}</select>
        {!run ? <p className="mt-6 leading-7 text-[var(--text-secondary)]">写下预测再运行。实验会按当前账户保存，刷新后仍可回看。</p> : <><p className="mt-5 font-semibold">{methodNames[run.task.method]} · {run.task.domain === "linear_system" ? "线性方程组" : "数值积分"}</p><p className="mt-2 leading-7">我的预测：{run.prediction}</p><details className="mt-3"><summary className="min-h-11 cursor-pointer">查看本次保存参数</summary><pre className="overflow-auto rounded-lg bg-[var(--bg-tertiary)] p-3 text-sm">{JSON.stringify(run.task, null, 2)}</pre></details><p className="mt-3 leading-7">{run.stop_detail}</p>
          <button disabled={busy || checking || loading} className="mt-3 min-h-11 text-olive-700 underline dark:text-olive-300" onClick={() => loadParameters(run)}>载入本次保存参数，再改一个变量</button>
          <ul className="mt-3 list-disc space-y-2 pl-5 leading-7 text-[var(--text-secondary)]">{run.conditions.map(condition => <li key={condition}>{condition}</li>)}</ul>
          <label htmlFor="num-comparison" className="mb-2 mt-4 block">选择另一种方法对照</label><select id="num-comparison" className={learningInput} value={compareId} onChange={e => setCompareId(e.target.value)}><option value="">不对照</option>{runs.filter(value => value.id !== run.id).map(value => <option key={value.id} value={value.id}>{methodNames[value.task.method]} · {value.prediction.slice(0, 20)}</option>)}</select>{comparison && !comparable && <p className="mt-2 leading-7 text-ochre-700 dark:text-ochre-300">问题、初始向量或阈值不同，暂不叠加轨迹。</p>}
          {comparable && comparison && <p className="mt-3 break-all leading-7">对照末值：{comparison.rows.at(-1)?.vector?.map(v => v.toPrecision(7)).join(", ") ?? comparison.rows.at(-1)?.value?.toPrecision(9)}；{comparison.stop_detail}</p>}
          <NumericalPlayback key={run.id} run={run} comparison={comparable ? comparison : undefined}/>
          <form onSubmit={check} className="mt-6 space-y-3 border-t border-[var(--border-subtle)] pt-5"><label htmlFor="num-answer" className="block font-semibold">核对自己的数值结果（已参考帮助）</label><input id="num-answer" required maxLength={500} value={answer} onChange={e => {setAnswer(e.target.value); setFeedback(null);}} className={learningInput} placeholder={run.task.domain === "linear_system" ? "例如：0.1 0.6" : "填写一个积分近似值"}/><button disabled={checking || busy || loading} className={learningButton}>{checking ? "正在核对…" : "核对数值依据"}</button></form>
          {feedback && <div role="status" className="mt-4 rounded-lg bg-[var(--bg-tertiary)] p-4 leading-7"><p>{feedback.matches ? "与本次核对规则相符" : "暂未与本次核对规则相符"} · {feedback.residual !== undefined ? `残差 ${feedback.residual.toExponential(5)}` : `与参考值差 ${feedback.difference?.toExponential(5)}`}</p><p>{feedback.message}</p></div>}
          <p className="mt-5 leading-7 text-[var(--text-secondary)]">参考实验和结果核对均不计为独立完成，不更新求根成绩，也不执行学生程序。</p>
          <button className="mt-4 min-h-11 text-olive-700 underline dark:text-olive-300" onClick={async () => {try {await navigator.clipboard.writeText(discussionDraft(run)); setCopied(true);} catch {setError("复制不可用，请从保存参数中选取内容");}}}>{copied ? "已复制实验问题，可粘贴到对话" : "复制实验问题，向小珞讨论"}</button><Link href="/chat" className="ml-4 inline-block min-h-11 py-3 text-olive-700 underline dark:text-olive-300">打开对话 →</Link>
        </>}
      </section>
    </div>
  </LearningShell>;
}
