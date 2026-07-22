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

  const fetchPending = async () => {
    try {
      setLoading(true);
      setFetchError(null);
      const res = await fetch(`${API_BASE}/api/admin/knowledge/pending`);
      if (!res.ok) throw new Error("Failed to fetch pending knowledge units");
      const data = await res.json();
      setUnits(data.units || data.items || []);
    } catch (err: any) {
      console.error(err);
      setFetchError(err.message || "An unexpected error occurred while fetching pending units.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, []);

  const selectedUnit = units.find((u) => u.id === selectedId);

  // Group by chapter
  const grouped = units.reduce((acc, unit) => {
    const key = unit.chapter_path || "Uncategorized";
    if (!acc[key]) acc[key] = [];
    acc[key].push(unit);
    return acc;
  }, {} as Record<string, KnowledgeUnit[]>);

  const handleProcessed = (id: string) => {
    setUnits((prev) => prev.filter((u) => u.id !== id));
    if (selectedId === id) setSelectedId(null);
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden">
      {/* Left Pane */}
      <div className="w-80 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100">
            Pending Review ({units.length})
          </h2>
          {fetchError && (
            <Button variant="ghost" size="sm" onClick={fetchPending} title="Retry fetch">
              Retry
            </Button>
          )}
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {loading ? (
            <div className="text-sm text-slate-500">Loading pending units...</div>
          ) : fetchError ? (
            <div className="text-sm text-red-500 bg-red-50 dark:bg-red-950 p-3 rounded-md">
              {fetchError}
            </div>
          ) : Object.keys(grouped).length === 0 ? (
            <div className="text-sm text-slate-500">No pending units.</div>
          ) : (
            Object.entries(grouped).map(([chapter, items]) => (
              <div key={chapter}>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  {chapter}
                </h3>
                <div className="space-y-1">
                  {items.map((unit) => (
                    <button
                      key={unit.id}
                      onClick={() => setSelectedId(unit.id)}
                      className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
                        selectedId === unit.id
                          ? "bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-100"
                          : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                      }`}
                    >
                      <div className="font-medium truncate">{unit.title}</div>
                    </button>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right Pane */}
      <div className="flex-1 flex flex-col bg-slate-50 dark:bg-slate-950 overflow-hidden">
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
