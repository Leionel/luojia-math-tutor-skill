"use client";

import Link from "next/link";

import type { Subject, TutorMode } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Menu, LayoutPanelLeft, Target, User, LogOut, BookOpen, FileText, Loader2, Network } from "lucide-react";
import { ModeSwitcher } from "./mode-switcher";
import { SettingsDrawer } from "./settings-drawer";
import { ThemeToggle } from "./theme-toggle";

export function AppHeader({
  mode,
  onModeChange,
  onNewSession,
  onToggleSidebar,
  onToggleLearning,
  onToggleZenMode,
}: {
  mode: TutorMode;
  onModeChange: (mode: TutorMode) => void;
  onNewSession: () => void;
  onToggleSidebar?: () => void;
  onToggleLearning?: () => void;
  onToggleZenMode?: () => void;
}) {
  return (
    <header className="relative z-50 flex h-16 flex-shrink-0 items-center justify-between px-4 sm:px-6 transition-colors duration-300 pointer-events-none">
      <div className="flex items-center gap-2 sm:gap-4 pointer-events-auto">
        {onToggleSidebar && (
          <Button variant="ghost" size="icon" onClick={onToggleSidebar} className="h-9 w-9 -ml-2 text-[var(--text-secondary)]">
            <Menu className="w-5 h-5" />
          </Button>
        )}
        <div className="flex flex-col mr-2">
          <div className="text-[17px] font-bold tracking-tight text-[var(--text-primary)] sm:text-lg font-title">珞珈数智助教</div>
        </div>

        <SettingsDrawer />
        
        {/* User Info */}
        <div className="hidden md:flex items-center gap-2 border border-[var(--border-subtle)] bg-white/50 dark:bg-[var(--bg-tertiary)] rounded-full p-1 pr-3 shadow-sm hover:border-[#617a55]/30 transition-all">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-[#617a55]/20 to-[#617a55]/5 text-[#617a55] border border-[#617a55]/20 shadow-inner">
            <User className="h-3.5 w-3.5" />
          </div>
          <span className="text-xs font-bold text-[var(--text-primary)] font-title tracking-widest">珞珈学员</span>
          <div className="h-3 w-px bg-[var(--border-subtle)] mx-1"></div>
          <Link href="/auth/login" className="text-[var(--text-muted)] hover:text-[#c44a3d] transition-colors" title="退出登录">
             <LogOut className="h-3.5 w-3.5" />
          </Link>
        </div>

        <ThemeToggle />
        {onToggleZenMode && (
          <Button variant="ghost" size="icon" onClick={onToggleZenMode} className="h-9 w-9 rounded-md border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] text-indigo-500 hover:bg-indigo-500/10 transition-colors shadow-sm" title="进入沉浸模式 (Zen Mode)">
            <Target className="w-4 h-4" />
          </Button>
        )}
        <Link href="/" className="hidden sm:flex h-9 w-9 items-center justify-center rounded-md border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors shadow-sm" title="农场主页 (Home)">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        </Link>
      </div>
      <div className="flex flex-wrap items-center gap-2 sm:gap-3 pointer-events-auto">
        <Link href="/graph" className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 h-9 rounded-md border border-cyan-500/20 bg-cyan-500/5 text-cyan-600 dark:text-cyan-400 hover:bg-cyan-500/10 transition-colors text-xs font-bold font-body shadow-sm">
          <Network className="w-4 h-4" />
          知识网络
        </Link>
        <Link href="/notebook" className="hidden md:flex items-center gap-1.5 px-3 py-1.5 h-9 rounded-md border border-indigo-500/20 bg-indigo-500/5 text-indigo-500 hover:bg-indigo-500/10 transition-colors text-xs font-bold font-body shadow-sm">
          <BookOpen className="w-4 h-4" />
          笔记本
        </Link>
        <Link href="/mistake-book" className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 h-9 rounded-md border border-[#c44a3d]/20 bg-[#c44a3d]/5 text-[#c44a3d] hover:bg-[#c44a3d]/10 transition-colors text-xs font-bold font-body shadow-sm">
          <BookOpen className="w-4 h-4" />
          错题本
        </Link>
        <ModeSwitcher value={mode} onChange={onModeChange} />
        <Button variant="secondary" size="sm" onClick={onNewSession} className="hidden sm:flex">新会话</Button>
        {onToggleLearning && (
          <Button variant="ghost" size="icon" onClick={onToggleLearning} className="xl:hidden h-9 w-9 -mr-2 text-[var(--text-secondary)]">
            <LayoutPanelLeft className="w-5 h-5" />
          </Button>
        )}
      </div>
    </header>
  );
}
