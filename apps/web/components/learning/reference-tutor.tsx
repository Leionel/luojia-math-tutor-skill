"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {getCurrentUserId} from "@/lib/demo-auth";
import {learningRequest} from "@/lib/learning-api";
import {referenceChatKey,type LearningContextRef,type LearningTaskSnapshot} from "@/lib/learning-context";
import {ContextBanner} from "./context-banner";
import {TutorConversation} from "../tutor-conversation";
export function ReferenceTutor({reference}: {reference:LearningContextRef}){
 const identity=JSON.stringify(reference),owner=getCurrentUserId();
 const [snapshot,setSnapshot]=useState<LearningTaskSnapshot|null>(null),[session,setSession]=useState<string>(),[error,setError]=useState(""),[retry,setRetry]=useState(0);
 useEffect(()=>{
  const controller=new AbortController();const selected=JSON.parse(identity) as LearningContextRef;
  setSnapshot(null);setError("");
  try{setSession(localStorage.getItem(referenceChatKey(owner,selected))??undefined);}catch{setSession(undefined);}
  learningRequest<LearningTaskSnapshot>("/tutor/context",selected,controller.signal).then(s=>{if(!controller.signal.aborted&&owner===getCurrentUserId())setSnapshot(s);}).catch(e=>{if(!controller.signal.aborted)setError(e.message);});
  return()=>controller.abort();
 },[identity,owner,retry]);
 const bind=(id:string)=>{if(owner===getCurrentUserId()){try{localStorage.setItem(referenceChatKey(owner,reference),id);}catch{ /* Session remains usable without local persistence. */ }}};
 return <section aria-label="小珞引用伴读" className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-olive-500/25 bg-[var(--bg-card)]">
  <header className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border-subtle)] p-4"><h2 className="font-serif text-xl">小珞 · 来源伴读</h2><Link className="min-h-12 py-3 text-sm underline" href={`/chat?ref=${encodeURIComponent(identity)}`}>在完整聊天页讨论 ↗</Link></header>
  {error?<div className="p-4"><p role="alert">{error}</p><button type="button" className="min-h-12 underline" onClick={()=>setRetry(n=>n+1)}>重新读取来源</button></div>:!snapshot?<p role="status" className="p-4">正在核对来源…</p>:<><div className="p-3"><ContextBanner snapshot={snapshot}/><p className="mt-2 text-xs leading-6 text-[var(--text-muted)]">引用固定在已保存对象。换引用前的草稿会保留，请核对其中提到的步骤。</p></div><div className="min-h-0 flex-1"><TutorConversation sessionId={session} scope={`${owner}:${identity}`} subject="数值分析" context={snapshot.ref} onSession={bind} draftKey={`${referenceChatKey(owner,snapshot.ref)}:draft`}
   suggestions={reference.kind==="code_static"?[{label:"解释静态提示",message:"请只依据已保存代码范围和这条静态提示解释原因，指出尚未执行或不能判断的部分；不要把手动轨迹当程序输出。"}]:reference.kind==="reading"?[{label:"说明适用条件",message:"请仅依据当前选段，区分原文结论、必要条件与不能确认的补充。"}]:[{label:"解释这一步",message:"请依据当前引用的真实迭代，解释现象、停止依据与不能推出的结论。"}]}
   placeholder={reference.kind==="reading"?"这段原文，哪个条件还没读懂？":"想问当前引用的哪一步？"}/></div></>}
 </section>;
}
