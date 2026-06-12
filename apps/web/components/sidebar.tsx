"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Session } from "@/lib/api";
import { Edit2, Trash2, Check, X, User, Search } from "lucide-react";
import { deleteSession, renameSession } from "@/lib/api";
import {
  nextVisibleSessionCount,
  SESSION_BATCH_SIZE,
} from "@/lib/ui-runtime";
import { ConfirmDialog } from "./confirm-dialog";

export function Sidebar({
  sessions,
  activeSessionId,
  onSelect,
  onRefresh,
  onDeleted,
  searchQuery,
  onSearchChange,
  onModeSelect,
}: {
  sessions: Session[];
  activeSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onRefresh?: () => void;
  onDeleted?: (deletedId: string) => void;
  searchQuery?: string;
  onSearchChange?: (val: string) => void;
  onModeSelect?: (modeId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [visibleCount, setVisibleCount] = useState(SESSION_BATCH_SIZE);

  const SUBJECT_MAP: Record<string, string> = {
    calculus: "高等数学",
    linear_algebra: "线性代数",
    probability: "概率论"
  };

  const handleRename = async (id: string) => {
    if (!editTitle.trim()) return setEditingId(null);
    try {
      await renameSession(id, editTitle);
      if (onRefresh) onRefresh();
    } catch(e) { console.error(e); }
    setEditingId(null);
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteTarget(id);
  };

  const confirmDelete = async () => {
    const id = deleteTarget;
    if (!id) return;
    // Let errors propagate to ConfirmDialog — it will keep the dialog open and show the error.
    await deleteSession(id);
    if (onDeleted) onDeleted(id);
    if (onRefresh) onRefresh();
    setDeleteTarget(null);
  };

  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  const uniqueTags = Array.from(new Set(sessions.map(s => SUBJECT_MAP[s.subject] || s.subject || "综合"))).filter(Boolean);

  const filteredSessions = sessions.filter(s => {
    if (selectedTag) {
      const sTag = SUBJECT_MAP[s.subject] || s.subject || "综合";
      if (sTag !== selectedTag) return false;
    }
    return true;
  });
  const visibleSessions = filteredSessions.slice(0, visibleCount);
  const remainingSessions = Math.max(0, filteredSessions.length - visibleCount);

  useEffect(() => {
    setVisibleCount(SESSION_BATCH_SIZE);
  }, [searchQuery, selectedTag]);

  const content = (
    <div className="flex flex-col h-full relative">
      {/* Top decorative ink drop / gradient */}
      <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-[#617a55]/10 to-transparent pointer-events-none -mt-5 -mx-5" />

      {/* Section: Sessions */}
      <div className="mb-4 flex items-center gap-3">
        <div className="h-px bg-[var(--border-subtle)] flex-1"></div>
        <div className="text-[10px] font-bold tracking-[0.25em] uppercase text-[var(--text-muted)] font-body">最近会话 Sessions</div>
        <div className="h-px bg-[var(--border-subtle)] flex-1"></div>
      </div>
      
      {onSearchChange && (
        <div className="mb-4 space-y-3">
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-[var(--text-muted)] group-focus-within:text-[#617a55] transition-colors" />
            </div>
            <input
              type="text"
              className="block w-full pl-9 pr-4 py-2 border border-[var(--border-subtle)] rounded-full text-[13px] bg-white/50 dark:bg-black/10 text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[#617a55]/20 focus:border-[#617a55] transition-all shadow-sm font-body"
              placeholder="搜索历史对话内容..."
              value={searchQuery || ""}
              onChange={(e) => onSearchChange(e.target.value)}
            />
          </div>
          
          {uniqueTags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <button
                onClick={() => setSelectedTag(null)}
                className={`px-2.5 py-1 text-[11px] font-medium rounded-full transition-colors border ${
                  selectedTag === null 
                    ? "bg-[#617a55] text-white border-[#617a55]" 
                    : "bg-white/50 dark:bg-black/20 text-[var(--text-secondary)] border-[var(--border-subtle)] hover:bg-[#617a55]/10 hover:text-[#617a55] hover:border-[#617a55]/30"
                }`}
              >
                全部
              </button>
              {uniqueTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => setSelectedTag(tag)}
                  className={`px-2.5 py-1 text-[11px] font-medium rounded-full transition-colors border ${
                    selectedTag === tag 
                      ? "bg-[#617a55] text-white border-[#617a55]" 
                      : "bg-white/50 dark:bg-black/20 text-[var(--text-secondary)] border-[var(--border-subtle)] hover:bg-[#617a55]/10 hover:text-[#617a55] hover:border-[#617a55]/30"
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="space-y-2 font-body flex-1 overflow-y-auto pr-1">
        {visibleSessions.map((session) => (
          <div
            key={session.id}
            className={`group relative flex w-full flex-col rounded-xl px-4 py-3 text-left text-[13px] transition-all duration-300 cursor-pointer ${
              activeSessionId === session.id 
                ? "bg-gradient-to-r from-[#617a55]/15 to-transparent text-[var(--text-primary)] border-l-[3px] border-[#617a55] shadow-sm font-bold" 
                : "text-[var(--text-secondary)] hover:bg-white/40 dark:hover:bg-black/10 border-l-[3px] border-transparent font-medium hover:border-[var(--border-subtle)]"
            }`}
            onClick={() => {
              if (editingId === session.id) return;
              onSelect(session.id);
              setOpen(false);
            }}
          >
            {editingId === session.id ? (
              <div className="flex items-center gap-2 w-full" onClick={(e) => e.stopPropagation()}>
                <input 
                  autoFocus
                  className="flex-1 bg-white/50 dark:bg-black/20 border-b border-[#617a55] outline-none text-[13px] px-1 py-0.5 rounded-sm"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRename(session.id);
                    if (e.key === 'Escape') setEditingId(null);
                  }}
                />
                <button onClick={() => handleRename(session.id)} className="text-[#617a55] hover:text-[#4e6344] p-1 rounded-md hover:bg-[#617a55]/10"><Check className="w-3.5 h-3.5" /></button>
                <button onClick={() => setEditingId(null)} className="text-[#c44a3d] hover:text-[#a33b30] p-1 rounded-md hover:bg-[#c44a3d]/10"><X className="w-3.5 h-3.5" /></button>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <div className="truncate pr-2 font-title text-[14px]">{session.title}</div>
                  <div className="flex items-center gap-0.5 shrink-0 opacity-60 lg:opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => { e.stopPropagation(); setEditingId(session.id); setEditTitle(session.title); }}
                      aria-label="重命名会话"
                      className="text-[var(--text-muted)] hover:text-[#617a55] p-2 rounded-md hover:bg-[#617a55]/10 transition-colors touch-manipulation"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={(e) => handleDelete(session.id, e)}
                      aria-label="删除会话"
                      className="text-[var(--text-muted)] hover:text-[#c44a3d] p-2 rounded-md hover:bg-[#c44a3d]/10 transition-colors touch-manipulation"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <div className="mt-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] tracking-widest font-medium border border-[#617a55]/20 bg-[#617a55]/5 text-[#617a55] dark:border-[#8da47e]/30 dark:bg-[#8da47e]/10 dark:text-[#8da47e]">
                    {SUBJECT_MAP[session.subject] || session.subject}
                  </span>
                </div>
              </>
            )}
          </div>
        ))}
        {remainingSessions > 0 && (
          <button
            type="button"
            onClick={() => setVisibleCount((current) =>
              nextVisibleSessionCount(current, filteredSessions.length)
            )}
            className="w-full rounded-lg border border-[var(--border-subtle)] px-3 py-2 text-xs font-medium text-[var(--text-secondary)] transition-colors hover:border-[#617a55]/40 hover:bg-[#617a55]/5 hover:text-[#617a55]"
          >
            加载更多（剩余 {remainingSessions} 条）
          </button>
        )}
      </div>
    </div>
  );

  return (
    <>
      <button
        className="fixed left-3 top-20 z-20 rounded-md border border-[var(--border-primary)] bg-[var(--bg-secondary)] text-[var(--text-primary)] px-3 py-2 text-sm shadow-sm backdrop-blur-md lg:hidden"
        onClick={() => setOpen((v) => !v)}
      >
        会话
      </button>
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/30 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}
      <aside
        className={`fixed left-0 top-16 z-30 h-[calc(100vh-4rem)] w-64 shrink-0 overflow-y-auto border-r border-[var(--border-primary)] bg-gray-50 dark:bg-[var(--bg-sidebar)] dark:backdrop-blur-3xl p-5 transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] lg:static lg:w-full lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {content}
      </aside>

      <ConfirmDialog
        open={deleteTarget !== null}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
        title="删除会话"
        description="删除后会话中的所有消息和验算记录将被永久移除，此操作不可恢复。"
        confirmText="确认删除"
        cancelText="取消"
        variant="destructive"
      />
    </>
  );
}
