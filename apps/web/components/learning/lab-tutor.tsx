"use client";
import Image from "next/image";
import Link from "next/link";
import {useEffect, useState} from "react";
import {ArrowUpRight, BookOpen, Loader2} from "lucide-react";
import {getCurrentUserId} from "@/lib/demo-auth";
import {learningRequest, type LabRun} from "@/lib/learning-api";
import {labChatKey, rootContextRef, type LearningTaskSnapshot} from "@/lib/learning-context";
import {TutorConversation} from "../tutor-conversation";

export function LabTutor({run, selectedStep, onSaved, onResetStep}: {run:LabRun; selectedStep:number|null; onSaved:(run:LabRun)=>void; onResetStep?:()=>void}) {
  const [snapshot,setSnapshot]=useState<LearningTaskSnapshot|null>(null);
  const [session,setSession]=useState<string>();
  const [error,setError]=useState("");
  const [retry,setRetry]=useState(0);
  const scope=`${run.id}:${run.input_hash}:${run.runner_version}:${run.graph_revision}:${selectedStep}`;
  useEffect(()=>{
    const owner=getCurrentUserId(), controller=new AbortController();
    setSnapshot(null); setError("");
    try {
      setSession(localStorage.getItem(labChatKey(owner,run.id))??undefined);
      learningRequest<LearningTaskSnapshot>("/tutor/context",rootContextRef(run,selectedStep),controller.signal)
        .then(next=>{if(!controller.signal.aborted && owner===getCurrentUserId())setSnapshot(next);})
        .catch(e=>{if(!controller.signal.aborted)setError(e.message);});
    } catch(e) {setError(e instanceof Error?e.message:"实验引用不可用");}
    return ()=>controller.abort();
  },[scope,retry,run,selectedStep]);
  const bindSession=(id:string)=>{
    // The controller already checks the owner and context before this callback.
    localStorage.setItem(labChatKey(getCurrentUserId(),run.id),id);
    // Keep the prop stable while streaming; assigning it would trigger a reload.
  };
  const save=(next:LabRun)=>{
    const id=localStorage.getItem(labChatKey(getCurrentUserId(),run.id));
    if(id)localStorage.setItem(labChatKey(getCurrentUserId(),next.id),id);
    onSaved(next);
  };
  return <aside aria-label="小珞实验助教" className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-olive-500/20 bg-[var(--bg-card)] shadow-[0_18px_50px_-32px_rgba(53,64,44,.35)]">
    <div className="flex shrink-0 items-center gap-3 border-b border-[var(--border-subtle)] px-5 py-5">
      <div className="size-12 overflow-hidden rounded-full border border-olive-500/25 bg-paper-100"><Image src="/brand/xiaoluo.png" width={128} height={128} sizes="128px" alt="小珞" className="h-full w-full origin-[54%_16%] scale-[2.6] object-cover object-top"/></div>
      <div className="flex-1"><p className="font-serif text-xl font-semibold">小珞 · 实验伴学</p><p className="mt-1 text-xs tracking-wide text-[var(--text-muted)]">陪你看清每一步的依据</p></div>
      <Link aria-label="在完整聊天页讨论当前实验" href={`/chat?lab=${encodeURIComponent(run.id)}${selectedStep===null?"":`&step=${selectedStep}`}`} className="flex size-12 items-center justify-center rounded-lg text-[var(--text-secondary)] hover:bg-olive-500/5 focus-visible:outline-2 focus-visible:outline-olive-600"><ArrowUpRight aria-hidden="true" className="size-5"/></Link>
    </div>
    <div className="shrink-0 border-b border-olive-500/10 bg-olive-500/5 px-5 py-4">
      <p className="flex items-center gap-2 text-sm font-medium text-olive-800 dark:text-olive-200"><BookOpen aria-hidden="true" className="size-4"/>当前引用 · {selectedStep===null?"完整实验":`第 ${selectedStep} 步`}</p>
      <p className="mt-2 break-all font-mono text-sm leading-6">f(x) = {run.parameters.function} · x₀={run.parameters.initial_value}</p>
      <p className="mt-2 text-xs leading-6 text-[var(--text-muted)]">已保存轨迹 · {run.rows.length} 步 · 参考帮助</p>
      {selectedStep!==null && onResetStep && <button type="button" onClick={onResetStep} className="mt-1 min-h-12 text-sm text-olive-700 underline underline-offset-4 dark:text-olive-300">讨论整个实验</button>}
    </div>
    {error?<div className="p-5"><p role="alert" className="text-sm leading-7 text-cinnabar-700 dark:text-cinnabar-300">{error}</p><button type="button" onClick={()=>setRetry(n=>n+1)} className="mt-3 min-h-12 text-sm underline">重新读取实验</button></div>:!snapshot?<p role="status" className="flex items-center gap-2 p-5 text-sm text-[var(--text-secondary)]"><Loader2 aria-hidden="true" className="size-4 animate-spin"/>正在核对实验版本…</p>:<div className="min-h-0 flex-1">
      <TutorConversation sessionId={session} scope={scope} subject="数值分析" context={snapshot.ref} onSession={bindSession} onLabSaved={save}
        draftKey={`lab-chat-draft:${getCurrentUserId()}:${run.id}`} placeholder={selectedStep===null?"这次迭代，哪一步让你困惑？":`想问第 ${selectedStep} 步的什么现象？`}
        suggestions={[{label:"解释这步",message:selectedStep===null?"请根据这次实验的真实轨迹解释主要现象，并指出停止依据和局限。":`请解释已保存轨迹中的第 ${selectedStep} 步，它为什么会得到这个近似值？`},
          {label:"调整初值",message:"我想改变初值做对照。请解释应该观察什么，然后让我调整参数预览。"}]}/>
    </div>}
  </aside>;
}
