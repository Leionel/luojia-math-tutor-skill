"use client";

import { useState } from "react";
import Link from "next/link";
import type { Session } from "@/lib/api";
import { Edit2, Trash2, Check, X, User } from "lucide-react";
import { deleteSession, renameSession } from "@/lib/api";

export function Sidebar({
  sessions,
  activeSessionId,
  onSelect,
  onRefresh,
}: {
  sessions: Session[];
  activeSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onRefresh?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

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
    if (!confirm("确定要删除这个会话吗？")) return;
    try {
      await deleteSession(id);
      if (onRefresh) onRefresh();
    } catch(e) { console.error(e); }
  };

  const content = (
    <>
      <div className="mb-6 flex items-center justify-between rounded-md bg-[var(--bg-tertiary)] p-3 border border-[var(--border-subtle)] shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#617a55]/20 text-[#617a55]">
            <User className="h-5 w-5" />
          </div>
          <div className="flex flex-col overflow-hidden">
            <span className="truncate text-sm font-bold text-[var(--text-primary)] font-body">注册用户 (demo)</span>
            <span className="text-xs text-[#757a6b] font-body mt-0.5">角色: 学生</span>
          </div>
        </div>
        <Link href="/auth/login" className="p-1.5 text-[#757a6b] hover:text-[#c44a3d] hover:bg-[#c44a3d]/10 rounded-md transition-colors" title="退出登录">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
        </Link>
      </div>
      <div className="mb-4 text-[10px] font-bold tracking-[0.2em] uppercase text-[var(--text-muted)]">功能 (Features)</div>
      <div className="mb-8 grid gap-2 text-[13px]">
        <Link href="/mistake-book" className="flex items-center gap-2 rounded-md border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] px-3 py-2.5 font-medium text-[var(--text-secondary)] hover:border-[#c44a3d]/40 hover:text-[#c44a3d] transition-colors shadow-sm font-body">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
          全局错题本
        </Link>
        <Link href="/" className="flex items-center gap-2 px-3 py-2.5 font-medium text-[var(--text-secondary)] hover:text-[#617a55] transition-colors font-body -mx-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="opacity-70"><path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><path d="m14.5 4-5 16"/></svg>
          返回功能门户
        </Link>
        {[{id: "foundations", name: "基础概念", desc: "侧重于对定义、定理来源的通俗化解释，帮助扫盲并建立直觉基石。"}, 
          {id: "derivation", name: "深度推导", desc: "侧重于严谨的数学推演、证明步骤与逻辑链条，适合冲刺高分的拔高训练。"}, 
          {id: "problem_solving", name: "实战解题", desc: "侧重于解题技巧、套路总结和错题分析，直接面向应试拿分。"}].map((item) => (
          <div key={item.id} className="group relative rounded-md border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] px-3 py-2.5 font-medium text-[var(--text-secondary)] shadow-sm font-body hover:border-[#617a55]/40 hover:text-[#617a55] transition-colors cursor-help">
            {item.name}
            
            {/* HOVER TOOLTIP */}
            <div className="absolute left-0 top-full mt-2 w-full opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 z-[100] -translate-y-2 group-hover:translate-y-0">
              <div className="bg-white dark:bg-[#1e1e1b] border border-[#d6d0ba] dark:border-[#3e3f36] shadow-xl rounded-xl p-3 text-left">
                <div className="absolute -top-1.5 left-6 w-3 h-3 bg-white dark:bg-[#1e1e1b] border-l border-t border-[#d6d0ba] dark:border-[#3e3f36] rotate-45"></div>
                <p className="font-bold text-[var(--text-primary)] text-xs mb-1 relative z-10">{item.name}</p>
                <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed relative z-10">{item.desc}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="mb-4 text-[10px] font-bold tracking-[0.2em] uppercase text-[var(--text-muted)]">最近会话 (Sessions)</div>
      <div className="space-y-1.5 font-body">
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`group relative flex w-full flex-col rounded-md px-3 py-2.5 text-left text-[13px] transition-all duration-200 cursor-pointer ${
              activeSessionId === session.id 
                ? "bg-[var(--accent-light)] text-[var(--accent)] border border-[var(--accent-light)] shadow-sm font-bold" 
                : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] border border-transparent font-medium"
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
                  className="flex-1 bg-transparent border-b border-[#617a55] outline-none text-[13px]"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRename(session.id);
                    if (e.key === 'Escape') setEditingId(null);
                  }}
                />
                <button onClick={() => handleRename(session.id)} className="text-[#617a55] hover:text-[#4e6344]"><Check className="w-3.5 h-3.5" /></button>
                <button onClick={() => setEditingId(null)} className="text-[#c44a3d] hover:text-[#a33b30]"><X className="w-3.5 h-3.5" /></button>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <div className="truncate pr-4">{session.title}</div>
                  <div className="hidden group-hover:flex items-center gap-1.5 shrink-0">
                    <button onClick={(e) => { e.stopPropagation(); setEditingId(session.id); setEditTitle(session.title); }} className="text-[var(--text-muted)] hover:text-[#617a55]">
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={(e) => handleDelete(session.id, e)} className="text-[var(--text-muted)] hover:text-[#c44a3d]">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <div className="text-[11px] opacity-70 mt-0.5">{session.subject}</div>
              </>
            )}
          </div>
        ))}
      </div>
    </>
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
    </>
  );
}

