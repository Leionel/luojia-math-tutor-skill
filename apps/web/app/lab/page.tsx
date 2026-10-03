"use client";
import Link from "next/link";
import {getCurrentUserId} from "@/lib/demo-auth";
import {useEffect, useRef, useState} from "react";
import {LearningShell, Notice, learningButton, learningInput, learningPanel} from "@/components/learning/learning-shell";
import {finiteNumber, learningRequest, stableRequestId, type LabRun, type RootParameters} from "@/lib/learning-api";
import {LabReflection} from "@/components/learning/lab-reflection";
import {ExperimentNavigation} from "@/components/learning/experiment-navigation";
import {LabTutor} from "@/components/learning/lab-tutor";
import {MobileDrawer} from "@/components/mobile-drawer";
import {MessageCircle} from "lucide-react";
import {LabPlayback} from "@/components/learning/lab-playback";

export default function LabPage() {
  const [desktop,setDesktop]=useState(false);
  const [tutorOpen,setTutorOpen]=useState(false);
  const [selectedStep,setSelectedStep]=useState<number|null>(null);
  const operation=useRef<AbortController|null>(null);
  const mounted=useRef(false);
  const locked=useRef(false);
  const [method,setMethod]=useState<RootParameters["method"]>("newton");
  const [expression,setExpression]=useState("x^3-2*x+2");
  const [initial,setInitial]=useState("0");
  const [left,setLeft]=useState("-2");
  const [right,setRight]=useState("0");
  const [phi,setPhi]=useState("cos(x)");
  const [tolerance,setTolerance]=useState("0.0001");
  const [goal,setGoal]=useState<"root_error"|"residual">("residual");
  const [limit,setLimit]=useState("20");
  const [prediction,setPrediction]=useState("");
  const [run,setRun]=useState<LabRun|null>(null);
  const [history,setHistory]=useState<LabRun[]>([]);
  const [comparison,setComparison]=useState("");
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const [hydrated,setHydrated]=useState(false);
  const [presetValue,setPresetValue]=useState("cycle");
  useEffect(()=>{
    mounted.current=true;
    const media=window.matchMedia("(min-width: 1280px)");
    const update=()=>{setDesktop(media.matches); if(media.matches)setTutorOpen(false);}; update();
    media.addEventListener("change",update);
    const cancel=()=>{mounted.current=false; operation.current?.abort();setRun(null);setHistory([]);};
    window.addEventListener("luojia-auth-change",cancel);
    return()=>{mounted.current=false;operation.current?.abort();media.removeEventListener("change",update);window.removeEventListener("luojia-auth-change",cancel);};
  },[]);
  useEffect(()=>{
    try{
      const d=JSON.parse(localStorage.getItem(`lab-draft:${getCurrentUserId()}`)??"null");
      if(d && typeof d==="object"){
        if(["newton","bisection","fixed_point"].includes(d.method))setMethod(d.method);
        if(["root_error","residual"].includes(d.goal))setGoal(d.goal);
        if(["cycle","root","bisect","fixed","custom"].includes(d.presetValue))setPresetValue(d.presetValue);
        if(typeof d.expression==="string")setExpression(d.expression);
        if(typeof d.initial==="string")setInitial(d.initial);
        if(typeof d.left==="string")setLeft(d.left);
        if(typeof d.right==="string")setRight(d.right);
        if(typeof d.phi==="string")setPhi(d.phi);
        if(typeof d.tolerance==="string")setTolerance(d.tolerance);
        if(typeof d.limit==="string")setLimit(d.limit);
        if(typeof d.prediction==="string")setPrediction(d.prediction);
      }
    }catch{/* A corrupt browser draft does not alter server history. */}
    setHydrated(true);
    const owner=getCurrentUserId(),controller=new AbortController();operation.current=controller;
    learningRequest<{runs:LabRun[]}>("/root-lab/runs",undefined,controller.signal).then(async a=>{if(!mounted.current||owner!==getCurrentUserId())return;setHistory(a.runs);const id=new URLSearchParams(window.location.search).get("id");const loaded=id?await learningRequest<LabRun>(`/root-lab/runs/${encodeURIComponent(id)}`,undefined,controller.signal):a.runs.at(-1)??null;if(mounted.current&&owner===getCurrentUserId()){setRun(loaded);const step=new URLSearchParams(window.location.search).get("step");if(step!==null&&loaded&&Number.isInteger(Number(step))&&Number(step)>=0&&Number(step)<loaded.rows.length)setSelectedStep(Number(step));}}).catch(e=>{if(!controller.signal.aborted)setError(e.message);});
    return()=>controller.abort();
  },[]);
  useEffect(()=>{if(hydrated)localStorage.setItem(`lab-draft:${getCurrentUserId()}`,JSON.stringify({method,expression,initial,left,right,phi,tolerance,goal,limit,prediction,presetValue}));},[hydrated,method,expression,initial,left,right,phi,tolerance,goal,limit,prediction,presetValue]);
  const compare=history.find(r=>r.id===comparison);
  const comparable=compare && run && compare.parameters.function===run.parameters.function && compare.parameters.goal===run.parameters.goal && compare.parameters.tolerance===run.parameters.tolerance;
  const submit=async()=>{if(locked.current||!mounted.current)return;locked.current=true;const owner=getCurrentUserId(),controller=new AbortController();operation.current?.abort();operation.current=controller;setBusy(true);setError("");try{
    const params:RootParameters={method,function:expression,tolerance:finiteNumber(tolerance,"容差"),goal,interval:[finiteNumber(left,"左端点"),finiteNumber(right,"右端点")],...(method==="bisection"?{}:{initial_value:finiteNumber(initial,"初值")}),...(method==="fixed_point"?{phi}:{})};
    const result=await learningRequest<LabRun>("/root-lab/runs",{attempt:params,max_iterations:finiteNumber(limit,"迭代上限"),prediction,request_id:stableRequestId(localStorage,`lab-request:${getCurrentUserId()}`,{params,limit,prediction},()=>crypto.randomUUID())},controller.signal);if(!mounted.current||owner!==getCurrentUserId())return;setSelectedStep(null);setRun(result);window.history.replaceState(null,"",`/lab?id=${encodeURIComponent(result.id)}`);setHistory(previous=>[...previous.filter(r=>r.id!==result.id),result].slice(-20));
  }catch(e){if(!controller.signal.aborted)setError(e instanceof Error?e.message:"实验失败");}finally{locked.current=false;if(mounted.current)setBusy(false);}};
  const preset=(value:string)=>{setPresetValue(value);setComparison("");if(value==="cycle"){setMethod("newton");setExpression("x^3-2*x+2");setInitial("0");setLeft("-2");setRight("0");setGoal("residual");}if(value==="root"){setMethod("newton");setExpression("x^2-2");setInitial("1");setLeft("1");setRight("2");setGoal("root_error");}if(value==="bisect"){setMethod("bisection");setExpression("x^2-2");setLeft("1");setRight("2");setGoal("root_error");}if(value==="fixed"){setMethod("fixed_point");setExpression("cos(x)-x");setPhi("cos(x)");setInitial("0.5");setLeft("0");setRight("1");setGoal("root_error");}};
  const saved=(next:LabRun)=>{setRun(next);setSelectedStep(null);setComparison("");setHistory(previous=>[...previous.filter(r=>r.id!==next.id),next].slice(-20));window.history.replaceState(null,"",`/lab?id=${encodeURIComponent(next.id)}`);};
  return <LearningShell wide title="让迭代过程看得见" description="先预测，再运行。改变初值、方法或阈值，对照轨迹与停止依据，最后回到自己的求根练习。">
    <ExperimentNavigation active="root"/>
    <Notice error={error}/><div className={run?.parameters.method==="newton"?"grid items-start gap-8 xl:grid-cols-[minmax(0,1fr)_400px]":""}><div className="grid gap-8 lg:grid-cols-[minmax(240px,.75fr)_minmax(0,1.4fr)]">
      <section className={`${learningPanel} self-start`}><label htmlFor="preset" className="block mb-2 font-semibold">从典型现象开始</label><select id="preset" name="preset" value={presetValue} className={`${learningInput} mb-5`} onChange={e=>preset(e.target.value)}><option value="custom">自定义参数</option><option value="cycle">牛顿法：0 → 1 → 0 循环</option><option value="root">牛顿法：逼近 √2</option><option value="bisect">二分法：缩小有根区间</option><option value="fixed">不动点：cos(x) 迭代</option></select>
        <form className="space-y-4" onSubmit={e=>{e.preventDefault();submit();}}>
          <div><label htmlFor="method" className="mb-2 block">方法</label><select id="method" name="method" className={learningInput} value={method} onChange={e=>{setPresetValue("custom");setMethod(e.target.value as RootParameters["method"]);}}><option value="newton">标准牛顿法</option><option value="bisection">二分法</option><option value="fixed_point">不动点迭代</option></select></div>
          <div><label htmlFor="function" className="mb-2 block">f(x)</label><input id="function" name="function" required maxLength={200} className={`${learningInput} font-mono`} value={expression} onChange={e=>{setPresetValue("custom");setExpression(e.target.value);}}/></div>
          {method!=="bisection" && <div><label htmlFor="initial" className="mb-2 block">初值 x₀</label><input id="initial" name="initial" required className={learningInput} value={initial} onChange={e=>{setPresetValue("custom");setInitial(e.target.value);}}/></div>}
          {method==="fixed_point" && <div><label htmlFor="phi" className="mb-2 block">phi(x)</label><input id="phi" name="phi" required maxLength={200} className={`${learningInput} font-mono`} value={phi} onChange={e=>{setPresetValue("custom");setPhi(e.target.value);}}/></div>}
          <div className="grid grid-cols-2 gap-3"><div><label htmlFor="left" className="mb-2 block">区间下界</label><input id="left" name="left" required className={learningInput} value={left} onChange={e=>{setPresetValue("custom");setLeft(e.target.value);}}/></div><div><label htmlFor="right" className="mb-2 block">区间上界</label><input id="right" name="right" required className={learningInput} value={right} onChange={e=>{setPresetValue("custom");setRight(e.target.value);}}/></div></div>
          <div><label htmlFor="goal" className="mb-2 block">观察目标</label><select id="goal" name="goal" className={learningInput} value={goal} onChange={e=>{setPresetValue("custom");setGoal(e.target.value as "root_error"|"residual");}}><option value="residual">残差 |f(x)|</option><option value="root_error">根误差（须有可核对的界）</option></select></div>
          <div className="grid grid-cols-2 gap-3"><div><label htmlFor="tolerance" className="mb-2 block">阈值</label><input id="tolerance" name="tolerance" required className={learningInput} value={tolerance} onChange={e=>{setPresetValue("custom");setTolerance(e.target.value);}}/></div><div><label htmlFor="limit" className="mb-2 block">迭代上限</label><input id="limit" name="limit" type="number" min={1} max={100} required className={learningInput} value={limit} onChange={e=>{setPresetValue("custom");setLimit(e.target.value);}}/></div></div>
          <div><label htmlFor="prediction" className="mb-2 block">先写下预测</label><textarea id="prediction" name="prediction" required maxLength={1000} rows={3} className={learningInput} value={prediction} onChange={e=>setPrediction(e.target.value)} placeholder="会收敛、循环，还是停止？你的依据是什么？"/></div><button type="submit" disabled={busy || !prediction.trim()} className={learningButton}>{busy?"正在计算…":"运行参考实验"}</button>
        </form>
      </section>
      <section className="min-w-0">{!run?<div className={learningPanel}><h2 className="text-xl font-semibold">试试改一个初值</h2><p className="mt-4 leading-7 text-[var(--text-secondary)]">默认示例会在 0 和 1 之间循环。预测原因后运行，再把初值改为 −2 对照。</p></div>:<>
        <h2 className="text-xl font-semibold">本次观察</h2><p className="mt-3 break-words font-mono">{run.parameters.method} · f(x) = {run.parameters.function}</p><p className="mt-3 leading-7 text-[var(--text-secondary)]">{run.prediction_timing==="after_preview"?"预览后的观察":"我的预测"}：{run.prediction}</p><p className="mt-3 leading-7">{run.stop_detail}</p><p className="mt-2 leading-7 text-[var(--text-secondary)]">{run.diagnosis.summary}</p>
        <LabPlayback key={run.id} run={run} comparison={comparable?compare:undefined} onDiscussStep={run.parameters.method==="newton"?step=>{setSelectedStep(step);setTutorOpen(true);window.history.replaceState(null,"",`/lab?id=${encodeURIComponent(run.id)}&step=${step}`);}:undefined}/>
        <LabReflection key={`reflection-${run.id}`} runId={run.id}/>
        <div className="mt-6"><label htmlFor="compare" className="mb-2 block">选择历史实验对照</label><select id="compare" name="compare" className={learningInput} value={comparison} onChange={e=>setComparison(e.target.value)}><option value="">不对照</option>{history.filter(h=>h.id!==run.id).map(h=><option key={h.id} value={h.id}>{h.parameters.method} · {h.parameters.function} · x₀={h.parameters.initial_value??"中点"}</option>)}</select>{compare && <button type="button" className="mt-3 min-h-11 text-olive-700 dark:text-olive-300 underline" onClick={()=>{setRun(compare);setSelectedStep(null);setComparison("");window.history.replaceState(null,"",`/lab?id=${encodeURIComponent(compare.id)}`);}}>回看这次历史实验</button>}{compare && !comparable && <p className="mt-3 text-ochre-700 dark:text-ochre-300">函数、目标或阈值不同，暂不合并轨迹。</p>}{comparable && <p className="mt-3 leading-7">对照结果：{compare.stop_detail}；记录 {compare.rows.length} 个近似值，本次 {run.rows.length} 个。</p>}</div>
        <div className="mt-6 overflow-x-auto rounded-lg border border-[var(--border-subtle)]"><table className="w-full text-right text-base sm:text-sm"><caption className="p-3 text-left font-semibold">本次迭代轨迹</caption><thead className="bg-[var(--bg-tertiary)]"><tr>{["k","xₖ","f(xₖ)","相邻差","区间"].map(s=><th key={s} scope="col" className="whitespace-nowrap px-3 py-3 font-medium">{s}</th>)}</tr></thead><tbody>{run.rows.map(row=><tr key={row.k} className="border-t border-[var(--border-subtle)]"><td className="p-3">{row.k}</td><td className="p-3 font-mono">{row.x.toPrecision(7)}</td><td className="p-3 font-mono">{row.fx.toExponential(3)}</td><td className="p-3 font-mono">{row.step?.toExponential(3)??"—"}</td><td className="whitespace-nowrap p-3 font-mono">{row.bracket?.map(x=>x.toPrecision(5)).join(" ~ ")??"—"}</td></tr>)}</tbody></table></div>
        <p className="mt-5 text-base sm:text-sm text-[var(--text-secondary)]">这是系统生成的参考轨迹，会记录为帮助；不计为独立完成。</p>
        {run.parameters.method === "newton" && <Link href={`/chat?lab=${encodeURIComponent(run.id)}`} className="mt-3 inline-flex min-h-12 items-center text-olive-700 underline dark:text-olive-300">带着这次实验问小珞 →</Link>}
        <Link href="/study" className="mt-4 block text-olive-700 dark:text-olive-300 underline">回到自己的求根练习 →</Link>
      </>}</section>
    </div>
    {run?.parameters.method==="newton" && desktop && <div className="sticky top-6 h-[min(760px,calc(100dvh-360px))] min-h-[480px]"><LabTutor run={run} selectedStep={selectedStep} onSaved={saved} onResetStep={()=>{setSelectedStep(null);window.history.replaceState(null,"",`/lab?id=${encodeURIComponent(run.id)}`);}}/></div>}
    </div>
    {run?.parameters.method==="newton" && !desktop && <>
      <button type="button" onClick={()=>setTutorOpen(true)} className="fixed bottom-5 right-5 z-40 flex min-h-14 items-center gap-2 rounded-full border border-olive-500/25 bg-olive-700 px-5 font-medium text-paper-50 shadow-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-olive-600"><MessageCircle aria-hidden="true" className="size-5"/>问小珞</button>
      {tutorOpen && <MobileDrawer title="小珞 · 实验伴学" side="right" breakpoint={1280} onClose={()=>setTutorOpen(false)}><LabTutor run={run} selectedStep={selectedStep} onSaved={saved} onResetStep={()=>{setSelectedStep(null);window.history.replaceState(null,"",`/lab?id=${encodeURIComponent(run.id)}`);}}/></MobileDrawer>}
    </>}
  </LearningShell>;
}
