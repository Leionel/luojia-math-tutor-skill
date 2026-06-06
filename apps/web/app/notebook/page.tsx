"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, BookOpen, Trash2, Printer, Target } from "lucide-react";
import { listNotes, deleteNote, type NoteEntry } from "@/lib/api";
import { LatexRenderer } from "@/components/latex-renderer";
import { NotebookChat } from "@/components/notebook-chat";

export default function NotebookPage() {
  const [notes, setNotes] = useState<NoteEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);
  const [filterSubject, setFilterSubject] = useState<string>("all");

  const refresh = () => {
    setLoading(true);
    listNotes("demo-user")
      .then((data) => {
        setNotes(data);
        if (data.length > 0 && !selectedNoteId) {
          setSelectedNoteId(data[0].id);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("确定要删除这条随堂笔记吗？")) return;
    try {
      await deleteNote(id);
      if (selectedNoteId === id) setSelectedNoteId(null);
      refresh();
    } catch (err) {
      alert("删除失败");
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const filteredNotes = notes.filter((n) => filterSubject === "all" || n.subject === filterSubject);
  const selectedNote = notes.find((n) => n.id === selectedNoteId);

  return (
    <div className="flex h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] transition-colors duration-300 overflow-hidden">
      {/* Left Sidebar (List) */}
      <aside className="w-80 border-r border-[var(--border-primary)] bg-[var(--bg-tertiary)] flex flex-col h-full flex-shrink-0">
        <header className="flex h-16 shrink-0 items-center border-b border-[var(--border-primary)] bg-[var(--bg-header)] px-4">
          <Link href="/" className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
            <ArrowLeft className="w-4 h-4" />
            返回学习
          </Link>
          <div className="ml-auto flex items-center gap-2 font-bold tracking-widest uppercase">
            <BookOpen className="w-4 h-4 text-indigo-500" />
            <span>Notebook</span>
          </div>
        </header>

        <div className="p-4 border-b border-[var(--border-subtle)]">
          <select 
            value={filterSubject}
            onChange={(e) => setFilterSubject(e.target.value)}
            className="w-full bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[#617a55]"
          >
            <option value="all">所有科目 (All Subjects)</option>
            <option value="foundations">基础概念 (Foundations)</option>
            <option value="derivation">深度推导 (Derivation)</option>
            <option value="problem_solving">解题实践 (Problem Solving)</option>
          </select>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-hide">
          {loading ? (
            <div className="p-4 text-center text-sm text-[var(--text-muted)] animate-pulse">
              加载中...
            </div>
          ) : filteredNotes.length === 0 ? (
            <div className="p-4 text-center text-sm text-[var(--text-muted)]">
              暂无笔记记录
            </div>
          ) : (
            filteredNotes.map((note) => (
              <button
                key={note.id}
                onClick={() => setSelectedNoteId(note.id)}
                className={`w-full text-left p-3 rounded-lg flex flex-col gap-1.5 transition-colors group ${
                  selectedNoteId === note.id
                    ? "bg-[#617a55]/10 border border-[#617a55]/20"
                    : "hover:bg-[var(--bg-hover)] border border-transparent"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">
                    {note.subject}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-[var(--text-muted)]">
                      {new Date(note.created_at).toLocaleDateString()}
                    </span>
                    <Trash2 
                      className={`w-3.5 h-3.5 text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity hover:text-rose-600 ${selectedNoteId === note.id ? "opacity-100" : ""}`}
                      onClick={(e) => handleDelete(note.id, e)}
                    />
                  </div>
                </div>
                <div className="text-sm font-medium text-[var(--text-primary)] line-clamp-2 leading-relaxed">
                  {note.content.split("\n")[0].replace(/[#*`]/g, "") || "Untitled Note"}
                </div>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Right Content Area */}
      <main className="flex-1 flex flex-col min-w-0 bg-[var(--bg-primary)]">
        {selectedNote ? (
          <>
            <header className="flex h-16 shrink-0 justify-end items-center border-b border-[var(--border-subtle)] px-6">
              <button 
                onClick={() => {
                  const printContent = document.getElementById("note-print-area");
                  if (printContent) {
                    const originalBody = document.body.innerHTML;
                    document.body.innerHTML = printContent.innerHTML;
                    window.print();
                    document.body.innerHTML = originalBody;
                    window.location.reload();
                  }
                }}
                className="print:hidden flex items-center gap-1.5 text-xs font-bold bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] px-3 py-1.5 rounded-md transition-colors text-[var(--text-primary)]"
              >
                <Printer className="w-3.5 h-3.5" /> 打印 / 导出 PDF
              </button>
            </header>
            <div className="flex-1 flex overflow-hidden">
              {/* Left Note Content */}
              <div id="note-print-area" className="flex-1 overflow-y-auto p-8 lg:p-12 bg-white dark:bg-[#1a1a18]">
                <div className="max-w-2xl mx-auto">
                  <div className="mb-8 flex items-center gap-2 text-sm text-[#617a55] font-mono">
                    <Target className="w-4 h-4" />
                    <span>{new Date(selectedNote.created_at).toLocaleString()} / {selectedNote.subject}</span>
                  </div>
                  <div className="prose prose-sm md:prose-base dark:prose-invert max-w-none">
                    <LatexRenderer content={selectedNote.content} />
                  </div>
                </div>
              </div>
              
              {/* Right Chat Area */}
              <div className="w-[450px] shrink-0 border-l border-[var(--border-primary)] flex flex-col bg-[var(--bg-primary)] hidden xl:flex">
                <NotebookChat sessionId={selectedNote.session_id} subject={selectedNote.subject} />
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-[var(--text-muted)] p-8 text-center">
            <BookOpen className="w-12 h-12 mb-4 opacity-20" />
            <h2 className="text-xl font-mono font-medium mb-2">Notebook</h2>
            <p className="text-sm max-w-md">
              选择左侧的一条随堂笔记进行阅读。你可以在学习时点击顶部的“智能笔记”按钮，AI 会自动为你生成并保存本节课的精华。
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
