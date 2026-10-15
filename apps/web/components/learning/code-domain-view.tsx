"use client";

import React, { useEffect, useState, useMemo, useCallback, useId, useRef } from "react";
import {
  AtelierFolioCard,
  Notice,
  learningInput,
  learningButton,
  NumericalTraceVisualizer
} from "@/components/learning/learning-shell";
import {
  learningRequest,
  parseTrace,
  stableRequestId,
  type CodeAssignment,
  type CodeSubmission
} from "@/lib/learning-api";
import { codeContextRef, type CodeContextRef } from "@/lib/learning-context";
import { getCurrentUserId } from "@/lib/demo-auth";
import { Sparkles, FileCode, Layers, MessageSquareShare, Check } from "lucide-react";

const diagnosticLabels: Record<string, string> = {
  supported: "证据支持",
  contradicted: "发现偏差",
  inconclusive: "尚不能确认",
  tool_error: "诊断失败",
};
const diagnosticLabel = (status: string | null | undefined) => diagnosticLabels[status ?? ""] ?? "未提交";

export interface CodeDomainViewProps {
  mode?: "full" | "canvas";
  initialSubmissionId?: string | null;
  onDiscussFinding?: (ref: CodeContextRef, prompt: string) => void;
}

export function CodeDomainView({
  mode = "full",
  initialSubmissionId = null,
  onDiscussFinding,
}: CodeDomainViewProps) {
  const isCanvas = mode === "canvas";
  const [assignment, setAssignment] = useState<CodeAssignment | null>(null);
  const [code, setCode] = useState("");
  const [trace, setTrace] = useState("");
  const [stop, setStop] = useState("none");
  const [result, setResult] = useState<CodeSubmission | null>(null);
  const [history, setHistory] = useState<CodeSubmission[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [focusedLine, setFocusedLine] = useState<number | null>(null);
  const [diffOpen, setDiffOpen] = useState(false);
  const [previousSubmission, setPreviousSubmission] = useState<CodeSubmission | null>(null);
  const editorId = useId();
  const loadedId = useRef<string | null>(null);

  const draftKey = `code-workshop:${getCurrentUserId()}:${result?.id ?? "new"}`;

  const restore = useCallback((s: CodeSubmission) => {
    loadedId.current = s.id;
    const key = `code-workshop:${getCurrentUserId()}:${s.id}`;
    setResult(s);
    setCode(localStorage.getItem(`${key}:code`) ?? s.code);
    setTrace(localStorage.getItem(`${key}:trace`) ?? s.iterates.join(", "));
    setStop(localStorage.getItem(`${key}:stop`) ?? s.stop_reason);
    if (!isCanvas) {
      window.history.replaceState(null, "", `/code-workshop?id=${encodeURIComponent(s.id)}`);
    }
  }, [isCanvas]);

  useEffect(() => {
    const controller = new AbortController();
    const signal = controller.signal;
    Promise.all([
      learningRequest<CodeAssignment>("/code-workshop/assignment", undefined, signal),
      learningRequest<{ submissions: CodeSubmission[] }>("/code-workshop/submissions", undefined, signal),
    ])
      .then(async ([a, b]) => {
        if (signal.aborted) return;
        setHistory(b.submissions);
        setCode(localStorage.getItem(`code-workshop:${getCurrentUserId()}:new:code`) ?? a.template);
        setTrace(localStorage.getItem(`code-workshop:${getCurrentUserId()}:new:trace`) ?? "");
        setStop(localStorage.getItem(`code-workshop:${getCurrentUserId()}:new:stop`) ?? "none");

        const targetId = initialSubmissionId || (!isCanvas ? new URLSearchParams(window.location.search).get("id") : null);
        if (targetId) {
          const loaded = await learningRequest<CodeSubmission>(`/code-workshop/submissions/${encodeURIComponent(targetId)}`, undefined, signal);
          if (!signal.aborted) restore(loaded);
        }
        if (!signal.aborted) setAssignment(a);
      })
      .catch((e) => { if (!signal.aborted) setError(e.message); })
      .finally(() => { if (!signal.aborted) setLoading(false); });
    return () => controller.abort();
    // Initialize once. External selections below do not replace a mounted draft.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (busy || !assignment || !initialSubmissionId || loadedId.current === initialSubmissionId) return;
    const controller = new AbortController();
    learningRequest<CodeSubmission>(`/code-workshop/submissions/${encodeURIComponent(initialSubmissionId)}`, undefined, controller.signal)
      .then((saved) => { if (!controller.signal.aborted) restore(saved); })
      .catch((e) => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [initialSubmissionId, assignment, restore, busy]);

  // 加载上一版供并排 Diff
  useEffect(() => {
    if (!result?.previous_id) {
      setPreviousSubmission(null);
      return;
    }
    const controller = new AbortController();
    learningRequest<CodeSubmission>(`/code-workshop/submissions/${encodeURIComponent(result.previous_id)}`, undefined, controller.signal)
      .then((saved) => { if (!controller.signal.aborted) setPreviousSubmission(saved); })
      .catch(() => { if (!controller.signal.aborted) setPreviousSubmission(null); });
    return () => controller.abort();
  }, [result?.previous_id]);

  // 代码行数
  const lineCount = useMemo(() => {
    return Math.max(code.split("\n").length, isCanvas ? 8 : 12);
  }, [code, isCanvas]);

  // 代码是否有未保存修改
  const isDirty = result ? code !== result.code || trace !== result.iterates.join(", ") || stop !== result.stop_reason
    : Boolean(assignment && (code !== assignment.template || trace.trim() || stop !== "none"));

  // 动态分析本地轨迹序列
  const parsedTraceValues = useMemo(() => {
    if (!trace.trim()) return [];
    try {
      return parseTrace(trace).filter((v): v is number => typeof v === "number");
    } catch {
      return [];
    }
  }, [trace]);

  // Keep Tab / Shift+Tab available for keyboard navigation.
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "]" && e.ctrlKey && !e.shiftKey) {
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

  const locateLine = (line: number) => {
    setFocusedLine(line);
    requestAnimationFrame(() => document.getElementById(`${editorId}-saved-line-${line}`)?.scrollIntoView({ block: "center", behavior: "smooth" }));
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-xs text-[var(--text-muted)] flex items-center justify-center gap-2">
        <span className="size-2 rounded-full bg-olive-500 animate-ping" />
        <span>正在恢复算法工坊作业与版本树…</span>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="p-6 text-center text-xs text-cinnabar-700 bg-cinnabar-500/5 rounded-xl border border-cinnabar-500/20">
        作业暂不可用，请核对权限或重新加载。
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${isCanvas ? "px-1 py-1" : ""}`}>
      <Notice error={error} />

      {/* 1. 目标与规范概要条 */}
      <div className="rounded-xl p-3.5 bg-paper-100/70 dark:bg-paper-900/40 border border-paper-200/80 dark:border-paper-800/80 atelier-hairline text-xs font-mono">
        <div className="flex items-center justify-between text-[var(--text-primary)] font-semibold">
          <span>{assignment.title}</span>
          <span className="text-[11px] px-2 py-0.5 rounded bg-olive-500/15 text-olive-800 dark:text-olive-200 font-mono">
            Newton 法代码审阅
          </span>
        </div>
        <div className="mt-2 text-[var(--text-secondary)] flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px]">
          <span>目标：f(x) = x² − 2</span>
          <span>初值：x₀ = 1.0</span>
          <span>精度：|x_k − √2| ≤ 10⁻⁴</span>
        </div>
      </div>

      {/* 2. 水墨 IDE 代码编辑区 */}
      <div className="rounded-2xl border border-paper-300/80 dark:border-paper-700/80 bg-[var(--bg-card)] shadow-soft overflow-hidden atelier-hairline">
        {/* IDE 窗口顶栏 */}
        <div className="flex items-center justify-between px-3.5 py-2 bg-paper-100/90 dark:bg-paper-800/80 border-b border-paper-200 dark:border-paper-700 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-cinnabar-400" />
            <span className="size-2 rounded-full bg-ochre-400" />
            <span className="size-2 rounded-full bg-olive-500" />
            <span className="ml-2 font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
              <FileCode className="size-3.5 text-olive-600" />
              newton_method.py
              {isDirty && (
                <span className="size-1.5 rounded-full bg-ochre-500 animate-pulse" title="代码已修改" />
              )}
            </span>
          </div>
          <div className="flex items-center gap-2 text-[11px]">
            <button
              type="button"
              onClick={() => {
                setCode(assignment.template);
                localStorage.setItem(`${draftKey}:code`, assignment.template);
              }}
              className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
            >
              重置模板
            </button>
            <span className="px-1.5 py-0.5 rounded bg-paper-200/80 dark:bg-paper-700 text-[var(--text-muted)]">
              Python 3
            </span>
          </div>
        </div>

        {/* 编辑器核心：行号槽 + 文本域 */}
        <div className="flex bg-[var(--bg-input)] font-mono text-xs leading-6">
          <div className="select-none py-3 px-2.5 text-right text-[var(--text-muted)] border-r border-paper-200 dark:border-paper-800/60 bg-paper-50/40 dark:bg-paper-900/20 text-[11px] opacity-60">
            {Array.from({ length: lineCount }).map((_, i) => {
              const lineNum = i + 1;
              const isHighlight = focusedLine === lineNum;
              return (
                <div
                  key={lineNum}
                  id={`${editorId}-line-${lineNum}`}
                  className={`${isHighlight ? "font-bold text-olive-700 dark:text-olive-300 bg-olive-500/20 px-1 rounded" : ""}`}
                >
                  {lineNum}
                </div>
              );
            })}
          </div>
          <textarea
            id={editorId}
            aria-label="作业代码"
            rows={isCanvas ? 10 : 13}
            spellCheck={false}
            maxLength={8000}
            onKeyDown={handleKeyDown}
            value={code}
            onChange={(e) => {
              setCode(e.target.value);
              localStorage.setItem(`${draftKey}:code`, e.target.value);
            }}
            className="w-full bg-transparent p-3 leading-6 font-mono text-xs text-[var(--text-primary)] focus:outline-none resize-none"
          />
        </div>

        {/* 底栏状态 */}
        <div className="px-3 py-1.5 bg-paper-100/60 dark:bg-paper-800/40 border-t border-paper-200 dark:border-paper-700/60 flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono">
          <span>Ctrl+] 缩进 4 格 · 仅静态检查，不执行代码</span>
          <span>{code.length} 字符</span>
        </div>
      </div>

      {/* 3. 提交与审阅动作条 */}
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
        className="space-y-4"
      >
        <label className="block text-xs space-y-2">
          <span>手动迭代轨迹（可选；不是程序运行输出）</span>
          <textarea className={learningInput} rows={2} value={trace} onChange={(e) => {
            setTrace(e.target.value); localStorage.setItem(`${draftKey}:trace`, e.target.value);
          }} placeholder="例如：1, 1.5, 1.4166667" />
        </label>
        {parsedTraceValues.length > 0 && <NumericalTraceVisualizer values={parsedTraceValues} />}
        <label className="block text-xs space-y-2">
          <span>手动记录的停止原因</span>
          <select className={learningInput} value={stop} onChange={(e) => {
            setStop(e.target.value); localStorage.setItem(`${draftKey}:stop`, e.target.value);
          }}>
            <option value="none">未声明</option><option value="residual">残差阈值</option>
            <option value="step">步长阈值</option><option value="exact">精确零点</option>
            <option value="iteration_limit">达到迭代上限</option>
          </select>
        </label>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={busy || !code.trim()}
              className={`${learningButton} text-xs py-2 px-3.5`}
            >
              <Sparkles className="size-3.5 mr-1" />
              {busy ? "正在审阅…" : result ? "保存修订并静态审阅" : "保存代码并静态审阅"}
            </button>
          </div>
          {history.length > 0 && (
            <div className="text-xs text-[var(--text-muted)] font-mono">
              已保存 {history.length} 个版本
            </div>
          )}
        </div>
      </form>

      {history.length > 0 && <label className="block text-xs space-y-2">
        <span>打开已保存版本（当前草稿保留在本机）</span>
        <select aria-label="已保存代码版本" className={learningInput} value={result?.id ?? ""} disabled={busy}
          onChange={(e) => { const saved = history.find((s) => s.id === e.target.value); if (saved) restore(saved); }}>
          <option value="" disabled>选择提交版本</option>
          {[...history].reverse().map((saved) => <option key={saved.id} value={saved.id}>{saved.id.slice(0, 8)} · {saved.previous_id ? "修订" : "首次提交"}</option>)}
        </select>
      </label>}

      {/* 4. 静态审阅报告与行级探讨通道 */}
      {result && (
        <div className="space-y-4">
          <AtelierFolioCard
            title={`静态审阅报告 · ${result.previous_id ? "修订版" : "首次提交版"}`}
            badge={result.static_rule_version ?? "v1"}
            badgeVariant="olive"
          >
            {isDirty && (
              <p role="status" className="mb-3 text-xs leading-5 text-ochre-700 dark:text-ochre-300">
                编辑器中已有未保存修改；下方报告对应已保存的提交版本（{result.id.slice(0, 8)}）。
              </p>
            )}

            <div className="space-y-2.5 text-xs">
              {result.trace_diagnosis && <p>手动轨迹诊断：{diagnosticLabel(result.trace_diagnosis.status)} · {result.trace_diagnosis.summary}</p>}
              {result.findings.length === 0 ? (
                <div className="p-3 rounded-xl bg-olive-500/10 border border-olive-500/20 text-olive-800 dark:text-olive-200 flex items-center gap-2">
                  <Check className="size-4 text-olive-600" />
                  <span>未触发当前有限规则警示；尚不能确认算法正确。</span>
                </div>
              ) : (
                result.findings.map((f, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-paper-50 dark:bg-paper-900/40 border border-paper-200 dark:border-paper-800 space-y-1.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                            f.evidence_scope === "structural_fact"
                              ? "bg-dai-500/15 text-dai-800 dark:text-dai-200"
                              : "bg-ochre-500/15 text-ochre-800 dark:text-ochre-200"
                          }`}
                        >
                          {f.evidence_scope === "structural_fact" ? "代码结构事实" : "算法线索"}
                        </span>
                        {f.line && (
                          <button
                            type="button"
                            onClick={() => locateLine(f.line!)}
                            className="font-mono text-olive-700 dark:text-olive-300 underline hover:opacity-80 text-[11px]"
                          >
                            定位已保存代码第 {f.line} 行
                          </button>
                        )}
                      </div>

                      {/* 与助教探讨此行代码 */}
                      {onDiscussFinding && (
                        <button
                          type="button"
                          onClick={() => {
                            const ref = codeContextRef(result, i);
                            const prompt = f.line
                              ? `请针对代码第 ${f.line} 行的静态规则提示：“${f.message}”，分析我的实现思路。`
                              : `请分析我的算法实现提示：“${f.message}”。`;
                            onDiscussFinding(ref, prompt);
                          }}
                          className="inline-flex items-center gap-1 text-[11px] text-olive-700 dark:text-olive-300 hover:underline"
                        >
                          <MessageSquareShare className="size-3" />
                          <span>与助教讨论此项 →</span>
                        </button>
                      )}
                    </div>
                    <p className="text-[var(--text-secondary)] leading-relaxed">{f.message}</p>
                  </div>
                ))
              )}
            </div>

            <details className="mt-4 text-xs" open={focusedLine !== null}>
              <summary className="cursor-pointer py-2">查看已保存代码与行号</summary>
              <div className="max-h-80 overflow-auto rounded-lg bg-paper-100 dark:bg-paper-900 p-2 font-mono">
                {result.code.split("\n").map((text, i) => <div key={i} id={`${editorId}-saved-line-${i+1}`}
                  className={`flex gap-3 leading-6 ${focusedLine === i+1 ? "bg-olive-500/20" : ""}`}>
                  <span aria-hidden="true">{i+1}</span><code className="whitespace-pre">{text || " "}</code>
                </div>)}
              </div>
            </details>

            {/* 双版本并排对比 Diff 折叠 */}
            {previousSubmission && (
              <div className="mt-4 pt-3 border-t border-paper-200 dark:border-paper-800">
                <button
                  type="button"
                  onClick={() => setDiffOpen(!diffOpen)}
                  className="inline-flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                >
                  <Layers className="size-3.5" />
                  <span>{diffOpen ? "收起与上一版的代码对比" : "展开与上一版本代码并排对比"}</span>
                </button>
                {diffOpen && (
                  <div className="mt-3 grid gap-3 lg:grid-cols-2 text-xs font-mono">
                    <div className="p-2.5 rounded-lg bg-paper-100/60 dark:bg-paper-800/40 border border-paper-200 dark:border-paper-700">
                      <div className="font-semibold text-[var(--text-muted)] mb-1">
                        上一版本（{previousSubmission.id.slice(0, 8)}）
                      </div>
                      <pre className="max-h-60 overflow-auto whitespace-pre-wrap leading-5">
                        {previousSubmission.code}
                      </pre>
                    </div>
                    <div className="p-2.5 rounded-lg bg-olive-500/5 border border-olive-500/20">
                      <div className="font-semibold text-olive-700 dark:text-olive-300 mb-1">
                        当前已保存（{result.id.slice(0, 8)}）
                      </div>
                      <pre className="max-h-60 overflow-auto whitespace-pre-wrap leading-5 text-[var(--text-primary)]">
                        {result.code}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}
          </AtelierFolioCard>
        </div>
      )}
    </div>
  );
}
