"use client";
import Link from "next/link";
import {notesForSource} from "@/lib/learning-input";
import {useEffect, useState} from "react";
import {MathMarkdown, MathView} from "@/components/math-view";
import {LearningShell, Notice, learningButton, learningInput, learningPanel} from "@/components/learning/learning-shell";
import {learningRequest, stableRequestId, type ReadingUnit, type ReadingDocument, type ReadingNote} from "@/lib/learning-api";
import {getCurrentUserId} from "@/lib/demo-auth";
import {ReadingDiscussion} from "@/components/learning/reading-discussion";
import {ReadingExplanation} from "@/components/learning/reading-explanation";

export default function ReadingPage() {
  const [units, setUnits] = useState<ReadingUnit[]>([]);
  const [selected, setSelected] = useState("NA_NEWTON");
  const [documentId, setDocumentId] = useState("");
  const [documents, setDocuments] = useState<{id:string;filename:string}[]>([]);
  const [doc, setDoc] = useState<ReadingDocument | null>(null);
  const [sectionId, setSectionId] = useState("0");
  const [notes, setNotes] = useState<ReadingNote[]>([]);
  const [note, setNote] = useState("");
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  useEffect(()=>{const unit = new URLSearchParams(window.location.search).get("unit"); if(unit) setSelected(unit);
    Promise.all([learningRequest<{units:ReadingUnit[]}>("/reading/units"),learningRequest<{notes:ReadingNote[]}>("/reading/notes"),learningRequest<{documents:{id:string;filename:string}[]}>("/reading/documents")]).then(async ([a,b,c])=>{
      setUnits(a.units);setNotes(b.notes);setDocuments(c.documents);
      const params=new URLSearchParams(window.location.search);
      const savedId=params.get("document");
      if(savedId){
        const value=await learningRequest<ReadingDocument>(`/reading/documents/${encodeURIComponent(savedId)}`);
        setDoc(value);setDocumentId(savedId);
        setSectionId(value.sections.some(s=>s.id===params.get("section")) ? params.get("section")! : value.sections[0]?.id??"0");
      }
    }).catch(e=>setError(e.message)).finally(()=>setLoading(false));
  },[]);
  const unit = units.find(u=>u.id===selected);
  const section = doc?.sections.find(s=>s.id===sectionId);
  const sourceId = doc?.id ?? unit?.id;
  const sourceHash = doc?.source_hash ?? unit?.source_hash;
  const visibleNotes=notesForSource(notes,sourceId,doc?sectionId:null);
  const draftKey = sourceId ? `reading-note:${getCurrentUserId()}:${sourceId}:${sectionId}` : null;
  useEffect(()=>{if(draftKey) setNote(localStorage.getItem(draftKey) ?? "");},[draftKey]);
  const act = async(action:()=>Promise<void>)=>{setError("");setBusy(true);try{await action();}catch(e){setError(e instanceof Error ? e.message : "请求失败");}finally{setBusy(false);}};
  return <LearningShell title="带着条件读教材" description="从课程摘录追溯公式与适用条件，也可以打开自己上传的教材原文。把疑问和来源一起留下。">
    <Notice error={error} />
    <div className="grid gap-8 lg:grid-cols-[260px_minmax(0,1fr)]">
      <aside><h2 className="mb-4 font-semibold">求根章节</h2><div className="flex flex-col gap-2">{units.map(u=><button type="button" key={u.id} className={`rounded-lg p-3 text-left text-base sm:text-sm ${!doc && selected===u.id ? "bg-olive-600/10 text-olive-700 dark:text-olive-300 font-semibold" : "hover:bg-[var(--bg-hover)]"}`} onClick={()=>{setDoc(null);setSelected(u.id);setFeedback("");window.history.replaceState(null,"",`/reading?unit=${encodeURIComponent(u.id)}`);}}>{u.title}</button>)}</div>
        <form className="mt-8 border-t border-[var(--border-subtle)] pt-5 space-y-3" onSubmit={e=>{e.preventDefault();act(async()=>{const value=await learningRequest<ReadingDocument>(`/reading/documents/${encodeURIComponent(documentId.trim())}`);setDoc(value);setSectionId(value.sections[0]?.id??"0");setFeedback("");window.history.replaceState(null,"",`/reading?document=${encodeURIComponent(value.id)}&section=${value.sections[0]?.id??"0"}`);});}}><label htmlFor="documentId" className="block font-semibold">我的教材</label><p className="text-base sm:text-sm leading-6 text-[var(--text-secondary)]">选择自己上传的材料，按原文章节阅读。</p><select id="documentId" name="documentId" required className={learningInput} value={documentId} onChange={e=>setDocumentId(e.target.value)}><option value="">选择已上传的教材</option>{documents.map(d=><option key={d.id} value={d.id}>{d.filename}</option>)}</select><button type="submit" disabled={busy} className={learningButton}>打开原文</button></form>
        {doc && <div className="mt-5"><label htmlFor="section" className="block mb-2">原文章节</label><select id="section" name="section" className={learningInput} value={sectionId} onChange={e=>{setSectionId(e.target.value);window.history.replaceState(null,"",`/reading?document=${encodeURIComponent(doc.id)}&section=${encodeURIComponent(e.target.value)}`);}}>{doc.sections.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select></div>}
      </aside>
      <section className="min-w-0">
        {loading ? <p role="status">正在加载课程来源…</p> : !(doc || unit) ? <p>暂没有可用的课程材料。</p> : <>
          <article className={learningPanel}><p className="mb-3 text-base sm:text-sm text-[var(--text-secondary)]">{doc ? `上传原文 · ${doc.filename}` : "课程知识包摘录 · 非教材原页"}</p><h2 className="mb-5 font-title text-2xl font-semibold">{doc ? section?.title : unit?.title}</h2><MathMarkdown content={doc ? section?.quote ?? "" : unit?.quote ?? ""} className="!text-base !leading-8"/>{!doc && unit?.latex && <div className="my-6 overflow-x-auto"><MathView math={unit.latex} display/></div>}
            <p className="mt-5 break-all text-base sm:text-xs text-[var(--text-muted)]">{doc && section ? `原文字符 ${section.start}–${section.end} · ` : ""}来源校验：{sourceHash?.slice(0,16)}</p>
          </article>
          {!doc && unit && <div className="mt-7"><h3 className="text-xl font-semibold">使用这条公式前</h3><ul className="mt-4 list-disc space-y-2 pl-5 leading-7">{unit.conditions.map(c=><li key={c}>{c}</li>)}</ul><p className="mt-3 text-base sm:text-sm text-[var(--text-muted)]">条件卡为开发版整理，用于对照阅读。</p><fieldset className="mt-6"><legend className="mb-3 font-medium">{unit.question}</legend><div className="flex flex-wrap gap-3">{unit.options.map((o,i)=><button type="button" key={o} disabled={busy} className="rounded-lg border border-[var(--border-subtle)] px-4 py-3 text-base sm:text-sm hover:bg-[var(--bg-hover)]" onClick={()=>act(async()=>{const result=await learningRequest<{reference_match:boolean;explanation:string}>(`/reading/units/${unit.id}/condition-attempts`,{option:i,source_hash:unit.source_hash});setFeedback(`${result.reference_match ? "与参考判断一致" : "再核对一下条件"}：${result.explanation}`);})}>{o}</button>)}</div></fieldset>{feedback && <p role="status" className="mt-4 rounded-lg bg-olive-600/5 p-4 leading-7">{feedback}</p>}</div>}
          {!doc && unit && <Link href={`/teach-back?unit=${encodeURIComponent(unit.id)}`} className="mt-6 inline-flex min-h-12 items-center text-olive-700 dark:text-olive-300 underline">我来解释这条条件 →</Link>}
          {sourceId && sourceHash && <ReadingExplanation sourceId={sourceId} sourceHash={sourceHash} sectionId={doc?sectionId:null} quote={doc?section?.quote??"":unit?.quote??""} onAnnotate={quote=>{
            const addition=`原文摘录：\n${quote}\n\n我的理解 / 疑问：\n`;
            const next=note?`${note}\n\n${addition}`:addition;
            if(next.length>4000){setError("加入后超过笔记的4000字符上限，请选择更短的段落或先保存当前笔记。");return;}
            setNote(next);if(draftKey)localStorage.setItem(draftKey,next);
            document.getElementById("note")?.focus();
          }}/>}
          {sourceId&&sourceHash&&<ReadingDiscussion sourceId={sourceId} sourceHash={sourceHash} sectionId={doc?sectionId:null} quote={doc?section?.quote??"":unit?.quote??""} graphRevision={doc?null:unit?.graph_revision??null} conditions={doc?[]:unit?.conditions??[]} conditionHash={doc?null:unit?.condition_hash??null}/>}
          <form className="mt-8 border-t border-[var(--border-subtle)] pt-6" onSubmit={e=>{e.preventDefault();act(async()=>{const saved=await learningRequest<ReadingNote>("/reading/notes",{request_id:stableRequestId(localStorage,`note-request:${getCurrentUserId()}:${sourceId}:${sectionId}`,{note,sourceHash},()=>crypto.randomUUID()),source_id:sourceId,source_hash:sourceHash,section_id:doc ? sectionId : null,content:note});setNotes(previous=>[...previous.filter(n=>n.id!==saved.id),saved]);setNote("");if(draftKey)localStorage.removeItem(draftKey);});}}><label htmlFor="note" className="block mb-3 text-xl font-semibold">留下一个问题或理解</label><textarea id="note" name="note" required maxLength={4000} rows={4} className={learningInput} value={note} onChange={e=>{setNote(e.target.value);if(draftKey)localStorage.setItem(draftKey,e.target.value);}} placeholder="这一步用了什么条件？为什么小残差还不够？"/><button type="submit" disabled={busy || !note.trim()} className={`${learningButton} mt-3`}>保存笔记与来源</button></form>
          {visibleNotes.length>0 && <div className="mt-7"><h3 className="font-semibold">本章节的伴读笔记</h3>{visibleNotes.map(n=><div key={n.id} className="border-b border-[var(--border-subtle)] py-4"><p className="whitespace-pre-wrap leading-7">{n.content}</p><time className="text-base sm:text-xs text-[var(--text-muted)]">{new Date(n.created_at).toLocaleString("zh-CN")}</time></div>)}</div>}
        </>}
      </section>
    </div>
  </LearningShell>;
}
