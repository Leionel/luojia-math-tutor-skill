"use client";

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

function verificationLabel(meta: TutorMeta | null) {
  if (!meta) return "尚未开始";
  if (!meta.verified) return "本轮无需验算";
  return meta.is_correct ? "验算正确" : "发现偏差";
}

function nextStepAdvice(
  meta: TutorMeta | null,
  mastery: MasteryItem[],
) {
  if (!meta) {
    return "输入一道题或写下你的推导步骤，面板会随本轮学习自动更新。";
  }
  const concept = meta.concepts?.[0]
    || meta.learning_objective
    || subjectMap[meta.subject]
    || "当前知识点";
  if (meta.verified && meta.is_correct === false) {
    return `先根据对话中的提示修正“${concept}”这一步，再独立重做一道同类题。`;
  }
  if (meta.verified && meta.is_correct === true) {
    return `本轮验算已通过。建议继续完成一道稍高难度的“${concept}”题，检验能否迁移。`;
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
  const [open, setOpen] = useState(false);
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
    <div className="flex w-full max-w-full flex-col gap-6">
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
          <Target className="h-3.5 w-3.5 text-[var(--accent)]" />
          当前考点
        </h2>
        <div className="flex flex-wrap gap-2">
          {concepts.slice(0, 5).map((concept) => (
            <span
              key={concept}
              className="rounded-full border border-[var(--border-subtle)] bg-[var(--bg-card)] px-3 py-1 text-[12px] font-medium text-[var(--text-secondary)] shadow-sm"
            >
              {concept}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
          <Brain className="h-3.5 w-3.5 text-emerald-500" />
          状态与复盘
        </h2>
        <div
          className={cn(
            "space-y-3 rounded-lg border bg-[var(--bg-card)] p-4 shadow-sm",
            meta?.verified && meta.is_correct
              ? "border-emerald-500/30"
              : "border-[var(--border-primary)]",
          )}
        >
          <div className="flex items-center justify-between gap-3 text-[13px]">
            <span className="text-[var(--text-muted)]">教学方式</span>
            <span className="text-right font-semibold text-[var(--text-primary)]">
              {meta ? intentMap[meta.intent] || meta.intent : "尚未开始"}
            </span>
          </div>
          <div className="flex items-center justify-between gap-3 text-[13px]">
            <span className="text-[var(--text-muted)]">后台验算</span>
            <span
              className={cn(
                "flex items-center gap-1 font-semibold",
                meta?.verified && meta.is_correct
                  ? "text-emerald-500"
                  : meta?.verified
                    ? "text-rose-500"
                    : "text-[var(--text-secondary)]",
              )}
            >
              {meta?.verified && meta.is_correct ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : meta?.verified ? (
                <XCircle className="h-4 w-4" />
              ) : null}
              {verificationLabel(meta)}
            </span>
          </div>

          {meta?.mistake && (
            <div className="flex items-start gap-2 rounded-md border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-500">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span className="font-medium">{meta.mistake}</span>
            </div>
          )}

          {meta?.mastery_score !== undefined && (
            <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
                  当前考点掌握度
                </div>
                <div className="text-sm font-bold text-[var(--text-primary)]">
                  {Math.round(meta.mastery_score * 100)}%
                  <span className="ml-1 text-[11px] font-medium opacity-60">
                    {meta.mastery_label || "待评估"}
                  </span>
                </div>
              </div>
              {!!meta.mastery_delta && (
                <div
                  className={cn(
                    "flex items-center gap-0.5 rounded-md border px-2 py-1 text-xs font-bold",
                    meta.mastery_delta > 0
                      ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-500"
                      : "border-rose-500/20 bg-rose-500/10 text-rose-500",
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
            <div className="flex w-fit items-center gap-1.5 rounded-md border border-amber-500/20 px-2.5 py-1.5 text-[11px] font-medium text-amber-500">
              <Lightbulb className="h-3.5 w-3.5" />
              已使用第 {meta.hint_level} 级提示
            </div>
          )}
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
            <BarChart2 className="h-3.5 w-3.5 text-[var(--accent)]" />
            能力雷达图
          </h2>
        </div>
        <div className="flex flex-col items-center gap-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] p-4">
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
    <>
      <button
        className="fixed bottom-24 right-4 z-40 flex items-center justify-center gap-2 rounded-full border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-2.5 text-sm font-medium text-[var(--text-primary)] shadow-lg transition-colors xl:hidden"
        onClick={() => setOpen((value) => !value)}
      >
        <Brain className="h-4 w-4 text-brand" />
        学习面板
      </button>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/20 backdrop-blur-sm xl:hidden"
          onClick={() => setOpen(false)}
        />
      )}
      <aside
        className={cn(
          "fixed right-0 top-16 z-40 h-[calc(100vh-4rem)] w-80 shrink-0 overflow-y-auto border-l border-[var(--border-primary)] bg-gray-50 p-6 transition-transform duration-300 dark:bg-[var(--bg-sidebar)] xl:static xl:h-full xl:w-full xl:translate-x-0",
          open ? "translate-x-0 shadow-2xl" : "translate-x-full",
        )}
      >
        {content}
      </aside>
    </>
  );
}
