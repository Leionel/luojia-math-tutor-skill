"use client";
import {useEffect,useRef,useState} from "react";
import Link from "next/link";
import {generateDocumentNote,listUploadedDocuments,type DocumentEntry} from "@/lib/api";
import {learningRequest,type ReadingDocument} from "@/lib/learning-api";
import {getCurrentUserId,getAuthHeaders,isAuthStorageKey} from "@/lib/demo-auth";
import {DocumentUpload} from "./document-upload";

export function DocumentNoteUpload({withMistakes=false,description,onGenerated}: {withMistakes?:boolean;description:string;onGenerated:()=>void}) {
  const [documents,setDocuments]=useState<DocumentEntry[]>([]),[id,setId]=useState(""),[reload,setReload]=useState(0);
  const [busy,setBusy]=useState(false),[loading,setLoading]=useState(true),[error,setError]=useState(""),[message,setMessage]=useState("");
  const [importing,setImporting]=useState(false);const alive=useRef(true),epoch=useRef(0),initialApplied=useRef(false);
  useEffect(()=>{alive.current=true;const changed=()=>{epoch.current++;initialApplied.current=false;setDocuments([]);setId("");setBusy(false);setError("");setMessage("");setReload(n=>n+1);};const storage=(e:StorageEvent)=>{if(isAuthStorageKey(e.key))changed();};window.addEventListener("luojia-auth-change",changed);window.addEventListener("storage",storage);return()=>{alive.current=false;window.removeEventListener("luojia-auth-change",changed);window.removeEventListener("storage",storage);};},[]);
  useEffect(()=>{let active=true;const owner=getCurrentUserId(),credential=getAuthHeaders().Authorization;setLoading(true);listUploadedDocuments().then(value=>{if(active&&owner===getCurrentUserId()&&credential===getAuthHeaders().Authorization){setDocuments(value);const requested=new URLSearchParams(window.location.search).get("document");if(!initialApplied.current){initialApplied.current=true;if(requested&&value.some(x=>x.id===requested))setId(requested);}}}).catch(e=>{if(active)setError(e instanceof Error?e.message:"资料读取失败。");}).finally(()=>{if(active)setLoading(false);});return()=>{active=false;};},[reload]);
  async function generate(){if(!id||busy)return;const owner=getCurrentUserId(),credential=getAuthHeaders().Authorization,token=++epoch.current;const valid=()=>alive.current&&token===epoch.current&&owner===getCurrentUserId()&&credential===getAuthHeaders().Authorization;setBusy(true);setError("");setMessage("");try{const source=await learningRequest<ReadingDocument>(`/reading/documents/${encodeURIComponent(id)}`);if(!valid())return;await generateDocumentNote(owner,id,withMistakes,source.source_hash);if(valid()){setMessage("笔记已生成，来源与抽样范围已保存。");onGenerated();}}catch(e){if(valid())setError(`${e instanceof Error?e.message:"笔记生成失败。"} 已保存资料仍可继续阅读或引用。`);}finally{if(valid())setBusy(false);}}
  return <section aria-label="从已有资料生成笔记" className="space-y-3 rounded-xl border border-olive-600/20 p-4">
    <h2 className="text-sm font-semibold">{withMistakes?"基于已有资料辅助复习":"从已有资料生成笔记"}</h2><p className="text-xs leading-6 text-[var(--text-secondary)]">{description}</p>
    {loading?<p role="status" className="text-xs">正在读取资料…</p>:<><label className="block text-xs">选择资料<select aria-label="笔记来源资料" value={id} disabled={busy} onChange={e=>{setId(e.target.value);setMessage("");}} className="mt-2 min-h-11 w-full rounded-lg border border-[var(--border-primary)] bg-[var(--bg-input)] p-2 text-sm"><option value="">{documents.length?"选择已保存的资料":"还没有资料，请先导入"}</option>{documents.map(d=><option key={d.id} value={d.id} disabled={d.parse_status==="source_missing"}>{d.filename}{d.parse_status==="source_missing"?"（缺少原文）":""}</option>)}</select></label><button type="button" disabled={!id||busy} onClick={()=>void generate()} className="min-h-11 rounded-lg bg-olive-700 px-3 text-sm text-paper-50 disabled:opacity-50">{busy?"正在生成笔记…":"生成抽样学习笔记"}</button></>}
    <div className="flex flex-wrap gap-3 text-xs"><button type="button" disabled={busy} className="min-h-11 underline" onClick={()=>setImporting(x=>!x)}>+ 导入新资料</button><Link className="min-h-11 py-3 underline" href="/materials">管理我的资料</Link><button type="button" className="min-h-11 underline" onClick={()=>setReload(n=>n+1)}>刷新资料</button></div>
    {importing&&<DocumentUpload disabled={busy} onUploaded={newId=>{setId(newId);setReload(n=>n+1);setMessage("资料已保存；点击生成笔记后才会请求 AI。");}}/>}
    {error&&<p role="alert" className="text-xs leading-6 text-cinnabar-700 dark:text-cinnabar-300">{error}</p>}{message&&<p role="status" className="text-xs leading-6 text-olive-700 dark:text-olive-300">{message}</p>}
  </section>;
}
