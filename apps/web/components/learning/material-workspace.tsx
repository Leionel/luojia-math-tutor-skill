"use client";
import {useEffect,useRef,useState} from "react";
import Link from "next/link";
import {BookOpen,Upload,Quote,Loader2} from "lucide-react";
import {MathMarkdown} from "@/components/math-view";
import {learningRequest,type ReadingDocument,type ReadingUnit} from "@/lib/learning-api";
import {paragraphSpans} from "@/lib/learning-input";
import {selectionRange,type ReadingContextRef} from "@/lib/learning-context";
import {getCurrentUserId,getAuthHeaders} from "@/lib/demo-auth";
import {API_BASE} from "@/lib/api-base";
import {learningButton,learningButtonSecondary,learningInput,Notice} from "./learning-shell";

export function MaterialWorkspace({initialReference,onDiscuss,disabled=false}:{initialReference?:ReadingContextRef;onDiscuss?:(ref:ReadingContextRef,prompt:string)=>void;disabled?:boolean}){
  const owner=getCurrentUserId();const alive=useRef(true),generation=useRef(0),fileInput=useRef<HTMLInputElement>(null);
  const [units,setUnits]=useState<ReadingUnit[]>([]),[documents,setDocuments]=useState<{id:string;filename:string}[]>([]);
  const [unit,setUnit]=useState<ReadingUnit|null>(null),[doc,setDoc]=useState<ReadingDocument|null>(null),[section,setSection]=useState("0");
  const [loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState(""),[reload,setReload]=useState(0);
  const [range,setRange]=useState({start:0,end:0}),[question,setQuestion]=useState(""),[title,setTitle]=useState(""),[text,setText]=useState("");
  const identity=initialReference?`${initialReference.source_id}:${initialReference.source_hash}:${initialReference.section_id}:${initialReference.start}:${initialReference.end}`:"";
  useEffect(()=>{alive.current=true;const id=++generation.current;const controller=new AbortController();
    const valid=()=>alive.current&&generation.current===id&&owner===getCurrentUserId();
    setLoading(true);setError("");
    Promise.all([learningRequest<{units:ReadingUnit[]}>("/reading/units",undefined,controller.signal),learningRequest<{documents:{id:string;filename:string}[]}>("/reading/documents",undefined,controller.signal)])
      .then(async([u,d])=>{if(!valid())return;setUnits(u.units);setDocuments(d.documents);
        if(initialReference?.section_id!=null){const value=await learningRequest<ReadingDocument>(`/reading/documents/${encodeURIComponent(initialReference.source_id)}`,undefined,controller.signal);if(!valid())return;
          if(value.source_hash!==initialReference.source_hash)throw Error("材料版本已改变，请回原始来源重新选择。");setDoc(value);setUnit(null);setSection(initialReference.section_id);setRange({start:initialReference.start,end:initialReference.end});
        }else{const selected=u.units.find(x=>x.id===initialReference?.source_id)||u.units[0]||null;setUnit(selected);setDoc(null);setRange(initialReference?{start:initialReference.start,end:initialReference.end}:{start:0,end:Math.min(Array.from(selected?.quote||"").length,6000)});}
      }).catch(e=>{if(valid())setError(e instanceof Error?e.message:"暂时无法读取材料。");}).finally(()=>{if(valid())setLoading(false);});
    return()=>{alive.current=false;controller.abort();};
  // A changed validated reference must restore the exact source and character span.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[owner,identity,reload]);
  const source=doc?.sections.find(x=>x.id===section),quote=doc?(source?.quote||""):(unit?.quote||"");
  const chars=Array.from(quote),spans=paragraphSpans(quote).slice(1);
  const current=()=>alive.current&&owner===getCurrentUserId();
  async function loadDocument(id:string){const epoch=++generation.current;setBusy(true);setError("");try{const value=await learningRequest<ReadingDocument>(`/reading/documents/${encodeURIComponent(id)}`);if(!current()||generation.current!==epoch)return;setDoc(value);setUnit(null);setSection(value.sections[0]?.id||"0");setRange({start:0,end:Math.min(Array.from(value.sections[0]?.quote||"").length,6000)});}catch(e){if(current()&&generation.current===epoch)setError(e instanceof Error?e.message:"材料读取失败。");}finally{if(current()&&generation.current===epoch)setBusy(false);}}
  async function saveText(name:string,content:string){
    if(!name.trim()||!content.trim()||content.length>20000)throw Error("请填写材料名称和 1–20000 字符的正文。");
    const epoch=++generation.current;setBusy(true);setError("");try{const value=await learningRequest<ReadingDocument>("/reading/documents",{title:name.slice(0,120),text:content});if(!current()||generation.current!==epoch)return;
      setDocuments(v=>[{id:value.id,filename:value.filename},...v]);setDoc(value);setUnit(null);setSection(value.sections[0]?.id||"0");setRange({start:0,end:Math.min(Array.from(value.sections[0]?.quote||"").length,6000)});
    }finally{if(current()&&generation.current===epoch)setBusy(false);}
  }
  async function importFile(file:File){try{
    if(/\.(txt|md)$/i.test(file.name)){if(file.size>200*1024)throw Error("文本文件请控制在 200KB 内。");const content=new TextDecoder("utf-8",{fatal:true}).decode(await file.arrayBuffer());if(current())await saveText(file.name,content);}
    else{if(!/\.(pdf|docx?|pptx)$/i.test(file.name))throw Error("请选择 txt、md、PDF、Word 或 PowerPoint 文件。");setBusy(true);setError("");const body=new FormData();body.append("file",file);const result=await fetch(`${API_BASE}/api/uploads`,{method:"POST",headers:getAuthHeaders(),body});const value=await result.json();if(!current())return;if(!result.ok)throw Error(typeof value.detail==="string"?value.detail:"文档解析失败，请重试。");if(!value.document_id)throw Error("解析未返回可引用的文档，请重试。");setDocuments(v=>[{id:value.document_id,filename:file.name},...v]);await loadDocument(value.document_id);}
  }catch(e){if(current())setError(e instanceof Error?e.message:"导入失败，原材料仍保留。");}finally{if(current())setBusy(false);}}
  function bind(start=range.start,end=range.end){if(!onDiscuss)return;if(!Number.isInteger(start)||!Number.isInteger(end)||start<0||end<=start||end>chars.length||end-start>6000){setError("请选择 1–6000 字符，保留这一步需要的条件。");return;}
    const sourceId=doc?.id||unit?.id,hash=doc?.source_hash||unit?.source_hash;if(!sourceId||!hash)return;
    onDiscuss({kind:"reading",source_id:sourceId,source_hash:hash,section_id:doc?section:null,start,end,graph_revision:doc?null:unit!.graph_revision},question.trim());
  }
  return <div className="space-y-5 p-4 sm:p-5"><div className="flex items-center justify-between gap-3"><div><h2 className="font-serif text-xl">带着原文，与小珞讨论</h2><p className="mt-1 text-xs leading-6 text-[var(--text-muted)]">选择来源和选段，再把引用带入当前对话。</p></div><BookOpen className="size-6 shrink-0 text-dai-600"/></div>
    <Notice error={error}/>{loading?<p role="status" className="flex items-center gap-2 text-sm"><Loader2 className="size-4 animate-spin"/>正在读取你的材料…</p>:<>
      <label className="block text-sm">选择课程材料或自己的文档<select aria-label="选择伴读材料" disabled={busy||disabled} value={doc?`doc:${doc.id}`:unit?`unit:${unit.id}`:""} className={`${learningInput} mt-2`} onChange={e=>{if(e.target.value.startsWith("doc:"))void loadDocument(e.target.value.slice(4));else{generation.current++;setDoc(null);const selected=units.find(u=>u.id===e.target.value.slice(5))||null;setUnit(selected);setRange({start:0,end:Math.min(Array.from(selected?.quote||"").length,6000)});setError("");}}}>
        {!unit&&!doc&&<option value="">请选择材料</option>}<optgroup label="课程整理材料">{units.map(u=><option key={u.id} value={`unit:${u.id}`}>{u.title}</option>)}</optgroup><optgroup label="我的材料">{documents.map(d=><option key={d.id} value={`doc:${d.id}`}>{d.filename}</option>)}</optgroup></select></label>
      <details className="rounded-xl border border-[var(--border-primary)] p-3"><summary className="min-h-11 cursor-pointer py-2 text-sm font-medium">添加自己的材料</summary><p className="mt-2 text-xs leading-6 text-[var(--text-muted)]">文本可直接保存；PDF、Word 和 PowerPoint 使用现有文档解析服务。登录后保存到个人材料。</p><input ref={fileInput} type="file" accept=".txt,.md,.pdf,.doc,.docx,.pptx" aria-label="导入伴读材料" className="mt-3 w-full text-sm" disabled={busy||disabled} onChange={e=>{const file=e.target.files?.[0];if(file)void importFile(file);e.target.value="";}}/>
        <form className="mt-4 space-y-3" onSubmit={e=>{e.preventDefault();void saveText(title,text).catch(e=>{if(current())setError(e instanceof Error?e.message:"保存失败，输入仍保留。");});}}><label className="block text-sm">材料名称<input maxLength={120} value={title} onChange={e=>setTitle(e.target.value)} className={`${learningInput} mt-1`} disabled={busy||disabled}/></label><label className="block text-sm">粘贴原文<textarea maxLength={20000} rows={5} value={text} onChange={e=>setText(e.target.value)} className={`${learningInput} mt-1`} disabled={busy||disabled}/></label><button type="submit" disabled={busy||disabled||!title.trim()||!text.trim()} className={learningButtonSecondary}><Upload className="size-4"/>{busy?"正在保存…":"保存为新的材料"}</button></form></details>
      {doc&&<label className="block text-sm">原文章节<select aria-label="选择原文章节" className={`${learningInput} mt-1`} value={section} disabled={busy||disabled} onChange={e=>{setSection(e.target.value);const s=doc.sections.find(s=>s.id===e.target.value);setRange({start:0,end:Math.min(Array.from(s?.quote||"").length,6000)});}}>{doc.sections.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select></label>}
      {busy?<p role="status" className="text-sm">正在读取或保存材料，请稍候…</p>:quote?<section aria-label="伴读原文" className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-4"><p className="mb-4 text-xs leading-6 text-[var(--text-muted)]">{doc?"用户提供的原文 · 内容未经数学审核":"课程整理材料 · 非教材逐字引文"}</p>{spans.map((s,i)=><div key={`${s.start}:${s.end}`} className="border-t border-[var(--border-subtle)] py-4 first:border-0 first:pt-0"><MathMarkdown content={chars.slice(s.start,s.end).join("")} className="text-sm leading-8"/><button type="button" disabled={disabled} className="mt-2 inline-flex min-h-11 items-center gap-2 text-xs text-dai-700 dark:text-dai-300 underline disabled:opacity-50" onClick={()=>{setRange({start:s.start,end:s.end});bind(s.start,s.end);}}><Quote className="size-3.5"/>引用第 {i+1} 段到对话</button></div>)}<details className="mt-2"><summary className="min-h-11 cursor-pointer py-2 text-sm">精确选择原文中的文字</summary><label className="mt-2 block text-sm">拖选要引用的原文<textarea aria-label="精确选择原文" readOnly value={quote} rows={7} className={`${learningInput} mt-2`} onSelect={e=>{const el=e.currentTarget;if(el.selectionEnd>el.selectionStart)setRange(selectionRange(quote,el.selectionStart,el.selectionEnd));}}/></label></details>
        <div className="mt-3 border-t border-[var(--border-subtle)] pt-3"><p className="text-xs text-[var(--text-muted)]">当前选段：字符 {range.start}–{range.end}</p><blockquote className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words border-l-2 border-dai-500 pl-3 text-sm leading-7">{chars.slice(range.start,range.end).join("")}</blockquote><label className="mt-4 block text-sm">想问什么？（可选）<textarea value={question} maxLength={1000} onChange={e=>setQuestion(e.target.value)} rows={2} className={`${learningInput} mt-1`} placeholder="也可以先带入引用，再在对话框里组织问题。"/></label><button type="button" disabled={busy||disabled} onClick={()=>bind()} className={`${learningButton} mt-3`}>引用选段到对话</button><p className="mt-2 text-xs leading-6 text-[var(--text-muted)]">先核对来源，再由你发送消息。更换材料不会改写已发送消息的引用。</p></div></section>:<p className="text-sm leading-7">还没有可读材料，可以添加自己的讲义、题目或解答。</p>}
      <div className="flex flex-wrap items-center justify-between gap-3"><button type="button" disabled={busy} onClick={()=>setReload(n=>n+1)} className="min-h-11 text-sm underline">重新读取材料列表</button><Link href="/reading" className="min-h-11 py-3 text-sm text-olive-700 dark:text-olive-300 underline">打开完整材料伴读 →</Link></div>
    </>}
  </div>;
}
