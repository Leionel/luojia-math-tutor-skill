"use client";
import {getCurrentUserId} from "@/lib/demo-auth";
import {ReferenceTutor} from "./reference-tutor";
import {codeContextRef,type CodeContextRef} from "@/lib/learning-context";
import {useEffect, useState} from "react";
import {learningRequest, type CodeSubmission} from "@/lib/learning-api";

export function SavedCodeReview({submission,edited}: {submission:CodeSubmission;edited:boolean}) {
  const [reference,setReference]=useState<CodeContextRef|null>(null);
  const selectionKey=`code-discussion:${getCurrentUserId()}:${submission.id}:${submission.code_hash}:${submission.static_rule_version??"legacy"}`;
  useEffect(()=>{try{const value=localStorage.getItem(selectionKey);if(value!==null)setReference(codeContextRef(submission,Number(value)));}catch{setReference(null);}},[selectionKey,submission]);
  const discuss=(index:number)=>{try{setReference(codeContextRef(submission,index));try{localStorage.setItem(selectionKey,String(index));}catch{ /* Locator persistence is optional. */ }}catch(e){setError(e instanceof Error?e.message:"引用不可用");}};
  const [previous,setPrevious]=useState<CodeSubmission|null>(null);
  const [error,setError]=useState("");
  const [line,setLine]=useState<number|null>(null);
  const [open,setOpen]=useState(false);
  useEffect(()=>{
    if(!submission.previous_id)return;
    const controller=new AbortController();
    learningRequest<CodeSubmission>(`/code-workshop/submissions/${encodeURIComponent(submission.previous_id)}`,undefined,controller.signal).then(setPrevious).catch(e=>{if(!controller.signal.aborted)setError(e instanceof Error?e.message:"前一版本暂不可用");});
    return ()=>controller.abort();
  },[submission.previous_id]);
  const locate=(number:number)=>{setOpen(true);setLine(number);};
  useEffect(()=>{if(open && line)document.getElementById(`saved-code-line-${line}`)?.scrollIntoView({block:"center"});},[open,line]);
  return <>
    {edited && <p role="status" className="mt-3 leading-7 text-ochre-700 dark:text-ochre-300">编辑区已有未提交的修改；下面的提示仍对应已保存版本。</p>}
    <p className="mt-3 text-sm">静态规则：{submission.static_rule_version??"历史版本未记录规则编号"} · 历史结果未重新计算</p>
    <ul className="mt-4 space-y-3">{submission.findings.length?submission.findings.map((f,i)=><li key={i} className="leading-7">{f.line && <button type="button" onClick={()=>locate(f.line!)} className="mr-2 min-h-11 text-olive-700 dark:text-olive-300 underline">定位已保存代码第 {f.line} 行</button>}{f.message}<button type="button" onClick={()=>discuss(i)} className="ml-3 min-h-12 text-olive-700 underline dark:text-olive-300">讨论这条提示</button></li>):<li className="leading-7">未触发当前有限规则；不能据此确认算法、终止性或一般正确性。</li>}</ul>
    {reference&&<div className="mt-5 h-[680px]"><ReferenceTutor reference={reference}/></div>}
    <details open={open} onToggle={e=>setOpen(e.currentTarget.open)} className="mt-5"><summary className="min-h-11 cursor-pointer font-medium">查看已保存代码与行号</summary><div className="mt-3 overflow-x-auto rounded-lg bg-[var(--bg-tertiary)] py-3 font-mono text-sm">{submission.code.split("\n").map((text,i)=><div key={i} id={`saved-code-line-${i+1}`} className={`flex min-w-max gap-4 px-4 leading-7 ${line===i+1?"bg-ochre-600/15":""}`}><span aria-hidden="true" className="w-8 shrink-0 text-right text-[var(--text-muted)]">{i+1}</span><code className="whitespace-pre">{text||" "}</code></div>)}</div></details>
    {submission.previous_id && <details className="mt-5"><summary className="min-h-11 cursor-pointer font-medium">并排核对上一版与本版代码</summary>{error?<p role="alert" className="mt-3">{error}</p>:!previous?<p role="status" className="mt-3">正在读取上一版原文…</p>:<div className="mt-3 grid min-w-0 gap-4 lg:grid-cols-2">{[{label:"上一版（已保存）",value:previous},{label:"本版（已保存）",value:submission}].map(item=><div key={item.label} className="min-w-0"><h4 className="mb-2 font-medium">{item.label}</h4><pre className="max-h-96 overflow-auto rounded-lg bg-[var(--bg-tertiary)] p-3 text-sm leading-7"><code>{item.value.code}</code></pre></div>)}</div>}</details>}
  </>;
}
