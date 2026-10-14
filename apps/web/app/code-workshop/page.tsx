"use client";
import { useEffect, useState, useMemo } from "react";
import { 
  LearningShell, 
  Notice, 
  learningInput, 
  learningButton, 
  learningButtonSecondary,
  AtelierFolioCard,
  SocraticCompanionBubble,
  NumericalTraceVisualizer
} from "@/components/learning/learning-shell";
import { 
  learningRequest, 
  parseTrace, 
  stableRequestId, 
  type CodeAssignment, 
  type CodeSubmission 
} from "@/lib/learning-api";
import { SavedCodeReview } from "@/components/learning/saved-code-review";
import { getCurrentUserId } from "@/lib/demo-auth";
import { 
  Code2, 
  Terminal, 
  Clock, 
  Sparkles, 
  FileCode, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight,
  TrendingDown,
  Layers
} from "lucide-react";

const diagnosticLabels: Record<string, string> = {
  supported: "证据支持",
  contradicted: "发现偏差",
  inconclusive: "尚不能确认",
  tool_error: "诊断失败",
};
const diagnosticLabel = (status: string | null | undefined) => diagnosticLabels[status ?? ""] ?? "未提交";

export default function CodeWorkshopPage() {
  const [assignment, setAssignment] = useState<CodeAssignment | null>(null);
  const [code, setCode] = useState("");
  const [trace, setTrace] = useState("");
  const [stop, setStop] = useState("none");
  const [result, setResult] = useState<CodeSubmission | null>(null);
  const [history, setHistory] = useState<CodeSubmission[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const draftKey = `code-workshop:${getCurrentUserId()}:${result?.id ?? "new"}`;

  const restore = (s: CodeSubmission) => {
    const key = `code-workshop:${getCurrentUserId()}:${s.id}`;
    setResult(s);
    setCode(localStorage.getItem(`${key}:code`) ?? s.code);
    setTrace(localStorage.getItem(`${key}:trace`) ?? s.iterates.join(", "));
    setStop(localStorage.getItem(`${key}:stop`) ?? s.stop_reason);
    window.history.replaceState(null, "", `/code-workshop?id=${encodeURIComponent(s.id)}`);
  };

  useEffect(() => {
    Promise.all([
      learningRequest<CodeAssignment>("/code-workshop/assignment"),
      learningRequest<{ submissions: CodeSubmission[] }>("/code-workshop/submissions"),
    ])
      .then(async ([a, b]) => {
        setAssignment(a);
        setHistory(b.submissions);
        setCode(localStorage.getItem(`code-workshop:${getCurrentUserId()}:new:code`) ?? a.template);
        setTrace(localStorage.getItem(`code-workshop:${getCurrentUserId()}:new:trace`) ?? "");
        setStop(localStorage.getItem(`code-workshop:${getCurrentUserId()}:new:stop`) ?? "none");
        const id = new URLSearchParams(window.location.search).get("id");
        if (id) restore(await learningRequest<CodeSubmission>(`/code-workshop/submissions/${encodeURIComponent(id)}`));
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // 代码行数与行号槽
  const lineCount = useMemo(() => {
    return Math.max(code.split("\n").length, 12);
  }, [code]);

  // 代码是否有未保存修改
  const isDirty = (result && code !== result.code) || (!result && assignment && code !== assignment.template);

  // 动态分析本地轨迹序列
  const parsedTraceValues = useMemo(() => {
    if (!trace.trim()) return [];
    try {
      return parseTrace(trace).filter((v): v is number => typeof v === "number");
    } catch {
      return [];
    }
  }, [trace]);

  // Tab 键支持缩进
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const nextCode = code.substring(0, start) + "    " + code.substring(end);
      setCode(nextCode);
      localStorage.setItem(`${draftKey}:code`, nextCode);
      requestAnimationFrame(() => {
        target.selectionStart = target.selectionEnd = start + 4;
      });
    }
  };

  return (
    <LearningShell
      title="算法工坊 · 静态代码审阅"
      description="Newton 法等经典作业的代码规范核对与数值轨迹诊断。学生代码安全隔离不予执行，呈现严密数学依据。"
    >
      <Notice error={error} />

      {loading ? (
        <div className="p-12 text-center rounded-2xl border border-paper-300/70 bg-[var(--bg-card)] text-sm text-[var(--text-secondary)]">
          正在恢复代码作业与版本树…
        </div>
      ) : !assignment ? (
        <div className="p-12 text-center rounded-2xl border border-paper-300/70 bg-[var(--bg-card)] text-sm leading-relaxed text-cinnabar-700">
          作业暂不可用，请先处理上方提示后重新加载。
        </div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-12 items-start">
          {/* 左栏：规范看板与历史提交版本树 (3.5 cols) */}
          <aside className="lg:col-span-4 space-y-6">
            <AtelierFolioCard title={assignment.title} badge="Newton 法作业" badgeVariant="olive">
              <div className="relative overflow-hidden p-4 rounded-xl bg-dai-500/[0.07] border border-dai-500/20 text-xs font-mono space-y-1.5 mb-4">
                <div className="font-bold text-sm text-[var(--text-primary)]">目标方程：f(x) = x² − 2</div>
                <div className="text-[var(--text-secondary)] flex items-center justify-between">
                  <span>初值：x₀ = 1</span>
                  <span>区间：[1, 2]</span>
                </div>
                <div className="pt-1.5 border-t border-dai-500/15 text-dai-800 dark:text-dai-200 font-semibold">
                  收敛精度：|x_k − √2| ≤ 10⁻⁴
                </div>
              </div>

              <div className="mb-4">
                <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] font-semibold block mb-1">
                  函数接口规范
                </span>
                <code className="block p-2 rounded-lg bg-paper-100 dark:bg-paper-800/60 border border-paper-200 dark:border-paper-700 text-xs font-mono text-olive-800 dark:text-olive-200 break-all">
                  {assignment.signature}
                </code>
              </div>

              <div>
                <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] font-semibold block mb-2">
                  静态规则要求
                </span>
                <div className="space-y-1.5 text-xs">
                  {assignment.checks.map((c) => (
                    <div key={c} className="flex items-start gap-2 p-2 rounded-lg border border-paper-200 dark:border-paper-800 bg-[var(--bg-tertiary)] text-[var(--text-secondary)]">
                      <CheckCircle2 className="w-3.5 h-3.5 text-olive-600 shrink-0 mt-0.5" />
                      <span className="leading-relaxed">{c}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-5 p-3 rounded-lg bg-ochre-500/10 border border-ochre-500/20 text-xs leading-relaxed text-ochre-800 dark:text-ochre-200">
                隔离沙箱安全规范：学生代码不会在服务器直接执行。静态检查规则与手动轨迹不能等同于动态运行正确。
              </div>

              {/* 提交版本历史 */}
              <div className="mt-6 border-t border-paper-200 dark:border-paper-800 pt-5">
                <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
                  <Clock className="w-3.5 h-3.5" />
                  <span>提交与修订版本树</span>
                </div>
                {history.length === 0 ? (
                  <p className="text-xs text-[var(--text-secondary)]">还没有保存的代码版本。</p>
                ) : (
                  <ul className="space-y-2">
                    {[...history].reverse().map((s) => (
                      <li key={s.id}>
                        <button
                          type="button"
                          disabled={busy}
                          className="w-full rounded-xl border border-paper-200 dark:border-paper-800 p-3 text-left hover:bg-olive-500/5 hover:border-olive-500/30 transition-all text-xs"
                          onClick={() => restore(s)}
                        >
                          <div className="flex items-center justify-between gap-1 mb-1">
                            <span className="font-semibold text-[var(--text-primary)]">
                              {s.previous_id ? "修订版本" : "首次提交版本"}
                            </span>
                            <span className="font-mono text-[10px] text-[var(--text-muted)]">
                              {s.id.slice(0, 8)}
                            </span>
                          </div>
                          <time className="text-[11px] text-[var(--text-muted)] font-mono">
                            {new Date(s.created_at).toLocaleString("zh-CN")}
                          </time>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </AtelierFolioCard>
          </aside>

          {/* 右栏：水墨 IDE 代码编辑器与静态审阅 (8.5 cols) */}
          <section className="lg:col-span-8 space-y-6">
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                setBusy(true);
                setError("");
                try {
                  const values = trace.trim() ? parseTrace(trace) : [];
                  if (values.some((v) => typeof v !== "number")) {
                    throw new Error("作业轨迹暂只接受有限数值；请在数值实验台核对发散或非有限观察。");
                  }
                  const body = {
                    assignment_id: assignment.id,
                    code,
                    iterates: values,
                    stop_reason: stop,
                    previous_id: result?.id ?? null,
                  };
                  const request_id = stableRequestId(localStorage, `${draftKey}:request`, body, () => crypto.randomUUID());
                  const saved = await learningRequest<CodeSubmission>("/code-workshop/submissions", { ...body, request_id });
                  restore(saved);
                  setHistory((prev) => [...prev.filter((s) => s.id !== saved.id), saved]);
                } catch (e) {
                  setError(e instanceof Error ? e.message : "审阅失败，代码仍保留");
                } finally {
                  setBusy(false);
                }
              }}
              className="space-y-6"
            >
              {/* 水墨 IDE 编辑器 */}
              <div className="rounded-2xl border border-paper-300 dark:border-paper-700 bg-[var(--bg-card)] shadow-soft overflow-hidden">
                {/* 模拟编辑器窗口顶栏 */}
                <div className="flex items-center justify-between px-4 py-2.5 bg-paper-100 dark:bg-paper-800/80 border-b border-paper-200 dark:border-paper-700">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-cinnabar-400/80" />
                      <span className="w-2.5 h-2.5 rounded-full bg-ochre-400/80" />
                      <span className="w-2.5 h-2.5 rounded-full bg-olive-500/80" />
                    </div>
                    <span className="ml-3 font-mono text-xs font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
                      <FileCode className="w-3.5 h-3.5 text-olive-600" />
                      newton_method.py
                      {isDirty && (
                        <span className="w-2 h-2 rounded-full bg-ochre-500 animate-pulse inline-block" title="代码已修改尚未保存" />
                      )}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {assignment && (
                      <button
                        type="button"
                        onClick={() => {
                          setCode(assignment.template);
                          localStorage.setItem(`${draftKey}:code`, assignment.template);
                        }}
                        className="text-[11px] px-2 py-0.5 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-paper-200 dark:hover:bg-paper-700 transition-all font-mono"
                      >
                        重置为初始模板
                      </button>
                    )}
                    <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-paper-200 dark:bg-paper-700 text-[var(--text-muted)] font-medium">
                      Python 3 · UTF-8
                    </span>
                  </div>
                </div>

                {/* 编辑器主体：行号槽 + 代码文本域 */}
                <div className="flex bg-[var(--bg-input)] font-mono text-xs sm:text-sm">
                  {/* 行号槽 Gutter */}
                  <div className="select-none py-3 px-3 text-right text-[var(--text-muted)] border-r border-paper-200 dark:border-paper-800 bg-paper-50/50 dark:bg-paper-900/30 text-xs font-mono leading-6 opacity-60">
                    {Array.from({ length: lineCount }).map((_, i) => (
                      <div key={i}>{i + 1}</div>
                    ))}
                  </div>

                  {/* 代码输入框 */}
                  <textarea
                    id="student-code"
                    required
                    spellCheck={false}
                    maxLength={8000}
                    rows={14}
                    onKeyDown={handleKeyDown}
                    className="w-full bg-transparent p-3 leading-6 font-mono text-xs sm:text-sm text-[var(--text-primary)] focus:outline-none resize-none"
                    value={code}
                    onChange={(e) => {
                      setCode(e.target.value);
                      localStorage.setItem(`${draftKey}:code`, e.target.value);
                    }}
                  />
                </div>

                {/* 编辑器底栏 */}
                <div className="px-4 py-2 bg-paper-100/70 dark:bg-paper-800/40 border-t border-paper-200 dark:border-paper-700/60 flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono">
                  <span>按 Tab 键可直接缩进 4 格。函数必须符合规范接口。</span>
                  <div className="flex items-center gap-3">
                    <span>行数: {lineCount}</span>
                    <span>字符: {code.length}</span>
                    <span>Spaces: 4</span>
                  </div>
                </div>
              </div>

              {/* 手动计算轨迹输入 */}
              <AtelierFolioCard title="可选：手动提交本地推演轨迹" badge="数值校验" badgeVariant="dai">
                <p className="text-xs text-[var(--text-secondary)] mb-3 leading-relaxed">
                  填写你在本地执行代码算出的实数序列（包含初值 1.0），用逗号或换行分隔。静态审阅系统将对这段轨迹的收敛性做独立诊断。
                </p>

                {/* 快捷填入典型序列 */}
                <div className="flex flex-wrap gap-1.5 items-center mb-2.5">
                  <span className="text-[var(--text-muted)] text-[11px]">快捷填入试算：</span>
                  <button
                    type="button"
                    onClick={() => {
                      const demo = "1.0, 1.5, 1.416667, 1.414216, 1.414214";
                      setTrace(demo);
                      localStorage.setItem(`${draftKey}:trace`, demo);
                    }}
                    className="px-2 py-0.5 rounded-md bg-paper-200/80 dark:bg-paper-800 text-[11px] text-olive-800 dark:text-olive-200 hover:bg-olive-500/10 hover:border-olive-500/30 border border-transparent transition-all font-mono"
                  >
                    标准牛顿二次收敛列 (x₀=1.0)
                  </button>
                </div>

                <textarea
                  id="code-trace"
                  rows={3}
                  className={`${learningInput} font-mono text-xs`}
                  value={trace}
                  placeholder="例如：1.0, 1.5, 1.416667, 1.414216 ..."
                  onChange={(e) => {
                    setTrace(e.target.value);
                    localStorage.setItem(`${draftKey}:trace`, e.target.value);
                  }}
                />

                {/* 动态收敛阶微雷达可视化 */}
                <NumericalTraceVisualizer values={parsedTraceValues} />

                <div className="mt-4">
                  <label htmlFor="code-stop" className="block text-xs font-semibold mb-1.5 text-[var(--text-secondary)]">
                    该轨迹在本地的停机依据
                  </label>
                  <select
                    id="code-stop"
                    className={learningInput}
                    value={stop}
                    onChange={(e) => {
                      setStop(e.target.value);
                      localStorage.setItem(`${draftKey}:stop`, e.target.value);
                    }}
                  >
                    <option value="none">尚未停止 / 未提交数值轨迹</option>
                    <option value="residual">残差达到目标阈值 |f(x_k)| ≤ 10⁻⁴</option>
                    <option value="step">{"相邻迭代差达到阈值 |x_k − x_{k-1}| ≤ 10⁻⁴"}</option>
                    <option value="exact">零残差精确命中</option>
                    <option value="iteration_limit">达到循环最大步数上限</option>
                  </select>
                </div>
              </AtelierFolioCard>

              {/* 提交按钮 */}
              <div className="pt-2">
                <button type="submit" disabled={busy || !code.trim()} className={learningButton}>
                  <Sparkles className="w-4 h-4 mr-1.5" />
                  {busy ? "代码保存与静态审阅中…" : result ? "保存修订并进行版本比较" : "保存代码并开始静态审阅"}
                </button>
              </div>
            </form>

            {/* 审阅反馈与双版本对比 */}
            {result && (
              <AtelierFolioCard
                title="已保存版本的静态审阅报告"
                badge="静态规则"
                badgeVariant="ochre"
              >
                <p className="text-xs text-[var(--text-secondary)] mb-4">
                  代码保留于服务器版本库（未执行）。下方列出语法与命名规范分析结果：
                </p>
                <SavedCodeReview key={result.id} submission={result} edited={code !== result.code} />

                {result.trace_diagnosis && (
                  <div className="mt-6 border-t border-paper-200 dark:border-paper-800 pt-5">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingDown className="w-4 h-4 text-olive-600" />
                      <h4 className="font-semibold text-xs sm:text-sm text-[var(--text-primary)]">
                        手动轨迹诊断 · {diagnosticLabel(result.trace_diagnosis.status)}
                      </h4>
                    </div>
                    <p className="text-xs sm:text-sm text-[var(--text-secondary)] leading-relaxed">
                      {result.trace_diagnosis.summary}
                    </p>
                    <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                      此诊断仅评估提交数值本身的收敛性，不计为独立推演成功。
                    </p>
                  </div>
                )}

                {result.comparison && (
                  <div className="mt-6 border-t border-paper-200 dark:border-paper-800 pt-5 space-y-2 text-xs sm:text-sm">
                    <div className="flex items-center gap-2 font-semibold text-[var(--text-primary)]">
                      <Layers className="w-4 h-4 text-dai-600" />
                      <span>与上一提交版本对比分析</span>
                    </div>
                    <p className="text-[var(--text-secondary)]">
                      代码逻辑{result.comparison.code_changed ? "已有实质修改" : "内容保持相同"}；静态规则待修项：
                      <strong className="font-mono mx-1">
                        {result.comparison.previous_findings} → {result.comparison.current_findings} 项
                      </strong>
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)]">
                      轨迹收敛判定：{diagnosticLabel(result.comparison.previous_trace_status)} → {diagnosticLabel(result.comparison.current_trace_status)}。
                    </p>
                  </div>
                )}
              </AtelierFolioCard>
            )}
          </section>
        </div>
      )}
    </LearningShell>
  );
}
