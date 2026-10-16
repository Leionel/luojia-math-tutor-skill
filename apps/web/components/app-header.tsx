"use client";
import Link from "next/link";
import {Menu, Plus, Target, LayoutPanelLeft} from "lucide-react";
import {BrandLogo} from "./brand-logo";
export function AppHeader({onNewSession,onToggleSidebar,onToggleLearning,onToggleZenMode}: {
  onNewSession:()=>void; onToggleSidebar?:()=>void; onToggleLearning?:()=>void; onToggleZenMode?:()=>void;
}) {
  const iconButton="inline-flex size-11 items-center justify-center rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] focus-visible:outline-2 focus-visible:outline-olive-600";
  return <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center justify-between gap-2 border-b border-[var(--border-primary)] px-3 sm:px-5 glass-header">
    <div className="flex min-w-0 items-center gap-2">
      {onToggleSidebar&&<button type="button" onClick={onToggleSidebar} aria-label="展开或收起导航侧栏" className={iconButton}><Menu className="size-5"/></button>}
      <Link href="/" className="flex items-center gap-2 font-title text-base font-semibold sm:text-lg"><BrandLogo className="size-9"/><span className="whitespace-nowrap">珞珈数智</span></Link>
    </div>
    <div className="flex shrink-0 items-center gap-1 sm:gap-2">
      {onToggleZenMode&&<button type="button" onClick={onToggleZenMode} aria-label="全屏学习" className={`${iconButton} hidden sm:inline-flex`}><Target className="size-4"/></button>}
      {onToggleLearning&&<button type="button" onClick={onToggleLearning} aria-label="展开或收起数理仪器" className={iconButton}><LayoutPanelLeft className="size-4"/></button>}
      <button type="button" onClick={onNewSession} aria-label="新会话" className="inline-flex min-h-11 items-center gap-1.5 rounded-lg bg-olive-700 px-3 text-xs font-semibold text-paper-50 hover:bg-olive-800"><Plus className="size-4"/><span className="hidden sm:inline">新会话</span></button>
    </div>
  </header>;
}
