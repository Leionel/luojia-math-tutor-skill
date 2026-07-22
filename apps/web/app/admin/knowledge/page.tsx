"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { LatexRenderer } from "@/components/latex-renderer";
import { Textarea } from "@/components/ui/textarea";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

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
  onProcessed,
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
      // 1. If editing, update content first
      if (isEditing) {
        const payload = {
          content: editContent,
          latex: editLatex,
        };
        const res = await fetch(`${API_BASE}/api/admin/knowledge/units/${unit.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error("Failed to save content edits.");
      }

      // 2. Always update status using /review
      const action = status === "active" ? "approve" : "reject";
      const resPost = await fetch(`${API_BASE}/api/admin/knowledge/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ unit_ids: [unit.id], action }),
      });
      if (!resPost.ok) throw new Error("Failed to update status.");

      // Success
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
      <div className="p-6 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white truncate max-w-lg">
          {unit.title}
        </h1>
        <div className="space-x-3 shrink-0 flex items-center">
          {errorMsg && <span className="text-sm text-red-500 mr-2">{errorMsg}</span>}
          {isEditing ? (
            <Button variant="secondary" onClick={() => setIsEditing(false)} disabled={isSubmitting}>
              Cancel Edit
            </Button>
          ) : (
            <Button variant="secondary" onClick={() => setIsEditing(true)} disabled={isSubmitting}>
              Edit Content
            </Button>
          )}
          <Button
            variant="danger"
            onClick={() => handleUpdate("rejected")}
            disabled={isSubmitting}
          >
            {isSubmitting ? "Processing..." : "Reject"}
          </Button>
          <Button
            variant="success"
            onClick={() => handleUpdate("active")}
            disabled={isSubmitting}
          >
            {isSubmitting ? "Processing..." : "Approve"}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-8 pb-12">
          {unit.source_span && (
            <div className="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-amber-800 dark:text-amber-500 uppercase tracking-wider mb-2">
                Source Reference
              </h4>
              {unit.source_span.page_start && (
                <div className="text-sm text-amber-700 dark:text-amber-400 mb-2">
                  Pages: {unit.source_span.page_start} -{" "}
                  {unit.source_span.page_end || unit.source_span.page_start}
                </div>
              )}
              {unit.source_span.quote && (
                <blockquote className="text-sm text-amber-900 dark:text-amber-200/80 border-l-2 border-amber-400 dark:border-amber-700 pl-3 italic">
                  "{unit.source_span.quote}"
                </blockquote>
              )}
            </div>
          )}

          <div className="bg-white dark:bg-slate-900 rounded-lg shadow-sm border border-slate-200 dark:border-slate-800 p-6">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Content
            </h3>
            {isEditing ? (
              <Textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="min-h-[250px] font-mono text-sm"
              />
            ) : (
              <div className="prose dark:prose-invert max-w-none">
                <LatexRenderer content={unit.content || ""} />
              </div>
            )}
          </div>

          {(unit.latex || isEditing) && (
            <div className="bg-white dark:bg-slate-900 rounded-lg shadow-sm border border-slate-200 dark:border-slate-800 p-6">
              <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-4">
                LaTeX (Formula)
              </h3>
              {isEditing ? (
                <Textarea
                  value={editLatex}
                  onChange={(e) => setEditLatex(e.target.value)}
                  className="min-h-[120px] font-mono text-sm"
                />
              ) : (
                <div className="prose dark:prose-invert max-w-none bg-slate-50 dark:bg-slate-950 p-4 rounded-md border border-slate-100 dark:border-slate-800">
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

export default function AdminKnowledgePage() {
  const [units, setUnits] = useState<KnowledgeUnit[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  
  // New States
  const [filterStatus, setFilterStatus] = useState<string>("draft");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(new Set());
  const [isPublishing, setIsPublishing] = useState(false);

  const fetchUnits = async () => {
    try {
      setLoading(true);
      setFetchError(null);
      const res = await fetch(`${API_BASE}/api/admin/knowledge/list`);
      if (!res.ok) throw new Error("Failed to fetch knowledge units");
      const data = await res.json();
      setUnits(data.units || data.items || []);
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
    // We don't remove it from units anymore, we just refetch or update its status locally
    setUnits((prev) => prev.map((u) => {
      // It's already updated on the backend, we should just refetch or optimistically update.
      // Easiest is to refetch, but for UX, let's just refetch all to keep them in sync.
      return u;
    }));
    fetchUnits();
  };

  const handleBatchReview = async (action: "approve" | "reject") => {
    if (selectedIds.size === 0) return;
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/admin/knowledge/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ unit_ids: Array.from(selectedIds), action }),
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
      const res = await fetch(`${API_BASE}/api/admin/knowledge/publish`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to publish");
      alert("发布成功 (Publish successful)!");
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsPublishing(false);
    }
  };

  const toggleChapter = (chapter: string) => {
    setExpandedChapters(prev => {
      const next = new Set(prev);
      if (next.has(chapter)) next.delete(chapter);
      else next.add(chapter);
      return next;
    });
  };

  const toggleSelection = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const filteredUnits = units.filter(u => {
    if (filterStatus !== "all" && u.review_status !== filterStatus && (u as any).status !== filterStatus) {
      // check both review_status and status just in case backend used different key
      const status = u.review_status || (u as any).status || "draft";
      if (status !== filterStatus) return false;
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return u.title?.toLowerCase().includes(q) || u.content?.toLowerCase().includes(q);
    }
    return true;
  });

  const selectedUnit = units.find((u) => u.id === selectedId);

  // Group by chapter
  const grouped = filteredUnits.reduce((acc, unit) => {
    const key = unit.chapter_path || "Uncategorized";
    if (!acc[key]) acc[key] = [];
    acc[key].push(unit);
    return acc;
  }, {} as Record<string, KnowledgeUnit[]>);

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden text-slate-800 dark:text-slate-200">
      {/* Left Pane */}
      <div className="w-96 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-col gap-3">
          <div className="flex justify-between items-center">
            <h2 className="font-semibold text-lg">Review Center</h2>
            <Button variant="default" size="sm" onClick={handlePublish} disabled={isPublishing}>
              {isPublishing ? "Publishing..." : "Publish"}
            </Button>
          </div>
          
          <input 
            type="text" 
            placeholder="Search units..." 
            className="w-full px-3 py-2 border rounded-md text-sm dark:bg-slate-800 dark:border-slate-700"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-md text-sm">
            {["draft", "active", "rejected", "all"].map(tab => (
              <button 
                key={tab}
                onClick={() => setFilterStatus(tab)}
                className={`flex-1 py-1 text-center rounded-sm capitalize transition-colors ${filterStatus === tab ? "bg-white dark:bg-slate-700 shadow-sm font-medium" : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"}`}
              >
                {tab}
              </button>
            ))}
          </div>

          {selectedIds.size > 0 && (
            <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-900/20 p-2 rounded-md">
              <span className="text-xs font-medium text-blue-700 dark:text-blue-300">{selectedIds.size} selected</span>
              <div className="space-x-2">
                <Button variant="success" size="sm" className="h-7 text-xs px-2" onClick={() => handleBatchReview("approve")}>Approve</Button>
                <Button variant="danger" size="sm" className="h-7 text-xs px-2" onClick={() => handleBatchReview("reject")}>Reject</Button>
              </div>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading ? (
            <div className="text-sm text-slate-500">Loading units...</div>
          ) : fetchError ? (
            <div className="text-sm text-red-500 bg-red-50 dark:bg-red-950 p-3 rounded-md">
              {fetchError} <Button variant="ghost" size="sm" onClick={fetchUnits}>Retry</Button>
            </div>
          ) : Object.keys(grouped).length === 0 ? (
            <div className="text-sm text-slate-500">No units match your criteria.</div>
          ) : (
            Object.entries(grouped).map(([chapter, items]) => {
              const isExpanded = !expandedChapters.has(chapter); // default expanded
              return (
                <div key={chapter} className="border border-slate-100 dark:border-slate-800 rounded-md overflow-hidden">
                  <div 
                    className="flex justify-between items-center bg-slate-50 dark:bg-slate-800/50 p-2 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800"
                    onClick={() => toggleChapter(chapter)}
                  >
                    <h3 className="text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider truncate mr-2" title={chapter}>
                      {chapter}
                    </h3>
                    <span className="text-xs text-slate-400">{items.length}</span>
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
                          <div className="pt-1 mr-3">
                            <input 
                              type="checkbox" 
                              checked={selectedIds.has(unit.id)}
                              onChange={() => {}}
                              onClick={(e) => toggleSelection(unit.id, e)}
                              className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className={`text-sm font-medium truncate ${selectedId === unit.id ? 'text-blue-900 dark:text-blue-200' : 'text-slate-700 dark:text-slate-300'}`}>
                              {unit.title}
                            </div>
                            <div className="text-xs text-slate-400 truncate mt-0.5">
                              {unit.content?.substring(0, 50) || "No content"}
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
      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedUnit ? (
          <KnowledgeReviewEditor
            key={selectedUnit.id}
            unit={selectedUnit}
            onProcessed={handleProcessed}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400 dark:text-slate-500">
            Select a knowledge unit from the left to review.
          </div>
        )}
      </div>
    </div>
  );
}
