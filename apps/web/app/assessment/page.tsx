"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { 
  LearningShell, 
  Notice, 
  learningButton, 
  learningButtonSecondary,
  AtelierFolioCard,
  SocraticCompanionBubble 
} from "@/components/learning/learning-shell";
import { learningRequest, type Assessment } from "@/lib/learning-api";
import { assessmentDraft } from "@/lib/learning-input";
import { getCurrentUserId } from "@/lib/demo-auth";
import { 
  CheckCircle2, 
  HelpCircle, 
  Sparkles, 
  ArrowRight, 
  RotateCcw, 
  Layers, 
  Award,
  ChevronDown
} from "lucide-react";

export default function AssessmentPage() {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [history, setHistory] = useState<Assessment[]>([]);
  const [draft, setDraft] = useState<Record<string, number>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const setCurrent = useCallback((value: Assessment | null) => {
    setAssessment(value);
    const key = value ? `assessment-draft:${getCurrentUserId()}:${value.id}` : null;
    const restored = value?.state === "in_progress" ? assessmentDraft(localStorage.getItem(key!), value.questions, value.answers) : {};
    setDraft(restored);
    if (key) {
      if (value?.state === "in_progress") localStorage.setItem(key, JSON.stringify(restored));
      else localStorage.removeItem(key);
    }
    window.history.replaceState(null, "", value ? `/assessment?id=${encodeURIComponent(value.id)}` : "/assessment");
  }, []);

  const choose = (id: string, option: number) => {
    const next = { ...draft, [id]: option };
    setDraft(next);
    if (assessment) localStorage.setItem(`assessment-draft:${getCurrentUserId()}:${assessment.id}`, JSON.stringify(next));
  };

  useEffect(() => {
    learningRequest<{ assessments: Assessment[] }>("/assessments")
      .then(async (a) => {
        setHistory(a.assessments);
        const id = new URLSearchParams(window.location.search).get("id");
        setCurrent(id ? await learningRequest<Assessment>(`/assessments/${encodeURIComponent(id)}`) : a.assessments.find((item) => item.state === "in_progress") ?? null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [setCurrent]);

  const act = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setBusy(false);
    }
  };

  const completed = assessment?.state === "completed";
  const ended = assessment?.state === "abandoned";
  const closed = completed || ended;

  return (
    <LearningShell
      title="非线性方程求根 · 试金石自检"
      description="六道辨析题，深度覆盖适用条件、单步更新与停止依据。首次有效作答将留痕存盘，交卷后支持三层递进解析与弱项定向复盘。"
    >
      <Notice error={error} />

      {loading ? (
        <div className="p-12 text-center rounded-2xl border border-paper-300/70 bg-[var(--bg-card)] text-sm text-[var(--text-secondary)]">
          正在恢复测评记录…
        </div>
      ) : !assessment ? (
        <div className="max-w-3xl mx-auto space-y-6">
          <AtelierFolioCard
            title="非线性方程求根 · 章节认知试金石"
            badge="约 5–8 分钟"
            badgeVariant="ochre"
          >
            <p className="text-sm text-[var(--text-secondary)] mb-6 leading-relaxed">
              本套诊断试题旨在帮助你排查概念盲区（例如：一阶导数接近零时的停机风险、初值选取的局部性约束、牛顿法与弦截法的收敛阶差异）。开发版参考题用于自查，不作为正式科研测验成绩。
            </p>
            <button
              type="button"
              disabled={busy}
              className={learningButton}
              onClick={() =>
                act(async () => {
                  setCurrent(await learningRequest<Assessment>("/assessments", {}));
                  setDraft({});
                })
              }
            >
              <Sparkles className="w-4 h-4 mr-1.5" />
              开启本章自检
            </button>

            {history.length > 0 && (
              <div className="mt-8 border-t border-paper-200 dark:border-paper-800 pt-5">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
                  历史自检作答谱系
                </h3>
                <div className="space-y-2">
                  {history.map((a) => (
                    <button
                      type="button"
                      key={a.id}
                      disabled={busy}
                      onClick={() => setCurrent(a)}
                      className="w-full flex items-center justify-between p-3 rounded-xl border border-paper-200 dark:border-paper-800 text-xs sm:text-sm hover:bg-olive-500/5 hover:border-olive-500/30 transition-all text-left"
                    >
                      <div className="flex items-center gap-2">
                        <Award className="w-4 h-4 text-olive-600" />
                        <span className="font-medium text-[var(--text-primary)]">
                          {a.state === "completed"
                            ? `参考匹配 ${a.reference_matches} / ${a.questions.length}`
                            : a.state === "abandoned"
                            ? "已结束，不计分"
                            : "继续本次作答"}
                        </span>
                      </div>
                      <span className="font-mono text-xs text-[var(--text-muted)]">
                        ID: {a.id.slice(0, 8)} →
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </AtelierFolioCard>
        </div>
      ) : (
        <div className="max-w-4xl mx-auto space-y-6">
          {/* 状态看板 */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-[var(--bg-card)] border border-paper-300/80 dark:border-paper-700/80 shadow-soft">
            <div>
              <span className="text-xs font-mono uppercase text-[var(--text-muted)] font-semibold">自检状态</span>
              <h2 className="font-title text-xl font-bold text-[var(--text-primary)]">
                {completed
                  ? `匹配得分 ${assessment.score?.percentage ?? Math.round((100 * (assessment.reference_matches ?? 0)) / assessment.questions.length)} 分 · ${assessment.reference_matches} / ${assessment.questions.length}`
                  : `已确认进度 ${Object.keys(assessment.answers).length} / ${assessment.questions.length}`}
              </h2>
            </div>
            <div className="text-xs font-medium px-3 py-1.5 rounded-full border border-paper-300 dark:border-paper-700 bg-[var(--bg-tertiary)]">
              {completed ? "已完成交卷" : ended ? "已结束，不计分" : "首次确认选择后不能修改"}
            </div>
          </div>

          {completed && (
            <SocraticCompanionBubble
              title="小珞对本章自检的复盘"
              content={
                <div className="space-y-2">
                  <p>
                    {assessment.review_units?.length
                      ? `诊断建议回看 ${assessment.review_units.length} 个核心定理前置条件，下方每题均有逐层解析与直达材料。后续今日学习日课将优先排期。`
                      : "恭喜！这组参考题与标准答案完全匹配。可以继续前往实验台用更复杂的函数检验收敛过程。"}
                  </p>
                  <p className="text-[11px] text-[var(--text-muted)]">
                    {assessment.feedback_review_status === "development_unreviewed"
                      ? `已采用分层提示标准 ${assessment.feedback_version} · 开发参考版本。`
                      : "沿用经典参考题解。"}
                  </p>
                </div>
              }
            />
          )}

          {/* 答题快速跳转导航条 */}
          {!closed && (
            <nav aria-label="答题导航" className="p-4 rounded-xl bg-[var(--bg-card)] border border-paper-200 dark:border-paper-800 shadow-xs">
              <div className="flex items-center justify-between text-xs text-[var(--text-secondary)] mb-3">
                <span>选项草稿在当前标签页自动存盘，点击“确认”后永久保存。</span>
                <span className="font-mono">
                  {Object.keys(assessment.answers).length} / {assessment.questions.length} 已确认
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {assessment.questions.map((q, i) => {
                  const isAnswered = q.id in assessment.answers;
                  const isDraft = q.id in draft;
                  return (
                    <a
                      key={q.id}
                      href={`#assessment-question-${q.id}`}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                        isAnswered
                          ? "bg-olive-600/10 border-olive-600 text-olive-800 dark:text-olive-200 font-semibold"
                          : isDraft
                          ? "bg-ochre-500/10 border-ochre-500 text-ochre-800 dark:text-ochre-200"
                          : "border-paper-300 dark:border-paper-700 text-[var(--text-muted)] hover:border-paper-400"
                      }`}
                    >
                      {i + 1} · {isAnswered ? "已确认" : isDraft ? "草稿" : "未答"}
                    </a>
                  );
                })}
              </div>
            </nav>
          )}

          {/* 题目卡牌流 */}
          <ol className="space-y-6">
            {assessment.questions.map((q, index) => {
              const selected = assessment.answers[q.id] ?? draft[q.id];
              const saved = q.id in assessment.answers;
              const feedback = assessment.feedback?.find((f) => f.id === q.id);

              return (
                <li key={q.id} id={`assessment-question-${q.id}`} className="scroll-mt-24 list-none">
                  <AtelierFolioCard
                    index={index + 1}
                    title={q.prompt}
                    badge={saved ? "作答已存盘" : selected !== undefined ? "草稿待确认" : "待作答"}
                    badgeVariant={saved ? "olive" : selected !== undefined ? "ochre" : "muted"}
                    footer={
                      !closed ? (
                        <div className="w-full flex items-center justify-between">
                          <span className="text-xs text-[var(--text-muted)]">
                            {saved ? "本题作答已固化保存" : "请先选择选项，再点击确认"}
                          </span>
                          <button
                            type="button"
                            disabled={busy || saved || selected === undefined}
                            className={learningButton}
                            onClick={() =>
                              act(async () =>
                                setCurrent(
                                  await learningRequest<Assessment>(`/assessments/${assessment.id}/answers`, {
                                    question_id: q.id,
                                    option: selected,
                                  })
                                )
                              )
                            }
                          >
                            {saved ? "已保存" : "确认本题作答"}
                          </button>
                        </div>
                      ) : null
                    }
                  >
                    <fieldset disabled={saved || busy || closed} className="space-y-2.5 my-2">
                      {q.options.map((o, i) => {
                        const isChosen = selected === i;
                        return (
                          <label
                            key={o}
                            className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3.5 text-xs sm:text-sm leading-relaxed transition-all ${
                              isChosen
                                ? "border-olive-600 bg-olive-500/10 text-[var(--text-primary)] font-medium shadow-xs"
                                : "border-paper-300 dark:border-paper-700/80 bg-[var(--bg-card)] hover:border-paper-400"
                            }`}
                          >
                            <input
                              type="radio"
                              name={q.id}
                              value={i}
                              checked={isChosen}
                              onChange={() => choose(q.id, i)}
                              className="mt-0.5 h-4 w-4 shrink-0 accent-olive-600"
                            />
                            <span>{o}</span>
                          </label>
                        );
                      })}
                    </fieldset>

                    {/* 三层剥茧式解析反馈 */}
                    {feedback && (
                      <div className="mt-5 border-t border-paper-200 dark:border-paper-800 pt-4 space-y-3">
                        <div className="flex items-center gap-2">
                          {feedback.reference_match ? (
                            <span className="flex items-center gap-1.5 text-xs font-semibold text-olive-700 dark:text-olive-300">
                              <CheckCircle2 className="w-4 h-4" />
                              与参考选项一致
                            </span>
                          ) : (
                            <span className="flex items-center gap-1.5 text-xs font-semibold text-ochre-700 dark:text-ochre-300">
                              <HelpCircle className="w-4 h-4" />
                              与参考选项不同，先重审依据
                            </span>
                          )}
                        </div>

                        {feedback.layers ? (
                          <div className="space-y-2 text-xs sm:text-sm">
                            <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] border border-paper-200 dark:border-paper-700 text-[var(--text-secondary)]">
                              <strong className="text-[var(--text-primary)] block mb-1">第一层 · 条件探针：</strong>
                              {feedback.layers.condition}
                            </div>

                            <details className="group rounded-lg border border-paper-200 dark:border-paper-800 bg-[var(--bg-card)] p-3">
                              <summary className="cursor-pointer font-medium text-xs text-olive-700 dark:text-olive-300 flex items-center justify-between">
                                <span>第二层 · 方法思维提示（思考支架）</span>
                                <ChevronDown className="w-3.5 h-3.5 group-open:rotate-180 transition-transform" />
                              </summary>
                              <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                                {feedback.layers.method}
                              </p>
                            </details>

                            <details className="group rounded-lg border border-paper-200 dark:border-paper-800 bg-[var(--bg-card)] p-3">
                              <summary className="cursor-pointer font-medium text-xs text-olive-700 dark:text-olive-300 flex items-center justify-between">
                                <span>第三层 · 完整题解与收敛性反思</span>
                                <ChevronDown className="w-3.5 h-3.5 group-open:rotate-180 transition-transform" />
                              </summary>
                              <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                                {feedback.layers.full}
                              </p>
                            </details>
                          </div>
                        ) : (
                          <p className="text-xs sm:text-sm leading-relaxed text-[var(--text-secondary)]">
                            {feedback.explanation}
                          </p>
                        )}

                        <div className="pt-2">
                          <Link
                            href={`/reading?unit=${encodeURIComponent(feedback.unit_id)}`}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-olive-700 dark:text-olive-300 hover:underline"
                          >
                            <span>回到对应章节的定理条件</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </Link>
                        </div>
                      </div>
                    )}
                  </AtelierFolioCard>
                </li>
              );
            })}
          </ol>

          {/* 底部动作条 */}
          {!closed ? (
            <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-paper-200 dark:border-paper-800">
              <button
                type="button"
                disabled={busy}
                className="text-xs text-[var(--text-muted)] hover:text-cinnabar-700 hover:underline"
                onClick={() =>
                  act(async () => {
                    const result = await learningRequest<Assessment>(`/assessments/${assessment.id}/end`, {});
                    setCurrent(result);
                    setHistory((prev) => [...prev.filter((a) => a.id !== result.id), result]);
                  })
                }
              >
                结束本次自检，保留作答记录且不计分
              </button>

              <button
                type="button"
                disabled={busy || Object.keys(assessment.answers).length !== assessment.questions.length}
                className={learningButton}
                onClick={() =>
                  act(async () => {
                    const result = await learningRequest<Assessment>(`/assessments/${assessment.id}/submit`, {});
                    setCurrent(result);
                    setHistory((prev) => [...prev.filter((a) => a.id !== result.id), result]);
                  })
                }
              >
                <CheckCircle2 className="w-4 h-4 mr-1.5" />
                交卷并解锁三层参考题解
              </button>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-4 pt-4 border-t border-paper-200 dark:border-paper-800">
              <Link href="/study" className={learningButton}>
                回到今日学习日课
              </Link>
              <button
                type="button"
                disabled={busy}
                className={learningButtonSecondary}
                onClick={() => {
                  setCurrent(null);
                  setDraft({});
                }}
              >
                <RotateCcw className="w-3.5 h-3.5 mr-1" />
                回看历史或再做一份
              </button>
            </div>
          )}
        </div>
      )}
    </LearningShell>
  );
}
