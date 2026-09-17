"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Network,
  BookOpen,
  Search,
  Sparkles,
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
import { matchLocalCase, TeachingCaseSummary, teachingCasesList } from "@/lib/numerical-analysis-graph";
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
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [matchedCaseResult, setMatchedCaseResult] = useState<any>(null);
  const [highlightNodeIds, setHighlightNodeIds] = useState<string[]>([]);

  const handleRunMatch = (queryText: string) => {
    setSearchQuery(queryText);
    const res = matchLocalCase(queryText);
    setMatchedCaseResult(res);
    if (res.concept_anchors && res.concept_anchors.length > 0) {
      setHighlightNodeIds(res.concept_anchors);
    } else {
      setHighlightNodeIds([]);
    }
  };

  const handleClearMatch = () => {
    setSearchQuery("");
    setMatchedCaseResult(null);
    setHighlightNodeIds([]);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden">
      {/* Top Navigation */}
      <header className="flex-shrink-0 h-16 px-6 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md relative z-20">
        <div className="flex items-center gap-4">
          <Link 
            href="/chat"
            className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            返回对话
          </Link>
          <div className="h-4 w-px bg-slate-200 dark:bg-slate-800" />
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
            <Network className="w-5 h-5" />
            <h1 className="text-lg font-bold font-title tracking-wider">课程知识图谱 2.0 (Course Graph)</h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Course select badge */}
          <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300">
            <BookOpen className="w-3.5 h-3.5 text-indigo-500" />
            <span>《数值分析》求根单元 (27 节点 / 21 关系)</span>
          </div>

          {/* Scope Filters */}
          <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
            {[
              { label: "全部", value: undefined },
              { label: "核心 (Core)", value: "core" },
              { label: "前置 (Prereq)", value: "prerequisite" },
              { label: "拓展 (Extension)", value: "extension" },
            ].map((btn) => (
              <button
                key={btn.label}
                onClick={() => setScopeFilter(btn.value)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  scopeFilter === btn.value
                    ? "bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
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
        <main className="flex-1 relative bg-white dark:bg-black">
          <KnowledgeGraph 
            courseId={courseId}
            scopeFilter={scopeFilter}
            onSelectNode={(node) => setSelectedNode(node)}
            highlightNodeIds={highlightNodeIds}
            selectedNodeId={selectedNode?.id}
            className="w-full h-full border-0 rounded-none bg-transparent" 
          />

          {/* Floating Teaching Case Simulator Overlay (Top-Left) */}
          <div className="absolute top-4 left-4 z-10 w-96 max-w-[calc(100vw-2rem)] bg-white/95 dark:bg-slate-900/95 backdrop-blur-md rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl p-4 transition-all">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-600 dark:text-indigo-400">
                <Sparkles className="w-4 h-4 text-indigo-500" />
                <span>Teaching Case 问法仿真器</span>
              </div>
              {matchedCaseResult && (
                <button
                  onClick={handleClearMatch}
                  className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  清除高亮
                </button>
              )}
            </div>

            <div className="relative mb-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleRunMatch(searchQuery)}
                placeholder="输入学生问句测试案例匹配与图谱锚点..."
                className="w-full pl-8 pr-16 py-1.5 text-xs bg-slate-100 dark:bg-slate-800 rounded-lg border border-transparent focus:border-indigo-500 focus:outline-none"
              />
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-slate-400" />
              <button
                onClick={() => handleRunMatch(searchQuery)}
                className="absolute right-1 top-1 px-2 py-0.5 bg-indigo-600 text-white rounded text-[11px] font-medium hover:bg-indigo-700"
              >
                匹配
              </button>
            </div>

            {/* Presets */}
            <div className="flex flex-wrap gap-1 mb-2">
              {PRESET_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => handleRunMatch(q)}
                  className="text-[10px] bg-slate-100 dark:bg-slate-800 hover:bg-indigo-50 dark:hover:bg-indigo-950/50 hover:text-indigo-600 dark:hover:text-indigo-400 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded transition-colors text-left"
                >
                  {q}
                </button>
              ))}
            </div>

            {/* Matched Case Card */}
            {matchedCaseResult && matchedCaseResult.case_info && (
              <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-slate-800 dark:text-slate-100">
                    {matchedCaseResult.case_info.title}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 rounded font-mono font-medium">
                    {matchedCaseResult.decision} ({Math.round(matchedCaseResult.confidence * 100)}%)
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-1.5">
                  {matchedCaseResult.case_info.learning_objectives[0]}
                </p>

                {matchedCaseResult.case_info.diagnostic_probes.length > 0 && (
                  <div className="bg-indigo-50/80 dark:bg-indigo-950/40 p-2.5 rounded-lg border border-indigo-100 dark:border-indigo-900 text-[11px] text-indigo-900 dark:text-indigo-200">
                    <span className="font-semibold block mb-1 flex items-center gap-1">
                      <HelpCircle className="w-3.5 h-3.5 text-indigo-500" />
                      教学诊断探针：
                    </span>
                    <MathMarkdown content={matchedCaseResult.case_info.diagnostic_probes[0].question} className="text-[11px] text-indigo-900 dark:text-indigo-200 mb-1" />
                    <div className="mt-1 pt-1 border-t border-indigo-100/60 dark:border-indigo-800/40 text-[10px]">
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400 mr-1">诊断基准：</span>
                      <MathMarkdown content={matchedCaseResult.case_info.diagnostic_probes[0].correct_answer} className="text-[10px] text-slate-600 dark:text-slate-300 inline" />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>

        {/* Right Slide-Over Node Detail Drawer */}
        {selectedNode && (
          <aside className="w-96 md:w-[450px] flex-shrink-0 border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6 flex flex-col justify-between overflow-y-auto z-20 transition-all">
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                    selectedNode.data.scope === "core" ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300" :
                    selectedNode.data.scope === "prerequisite" ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300" :
                    "bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300"
                  }`}>
                    {selectedNode.data.scope === "core" ? "核心必修" : selectedNode.data.scope === "prerequisite" ? "微积分前置" : "课程拓展"}
                  </span>
                  <span className="text-[10px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-500 font-mono">
                    ID: {selectedNode.id}
                  </span>
                </div>
                <button 
                  onClick={() => setSelectedNode(null)}
                  className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600"
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
                <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-100 dark:border-slate-800">
                  <span>类型: <strong className="text-slate-700 dark:text-slate-200">{selectedNode.data.unit_type}</strong></span>
                  <span>难度: <strong className="text-amber-500 dark:text-amber-400">★{selectedNode.data.difficulty || 2}</strong></span>
                  <span>掌握度: <strong className="text-emerald-600 dark:text-emerald-400">{Math.round((selectedNode.data.mastery || 0.5) * 100)}%</strong></span>
                </div>
              </div>

              {/* KaTeX Mathematical Environment - Prominent Display */}
              {selectedNode.data.latex && (
                <div className="bg-gradient-to-br from-indigo-50/80 via-white to-indigo-50/40 dark:from-indigo-950/60 dark:via-slate-800/80 dark:to-indigo-950/40 p-3.5 rounded-xl border border-indigo-100 dark:border-indigo-800/80 shadow-sm">
                  <span className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400 uppercase tracking-wider font-semibold block mb-1 flex items-center gap-1">
                    <Calculator className="w-3.5 h-3.5" /> 数学表达式 / 递推公理 (KaTeX)
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
                    <BookOpen className="w-3.5 h-3.5 text-indigo-500 dark:text-indigo-400" />
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
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/90 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    {selectedNode.data.content}
                  </p>
                </div>
              )}

              {/* Related Teaching Cases */}
              {selectedNode.data.cases && selectedNode.data.cases.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-2 flex items-center gap-1.5">
                    <Tag className="w-3.5 h-3.5 text-indigo-500 dark:text-indigo-400" />
                    关联 Teaching Cases 教学案例
                  </h3>
                  <div className="space-y-1.5">
                    {selectedNode.data.cases.map((cId: string) => {
                      const caseItem = teachingCasesList.find((c) => c.case_id === cId);
                      return (
                        <div 
                          key={cId}
                          onClick={() => handleRunMatch(caseItem?.accepted_variants[0] || cId)}
                          className="text-xs p-2.5 bg-slate-50 dark:bg-slate-800/80 hover:bg-indigo-50 dark:hover:bg-indigo-950/50 rounded-lg cursor-pointer transition-colors border border-slate-200/80 dark:border-slate-700/80"
                        >
                          <div className="font-semibold text-slate-800 dark:text-slate-200 mb-0.5">
                            {caseItem ? caseItem.title : cId}
                          </div>
                          <div className="text-[11px] text-slate-400">
                            {caseItem?.task_type} · 点击测试问法仿真
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Action */}
            <div className="pt-4 mt-6 border-t border-slate-200 dark:border-slate-800">
              <Link
                href={`/chat`}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow transition-colors"
              >
                在对话中以此知识点提问
              </Link>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
