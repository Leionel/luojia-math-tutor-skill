"use client";
import Link from "next/link";
import {BookOpen,FlaskConical,CalendarCheck2,Code2,X} from "lucide-react";
import type {WorkspaceTab} from "./canvas-workspace";
export function ChatWorkspaceBar({open,tab,hasReference,disabled,onOpen,onClose,onPlain,onRootCheck}:{open:boolean;tab:WorkspaceTab;hasReference:boolean;disabled:boolean;onOpen:(tab:WorkspaceTab)=>void;onClose:()=>void;onPlain:()=>void;onRootCheck:()=>void}){
  return <div className="flex flex-wrap items-center gap-1 pb-2">
    <div className="flex flex-wrap items-center gap-2"><button type="button" disabled={disabled} aria-pressed={open&&tab==="reading"} onClick={()=>open&&tab==="reading"?onClose():onOpen("reading")} className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-dai-600/25 px-3 text-xs text-dai-700 dark:text-dai-300 disabled:opacity-50"><BookOpen className="size-4"/>{open&&tab==="reading"?"收起材料":"选材料一起读"}</button>
      <details className="relative"><summary className="min-h-11 cursor-pointer rounded-lg px-3 py-3 text-xs text-[var(--text-secondary)]">按需打开工具</summary><div className="absolute right-0 bottom-full z-30 mb-1 grid w-48 gap-1 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-2 shadow-soft">{([{id:"lab",label:"数学实验",icon:FlaskConical},{id:"study",label:"学习任务",icon:CalendarCheck2},{id:"code",label:"代码静态审阅",icon:Code2}] as const).map(({id,label,icon:Icon})=><button key={id} type="button" disabled={disabled} className="flex min-h-11 items-center gap-2 rounded-lg px-3 text-left text-sm hover:bg-[var(--bg-hover)] disabled:opacity-50" onClick={e=>{e.currentTarget.closest("details")?.removeAttribute("open");onOpen(id);}}><Icon className="size-4"/>{label}</button>)}<button type="button" disabled={disabled} onClick={e=>{e.currentTarget.closest("details")?.removeAttribute("open");onRootCheck();}} className="min-h-11 px-3 text-left text-sm hover:underline disabled:opacity-50">检查求根过程</button><Link href="/records" className="min-h-11 px-3 py-3 text-sm hover:underline">回看学习记录</Link></div></details>
      {(hasReference||open)&&<button type="button" disabled={disabled} onClick={onPlain} className="inline-flex min-h-11 items-center gap-1 px-2 text-xs text-[var(--text-secondary)] hover:underline disabled:opacity-50"><X className="size-3.5"/>回到纯对话</button>}
    </div>
  </div>;
}
