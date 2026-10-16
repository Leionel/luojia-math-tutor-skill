"use client";
import {useState,useEffect,useRef} from "react";
import {useRouter} from "next/navigation";
import {Search,X,MessageCircle,ArrowRight,Loader2} from "lucide-react";
import {searchGlobal,listSessions,type GlobalSearchResultItem,type Session} from "@/lib/api";
import {getCurrentUserId,getAuthHeaders,isAuthStorageKey} from "@/lib/demo-auth";
import {MathMarkdown} from "./math-view";
const CATEGORIES=[{key:"all",label:"全部"},{key:"conversations",label:"历史对话"},{key:"curriculum",label:"教材定理"},{key:"notes",label:"随堂笔记"},{key:"mistakes",label:"错题复盘"}];
interface GlobalSearchModalProps {isOpen:boolean;onClose:()=>void;onSelectResult?:(text:string)=>void;onSelectSession?:(id:string)=>void;}
export function GlobalSearchModal({isOpen,onClose,onSelectResult,onSelectSession}:GlobalSearchModalProps){
 const router=useRouter();const [query,setQuery]=useState(""),[activeCategory,setActiveCategory]=useState("all");
 const [results,setResults]=useState<GlobalSearchResultItem[]>([]),[conversations,setConversations]=useState<Session[]>([]);
 const [loading,setLoading]=useState(false),[searched,setSearched]=useState(false),[errors,setErrors]=useState<string[]>([]);
 const inputRef=useRef<HTMLInputElement>(null),dialog=useRef<HTMLDivElement>(null),close=useRef(onClose);close.current=onClose;
 useEffect(()=>{
   if(!isOpen){setQuery("");setResults([]);setConversations([]);setErrors([]);setSearched(false);return;}
   const previous=document.activeElement as HTMLElement|null,overflow=document.body.style.overflow;
   document.body.style.overflow="hidden";inputRef.current?.focus();
   const changed=()=>{setResults([]);setConversations([]);setQuery("");close.current();};
   const storage=(e:StorageEvent)=>{if(isAuthStorageKey(e.key))changed();};
   const key=(e:KeyboardEvent)=>{
     if(e.key==="Escape"&&!e.isComposing){e.preventDefault();close.current();}
     if(e.key!=="Tab")return;
     const items=Array.from(dialog.current?.querySelectorAll<HTMLElement>('input,button:not(:disabled),a[href]')??[]).filter(x=>x.getClientRects().length);
     const first=items[0],last=items[items.length-1];
     if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}
   };
   document.addEventListener("keydown",key,true);window.addEventListener("luojia-auth-change",changed);window.addEventListener("storage",storage);
   return()=>{document.body.style.overflow=overflow;document.removeEventListener("keydown",key,true);window.removeEventListener("luojia-auth-change",changed);window.removeEventListener("storage",storage);if(previous?.isConnected)previous.focus();};
 },[isOpen]);
 useEffect(()=>{
   let active=true;setResults([]);setConversations([]);setErrors([]);setSearched(false);
   if(!isOpen||!query.trim()){setLoading(false);return;}
   const owner=getCurrentUserId(),credential=getAuthHeaders().Authorization;
   const valid=()=>active&&owner===getCurrentUserId()&&credential===getAuthHeaders().Authorization;
   setLoading(true);
   const timer=setTimeout(async()=>{
     const jobs:Promise<unknown>[]=[];const names:string[]=[];
     if(activeCategory==="all"||activeCategory==="conversations"){jobs.push(listSessions(owner,query.trim()));names.push("历史对话");}
     if(activeCategory!=="conversations"){jobs.push(searchGlobal(query.trim(),activeCategory));names.push("教材、笔记与错题");}
     const values=await Promise.allSettled(jobs);if(!valid())return;
     values.forEach((value,index)=>{if(value.status==="fulfilled"){if(names[index]==="历史对话")setConversations(value.value as Session[]);else setResults((value.value as {items:GlobalSearchResultItem[]}).items||[]);}});
     setErrors(values.flatMap((value,index)=>value.status==="rejected"?[`${names[index]}暂时无法读取，请重试。`]:[]));setSearched(true);setLoading(false);
   },280);
   return()=>{active=false;clearTimeout(timer);};
 },[isOpen,query,activeCategory]);
  const handleInsert = (item: GlobalSearchResultItem) => {
    let insertText = "";
    if (item.category === "curriculum") {
      insertText = item.formula
        ? `请问关于【${item.title}】：\n$$${item.formula}$$\n应如何理解其几何意义与应用？`
        : `请问关于【${item.title}】：${item.content}\n在解题中该如何把握？`;
    } else if (item.category === "mistakes") {
      insertText = `我想针对历史错题【${item.title}】进行变式专项突破，请帮我剖析错因并出题。`;
    } else {
      insertText = `我想探讨笔记中的这部分内容：${item.title}\n${item.content}`;
    }

    if (onSelectResult) {
      onSelectResult(insertText);
    }
    onClose();
  };

 if(!isOpen)return null;
 return <div className="fixed inset-0 z-[90] flex items-start justify-center bg-black/40 px-3 pt-[8dvh] backdrop-blur-sm" onClick={onClose}>
   <div ref={dialog} role="dialog" aria-modal="true" aria-label="搜索对话与知识" className="flex max-h-[84dvh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-[var(--border-primary)] bg-[var(--bg-card)] text-[var(--text-primary)] shadow-xl" onClick={e=>e.stopPropagation()}>
     <div className="flex items-center gap-3 border-b border-[var(--border-primary)] p-3 sm:p-4"><Search className="size-5 shrink-0 text-olive-600"/><input ref={inputRef} aria-label="搜索对话、教材、笔记和错题" maxLength={200} value={query} onChange={e=>setQuery(e.target.value)} placeholder="搜索对话、教材、笔记和错题…" className="min-w-0 flex-1 bg-transparent py-2 text-sm outline-none"/>{loading&&<Loader2 className="size-4 shrink-0 animate-spin"/>}<button type="button" aria-label="关闭搜索" onClick={onClose} className="flex size-11 shrink-0 items-center justify-center rounded-lg hover:bg-[var(--bg-hover)]"><X className="size-4"/></button></div>
     <div aria-label="搜索范围" className="flex shrink-0 gap-1 overflow-x-auto border-b border-[var(--border-primary)] p-2">{CATEGORIES.map(cat=><button type="button" key={cat.key} aria-pressed={activeCategory===cat.key} onClick={()=>setActiveCategory(cat.key)} className={`min-h-11 shrink-0 rounded-lg px-3 text-xs ${activeCategory===cat.key?"bg-olive-600/10 text-olive-800 dark:text-olive-200":"text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"}`}>{cat.label}</button>)}</div>
     <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
       {!!errors.length&&<div role="status" className="rounded-lg border border-ochre-600/30 p-3 text-xs leading-6">{errors.map(error=><p key={error}>{error}</p>)}</div>}
       {loading&&<p role="status" className="py-8 text-center text-sm">正在检索…</p>}
       {!searched&&!loading&&<p className="py-8 text-center text-sm leading-7 text-[var(--text-secondary)]">输入关键词，可检索历史消息内容，或查找教材、笔记与错题。</p>}
       {searched&&!loading&&!conversations.length&&!results.length&&!errors.length&&<p className="py-8 text-center text-sm">未找到匹配内容。</p>}
       {conversations.length>0&&<section aria-label="历史对话搜索结果" className="space-y-2"><h2 className="text-xs text-[var(--text-muted)]">历史对话 · {conversations.length}</h2>{conversations.map(session=><button type="button" key={session.id} onClick={()=>{onClose();if(onSelectSession)onSelectSession(session.id);else router.push(`/chat?session=${encodeURIComponent(session.id)}`);}} className="flex min-h-14 w-full items-center gap-3 rounded-xl border border-[var(--border-primary)] p-3 text-left hover:bg-[var(--bg-hover)]"><MessageCircle className="size-4 shrink-0 text-olive-600"/><span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium">{session.title}</span><span className="mt-1 block text-xs text-[var(--text-muted)]">{new Date(session.updated_at||session.created_at).toLocaleDateString("zh-CN")} · 继续这段对话</span></span><ArrowRight className="size-4 shrink-0"/></button>)}</section>}
       {results.length>0&&<section aria-label="知识搜索结果" className="space-y-3"><h2 className="text-xs text-[var(--text-muted)]">教材、笔记与错题 · {results.length}</h2>{results.map(item=><article key={item.id} className="space-y-2 rounded-xl border border-[var(--border-primary)] p-4"><span className="text-xs text-olive-700 dark:text-olive-300">{item.category_label}</span><h3 className="break-words text-sm font-semibold">{item.title}</h3><div className="line-clamp-3 text-xs leading-6 text-[var(--text-secondary)]"><MathMarkdown content={item.content}/></div>{item.formula&&<div className="overflow-x-auto text-sm"><MathMarkdown content={`$$${item.formula}$$`}/></div>}<button type="button" onClick={()=>handleInsert(item)} className="min-h-11 text-xs text-olive-700 dark:text-olive-300 underline">带入对话草稿 →</button></article>)}</section>}
     </div>
   </div>
 </div>;
}
