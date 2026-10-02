"use client";
import {useEffect, useMemo, useState} from "react";
import {MathMarkdown} from "@/components/math-view";
import {learningRequest, stableRequestId} from "@/lib/learning-api";
import {getCurrentUserId} from "@/lib/demo-auth";
import {Notice, learningButton, learningInput} from "./learning-shell";
import {paragraphSpans} from "@/lib/learning-input";

type Explanation = {answer:string;status:string;citation:{quote:string;source_hash:string;start:number;end:number}};

export function ReadingExplanation({sourceId,sourceHash,sectionId,quote,onAnnotate}: {sourceId:string;sourceHash:string;sectionId:string|null;quote:string;onAnnotate?:(quote:string)=>void}) {
  const [question,setQuestion]=useState("");
  const [selection,setSelection]=useState("");
  const [answer,setAnswer]=useState<Explanation|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const spans=useMemo(()=>paragraphSpans(quote),[quote]);
  const draftKey=`reading-question:${getCurrentUserId()}:${sourceId}:${sectionId??"unit"}`;
  useEffect(()=>{setQuestion(localStorage.getItem(draftKey)??"");setSelection("");setAnswer(null);setError("");},[draftKey,sourceHash]);
  const span=spans.find(s=>`${s.start}:${s.end}`===selection)??spans[0];
  if (!quote.trim()) return null;
  return <section className="mt-8 border-t border-[var(--border-subtle)] pt-6"><h3 className="text-xl font-semibold">围绕原文提问</h3><form className="mt-4 space-y-4" onSubmit={async e=>{e.preventDefault();setBusy(true);setError("");try{
    const payload={source_id:sourceId,source_hash:sourceHash,section_id:sectionId,start:span.start,end:span.end,question};
    const request_id=stableRequestId(localStorage,`explanation-request:${getCurrentUserId()}:${sourceId}`,payload,()=>crypto.randomUUID());
    setAnswer(await learningRequest<Explanation>("/reading/explain",{...payload,request_id}));
  }catch(e){setError(e instanceof Error?e.message:"解释暂不可用");}finally{setBusy(false);}}}>
    <div><label htmlFor="readingSpan" className="mb-2 block">选择原文段落</label><select id="readingSpan" name="readingSpan" className={learningInput} value={`${span.start}:${span.end}`} onChange={e=>{setSelection(e.target.value);setAnswer(null);}}>{spans.map((s,i)=><option key={`${s.start}:${s.end}:${i}`} value={`${s.start}:${s.end}`}>{s.label}</option>)}</select></div>
    {onAnnotate && <button type="button" className="min-h-11 text-olive-700 dark:text-olive-300 underline" onClick={()=>onAnnotate(Array.from(quote).slice(span.start,span.end).join(""))}>把所选原文加入笔记草稿</button>}
    <div><label htmlFor="readingQuestion" className="mb-2 block">我的问题</label><textarea id="readingQuestion" name="readingQuestion" required maxLength={1000} rows={3} className={learningInput} value={question} onChange={e=>{setQuestion(e.target.value);localStorage.setItem(draftKey,e.target.value);}} placeholder="这一步用了什么条件？为什么不能直接推出收敛？"/></div>
    <button type="submit" disabled={busy || !question.trim()} className={learningButton}>{busy?"正在解释…":"解释这段原文"}</button><Notice error={error}/>
  </form>{answer && <div className="mt-5 rounded-lg bg-olive-600/5 p-4"><p className="mb-3 font-medium">{answer.status==="model_explanation"?"模型解释 · 尚未作数学验证":"原文与条件对照"}</p><MathMarkdown content={answer.answer} className="!text-base !leading-7"/><details className="mt-4"><summary className="cursor-pointer text-olive-700 dark:text-olive-300">回看实际引用的原文</summary><blockquote className="mt-3 border-l-2 border-olive-600 pl-4 whitespace-pre-wrap leading-7">{answer.citation.quote}</blockquote><p className="mt-3 text-base sm:text-xs text-[var(--text-muted)]">所选范围 {answer.citation.start}–{answer.citation.end} · {answer.citation.source_hash.slice(0,16)}</p></details></div>}</section>;
}
