"use client";
import { verificationLabel } from "@/lib/message-status";

import { useEffect, useMemo, useState } from "react";
import type { MasteryItem, TutorMeta } from "@/lib/api";
import { fetchMastery } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  advanceMasteryTrend,
  parseMasteryTrendSnapshot,
  type MasteryTrend,
} from "@/lib/ui-runtime";
import { RadarChart } from "./radar-chart";
import { KnowledgeGraph } from "./knowledge-graph";
import {
  AlertCircle,
  BarChart2,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  History,
  Lightbulb,
  Sparkles,
  Target,
  XCircle,
} from "lucide-react";

const intentMap: Record<string, string> = {
  study_resume: "查看学习任务",
  concept: "概念讲解",
  solve_step_by_step: "分步引导",
  check_student_step: "步骤检查",
  full_solution: "完整解答",
  generate_exercise: "生成练习",
};

const subjectMap: Record<string, string> = {
  calculus: "微积分",
  linear_algebra: "线性代数",
  probability: "概率统计",
  foundations: "数学基础",
};

/**
 * Fixed competency axes for the radar chart.
 * Stable across sessions so the user can compare progress over time.
 * Each axis maps to a list of concept keywords matched against mastery records.
 * The last axis ("其他") is a catch-all so every mastery record contributes
 * to the overall score, even when the concept doesn't fit a named axis.
 */
const COMPETENCY_AXES: { axis: string; keywords: string[] }[] = [
  { axis: "微积分", keywords: ["积分", "导数", "极限", "洛必达", "泰勒", "微分", "连续", "数列", "级数", "中值", "Fubini"] },
  { axis: "线性代数", keywords: ["矩阵", "特征值", "QR", "正交", "Givens", "高斯消元", "向量", "行列式", "线性", "秩"] },
  { axis: "概率统计", keywords: ["概率", "正态", "分布", "期望", "方差", "贝叶斯", "样本", "假设检验", "随机"] },
  { axis: "符号运算", keywords: ["代数", "化简", "因式分解", "方程", "不等式", "多项式"] },
];

function categorizeConcept(concept: string): number {
  for (let i = 0; i < COMPETENCY_AXES.length; i++) {
    if (COMPETENCY_AXES[i].keywords.some((kw) => concept.includes(kw))) {
      return i;
    }
  }
  return COMPETENCY_AXES.length; // → catch-all "其他" axis
}

function aggregateCompetencyScores(items: MasteryItem[]): { label: string; value: number; assessed: boolean }[] {
  const buckets: MasteryItem[][] = [
    ...COMPETENCY_AXES.map(() => [] as MasteryItem[]),
    [] as MasteryItem[], // catch-all bucket
  ];
  for (const item of items) {
    buckets[categorizeConcept(item.concept)].push(item);
  }

  const allAxes = [
    ...COMPETENCY_AXES.map((a) => a.axis),
    "其他", // catch-all label
  ];

  return allAxes.map((label, i) => {
    const matched = buckets[i];
    if (matched.length === 0) {
      return { label, value: 0, assessed: false };
    }
    const totalWeight = matched.reduce((sum, m) => sum + Math.max(1, m.attempts_count), 0);
    const weighted =
      matched.reduce(
        (sum, m) => sum + m.score * Math.max(1, m.attempts_count),
        0,
      ) / totalWeight;
    return { label, value: weighted, assessed: true };
  });
}

type Mistake = {
  mistake_code: string;
  concept: string;
};

function nextStepAdvice(
  meta: TutorMeta | null,
  mastery: MasteryItem[],
) {
  if (!meta) {
    return "输入一道题或写下你的推导步骤，面板会随本轮学习自动更新。";
  }
  if (meta.verification_kind !== "root_oracle" && !meta.step_check?.eligible_learning_evidence) {
    return "先核对本轮说明的范围，补齐你自己的步骤或候选；参考计算、模型意见和历史回答不代表独立完成。";
  }
  const concept = meta.concepts?.[0]
    || meta.learning_objective
    || subjectMap[meta.subject]
    || "当前知识点";
  if (meta.verified && meta.is_correct === false) {
    return `先根据对话中的提示修正“${concept}”这一步，再独立重做一道同类题。`;
  }
  if (meta.verified && meta.is_correct === true) {
    return `这一步在说明范围内通过。接着做一道同类的“${concept}”题，检查是否能自己完成。`;
  }
  if ((meta.hint_level ?? 0) > 0) {
    return `沿着当前提示继续写出“${concept}”的下一步，并把你的推导发回来检查。`;
  }
  if (meta.pedagogical_action === "generate_exercise") {
    return `先独立完成当前练习，提交关键步骤后再查看验算与掌握度变化。`;
  }
  const currentMastery = mastery.find(
    (item) => meta.concepts?.includes(item.concept),
  );
  if (currentMastery && currentMastery.score < 0.6) {
    return `“${currentMastery.concept}”目前较薄弱，建议先复述条件，再做一个最小例题。`;
  }
  return `用自己的话总结“${concept}”的关键条件，然后尝试完成下一步推导。`;
}

export function LearningPanel({
  meta,
  mistakes,
}: {
  meta: TutorMeta | null;
  mistakes: Mistake[];
}) {
  const [activeTab, setActiveTab] = useState<"radar" | "graph">("radar");
  const [overallMastery, setOverallMastery] = useState<MasteryItem[]>([]);
  const [previousAverage, setPreviousAverage] = useState<number | null>(null);
  const [masteryTrend, setMasteryTrend] = useState<MasteryTrend | null>(null);

  useEffect(() => {
    let active = true;
    fetchMastery("demo-user")
      .then((items) => {
        if (active) setOverallMastery(items);
      })
      .catch(() => {
        if (active) setOverallMastery([]);
      });
    return () => {
      active = false;
    };
  }, [meta]);

  const concepts = useMemo(() => {
    if (meta?.concepts?.length) return meta.concepts;
    if (meta?.learning_objective) return [meta.learning_objective];
    if (meta?.subject) return [subjectMap[meta.subject] || meta.subject];
    return ["等待输入题目"];
  }, [meta]);

  const competencyScores = useMemo(
    () => aggregateCompetencyScores(overallMastery),
    [overallMastery],
  );

  // Average over assessed competency axes only — falls back to all axes if nothing assessed.
  const averageMastery = useMemo(() => {
    const assessed = competencyScores.filter((c) => c.assessed);
    if (assessed.length === 0) return null;
    return Math.round(
      (assessed.reduce((sum, c) => sum + c.value, 0) / assessed.length) * 100,
    );
  }, [competencyScores]);

  useEffect(() => {
    if (averageMastery === null) {
      setPreviousAverage(null);
      setMasteryTrend(null);
      return;
    }

    const userId = "demo-user";
    const storageKey = `luojia_mastery_trend_${userId}`;
    const fingerprint = JSON.stringify(
      [...overallMastery]
        .sort((a, b) => a.concept.localeCompare(b.concept))
        .map((item) => [
          item.concept,
          item.attempts_count,
          Math.round(item.score * 1000),
        ]),
    );
    const next = advanceMasteryTrend(
      parseMasteryTrendSnapshot(localStorage.getItem(storageKey)),
      fingerprint,
      averageMastery,
    );

    setPreviousAverage(next.previousAverage);
    setMasteryTrend(next.trend);
    localStorage.setItem(storageKey, JSON.stringify(next.snapshot));
  }, [averageMastery, overallMastery]);

  const advice = nextStepAdvice(meta, overallMastery);

  const content = (
    <div className="flex w-full max-w-full flex-col gap-5">
      <section>
        <h2 className="mb-2.5 flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-[var(--text-muted)] font-mono">
          <Target className="h-3.5 w-3.5 text-olive-600 dark:text-olive-400" />
          <span>当前重点考点 Focus</span>
        </h2>
        <div className="flex flex-wrap gap-2">
          {concepts.slice(0, 5).map((concept) => (
            <span
              key={concept}
              className="rounded-full border border-olive-500/20 bg-olive-500/5 px-3 py-1 text-[12px] font-medium text-olive-800 dark:text-olive-200 shadow-xs hover:border-olive-500/40 transition-colors"
            >
              {concept}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2.5 flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-[var(--text-muted)] font-mono">
          <Brain className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>诊断与复盘 Diagnostic</span>
        </h2>
        <div
          className={cn(
            "space-y-3 rounded-2xl border p-4 shadow-sm transition-all bg-[var(--bg-card)]",
            meta?.verified && meta.is_correct
              ? "border-emerald-500/30 bg-emerald-500/[0.02]"
              : meta?.verified && meta.is_correct === false
                ? "border-rose-500/30 bg-rose-500/[0.02]"
                : "border-[var(--border-subtle)]",
          )}
        >
          <div className="flex items-center justify-between gap-3 text-[13px]">
            <span className="text-[var(--text-muted)]">教学方式</span>
            <span className="text-right font-semibold text-[var(--text-primary)] px-2 py-0.5 rounded-md bg-[var(--bg-tertiary)]/70 text-xs">
              {meta ? intentMap[meta.intent] || meta.intent : "待激活"}
            </span>
          </div>
          <div className="flex items-center justify-between gap-3 text-[13px]">
            <span className="text-[var(--text-muted)]">本步检查</span>
            <span
              className={cn(
                "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold",
                meta?.verified && meta.is_correct
                  ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20"
                  : meta?.verified && meta.is_correct === false
                    ? "bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20"
                    : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)]",
              )}
            >
              {meta?.verified && meta.is_correct ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
              ) : meta?.verified && meta.is_correct === false ? (
                <XCircle className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" />
              ) : null}
              {verificationLabel(meta)}
            </span>
          </div>

          {meta?.step_check && meta.step_check.execution_status !== "not_requested" && (
            <div className="rounded-xl border border-olive-500/20 bg-olive-500/5 p-3 text-xs leading-relaxed text-[var(--text-secondary)]">
              <p>{meta.verifier_summary || "本次检查仅覆盖已声明的范围。"}</p>
              {meta.step_check.assumptions.map((condition, index) => <p key={index} className="mt-1">{condition}</p>)}
              {!meta.step_check.eligible_learning_evidence && <p className="mt-2 text-[var(--text-muted)]">本次结果不作为学生候选的学习更新。</p>}
            </div>
          )}

          {meta?.mistake && (
            <div className="flex items-start gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-700 dark:text-rose-300 leading-relaxed shadow-xs">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" />
              <span className="font-medium">{meta.mistake}</span>
            </div>
          )}

          {meta?.verified && !!meta.concepts?.length && meta.mastery_score !== undefined && (!meta.step_check || meta.step_check.eligible_learning_evidence) && (
            <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] font-mono">
                  <span title={meta.mastery_estimate_notice || "历史聚合估计：缺少逐条核验来源，不等于独立检验成绩。"}>考点掌握度估计 · 含历史记录</span>
                </div>
                <div className="text-base font-bold text-[var(--text-primary)] font-mono">
                  {Math.round(meta.mastery_score * 100)}%
                  <span className="ml-1.5 text-[11px] font-medium font-sans px-1.5 py-0.2 rounded bg-olive-500/10 text-olive-700 dark:text-olive-300">
                    {meta.mastery_label || "待评估"}
                  </span>
                </div>
              </div>
              {!!meta.mastery_delta && (
                <div
                  className={cn(
                    "flex items-center gap-0.5 rounded-full border px-2.5 py-1 text-xs font-bold font-mono shadow-xs",
                    meta.mastery_delta > 0
                      ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                      : "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-300",
                  )}
                >
                  {meta.mastery_delta > 0 ? (
                    <ChevronUp className="h-3.5 w-3.5" />
                  ) : (
                    <ChevronDown className="h-3.5 w-3.5" />
                  )}
                  {Math.abs(Math.round(meta.mastery_delta * 100))}%
                </div>
              )}
            </div>
          )}

          {!!meta?.hint_level && (
            <div className="flex w-fit items-center gap-1.5 rounded-lg border border-amber-500/25 bg-amber-500/10 px-2.5 py-1.5 text-[11px] font-medium text-amber-700 dark:text-amber-300">
              <Lightbulb className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
              已使用第 {meta.hint_level} 级提示
            </div>
          )}
        </div>
      </section>

      <section>
        <div className="mb-2.5 flex items-center justify-between gap-3">
          <h2 className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-[var(--text-muted)] font-mono">
            <BarChart2 className="h-3.5 w-3.5 text-olive-600 dark:text-olive-400" />
            <span>认知雷达与图谱 Radar</span>
          </h2>
          <div className="flex bg-[var(--bg-tertiary)] p-0.5 rounded-full border border-[var(--border-subtle)]">
             <button onClick={() => setActiveTab("radar")} className={cn("px-3 py-1 text-[11px] font-bold rounded-full transition-all", activeTab === "radar" ? "bg-white dark:bg-[#20211d] shadow-xs text-olive-700 dark:text-olive-300" : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]")}>
                雷达
             </button>
             <button onClick={() => setActiveTab("graph")} className={cn("px-3 py-1 text-[11px] font-bold rounded-full transition-all", activeTab === "graph" ? "bg-white dark:bg-[#20211d] shadow-xs text-olive-700 dark:text-olive-300" : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]")}>
                图谱
             </button>
          </div>
        </div>
        <div className="flex flex-col items-center gap-4 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-4 relative overflow-hidden shadow-sm">
          
          {activeTab === "radar" ? (
             <div className="flex flex-col items-center gap-4 w-full">
                <RadarChart
                  data={competencyScores.map((c) => ({
                    label: c.label,
                    value: c.value,
                    assessed: c.assessed,
                  }))}
                  size={220}
                />
                {averageMastery !== null ? (
                  <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-4 py-1.5 text-xs font-bold text-emerald-600 dark:text-emerald-400 shadow-sm">
                    <Sparkles className="h-3.5 w-3.5" />
                    综合掌握度 {averageMastery}%
                    {masteryTrend === "up" && (
                      <span title={previousAverage !== null ? `较上次 ${previousAverage}% 提升` : ""}>↑</span>
                    )}
                    {masteryTrend === "down" && (
                      <span title={previousAverage !== null ? `较上次 ${previousAverage}% 下降` : ""}>↓</span>
                    )}
                    {masteryTrend === "flat" && <span title="与上次基本一致">→</span>}
                  </div>
                ) : (
                  <div className="text-[11px] italic text-[var(--text-muted)]">
                    完成一次可验算的解题后，雷达图各能力轴将逐步填充。
                  </div>
                )}
                {/* Per-axis breakdown */}
                <div className="grid w-full grid-cols-1 gap-1.5 pt-2 border-t border-[var(--border-subtle)]">
                  {competencyScores.map((c) => (
                    <div key={c.label} className="flex items-center justify-between gap-2 text-[11px]">
                      <span className={c.assessed ? "text-[var(--text-secondary)]" : "text-[var(--text-muted)]/70 italic"}>
                        {c.label}
                      </span>
                      <span className={c.assessed ? "font-bold text-[var(--text-primary)]" : "text-[var(--text-muted)]/70"}>
                        {c.assessed ? `${Math.round(c.value * 100)}%` : "待评估"}
                      </span>
                    </div>
                  ))}
                </div>
             </div>
          ) : (
             <div className="w-full h-[350px] -mx-4 -mt-4 -mb-4">
               <KnowledgeGraph className="w-full h-full border-0 rounded-none !bg-transparent" />
             </div>
          )}
        </div>
      </section>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
          <History className="h-3.5 w-3.5" />
          最近错因
        </h2>
        <div className="space-y-2">
          {mistakes.length ? (
            mistakes.slice(0, 5).map((mistake, index) => (
              <div
                key={`${mistake.mistake_code}-${index}`}
                className="flex items-center gap-2 rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-2.5 text-[12px] font-medium text-amber-600 dark:text-amber-500"
              >
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                {mistake.concept || mistake.mistake_code}
              </div>
            ))
          ) : (
            <div className="px-2 text-[12px] italic text-[var(--text-muted)]">
              暂无错因记录。
            </div>
          )}
        </div>
      </section>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
          <Sparkles className="h-3.5 w-3.5 text-[var(--accent)]" />
          下一步建议
        </h2>
        <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-card)] p-4 text-[13px] leading-relaxed text-[var(--text-secondary)] shadow-sm">
          {advice}
        </div>
      </section>
    </div>
  );

  return (
    <aside className="h-full w-full min-h-0 overflow-y-auto border-l border-[var(--border-primary)] bg-[var(--bg-sidebar)] p-6">
      {content}
    </aside>
  );
}
