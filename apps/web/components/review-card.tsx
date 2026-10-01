"use client";

import { useState } from "react";
import { useTheme } from "@/lib/theme-context";
import { CheckCircle2, AlertTriangle, ChevronDown, ChevronUp, Sparkles, BookOpen } from "lucide-react";

export type ReviewData = {
  concepts: string[];
  is_correct: boolean;
  mistake: string | null;
  mastery_score: number;
  mastery_label: string;
  mastery_delta: number;
  verification_kind?: string;
  verifier_summary?: string;
};

export function ReviewCard({
  data,
  onSimilar,
}: {
  data: ReviewData;
  onSimilar?: () => void;
}) {
  const isCorrect = data.is_correct;
  const deltaPercent = Math.abs(Math.round(data.mastery_delta * 100));
  const { t } = useTheme();
  const [isCompExpanded, setIsCompExpanded] = useState(true);

  return (
    <div className="mt-4 rounded-xl border border-[#dcd4c0] dark:border-[#3e3f36] bg-[#fbf9f4] dark:bg-[#20211d] overflow-hidden shadow-xs">
      {/* 顶栏：复盘状态与印签 */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#f4eee1] dark:bg-[#272824] border-b border-[#e6deca] dark:border-[#383a32]">
        <div className="flex items-center gap-2">
          {isCorrect ? (
            <span className="flex items-center gap-1.5 text-xs font-bold text-olive-700 dark:text-olive-300">
              <CheckCircle2 className="w-4 h-4 text-olive-600 dark:text-olive-400" />
              <span>{data.verification_kind === "llm_review" ? t("审查认为本步正确", "Review Suggests This Step Is Correct") : t("本步核对通过", "This Step Passed the Check")}</span>
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-xs font-bold text-cinnabar-700 dark:text-cinnabar-300">
              <AlertTriangle className="w-4 h-4 text-cinnabar-600 dark:text-cinnabar-400" />
              <span>{t("步骤存疑 · 考点复盘", "Step Review & Pitfall Diagnosis")}</span>
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-[var(--text-secondary)]">
            掌握度估计 {Math.round(data.mastery_score * 100)}% ({data.mastery_label})
          </span>
          <span className={`font-semibold ${data.mastery_delta >= 0 ? "text-olive-600 dark:text-olive-400" : "text-cinnabar-600 dark:text-cinnabar-400"}`}>
            {data.mastery_delta >= 0 ? "↑" : "↓"}{deltaPercent}%
          </span>
        </div>
      </div>

      <div className="p-4 space-y-3">
        {/* 考点标签 */}
        {data.concepts.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <span className="text-[var(--text-muted)] flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5 text-olive-600" />
              {t("核心考点", "Concepts")}:
            </span>
            {data.concepts.map((c) => (
              <span
                key={c}
                className="px-2 py-0.5 rounded text-[11px] font-medium bg-olive-500/10 text-olive-800 dark:text-olive-200 border border-olive-500/20"
              >
                {c}
              </span>
            ))}
          </div>
        )}

        {/* 融入 C 方案：特定疑难步骤的“对开学案复盘” (Comparison Mode) */}
        {data.mistake && (
          <div className="rounded-lg border border-[#e4dcbe] dark:border-[#3e3f36] bg-[#f7f3e8]/70 dark:bg-[#1a1b18] overflow-hidden mt-2">
            <button
              type="button"
              onClick={() => setIsCompExpanded(!isCompExpanded)}
              className="w-full flex items-center justify-between px-3 py-2 text-xs font-bold text-cinnabar-700 dark:text-cinnabar-300 bg-[#efe7d3] dark:bg-[#272824] hover:bg-[#eae0c8] transition-colors"
            >
              <span className="flex items-center gap-1.5">
                <span>⚡ 易错陷阱对照复盘学案</span>
              </span>
              <span className="flex items-center gap-1 text-[11px] font-normal text-[var(--text-muted)]">
                {isCompExpanded ? (
                  <><span>收起对照</span><ChevronUp className="w-3.5 h-3.5" /></>
                ) : (
                  <><span>展开双栏对照</span><ChevronDown className="w-3.5 h-3.5" /></>
                )}
              </span>
            </button>

            {isCompExpanded && (
              <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#e2d8bd] dark:divide-[#383a32] text-xs">
                {/* 左栏：学子失误断点 */}
                <div className="p-3 bg-white/50 dark:bg-black/20">
                  <div className="font-semibold text-cinnabar-700 dark:text-cinnabar-400 mb-1 flex items-center gap-1">
                    <span>【学子草稿断点 · 疑误分析】</span>
                  </div>
                  <div className="text-[var(--text-secondary)] leading-relaxed">
                    <span className="px-1.5 py-0.5 rounded bg-cinnabar-500/10 text-cinnabar-700 dark:text-cinnabar-300 font-semibold mr-1">
                      {data.mistake}
                    </span>
                    <p className="mt-1.5 text-[11.5px] text-[var(--text-muted)]">
                      {data.verifier_summary || "具体问题请结合本轮讲解核对，当前未提供更详细的检查依据。"}
                    </p>
                  </div>
                </div>

                {/* 右栏：导师正解与辨析 */}
                <div className="p-3 bg-olive-500/[0.03]">
                  <div className="font-semibold text-olive-700 dark:text-olive-300 mb-1 flex items-center gap-1">
                    <span>【正解准则 · 思维纠偏】</span>
                  </div>
                  <div className="text-[var(--text-secondary)] leading-relaxed text-[11.5px]">
                    根据本轮指出的问题，先核对所用规则的前提，再修改对应步骤；修改后可以再次提交检查。
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 底部动作：做类似题 */}
        {onSimilar && (
          <div className="pt-2 flex justify-end">
            <button
              onClick={onSimilar}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-olive-600 hover:bg-olive-700 text-white shadow-xs transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{t("针对性练习巩固", "Practice Similar Problem")}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
