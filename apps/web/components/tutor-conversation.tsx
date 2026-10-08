"use client";
import {useEffect, useRef, useState} from "react";
import {Loader2, Send, Square, RotateCcw} from "lucide-react";
import {MathMessage} from "./math-message";
import {messageStatus} from "@/lib/message-status";
import type {TutorMode} from "@/lib/api";
import type {LabRun} from "@/lib/learning-api";
import type {LearningContextRef} from "@/lib/learning-context";
import {useTutorConversation} from "@/lib/use-tutor-conversation";

export function TutorConversation({sessionId, scope, subject, context, onSession, onLabSaved, draftKey, suggestions, placeholder, blocked=false}: {
  sessionId?: string; scope: string; subject: string; context?: LearningContextRef;
  onSession?: (id: string)=>void; onLabSaved?: (run: LabRun)=>void; draftKey?: string;
  suggestions: {label:string; message:string; mode?:TutorMode}[]; placeholder: string; blocked?: boolean;
}) {
  const chat=useTutorConversation({sessionId,scope,subject,context,onSession});
  const [draft,setDraft]=useState("");
  const [hydrated,setHydrated]=useState<string>();
  const currentScope=useRef(scope); currentScope.current=scope;
  const scroll=useRef<HTMLDivElement>(null), end=useRef<HTMLDivElement>(null);
  const follow=useRef(true);
  useEffect(()=>{
    setHydrated(undefined);
    try {setDraft(draftKey?localStorage.getItem(draftKey)??"":"");} catch {setDraft("");}
    setHydrated(draftKey);
  },[draftKey]);
  useEffect(()=>{if(hydrated===draftKey && draftKey) localStorage.setItem(draftKey,draft);},[draft,draftKey,hydrated]);
  useEffect(()=>{if(follow.current) end.current?.scrollIntoView({behavior:"instant",block:"nearest"});},[chat.messages]);
  const unavailable=blocked||chat.loading||chat.busy||!!chat.error;
  async function submit(value: string, mode?: TutorMode) {
    if (unavailable || !value.trim()) return;
    const previous=draft, submittedScope=scope; setDraft(""); follow.current=true;
    const finished=await chat.submit(value,mode);
    if (!finished && currentScope.current===submittedScope) setDraft(current=>current||previous);
  }
  return <div className="flex h-full min-h-0 flex-col text-[var(--text-primary)]">
    <div ref={scroll} onScroll={()=>{const el=scroll.current;if(el)follow.current=el.scrollHeight-el.scrollTop-el.clientHeight<100;}} className="min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain px-4 py-5">
      {chat.loading?<p role="status" className="flex items-center gap-2 text-sm text-[var(--text-secondary)]"><Loader2 aria-hidden="true" className="size-4 animate-spin"/>正在恢复讨论…</p>:chat.messages.length===0?<div className="py-5"><p className="font-serif text-xl leading-8">从你想弄清的那一步开始。</p><p className="mt-3 text-sm leading-7 text-[var(--text-secondary)]">{context?.kind==="code_static"?"小珞会读取已保存代码与静态提示，说明原因和无法判断的部分。代码不会执行。":context?.kind==="reading"?"小珞会读取当前选段，区分原文、条件补充与不能确定的内容。":context?"小珞会读取已保存的真实轨迹。你可以先问原因，再回实验台验证自己的想法。":"围绕当前笔记提问，或从下面的建议开始讨论。"}</p></div>:chat.messages.map(m=><MathMessage key={m.id} content={m.content} role={m.role} sessionId={chat.sessionId}
        isThinking={m.status==="thinking"} isGenerating={chat.busy && (m.status==="thinking"||m.status==="typing")}
        isIncomplete={m.status==="error"||!!m.learning_meta?.error} rootDiagnosis={m.learning_meta?.root_diagnosis}
        status={m.role==="assistant" && m.status!=="thinking" ? messageStatus(m.learning_meta) : undefined}
        thinkingChain={m.thinkingChain} thinkingSummary={m.thinking_summary} thinkingElapsedMs={m.thinking_elapsed_ms}
        answerGuard={m.learning_meta?.answer_guard} agentRun={m.learning_meta?.agent_run} learningMeta={m.learning_meta}
        messageId={m.id} learningContext={context} actionsDisabled={blocked||chat.busy} onLabSaved={onLabSaved}/>)}
      <div ref={end}/>
    </div>
    <div className="shrink-0 space-y-3 border-t border-[var(--border-subtle)] bg-[var(--bg-card)] p-4">
      {chat.error && <div role="alert" className="text-sm leading-6 text-cinnabar-700 dark:text-cinnabar-300">{chat.error}<button type="button" className="ml-2 inline-flex min-h-12 items-center gap-1 underline" onClick={()=>chat.clearError()}><RotateCcw aria-hidden="true" className="size-3"/>重试</button></div>}
      <div className="flex flex-wrap gap-2">{suggestions.map(item=><button key={item.label} disabled={unavailable} onClick={()=>void submit(item.message,item.mode)} className="min-h-12 rounded-lg border border-[var(--border-primary)] px-3 text-sm text-[var(--text-secondary)] transition-colors hover:border-olive-500/40 hover:bg-olive-500/5 focus-visible:outline-2 focus-visible:outline-olive-600 disabled:opacity-45">{item.label}</button>)}</div>
      <form onSubmit={e=>{e.preventDefault();void submit(draft);}} className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] p-3 transition-colors focus-within:border-olive-600">
        <label htmlFor={`chat-input-${scope.replace(/[^a-zA-Z0-9_-]/g,"-")}`} className="sr-only">向小珞提问</label>
        <textarea id={`chat-input-${scope.replace(/[^a-zA-Z0-9_-]/g,"-")}`} rows={2} maxLength={10000} value={draft} onChange={e=>setDraft(e.target.value)} disabled={blocked||chat.loading} placeholder={placeholder} className="w-full resize-none bg-transparent text-base leading-7 outline-none placeholder:text-[var(--text-muted)]"/>
        <div className="mt-2 flex items-center justify-between gap-2"><span className="text-xs text-[var(--text-muted)]">{context?.kind==="code_static"?"围绕已保存代码 · 未执行":context?.kind==="reading"?"围绕当前原文选段":context?"围绕当前参考实验":"小珞 · AI 助教"}</span>{chat.busy?<button type="button" onClick={chat.cancel} className="flex min-h-12 min-w-12 items-center justify-center gap-2 rounded-lg border border-[var(--border-primary)] px-3 text-sm"><Square aria-hidden="true" className="size-3"/>停止</button>:<button type="submit" aria-label="发送提问" disabled={unavailable||!draft.trim()} className="flex size-12 items-center justify-center rounded-lg bg-olive-700 text-paper-50 transition-colors hover:bg-olive-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-olive-600 disabled:opacity-40"><Send aria-hidden="true" className="size-4"/></button>}</div>
      </form>
    </div>
  </div>;
}
