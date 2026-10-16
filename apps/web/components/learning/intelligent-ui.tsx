"use client";
import {
  createContext,
  useContext,
  useId,
  useState,
  Component,
  type ReactNode,
} from "react";
import {
  createLibrary,
  defineComponent,
  Renderer,
} from "@openuidev/react-lang";
import { z } from "zod/v4";
import {
  FlaskConical,
  ArrowUpRight,
  BookOpen,
  CheckCircle2,
  HelpCircle,
  Copy,
  Check,
  Sparkles,
  Scale,
  Activity,
} from "lucide-react";
import type { TutorMeta } from "@/lib/api";
import type { LearningContextRef, RootSnapshot } from "@/lib/learning-context";
import type { LabRun } from "@/lib/learning-api";
import {
  evidenceText,
  parseTeachingDecision,
  resolveIntelligentUI,
  sameLearningReference,
  type TeachingDecision,
  type WorkspaceIntent,
} from "@/lib/intelligent-ui";
import { LatexRenderer } from "../latex-renderer";
import { RootActionCards } from "./root-action-card";
import { learningInput, learningButton } from "./learning-shell";

type Runtime = {
  decision: TeachingDecision;
  meta: TutorMeta;
  sessionId: string;
  messageId: string;
  disabled: boolean;
  context?: LearningContextRef;
  onWorkspace?: (intent: WorkspaceIntent) => void;
  onSaved?: (run: LabRun) => void;
};
const RuntimeContext = createContext<Runtime | null>(null);
const statusLabels = {
  supported: "局部有依据",
  partially_supported: "部分有依据",
  contradicted: "发现冲突",
  unknown: "待补条件",
};
const actionButton =
  "inline-flex min-h-11 items-center gap-2 rounded-xl border border-olive-600/30 bg-olive-500/5 px-4 text-xs sm:text-sm font-medium text-olive-800 dark:text-olive-200 hover:bg-olive-500/15 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-olive-600 disabled:opacity-40 transition-all cursor-pointer shadow-xs";
function useRuntime() {
  const value = useContext(RuntimeContext);
  if (!value) throw Error("Missing Learning UI context");
  return value;
}
const refProps = () => z.object({ evidence_ref: z.string() });

const SourceExcerpt = defineComponent({
  name: "SourceExcerpt",
  props: refProps(),
  description: "Server supplied source excerpt, referenced by its evidence id.",
  component: function SourceExcerptView({ props }) {
    const { decision } = useRuntime();
    const [copied, setCopied] = useState(false);
    const source = decision.sources.find((s) => s.id === props.evidence_ref);
    if (!source) return null;
    const text =
      evidenceText(source.data) || "请回到原工作区，核对这条来源的完整记录。";
    const handleCopy = () => {
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };
    return (
      <details className="group my-3 rounded-2xl border border-dai-500/25 bg-gradient-to-br from-dai-500/[0.04] to-dai-500/[0.01] p-3.5 sm:p-4 text-xs sm:text-sm shadow-2xs transition-all overflow-hidden">
        <summary className="flex cursor-pointer items-center justify-between font-medium text-dai-800 dark:text-dai-200 select-none">
          <span className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-dai-600 shrink-0" />
            <span className="font-title font-semibold tracking-wide">核对引用依据</span>
            <span className="rounded-md border border-dai-500/20 bg-dai-500/10 px-1.5 py-0.2 font-mono text-[10px] text-dai-700 dark:text-dai-300">
              {source.kind === "scoped_check"
                ? "限定范围核验"
                : source.kind === "model_opinion"
                  ? "模型意见"
                  : "本轮来源"}
            </span>
          </span>
          <span className="text-[11px] text-[var(--text-muted)] group-open:rotate-180 transition-transform">
            ▼
          </span>
        </summary>
        <div className="mt-3 border-t border-dai-500/15 pt-3">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] text-[var(--text-muted)]">
              SOURCE DATA / 原文或轨迹数据
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1 text-[11px] text-[var(--text-secondary)] hover:text-dai-700 dark:hover:text-dai-300 cursor-pointer"
            >
              {copied ? <Check className="w-3 h-3 text-olive-600" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? "已复制" : "复制"}</span>
            </button>
          </div>
          <div className="max-h-60 overflow-auto whitespace-pre-wrap break-words rounded-xl bg-[var(--bg-card)]/80 p-3 font-mono text-xs leading-relaxed border border-paper-200 dark:border-paper-800">
            <LatexRenderer content={text} />
          </div>
        </div>
      </details>
    );
  },
});

const ConditionChecklist = defineComponent({
  name: "ConditionChecklist",
  props: refProps(),
  description:
    "Review explicit and missing conditions from a model teaching decision.",
  component: function ConditionChecklistView() {
    const { decision } = useRuntime();
    return (
      <section
        aria-label="条件核对"
        className="my-3 rounded-2xl border border-paper-300/80 dark:border-paper-700/80 bg-[var(--bg-card)] p-4 sm:p-5 shadow-2xs"
      >
        <div className="flex items-center justify-between mb-3 border-b border-paper-200/60 dark:border-paper-800/60 pb-2">
          <h4 className="flex items-center gap-2 font-title text-xs sm:text-sm font-semibold text-[var(--text-primary)]">
            <Scale className="w-4 h-4 text-olive-600 shrink-0" />
            <span>结论成立 · 定理适用范围核对</span>
          </h4>
          <span className="font-mono text-[10px] text-[var(--text-muted)]">
            助教整理 · 严谨研学
          </span>
        </div>

        <div className="space-y-3 text-xs sm:text-sm">
          {decision.known_conditions.length > 0 && (
            <div className="rounded-xl border border-olive-500/25 bg-olive-500/[0.04] p-3">
              <div className="flex items-center gap-1.5 font-semibold text-olive-800 dark:text-olive-200 mb-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-olive-600 shrink-0" />
                <span>本轮明确具备的前提条件</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {decision.known_conditions.map((text, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 rounded-lg border border-olive-500/30 bg-[var(--bg-card)] px-2.5 py-1 text-xs text-[var(--text-primary)] font-mono"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-olive-500" />
                    <span>{text}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {decision.missing_conditions.length > 0 && (
            <div className="rounded-xl border border-ochre-500/30 bg-ochre-500/[0.04] p-3">
              <div className="flex items-center gap-1.5 font-semibold text-ochre-800 dark:text-ochre-200 mb-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-ochre-600 shrink-0" />
                <span>尚需补充核验的前提边界</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {decision.missing_conditions.map((text, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 rounded-lg border border-ochre-500/30 bg-[var(--bg-card)] px-2.5 py-1 text-xs text-[var(--text-primary)] font-mono"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-ochre-500" />
                    <span>{text}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {!decision.known_conditions.length &&
            !decision.missing_conditions.length && (
              <p className="text-xs text-[var(--text-secondary)] italic">
                本轮没有额外列出的条件；请结合正文核对适用范围。
              </p>
            )}
        </div>
      </section>
    );
  },
});

const PredictionForm = defineComponent({
  name: "PredictionForm",
  props: refProps(),
  description:
    "Write a local prediction before opening the same-session Lab; no automatic model call.",
  component: () => <Prediction />,
});

function Prediction() {
  const runtime = useRuntime(),
    id = useId();
  const [value, setValue] = useState("");
  const suggestions = [
    "预计 4~5 步二次收敛；依据是初值靠近根且导数非零。",
    "预计拐点附近死循环震荡；依据是局部切线反弹。",
    "预计对半收缩，约 14 步达到 10⁻⁴ 精度。",
  ];
  return (
    <section className="my-3 rounded-2xl border border-ochre-500/30 bg-gradient-to-br from-ochre-500/[0.05] via-transparent to-ochre-500/[0.02] p-4 sm:p-5 shadow-2xs">
      <div className="flex items-center justify-between mb-2">
        <label htmlFor={id} className="flex items-center gap-1.5 font-title font-semibold text-xs sm:text-sm text-ochre-800 dark:text-ochre-200">
          <Sparkles className="w-4 h-4 text-ochre-600 shrink-0" />
          <span>换条件前，先写下你的科学预测</span>
        </label>
        <span className="font-mono text-[10px] text-ochre-700 dark:text-ochre-300 bg-ochre-500/10 px-1.5 py-0.2 rounded border border-ochre-500/20">
          先验猜想
        </span>
      </div>
      <textarea
        id={id}
        name="ui-prediction"
        rows={2}
        maxLength={1000}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className={`${learningInput} text-xs leading-relaxed`}
        placeholder="我预计接下来会……；依据是……"
      />
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="text-[10px] text-[var(--text-muted)]">快捷填入：</span>
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setValue(s)}
            className="text-[10px] px-2 py-0.5 rounded-md border border-ochre-500/20 bg-ochre-500/10 text-ochre-800 dark:text-ochre-200 hover:bg-ochre-500/20 transition-colors cursor-pointer"
          >
            + {idx === 0 ? "二次收敛" : idx === 1 ? "拐点震荡" : "对半收缩"}
          </button>
        ))}
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-ochre-500/15 pt-3">
        <p className="text-[11px] text-[var(--text-secondary)]">
          只带入实验草稿；运行后才保存，不计为独立考核。
        </p>
        <button
          type="button"
          disabled={runtime.disabled || !runtime.onWorkspace || !value.trim()}
          onClick={() =>
            runtime.onWorkspace?.({
              ref: runtime.meta.learning_context?.ref,
              prediction: value.trim(),
            })
          }
          className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-b from-olive-600 to-olive-700 px-3.5 py-2 text-xs font-semibold text-white shadow-xs hover:from-olive-500 hover:to-olive-600 disabled:opacity-40 cursor-pointer transition-all"
        >
          <FlaskConical className="w-3.5 h-3.5" />
          <span>带着预测展开实验台</span>
        </button>
      </div>
    </section>
  );
}

const ParameterCompare = defineComponent({
  name: "ParameterCompare",
  props: refProps(),
  description: "Existing server-bound numerical preview and save controls.",
  component: function ParameterCompareView() {
    const runtime = useRuntime();
    return (
      <RootActionCards
        meta={runtime.meta}
        sessionId={runtime.sessionId}
        messageId={runtime.messageId}
        context={runtime.context}
        disabled={runtime.disabled}
        onSaved={runtime.onSaved}
      />
    );
  },
});

const RunTraceChart = defineComponent({
  name: "RunTraceChart",
  props: refProps(),
  description:
    "Plot real saved iteration values; data is resolved from the message snapshot.",
  component: function RunTraceChartView() {
    const { meta } = useRuntime();
    const snapshot = meta.learning_context;
    if (snapshot?.ref.kind !== "root_lab" || !("rows" in snapshot)) return null;
    const root = snapshot as RootSnapshot;
    const rows = root.rows;
    if (!rows.length) return null;
    const min = Math.min(...rows.map((r) => r.x)),
      max = Math.max(...rows.map((r) => r.x)),
      span = Math.max(max - min, 1e-12),
      last = Math.max(...rows.map((r) => r.k), 1);

    const points = rows.map((r) => ({
      cx: 40 + (r.k / last) * 430,
      cy: 130 - ((r.x - min) / span) * 100,
      ...r,
    }));
    const lineD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.cx} ${p.cy}`).join(" ");
    const areaD = `${lineD} L ${points[points.length - 1].cx} 140 L ${points[0].cx} 140 Z`;

    return (
      <figure className="my-3 rounded-2xl border border-paper-300/80 dark:border-paper-700/80 bg-[var(--bg-card)] p-4 sm:p-5 shadow-2xs">
        <div className="flex items-center justify-between mb-2">
          <figcaption className="flex items-center gap-2 font-title text-xs sm:text-sm font-semibold text-[var(--text-primary)]">
            <Activity className="w-4 h-4 text-olive-600" />
            <span>本轮已保存的近似值收敛轨迹</span>
          </figcaption>
          <span className="font-mono text-[10px] text-olive-700 dark:text-olive-300 bg-olive-500/10 px-2 py-0.5 rounded-full border border-olive-500/20">
            共 {root.total_rows} 步 · 引用 {rows.length} 步
          </span>
        </div>

        <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-input)]/40 p-3">
          <svg
            viewBox="0 0 500 160"
            role="img"
            aria-label="参考实验近似值散点折线图，横轴迭代次数，纵轴近似值"
            className="w-full text-olive-700 dark:text-olive-300 overflow-visible"
          >
            <defs>
              <linearGradient id="traceGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="currentColor" stopOpacity="0.25" />
                <stop offset="100%" stopColor="currentColor" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <line x1="40" y1="30" x2="475" y2="30" stroke="currentColor" strokeOpacity="0.1" strokeDasharray="3 3" />
            <line x1="40" y1="80" x2="475" y2="80" stroke="currentColor" strokeOpacity="0.1" strokeDasharray="3 3" />
            <line x1="40" y1="130" x2="475" y2="130" stroke="currentColor" strokeOpacity="0.2" />

            <path d={areaD} fill="url(#traceGrad)" />
            <path d={lineD} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

            {points.map((p) => (
              <g key={p.k} className="cursor-pointer group">
                <circle cx={p.cx} cy={p.cy} r={3.5} fill="var(--bg-card)" stroke="currentColor" strokeWidth="2" />
                <circle cx={p.cx} cy={p.cy} r={6} fill="currentColor" opacity="0.15" />
                <title>
                  k={p.k}, x={p.x.toPrecision(6)}, f(x)={p.fx.toExponential(2)}
                </title>
              </g>
            ))}

            <text x="40" y="152" fill="currentColor" fontSize="10" fontFamily="monospace">
              k=0
            </text>
            <text x="450" y="152" fill="currentColor" fontSize="10" fontFamily="monospace">
              k={last}
            </text>
            <text x="5" y="34" fill="currentColor" fontSize="10" fontFamily="monospace" opacity="0.7">
              {max.toPrecision(3)}
            </text>
            <text x="5" y="134" fill="currentColor" fontSize="10" fontFamily="monospace" opacity="0.7">
              {min.toPrecision(3)}
            </text>
          </svg>
        </div>

        <details className="mt-3 group">
          <summary className="cursor-pointer text-xs font-medium text-[var(--text-secondary)] hover:text-olive-700 dark:hover:text-olive-300">
            ▸ 展开查看数值明细表格 ({rows.length} 步)
          </summary>
          <div className="mt-2 max-h-48 overflow-auto rounded-lg border border-paper-200 dark:border-paper-800">
            <table className="w-full text-right text-xs">
              <thead className="bg-[var(--bg-input)] text-[var(--text-muted)] sticky top-0">
                <tr>
                  <th className="p-2 text-left">k 步数</th>
                  <th className="p-2">xₖ 近似值</th>
                  <th className="p-2">f(xₖ) 残差</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-paper-200/50 dark:divide-paper-800/50 font-mono">
                {rows.map((row) => (
                  <tr key={row.k} className="hover:bg-olive-500/5">
                    <td className="p-2 text-left text-[var(--text-muted)] font-bold">{row.k}</td>
                    <td className="p-2 text-[var(--text-primary)]">{row.x.toPrecision(7)}</td>
                    <td className="p-2 text-olive-700 dark:text-olive-300">{row.fx.toExponential(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </figure>
    );
  },
});

const LearningUI = defineComponent({
  name: "LearningUI",
  description:
    "Bounded learning interactions below an independently readable answer.",
  props: z.object({
    children: z.array(
      z.union([
        SourceExcerpt.ref,
        ConditionChecklist.ref,
        PredictionForm.ref,
        ParameterCompare.ref,
        RunTraceChart.ref,
      ]),
    ),
  }),
  component: ({ props, renderNode }) => <div>{renderNode(props.children)}</div>,
});
export const learningUILibrary = createLibrary({
  root: "LearningUI",
  components: [
    LearningUI,
    SourceExcerpt,
    ConditionChecklist,
    PredictionForm,
    ParameterCompare,
    RunTraceChart,
  ],
});

class UIFallback extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <p
        role="status"
        className="py-3 text-base sm:text-sm text-[var(--text-secondary)]"
      >
        交互内容暂不可用，请继续查看上方正文。
      </p>
    ) : (
      this.props.children
    );
  }
}

export function TeachingDecisionReceipt({ value }: { value: unknown }) {
  const decision = parseTeachingDecision(value);
  if (!decision) return null;
  const statusStyles: Record<string, string> = {
    supported: "border-olive-500/30 bg-olive-500/[0.05] text-olive-800 dark:text-olive-200",
    partially_supported: "border-ochre-500/30 bg-ochre-500/[0.05] text-ochre-800 dark:text-ochre-200",
    contradicted: "border-cinnabar-500/30 bg-cinnabar-500/[0.05] text-cinnabar-800 dark:text-cinnabar-200",
    unknown: "border-dai-500/30 bg-dai-500/[0.05] text-dai-800 dark:text-dai-200",
  };
  return (
    <details className={`my-3 rounded-2xl border p-3 sm:p-4 text-xs sm:text-sm shadow-2xs transition-all ${statusStyles[decision.claim_status] || "border-paper-300"}`}>
      <summary className="cursor-pointer font-medium flex items-center justify-between select-none">
        <span className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
          <span className="font-semibold font-title">助教研学判断 · {statusLabels[decision.claim_status]}</span>
          <span className="text-[10px] text-[var(--text-muted)] font-normal border border-current/20 px-1.5 py-0.2 rounded-md">
            模型建议 · 未经独立核验
          </span>
        </span>
        <span className="text-[10px] text-[var(--text-muted)]">详情 ▾</span>
      </summary>
      <div className="mt-2.5 pt-2 border-t border-current/15 leading-relaxed text-[var(--text-primary)]">
        <p>{decision.reason}</p>
        {decision.assessments.length > 0 && (
          <div className="mt-2.5 space-y-1.5">
            <span className="block text-[10px] text-[var(--text-muted)] font-mono font-bold">
              STEP ASSESSMENTS / 各步判断依据
            </span>
            {decision.assessments.map((item, i) => (
              <div key={i} className="flex items-start gap-1.5 font-mono text-xs">
                <span className="font-bold shrink-0">{statusLabels[item.status]}：</span>
                <span className="text-[var(--text-secondary)]">{item.claim}</span>
              </div>
            ))}
          </div>
        )}
        <p className="mt-2 text-[10px] text-[var(--text-muted)]">
          引用范围与模型判断分开记录；本条不会更新学生掌握度。
        </p>
      </div>
    </details>
  );
}
export function IntelligentUI({
  meta,
  sessionId,
  messageId,
  context,
  disabled,
  onWorkspace,
  onSaved,
}: {
  meta?: TutorMeta | null;
  sessionId: string;
  messageId?: string;
  context?: LearningContextRef;
  disabled?: boolean;
  onWorkspace?: (intent: WorkspaceIntent) => void;
  onSaved?: (run: LabRun) => void;
}) {
  const resolved = resolveIntelligentUI(meta, messageId);
  if (!resolved || !meta || !messageId) return null;
  const runtime: Runtime = {
    decision: resolved.decision,
    meta,
    sessionId,
    messageId,
    context,
    disabled:
      !!disabled || !sameLearningReference(context, meta.learning_context?.ref),
    onWorkspace,
    onSaved,
  };
  return (
    <RuntimeContext.Provider value={runtime}>
      <UIFallback key={resolved.artifact.artifact_id}>
        <Renderer
          library={learningUILibrary}
          response={resolved.artifact.response}
          isStreaming={false}
          publishObservability={false}
        />
        {onWorkspace && meta.learning_context?.ref.kind === "root_lab" && (
          <button
            type="button"
            disabled={runtime.disabled}
            className={actionButton}
            onClick={() => onWorkspace({ ref: meta.learning_context?.ref })}
          >
            展开实验工作区
            <ArrowUpRight aria-hidden="true" className="size-4" />
          </button>
        )}
      </UIFallback>
    </RuntimeContext.Provider>
  );
}
