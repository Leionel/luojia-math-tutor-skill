"use client";

import Link from "next/link";
import {useEffect, useRef, useState} from "react";
import {ArrowRight, Check, Eye, Loader2} from "lucide-react";
import {getCurrentUserId, isAuthStorageKey} from "@/lib/demo-auth";
import {learningRequest, stableRequestId, type LabRun, type NewtonActivityState} from "@/lib/learning-api";
import {learningInput} from "./learning-shell";
import {LabPlayback} from "./lab-playback";

const path = "/root-lab/activity/newton-cycle-v1";

export function NewtonActivity({onDiscuss}: {onDiscuss:(run:LabRun,step:number)=>void}) {
  const [activity,setActivity]=useState<NewtonActivityState|null>(null);
  const [prediction,setPrediction]=useState("");
  const [reason,setReason]=useState("");
  const [explanation,setExplanation]=useState("");
  const [revision,setRevision]=useState("");
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [loginNeeded,setLoginNeeded]=useState(false);
  const generation=useRef(0);
  const request=useRef<AbortController|null>(null);

  useEffect(()=>{
    const owner=getCurrentUserId(),version=++generation.current,controller=new AbortController();
    request.current=controller;
    learningRequest<NewtonActivityState>(path,undefined,controller.signal)
      .then(next=>{if(version===generation.current&&owner===getCurrentUserId())setActivity(next);})
      .catch(e=>{if(!controller.signal.aborted){setError(e instanceof Error?e.message:"活动暂不可用");setLoginNeeded((e as {status?:number}).status===401);}});
    const changed=()=>{generation.current++;request.current?.abort();setActivity(null);setBusy(false);setError("身份已变化，请刷新后继续。");};
    const storage=(event:StorageEvent)=>{if(isAuthStorageKey(event.key))changed();};
    window.addEventListener("luojia-auth-change",changed);window.addEventListener("storage",storage);
    return()=>{generation.current=version+1;controller.abort();window.removeEventListener("luojia-auth-change",changed);window.removeEventListener("storage",storage);};
  },[]);

  async function send(action:"predict"|"reveal"|"explain"|"revise",payload:Record<string,unknown>) {
    if(busy)return;
    const owner=getCurrentUserId(),version=generation.current,controller=new AbortController();
    request.current=controller;setBusy(true);setError("");
    try {
      const request_id=stableRequestId(localStorage,`newton-activity:${owner}:${action}:${action==="revise"?(activity?.revisions.length??0):0}`,
        payload,()=>crypto.randomUUID());
      const next=await learningRequest<NewtonActivityState>(`${path}/${action}`,{...payload,request_id},controller.signal);
      if(version!==generation.current||owner!==getCurrentUserId()||controller.signal.aborted)return;
      setActivity(next);
      if(action==="predict"){setPrediction("");setReason("");}
      if(action==="explain")setExplanation("");
      if(action==="revise")setRevision("");
    } catch(e) {
      if(!controller.signal.aborted&&version===generation.current)setError(e instanceof Error?e.message:"提交未完成，请重试");
    } finally {if(version===generation.current)setBusy(false);}
  }

  const run=activity?.run;
  const reached=activity?.reveal!==null&&activity?.reveal!==undefined;
  const stage=reached?activity?.revisions.length?4:activity?.explanation?3:2:activity?.prediction?1:0;
  const button="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-olive-700 px-5 py-3 font-medium text-paper-50 transition-colors hover:bg-olive-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-olive-600 disabled:cursor-wait disabled:opacity-45";

  return <section aria-label="Newton 参与式学习活动" className="mb-10 overflow-hidden rounded-[1.75rem] border border-olive-700/20 bg-[var(--bg-card)] shadow-[0_28px_80px_-58px_rgba(22,29,19,.55)]">
    <div className="relative overflow-hidden bg-olive-950 px-5 py-8 text-paper-50 sm:px-8 sm:py-10">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 opacity-20" style={{backgroundImage:"linear-gradient(#a8ba90 1px, transparent 1px), linear-gradient(90deg, #a8ba90 1px, transparent 1px)",backgroundSize:"34px 34px",maskImage:"linear-gradient(90deg,transparent 12%,black 100%)"}}/>
      <div className="relative grid gap-8 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,.8fr)] lg:items-end">
        <div><p className="font-mono text-xs tracking-[.22em] text-olive-200">NEWTON / 参与式实验 01</p>
          <h2 className="mt-4 font-title text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">先写下判断，<br/>再让迭代回答。</h2>
          <p className="mt-4 max-w-xl text-sm leading-7 text-olive-100">同一个函数，从给定初值出发会怎样？先留下你的判断；轨迹只会在你提交或选择跳过后出现。</p>
        </div>
        <div className="rounded-2xl border border-olive-300/30 bg-olive-900/70 p-5 backdrop-blur-sm sm:p-6">
          <p className="text-xs tracking-widest text-olive-200">已知条件</p>
          <p className="mt-3 break-all font-mono text-xl font-medium sm:text-2xl">f(x) = x³ − 2x + 2</p>
          <p className="mt-2 font-mono text-sm text-olive-100">f′(x) = 3x² − 2　·　x₀ = 0</p>
          <div className="mt-5 flex items-center gap-3 border-t border-olive-300/20 pt-4"><span className="size-2 rounded-full bg-ochre-300"/><span className="text-xs text-olive-100">后续轨迹暂未展开</span></div>
        </div>
      </div>
    </div>
    <div className="px-5 py-6 sm:px-8 sm:py-8">
      <ol aria-label="学习步骤" className="grid grid-cols-4 gap-2 border-b border-[var(--border-subtle)] pb-6 text-xs sm:text-sm">
        {["预测","观察","解释","修订"].map((label,index)=><li key={label} className={`flex items-center gap-2 ${stage>=index+1?"text-olive-700 dark:text-olive-300":"text-[var(--text-muted)]"}`}><span className={`flex size-7 shrink-0 items-center justify-center rounded-full border font-mono text-xs ${stage>=index+1?"border-olive-600 bg-olive-600/10":"border-[var(--border-subtle)]"}`}>{stage>=index+1?<Check aria-hidden="true" className="size-3.5"/>:index+1}</span><span>{label}</span></li>)}
      </ol>
      {!activity&&!error&&<p role="status" className="mt-6 flex items-center gap-2 text-sm"><Loader2 aria-hidden="true" className="size-4 animate-spin"/>正在恢复活动…</p>}
      {error&&<p role="alert" className="mt-6 rounded-xl border border-cinnabar-600/25 bg-cinnabar-600/5 p-4 text-sm text-cinnabar-700 dark:text-cinnabar-300">{error}{loginNeeded&&<> <Link href="/auth/login" className="underline">前往登录</Link></>}</p>}
      {activity&&!activity.prediction&&!reached&&<div className="mt-7 grid gap-7 lg:grid-cols-[minmax(0,1fr)_minmax(250px,.55fr)]">
        <div><h3 className="font-title text-xl font-semibold">你预计接下来的近似值会怎样变化？</h3><p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">猜测可以不确定。这里保存你的原话，不据此判断是否掌握。</p>
          <label htmlFor="newton-prediction" className="mt-5 block text-sm font-medium">我的预测</label><textarea id="newton-prediction" rows={3} maxLength={1000} value={prediction} onChange={e=>setPrediction(e.target.value)} placeholder="我预计……" className={`${learningInput} mt-2`}/>
          <label htmlFor="newton-reason" className="mt-4 block text-sm font-medium">依据（可选）</label><textarea id="newton-reason" rows={2} maxLength={1000} value={reason} onChange={e=>setReason(e.target.value)} placeholder="因为我目前知道……" className={`${learningInput} mt-2`}/>
          <div className="mt-5 flex flex-wrap items-center gap-4"><button type="button" disabled={busy||!prediction.trim()} onClick={()=>void send("predict",{text:prediction.trim(),reason:reason.trim()})} className={button}>{busy?<Loader2 aria-hidden="true" className="size-4 animate-spin"/>:<ArrowRight aria-hidden="true" className="size-4"/>}保存预测</button><button type="button" disabled={busy} onClick={()=>void send("reveal",{mode:"answer"})} className="min-h-12 text-sm text-olive-700 underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-olive-600 disabled:opacity-45 dark:text-olive-300">跳过预测，直接看答案</button></div>
        </div><aside className="self-start rounded-2xl border border-dashed border-olive-500/40 bg-olive-500/5 p-5"><p className="font-mono text-xs tracking-wider text-olive-700 dark:text-olive-300">观察窗口</p><div aria-hidden="true" className="my-8 flex h-24 items-end border-b border-l border-olive-500/40 pl-4 pb-3"><span className="size-3 rounded-full bg-olive-600"/></div><p className="text-sm leading-6 text-[var(--text-secondary)]">当前只知道起点。保存预测后，再逐步查看真实计算。</p></aside>
      </div>}
      {activity?.prediction&&<div className="mt-7 rounded-xl border-l-4 border-olive-600 bg-olive-500/5 px-5 py-4"><p className="text-xs font-medium tracking-wider text-olive-700 dark:text-olive-300">最初的预测 · 已保存原文</p><p className="mt-2 whitespace-pre-wrap leading-7">{activity.prediction.text}</p>{activity.prediction.reason&&<p className="mt-2 text-sm text-[var(--text-secondary)]">依据：{activity.prediction.reason}</p>}</div>}
      {activity?.prediction&&!reached&&<div className="mt-6 flex flex-wrap gap-4"><button type="button" disabled={busy} onClick={()=>void send("reveal",{mode:"observe"})} className={button}><Eye aria-hidden="true" className="size-4"/>开始观察真实迭代</button><button type="button" disabled={busy} onClick={()=>void send("reveal",{mode:"answer"})} className="min-h-12 text-sm text-olive-700 underline underline-offset-4 dark:text-olive-300">直接看完整答案</button></div>}
      {run&&<div className="mt-8"><div className="flex flex-wrap items-baseline justify-between gap-2"><h3 className="font-title text-2xl font-semibold">逐步观察</h3><span className="font-mono text-xs text-[var(--text-muted)]">{run.runner_version} · {run.id}</span></div><p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">标准 Newton · x₀={run.parameters.initial_value} · 残差阈值 {run.parameters.tolerance} · 上限 {run.max_iterations} 步。由受控计算器生成，属于参考帮助。</p>
        <LabPlayback run={run} concealFuture onDiscussStep={activity.context_current?step=>onDiscuss(run,step):undefined}/>
        <p className="mt-3 text-sm leading-6 text-[var(--text-secondary)]">停止说明：{run.stop_detail}。数值回放只描述这一次计算；更换初值须重新运行，不能沿用本题判断。</p>
        {!activity.context_current&&<p role="status" className="mt-3 text-sm text-ochre-700 dark:text-ochre-300">计算或课程版本已更新：旧轨迹仅供回看，请重新实验后再与助教讨论。</p>}
      </div>}
      {run&&!activity?.explanation&&activity?.prediction_choice==="submitted"&&<div className="mt-8 rounded-2xl border border-olive-500/20 bg-olive-500/5 p-5 sm:p-6"><h3 className="font-title text-xl font-semibold">把观察说清楚</h3><p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">你看到了什么？为什么不能只凭局部收敛结论判断这个初值？这里记录你的解释，不自动计分。</p><label htmlFor="newton-explanation" className="sr-only">我的解释</label><textarea id="newton-explanation" rows={3} maxLength={2000} value={explanation} onChange={e=>setExplanation(e.target.value)} placeholder="我观察到……；局部定理要求……" className={`${learningInput} mt-4`}/><div className="mt-4 flex flex-wrap items-center gap-4"><button type="button" disabled={busy||!explanation.trim()} onClick={()=>void send("explain",{run_id:run.id,input_hash:run.input_hash,text:explanation.trim()})} className={button}>保存解释<ArrowRight aria-hidden="true" className="size-4"/></button>{!activity.answer_exposed&&<button type="button" disabled={busy} onClick={()=>void send("reveal",{mode:"answer"})} className="min-h-12 text-sm text-olive-700 underline underline-offset-4 dark:text-olive-300">直接看完整答案</button>}</div></div>}
      {activity?.explanation&&<div className="mt-7"><p className="text-xs font-medium tracking-wider text-olive-700 dark:text-olive-300">我的解释 · 已保存原文</p><p className="mt-2 whitespace-pre-wrap leading-7">{activity.explanation.text}</p></div>}
      {activity?.exact_check&&<div className="mt-8 rounded-2xl border border-dai-500/25 bg-dai-500/5 p-5 sm:p-6"><p className="text-xs font-medium tracking-wider text-dai-700 dark:text-dai-300">精确代数核对 · 与数值回放分开</p><ol className="mt-3 space-y-2 text-sm leading-7">{activity.exact_check.steps.map(step=><li key={step}>{step}</li>)}</ol><p className="mt-3 text-sm leading-7">{activity.exact_check.conclusion}</p><p className="mt-3 text-xs text-[var(--text-muted)]">{activity.exact_check.scope}</p></div>}
      {run&&activity?.explanation&&activity.prediction&&<div className="mt-8 border-t border-[var(--border-subtle)] pt-6"><h3 className="font-title text-xl font-semibold">修订刚才的观点</h3><p className="mt-2 text-sm text-[var(--text-secondary)]">原预测保留在上方。修订会作为新版本保存，不覆盖它。</p><label htmlFor="newton-revision" className="sr-only">修订后的观点</label><textarea id="newton-revision" rows={3} maxLength={2000} value={revision} onChange={e=>setRevision(e.target.value)} placeholder="现在我认为……；还需要确认……" className={`${learningInput} mt-4`}/><button type="button" disabled={busy||!revision.trim()} onClick={()=>void send("revise",{run_id:run.id,input_hash:run.input_hash,text:revision.trim()})} className={`${button} mt-4`}>保存修订<ArrowRight aria-hidden="true" className="size-4"/></button>{activity.revisions.length>0&&<ol className="mt-6 space-y-3">{activity.revisions.map((item,index)=><li key={item.request_id} className="rounded-xl border border-[var(--border-subtle)] p-4"><span className="text-xs text-[var(--text-muted)]">第 {index+1} 次修订</span><p className="mt-2 whitespace-pre-wrap leading-7">{item.text}</p></li>)}</ol>}</div>}
      {activity?.prediction_choice==="skipped"&&run&&<p className="mt-6 text-sm leading-6 text-[var(--text-secondary)]">你选择了直接看答案。本次只记录参考帮助曝光，不代表不会，也不计独立完成。</p>}
      {run&&<div className="mt-8 flex flex-wrap gap-x-6 gap-y-3 border-t border-[var(--border-subtle)] pt-5 text-sm"><button type="button" disabled={!activity?.context_current} onClick={()=>onDiscuss(run,0)} className="min-h-11 text-olive-700 underline underline-offset-4 disabled:opacity-45 dark:text-olive-300">带着这次实验问小珞 →</button><Link href="/study" className="inline-flex min-h-11 items-center text-olive-700 underline underline-offset-4 dark:text-olive-300">去做自己的求根练习 →</Link></div>}
    </div>
  </section>;
}
