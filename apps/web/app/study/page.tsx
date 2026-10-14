"use client";
import Link from "next/link";
import { useCallback, useEffect, useState, useMemo } from "react";
import { 
  LearningShell, 
  Notice, 
  learningButton, 
  learningButtonSecondary,
  learningInput, 
  AtelierFolioCard,
  SocraticCompanionBubble,
  NumericalTraceVisualizer
} from "@/components/learning/learning-shell";
import { 
  learningRequest, 
  parseTrace, 
  stableRequestId, 
  type StudyToday, 
  type StudyTask, 
  type LearningOverview 
} from "@/lib/learning-api";
import { getCurrentUserId } from "@/lib/demo-auth";
import { recommendationHref } from "@/lib/study-summary";
import type { LearningRecommendation } from "@/lib/learning-api";
import { 
  Sparkles, 
  CheckCircle2, 
  ArrowRight, 
  Clock, 
  RefreshCw, 
  BookOpen, 
  Calculator,
  ChevronRight,
  TrendingDown
} from "lucide-react";

const states: Record<string, { label: string; variant: "olive" | "ochre" | "cinnabar" | "dai" | "muted" }> = {
  planned: { label: "待开始", variant: "muted" },
  in_progress: { label: "演算中", variant: "ochre" },
  awaiting_check: { label: "反馈待确认", variant: "ochre" },
  verified_complete: { label: "独立检验通过", variant: "olive" },
  assisted_complete: { label: "练习已完成", variant: "olive" },
  needs_revision: { label: "需要修订", variant: "cinnabar" },
  unknown: { label: "尚不能确认", variant: "muted" },
  read_complete: { label: "已读完", variant: "olive" },
};

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
          const st = states[t.state] ?? { label: t.state, variant: "muted" as const };
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

export default function StudyPage() {
  const [today, setToday] = useState<StudyToday | null>(null);
  const [task, setTask] = useState<StudyTask | null>(null);
  const [trace, setTrace] = useState("");
  const [stop, setStop] = useState("residual");
  const [minutes, setMinutes] = useState(15);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<StudyTask[]>([]);
  const [recommendation, setRecommendation] = useState<LearningRecommendation | null>(null);

  const reload = useCallback(async () => {
    const [value, overview] = await Promise.all([
      learningRequest<StudyToday>("/study/today"),
      learningRequest<LearningOverview>("/learning/overview"),
    ]);
    setToday(value);
    setPending(overview.pending_tasks.filter((t) => !value.plan?.tasks.some((p) => p.id === t.id)));
    setRecommendation(overview.recommendation);
  }, []);

  const openTask = useCallback((value: StudyTask) => {
    setTask(value);
    const key = `learning-trace:${getCurrentUserId()}:${value.id}`;
    setTrace(localStorage.getItem(key) ?? value.feedback?.input?.iterates?.join(",") ?? "");
    setStop(localStorage.getItem(`${key}:stop`) ?? value.feedback?.input?.stop_reason ?? "residual");
    window.history.replaceState(null, "", `/study?task=${encodeURIComponent(value.id)}`);
  }, []);

  useEffect(() => {
    reload()
      .then(async () => {
        const selected = new URLSearchParams(window.location.search).get("task");
        if (selected) {
          openTask(await learningRequest<StudyTask>(`/study/tasks/${encodeURIComponent(selected)}`));
        }
      })
      .catch((e) => setError(e.message));
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

  const locked = busy || (!!task && ["planned", "awaiting_check", "assisted_complete", "verified_complete"].includes(task.state));
  const start = (id: string) => act(async () => {
    openTask(await learningRequest<StudyTask>(`/study/tasks/${id}/start`, {}));
  });

  const recommendedTaskId = recommendation && /^\/study\?task=([A-Za-z0-9_-]{1,80})$/.exec(recommendationHref(recommendation))?.[1];

  // 动态分析输入的轨迹点
  const parsedTraceValues = useMemo(() => {
    if (!trace.trim()) return [];
    try {
      return parseTrace(trace).filter((v): v is number => typeof v === "number");
    } catch {
      return [];
    }
  }, [trace]);

  return (
    <LearningShell
      title="今日研学 · 循序推演"
      description="结合到期复习与前日推演，有序完成核心任务；亲手计算并提交迭代序列，验证局部收敛阶。"
    >
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
                      const st = states[t.state] ?? { label: t.state, variant: "muted" as const };
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
                    badge={states[task.state]?.label ?? task.state}
                    badgeVariant={states[task.state]?.variant ?? "muted"}
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

                            {/* 快捷填入预设试算按钮 */}
                            <div className="flex flex-wrap gap-1.5 items-center mb-2.5">
                              <span className="text-[var(--text-muted)] text-[11px]">快捷填入试算：</span>
                              <button
                                type="button"
                                disabled={locked}
                                onClick={() => {
                                  const demo = `${task.challenge?.initial_value ?? 1.5}, 1.416667, 1.414216, 1.414214`;
                                  setTrace(demo);
                                  localStorage.setItem(`learning-trace:${getCurrentUserId()}:${task.id}`, demo);
                                }}
                                className="px-2 py-0.5 rounded-md bg-paper-200/80 dark:bg-paper-800 text-[11px] text-olive-800 dark:text-olive-200 hover:bg-olive-500/10 hover:border-olive-500/30 border border-transparent transition-all font-mono"
                              >
                                填入典型二次收敛序列
                              </button>
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
    </LearningShell>
  );
}
