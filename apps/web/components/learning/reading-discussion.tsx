"use client";
import {useEffect,useState} from "react";
import {ReferenceTutor} from "./reference-tutor";
import {selectionRange,restoreReadingReference,type ReadingContextRef} from "@/lib/learning-context";
import {getCurrentUserId} from "@/lib/demo-auth";
import {learningButton,learningInput} from "./learning-shell";
export function ReadingDiscussion({sourceId,sourceHash,sectionId,quote,graphRevision}:{sourceId:string;sourceHash:string;sectionId:string|null;quote:string;graphRevision:string|null}){
 const owner=getCurrentUserId();
 const scope=`reading-selection:${owner}:${sourceId}:${sourceHash}:${sectionId}:${graphRevision}`;
 const [start,setStart]=useState(0),[end,setEnd]=useState(0),[reference,setReference]=useState<ReadingContextRef|null>(null),[error,setError]=useState("");
 useEffect(()=>{
  let restored:ReadingContextRef|null=null;
  try{restored=restoreReadingReference(localStorage.getItem(scope),{source_id:sourceId,source_hash:sourceHash,section_id:sectionId,graph_revision:graphRevision},Array.from(quote).length);}catch{ /* Storage is optional; server still validates every reference. */ }
  setStart(restored?.start??0);setEnd(restored?.end??Math.min(Array.from(quote).length,900));setReference(restored);setError("");
 },[scope,quote,sourceId,sourceHash,sectionId,graphRevision]);
 const bind=()=>{if(!Number.isInteger(start)||!Number.isInteger(end)||start<0||end<=start||end>Array.from(quote).length){setError("请选择原文章节内的有效字符范围。");return;}setError("");const selected:ReadingContextRef={kind:"reading",source_id:sourceId,source_hash:sourceHash,section_id:sectionId,start,end,graph_revision:graphRevision};setReference(selected);try{localStorage.setItem(scope,JSON.stringify(selected));}catch{ /* Discussion works without local persistence. */ }};
 return <section className="mt-8 border-t border-[var(--border-subtle)] pt-5"><h3 className="font-serif text-xl">选段与小珞讨论</h3><p className="mt-2 text-sm leading-7">在下方原文框拖选，或填写字符范围。点击讨论后引用固定；已有笔记与解释不受影响。</p>
  <label className="mt-3 block" htmlFor="reading-reference-selection">原文选择框</label><textarea id="reading-reference-selection" readOnly rows={5} value={quote} className={`${learningInput} mt-2`} onSelect={e=>{const el=e.currentTarget;if(el.selectionEnd>el.selectionStart){const range=selectionRange(quote,el.selectionStart,el.selectionEnd);setStart(range.start);setEnd(range.end);}}}/>
  <div className="mt-3 flex flex-wrap items-end gap-3"><label>起始字符<input type="number" min={0} value={start} onChange={e=>setStart(Number(e.target.value))} className={learningInput}/></label><label>结束字符<input type="number" min={1} value={end} onChange={e=>setEnd(Number(e.target.value))} className={learningInput}/></label><button type="button" className={learningButton} onClick={bind}>讨论字符 {start}–{end}</button></div>
  <p className="mt-2 text-sm">当前选择 {end-start} 个字符；过长来源由服务端拒绝，不会悄悄截掉条件。</p>{error&&<p role="alert">{error}</p>}
  {reference&&<div className="mt-4 h-[680px]"><ReferenceTutor reference={reference}/></div>}
 </section>;
}
