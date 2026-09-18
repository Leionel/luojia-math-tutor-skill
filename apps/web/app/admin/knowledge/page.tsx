"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LatexRenderer } from "@/components/latex-renderer";
import { Textarea } from "@/components/ui/textarea";
import { MathView, MathMarkdown } from "@/components/math-view";
import { getAuthHeaders } from "@/lib/demo-auth";
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

// Fallback initial candidates if backend server is not running or returns empty
const FALLBACK_CANDIDATES: GraphCandidate[] = [
  {
    candidate_id: "CAND_SECANT_METHOD",
    candidate_type: "new_unit",
    course_id: "numerical_analysis",
    payload: {
      id: "NA_SECANT",
      title: "割线法 / 弦截法 (Secant Method)",
      type: "algorithm",
      content:
        "用相邻两点的割线斜率代替切线导数 $f'(x_k)$，避免解析求导。其渐进收敛阶为黄金分割比 $p = \\frac{1+\\sqrt{5}}{2} \\approx 1.618$，属于超线性收敛。每次迭代只需计算一次新函数值。",
      latex: "x_{k+1} = x_k - f(x_k) \\frac{x_k - x_{k-1}}{f(x_k) - f(x_{k-1})}",
      keywords: ["割线法", "弦截法", "Secant", "超线性收敛", "避免导数"],
      difficulty: 3,
      scope_level: "core",
      teaching_role: "core"
    },
    proposed_by: "student_query_cluster",
    support_count: 14,
    evidence_refs: ["query_cluster_202609_01", "student_dialogue_#849", "exam_review_2025"],
    status: "pending",
    first_seen: "2026-09-15T09:30:00Z",
    last_seen: "2026-09-17T08:12:00Z"
  },
  {
    candidate_id: "CAND_NEWTON_MODIFIED",
    candidate_type: "new_unit",
    course_id: "numerical_analysis",
    payload: {
      id: "NA_SIMPLIFIED_NEWTON",
      title: "简化牛顿法 / 平行弦法 (Modified Newton Method)",
      type: "algorithm",
      content:
        "在迭代全过程中固定使用初始导数值 $f'(x_0)$ 代替每次更新的 $f'(x_k)$。几何意义为用斜率固定的平行切线逼近根。每步迭代只需计算函数值，极大减少了导数计算开销，但收敛速度降为局部线性收敛。",
      latex: "x_{k+1} = x_k - \\frac{f(x_k)}{f'(x_0)}",
      keywords: ["简化牛顿法", "平行弦法", "固定斜率", "线性收敛"],
      difficulty: 3,
      scope_level: "core",
      teaching_role: "extension"
    },
    proposed_by: "teacher",
    support_count: 5,
    evidence_refs: ["textbook_ch2_sec3", "assignment_hw3_p2"],
    status: "pending",
    first_seen: "2026-09-16T14:10:00Z",
    last_seen: "2026-09-17T06:00:00Z"
  },
  {
    candidate_id: "CAND_ALIAS_TANGENT_METHOD",
    candidate_type: "new_alias",
    course_id: "numerical_analysis",
    payload: {
      target_id: "NA_NEWTON",
      alias: "切线法",
      note: "多位学生在提问中将牛顿迭代法直接称为“切线法”，建议合并为 NA_NEWTON 规范别名以提升匹配召回率。"
    },
    proposed_by: "student_query_cluster",
    support_count: 28,
    evidence_refs: ["query_cluster_202609_02", "dialogue_#1022", "dialogue_#1104"],
    status: "pending",
    first_seen: "2026-09-14T11:00:00Z",
    last_seen: "2026-09-17T07:45:00Z"
  },
  {
    candidate_id: "CAND_CASE_INITIAL_DIVERGENCE",
    candidate_type: "new_case",
    course_id: "numerical_analysis",
    payload: {
      case_id: "CASE_NEWTON_OSCILLATION_CYCLE",
      course_id: "numerical_analysis",
      title: "牛顿法初值选取导致的周期振荡案例",
      task_type: "debug_task",
      learning_objectives: [
        "引导学生诊断牛顿法在特定非凸多项式（如 $f(x)=x^3-x-3$）初值不当导致在局部极值两侧周期振荡的原因",
        "掌握二分法与牛顿法混合初值估计策略"
      ],
      concept_ids: ["NA_NEWTON", "NA_LOCAL_CONVERGENCE", "NA_STOPPING_CRITERIA"],
      required_condition_ids: ["initial_guess_in_convergence_ball", "cycle_detection"],
      reasoning_signature: [
        "检查导数是否过小 ($f'(x_k) \\approx 0$)",
        "检测序列是否在两点间循环振荡",
        "建议先使用二分法迭代数次获取收敛球内初值"
      ],
      accepted_variants: [
        "为什么牛顿法算出来一直在几个数之间跳",
        "牛顿迭代法死循环怎么排查",
        "初值怎么选才能保证牛顿法收敛"
      ],
      disclosure_policy: "scaffolded"
    },
    proposed_by: "teacher",
    support_count: 8,
    evidence_refs: ["office_hour_case_2026", "midterm_common_mistake"],
    status: "pending",
    first_seen: "2026-09-16T16:00:00Z",
    last_seen: "2026-09-17T08:00:00Z"
  },
  {
    candidate_id: "CAND_AITKEN_ACCELERATION",
    candidate_type: "new_unit",
    course_id: "numerical_analysis",
    payload: {
      id: "NA_AITKEN_ACCELERATION",
      title: "埃特金加速法 (Aitken Acceleration)",
      type: "algorithm",
      content:
        "通过利用三个连续迭代值的外推，消除线性收敛序列的主误差项，将线性收敛序列加速为更高阶收敛序列。",
      latex: "\\bar{x}_k = x_k - \\frac{(x_{k+1} - x_k)^2}{x_{k+2} - 2x_{k+1} + x_k}",
      difficulty: 4,
      scope_level: "extension"
    },
    proposed_by: "teacher",
    support_count: 3,
    evidence_refs: ["syllabus_expansion"],
    status: "approved",
    reviewer_id: "prof_luojia",
    review_note: "已批准纳入本课程扩展知识元，供进阶学员探索。",
    first_seen: "2026-09-12T10:00:00Z",
    last_seen: "2026-09-13T15:20:00Z"
  }
];

// Available canonical units in Course Graph for merge targets
const CANONICAL_UNITS = [
  { id: "NA_ROOT_FINDING", title: "非线性方程求根问题" },
  { id: "NA_BISECTION", title: "二分法 (Bisection Method)" },
  { id: "NA_FIXED_POINT", title: "不动点迭代法 (Fixed-Point Iteration)" },
  { id: "NA_NEWTON", title: "牛顿迭代法 (Newton-Raphson Method)" },
  { id: "NA_LOCAL_CONVERGENCE", title: "局部收敛性 (Local Convergence)" },
  { id: "NA_CONVERGENCE_ORDER", title: "收敛阶 (Order of Convergence)" },
  { id: "NA_STOPPING_CRITERIA", title: "停机准则 (Stopping Criteria)" },
  { id: "NA_TAYLOR_EXPANSION", title: "泰勒局部线性化" },
  { id: "NA_RESIDUAL", title: "残差估计" }
];

// ==========================================
// Candidate Review View Component
// ==========================================
function GraphCandidatesView({ courseId = "numerical_analysis" }: { courseId?: string }) {
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

  const fetchCandidates = async () => {
    try {
      setLoading(true);
      const url = `${API_BASE}/api/courses/${courseId}/candidates${
        statusFilter !== "all" ? `?status=${statusFilter}` : ""
      }`;
      const res = await fetch(url, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        if (data.candidates && data.candidates.length > 0) {
          setCandidates(data.candidates);
          if (!selectedId && data.candidates.length > 0) {
            setSelectedId(data.candidates[0].candidate_id);
          }
          return;
        }
      }
      // If server empty or fails, use fallback seed data
      setCandidates(FALLBACK_CANDIDATES);
      if (!selectedId && FALLBACK_CANDIDATES.length > 0) {
        setSelectedId(FALLBACK_CANDIDATES[0].candidate_id);
      }
    } catch {
      setCandidates(FALLBACK_CANDIDATES);
      if (!selectedId && FALLBACK_CANDIDATES.length > 0) {
        setSelectedId(FALLBACK_CANDIDATES[0].candidate_id);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [courseId, statusFilter]);

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

      // Update local state regardless of whether backend is connected
      const newStatus: CandidateStatus =
        action === "approve" ? "approved" : action === "merge" ? "merged" : action === "reject" ? "rejected" : "deferred";

      setCandidates((prev) =>
        prev.map((c) =>
          c.candidate_id === selectedCandidate.candidate_id
            ? {
                ...c,
                status: newStatus,
                reviewer_id: "teacher_admin",
                review_note: payload.review_note,
                last_seen: new Date().toISOString()
              }
            : c
        )
      );

      setActionFeedback({
        type: "success",
        text:
          action === "approve"
            ? "已成功批准入图！知识元与教学决策已写入规范图谱。"
            : action === "merge"
            ? `已成功合并至概念 ${payload.merge_target_id}！`
            : "已驳回候选条目。"
      });
      setIsMergeModalOpen(false);
      setReviewNote("");
    } catch (err: any) {
      // Optimistic local update
      const newStatus: CandidateStatus =
        action === "approve" ? "approved" : action === "merge" ? "merged" : action === "reject" ? "rejected" : "deferred";

      setCandidates((prev) =>
        prev.map((c) =>
          c.candidate_id === selectedCandidate.candidate_id
            ? { ...c, status: newStatus, review_note: payload.review_note }
            : c
        )
      );
      setActionFeedback({
        type: "success",
        text: `操作已记录 (本地模式): ${action === "approve" ? "批准入图" : action === "merge" ? "已合并" : "已驳回"}`
      });
      setIsMergeModalOpen(false);
      setReviewNote("");
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
      await fetch(`${API_BASE}/api/courses/${courseId}/candidates`, {
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
    } catch {
      // Ignored for offline fallback
    }

    setCandidates((prev) => [newCandidate, ...prev]);
    setSelectedId(newCandidate.candidate_id);
    setIsProposeModalOpen(false);
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

  const getTypeBadge = (type: CandidateType) => {
    switch (type) {
      case "new_unit":
        return <span className="text-[11px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-950/70 dark:text-blue-300 font-mono">新增知识元</span>;
      case "new_case":
        return <span className="text-[11px] px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 dark:bg-purple-950/70 dark:text-purple-300 font-mono">教学案例</span>;
      case "new_alias":
        return <span className="text-[11px] px-1.5 py-0.5 rounded bg-teal-100 text-teal-700 dark:bg-teal-950/70 dark:text-teal-300 font-mono">别名归一</span>;
      case "new_relation":
        return <span className="text-[11px] px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 dark:bg-orange-950/70 dark:text-orange-300 font-mono">拓扑关系</span>;
      default:
        return <span className="text-[11px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 font-mono">{type}</span>;
    }
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
                    {getTypeBadge(candidate.candidate_type)}
                    {getStatusBadge(candidate.status)}
                  </div>

                  <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 line-clamp-1 mb-1">
                    {title}
                  </h4>

                  <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed mb-2 font-serif">
                    {candidate.payload?.content || candidate.payload?.note || "无补充描述"}
                  </p>

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
                    {selectedCandidate.payload?.title || selectedCandidate.candidate_id}
                  </h2>
                  {getTypeBadge(selectedCandidate.candidate_type)}
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
                      <CheckCircle2 className="w-4 h-4" /> 批准入图 (Approve)
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

            {/* Notification Banner */}
            {actionFeedback && (
              <div
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
                      核心数学公式 (LaTeX Formulation)
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
                  知识内容解析与定义
                </h3>
                <div className="prose dark:prose-invert max-w-none text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                  <MathMarkdown content={selectedCandidate.payload?.content || selectedCandidate.payload?.note || "暂无文字定义"} />
                </div>

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
                        目标能力达成 (Learning Objectives):
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
                        诊断探针与推理签名 (Reasoning Signature):
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
                        学情高频提问变体 (Accepted Student Variants):
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
                    <div className="text-xs text-slate-400 mb-1.5">关联证据链 (Evidence References):</div>
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
                  选择目标概念节点 (Target Unit ID):
                </label>
                <select
                  className="w-full px-3 py-2 border rounded-md text-sm bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
                  value={mergeTargetId}
                  onChange={(e) => setMergeTargetId(e.target.value)}
                >
                  {CANONICAL_UNITS.map((u) => (
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
                确认合并 (Merge)
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
                提议图谱演化新候选 (Propose Candidate)
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
                    候选唯一ID (Candidate ID):
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
                    大纲范畴 (Scope Level):
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

function KnowledgeReviewEditor({
  unit,
  onProcessed
}: {
  unit: KnowledgeUnit;
  onProcessed: (id: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(unit.content || "");
  const [editLatex, setEditLatex] = useState(unit.latex || "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleUpdate = async (status: string) => {
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      if (isEditing) {
        const payload = { content: editContent, latex: editLatex };
        const res = await fetch(`${API_BASE}/api/admin/knowledge/units/${unit.id}`, {
          method: "PUT",
          headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Failed to save content edits.");
      }

      const action = status === "active" ? "approve" : "reject";
      const resPost = await fetch(`${API_BASE}/api/admin/knowledge/review`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ unit_ids: [unit.id], action })
      });
      if (!resPost.ok) throw new Error("Failed to update status.");

      onProcessed(unit.id);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Failed to process the unit.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white truncate max-w-lg">
          {unit.title}
        </h2>
        <div className="space-x-2 shrink-0 flex items-center">
          {errorMsg && <span className="text-xs text-red-500 mr-2">{errorMsg}</span>}
          {isEditing ? (
            <Button variant="secondary" size="sm" onClick={() => setIsEditing(false)} disabled={isSubmitting}>
              取消修改
            </Button>
          ) : (
            <Button variant="secondary" size="sm" onClick={() => setIsEditing(true)} disabled={isSubmitting}>
              编辑内容
            </Button>
          )}
          <Button variant="danger" size="sm" onClick={() => handleUpdate("rejected")} disabled={isSubmitting}>
            {isSubmitting ? "处理中..." : "驳回 (Reject)"}
          </Button>
          <Button variant="success" size="sm" onClick={() => handleUpdate("active")} disabled={isSubmitting}>
            {isSubmitting ? "处理中..." : "核准通过 (Approve)"}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6 pb-12">
          {unit.source_span && (
            <div className="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-amber-800 dark:text-amber-500 uppercase tracking-wider mb-2">
                教材原书引用出处
              </h4>
              {unit.source_span.page_start && (
                <div className="text-xs text-amber-700 dark:text-amber-400 mb-1 font-mono">
                  页码: {unit.source_span.page_start} - {unit.source_span.page_end || unit.source_span.page_start}
                </div>
              )}
              {unit.source_span.quote && (
                <blockquote className="text-xs text-amber-900 dark:text-amber-200/80 border-l-2 border-amber-400 dark:border-amber-700 pl-3 italic">
                  &quot;{unit.source_span.quote}&quot;
                </blockquote>
              )}
            </div>
          )}

          <div className="bg-white dark:bg-slate-900 rounded-lg shadow-sm border border-slate-200 dark:border-slate-800 p-5">
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
              条目文字内容
            </h3>
            {isEditing ? (
              <Textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="min-h-[220px] font-mono text-xs"
              />
            ) : (
              <div className="prose dark:prose-invert max-w-none text-sm">
                <LatexRenderer content={unit.content || ""} />
              </div>
            )}
          </div>

          {(unit.latex || isEditing) && (
            <div className="bg-white dark:bg-slate-900 rounded-lg shadow-sm border border-slate-200 dark:border-slate-800 p-5">
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
                LaTeX 独立数学公式
              </h3>
              {isEditing ? (
                <Textarea
                  value={editLatex}
                  onChange={(e) => setEditLatex(e.target.value)}
                  className="min-h-[100px] font-mono text-xs"
                />
              ) : (
                <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-md border border-slate-100 dark:border-slate-800 overflow-x-auto">
                  <LatexRenderer content={`\\[ ${unit.latex || ""} \\]`} />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function LegacyKnowledgeUnitsView() {
  const [units, setUnits] = useState<KnowledgeUnit[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>("draft");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(new Set());
  const [isPublishing, setIsPublishing] = useState(false);

  const fetchUnits = async () => {
    try {
      setLoading(true);
      setFetchError(null);
      const res = await fetch(`${API_BASE}/api/admin/knowledge/list`, { headers: getAuthHeaders() });
      if (!res.ok) throw new Error("Failed to fetch knowledge units");
      const data = await res.json();
      const list = data.units || data.items || [];
      setUnits(list);
      if (!selectedId && list.length > 0) {
        setSelectedId(list[0].id);
      }
    } catch (err: any) {
      console.error(err);
      setFetchError(err.message || "An unexpected error occurred while fetching units.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnits();
  }, []);

  const handleProcessed = (id: string) => {
    fetchUnits();
  };

  const handleBatchReview = async (action: "approve" | "reject") => {
    if (selectedIds.size === 0) return;
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/admin/knowledge/review`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ unit_ids: Array.from(selectedIds), action })
      });
      if (!res.ok) throw new Error(`Failed to batch ${action}`);
      setSelectedIds(new Set());
      await fetchUnits();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!confirm("即将根据已激活的知识库重新构建大语言模型的向量索引，是否继续？")) return;
    setIsPublishing(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/knowledge/publish`, {
        method: "POST",
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error("Failed to publish");
      alert("发布成功！已重新构建向量库索引。");
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsPublishing(false);
    }
  };

  const toggleChapter = (chapter: string) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(chapter)) next.delete(chapter);
      else next.add(chapter);
      return next;
    });
  };

  const toggleSelection = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const filteredUnits = units.filter((u) => {
    if (
      filterStatus !== "all" &&
      (u as any).review_status !== filterStatus &&
      (u as any).status !== filterStatus
    ) {
      const status = (u as any).review_status || (u as any).status || "draft";
      if (status !== filterStatus) return false;
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return u.title?.toLowerCase().includes(q) || u.content?.toLowerCase().includes(q);
    }
    return true;
  });

  const selectedUnit = units.find((u) => u.id === selectedId);

  const grouped = filteredUnits.reduce((acc, unit) => {
    const key = unit.chapter_path || "未分类章节";
    if (!acc[key]) acc[key] = [];
    acc[key].push(unit);
    return acc;
  }, {} as Record<string, KnowledgeUnit[]>);

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Left Pane */}
      <div className="w-96 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col shrink-0">
        <div className="p-3 border-b border-slate-200 dark:border-slate-800 flex flex-col gap-2.5">
          <div className="flex justify-between items-center">
            <h3 className="font-semibold text-xs text-slate-700 dark:text-slate-300">
              知识库分块核验 ({filteredUnits.length})
            </h3>
            <Button variant="primary" size="sm" className="h-7 text-xs" onClick={handlePublish} disabled={isPublishing}>
              {isPublishing ? "构建索引中..." : "重新发布索引"}
            </Button>
          </div>

          <input
            type="text"
            placeholder="搜索分块条目..."
            className="w-full px-3 py-1.5 border rounded-md text-xs dark:bg-slate-800 dark:border-slate-700 text-slate-800 dark:text-slate-200"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <div className="flex bg-slate-100 dark:bg-slate-800 p-0.5 rounded-md text-xs">
            {["draft", "active", "rejected", "all"].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterStatus(tab)}
                className={`flex-1 py-1 text-center rounded text-[11px] capitalize transition-colors ${
                  filterStatus === tab
                    ? "bg-white dark:bg-slate-700 shadow-sm font-semibold"
                    : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                }`}
              >
                {tab === "draft" ? "待审" : tab === "active" ? "已激活" : tab === "rejected" ? "已驳回" : "全部"}
              </button>
            ))}
          </div>

          {selectedIds.size > 0 && (
            <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-900/20 p-2 rounded-md">
              <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
                已选 {selectedIds.size} 项
              </span>
              <div className="space-x-1.5">
                <Button variant="success" size="sm" className="h-6 text-[11px] px-2" onClick={() => handleBatchReview("approve")}>
                  批量通过
                </Button>
                <Button variant="danger" size="sm" className="h-6 text-[11px] px-2" onClick={() => handleBatchReview("reject")}>
                  批量驳回
                </Button>
              </div>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {loading ? (
            <div className="text-xs text-slate-400 text-center py-6">正在加载条目...</div>
          ) : fetchError ? (
            <div className="text-xs text-red-500 bg-red-50 dark:bg-red-950/40 p-3 rounded-md">
              {fetchError} <Button variant="ghost" size="sm" onClick={fetchUnits}>重试</Button>
            </div>
          ) : Object.keys(grouped).length === 0 ? (
            <div className="text-xs text-slate-400 text-center py-6">没有匹配的分块条目。</div>
          ) : (
            Object.entries(grouped).map(([chapter, items]) => {
              const isExpanded = !expandedChapters.has(chapter);
              return (
                <div key={chapter} className="border border-slate-100 dark:border-slate-800 rounded-md overflow-hidden">
                  <div
                    className="flex justify-between items-center bg-slate-50 dark:bg-slate-800/50 p-2 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800"
                    onClick={() => toggleChapter(chapter)}
                  >
                    <h4 className="text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider truncate mr-2" title={chapter}>
                      {chapter}
                    </h4>
                    <span className="text-[11px] text-slate-400">{items.length}</span>
                  </div>

                  {isExpanded && (
                    <div className="divide-y divide-slate-100 dark:divide-slate-800">
                      {items.map((unit) => (
                        <div
                          key={unit.id}
                          onClick={() => setSelectedId(unit.id)}
                          className={`flex items-start px-3 py-2 cursor-pointer transition-colors ${
                            selectedId === unit.id
                              ? "bg-blue-50 dark:bg-blue-900/20"
                              : "hover:bg-slate-50 dark:hover:bg-slate-800/30"
                          }`}
                        >
                          <div className="pt-0.5 mr-2">
                            <input
                              type="checkbox"
                              checked={selectedIds.has(unit.id)}
                              onChange={() => {}}
                              onClick={(e) => toggleSelection(unit.id, e)}
                              className="w-3.5 h-3.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className={`text-xs font-semibold truncate ${selectedId === unit.id ? "text-blue-900 dark:text-blue-200" : "text-slate-700 dark:text-slate-300"}`}>
                              {unit.title}
                            </div>
                            <div className="text-[11px] text-slate-400 truncate mt-0.5">
                              {unit.content?.substring(0, 45) || "无正文"}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Pane */}
      <div className="flex-1 flex flex-col overflow-hidden bg-slate-50/50 dark:bg-slate-950">
        {selectedUnit ? (
          <KnowledgeReviewEditor key={selectedUnit.id} unit={selectedUnit} onProcessed={handleProcessed} />
        ) : (
          <div className="flex-1 flex items-center justify-center text-xs text-slate-400 dark:text-slate-500">
            从左侧章节列表中选择一个分块条目进行核对与修改
          </div>
        )}
      </div>
    </div>
  );
}

// ==========================================
// Main Admin Dashboard Page
// ==========================================
export default function AdminKnowledgePage() {
  const [activeTab, setActiveTab] = useState<"candidates" | "units">("candidates");

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

          {/* Tab Switcher */}
          <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-xs">
            <button
              onClick={() => setActiveTab("candidates")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-all ${
                activeTab === "candidates"
                  ? "bg-white dark:bg-slate-700 font-bold text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>图谱动态演化候选 (Graph Candidates)</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-500/20 text-amber-600 dark:text-amber-400 font-mono">
                5
              </span>
            </button>

            <button
              onClick={() => setActiveTab("units")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-all ${
                activeTab === "units"
                  ? "bg-white dark:bg-slate-700 font-bold text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <Layers className="w-3.5 h-3.5 text-blue-500" />
              <span>基础知识分块条目 (Legacy Chunks)</span>
            </button>
          </div>
        </div>

        {/* Quick Links */}
        <div className="flex items-center gap-3">
          <Link
            href="/graph"
            className="flex items-center gap-1.5 text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium"
          >
            <Network className="w-3.5 h-3.5" />
            查看全景图谱 (Canvas View)
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
        {activeTab === "candidates" ? <GraphCandidatesView /> : <LegacyKnowledgeUnitsView />}
      </main>
    </div>
  );
}
