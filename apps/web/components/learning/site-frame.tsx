"use client";
import {useEffect,useState,type ReactNode} from "react";
import {useRouter} from "next/navigation";
import {storeChatEntry} from "@/lib/chat-entry";
import {AppHeader} from "../app-header";
import {Sidebar} from "../sidebar";
import {MobileDrawer} from "../mobile-drawer";
import {GlobalSearchModal} from "../global-search-modal";
import {listSessions,type Session} from "@/lib/api";
import {getCurrentUserId,getAuthHeaders,isAuthStorageKey} from "@/lib/demo-auth";
export function SiteFrame({children}: {children:ReactNode}) {
  const router=useRouter();
  const [collapsed,setCollapsed]=useState(false),[mobile,setMobile]=useState(false),[searchOpen,setSearchOpen]=useState(false);
  const [sessions,setSessions]=useState<Session[]>([]),[query,setQuery]=useState(""),[refresh,setRefresh]=useState(0),[error,setError]=useState("");
  const [searchDraft,setSearchDraft]=useState("");
  useEffect(()=>{
    const changed=()=>{setSessions([]);setQuery("");setSearchDraft("");setRefresh(n=>n+1);};
    const storage=(event:StorageEvent)=>{if(isAuthStorageKey(event.key))changed();};
    window.addEventListener("luojia-auth-change",changed);window.addEventListener("storage",storage);
    return()=>{window.removeEventListener("luojia-auth-change",changed);window.removeEventListener("storage",storage);};
  },[]);
  useEffect(()=>{
    let live=true;
    const owner=getCurrentUserId(),credential=getAuthHeaders().Authorization;
    const current=()=>live&&owner===getCurrentUserId()&&credential===getAuthHeaders().Authorization;
    const timer=setTimeout(()=>{listSessions(owner,query).then(value=>{if(current()){setSessions(value);setError("");}}).catch(()=>{if(current())setError("暂时无法读取会话，请重试。");});},200);
    return()=>{live=false;clearTimeout(timer);};
  },[query,refresh]);
  useEffect(()=>{
    const key=(event:KeyboardEvent)=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==="k"){event.preventDefault();setMobile(false);setSearchOpen(true);}};
    window.addEventListener("keydown",key);return()=>window.removeEventListener("keydown",key);
  },[]);
  const sidebar=<div className="flex h-full min-h-0 flex-col">{error&&<button type="button" onClick={()=>setRefresh(n=>n+1)} className="shrink-0 p-3 text-xs text-cinnabar-700">{error}</button>}<div className="min-h-0 flex-1"><Sidebar sessions={sessions} activeSessionId={null} onSelect={id=>{setMobile(false);router.push(`/chat?session=${encodeURIComponent(id)}`);}} onRefresh={()=>setRefresh(n=>n+1)} searchQuery={query} onSearchChange={setQuery} onOpenSearch={()=>{setMobile(false);setSearchOpen(true);}} onNavigate={()=>setMobile(false)}/></div></div>;
  return <div className="flex h-dvh flex-col overflow-hidden bg-[var(--bg-primary)] text-[var(--text-primary)]">
    <AppHeader onNewSession={()=>router.push("/chat?new=1")} onToggleSidebar={()=>{if(window.innerWidth>=1024)setCollapsed(value=>!value);else setMobile(value=>!value);}}/>
    <div className="flex min-h-0 flex-1">{!collapsed&&<aside aria-label="导航与会话" className="hidden w-60 shrink-0 lg:block">{sidebar}</aside>}<div className="min-w-0 flex-1 overflow-y-auto">{children}</div></div>
    {mobile&&<MobileDrawer title="导航与历史会话" side="left" breakpoint={1024} onClose={()=>setMobile(false)}>{sidebar}</MobileDrawer>}
    {searchDraft&&<div role="alert" className="fixed bottom-4 right-4 z-40 max-w-[calc(100vw-32px)] rounded-xl border border-ochre-600/30 bg-[var(--bg-card)] p-4 shadow-soft"><p className="text-sm">检索内容未能转交，请复制到对话框。</p><textarea aria-label="待转交的检索内容" readOnly value={searchDraft} className="mt-2 w-full p-2 text-sm"/><button type="button" className="min-h-11 underline" onClick={()=>setSearchDraft("")}>关闭</button></div>}
    <GlobalSearchModal isOpen={searchOpen} onClose={()=>setSearchOpen(false)} onSelectResult={text=>{try{const id=crypto.randomUUID();storeChatEntry(sessionStorage,getCurrentUserId(),id,text);router.push(`/chat?draft=${id}`);}catch{setSearchDraft(text);}}}/>
  </div>;
}
