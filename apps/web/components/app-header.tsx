"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Menu,
  MoreHorizontal,
  LayoutPanelLeft,
  Target,
  User,
  LogOut,
  BookOpen,
  Network,
  Plus,
  Home,
  Sparkles,
  BookmarkCheck,
  Search
} from "lucide-react";
import { SettingsDrawer } from "./settings-drawer";
import { ThemeToggle } from "./theme-toggle";

export function AppHeader({
  onNewSession,
  onToggleSidebar,
  onToggleLearning,
  onToggleZenMode,
  onOpenSearch,
}: {
  onNewSession: () => void;
  onToggleSidebar?: () => void;
  onToggleLearning?: () => void;
  onToggleZenMode?: () => void;
  onOpenSearch?: () => void;
}) {
  return (
    <header className="sticky top-0 z-40 flex h-16 w-full flex-shrink-0 items-center justify-between px-3 sm:px-6 glass-header transition-colors duration-300">
      {/* Left: Brand & Sidebar toggle & User status */}
      <div className="flex items-center gap-2 sm:gap-3.5 min-w-0 shrink-0">
        {onToggleSidebar && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleSidebar}
            className="h-9 w-9 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] rounded-lg transition-colors -ml-1"
            title="展开/折叠历史会话"
          >
            <Menu className="w-4 h-4" />
          </Button>
        )}

        {/* Brand Crest & Title */}
        <Link href="/" className="flex items-center gap-2.5 group transition-transform active:scale-98">
          <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#617a55] to-[#4e6344] text-[#faf7f2] shadow-sm shadow-[#617a55]/25 border border-[#617a55]/30 overflow-hidden">
            <span className="font-title font-bold text-base leading-none tracking-widest select-none">珞</span>
            <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div className="hidden min-[360px]:flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="whitespace-nowrap text-sm sm:text-lg font-bold tracking-wide text-[var(--text-primary)] font-title group-hover:text-[#617a55] dark:group-hover:text-[#879f7a] transition-colors">
                珞珈数智
              </span>
              <span className="hidden xl:inline-flex items-center text-[10px] font-semibold font-sans px-1.5 py-0.5 rounded-full bg-[#617a55]/10 text-[#617a55] dark:text-[#879f7a] border border-[#617a55]/20">
                AI Tutor
              </span>
            </div>
          </div>
        </Link>

        <div className="h-4 w-px bg-[var(--border-subtle)] mx-1 hidden sm:block" />

        <SettingsDrawer />

        {/* User Badge */}
        <div className="hidden 2xl:flex items-center gap-2 border border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/60 rounded-full py-1 pl-1.5 pr-2.5 shadow-sm">
          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-[#617a55]/15 text-[#617a55] dark:text-[#879f7a]">
            <User className="h-3 w-3" />
          </div>
          <span className="text-xs font-medium text-[var(--text-secondary)] tracking-wide">珞珈学员</span>
          <div className="h-2.5 w-px bg-[var(--border-subtle)]" />
          <Link href="/auth/login" className="text-[var(--text-muted)] hover:text-[#c44a3d] transition-colors" title="退出登录">
            <LogOut className="h-3 w-3" />
          </Link>
        </div>
      </div>

      {/* Right: Functional Navigation & Actions */}
      <div className="flex shrink-0 items-center gap-1 sm:gap-2.5">
        {onOpenSearch && (
          <button
            type="button"
            onClick={onOpenSearch}
            className="hidden md:inline-flex items-center gap-2 px-3 py-1.5 h-8 rounded-full border border-[var(--border-subtle)] bg-[var(--bg-card)]/80 hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all text-xs shadow-xs"
            title="全局检索教材定理、错题与笔记 (Ctrl+K)"
          >
            <Search className="w-3.5 h-3.5 text-olive-600 dark:text-olive-400" />
            <span className="hidden xl:inline whitespace-nowrap">藏书阁检索</span>
            <kbd className="hidden xl:inline text-[10px] bg-[var(--bg-tertiary)] px-1.5 py-0.5 rounded border border-[var(--border-subtle)] font-mono text-[var(--text-tertiary)]">
              Ctrl K
            </kbd>
          </button>
        )}

        <Link
          href="/graph"
          className="hidden lg:inline-flex items-center gap-1.5 px-3 py-1.5 h-8 rounded-full border border-sky-500/20 bg-sky-500/5 text-sky-700 dark:text-sky-300 hover:bg-sky-500/10 hover:border-sky-500/30 transition-all text-xs font-semibold glass-pill shadow-sm"
          title="查看前置与核心知识点网络"
        >
          <Network className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />
          <span>知识网络</span>
        </Link>

        <Link
          href="/notebook"
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 h-8 rounded-full border border-olive-500/20 bg-olive-500/5 text-olive-700 dark:text-olive-300 hover:bg-olive-500/10 hover:border-olive-500/30 transition-all text-xs font-semibold glass-pill shadow-sm"
          title="查看随堂笔记与公式整理"
        >
          <BookmarkCheck className="w-3.5 h-3.5 text-olive-600 dark:text-olive-400" />
          <span className="hidden lg:inline whitespace-nowrap">笔记本</span>
        </Link>

        <Link
          href="/mistake-book"
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 h-8 rounded-full border border-[#c44a3d]/20 bg-[#c44a3d]/5 text-[#c44a3d] hover:bg-[#c44a3d]/10 hover:border-[#c44a3d]/35 transition-all text-xs font-semibold glass-pill shadow-sm"
          title="回看推导偏差与专项练习"
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span className="hidden lg:inline whitespace-nowrap">错题本</span>
        </Link>

        {/* New Session Button */}
        <Button
          variant="primary"
          size="sm"
          onClick={onNewSession}
          aria-label="新会话"
          className="h-9 w-9 sm:h-8 sm:w-auto px-0 sm:px-3 rounded-lg sm:rounded-full text-xs font-semibold gap-1 shadow-sm active:scale-95 transition-transform"
        >
          <Plus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline whitespace-nowrap">新会话</span>
        </Button>

        <div className="h-4 w-px bg-[var(--border-subtle)] mx-0.5 hidden sm:block" />

        {/* Zen / Immersion Mode */}
        {onToggleZenMode && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleZenMode}
            className="hidden sm:inline-flex h-8 w-8 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/50 text-[var(--text-secondary)] hover:text-[#617a55] dark:hover:text-[#879f7a] hover:bg-[var(--accent-light)] transition-all shadow-sm"
            title="开启沉浸禅意模式"
          >
            <Target className="w-3.5 h-3.5" />
          </Button>
        )}

        {/* Theme Toggle */}
        <div className="hidden sm:block"><ThemeToggle /></div>

        {/* Home Link */}
        <Link
          href="/"
          className="hidden sm:flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/50 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-all shadow-sm"
          title="返回主页"
        >
          <Home className="w-3.5 h-3.5" />
        </Link>

        {/* Learning & Instruments Panel Toggle (B Feature: On-Demand Expandable) */}
        {onToggleLearning && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleLearning}
            className="h-9 w-9 sm:h-8 sm:w-auto px-0 sm:px-2.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/50 text-[var(--text-secondary)] hover:text-[#617a55] dark:hover:text-[#879f7a] hover:bg-[var(--accent-light)] transition-all shadow-sm flex items-center gap-1.5 text-xs font-semibold"
            title="展开/收起数理仪器与状态复盘"
          >
            <LayoutPanelLeft className="w-3.5 h-3.5" />
            <span className="hidden md:inline">数理仪器</span>
          </Button>
        )}
        <details className="relative sm:hidden group" onKeyDown={event => { if (event.key === "Escape") event.currentTarget.removeAttribute("open"); }}>
          <summary aria-label="更多功能" className="flex h-9 w-9 cursor-pointer list-none items-center justify-center rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] [&::-webkit-details-marker]:hidden"><MoreHorizontal className="h-5 w-5" /></summary>
          <button aria-label="关闭更多功能" className="fixed inset-0 hidden group-open:block cursor-default" onClick={event => event.currentTarget.closest("details")?.removeAttribute("open")} />
          <div className="absolute right-0 top-full mt-2 w-48 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-2 shadow-lg text-sm text-[var(--text-primary)]">
            <button className="w-full rounded-lg p-3 text-left hover:bg-[var(--bg-hover)]" onClick={event => { event.currentTarget.closest("details")?.removeAttribute("open"); onOpenSearch?.(); }}>检索教材与笔记</button>
            <Link className="block rounded-lg p-3 hover:bg-[var(--bg-hover)]" href="/graph">知识网络</Link>
            <Link className="block rounded-lg p-3 hover:bg-[var(--bg-hover)]" href="/notebook">笔记本</Link>
            <Link className="block rounded-lg p-3 hover:bg-[var(--bg-hover)]" href="/mistake-book">错题本</Link>
            <button className="w-full rounded-lg p-3 text-left hover:bg-[var(--bg-hover)]" onClick={event => { event.currentTarget.closest("details")?.removeAttribute("open"); onToggleZenMode?.(); }}>沉浸模式</button>
            <div className="flex items-center justify-between border-t border-[var(--border-subtle)] p-3"><span>切换主题</span><ThemeToggle /></div>
          </div>
        </details>
      </div>
    </header>
  );
}
