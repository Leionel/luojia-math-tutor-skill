"use client";

import Link from "next/link";

import type { Subject, TutorMode } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Menu, LayoutPanelLeft, Target } from "lucide-react";
import { ModeSwitcher } from "./mode-switcher";
import { SettingsDrawer } from "./settings-drawer";
import { ThemeToggle } from "./theme-toggle";

export function AppHeader({
  subject,
  mode,
  onSubjectChange,
  onModeChange,
  onNewSession,
  onToggleSidebar,
  onToggleLearning,
  onToggleZenMode
}: {
  subject: Subject;
  mode: TutorMode;
  onSubjectChange: (subject: Subject) => void;
  onModeChange: (mode: TutorMode) => void;
  onNewSession: () => void;
  onToggleSidebar?: () => void;
  onToggleLearning?: () => void;
  onToggleZenMode?: () => void;
}) {
  return (
    <header className="sticky top-0 z-50 flex h-16 flex-shrink-0 items-center justify-between border-b border-[var(--border-primary)] bg-white dark:bg-[var(--bg-header)] dark:backdrop-blur-2xl px-4 sm:px-6 transition-colors duration-300">
      <div className="flex items-center gap-2 sm:gap-4">
        {onToggleSidebar && (
          <Button variant="ghost" size="icon" onClick={onToggleSidebar} className="lg:hidden h-9 w-9 -ml-2 text-[var(--text-secondary)]">
            <Menu className="w-5 h-5" />
          </Button>
        )}
        <SettingsDrawer />
        <ThemeToggle />
        {onToggleZenMode && (
          <Button variant="ghost" size="icon" onClick={onToggleZenMode} className="h-9 w-9 rounded-md border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] text-indigo-500 hover:bg-indigo-500/10 transition-colors shadow-sm" title="进入沉浸模式 (Zen Mode)">
            <Target className="w-4 h-4" />
          </Button>
        )}
        <Link href="/" className="hidden sm:flex h-9 w-9 items-center justify-center rounded-md border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors shadow-sm" title="农场主页 (Home)">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        </Link>
        <div className="flex flex-col">
          <div className="text-[17px] font-bold tracking-tight text-[var(--text-primary)] sm:text-lg">珞珈数智助教</div>
          <div className="hidden text-[11px] font-medium tracking-widest uppercase text-[var(--text-secondary)] sm:block">AI Tutor</div>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <Select
          value={subject}
          onChange={(event) => onSubjectChange(event.target.value as Subject)}
        >
          <option value="auto">自动识别</option>
          <option value="foundations">基础概念</option>
          <option value="derivation">深度推导</option>
          <option value="problem_solving">实战解题</option>
        </Select>
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
