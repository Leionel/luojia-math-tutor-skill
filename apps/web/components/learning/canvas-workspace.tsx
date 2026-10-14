"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  FlaskConical, 
  BookOpen, 
  CalendarCheck2, 
  Maximize2, 
  Minimize2, 
  ExternalLink, 
  X, 
  Sparkles,
  ArrowRight,
  ShieldCheck,
  HelpCircle,
  Cpu,
  Layers,
  ChevronRight,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { LabWorkspace } from "./lab-workspace";
import type { RootContextRef } from "@/lib/learning-context";
import type { LabRun } from "@/lib/learning-api";
import { AtelierFolioCard, ConditionPillarBadge } from "./learning-shell";

export type WorkspaceTab = "lab" | "reading" | "study";

interface CanvasWorkspaceProps {
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
  onAskTutor?: (prompt: string) => void;
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
  onAskTutor,
}: CanvasWorkspaceProps) {
  // Reading workspace inline state
  const [selectedReadingChapter, setSelectedReadingChapter] = useState<"newton_thm" | "secant_thm" | "bisection_thm">("newton_thm");

  const readingChapters = [
    {
      id: "newton_thm" as const,
      title: "牛顿切线法局部收敛定理",
      source: "《数值分析》第 2 章 · 第 3 节",
      formula: "x_{k+1} = x_k - \\frac{f(x_k)}{f'(x_k)}",
      condition: "f(x^*) = 0 且 f'(x^*) \\neq 0，f''(x) 在根邻域内连续有界",
      quote: "设 f \\in C^2[a,b]，若 x^* 为单根且 f'(x^*) \\neq 0，则存在充分小邻域 U(x^*)，对任意初值 x_0 \\in U(x^*)，牛顿序列平方收敛于 x^*。",
      probeQuestion: "如果 f'(x^*) = 0（即 x^* 为重根），牛顿法的收敛阶为什么会退化为线性收敛？",
    },
    {
      id: "secant_thm" as const,
      title: "弦截法超线性收敛判定",
      source: "《数值分析》第 2 章 · 第 4 节",
      formula: "x_{k+1} = x_k - f(x_k)\\frac{x_k - x_{k-1}}{f(x_k) - f(x_{k-1})}",
      condition: "两初始点充分靠近单根，且 f''(x) 连续非零",
      quote: "弦截法避免了计算导数 f'(x)，其收敛阶为黄金分割比 p = (1 + √5)/2 ≈ 1.618，属于超线性收敛，但需要保存两个历史点。",
      probeQuestion: "弦截法在分母 f(x_k) - f(x_{k-1}) 趋近于零时，如何避免计算机浮点数的大数相消与舍入误差？",
    },
    {
      id: "bisection_thm" as const,
      title: "介值定理与二分法收敛界",
      source: "《高等数学》上册 · 闭区间连续函数性质",
      formula: "|x_k - x^*| \\le \\frac{b-a}{2^k}",
      condition: "f(x) 在 [a,b] 上连续，且 f(a) \\cdot f(b) < 0",
      quote: "二分法以严格的几何衰减率 (1/2)^k 逼近真解。虽然收敛速度慢于牛顿法，但对初值完全鲁棒，不存在发散或奇异风险。",
      probeQuestion: "在工业级数值软件中，为什么通常用二分法进行粗定位，再转入牛顿法或 Brent 法加速？",
    },
  ];

  const currentReading = readingChapters.find((c) => c.id === selectedReadingChapter) || readingChapters[0];

  // Study workspace inline state
  const studyTasks = [
    {
      id: "study-1",
      tag: "实战推演",
      title: "验证二次收敛与残差判据陷阱",
      desc: "利用牛顿法实验台观察：残差 |f(x_k)| 达到 10⁻⁸ 时，真误差 |x_k - x*| 是否一定同样小？",
      prompt: "我想深入探究：为什么在数值分析中，残差 |f(x_k)| 很小不能直接作为判断已经接近真根的充分条件？请结合条件数和导数大小引导我推导。",
    },
    {
      id: "study-2",
      tag: "病态探针",
      title: "初值敏感性与极限环震荡",
      desc: "设计一个使牛顿迭代出现 2 周期震荡循环的反例（例如 f(x) = x³ - x 在特异初值下的表现）。",
      prompt: "请以函数 f(x) = x^3 - 5x 为例，指导我寻找一个会产生 2 步循环震荡的特定初值 x_0，并分析为什么牛顿法无法跳出该循环。",
    },
    {
      id: "study-3",
      tag: "算法改良",
      title: "重根修正公式的加速验证",
      desc: "对比标准牛顿法与修正牛顿法 x_{k+1} = x_k - m·f(x_k)/f'(x_k) 在 m 重根下的迭代步数。",
      prompt: "针对具有重根的非线性方程，修正牛顿法 x_{k+1} = x_k - m * f(x_k)/f'(x_k) 是如何恢复二次收敛速率的？请推导其渐近误差常数。",
    },
  ];

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

      {/* 2. Workspace Main Body */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "lab" && (
          <LabWorkspace
            embedded
            initialRef={initialRef}
            draftPrediction={draftPrediction}
            sessionId={sessionId}
            onDiscuss={onDiscuss}
            onSaved={onSaved}
          />
        )}

        {activeTab === "reading" && (
          <div className="p-4 sm:p-6 space-y-6 max-w-4xl mx-auto">
            {/* Top Overview Banner */}
            <div className="rounded-2xl border border-paper-200/80 dark:border-paper-800/80 bg-linear-to-r from-olive-500/5 via-paper-100/50 to-transparent p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-xl bg-olive-600/10 text-olive-700 dark:text-olive-300 font-title font-bold text-lg">
                    典
                  </div>
                  <div>
                    <h3 className="font-title text-base sm:text-lg font-semibold text-[var(--text-primary)]">
                      经典定理与前置条件对照录
                    </h3>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                      带着条件读教材 · 确保每一个公式都知其适用范围与证明界限
                    </p>
                  </div>
                </div>
                <Link
                  href="/reading"
                  className="hidden sm:inline-flex items-center gap-1 text-xs font-semibold text-olive-700 hover:text-olive-800 dark:text-olive-300 transition-colors"
                >
                  <span>研读大厅</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Chapter selector tabs */}
              <div className="mt-4 flex flex-wrap gap-2 pt-3 border-t border-paper-200/50 dark:border-paper-800/50">
                {readingChapters.map((chapter) => (
                  <button
                    key={chapter.id}
                    type="button"
                    onClick={() => setSelectedReadingChapter(chapter.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      selectedReadingChapter === chapter.id
                        ? "bg-olive-600 text-white shadow-2xs font-semibold"
                        : "bg-[var(--bg-card)] text-[var(--text-secondary)] border border-paper-200 dark:border-paper-800 hover:border-olive-500/40"
                    }`}
                  >
                    {chapter.title}
                  </button>
                ))}
              </div>
            </div>

            {/* Selected Chapter Theorem Card */}
            <AtelierFolioCard
              index="原文精粹"
              title={currentReading.title}
              badge={
                <span className="font-mono text-[10px] text-olive-700 dark:text-olive-300 bg-olive-500/10 px-2 py-0.5 rounded-full border border-olive-500/20">
                  {currentReading.source}
                </span>
              }
            >
              <div className="space-y-4">
                {/* Theorem Core Quote */}
                <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-input)]/50 p-4">
                  <p className="text-xs font-mono font-semibold text-olive-700 dark:text-olive-300 mb-1.5">
                    【定理原文陈述】
                  </p>
                  <blockquote className="text-sm font-serif leading-relaxed text-[var(--text-primary)] border-l-2 border-olive-600 pl-3">
                    {currentReading.quote}
                  </blockquote>
                </div>

                {/* Preconditions Checklist */}
                <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-card)] p-4 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text-secondary)]">
                    <ShieldCheck className="w-4 h-4 text-olive-600" />
                    <span>核心成立条件审查</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-olive-500/5 border border-olive-500/15 text-xs text-olive-800 dark:text-olive-200 font-mono">
                    {currentReading.condition}
                  </div>
                </div>

                {/* Socratic Deep Probe Card */}
                <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-linear-to-br from-paper-100/60 to-transparent p-4 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-olive-700 dark:text-olive-300">
                    <Sparkles className="w-4 h-4" />
                    <span>学术伴读研讨探针</span>
                  </div>
                  <p className="text-xs text-[var(--text-primary)] leading-relaxed">
                    {currentReading.probeQuestion}
                  </p>

                  <div className="pt-2 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => onAskTutor?.(`请围绕“${currentReading.title}”，帮我解答这个关键疑问：${currentReading.probeQuestion}`)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-olive-600 hover:bg-olive-700 text-white shadow-2xs transition-all active:scale-95"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>将此疑问带入对话探讨</span>
                    </button>
                    <Link
                      href={`/reading?chapter=${currentReading.id}`}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--text-secondary)] hover:bg-paper-200/50 dark:hover:bg-paper-800/50 transition-colors"
                    >
                      <span>展开完整文献标注</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            </AtelierFolioCard>
          </div>
        )}

        {activeTab === "study" && (
          <div className="p-4 sm:p-6 space-y-6 max-w-4xl mx-auto">
            {/* Top Overview Banner */}
            <div className="rounded-2xl border border-paper-200/80 dark:border-paper-800/80 bg-linear-to-r from-olive-500/5 via-paper-100/50 to-transparent p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-xl bg-olive-600/10 text-olive-700 dark:text-olive-300 font-title font-bold text-lg">
                    课
                  </div>
                  <div>
                    <h3 className="font-title text-base sm:text-lg font-semibold text-[var(--text-primary)]">
                      今日数学日课案 · 伴读随测
                    </h3>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                      循序渐进 · 从“验证单根”到“破除病态发散”的递进式挑战
                    </p>
                  </div>
                </div>
                <Link
                  href="/study"
                  className="hidden sm:inline-flex items-center gap-1 text-xs font-semibold text-olive-700 hover:text-olive-800 dark:text-olive-300 transition-colors"
                >
                  <span>完整日课中心</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Study Task Cards */}
            <div className="space-y-4">
              {studyTasks.map((task, idx) => (
                <AtelierFolioCard
                  key={task.id}
                  index={`日课 ${idx + 1}`}
                  title={task.title}
                  badge={
                    <span className="font-mono text-[10px] text-olive-700 dark:text-olive-300 bg-olive-500/10 px-2 py-0.5 rounded-full border border-olive-500/20">
                      {task.tag}
                    </span>
                  }
                >
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-4">
                    {task.desc}
                  </p>

                  <div className="flex items-center justify-between pt-3 border-t border-paper-200/60 dark:border-paper-800/60">
                    <span className="text-[11px] text-[var(--text-muted)] flex items-center gap-1">
                      <HelpCircle className="w-3.5 h-3.5" />
                      苏格拉底式启发引导
                    </span>
                    <button
                      type="button"
                      onClick={() => onAskTutor?.(task.prompt)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-olive-600 hover:bg-olive-700 text-white shadow-2xs transition-all active:scale-95"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>在对话中开启此推演</span>
                    </button>
                  </div>
                </AtelierFolioCard>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
