"use client";

import { useTheme } from "@/lib/theme-context";

export type ReviewData = {
  concepts: string[];
  is_correct: boolean;
  mistake: string | null;
  mastery_score: number;
  mastery_label: string;
  mastery_delta: number;
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

  return (
    <div
      className="rounded-2xl p-4"
      style={{
        background: isCorrect
          ? "rgba(16,185,129,0.08)"
          : "rgba(245,158,11,0.08)",
        border: `1px solid ${isCorrect ? "rgba(16,185,129,0.2)" : "rgba(245,158,11,0.2)"}`,
      }}
    >
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xl">{isCorrect ? "\u2705" : "\u274c"}</span>
        <span
          className="font-semibold"
          style={{ color: "var(--text-primary)" }}
        >
          {t("\u7ec3\u4e60\u590d\u76d8", "Review")}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <span style={{ color: "var(--text-secondary)" }}>
            {t("\u8003\u70b9", "Concepts")}:
          </span>
          <div className="flex flex-wrap gap-1">
            {data.concepts.map((c) => (
              <span
                key={c}
                className="rounded-full px-2 py-0.5 text-xs"
                style={{
                  background: "var(--accent-light)",
                  color: "var(--text-accent)",
                }}
              >
                {c}
              </span>
            ))}
          </div>
        </div>

        {data.mistake && (
          <div className="flex items-center gap-2">
            <span style={{ color: "var(--text-secondary)" }}>
              {t("\u9519\u56e0", "Mistake")}:
            </span>
            <span
              className="rounded px-2 py-0.5 text-xs"
              style={{ background: "rgba(239,68,68,0.1)", color: "#dc2626" }}
            >
              {data.mistake}
            </span>
          </div>
        )}

        <div className="flex items-center gap-2">
          <span style={{ color: "var(--text-secondary)" }}>
            {t("\u638c\u63e1\u5ea6", "Mastery")}:
          </span>
          <span
            className="font-medium"
            style={{ color: "var(--text-primary)" }}
          >
            {Math.round(data.mastery_score * 100)}% ({data.mastery_label})
          </span>
          <span
            className="text-xs"
            style={{ color: data.mastery_delta > 0 ? "#10b981" : "#ef4444" }}
          >
            {data.mastery_delta > 0 ? "\u2191" : "\u2193"}
            {deltaPercent}%
          </span>
        </div>
      </div>

      {onSimilar && (
        <div className="mt-3">
          <button
            className="rounded-xl px-4 py-2 text-xs font-medium text-white transition-all"
            style={{ background: "var(--accent)" }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "var(--accent-hover)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "var(--accent)")
            }
            onClick={onSimilar}
          >
            {t(
              "\ud83d\udcdd \u505a\u7c7b\u4f3c\u9898",
              "\ud83d\udcdd Similar Exercise",
            )}
          </button>
        </div>
      )}
    </div>
  );
}
