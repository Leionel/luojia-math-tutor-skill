"use client";

import React from "react";
import Link from "next/link";
import { 
  FlaskConical, 
  BookOpen, 
  CalendarCheck2, 
  Maximize2, 
  Minimize2, 
  ExternalLink, 
  X,
} from "lucide-react";
import { LabWorkspace } from "./lab-workspace";
import { ReadingDomainView } from "./reading-domain-view";
import { StudyDomainView } from "./study-domain-view";
import type { RootContextRef, ReadingContextRef, LearningContextRef } from "@/lib/learning-context";
import type { LabRun, StudyTask } from "@/lib/learning-api";

export type WorkspaceTab = "lab" | "reading" | "study";

export interface CanvasWorkspaceProps {
  activeTab: WorkspaceTab;
  onTabChange: (tab: WorkspaceTab) => void;
  onClose: () => void;
  isMaximized: boolean;
  onToggleMaximize: () => void;
  initialRef?: RootContextRef;
  draftPrediction?: string;
  sessionId?: string;
  onDiscuss?: (ref: RootContextRef) => void;
  onSaved?: (run: LabRun) => void;
  readingRef?: ReadingContextRef;
  onDiscussReading?: (ref: ReadingContextRef, prompt: string) => void;
  onDiscussStudy?: (prompt: string, taskRef?: LearningContextRef | null) => void;
  onStartStudyTask?: (task: StudyTask) => void;
}

export function CanvasWorkspace({
  activeTab,
  onTabChange,
  onClose,
  isMaximized,
  onToggleMaximize,
  initialRef,
  draftPrediction,
  sessionId,
  onDiscuss,
  onSaved,
  readingRef,
  onDiscussReading,
  onDiscussStudy,
  onStartStudyTask,
}: CanvasWorkspaceProps) {
  return (
    <div className="flex h-full flex-col bg-[var(--bg-primary)]">
      {/* 1. Canvas Atelier Ribbon / Header */}
      <div className="flex shrink-0 items-center justify-between border-b border-paper-200 dark:border-paper-800 bg-[var(--bg-card)]/90 backdrop-blur-md px-4 py-2.5">
        {/* Left: Tab Switcher Pills */}
        <div className="flex items-center gap-1 rounded-xl bg-paper-100 dark:bg-paper-900/60 p-1 border border-paper-200/60 dark:border-paper-800/60">
          <button
            type="button"
            onClick={() => onTabChange("lab")}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "lab"
                ? "bg-[var(--bg-card)] text-olive-800 dark:text-olive-200 shadow-2xs border border-paper-200 dark:border-paper-700"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            <FlaskConical className="w-3.5 h-3.5 text-olive-600" />
            <span>数值实验台</span>
          </button>

          <button
            type="button"
            onClick={() => onTabChange("reading")}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "reading"
                ? "bg-[var(--bg-card)] text-olive-800 dark:text-olive-200 shadow-2xs border border-paper-200 dark:border-paper-700"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5 text-olive-600" />
            <span>经典研读录</span>
          </button>

          <button
            type="button"
            onClick={() => onTabChange("study")}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "study"
                ? "bg-[var(--bg-card)] text-olive-800 dark:text-olive-200 shadow-2xs border border-paper-200 dark:border-paper-700"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            <CalendarCheck2 className="w-3.5 h-3.5 text-olive-600" />
            <span>今日日课案</span>
          </button>
        </div>

        {/* Right: Window Controls */}
        <div className="flex items-center gap-1">
          {/* Open in full page link */}
          <Link
            href={
              activeTab === "lab"
                ? "/lab"
                : activeTab === "reading"
                ? "/reading"
                : "/study"
            }
            target="_blank"
            rel="noopener noreferrer"
            title="在新独立标签页中全屏打开此工作空间"
            className="flex size-8 items-center justify-center rounded-lg text-[var(--text-muted)] hover:text-olive-700 hover:bg-olive-500/10 transition-colors"
          >
            <ExternalLink className="size-4" />
          </Link>

          {/* Maximize toggle */}
          <button
            type="button"
            onClick={onToggleMaximize}
            title={isMaximized ? "还原分栏宽度" : "最大化分栏宽度"}
            className="hidden sm:flex size-8 items-center justify-center rounded-lg text-[var(--text-muted)] hover:text-olive-700 hover:bg-olive-500/10 transition-colors"
          >
            {isMaximized ? (
              <Minimize2 className="size-4" />
            ) : (
              <Maximize2 className="size-4" />
            )}
          </button>

          {/* Close workspace */}
          <button
            type="button"
            onClick={onClose}
            title="收起分栏工作区"
            className="flex size-8 items-center justify-center rounded-lg text-[var(--text-muted)] hover:text-cinnabar-600 hover:bg-cinnabar-500/10 transition-colors ml-1"
          >
            <X className="size-4" />
          </button>
        </div>
      </div>

      {/* 2. Workspace Main Body - Preserves draft and object states across tab switches */}
      <div className="flex-1 overflow-y-auto">
        <div className={activeTab === "lab" ? "h-full" : "hidden"}>
          <LabWorkspace
            embedded
            initialRef={initialRef}
            draftPrediction={draftPrediction}
            sessionId={sessionId}
            onDiscuss={onDiscuss}
            onSaved={onSaved}
          />
        </div>

        <div className={activeTab === "reading" ? "h-full" : "hidden"}>
          <ReadingDomainView
            mode="canvas"
            initialReference={readingRef}
            onDiscuss={(ref, prompt) => {
              if (onDiscussReading) {
                onDiscussReading(ref, prompt);
              }
            }}
          />
        </div>

        <div className={activeTab === "study" ? "h-full" : "hidden"}>
          <StudyDomainView
            mode="canvas"
            onDiscussTask={(prompt, taskRef) => {
              if (onDiscussStudy) {
                onDiscussStudy(prompt, taskRef);
              }
            }}
            onStartTask={onStartStudyTask}
          />
        </div>
      </div>
    </div>
  );
}
