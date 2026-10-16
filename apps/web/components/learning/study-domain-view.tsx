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
  SocraticCompanionBubble,
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

function PendingTasks({ tasks, busy, start }: { tasks: StudyTask[]; busy: boolean; start: (id: string) => void }) {
  if (tasks.length === 0) return null;
  return (
    <section className="mt-8 rounded-xl border border-paper-300/70 dark:border-paper-800/70 bg-[var(--bg-card)] p-4 sm:p-5">
      <div className="flex items-center gap-2 mb-2">
        <Clock className="w-4 h-4 text-olive-600" />
        <h3 className="font-semibold text-sm">此前的探索与未完成任务</h3>
      </div>
      <p className="text-xs text-[var(--text-secondary)] mb-3">
        包含开始过的独立检验；随时可恢复草稿并接续推演。
      </p>
      <ul className="space-y-2">
        {tasks.map((t) => {
          const st = studyStates[t.state] ?? { label: t.state, variant: "muted" as const };
          return (
            <li key={t.id}>
              <button
                type="button"
                disabled={busy}
                onClick={() => start(t.id)}
                className="w-full flex items-center justify-between p-2.5 rounded-lg border border-paper-200 dark:border-paper-800/60 hover:bg-olive-500/5 hover:border-olive-500/30 text-left text-xs sm:text-sm transition-all"
              >
                <span className="font-medium truncate pr-2">{t.title}</span>
                <span className="shrink-0 text-xs text-olive-700 dark:text-olive-300 font-medium">
                  {st.label} →
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
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
    const draftKey = `learning-trace:${getCurrentUserId()}:${t.id}`;
    setTrace(localStorage.getItem(draftKey) ?? localStorage.getItem(`trace-draft:${getCurrentUserId()}:${t.id}`) ?? t.feedback?.input?.iterates?.join(",") ?? "");
    setStop(localStorage.getItem(`${draftKey}:stop`) ?? t.feedback?.input?.stop_reason ?? "residual");
    if (mode === "full" && typeof window !== "undefined") {
      window.history.replaceState(null, "", `/study?task=${encodeURIComponent(t.id)}`);
    }
  }, [mode]);

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
        {today && (!today.plan || today.plan.tasks.length === 0) && (
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
              <span className="text-[10px] text-[var(--text-muted)]">基于已保存状态</span>
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

  const recommendedTaskId = recommendation && /^\/study\?task=([A-Za-z0-9_-]{1,80})$/.exec(recommendationHref(recommendation))?.[1];
  const locked = busy || (!!task && ["planned", "awaiting_check", "assisted_complete", "verified_complete"].includes(task.state));

  return (
    <div>
      <Notice error={error} />

      {!today ? (
        <div className="flex items-center justify-center p-12 rounded-2xl border border-paper-300/60 bg-[var(--bg-card)]">
          <RefreshCw className="w-5 h-5 animate-spin text-olive-600 mr-3" />
          <p className="text-sm text-[var(--text-secondary)]">{error ? "连接失败，可重新加载。" : "正在展开今日研学计划…"}</p>
        </div>
      ) : (
        <>
          {!today.persistent && (
            <div className="mb-6 flex items-center gap-2 p-3.5 rounded-xl border border-ochre-500/30 bg-ochre-500/5 text-xs sm:text-sm text-ochre-800 dark:text-ochre-200">
              <span className="font-semibold">演示提示：</span>
              当前为内存演示模式，服务重启后将恢复初始状态；配置 COURSE_STORE_PATH 可持久化保留成长记录。
            </div>
          )}

          {/* 助教基于历史记录的主动建议 */}
          {recommendation && (
            <div className="mb-8">
              <SocraticCompanionBubble
                title="助教小珞的今日导学建议"
                content={
                  <div>
                    <h3 className="font-semibold text-sm sm:text-base text-[var(--text-primary)] mb-1">
                      {recommendation.title}
                    </h3>
                    <p className="mb-3 text-xs sm:text-sm leading-relaxed">{recommendation.reason}</p>
                    {recommendedTaskId ? (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => act(async () => openTask(await learningRequest<StudyTask>(`/study/tasks/${recommendedTaskId}`)))}
                        className="inline-flex items-center gap-1.5 text-xs font-medium text-olive-700 dark:text-olive-300 hover:underline"
                      >
                        打开对应历史任务 <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    ) : recommendationHref(recommendation) === "/study" ? (
                      <a href="#study-content" className="inline-flex items-center gap-1.5 text-xs font-medium text-olive-700 dark:text-olive-300 hover:underline">
                        在下方任务单中挑选 <ArrowRight className="w-3.5 h-3.5" />
                      </a>
                    ) : (
                      <Link href={recommendationHref(recommendation)} className="inline-flex items-center gap-1.5 text-xs font-medium text-olive-700 dark:text-olive-300 hover:underline">
                        前往该知识模块 <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    )}
                  </div>
                }
              />
            </div>
          )}

          <div id="study-content" />

          {/* 尚未生成今日任务时的启程卡 */}
          {!today.plan && !task ? (
            <div className="max-w-2xl mx-auto space-y-6">
              <AtelierFolioCard
                index="01"
                title="开启今日数值研学日课"
                badge="规划时长"
                badgeVariant="olive"
              >
                <p className="text-sm text-[var(--text-secondary)] mb-5 leading-relaxed">
                  系统将根据艾宾浩斯复习曲线与前日推演表现，合理精选不超过 3 项核心微任务。
                </p>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="minutes" className="block text-xs font-semibold mb-2 text-[var(--text-secondary)]">
                      今日研习时间预算
                    </label>
                    <select
                      id="minutes"
                      name="minutes"
                      className={`${learningInput} max-w-xs`}
                      value={minutes}
                      onChange={(e) => setMinutes(Number(e.target.value))}
                    >
                      <option value={15}>15 分钟 · 快速温故与重点单步验算</option>
                      <option value={30}>30 分钟 · 完整收敛推导与深度对比</option>
                    </select>
                  </div>
                  <button
                    type="button"
                    disabled={busy}
                    className={learningButton}
                    onClick={() => act(async () => setToday(await learningRequest<StudyToday>("/study/plans", { minutes })))}
                  >
                    <Sparkles className="w-4 h-4 mr-1.5" />
                    生成今日研学航标
                  </button>
                </div>
              </AtelierFolioCard>
              <PendingTasks tasks={pending} busy={busy} start={start} />
            </div>
          ) : (
            /* 任务与演练双栏空间 */
            <div className="grid gap-8 lg:grid-cols-12 items-start">
              {/* 左侧：日课推进航标 (4 cols) */}
              <div className="lg:col-span-5 space-y-5">
                <AtelierFolioCard
                  title={today.local_date}
                  badge={today.plan ? `${today.plan.minutes} 分钟预算` : "此前任务"}
                  badgeVariant="dai"
                >
                  {today.plan?.stale && (
                    <div className="mb-4 p-3 rounded-lg bg-cinnabar-500/10 border border-cinnabar-500/20 text-xs text-cinnabar-700">
                      课程知识库版本已更新，已保留旧版本供前后核对。
                    </div>
                  )}

                  <div className="space-y-3 mt-2">
                    {(today.plan?.tasks ?? []).map((t, idx) => {
                      const isSelected = task?.id === t.id;
                      const st = studyStates[t.state] ?? { label: t.state, variant: "muted" as const };
                      return (
                        <div
                          key={t.id}
                          className={`p-4 rounded-xl border transition-all duration-200 cursor-pointer ${
                            isSelected
                              ? "border-l-4 border-l-olive-600 border-paper-300 dark:border-paper-700 bg-gradient-to-r from-olive-500/10 via-olive-500/5 to-transparent shadow-xs ring-1 ring-olive-600/20"
                              : "border-l-4 border-l-transparent border-paper-200 dark:border-paper-800/80 bg-[var(--bg-card)] hover:border-paper-300 dark:hover:border-paper-700 hover:shadow-2xs hover:-translate-y-0.5"
                          }`}
                          onClick={() => start(t.id)}
                        >
                          <div className="flex items-start justify-between gap-2 mb-1.5">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs px-1.5 py-0.5 rounded bg-paper-200 dark:bg-paper-800 text-[var(--text-muted)] font-bold">
                                {idx + 1}
                              </span>
                              <h4 className="font-semibold text-sm text-[var(--text-primary)]">{t.title}</h4>
                            </div>
                            <span className="text-xs px-2 py-0.5 rounded-full border border-current text-olive-700 dark:text-olive-300 font-medium shrink-0">
                              {st.label}
                            </span>
                          </div>
                          <p className="text-xs text-[var(--text-secondary)] leading-relaxed pl-6 mb-2">
                            {t.reason}
                          </p>
                          <div className="pl-6 flex items-center text-xs font-medium text-olive-700 dark:text-olive-300">
                            <span>{t.state === "planned" ? "开始这项任务" : "继续 / 回顾推演"}</span>
                            <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {today.reviews.length > 0 && (
                    <div className="mt-6 border-t border-paper-200 dark:border-paper-800 pt-4">
                      <div className="flex items-center gap-1.5 mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                        <Clock className="w-3.5 h-3.5" />
                        <span>后续巩固计划</span>
                      </div>
                      <div className="space-y-1.5 text-xs text-[var(--text-secondary)]">
                        {today.reviews.map((r) => (
                          <div key={r.id} className="flex items-center justify-between py-1 border-b border-paper-100 dark:border-paper-800/40">
                            <span>{r.id === "NA_NEWTON" ? "牛顿法求根" : r.id}</span>
                            <span className="font-mono">{new Date(r.due_at).toLocaleDateString("zh-CN")}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {!today.plan && (
                    <button
                      type="button"
                      className="mt-4 text-xs font-medium text-olive-700 dark:text-olive-300 hover:underline"
                      onClick={() => {
                        setTask(null);
                        window.history.replaceState(null, "", "/study");
                      }}
                    >
                      重新安排今日的新任务 →
                    </button>
                  )}
                </AtelierFolioCard>

                <PendingTasks tasks={pending} busy={busy} start={start} />
              </div>

              {/* 右侧：演算与检验核心舞台 (7 cols) */}
              <div className="lg:col-span-7">
                {!task ? (
                  <AtelierFolioCard title="选择一项任务展开演算" badge="等待选择" badgeVariant="muted">
                    <div className="py-8 text-center space-y-5">
                      <div className="w-12 h-12 rounded-2xl bg-olive-500/10 border border-olive-500/20 flex items-center justify-center mx-auto text-olive-700 dark:text-olive-300">
                        <Calculator className="w-6 h-6 stroke-[1.5]" />
                      </div>
                      <div className="space-y-1">
                        <h3 className="font-title text-base font-semibold text-[var(--text-primary)]">
                          从左侧挑选任务，开启推演留痕
                        </h3>
                        <p className="text-xs sm:text-sm text-[var(--text-secondary)] max-w-md mx-auto">
                          阅读记录、参考实验、练习完成与独立检验都会分别留痕保存，助教将实时分析收敛阶特征。
                        </p>
                      </div>

                      {/* 研学推进三阶微卡 */}
                      <div className="grid sm:grid-cols-3 gap-3 text-left pt-2">
                        <div className="p-3.5 rounded-xl border border-paper-200 dark:border-paper-800/80 bg-[var(--bg-tertiary)]">
                          <span className="text-[10px] font-mono uppercase text-olive-700 dark:text-olive-300 font-bold block mb-1">
                            STEP 01
                          </span>
                          <div className="font-semibold text-xs text-[var(--text-primary)] mb-1">典籍与条件</div>
                          <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                            明晰方程形态与初值，核验区间一阶导是否非零。
                          </p>
                        </div>
                        <div className="p-3.5 rounded-xl border border-paper-200 dark:border-paper-800/80 bg-[var(--bg-tertiary)]">
                          <span className="text-[10px] font-mono uppercase text-dai-700 dark:text-dai-300 font-bold block mb-1">
                            STEP 02
                          </span>
                          <div className="font-semibold text-xs text-[var(--text-primary)] mb-1">推演计算列</div>
                          <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                            输入实数迭代点序列，自动绘制相邻步长衰减。
                          </p>
                        </div>
                        <div className="p-3.5 rounded-xl border border-paper-200 dark:border-paper-800/80 bg-[var(--bg-tertiary)]">
                          <span className="text-[10px] font-mono uppercase text-ochre-700 dark:text-ochre-300 font-bold block mb-1">
                            STEP 03
                          </span>
                          <div className="font-semibold text-xs text-[var(--text-primary)] mb-1">判定收敛阶</div>
                          <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                            区分残差判定与区间萎缩，检验二次收敛性质。
                          </p>
                        </div>
                      </div>

                      <div className="pt-2">
                        <Link href="/reading" className="inline-flex items-center gap-1.5 text-xs font-semibold text-olive-700 dark:text-olive-300 hover:underline">
                          <span>或者先去浏览教材选段</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>
                  </AtelierFolioCard>
                ) : (
                  <AtelierFolioCard
                    title={task.title}
                    badge={studyStates[task.state]?.label ?? task.state}
                    badgeVariant={studyStates[task.state]?.variant ?? "muted"}
                  >
                    {task.state === "planned" && (
                      <div className="mb-4">
                        <button type="button" disabled={busy} className={learningButton} onClick={() => start(task.id)}>
                          正式开始这项任务
                        </button>
                      </div>
                    )}

                    {task.kind === "reading" ? (
                      <div className="space-y-4">
                        <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                          重点阅读知识包摘录，仔细核对定理的前提约束，尝试条件辨析。
                        </p>
                        <div className="flex flex-wrap gap-3">
                          <Link href={`/reading?unit=${task.unit_id}`} className={learningButtonSecondary}>
                            <BookOpen className="w-4 h-4 text-olive-600" />
                            打开对应教材材料
                          </Link>
                          <button
                            type="button"
                            disabled={busy || task.state === "read_complete"}
                            className={learningButton}
                            onClick={() => act(async () => openTask(await learningRequest<StudyTask>(`/study/tasks/${task.id}/read-complete`, {})))}
                          >
                            <CheckCircle2 className="w-4 h-4 mr-1" />
                            标记本篇已读完
                          </button>
                        </div>
                      </div>
                    ) : task.challenge && (
                      <div className="space-y-6">
                        {/* 方程展示卡片 (Elevated Math Studio Card) */}
                        <div className="relative overflow-hidden p-5 rounded-2xl border border-dai-500/30 bg-gradient-to-br from-dai-500/[0.08] via-paper-50/40 dark:via-paper-900/40 to-transparent shadow-xs">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[11px] font-mono uppercase text-dai-800 dark:text-dai-300 tracking-wider font-bold flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5 text-dai-600" />
                              目标非线性方程
                            </span>
                            <span className="px-2.5 py-0.5 rounded-full bg-dai-500/15 text-dai-800 dark:text-dai-200 text-[11px] font-mono font-medium border border-dai-500/25">
                              Newton-Raphson
                            </span>
                          </div>
                          <div className="font-mono text-xl sm:text-2xl font-bold text-[var(--text-primary)] tracking-wide my-1.5">
                            f(x) = {task.challenge.function}
                          </div>
                          <div className="mt-3 pt-3 border-t border-dai-500/15 flex flex-wrap gap-x-5 gap-y-1.5 text-xs text-[var(--text-secondary)]">
                            <span className="flex items-center gap-1.5">
                              <span className="text-[var(--text-muted)]">初始迭代点:</span>
                              <strong className="font-mono px-1.5 py-0.5 rounded bg-[var(--bg-card)] border border-paper-300 dark:border-paper-700 text-[var(--text-primary)]">
                                x₀ = {task.challenge.initial_value}
                              </strong>
                            </span>
                            <span className="flex items-center gap-1.5">
                              <span className="text-[var(--text-muted)]">收敛精度:</span>
                              <strong className="font-mono px-1.5 py-0.5 rounded bg-[var(--bg-card)] border border-paper-300 dark:border-paper-700 text-[var(--text-primary)]">
                                {task.challenge.goal === "root_error" ? "根误差" : "残差"} ≤ {task.challenge.tolerance}
                              </strong>
                            </span>
                            {task.challenge.interval && (
                              <span className="flex items-center gap-1.5">
                                <span className="text-[var(--text-muted)]">定义区间:</span>
                                <strong className="font-mono px-1.5 py-0.5 rounded bg-[var(--bg-card)] border border-paper-300 dark:border-paper-700 text-[var(--text-primary)]">
                                  [{task.challenge.interval.join(", ")}]
                                </strong>
                              </span>
                            )}
                          </div>
                        </div>

                        {task.state === "awaiting_check" && (
                          <div className="p-3.5 rounded-xl border border-ochre-500/30 bg-ochre-500/5 text-xs text-ochre-800 dark:text-ochre-200 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-ochre-500 animate-pulse shrink-0" />
                            <span>本次反馈已生成，请在下方点击“已读反馈，保存结果”，再按小珞的依据进行下一步修订或换题。</span>
                          </div>
                        )}

                        {/* 交互输入表单 */}
                        <form
                          className="space-y-4"
                          onSubmit={(e) => {
                            e.preventDefault();
                            act(async () => {
                              const attempt = {
                                ...task.challenge,
                                iterates: parseTrace(trace),
                                brackets: [],
                                stop_reason: stop,
                              };
                              const request_id = stableRequestId(
                                localStorage,
                                `learning-request:${getCurrentUserId()}:${task.id}`,
                                attempt,
                                () => crypto.randomUUID()
                              );
                              openTask(await learningRequest<StudyTask>(`/study/tasks/${task.id}/attempts`, { request_id, attempt }));
                            });
                          }}
                        >
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <label htmlFor="trace" className="block text-xs font-semibold text-[var(--text-secondary)]">
                                我的迭代点序列（包含初值 x₀）
                              </label>
                              <span className="text-[11px] text-[var(--text-muted)]">支持逗号、空格或换行分隔</span>
                            </div>

                            <textarea
                              disabled={locked}
                              id="trace"
                              name="trace"
                              className={`${learningInput} font-mono text-xs sm:text-sm`}
                              rows={4}
                              placeholder="例如：1.0, 1.416667, 1.414216 ..."
                              value={trace}
                              onChange={(e) => {
                                setTrace(e.target.value);
                                localStorage.setItem(`learning-trace:${getCurrentUserId()}:${task.id}`, e.target.value);
                              }}
                            />

                            {/* 动态收敛阶微雷达可视化 */}
                            <NumericalTraceVisualizer values={parsedTraceValues} />
                          </div>

                          <div>
                            <label htmlFor="stop" className="block text-xs font-semibold mb-2 text-[var(--text-secondary)]">
                              我判定的停机依据
                            </label>
                            <select
                              disabled={locked}
                              id="stop"
                              name="stop"
                              className={learningInput}
                              value={stop}
                              onChange={(e) => {
                                setStop(e.target.value);
                                localStorage.setItem(`learning-trace:${getCurrentUserId()}:${task.id}:stop`, e.target.value);
                              }}
                            >
                              <option value="residual">残差达到目标阈值 |f(x_k)| ≤ ε</option>
                              <option value="step">{"相邻迭代差达到阈值 |x_k - x_{k-1}| ≤ ε"}</option>
                              <option value="exact">零残差精准命中</option>
                              <option value="iteration_limit">已到达最大迭代步数上限</option>
                              <option value="none">尚未停止 / 未达到停机条件</option>
                            </select>
                          </div>

                          <button type="submit" disabled={locked} className={learningButton}>
                            <Sparkles className="w-4 h-4 mr-1.5" />
                            核对我的计算过程
                          </button>
                        </form>

                        {/* 过程反馈区块 */}
                        {task.feedback && (
                          <div className="mt-8 border-t border-paper-200 dark:border-paper-800 pt-5">
                            <SocraticCompanionBubble
                              title="小珞对你演算过程的诊断"
                              content={
                                <div className="space-y-3">
                                  <p className="font-medium text-sm text-[var(--text-primary)] leading-relaxed">
                                    {task.feedback.summary}
                                  </p>
                                  {task.feedback.next_probe && (
                                    <div className="p-3 rounded-lg bg-[var(--bg-card)] border border-dai-500/20 text-xs">
                                      <span className="font-semibold text-dai-700 dark:text-dai-300 mr-1">思考探针：</span>
                                      {task.feedback.next_probe}
                                    </div>
                                  )}
                                  <div className="pt-2 flex flex-wrap gap-3">
                                    {task.feedback.delivery === "pending" && (
                                      <button
                                        type="button"
                                        disabled={busy}
                                        className={learningButton}
                                        onClick={() =>
                                          act(async () =>
                                            openTask(
                                              await learningRequest<StudyTask>(`/study/tasks/${task.id}/ack`, {
                                                attempt_id: task.feedback?.attempt_id,
                                                feedback_id: task.feedback?.feedback_id,
                                              })
                                            )
                                          )
                                        }
                                      >
                                        已读反馈，保存本次结果
                                      </button>
                                    )}
                                    {["assisted_complete", "verified_complete"].includes(task.state) && (
                                      <button
                                        type="button"
                                        disabled={busy}
                                        className={learningButtonSecondary}
                                        onClick={() => act(async () => openTask(await learningRequest<StudyTask>(`/study/tasks/${task.id}/probe`, {})))}
                                      >
                                        换一题独立检验 →
                                      </button>
                                    )}
                                  </div>
                                </div>
                              }
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </AtelierFolioCard>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
