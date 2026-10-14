"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { MathMarkdown } from "@/components/math-view";
import { TeachBackEvidence } from "@/components/learning/teachback-evidence";
import { 
  LearningShell, 
  Notice, 
  learningInput, 
  learningButton, 
  learningButtonSecondary,
  AtelierFolioCard,
  SocraticCompanionBubble 
} from "@/components/learning/learning-shell";
import { learningRequest, stableRequestId, type ReadingUnit, type TeachBack } from "@/lib/learning-api";
import { getCurrentUserId } from "@/lib/demo-auth";
import { 
  Sparkles, 
  BookOpen, 
  Link as LinkIcon, 
  Clock, 
  HelpCircle, 
  CheckCircle2, 
  ArrowRight,
  PenTool,
  Quote
} from "lucide-react";

function evidenceDraft(key: string, fallback: Record<number, string>): Record<number, string> {
  try {
    const value = JSON.parse(localStorage.getItem(`${key}:evidence`) ?? "null");
    return value && typeof value === "object" && !Array.isArray(value) && Object.values(value).every((v) => typeof v === "string")
      ? value
      : fallback;
  } catch {
    return fallback;
  }
}

export default function TeachBackPage() {
  const [units, setUnits] = useState<ReadingUnit[]>([]);
  const [selected, setSelected] = useState("NA_NEWTON");
  const [text, setText] = useState("");
  const [evidence, setEvidence] = useState<Record<number, string>>({});
  const [result, setResult] = useState<TeachBack | null>(null);
  const [history, setHistory] = useState<TeachBack[]>([]);
  const [focusedCondition, setFocusedCondition] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const unit = units.find((u) => u.id === selected);
  const draftKey = `teach-back-draft:${getCurrentUserId()}:${selected}:${result?.id ?? "new"}`;

  const restore = (r: TeachBack, conditionId: string | null = null) => {
    const key = `teach-back-draft:${getCurrentUserId()}:${r.unit_id}:${r.id}`;
    setResult(r);
    setSelected(r.unit_id);
    setFocusedCondition(conditionId && r.conditions.some((c) => c.condition_id === conditionId) ? conditionId : null);
    setText(localStorage.getItem(key) ?? r.text);
    setEvidence(evidenceDraft(key, Object.fromEntries(r.conditions.map((c, i) => [i, c.student_quote ?? ""]))));
    window.history.replaceState(
      null,
      "",
      `/teach-back?id=${encodeURIComponent(r.id)}${conditionId && r.conditions.some((c) => c.condition_id === conditionId) ? `&condition=${encodeURIComponent(conditionId)}` : ""}`
    );
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const unitId = params.get("unit") ?? "NA_NEWTON";
    setFocusedCondition(params.get("condition"));
    setSelected(unitId);
    const key = `teach-back-draft:${getCurrentUserId()}:${unitId}:new`;
    setText(localStorage.getItem(key) ?? "");
    setEvidence(evidenceDraft(key, {}));
    Promise.all([
      learningRequest<{ units: ReadingUnit[] }>("/reading/units"),
      learningRequest<{ submissions: TeachBack[] }>("/teach-back/submissions"),
    ])
      .then(async ([a, b]) => {
        setUnits(a.units);
        setHistory(b.submissions);
        if (params.get("id")) {
          restore(await learningRequest<TeachBack>(`/teach-back/submissions/${encodeURIComponent(params.get("id")!)}`), params.get("condition"));
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <LearningShell
      title="费曼讲学台 · 这一次，你来做老师"
      description="用你自己的数学直觉与推导逻辑，向小珞讲清公式为什么可用、何时失效。将你的论述原句与核心定理条件一一锚定。"
    >
      <Notice error={error} />

      {loading ? (
        <div className="p-12 text-center rounded-2xl border border-paper-300/70 bg-[var(--bg-card)] text-sm text-[var(--text-secondary)]">
          正在恢复讲学论述存盘…
        </div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-12 items-start">
          {/* 左栏：知识点选择与讲学历史谱系 (3.5 cols) */}
          <aside className="lg:col-span-4 space-y-6">
            <AtelierFolioCard title="选择要讲透的定理" badge="课题" badgeVariant="olive">
              <p className="text-xs text-[var(--text-secondary)] mb-3">
                挑选一项课程章节，以讲授者视角梳理定理前提与反例：
              </p>
              <div className="space-y-1.5">
                {units.map((u) => {
                  const isSelected = selected === u.id;
                  return (
                    <button
                      type="button"
                      key={u.id}
                      disabled={busy}
                      className={`w-full flex items-center justify-between p-3 rounded-xl text-left text-xs sm:text-sm transition-all duration-200 ${
                        isSelected
                          ? "bg-olive-600/10 text-olive-800 dark:text-olive-200 font-semibold border border-olive-600/30 shadow-xs ring-1 ring-olive-600/20"
                          : "hover:bg-[var(--bg-hover)]/70 text-[var(--text-secondary)] border border-transparent"
                      }`}
                      onClick={() => {
                        setSelected(u.id);
                        setResult(null);
                        const key = `teach-back-draft:${getCurrentUserId()}:${u.id}:new`;
                        setEvidence(evidenceDraft(key, {}));
                        setText(localStorage.getItem(key) ?? "");
                        window.history.replaceState(null, "", `/teach-back?unit=${encodeURIComponent(u.id)}`);
                      }}
                    >
                      <span className="truncate pr-2">{u.title}</span>
                      <BookOpen className={`w-4 h-4 shrink-0 ${isSelected ? "text-olive-600" : "text-[var(--text-muted)]"}`} />
                    </button>
                  );
                })}
              </div>

              <div className="mt-6 border-t border-paper-200 dark:border-paper-800 pt-5">
                <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
                  <Clock className="w-3.5 h-3.5" />
                  <span>我的讲学存盘版本</span>
                </div>
                {history.length === 0 ? (
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                    暂未提交过讲学论述。完成右侧陈述并对照后，所有修订版本将保留于此。
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {[...history].reverse().map((r) => (
                      <li key={r.id}>
                        <button
                          type="button"
                          disabled={busy}
                          className="w-full rounded-xl border border-paper-200 dark:border-paper-800 p-3 text-left hover:bg-olive-500/5 hover:border-olive-500/30 transition-all text-xs"
                          onClick={() => restore(r)}
                        >
                          <div className="flex items-center justify-between gap-1 mb-1">
                            <span className="font-semibold text-[var(--text-primary)] truncate">
                              {r.title}
                            </span>
                            {r.parent_id && (
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-dai-500/10 text-dai-700">
                                补充修订
                              </span>
                            )}
                          </div>
                          <time className="text-[11px] text-[var(--text-muted)] font-mono">
                            {new Date(r.created_at).toLocaleString("zh-CN")}
                          </time>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </AtelierFolioCard>
          </aside>

          {/* 右栏：讲学大幕布与条件引线 (8.5 cols) */}
          <section className="lg:col-span-8 space-y-6">
            {!unit ? (
              <div className="p-12 text-center rounded-2xl border border-paper-300/70 bg-[var(--bg-card)] text-sm">
                当前来源不可用，请选择其他知识点。
              </div>
            ) : (
              <>
                {/* 课题指南条与三维论述支架 (Socratic Podium Stage) */}
                <div className="relative overflow-hidden p-5 rounded-2xl border border-olive-500/25 bg-gradient-to-br from-olive-500/[0.08] via-paper-50/40 dark:via-paper-900/40 to-transparent shadow-xs">
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                    <div>
                      <span className="text-[11px] font-mono uppercase text-olive-800 dark:text-olive-200 tracking-wider font-bold flex items-center gap-1.5 mb-1">
                        <Sparkles className="w-3.5 h-3.5 text-olive-600" />
                        讲学课题 · 费曼探针
                      </span>
                      <h2 className="font-title text-lg sm:text-xl font-bold text-[var(--text-primary)]">{unit.title}</h2>
                    </div>
                    <Link
                      href={`/reading?unit=${encodeURIComponent(unit.id)}`}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border border-olive-500/30 bg-[var(--bg-card)] text-olive-800 dark:text-olive-200 hover:bg-olive-500/10 transition-all shadow-2xs"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>对照教材原文依据 →</span>
                    </Link>
                  </div>

                  {/* 讲授三维思考支架 */}
                  <div className="grid sm:grid-cols-3 gap-2.5 pt-3 border-t border-olive-500/15 text-xs">
                    <div className="p-2.5 rounded-lg bg-[var(--bg-card)]/80 border border-paper-200 dark:border-paper-800">
                      <span className="font-semibold text-olive-800 dark:text-olive-200 block mb-0.5">1. 几何直观</span>
                      <span className="text-[11px] text-[var(--text-secondary)]">用切线与横轴交点说明逼近原理</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-[var(--bg-card)]/80 border border-paper-200 dark:border-paper-800">
                      <span className="font-semibold text-dai-800 dark:text-dai-200 block mb-0.5">2. 定理前提</span>
                      <span className="text-[11px] text-[var(--text-secondary)]">讲清为何必须 f&apos;(x) ≠ 0 与初值充分近</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-[var(--bg-card)]/80 border border-paper-200 dark:border-paper-800">
                      <span className="font-semibold text-ochre-800 dark:text-ochre-200 block mb-0.5">3. 经典反例</span>
                      <span className="text-[11px] text-[var(--text-secondary)]">给出一个切线水平摆动或发散的反例</span>
                    </div>
                  </div>
                </div>

                {/* 讲授与原句引线表单 */}
                <AtelierFolioCard
                  title={result ? "补充我的数学阐述" : "我的费曼讲学论述"}
                  badge={result ? "修订态" : "初撰态"}
                  badgeVariant="ochre"
                >
                  <form
                    onSubmit={async (e) => {
                      e.preventDefault();
                      setBusy(true);
                      setError("");
                      try {
                        const body = {
                          unit_id: unit.id,
                          source_hash: unit.source_hash,
                          text,
                          evidence: Object.fromEntries(Object.entries(evidence).filter(([, v]) => v.trim())),
                          parent_id: result?.id ?? null,
                        };
                        const request_id = stableRequestId(
                          localStorage,
                          `teach-back-request:${getCurrentUserId()}:${unit.id}`,
                          body,
                          () => crypto.randomUUID()
                        );
                        const saved = await learningRequest<TeachBack>("/teach-back/submissions", {
                          ...body,
                          request_id,
                        });
                        restore(saved);
                        setHistory((prev) => [...prev.filter((r) => r.id !== saved.id), saved]);
                      } catch (e) {
                        setError(e instanceof Error ? e.message : "保存失败，输入仍保留");
                      } finally {
                        setBusy(false);
                      }
                    }}
                    className="space-y-6"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label htmlFor="teach-text" className="block text-xs font-semibold text-[var(--text-secondary)]">
                          讲学正文（用你自己的话解释：为何收敛？依赖什么？何时停机？）
                        </label>
                        <span className="text-[11px] text-[var(--text-muted)] font-mono">{text.length} / 4000 字符</span>
                      </div>

                      {/* 快捷讲学论述参考 */}
                      <div className="flex flex-wrap gap-1.5 items-center mb-2.5">
                        <span className="text-[var(--text-muted)] text-[11px]">快捷讲学论述参考：</span>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => {
                            const demo = "牛顿法的核心是用当前切线交点逼近零点。当区间内一阶导数远离零时切线稳定，但如果选点靠近极值点或者出现拐点，切线斜率过平可能导致点被甩出区间。为了保证局部二次收敛，必须满足 f'(x) ≠ 0 以及初值充分靠近真实根。";
                            setText(demo);
                            localStorage.setItem(draftKey, demo);
                          }}
                          className="px-2 py-0.5 rounded-md bg-paper-200/80 dark:bg-paper-800 text-[11px] text-olive-800 dark:text-olive-200 hover:bg-olive-500/10 hover:border-olive-500/30 border border-transparent transition-all"
                        >
                          填入经典 Newton 收敛性讲学范本
                        </button>
                      </div>

                      <textarea
                        id="teach-text"
                        required
                        maxLength={4000}
                        rows={7}
                        className={`${learningInput} font-serif leading-relaxed text-sm`}
                        value={text}
                        onChange={(e) => {
                          setText(e.target.value);
                          localStorage.setItem(draftKey, e.target.value);
                        }}
                        placeholder="例如：牛顿法的核心是用当前切线交点逼近零点。当区间内一阶导数远离零时切线稳定，但如果选点靠近极值点或者出现拐点，切线斜率过平可能导致点被甩出区间..."
                      />
                    </div>

                    {/* 原句与定理条件映射字段 */}
                    <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-tertiary)] p-4 sm:p-5">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text-primary)]">
                          <Quote className="w-4 h-4 text-olive-600" />
                          <span>将我的论述原句与定理必备条件对应起来</span>
                        </div>
                        <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full border border-olive-500/30 bg-olive-500/10 text-olive-800 dark:text-olive-200 font-medium">
                          已锚定 {Object.values(evidence).filter((v) => v && v.trim()).length} / {unit.conditions.length} 项
                        </span>
                      </div>
                      <p className="text-xs text-[var(--text-secondary)] mb-4 leading-relaxed">
                        从上方讲学文本中截取一句话填入对应卡片。尚不确定的条件可留空，保存后逐项补充；对应原句不代表已自动核验正确。
                      </p>

                      <div className="space-y-3">
                        {unit.conditions.map((c, i) => (
                          <div key={c} className="rounded-xl border border-paper-300 dark:border-paper-700/80 bg-[var(--bg-card)] p-3.5 space-y-2">
                            <div className="flex items-center justify-between">
                              <label htmlFor={`teach-evidence-${i}`} className="block text-xs font-semibold text-[var(--text-primary)]">
                                前提 {i + 1}：{c}
                              </label>
                              {evidence[i]?.trim() ? (
                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-olive-500/10 text-olive-800 dark:text-olive-200 font-medium border border-olive-500/25">
                                  已挂钩原句
                                </span>
                              ) : (
                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-paper-200 dark:bg-paper-800 text-[var(--text-muted)]">
                                  待挂钩
                                </span>
                              )}
                            </div>
                            <input
                              id={`teach-evidence-${i}`}
                              maxLength={4000}
                              className={`${learningInput} text-xs py-2 font-serif`}
                              value={evidence[i] ?? ""}
                              onChange={(e) => {
                                const value = { ...evidence, [i]: e.target.value };
                                setEvidence(value);
                                localStorage.setItem(`${draftKey}:evidence`, JSON.stringify(value));
                              }}
                              placeholder="粘贴我讲学中的对应原句，例如：“当区间内一阶导数远离零时...”"
                            />
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="pt-2">
                      <button type="submit" disabled={busy || !text.trim()} className={learningButton}>
                        <Sparkles className="w-4 h-4 mr-1.5" />
                        {busy ? "对照存盘中…" : result ? "保存补充修订版本" : "保存讲学论述并对照条件"}
                      </button>
                    </div>
                  </form>
                </AtelierFolioCard>

                {/* 已保存版本的证据对照与助教反馈 */}
                {result && (
                  <AtelierFolioCard
                    title="已存盘版本的条件对照分析"
                    badge={
                      result.model_status === "self_review"
                        ? "自省对照模式"
                        : result.model_status === "unavailable"
                        ? "条件已归档"
                        : "证据已对齐"
                    }
                    badgeVariant="dai"
                  >
                    <p className="text-xs text-[var(--text-secondary)] mb-4 leading-relaxed">
                      已完整记录你的原话与知识源哈希。
                      {result.model_status === "self_review"
                        ? "当前未配置模型密钥，展示严密的自我讲学与条件清单映射。"
                        : result.model_status === "unavailable"
                        ? "模型暂不可用；原话与条件对照存底已永久留痕。"
                        : "模型评语与启发探针供反思参考，尚未经过正式数学核验。"}
                    </p>

                    <TeachBackEvidence saved={result} focusedCondition={focusedCondition} />

                    {result.model_commentary && !result.evidence_version && (
                      <div className="mt-6">
                        <SocraticCompanionBubble
                          title="助教的整体思维反馈"
                          content={<MathMarkdown content={result.model_commentary} />}
                        />
                      </div>
                    )}

                    <details className="mt-6 border-t border-paper-200 dark:border-paper-800 pt-4">
                      <summary className="cursor-pointer text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                        查看本次绑定的课程原文出处 (SHA: {result.source_hash?.slice(0, 16)})
                      </summary>
                      <div className="mt-3 p-3.5 rounded-xl bg-paper-100 dark:bg-paper-800/60 font-serif text-xs leading-relaxed text-[var(--text-secondary)]">
                        <MathMarkdown content={result.source_quote} />
                      </div>
                    </details>
                  </AtelierFolioCard>
                )}
              </>
            )}
          </section>
        </div>
      )}
    </LearningShell>
  );
}
