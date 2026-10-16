"use client";
import Link from "next/link";
import {useState} from "react";
import {usePathname} from "next/navigation";
import {Search, Network, NotebookPen, BookOpen, BookmarkCheck, CalendarCheck2, CheckCircle2, MessageCircle, Code2, LogOut, LogIn, ChevronDown} from "lucide-react";
import {LearningNavigation} from "./learning-navigation";
import {SettingsDrawer} from "../settings-drawer";
import {ThemeToggle} from "../theme-toggle";
import {clearAuthSession,signOutCurrentSession} from "@/lib/demo-auth";
const row="flex min-h-11 w-full items-center gap-2.5 rounded-lg px-3 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] focus-visible:outline-2 focus-visible:outline-olive-600";
export function SidebarNavigation({onOpenSearch,onNavigate}: {onOpenSearch:()=>void;onNavigate?:()=>void}) {
  const pathname=usePathname();
  const items=[{href:"/explore",label:"数学探索",icon:Network},{href:"/study",label:"今日学习",icon:CalendarCheck2},{href:"/assessment",label:"章节自检",icon:CheckCircle2},{href:"/teach-back",label:"讲给助教听",icon:MessageCircle},{href:"/code-workshop",label:"代码静态审阅",icon:Code2},{href:"/graph",label:"知识网络",icon:Network},{href:"/notebook",label:"笔记本",icon:NotebookPen},{href:"/mistake-book",label:"错题本",icon:BookOpen},{href:"/admin/knowledge",label:"教师审核",icon:BookmarkCheck}];
  return <div onClick={event=>{if((event.target as HTMLElement).closest("a"))onNavigate?.();}}>
    <LearningNavigation/>
    <div role="separator" className="my-4 border-t border-[var(--border-primary)]"/>
    <nav aria-label="学习工具" className="grid gap-0.5">
      <button type="button" onClick={onOpenSearch} aria-label="搜索对话与知识" className={row}><Search className="size-4"/>搜索对话与知识<kbd className="ml-auto text-[10px] text-[var(--text-muted)]">Ctrl K</kbd></button>
      <Link href="/materials" aria-current={pathname==="/materials"?"page":undefined} className={`${row} ${pathname==="/materials"?"bg-olive-600/10 text-olive-800 dark:text-olive-200":""}`}><BookOpen className="size-4"/>我的资料</Link>
      <details className="group" open={items.slice(0,-1).some(item=>item.href===pathname)||undefined}>
        <summary className={`${row} cursor-pointer list-none [&::-webkit-details-marker]:hidden`}><BookOpen className="size-4"/>学习工具与资料<ChevronDown className="ml-auto size-3.5 transition-transform group-open:rotate-180"/></summary>
        <div className="ml-3 border-l border-[var(--border-primary)] pl-2">{items.slice(0,-1).map(({href,label,icon:Icon})=><Link key={href} href={href} aria-current={pathname===href?"page":undefined} className={`${row} ${pathname===href?"bg-olive-600/10 text-olive-800 dark:text-olive-200":""}`}><Icon className="size-4"/>{label}</Link>)}</div>
      </details>
      <Link href="/admin/knowledge" aria-current={pathname==="/admin/knowledge"?"page":undefined} className={row}><BookmarkCheck className="size-4"/>教师审核</Link>
    </nav>
  </div>;
}
export function SidebarAccount() {
  const [signingOut,setSigningOut]=useState(false),[error,setError]=useState("");
  const localSignOut=()=>{
    clearAuthSession();
    // Full navigation discards mounted owner-scoped state after sign-out.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign("/auth/login");
  };
  const signOut=async()=>{if(signingOut)return;setSigningOut(true);setError("");try{await signOutCurrentSession();localSignOut();}catch(e){setError(e instanceof Error?e.message:"退出失败，服务端撤销未确认。");}finally{setSigningOut(false);}};
  return <div className="mt-auto shrink-0 border-t border-[var(--border-primary)] pt-3">
    {error&&<div role="alert" className="mb-2 rounded-lg border border-cinnabar-600/30 p-3 text-xs leading-6"><p>{error}</p><button type="button" disabled={signingOut} onClick={signOut} className="min-h-11 underline">重试退出</button><button type="button" onClick={localSignOut} className="min-h-11 text-left underline">仅清除此设备登录及未提交草稿</button></div>}
    <div className="flex items-center justify-between px-2"><SettingsDrawer/><ThemeToggle/><Link href="/auth/login" aria-label="登录或切换账号" className="flex size-11 items-center justify-center rounded-lg hover:bg-[var(--bg-hover)]"><LogIn className="size-4"/></Link><button type="button" disabled={signingOut} onClick={signOut} aria-label="退出登录并清除本机未提交草稿" className="flex size-11 items-center justify-center rounded-lg hover:bg-[var(--bg-hover)] disabled:opacity-50"><LogOut className="size-4"/></button></div>
  </div>;
}
