"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LatexRenderer } from "@/components/latex-renderer";
import { Textarea } from "@/components/ui/textarea";
import { MathView, MathMarkdown } from "@/components/math-view";
import { getAuthHeaders, isAuthStorageKey } from "@/lib/demo-auth";
import {
  generateCandidatesFromDocument,
  listUploadedDocuments,
  type DocumentEntry,
} from "@/lib/api";
import {
  CheckCircle2,
  XCircle,
  GitMerge,
  Plus,
  Search,
  Sparkles,
  BookOpen,
  Layers,
  Clock,
  RefreshCw,
  ArrowRight,
  User,
  ChevronRight,
  Network
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

// ==========================================
// Types for Course Graph Candidates (2.0)
// ==========================================
export type CandidateType =
  | "new_unit"
  | "new_relation"
  | "merge_units"
  | "new_case"
  | "new_alias"
  | "scope_change";

export type CandidateStatus = "pending" | "approved" | "merged" | "rejected" | "deferred";

export interface GraphCandidate {
  candidate_id: string;
  candidate_type: CandidateType;
  course_id: string;
  payload: {
    id?: string;
    title?: string;
    type?: string;
    content?: string;
    latex?: string;
    keywords?: string[];
    difficulty?: number;
    scope_level?: "core" | "prerequisite" | "extension" | "external" | "unclassified";
    teaching_role?: string;
    target_id?: string;
    alias?: string;
    note?: string;
    case_id?: string;
    course_id?: string;
    task_type?: string;
    learning_objectives?: string[];
    concept_ids?: string[];
    required_condition_ids?: string[];
    reasoning_signature?: string[];
    accepted_variants?: string[];
    disclosure_policy?: string;
    source_unit_id?: string;
    target_unit_id?: string;
    relation_type?: string;
    source_title?: string;
    target_title?: string;
    confidence?: number;
    chapter_path?: string[];
    context_header?: string;
    source_document_id?: string;
  };
  evidence_refs: string[];
  proposed_by: "system" | "teacher" | "student_query_cluster";
  support_count: number;
  status: CandidateStatus;
  reviewer_id?: string | null;
  review_note?: string;
  first_seen?: string;
  last_seen?: string;
}

// Relation types the document pipeline and the review vocabulary produce.
// Without a label a reviewer sees only "拓扑关系" and cannot tell what edge
// they are about to approve.
const RELATION_LABELS: Record<string, string> = {
  supports_proof: "支撑证明",
  example_of: "例题佐证",
  derives_from: "推论来源",
  part_of: "从属小节",
  prerequisite: "前置知识",
  prerequisite_of: "被前置",
  applies_to: "应用于",
  exercise_of: "配套习题",
  common_mistake_of: "常见错误",
  misconception_of: "误区所属",
  counterexample_of: "反例",
  similar_to: "相似",
  contrast_with: "对比",
  special_case_of: "特例",
  algorithm_of: "算法实现",
  code_task_of: "代码任务",
  has_error_bound: "误差界",
  converges_if: "收敛条件",
  requires: "依赖",
  implemented_by: "实现方式",
  uses_stopping_rule: "停止准则",
  remediated_by: "补救方式",
};

const relationLabel = (relationType?: string): string =>
  (relationType && RELATION_LABELS[relationType]) || relationType || "未指定关系";

// Candidate state comes only from persisted server responses.
function GraphCandidatesView({ courseId = "numerical_analysis" }: { courseId?: string }) {
  const [canonicalUnits,setCanonicalUnits]=useState<{id:string;title:string}[]>([]);
  const [candidates, setCandidates] = useState<GraphCandidate[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("pending");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [reviewNote, setReviewNote] = useState("");
  const [actionFeedback, setActionFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Merge modal state
  const [isMergeModalOpen, setIsMergeModalOpen] = useState(false);
  const [mergeTargetId, setMergeTargetId] = useState("NA_NEWTON");

  // Document → candidates generation state
  const [documents, setDocuments] = useState<DocumentEntry[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [generatingFromDoc, setGeneratingFromDoc] = useState(false);

  // Propose candidate modal state
  const [isProposeModalOpen, setIsProposeModalOpen] = useState(false);
  const [proposeForm, setProposeForm] = useState({
    candidate_id: "",
    candidate_type: "new_unit" as CandidateType,
    title: "",
    latex: "",
    content: "",
    scope_level: "core",
    teaching_role: "core",
    difficulty: 3,
    evidence_ref: ""
  });

  const fetchCandidates = useCallback(async () => {
    try {
      setLoading(true);
      const url = `${API_BASE}/api/courses/${courseId}/candidates${
        statusFilter !== "all" ? `?status=${statusFilter}` : ""
      }`;
      const res = await fetch(url, { headers: getAuthHeaders() });
      if(!res.ok)throw Error(`候选读取失败（HTTP ${res.status}），未使用演示条目替代。`);
      const data=await res.json();
      if(!Array.isArray(data.candidates))throw Error("候选回执格式不可确认。");
      setCandidates(data.candidates);
      setSelectedId(current=>data.candidates.some((c:GraphCandidate)=>c.candidate_id===current)?current:data.candidates[0]?.candidate_id??null);
    } catch(error) {
      setCandidates([]);setSelectedId(null);
      setActionFeedback({type:"error",text:`候选读取失败：${error instanceof Error?error.message:"请重试。"}`});
    } finally {
      setLoading(false);
    }
  }, [courseId, statusFilter]);

  useEffect(() => {
    fetchCandidates();
    fetch(`${API_BASE}/api/courses/${courseId}/graph?format=raw`,{headers:getAuthHeaders()}).then(async response=>{if(!response.ok)throw Error("课程节点不可读取，无法选择合并目标。");const data=await response.json();setCanonicalUnits(data.units||[]);}).catch(()=>setCanonicalUnits([]));
    listUploadedDocuments()
      .then((docs) => {
        setDocuments(docs);
        if (docs.length > 0) setSelectedDocumentId((current) => current || docs[0].id);
      })
      .catch(() => setDocuments([]));
  }, [courseId, statusFilter, fetchCandidates]);

  const handleGenerateFromDocument = async () => {
    if (!selectedDocumentId) return;
    setGeneratingFromDoc(true);
    setActionFeedback(null);
    try {
      const result = await generateCandidatesFromDocument(courseId, selectedDocumentId);
      setActionFeedback({
        type: "success",
        text: `已从教材生成 ${result.total} 条候选，等待审核。`,
      });
      setStatusFilter("pending");
      await fetchCandidates();
    } catch (err) {
      setActionFeedback({
        type: "error",
        text: err instanceof Error ? err.message : "候选生成失败",
      });
    } finally {
      setGeneratingFromDoc(false);
    }
  };

  const selectedCandidate = candidates.find((c) => c.candidate_id === selectedId) || null;

  const handleReviewAction = async (action: "approve" | "merge" | "reject" | "defer", targetId?: string) => {
    if (!selectedCandidate) return;
    setActionLoading(true);
    setActionFeedback(null);

    const payload = {
      action,
      reviewer_id: "teacher_admin",
      review_note: reviewNote || (action === "approve" ? "教师审核通过入图" : action === "merge" ? `合并至已有概念 ${targetId}` : "审核未通过驳回"),
      merge_target_id: targetId || mergeTargetId
    };

    try {
      const res = await fetch(`${API_BASE}/api/courses/${courseId}/candidates/${selectedCandidate.candidate_id}/review`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if(!res.ok)throw Error(`审核未确认（HTTP ${res.status}），候选状态未修改。`);
      const receipt=await res.json();
      if(!receipt||receipt.status!=="success"||receipt.candidate?.candidate_id!==selectedCandidate.candidate_id||!receipt.revision_id)throw Error("审核回执不完整，尚未确认结果，请刷新核对。");
      await fetchCandidates();
      setActionFeedback({type:"success",text:"服务端已保存审核回执；以刷新后的课程版本和候选状态为准。"});
      setIsMergeModalOpen(false);
      setReviewNote("");
    } catch (err: any) {
      setActionFeedback({type:"error",text:err instanceof Error?err.message:"审核失败，未记录成功。"});
    } finally {
      setActionLoading(false);
    }
  };

  const handleProposeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!proposeForm.candidate_id || !proposeForm.title) {
      alert("请填写候选ID和标题");
      return;
    }

    const newCandidate: GraphCandidate = {
      candidate_id: proposeForm.candidate_id.startsWith("CAND_") ? proposeForm.candidate_id : `CAND_${proposeForm.candidate_id.toUpperCase()}`,
      candidate_type: proposeForm.candidate_type,
      course_id: courseId,
      payload: {
        id: proposeForm.candidate_id.startsWith("NA_") ? proposeForm.candidate_id : `NA_${proposeForm.candidate_id.toUpperCase()}`,
        title: proposeForm.title,
        latex: proposeForm.latex,
        content: proposeForm.content,
        scope_level: proposeForm.scope_level as any,
        teaching_role: proposeForm.teaching_role,
        difficulty: proposeForm.difficulty
      },
      evidence_refs: [proposeForm.evidence_ref || "teacher_manual_proposal"],
      proposed_by: "teacher",
      support_count: 1,
      status: "pending",
      first_seen: new Date().toISOString(),
      last_seen: new Date().toISOString()
    };

    try {
      const response=await fetch(`${API_BASE}/api/courses/${courseId}/candidates`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: newCandidate.candidate_id,
          candidate_type: newCandidate.candidate_type,
          payload: newCandidate.payload,
          proposed_by: "teacher",
          evidence_ref: proposeForm.evidence_ref
        })
      });
      if(!response.ok)throw Error(`候选未保存（HTTP ${response.status}）。`);
      const receipt=await response.json();
      if(!receipt.candidate?.candidate_id)throw Error("未取得已保存候选回执。");
      await fetchCandidates();
      setSelectedId(receipt.candidate.candidate_id);
      setIsProposeModalOpen(false);
    } catch(error) {
      setActionFeedback({type:"error",text:error instanceof Error?error.message:"候选提交失败。"});
      return;
    }
    setProposeForm({
      candidate_id: "",
      candidate_type: "new_unit",
      title: "",
      latex: "",
      content: "",
      scope_level: "core",
      teaching_role: "core",
      difficulty: 3,
      evidence_ref: ""
    });
  };

  // Filter candidates
  const filteredCandidates = candidates.filter((c) => {
    if (statusFilter !== "all" && c.status !== statusFilter) return false;
    if (typeFilter !== "all" && c.candidate_type !== typeFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const title = c.payload?.title || c.candidate_id;
      const content = c.payload?.content || "";
      return title.toLowerCase().includes(q) || content.toLowerCase().includes(q) || c.candidate_id.toLowerCase().includes(q);
    }
    return true;
  });

  const getStatusBadge = (status: CandidateStatus) => {
    switch (status) {
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300/40">
            <Clock className="w-3 h-3" /> 待审核
          </span>
        );
      case "approved":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300/40">
            <CheckCircle2 className="w-3 h-3" /> 已批准入图
          </span>
        );
      case "merged":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-300/40">
            <GitMerge className="w-3 h-3" /> 已合并概念
          </span>
        );
      case "rejected":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-300/40">
            <XCircle className="w-3 h-3" /> 已驳回
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            {status}
          </span>
        );
    }
  };

  const getTypeBadge = (type: CandidateType, relationType?: string) => {
    switch (type) {
      case "new_unit":
        return <span className="text-[11px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-950/70 dark:text-blue-300 font-mono">新增知识元</span>;
      case "new_case":
        return <span className="text-[11px] px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 dark:bg-purple-950/70 dark:text-purple-300 font-mono">教学案例</span>;
      case "new_alias":
        return <span className="text-[11px] px-1.5 py-0.5 rounded bg-teal-100 text-teal-700 dark:bg-teal-950/70 dark:text-teal-300 font-mono">别名归一</span>;
      case "new_relation":
        return (
          <span className="text-[11px] px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 dark:bg-orange-950/70 dark:text-orange-300 font-mono">
            拓扑关系 · {relationLabel(relationType)}
          </span>
        );
      default:
        return <span className="text-[11px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 font-mono">{type}</span>;
    }
  };

  // A relation candidate has no content of its own; what a reviewer must see is
  // which two units it connects and in which direction.
  const renderRelationEdge = (candidate: GraphCandidate, detailed: boolean) => {
    const payload = candidate.payload;
    const source = payload?.source_title || payload?.source_unit_id || "?";
    const target = payload?.target_title || payload?.target_unit_id || "?";
    return (
      <div className={`text-xs leading-relaxed mb-2 ${detailed ? "" : "line-clamp-2"}`}>
        <span className="text-slate-700 dark:text-slate-300 font-medium">{source}</span>
        <span className="mx-1.5 text-orange-600 dark:text-orange-400 font-mono">
          —{relationLabel(payload?.relation_type)}→
        </span>
        <span className="text-slate-700 dark:text-slate-300 font-medium">{target}</span>
        {detailed && typeof payload?.confidence === "number" && (
          <span className="ml-2 text-[11px] text-slate-400 dark:text-slate-500 font-mono">
            置信度 {payload.confidence.toFixed(2)}
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Left List Pane */}
      <div className="w-96 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col shrink-0">
        {/* Search & Filters */}
        <div className="p-3 border-b border-slate-200 dark:border-slate-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-medium">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>演化候选池 ({filteredCandidates.length})</span>
            </div>
            <Button
              variant="primary"
              size="sm"
              className="h-7 text-xs px-2.5 gap-1 shadow-sm"
              onClick={() => setIsProposeModalOpen(true)}
            >
              <Plus className="w-3.5 h-3.5" /> 提议新候选
            </Button>
          </div>

            {/* Notification Banner */}
            {actionFeedback && (
              <div
                role={actionFeedback.type === "error" ? "alert" : "status"}
                className={`p-3 text-xs flex items-center justify-between border-b ${
                  actionFeedback.type === "success"
                    ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800/40 text-emerald-800 dark:text-emerald-300"
                    : "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800/40 text-rose-800 dark:text-rose-300"
                }`}
              >
                <span>{actionFeedback.text}</span>
                <button
                  onClick={() => setActionFeedback(null)}
                  className="text-xs opacity-60 hover:opacity-100"
                >
                  关闭
                </button>
              </div>
            )}

          {/* Textbook → candidates pipeline */}
          {documents.length > 0 && (
            <div className="flex items-center gap-1.5">
              <select
                value={selectedDocumentId}
                onChange={(e) => setSelectedDocumentId(e.target.value)}
                className="flex-1 min-w-0 border border-slate-200 dark:border-slate-700 rounded-md text-xs bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.filename}
                  </option>
                ))}
              </select>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs px-2.5 gap-1 shrink-0"
                disabled={generatingFromDoc || !selectedDocumentId}
                onClick={handleGenerateFromDocument}
              >
                {generatingFromDoc ? "生成中…" : "教材提取候选"}
              </Button>
            </div>
          )}

          <div className="relative">
            <Search className="w-4 h-4 absolute left-2.5 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="搜索候选概念、公式或ID..."
              className="w-full pl-8 pr-3 py-1.5 border border-slate-200 dark:border-slate-700 rounded-md text-xs bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Status Tabs */}
          <div className="flex bg-slate-100 dark:bg-slate-800/80 p-0.5 rounded-md text-xs">
            {[
              { id: "pending", label: "待审" },
              { id: "approved", label: "已入图" },
              { id: "merged", label: "已合并" },
              { id: "rejected", label: "已驳回" },
              { id: "all", label: "全部" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`flex-1 py-1 text-center rounded text-[11px] transition-all ${
                  statusFilter === tab.id
                    ? "bg-white dark:bg-slate-700 shadow-sm font-semibold text-slate-900 dark:text-white"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 text-[11px]">
            {[
              { id: "all", label: "全部类型" },
              { id: "new_unit", label: "知识元" },
              { id: "new_case", label: "案例" },
              { id: "new_alias", label: "别名" }
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTypeFilter(t.id)}
                className={`px-2 py-0.5 rounded-full border transition-colors shrink-0 ${
                  typeFilter === t.id
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium"
                    : "border-slate-200 dark:border-slate-800 text-slate-500 hover:border-slate-300 dark:hover:border-slate-700"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Candidate Cards List */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/80">
          {loading ? (
            <div className="p-6 text-center text-xs text-slate-400">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 opacity-50" />
              正在加载候选列表...
            </div>
          ) : filteredCandidates.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400 dark:text-slate-500">
              未找到符合条件的图谱候选条目。
            </div>
          ) : (
            filteredCandidates.map((candidate) => {
              const isSelected = selectedId === candidate.candidate_id;
              const title = candidate.payload?.title || candidate.candidate_id;
              return (
                <div
                  key={candidate.candidate_id}
                  onClick={() => {
                    setSelectedId(candidate.candidate_id);
                    setActionFeedback(null);
                  }}
                  className={`p-3 cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-blue-50/80 dark:bg-blue-950/30 border-l-4 border-l-blue-600 dark:border-l-blue-500"
                      : "hover:bg-slate-50 dark:hover:bg-slate-800/40 border-l-4 border-l-transparent"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    {getTypeBadge(candidate.candidate_type, candidate.payload?.relation_type)}
                    {getStatusBadge(candidate.status)}
                  </div>

                  {candidate.candidate_type === "new_relation" ? (
                    renderRelationEdge(candidate, false)
                  ) : (
                    <>
                      <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 line-clamp-1 mb-1">
                        {title}
                      </h4>

                      {candidate.payload?.context_header && (
                        <div className="text-[11px] text-slate-400 dark:text-slate-500 line-clamp-1 mb-1 font-mono">
                          {candidate.payload.context_header}
                        </div>
                      )}

                      <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed mb-2 font-serif">
                        {candidate.payload?.content || candidate.payload?.note || "无补充描述"}
                      </p>
                    </>
                  )}

                  <div className="flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500">
                    <span className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {candidate.proposed_by === "student_query_cluster"
                        ? "学生提问聚类"
                        : candidate.proposed_by === "teacher"
                        ? "教师教研"
                        : "系统推理"}
                    </span>
                    <span className="font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-[10px]">
                      支持度: {candidate.support_count}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Detail Pane */}
      <div className="flex-1 flex flex-col overflow-hidden bg-slate-50/50 dark:bg-slate-950">
        {selectedCandidate ? (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Action Bar */}
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between shrink-0 shadow-sm">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                    {selectedCandidate.candidate_type === "new_relation"
                      ? relationLabel(selectedCandidate.payload?.relation_type)
                      : selectedCandidate.payload?.title || selectedCandidate.candidate_id}
                  </h2>
                  {getTypeBadge(selectedCandidate.candidate_type, selectedCandidate.payload?.relation_type)}
                  {getStatusBadge(selectedCandidate.status)}
                </div>
                <div className="text-xs text-slate-400 font-mono">
                  ID: {selectedCandidate.candidate_id}
                </div>
              </div>

              {/* Review Decision Buttons */}
              <div className="flex items-center gap-2">
                {selectedCandidate.status === "pending" ? (
                  <>
                    <Button
                      variant="danger"
                      size="sm"
                      className="gap-1 shadow-sm"
                      onClick={() => handleReviewAction("reject")}
                      disabled={actionLoading}
                    >
                      <XCircle className="w-4 h-4" /> 驳回
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1 border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-950/40"
                      onClick={() => setIsMergeModalOpen(true)}
                      disabled={actionLoading}
                    >
                      <GitMerge className="w-4 h-4" /> 合并到已有概念
                    </Button>
                    <Button
                      variant="success"
                      size="sm"
                      className="gap-1 shadow-sm font-semibold"
                      onClick={() => handleReviewAction("approve")}
                      disabled={actionLoading}
                    >
                      <CheckCircle2 className="w-4 h-4" /> 批准入图
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1 text-xs"
                    onClick={() => handleReviewAction("defer")}
                    disabled={actionLoading}
                  >
                    <RefreshCw className="w-3.5 h-3.5" /> 重新审核
                  </Button>
                )}
              </div>
            </div>

            {/* Review Note Input (if pending) */}
            {selectedCandidate.status === "pending" && (
              <div className="px-6 py-3 bg-amber-50/60 dark:bg-amber-950/20 border-b border-amber-200/50 dark:border-amber-900/30 flex items-center gap-3">
                <span className="text-xs font-medium text-amber-800 dark:text-amber-400 shrink-0">
                  审核意见 (可选):
                </span>
                <input
                  type="text"
                  placeholder="填写审核批注，例如：通过审核并纳入第2章核心大纲..."
                  className="flex-1 px-3 py-1.5 text-xs rounded border border-amber-200 dark:border-amber-800/60 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-amber-500"
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                />
              </div>
            )}

            {/* Content Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* 1. Mathematical Formula Preview */}
              {selectedCandidate.payload?.latex && (
                <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-blue-500" />
                      核心数学公式
                    </h3>
                    <span className="text-[10px] font-mono text-slate-400">KaTeX High-Contrast</span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-lg border border-slate-100 dark:border-slate-800/80 overflow-x-auto">
                    <MathView math={selectedCandidate.payload.latex} display={true} />
                  </div>
                  <div className="mt-2 text-[11px] font-mono text-slate-400 bg-slate-50 dark:bg-slate-950 px-2 py-1 rounded select-all truncate">
                    {selectedCandidate.payload.latex}
                  </div>
                </div>
              )}

              {/* 2. Conceptual Explanation */}
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-indigo-500" />
                  {selectedCandidate.candidate_type === "new_relation"
                    ? "关系断言（批准即写入规范图谱）"
                    : "知识内容解析与定义"}
                </h3>
                {selectedCandidate.candidate_type === "new_relation" ? (
                  <div className="space-y-2">
                    {renderRelationEdge(selectedCandidate, true)}
                    <div className="text-[11px] font-mono text-slate-400 dark:text-slate-500 space-y-0.5 select-all">
                      <div>source: {selectedCandidate.payload?.source_unit_id || "—"}</div>
                      <div>target: {selectedCandidate.payload?.target_unit_id || "—"}</div>
                      <div>relation_type: {selectedCandidate.payload?.relation_type || "—"}</div>
                    </div>
                  </div>
                ) : (
                  <>
                    {selectedCandidate.payload?.context_header && (
                      <div className="text-[11px] font-mono text-slate-400 dark:text-slate-500">
                        出处：{selectedCandidate.payload.context_header}
                      </div>
                    )}
                    <div className="prose dark:prose-invert max-w-none text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                      <MathMarkdown content={selectedCandidate.payload?.content || selectedCandidate.payload?.note || "暂无文字定义"} />
                    </div>
                  </>
                )}

                {selectedCandidate.payload?.keywords && selectedCandidate.payload.keywords.length > 0 && (
                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex flex-wrap gap-1.5 items-center">
                    <span className="text-xs text-slate-400">关键词:</span>
                    {selectedCandidate.payload.keywords.map((kw, i) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* 3. Teaching Case Pedagogy (If Teaching Case or Unit) */}
              {(selectedCandidate.payload?.learning_objectives ||
                selectedCandidate.payload?.reasoning_signature ||
                selectedCandidate.payload?.accepted_variants) && (
                <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-purple-500" />
                    教学决策与认知约束 (Course Graph 2.0 Pedagogy)
                  </h3>

                  {selectedCandidate.payload.learning_objectives && (
                    <div>
                      <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                        目标能力达成
                      </h4>
                      <ul className="list-disc list-inside space-y-1 text-xs text-slate-600 dark:text-slate-400">
                        {selectedCandidate.payload.learning_objectives.map((obj, i) => (
                          <li key={i}>
                            <MathMarkdown content={obj} />
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedCandidate.payload.reasoning_signature && (
                    <div>
                      <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                        诊断探针与推理签名
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedCandidate.payload.reasoning_signature.map((sig, i) => (
                          <span
                            key={i}
                            className="text-xs px-2.5 py-1 rounded bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800/40 font-mono"
                          >
                            {sig}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedCandidate.payload.accepted_variants && (
                    <div>
                      <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                        学情高频提问变体
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {selectedCandidate.payload.accepted_variants.map((v, i) => (
                          <div
                            key={i}
                            className="text-xs p-2 rounded bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-300 flex items-center gap-1.5"
                          >
                            <ChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
                            <span>{v}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 4. Evolution Source & Evidence Trace */}
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                  <Network className="w-3.5 h-3.5 text-teal-500" />
                  演化来源与提问佐证 (Evidence & Provenance)
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800">
                    <div className="text-slate-400 mb-1">提议者</div>
                    <div className="font-semibold text-slate-800 dark:text-slate-200">
                      {selectedCandidate.proposed_by}
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800">
                    <div className="text-slate-400 mb-1">支持提问频次</div>
                    <div className="font-semibold text-blue-600 dark:text-blue-400 font-mono text-sm">
                      {selectedCandidate.support_count} 次
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800">
                    <div className="text-slate-400 mb-1">首次捕捉时间</div>
                    <div className="font-mono text-slate-600 dark:text-slate-400 text-[11px] truncate">
                      {selectedCandidate.first_seen ? new Date(selectedCandidate.first_seen).toLocaleDateString() : "近期"}
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800">
                    <div className="text-slate-400 mb-1">审核人</div>
                    <div className="font-semibold text-slate-800 dark:text-slate-200">
                      {selectedCandidate.reviewer_id || "待指派"}
                    </div>
                  </div>
                </div>

                {selectedCandidate.evidence_refs && selectedCandidate.evidence_refs.length > 0 && (
                  <div className="pt-2">
                    <div className="text-xs text-slate-400 mb-1.5">关联证据链</div>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedCandidate.evidence_refs.map((ref, i) => (
                        <span
                          key={i}
                          className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200/60 dark:border-slate-700/60"
                        >
                          {ref}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedCandidate.review_note && (
                  <div className="mt-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/40 text-xs">
                    <span className="font-semibold text-blue-800 dark:text-blue-300 mr-2">审核批注:</span>
                    <span className="text-blue-900 dark:text-blue-200">{selectedCandidate.review_note}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400 dark:text-slate-500">
            <Sparkles className="w-10 h-10 mb-3 opacity-30 text-blue-500" />
            <p className="text-sm">从左侧列表选择一个图谱演化候选以展开详情与审核决策</p>
          </div>
        )}
      </div>

      {/* Merge Modal Dialog */}
      {isMergeModalOpen && selectedCandidate && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <GitMerge className="w-5 h-5 text-indigo-500" />
                合并至已有规范概念
              </h3>
              <button
                onClick={() => setIsMergeModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-500 dark:text-slate-400">
              将当前候选条目 <strong>{selectedCandidate.payload?.title || selectedCandidate.candidate_id}</strong> 作为别名或变体扩展合并到已有图谱节点中，保持规范图谱的精简与高内聚。
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  选择目标概念节点
                </label>
                <select
                  className="w-full px-3 py-2 border rounded-md text-sm bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
                  value={mergeTargetId}
                  onChange={(e) => setMergeTargetId(e.target.value)}
                >
                  <option value="">选择实际课程节点</option>
                  {canonicalUnits.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.id} - {u.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  合并说明与别名补充:
                </label>
                <input
                  type="text"
                  placeholder="例如：添加别名 切线法 到牛顿迭代法"
                  className="w-full px-3 py-2 border rounded-md text-sm bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
              <Button variant="secondary" onClick={() => setIsMergeModalOpen(false)}>
                取消
              </Button>
              <Button
                variant="primary"
                onClick={() => handleReviewAction("merge", mergeTargetId)}
                disabled={actionLoading}
              >
                确认合并
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Propose Candidate Modal */}
      {isProposeModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xl max-w-xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Plus className="w-5 h-5 text-blue-500" />
                提议图谱演化新候选
              </h3>
              <button
                onClick={() => setIsProposeModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleProposeSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    候选类型:
                  </label>
                  <select
                    className="w-full px-3 py-2 border rounded-md text-xs bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
                    value={proposeForm.candidate_type}
                    onChange={(e) =>
                      setProposeForm({ ...proposeForm, candidate_type: e.target.value as CandidateType })
                    }
                  >
                    <option value="new_unit">新增知识元 (new_unit)</option>
                    <option value="new_case">新增教学案例 (new_case)</option>
                    <option value="new_alias">新增概念别名 (new_alias)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    候选唯一 ID
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="如 CAND_ROMBERG"
                    className="w-full px-3 py-2 border rounded-md text-xs bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-mono"
                    value={proposeForm.candidate_id}
                    onChange={(e) => setProposeForm({ ...proposeForm, candidate_id: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  概念 / 案例标题:
                </label>
                <input
                  type="text"
                  required
                  placeholder="例如：龙贝格求积法 (Romberg Integration)"
                  className="w-full px-3 py-2 border rounded-md text-xs bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
                  value={proposeForm.title}
                  onChange={(e) => setProposeForm({ ...proposeForm, title: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  核心数学公式 (LaTeX, 可选):
                </label>
                <input
                  type="text"
                  placeholder="例如：T_m(h) = \frac{4^m T_{m-1}(h/2) - T_{m-1}(h)}{4^m - 1}"
                  className="w-full px-3 py-2 border rounded-md text-xs bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-mono"
                  value={proposeForm.latex}
                  onChange={(e) => setProposeForm({ ...proposeForm, latex: e.target.value })}
                />
                {proposeForm.latex && (
                  <div className="mt-2 p-2 bg-slate-50 dark:bg-slate-950 rounded border border-slate-200 dark:border-slate-800">
                    <div className="text-[10px] text-slate-400 mb-1">实时公式预览:</div>
                    <MathView math={proposeForm.latex} display={true} />
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  内容说明与教学定义:
                </label>
                <Textarea
                  placeholder="详细描述该知识元的几何直观、核心结论或教学案例目标..."
                  className="min-h-[90px] text-xs font-sans"
                  value={proposeForm.content}
                  onChange={(e) => setProposeForm({ ...proposeForm, content: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    大纲范畴
                  </label>
                  <select
                    className="w-full px-3 py-2 border rounded-md text-xs bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
                    value={proposeForm.scope_level}
                    onChange={(e) => setProposeForm({ ...proposeForm, scope_level: e.target.value })}
                  >
                    <option value="core">核心要求 (core)</option>
                    <option value="extension">拓展选学 (extension)</option>
                    <option value="prerequisite">先修依赖 (prerequisite)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    佐证来源参考:
                  </label>
                  <input
                    type="text"
                    placeholder="如：2026春期中考点增补"
                    className="w-full px-3 py-2 border rounded-md text-xs bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
                    value={proposeForm.evidence_ref}
                    onChange={(e) => setProposeForm({ ...proposeForm, evidence_ref: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                <Button variant="secondary" type="button" onClick={() => setIsProposeModalOpen(false)}>
                  取消
                </Button>
                <Button variant="primary" type="submit">
                  提议并加入候选池
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ==========================================
// Legacy Knowledge Units Review View
// ==========================================
type KnowledgeUnit = {
  id: string;
  chapter_path: string;
  title: string;
  content: string;
  latex?: string;
  source_span?: { quote?: string; page_start?: number; page_end?: number };
  status: string;
};

export default function AdminKnowledgePage() {
  const [identity,setIdentity]=useState(0);
  useEffect(()=>{const changed=()=>setIdentity(n=>n+1);const storage=(e:StorageEvent)=>{if(isAuthStorageKey(e.key))changed();};window.addEventListener("luojia-auth-change",changed);window.addEventListener("storage",storage);return()=>{window.removeEventListener("luojia-auth-change",changed);window.removeEventListener("storage",storage);};},[]);
  return <AdminKnowledge key={identity}/>;
}
function AdminKnowledge() {


  return (
    <div className="flex flex-col h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden text-slate-800 dark:text-slate-200">
      {/* Top Header Navigation */}
      <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 flex items-center justify-between shrink-0 shadow-sm">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="font-bold text-base bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              珞珈图谱后台 (Course Graph 2.0 Admin)
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 font-mono">
              数值分析 (numerical_analysis)
            </span>
          </div>

          <span className="text-xs text-[var(--text-secondary)]">官方更新仅通过课程候选审核；旧文件资料为只读兼容来源。</span>
        </div>

        {/* Quick Links */}
        <div className="flex items-center gap-3">
          <Link
            href="/graph"
            className="flex items-center gap-1.5 text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium"
          >
            <Network className="w-3.5 h-3.5" />
            查看全景图谱
          </Link>
          <Link
            href="/"
            className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
          >
            返回导师主页
          </Link>
        </div>
      </header>

      {/* Main Tab Content */}
      <main className="flex-1 flex overflow-hidden">
        <GraphCandidatesView />
      </main>
    </div>
  );
}
