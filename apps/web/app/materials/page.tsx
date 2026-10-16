"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import {LearningShell,learningButtonSecondary,learningInput} from "@/components/learning/learning-shell";
import {DocumentUpload} from "@/components/document-upload";
import {listUploadedDocuments,type DocumentEntry} from "@/lib/api";
import {learningRequest,type ReadingDocument} from "@/lib/learning-api";
import {chatReferenceHref,readingSourceRef} from "@/lib/learning-context";
import {getCurrentUserId,getAuthHeaders,isAuthStorageKey} from "@/lib/demo-auth";
import {materialStatus} from "@/lib/material-policy";

export default function MaterialsPage(){
 const router=useRouter();const [items,setItems]=useState<DocumentEntry[]>([]),[reload,setReload]=useState(0),[loading,setLoading]=useState(true),[error,setError]=useState("");
 const [selected,setSelected]=useState(""),[doc,setDoc]=useState<ReadingDocument|null>(null),[section,setSection]=useState(""),[opening,setOpening]=useState(false),[selectionRefresh,setSelectionRefresh]=useState(0);
 useEffect(()=>{const changed=()=>{setItems([]);setSelected("");setDoc(null);setOpening(false);setError("");setReload(n=>n+1);};const storage=(e:StorageEvent)=>{if(isAuthStorageKey(e.key))changed();};window.addEventListener("luojia-auth-change",changed);window.addEventListener("storage",storage);return()=>{window.removeEventListener("luojia-auth-change",changed);window.removeEventListener("storage",storage);};},[]);
 useEffect(()=>{let active=true;const owner=getCurrentUserId(),credential=getAuthHeaders().Authorization;const valid=()=>active&&owner===getCurrentUserId()&&credential===getAuthHeaders().Authorization;setLoading(true);listUploadedDocuments().then(value=>{if(valid()){setItems(value);setError("");}}).catch(e=>{if(valid())setError(e instanceof Error?e.message:"资料读取失败。");}).finally(()=>{if(valid())setLoading(false);});return()=>{active=false;};},[reload]);
 useEffect(()=>{setDoc(null);if(!selected)return;let active=true;const owner=getCurrentUserId(),credential=getAuthHeaders().Authorization;const valid=()=>active&&owner===getCurrentUserId()&&credential===getAuthHeaders().Authorization;setOpening(true);learningRequest<ReadingDocument>(`/reading/documents/${encodeURIComponent(selected)}`).then(value=>{if(valid()){setDoc(value);setSection(value.sections[0]?.id||"");}}).catch(e=>{if(valid())setError(e instanceof Error?e.message:"无法读取原文。");}).finally(()=>{if(valid())setOpening(false);});return()=>{active=false;};},[selected,selectionRefresh]);
 const source=doc?.sections.find(s=>s.id===section);
 return <LearningShell title="我的资料" description="上传解析一次，在材料伴读、对话和笔记本中复用同一份原文。资料属于当前账号，不会自动进入官方课程图谱。" wide>
   <DocumentUpload onUploaded={id=>{setReload(n=>n+1);setSelected(id);}}/>
   <div className="my-5 flex items-center justify-between gap-3"><h2 className="font-serif text-xl">已保存资料</h2><button type="button" onClick={()=>setReload(n=>n+1)} className={learningButtonSecondary}>刷新资料列表</button></div>
   {error&&<p role="alert" className="mb-4 rounded-lg border border-cinnabar-600/30 p-4 text-sm leading-7">{error}</p>}
   {loading?<p role="status">正在读取资料…</p>:items.length?<div className="grid gap-4 md:grid-cols-2">{items.map(item=><article key={item.id} className="min-w-0 space-y-3 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-5">
     <h3 className="break-all font-serif text-xl">{item.filename}</h3><p className="text-xs text-[var(--text-secondary)]">{item.filename.includes(".")?item.filename.split(".").pop()?.toUpperCase():"文本"} · <time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString("zh-CN")}</time></p>
     <p className="text-sm">{materialStatus(item.parse_status)}</p><p className="text-xs leading-6 text-[var(--text-muted)]">用户提供材料，数学内容未经审核。</p>
     {item.parse_status!=="source_missing"&&<div className="flex flex-wrap gap-3 text-sm"><Link className="min-h-11 py-3 text-olive-700 dark:text-olive-300 underline" href={`/reading?document=${encodeURIComponent(item.id)}`}>打开材料伴读</Link><button type="button" className="min-h-11 underline" onClick={()=>{setError("");setSelected(item.id);setSelectionRefresh(n=>n+1);}}>选择用于对话</button><Link className="min-h-11 py-3 underline" href={`/notebook?document=${encodeURIComponent(item.id)}`}>用此资料生成笔记</Link></div>}
   </article>)}</div>:<p className="rounded-xl border border-dashed border-[var(--border-primary)] p-8 text-sm leading-7">还没有可用资料。请在上方导入；解析成功后可以先阅读，也可以选择对话或生成笔记。</p>}
   {(opening||doc)&&<section aria-label="选择资料引用范围" className="mt-6 space-y-4 rounded-xl border border-dai-600/30 bg-[var(--bg-card)] p-5"><h2 className="font-serif text-xl">{opening?"正在核对资料…":`引用：${doc?.filename}`}</h2>{doc&&<><label className="block text-sm">引用章节<select aria-label="引用章节" className={`${learningInput} mt-2`} value={section} onChange={e=>setSection(e.target.value)}>{doc.sections.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select></label><p className="whitespace-pre-wrap break-words text-sm leading-7">{Array.from(source?.quote||"").slice(0,300).join("")}</p><p className="text-xs leading-6 text-[var(--text-muted)]">仅引用此章节，最多 6000 字符。进入对话后可继续选段或清除引用；不会自动发送问题。</p><details className="text-xs"><summary className="min-h-11 cursor-pointer py-3">来源详情</summary><dl className="space-y-2 break-all"><dt>文档标识</dt><dd>{doc.id}</dd><dt>原文版本哈希</dt><dd>{doc.source_hash}</dd></dl></details><button type="button" disabled={!source} className={learningButtonSecondary} onClick={()=>{if(doc&&source)try{router.push(chatReferenceHref(readingSourceRef(doc,source.quote,source.id)));}catch(e){setError(e instanceof Error?e.message:"无法引用。");}}}>带此章节进入对话</button></>}</section>}
 </LearningShell>;
}
