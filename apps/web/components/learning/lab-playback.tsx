"use client";
import {useEffect, useState} from "react";
import type {LabRun} from "@/lib/learning-api";

export function LabPlayback({run, comparison, onDiscussStep, concealFuture=false}: {run: LabRun; comparison?: LabRun; onDiscussStep?: (step:number)=>void; concealFuture?:boolean}) {
  const [step,setStep]=useState(0);
  const [playing,setPlaying]=useState(false);
  const last=run.rows.length-1;
  useEffect(()=>{
    if(!playing)return;
    if(step>=last){setPlaying(false);return;}
    const timer=setTimeout(()=>setStep(s=>Math.min(s+1,last)),850);
    const hidden=()=>{if(document.hidden)setPlaying(false);};
    document.addEventListener("visibilitychange",hidden);
    return ()=>{clearTimeout(timer);document.removeEventListener("visibilitychange",hidden);};
  },[playing,step,last]);
  if(last<0)return null;
  const row=run.rows[step];
  const runs=comparison?[run,comparison]:[run];
  const values=runs.flatMap(r=>r.rows.map(v=>v.x));
  const low=Math.min(...values),high=Math.max(...values),span=Math.max(high-low,1e-12);
  const maxK=Math.max(...runs.flatMap(r=>r.rows.map(v=>v.k)),1);
  const point=(v:LabRun["rows"][number])=>`${50+v.k/maxK*560},${175-(v.x-low)/span*150}`;
  const move=(n:number)=>{setPlaying(false);setStep(Math.max(0,Math.min(last,n)));};
  const button="min-h-12 rounded-lg border border-[var(--border-primary)] px-3 text-base sm:text-sm hover:bg-olive-600/10 disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-olive-600";
  return <section aria-label="逐步观察迭代" className="mt-6 rounded-xl bg-[var(--bg-tertiary)] p-4 sm:p-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold">拖动看一步，播放看趋势</h3><p className="font-mono text-base sm:text-sm">k = {row.k} / {run.rows[last].k}</p></div>
    <figure className="mt-3"><svg viewBox="0 0 640 220" role="img" aria-label={`迭代序列，横轴迭代次数、纵轴近似值；当前第${row.k}步，近似值${row.x.toPrecision(7)}`} className="w-full">
      <path d="M50 15V185H620" fill="none" stroke="currentColor" opacity=".3"/>
      <text x="5" y="25" fill="currentColor" fontSize="12">{high.toPrecision(4)}</text><text x="5" y="180" fill="currentColor" fontSize="12">{low.toPrecision(4)}</text><text x="48" y="207" fill="currentColor" fontSize="12">k=0</text><text x="560" y="207" fill="currentColor" fontSize="12">k={maxK}</text>
      {!concealFuture && <polyline points={run.rows.map(point).join(" ")} fill="none" stroke="currentColor" strokeWidth="2" opacity=".18" className="text-olive-600 dark:text-olive-400"/>}
      <polyline points={run.rows.slice(0,step+1).map(point).join(" ")} fill="none" stroke="currentColor" strokeWidth="2.5" className="text-olive-600 dark:text-olive-400"/>
      {comparison && <polyline points={comparison.rows.filter(v=>v.k<=row.k).map(point).join(" ")} fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="6 4" className="text-cinnabar-600 dark:text-cinnabar-300"/>}
      <line x1={50+row.k/maxK*560} x2={50+row.k/maxK*560} y1="15" y2="185" stroke="currentColor" strokeDasharray="3 5" opacity=".25"/>
      <circle cx={50+row.k/maxK*560} cy={175-(row.x-low)/span*150} r="5" fill="currentColor" className="text-olive-700 dark:text-olive-300"/>
    </svg><figcaption className="text-base sm:text-sm leading-6 text-[var(--text-secondary)]">实线：{concealFuture?"当前已回看的步骤":"本次轨迹"}；{concealFuture?"继续步进可查看后续计算。":"淡线：全部已算步骤。"}{comparison?"虚线：对照轨迹的相同步数。":""}图形趋势不替代收敛与误差判断。</figcaption></figure>
    <label htmlFor={`step-${run.id}`} className="mt-4 block text-base sm:text-sm">选择迭代步骤</label><input id={`step-${run.id}`} aria-valuetext={`第${row.k}步，近似值${row.x.toPrecision(7)}`} type="range" min={0} max={Math.max(last,1)} step={1} value={step} disabled={last===0} onChange={e=>move(Number(e.target.value))} className="h-12 w-full accent-olive-700"/>
    <div className="flex flex-wrap gap-2"><button type="button" className={button} disabled={step===0} onClick={()=>move(step-1)}>上一步</button><button type="button" className={button} disabled={last===0} onClick={()=>{if(playing)setPlaying(false);else{if(step===last)setStep(0);setPlaying(true);}}}>{playing?"暂停回放":step===last?"重新播放":"播放迭代"}</button><button type="button" className={button} disabled={step===last} onClick={()=>move(step+1)}>下一步</button><button type="button" className={button} disabled={step===last} onClick={()=>move(last)}>看最后一步</button></div>
    {onDiscussStep && <button type="button" onClick={()=>{setPlaying(false);onDiscussStep(row.k);}} className="mt-3 inline-flex min-h-12 items-center text-sm font-medium text-olive-700 underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-olive-600 dark:text-olive-300">问小珞：解释第 {row.k} 步 →</button>}
    <dl className="mt-4 grid grid-cols-2 gap-4 border-t border-[var(--border-primary)] pt-4 text-base sm:text-sm"><div><dt>近似值 xₖ</dt><dd className="mt-1 break-all font-mono">{row.x.toPrecision(9)}</dd></div><div><dt>残差 |f(xₖ)|</dt><dd className="mt-1 break-all font-mono">{Math.abs(row.fx).toExponential(4)}</dd></div><div><dt>相邻差</dt><dd className="mt-1 font-mono">{row.step?.toExponential(4)??"初值，无前一步"}</dd></div><div><dt>当前区间</dt><dd className="mt-1 break-words font-mono">{row.bracket?.map(v=>v.toPrecision(6)).join(" ~ ")??"此方法未逐步保存区间"}</dd></div></dl>
    <p className="mt-4 text-base sm:text-sm leading-7 text-[var(--text-secondary)]">{step===last?`到达已保存的末步。${run.stop_detail}；${run.diagnosis.summary}`:"当前在回放中间步骤。残差或相邻差变小，不能直接认定已达到根误差目标。"}</p>
  </section>;
}
