"use client";

import React, { useCallback, useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { 
  Sparkles, 
  CheckCircle2, 
  ArrowRight, 
  Clock, 
  RefreshCw, 
  BookOpen, 
  Calculator,
  ChevronRight,
  TrendingDown,
  AlertCircle,
  ExternalLink,
  HelpCircle,
  Layers,
  MessageSquare
} from "lucide-react";
import { 
  AtelierFolioCard, 
  Notice, 
  learningButton, 
  learningButtonSecondary, 
  learningInput,
  NumericalTraceVisualizer
} from "./learning-shell";
import { 
  learningRequest, 
  parseTrace, 
  stableRequestId, 
  type StudyToday, 
  type StudyTask, 
  type LearningOverview,
  type LearningRecommendation
} from "@/lib/learning-api";
import { getCurrentUserId } from "@/lib/demo-auth";
import { recommendationHref, studyTaskHref } from "@/lib/study-summary";
import type { LearningContextRef, RootContextRef, ReadingContextRef } from "@/lib/learning-context";

export const studyStates: Record<string, { label: string; variant: "olive" | "ochre" | "cinnabar" | "dai" | "muted" }> = {
  planned: { label: "待开始", variant: "muted" },
  in_progress: { label: "演算中", variant: "ochre" },
  awaiting_check: { label: "反馈待确认", variant: "ochre" },
  verified_complete: { label: "独立检验通过", variant: "olive" },
  assisted_complete: { label: "练习已完成", variant: "olive" },
  needs_revision: { label: "需要修订", variant: "cinnabar" },
  unknown: { label: "尚不能确认", variant: "muted" },
  read_complete: { label: "已读完", variant: "olive" },
};

export interface StudyDomainViewProps {
  mode: "full" | "canvas";
  onStartTask?: (task: StudyTask) => void;
  onDiscussTask?: (prompt: string, taskRef?: LearningContextRef | null) => void;
}

export function StudyDomainView({
  mode,
  onStartTask,
  onDiscussTask,
}: StudyDomainViewProps) {
  const [today, setToday] = useState<StudyToday | null>(null);
  const [task, setTask] = useState<StudyTask | null>(null);
  const [trace, setTrace] = useState("");
  const [stop, setStop] = useState("residual");
  const [minutes, setMinutes] = useState(15);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<StudyTask[]>([]);
  const [recommendation, setRecommendation] = useState<LearningRecommendation | null>(null);

  const reload = useCallback(async () => {
    setError("");
    try {
      const [todayData, overviewData] = await Promise.all([
        learningRequest<StudyToday>("/study/today"),
        learningRequest<LearningOverview>("/learning/overview"),
      ]);
      setToday(todayData);
      setPending(
        overviewData.pending_tasks.filter((t) => !todayData.plan?.tasks.some((p) => p.id === t.id))
      );
      setRecommendation(overviewData.recommendation || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "获取今日研学计划失败");
    } finally {
      setLoading(false);
    }
  }, []);

  const openTask = useCallback((t: StudyTask) => {
    setTask(t);
    const draftKey = `trace-draft:${getCurrentUserId()}:${t.id}`;
    setTrace(localStorage.getItem(draftKey) ?? "");
    setStop("residual");
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", `/study?task=${encodeURIComponent(t.id)}`);
    }
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    reload().then(() => {
      if (!active) return;
      const params = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;
      const taskId = params?.get("task");
      if (taskId) {
        learningRequest<StudyTask>(`/study/tasks/${encodeURIComponent(taskId)}`)
          .then((t) => {
            if (active) openTask(t);
          })
          .catch((e) => {
            if (active) setError(e instanceof Error ? e.message : "读取任务失败");
          });
      }
    });

    return () => {
      active = false;
    };
  }, [reload, openTask]);

  const act = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setBusy(false);
    }
  };

  const start = (id: string) =>
    act(async () => {
      const started = await learningRequest<StudyTask>(`/study/tasks/${id}/start`, {});
      openTask(started);
      onStartTask?.(started);
    });

  // 动态分析输入的轨迹点
  const parsedTraceValues = useMemo(() => {
    if (!trace.trim()) return [];
    try {
      return parseTrace(trace).filter((v): v is number => typeof v === "number");
    } catch {
      return [];
    }
  }, [trace]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center">
        <div className="size-6 animate-spin rounded-full border-2 border-olive-600 border-t-transparent mb-3" />
        <p className="text-xs text-[var(--text-secondary)]">正在展开今日研学计划…</p>
      </div>
    );
  }

  // -------------------------------------------------------------
  // Mode: "canvas"（紧凑分栏工作区视窗）
  // -------------------------------------------------------------
  if (mode === "canvas") {
    return (
      <div className="p-4 sm:p-5 space-y-5">
        <Notice error={error} />

        {/* 顶部标题栏 */}
        <div className="flex items-center justify-between pb-3 border-b border-paper-200 dark:border-paper-800">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-olive-600" />
              <span>今日日课案 · 状态看板</span>
            </h3>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5">
              {today?.local_date ? `${today.local_date} 排定` : "实时排定"} · 证据驱动与错题巩固
            </p>
          </div>
          <Link
            href="/study"
            target="_blank"
            className="text-[11px] text-olive-700 dark:text-olive-300 hover:underline inline-flex items-center gap-1 font-medium"
          >
            <span>进入日课大厅</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>

        {/* 状态 1: 今日尚无排定计划 */}
        {(!today?.plan || today.plan.tasks.length === 0) && (
          <div className="p-6 rounded-2xl border border-dashed border-paper-300 dark:border-paper-700 bg-[var(--bg-card)]/60 text-center space-y-3">
            <p className="text-xs text-[var(--text-secondary)]">
              今日尚无排定任务。你可以随时在全量日课中心安排今日学习，或探索下方推荐挑战。
            </p>
            <Link
              href="/study"
              className={learningButtonSecondary}
            >
              安排今日学习计划
            </Link>
          </div>
        )}

        {/* 状态 2: 今日排定任务列表 */}
        {today?.plan && today.plan.tasks.length > 0 && (
          <div className="space-y-3">
            <div className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
              今日排定任务（{today.plan.tasks.length} 项）
            </div>
            {today.plan.tasks.map((t, idx) => {
              const stateBadge = studyStates[t.state] ?? { label: t.state, variant: "muted" as const };
              return (
                <AtelierFolioCard
                  key={t.id}
                  index={`任务 ${idx + 1}`}
                  title={t.title}
                  badge={
                    today?.plan?.stale ? "课程版本已更新 · 需核对" : stateBadge.label
                  }
                  badgeVariant={today?.plan?.stale ? "cinnabar" : stateBadge.variant}
                >
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-3">
                    {t.reason || "围绕当前核心概念的推演与独立检验任务。"}
                  </p>

                  <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-paper-200/60 dark:border-paper-800/60">
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">
                      任务代号: {t.id}
                    </span>
                    <div className="flex items-center gap-2">
                      <Link
                        href={`/study?task=${encodeURIComponent(t.id)}`}
                        className="text-[11px] text-olive-700 dark:text-olive-300 hover:underline font-medium"
                      >
                        在完整页面作答 →
                      </Link>
                      {onDiscussTask && (
                        <button
                          type="button"
                          onClick={() => {
                            // 映射任务到合法讨论 Prompt
                            const prompt = `针对今日任务【${t.title}】（状态：${stateBadge.label}）：${t.reason}。请以苏格拉底式提问引导我梳理推导思路。`;
                            // 无底层实体时传 null，绝不伪造非法 kind
                            onDiscussTask(prompt, null);
                          }}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-olive-600 hover:bg-olive-700 text-white shadow-2xs transition-all active:scale-95"
                        >
                          <MessageSquare className="w-3 h-3" />
                          <span>在对话中探讨</span>
                        </button>
                      )}
                    </div>
                  </div>
                </AtelierFolioCard>
              );
            })}
          </div>
        )}

        {/* 状态 3: 系统推荐任务（明确标明非今日排定） */}
        {recommendation && (
          <div className="rounded-2xl border border-paper-200/80 dark:border-paper-800/80 bg-linear-to-r from-olive-500/5 to-transparent p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-olive-700 dark:text-olive-300 flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                <span>系统推荐攻关点（非今日已排定计划）</span>
              </span>
              <span className="text-[10px] text-[var(--text-muted)]">基于掌握度模型</span>
            </div>
            <p className="text-xs font-medium text-[var(--text-primary)]">
              {recommendation.title}
            </p>
            <p className="text-xs text-[var(--text-secondary)]">
              {recommendation.reason}
            </p>
            <div className="pt-2 flex justify-end">
              <Link
                href={recommendationHref(recommendation)}
                className="text-xs font-semibold text-olive-700 dark:text-olive-300 hover:underline inline-flex items-center gap-1"
              >
                <span>前往推荐任务来源</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}

        {/* 状态 4: 到期复习与未完成任务 */}
        {pending.length > 0 && (
          <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-card)] p-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)] mb-2">
              <Clock className="w-3.5 h-3.5 text-olive-600" />
              <span>待接续或复习项（{pending.length} 项）</span>
            </div>
            <div className="space-y-1.5">
              {pending.slice(0, 3).map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between p-2 rounded-lg bg-[var(--bg-input)]/50 text-xs"
                >
                  <span className="truncate pr-2">{p.title}</span>
                  <span className="text-[10px] text-olive-700 dark:text-olive-300 font-mono shrink-0">
                    {studyStates[p.state]?.label || p.state}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // -------------------------------------------------------------
  // Mode: "full"（独立研学大厅完整视窗，带完整推演输入与打卡逻辑）
  // -------------------------------------------------------------
  const locked =
    busy || (!!task && ["planned", "awaiting_check", "assisted_complete", "verified_complete"].includes(task.state));

  return (
    <div className="space-y-8">
      <Notice error={error} />

      {!today ? (
        <div className="flex items-center justify-center p-12 rounded-2xl border border-paper-300/60 bg-[var(--bg-card)]">
          <RefreshCw className="w-5 h-5 animate-spin text-olive-600 mr-3" />
          <p className="text-sm text-[var(--text-secondary)]">
            {error ? "连接失败，可重新加载。" : "正在展开今日研学计划…"}
          </p>
        </div>
      ) : (
        <>
          {!today.persistent && (
            <div className="mb-6 flex items-center gap-2 p-3.5 rounded-xl border border-ochre-500/30 bg-ochre-500/5 text-xs sm:text-sm text-ochre-800 dark:text-ochre-200">
              <span className="font-semibold">演示提示：</span>
              当前为内存演示模式，服务重启后将恢复初始状态；配置 COURSE_STORE_PATH 可持久化保留成长记录。
            </div>
          )}

          {/* 阶段性推荐横幅 */}
          {recommendation && (
            <div className="mb-8 rounded-2xl border border-paper-300/80 dark:border-paper-700/80 bg-linear-to-r from-olive-500/10 via-paper-100/50 dark:via-paper-800/40 to-transparent p-5 sm:p-6 shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-olive-500/20 text-olive-800 dark:text-olive-200 border border-olive-500/30">
                      <Sparkles className="w-3 h-3 text-olive-600" />
                      系统推荐攻关点（非今日已排定计划）
                    </span>
                    <span className="text-xs text-[var(--text-muted)] font-mono">
                      来自知识图谱掌握度拓扑
                    </span>
                  </div>
                  <h3 className="font-title text-base sm:text-lg font-bold text-[var(--text-primary)]">
                    {recommendation.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-[var(--text-secondary)] leading-relaxed max-w-2xl">
                    {recommendation.reason}
                  </p>
                </div>
                <Link
                  href={recommendationHref(recommendation)}
                  className="shrink-0 inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-olive-600 hover:bg-olive-700 text-white text-xs sm:text-sm font-semibold shadow-xs hover:shadow-sm transition-all"
                >
                  <span>立即攻关</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          )}

          {/* 今日任务与推演区 */}
          {today.plan ? (
            <div className="grid gap-8 lg:grid-cols-12 items-start">
              {/* 左侧任务列表 (5 cols) */}
              <div className="lg:col-span-5 space-y-4">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                    今日任务清单（共 {today.plan.tasks.length} 项）
                  </h2>
                  <span className="text-xs text-[var(--text-muted)] font-mono">
                    预期用时 {today.plan.minutes} 分钟
                  </span>
                </div>
                {today.plan.tasks.map((t, index) => {
                  const isCurrent = task?.id === t.id;
                  const st = studyStates[t.state] ?? { label: t.state, variant: "muted" as const };
                  return (
                    <AtelierFolioCard
                      key={t.id}
                      index={`任务 ${index + 1}`}
                      title={t.title}
                      badge={today?.plan?.stale ? "课程版本已变化 · 需核对" : st.label}
                      badgeVariant={today?.plan?.stale ? "cinnabar" : st.variant}
                      className={isCurrent ? "ring-2 ring-olive-600/30" : ""}
                    >
                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-4">
                        {t.reason}
                      </p>
                      <div className="flex items-center justify-between pt-3 border-t border-paper-200 dark:border-paper-800">
                        <span className="text-xs text-[var(--text-muted)] font-mono">
                          {t.unit_id}
                        </span>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => (t.state === "planned" ? start(t.id) : openTask(t))}
                          className={learningButtonSecondary}
                        >
                          {t.state === "planned" ? "开启任务" : isCurrent ? "正在推演" : "查看详情"}
                        </button>
                      </div>
                    </AtelierFolioCard>
                  );
                })}
              </div>

              {/* 右侧推演详情 (7 cols) */}
              <div className="lg:col-span-7 space-y-6">
                {task ? (
                  <AtelierFolioCard
                    title={task.title}
                    badge={studyStates[task.state]?.label || task.state}
                    badgeVariant={studyStates[task.state]?.variant || "muted"}
                  >
                    <div className="space-y-4">
                      <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                        {task.reason}
                      </p>

                      {task.challenge && (
                        <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-input)]/40 p-4 space-y-2">
                          <span className="text-xs font-mono font-semibold text-olive-700 dark:text-olive-300">
                            【待检验算式】
                          </span>
                          <p className="font-mono text-sm">
                            f(x) = {task.challenge.function} · 初值 x₀ = {task.challenge.initial_value}
                          </p>
                        </div>
                      )}

                      {/* 推演轨迹输入 */}
                      <div className="space-y-2">
                        <label htmlFor="trace-input" className="block text-xs font-semibold text-[var(--text-secondary)]">
                          输入手动推演的迭代序列（空格或逗号分隔）
                        </label>
                        <textarea
                          id="trace-input"
                          rows={3}
                          value={trace}
                          disabled={locked}
                          onChange={(e) => {
                            setTrace(e.target.value);
                            localStorage.setItem(`trace-draft:${getCurrentUserId()}:${task.id}`, e.target.value);
                          }}
                          className={learningInput}
                          placeholder="例如: 1.5, 1.3478, 1.3252, 1.3247"
                        />
                      </div>

                      {/* 轨迹可视化 */}
                      {parsedTraceValues.length > 0 && (
                        <NumericalTraceVisualizer values={parsedTraceValues} />
                      )}
                    </div>
                  </AtelierFolioCard>
                ) : (
                  <div className="p-12 text-center rounded-2xl border border-paper-300/60 bg-[var(--bg-card)] text-xs sm:text-sm text-[var(--text-secondary)]">
                    请在左侧选择一个任务展开演算。
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center rounded-2xl border border-dashed border-paper-300 dark:border-paper-700 bg-[var(--bg-card)] space-y-4">
              <h3 className="font-title text-base sm:text-lg font-bold">今天还没有排定计划</h3>
              <p className="text-xs sm:text-sm text-[var(--text-secondary)] max-w-md mx-auto">
                系统可根据你的认知模型与错题记录，自动排定最适合今日攻关的数学任务。
              </p>
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  act(async () => {
                    await learningRequest("/study/plan", { minutes });
                  })
                }
                className={learningButton}
              >
                生成今日 {minutes} 分钟学习计划
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
