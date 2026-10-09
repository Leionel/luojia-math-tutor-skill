"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {learningRequest,type TeachBack} from "@/lib/learning-api";
import {teachBackContextRef} from "@/lib/learning-context";

const judgments:Record<string,string>={supported:"模型认为有对应解释",needs_followup:"仍需补充",contradiction:"模型发现可能矛盾",unknown:"模型尚不能判断"};
export function TeachBackEvidence({saved,focusedCondition}:{saved:TeachBack;focusedCondition?:string|null}){
 const [span,setSpan]=useState<{start:number;end:number}|null>(null),[previous,setPrevious]=useState<TeachBack|null>(null),[error,setError]=useState("");
 useEffect(()=>{setPrevious(null);setError("");setSpan(null);if(!saved.parent_id)return;const controller=new AbortController();learningRequest<TeachBack>(`/teach-back/submissions/${encodeURIComponent(saved.parent_id)}`,undefined,controller.signal).then(setPrevious).catch(()=>{if(!controller.signal.aborted)setError("上一版暂不可用，本版原话仍保留。");});return()=>controller.abort();},[saved.id,saved.parent_id]);
 const chars=Array.from(saved.text);
 const focus=saved.conditions.find(c=>c.model_evidence?["contradiction","unknown","needs_followup"].includes(c.model_evidence.judgment):c.status==="needs_followup");
 return <div className="mt-5 rounded-xl border border-[var(--border-subtle)] p-4">
  <h3 className="font-semibold">原句与评语的依据</h3><p className="mt-2 text-sm leading-7">{saved.evidence_version?"原句位置已绑定":"历史记录未保存原句位置"} · 条件卡为开发参考；原句定位与模型意见均不证明已掌握。</p>
  {focus&&<p className="mt-3 leading-7">先补这一点：{focus.model_evidence?.followup??focus.followup}</p>}
  <ul className="mt-3 space-y-4">{saved.conditions.map(c=><li id={`condition-${c.condition_id}`} key={c.condition_id} className={focusedCondition===c.condition_id?"rounded-lg border border-olive-500/40 bg-olive-500/5 p-3":""}><p className="font-medium">{c.condition}</p>{!c.student_quote&&<p className="mt-2 text-sm">尚未提供对应原句，可补充后保存新版本。</p>}{c.student_quote&&!c.student_spans&&<blockquote className="mt-2 border-l-2 border-olive-600 pl-3">{c.student_quote}</blockquote>}{c.student_spans?.map((s,i)=><button key={`${s.start}:${s.end}`} type="button" onClick={()=>setSpan(s)} className="mr-3 min-h-12 text-olive-700 underline dark:text-olive-300">定位原句 {c.student_spans!.length>1?i+1:""}（字符 {s.start}–{s.end}）</button>)}{c.model_evidence&&<><p className="mt-1 text-sm">{judgments[c.model_evidence.judgment]} · 未核验</p><p className="mt-2 leading-7">{c.model_evidence.note}</p>{c.model_evidence.evidence&&<button type="button" className="min-h-12 underline" onClick={()=>setSpan(c.model_evidence!.evidence!)}>核对评语所引原话（{c.model_evidence.evidence.start}–{c.model_evidence.evidence.end}）</button>}</>}{saved.evidence_version==="teachback-evidence-v1"&&<Link href={`/chat?ref=${encodeURIComponent(JSON.stringify(teachBackContextRef(saved,c.condition_id)))}`} className="mt-2 inline-flex min-h-11 items-center text-sm text-olive-700 underline underline-offset-4 dark:text-olive-300">带着这项条件问小珞 →</Link>}</li>)}</ul>
  <h4 className="mt-4 font-medium">本次已保存原话</h4><p className="mt-2 whitespace-pre-wrap break-words leading-7">{span?<>{chars.slice(0,span.start).join("")}<mark className="bg-ochre-500/25 text-inherit">{chars.slice(span.start,span.end).join("")}</mark>{chars.slice(span.end).join("")}</>:saved.text}</p>
  {saved.parent_id&&<details className="mt-4"><summary className="min-h-12 cursor-pointer py-3">对照补充前后的原话</summary>{error?<p role="alert">{error}</p>:!previous?<p role="status">正在读取上一版…</p>:<div className="grid gap-4 lg:grid-cols-2"><div><h4>上一版（保留）</h4><p className="mt-2 whitespace-pre-wrap break-words leading-7">{previous.text}</p></div><div><h4>本版</h4><p className="mt-2 whitespace-pre-wrap break-words leading-7">{saved.text}</p></div></div>}</details>}
 </div>;
}
