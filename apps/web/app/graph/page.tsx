"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Network,
  BookOpen,
  Search,
  Sparkles,
  ChevronDown,
  X,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Code,
  Tag,
  Calculator,
  Eye,
  ShieldAlert,
  ListOrdered
} from "lucide-react";
import { KnowledgeGraph } from "@/components/knowledge-graph";
import { matchCourseCase, listCourseCases } from "@/lib/api";
import { MathView, MathMarkdown } from "@/components/math-view";
import { Node } from "@xyflow/react";

const PRESET_QUERIES = [
  "为什么牛顿法初值选不好会发散？",
  "重根情况下牛顿法的收敛速度是多少？",
  "残差很小是不是就说明算对了？",
  "二分法需要满足什么条件？"
];

export default function GraphPage() {
  const [courseId] = useState("numerical_analysis");
  const [scopeFilter, setScopeFilter] = useState<string | undefined>(undefined);
  const [selectedNode, setSelectedNode] = useState<Node<any> | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [matchedCaseResult, setMatchedCaseResult] = useState<any>(null);
  const [matchError, setMatchError] = useState<string | null>(null);
  const requestId = useRef(0);
  const [matching, setMatching] = useState(false);
  const [simOpen, setSimOpen] = useState(false);
  const [highlightNodeIds, setHighlightNodeIds] = useState<string[]>([]);
  const [courseCases, setCourseCases] = useState<Array<{ case_id: string; title: string; task_type: string; accepted_variants: string[] }>>([]);

  // Course cases live in the backend course pack (single source of truth).
  useEffect(() => {
    listCourseCases(courseId)
      .then(setCourseCases)
      .catch(() => setCourseCases([]));
  }, [courseId]);

  const handleRunMatch = (queryText: string) => {
    if (!queryText.trim()) return;
    setSimOpen(true);
    setSelectedNode(null);
    const current = ++requestId.current;
    setMatching(true);
    setMatchedCaseResult(null);
    setHighlightNodeIds([]);
    setSearchQuery(queryText);
    setMatchError(null);
    matchCourseCase(courseId, queryText, {})
      .then((res) => {
        if (current !== requestId.current) return;
        setMatchedCaseResult(res);
        setHighlightNodeIds(res.concept_anchor_ids || []);
      })
      .catch(() => {
        if (current !== requestId.current) return;
        setMatchedCaseResult(null);
        setHighlightNodeIds([]);
        setMatchError("案例匹配失败：请确认后端 API 已启动。");
      })
      .finally(() => { if (current === requestId.current) setMatching(false); });
  };

  const handleClearMatch = () => {
    ++requestId.current;
    setMatching(false);
    setMatchError(null);
    setSearchQuery("");
    setMatchedCaseResult(null);
    setHighlightNodeIds([]);
  };

  return (
    <div className="flex flex-col h-screen bg-[var(--bg-primary)] overflow-hidden">
      {/* Top Navigation */}
      <header className="flex-shrink-0 min-h-16 py-3 px-4 sm:px-6 flex flex-wrap gap-3 items-center justify-between border-b border-[var(--border-subtle)] bg-[var(--bg-primary)] relative z-30">
        <div className="flex items-center gap-3 sm:gap-4">
          <Link
            href="/chat"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>返回对话</span>
          </Link>
          <div className="h-4 w-px bg-[var(--border-subtle)]" />
          <div className="flex items-center gap-2 text-olive-700 dark:text-olive-300">
            <Network className="w-4.5 h-4.5 text-olive-600 dark:text-olive-400" />
            <h1 className="text-sm font-medium">课程关系图</h1>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          {/* Course select badge */}
          <div className="hidden md:flex items-center gap-1.5 bg-[var(--bg-tertiary)]/70 px-3 py-1.5 rounded-full text-xs font-semibold text-[var(--text-secondary)] border border-[var(--border-subtle)]">
            <BookOpen className="w-3.5 h-3.5 text-olive-600 dark:text-olive-400" />
            <span>《数值分析》求根单元</span>
          </div>

          {/* Scope Filters */}
          <div className="flex items-center gap-1 bg-[var(--bg-tertiary)]/80 p-1 rounded-full border border-[var(--border-subtle)] shadow-xs">
            {[
              { label: "全部", value: undefined, active: "bg-white dark:bg-[#22231f] text-olive-700 dark:text-olive-300 shadow-xs" },
              { label: "核心", value: "core", active: "bg-olive-600 text-[#faf7f2] shadow-xs" },
              { label: "前置", value: "prerequisite", active: "bg-ochre-600 text-[#faf7f2] shadow-xs" },
              { label: "拓展", value: "extension", active: "bg-dai-600 text-[#faf7f2] shadow-xs" },
            ].map((btn) => (
              <button
                key={btn.label}
                aria-pressed={scopeFilter === btn.value}
                onClick={() => { setScopeFilter(btn.value); setSelectedNode(null); }}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                  scopeFilter === btn.value
                    ? btn.active
                    : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Graph Area */}
      <div className="flex-1 relative flex overflow-hidden">
        {/* React Flow Graph */}
        <main className="flex-1 min-w-0 min-h-0 relative flex flex-col lg:flex-row bg-[var(--bg-primary)]">
          <div className="flex-1 min-w-0 min-h-0 relative">
          <KnowledgeGraph
            courseId={courseId}
            scopeFilter={scopeFilter}
            onSelectNode={(node) => setSelectedNode(node)}
            highlightNodeIds={highlightNodeIds}
            selectedNodeId={selectedNode?.id}
            className="w-full h-full border-0 rounded-none bg-transparent"
          />

          </div>

          {/* Teaching Case simulator: docked and collapsible so the canvas keeps the stage */}
          <div className="order-first shrink-0 w-full lg:w-64 max-h-[38vh] lg:max-h-none overflow-y-auto bg-[var(--bg-secondary)] border-b lg:border-b-0 lg:border-r border-[var(--border-subtle)]">
            <div className="flex items-center justify-between px-4 py-2.5">
              <button
                aria-expanded={simOpen}
                onClick={() => setSimOpen(!simOpen)}
                className="flex items-center gap-1.5 text-xs font-bold text-olive-600 dark:text-olive-400"
              >
                <Sparkles className="w-4 h-4 text-olive-500" />
                <span>问题定位</span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${simOpen ? "" : "-rotate-90"}`} />
              </button>
              {matchedCaseResult && (
                <button
                  onClick={handleClearMatch}
                  className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  清除高亮
                </button>
              )}
            </div>

            <div className="hidden lg:block px-4 pb-5 text-xs text-[var(--text-muted)] space-y-3">
              <p>每个圆点是一项课程知识。点选节点查看内容，悬停聚焦相邻关系。</p>
              <div className="flex gap-4"><span className="flex items-center gap-1.5"><i className="w-2 h-2 rounded-full bg-[var(--text-muted)]" />核心</span><span className="flex items-center gap-1.5"><i className="w-2 h-2 rounded-full bg-dai-500" />前置</span><span className="flex items-center gap-1.5"><i className="w-2 h-2 rounded-full bg-ochre-500" />拓展</span></div>
            </div>
            {simOpen && (
            <div className="px-4 pb-4">
            <div className="relative mb-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleRunMatch(searchQuery)}
                placeholder="输入问题，定位相关知识…"
                className="w-full pl-8 pr-16 py-1.5 text-xs bg-[var(--bg-tertiary)] rounded-lg border border-transparent focus:border-olive-500 focus:outline-none"
              />
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-[var(--text-muted)]" />
              <button
                disabled={matching || !searchQuery.trim()}
                onClick={() => handleRunMatch(searchQuery)}
                className="absolute right-1 top-1 px-2 py-0.5 bg-olive-600 text-[#faf7f2] rounded text-[11px] font-medium hover:bg-olive-700"
              >
                {matching ? "匹配中" : "匹配"}
              </button>
            </div>

            {/* Presets */}
            <div className="flex flex-wrap gap-1 mb-2">
              {PRESET_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => handleRunMatch(q)}
                  className="text-[10px] bg-[var(--bg-tertiary)] hover:bg-olive-50 dark:hover:bg-indigo-950/50 hover:text-olive-600 dark:hover:text-olive-400 text-[var(--text-secondary)] px-2 py-0.5 rounded transition-colors text-left"
                >
                  {q}
                </button>
              ))}
            </div>

            {/* Matched Case Card */}
            {matchError && (
              <div className="mt-2 pt-2 border-t border-cinnabar-100 dark:border-red-900/40 text-[11px] text-cinnabar-600 dark:text-cinnabar-400">
                {matchError}
              </div>
            )}
            {matchedCaseResult && (
              <div className="mt-2 pt-2 border-t border-[var(--border-subtle)] text-xs space-y-2" role="status">
                <div className="font-semibold text-[var(--text-primary)]">
                  {matchedCaseResult.matched_case?.title || (matchedCaseResult.decision === "UNCERTAIN" ? "需要补充题目信息" : "当前案例库未覆盖此问题")}
                </div>
                <p className="text-[11px] text-[var(--text-muted)]">
                  {matchedCaseResult.matched_case ? "仅为主题匹配，尚未验算解题过程。" : matchedCaseResult.reason === "out_of_course" ? "该问题超出当前求根单元的课程范围。" : "补充算法、题目条件和解题步骤后，可重新匹配。"}
                </p>
                {matchedCaseResult.clarification_question && (
                  <p className="p-2 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] leading-relaxed">{matchedCaseResult.clarification_question}</p>
                )}
                {matchedCaseResult.matched_case?.diagnostic_probes?.length > 0 && (
                  <div className="p-2.5 rounded-lg border border-[var(--border-subtle)] text-[11px]">
                    <span className="font-semibold mb-1 flex items-center gap-1"><HelpCircle className="w-3.5 h-3.5 text-olive-500" />思考问题</span>
                    <MathMarkdown content={matchedCaseResult.matched_case.diagnostic_probes[0].question} className="text-[11px] text-[var(--text-secondary)]" />
                  </div>
                )}
              </div>
            )}
            </div>
            )}
          </div>
        </main>

        {/* Right Slide-Over Node Detail Drawer */}
        {selectedNode && (
          <aside className="absolute inset-y-0 right-0 w-[min(100%,384px)] lg:relative lg:w-80 flex-shrink-0 border-l border-[var(--border-subtle)] bg-white dark:bg-slate-900 shadow-2xl p-6 flex flex-col justify-between overflow-y-auto z-20 transition-all">
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                    selectedNode.data.scope === "core" ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300" :
                    selectedNode.data.scope === "prerequisite" ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300" :
                    selectedNode.data.scope === "extension" ? "bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300" :
                    "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                  }`}>
                    {selectedNode.data.scope === "core" ? "核心必修" :
                     selectedNode.data.scope === "prerequisite" ? "微积分前置" :
                     selectedNode.data.scope === "extension" ? "课程拓展" : "未分类 · 待教师审核"}
                  </span>

                </div>
                <button
                  aria-label="关闭知识点详情"
                  onClick={() => setSelectedNode(null)}
                  className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-[var(--text-muted)] hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Title */}
              <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-1">
                  {selectedNode.data.label}
                </h2>
                {/* Meta tags */}
                <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-[var(--text-muted)] pb-2 border-b border-slate-100 dark:border-slate-800">
                  <span>类型: <strong className="text-slate-700 dark:text-slate-200">{({ concept: "概念", algorithm: "算法", theorem: "定理", definition: "定义", counterexample: "反例", misconception: "易错点" } as Record<string, string>)[String(selectedNode.data.unit_type)] || "知识点"}</strong></span>
                  <span>难度: <strong className="text-amber-500 dark:text-amber-400">★{selectedNode.data.difficulty || 2}</strong></span>
                  <span>掌握度: <strong className="text-emerald-600 dark:text-emerald-400">{selectedNode.data.mastery != null ? `${Math.round(selectedNode.data.mastery * 100)}%` : "未评估"}</strong></span>
                </div>
              </div>

              {/* KaTeX Mathematical Environment - Prominent Display */}
              {selectedNode.data.latex && (
                <div className="bg-gradient-to-br from-indigo-50/80 via-white to-indigo-50/40 dark:from-indigo-950/60 dark:via-slate-800/80 dark:to-indigo-950/40 p-3.5 rounded-xl border border-indigo-100 dark:border-indigo-800/80 shadow-sm">
                  <span className="text-[10px] font-mono text-olive-600 dark:text-olive-400 uppercase tracking-wider font-semibold block mb-1 flex items-center gap-1">
                    <Calculator className="w-3.5 h-3.5" /> 数学表达式
                  </span>
                  <div className="py-1 text-center overflow-x-auto">
                    <MathView math={selectedNode.data.latex} display={true} className="text-sm font-serif text-indigo-950 dark:text-indigo-100" />
                  </div>
                </div>
              )}

              {/* Formal Mathematical Statement / Theorem */}
              {selectedNode.data.formal_statement && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-olive-500 dark:text-indigo-400" />
                    形式化数学定理与定义表述
                  </h3>
                  <div className="bg-slate-50 dark:bg-slate-800/90 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    <MathMarkdown content={selectedNode.data.formal_statement} />
                  </div>
                </div>
              )}

              {/* Geometric & Intuitive Meaning */}
              {selectedNode.data.geometric_meaning && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5 flex items-center gap-1.5">
                    <Eye className="w-3.5 h-3.5 text-teal-500 dark:text-teal-400" />
                    几何直观与图象释义
                  </h3>
                  <div className="bg-teal-50/60 dark:bg-teal-950/40 p-3.5 rounded-xl border border-teal-100 dark:border-teal-800/60 shadow-sm">
                    <MathMarkdown content={selectedNode.data.geometric_meaning} />
                  </div>
                </div>
              )}

              {/* Conditions & Failure Modes */}
              {selectedNode.data.conditions_and_failure && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5 flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
                    前提条件与病态 / 失效模式
                  </h3>
                  <div className="bg-amber-50/60 dark:bg-amber-950/40 p-3.5 rounded-xl border border-amber-100 dark:border-amber-800/60 shadow-sm">
                    <MathMarkdown content={selectedNode.data.conditions_and_failure} />
                  </div>
                </div>
              )}

              {/* Algorithm Steps (if present) */}
              {selectedNode.data.algorithm_steps && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5 flex items-center gap-1.5">
                    <ListOrdered className="w-3.5 h-3.5 text-blue-500 dark:text-blue-400" />
                    计算与递推算法步骤
                  </h3>
                  <div className="bg-blue-50/50 dark:bg-blue-950/40 p-3.5 rounded-xl border border-blue-100 dark:border-blue-800/60 shadow-sm">
                    <MathMarkdown content={selectedNode.data.algorithm_steps} />
                  </div>
                </div>
              )}

              {/* Fallback Content */}
              {selectedNode.data.content && !selectedNode.data.formal_statement && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5">
                    知识点释义与教学要点
                  </h3>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed bg-slate-50 dark:bg-slate-800/90 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    {selectedNode.data.content}
                  </p>
                </div>
              )}

              {/* Related Teaching Cases */}
              {selectedNode.data.cases && selectedNode.data.cases.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-2 flex items-center gap-1.5">
                    <Tag className="w-3.5 h-3.5 text-olive-500 dark:text-indigo-400" />
                    相关教学案例
                  </h3>
                  <div className="space-y-1.5">
                    {selectedNode.data.cases.map((cId: string) => {
                      const caseItem = courseCases.find((c) => c.case_id === cId);
                      return (
                        <div
                          key={cId}
                          onClick={() => handleRunMatch(caseItem?.accepted_variants[0] || cId)}
                          className="text-xs p-2.5 bg-slate-50 dark:bg-slate-800/80 hover:bg-olive-50 dark:hover:bg-indigo-950/50 rounded-lg cursor-pointer transition-colors border border-slate-200/80 dark:border-slate-700/80"
                        >
                          <div className="font-semibold text-slate-800 dark:text-slate-200 mb-0.5">
                            {caseItem ? caseItem.title : cId}
                          </div>
                          <div className="text-[11px] text-[var(--text-muted)]">
                            {({ concept_explanation: "概念理解", convergence_analysis: "收敛分析", derivation: "公式推导", error_debugging: "错误排查", code_task: "代码实践" } as Record<string, string>)[caseItem?.task_type || ""] || "教学问题"} · 查看相关问题
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Action */}
            <div className="pt-4 mt-6 border-t border-[var(--border-subtle)]">
              <Link
                href={`/chat`}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-indigo-600 hover:bg-olive-700 text-white rounded-xl text-xs font-semibold shadow transition-colors"
              >
                返回对话继续学习
              </Link>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
