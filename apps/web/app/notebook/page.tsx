"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {getCurrentUserId,isAuthStorageKey} from "@/lib/demo-auth";
import { ArrowLeft, BookOpen, Trash2, Printer, Target } from "lucide-react";
import { listNotes, deleteNote, type NoteEntry } from "@/lib/api";
import { LatexRenderer } from "@/components/latex-renderer";
import { NotebookChat } from "@/components/notebook-chat";
import {documentNoteSource} from "@/lib/document-note-source";
import { DocumentNoteUpload } from "@/components/document-note-upload";

export default function NotebookPage() {
  const [identity,setIdentity]=useState(0);
  useEffect(()=>{const changed=()=>setIdentity(n=>n+1);const storage=(e:StorageEvent)=>{if(isAuthStorageKey(e.key))changed();};window.addEventListener("luojia-auth-change",changed);window.addEventListener("storage",storage);return()=>{window.removeEventListener("luojia-auth-change",changed);window.removeEventListener("storage",storage);};},[]);
  return <NotebookContent key={identity}/>;
}
function NotebookContent() {
  const [notes, setNotes] = useState<NoteEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);
  const [filterSubject, setFilterSubject] = useState<string>("all");

  const refresh = () => {
    setLoading(true);
    listNotes(getCurrentUserId())
      .then((data) => {
        setNotes(data);
        const requested=new URLSearchParams(window.location.search).get("note");
        if(requested&&data.some(n=>n.id===requested))setSelectedNoteId(requested);
        else if (data.length > 0 && !selectedNoteId) {
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

  const selectedSource=selectedNote?documentNoteSource(selectedNote):null;
  return (
    <div className="flex h-dvh min-h-0 flex-col md:flex-row bg-[var(--bg-primary)] text-[var(--text-primary)] transition-colors duration-300 overflow-hidden">
      {/* Left Sidebar (List) */}
      <aside className="w-full max-h-[55dvh] shrink-0 overflow-y-auto md:max-h-none md:w-80 border-r border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/70 flex flex-col h-full flex-shrink-0 backdrop-blur-md">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-[var(--border-subtle)] px-4 glass-header">
          <Link href="/chat" className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span>返回对话</span>
          </Link>
          <div className="flex items-center gap-1.5 font-bold tracking-wider text-xs text-olive-700 dark:text-olive-300">
            <BookOpen className="w-4 h-4 text-olive-600 dark:text-olive-400" />
            <span>随堂笔记本</span>
          </div>
        </header>

        <div className="p-3.5 border-b border-[var(--border-subtle)] space-y-3">
          <select
            value={filterSubject}
            onChange={(e) => setFilterSubject(e.target.value)}
            className="w-full bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-xl px-3 py-2 text-xs font-medium text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-olive-500 shadow-xs"
          >
            <option value="all">全部课程范畴</option>
            <option value="foundations">基础概念与公理</option>
            <option value="derivation">深度数理推导</option>
            <option value="problem_solving">经典习题实践</option>
          </select>
          <DocumentNoteUpload
            description="选择已有资料后按需生成。上传只保存原文，不会自动生成笔记；笔记采用章节大纲与抽样正文。"
            onGenerated={refresh}
          />
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1.5 scrollbar-hide">
          {loading ? (
            <div className="p-6 text-center text-xs text-[var(--text-muted)] animate-pulse">
              笔记加载中...
            </div>
          ) : filteredNotes.length === 0 ? (
            <div className="p-6 text-center text-xs text-[var(--text-muted)]">
              暂无笔记记录
            </div>
          ) : (
            filteredNotes.map((note) => (
              <button
                key={note.id}
                onClick={() => setSelectedNoteId(note.id)}
                className={`w-full text-left p-3 rounded-xl flex flex-col gap-1.5 transition-all group ${
                  selectedNoteId === note.id
                    ? "bg-white dark:bg-[#252622] border border-olive-500/35 shadow-xs font-semibold"
                    : "hover:bg-white/40 dark:hover:bg-white/5 border border-transparent font-medium"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-olive-500/10 text-olive-700 dark:text-olive-300 tracking-wider">
                    {note.subject}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">
                      {new Date(note.created_at).toLocaleDateString([], { month: 'numeric', day: 'numeric' })}
                    </span>
                    <Trash2 
                      className={`w-3 h-3 text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity hover:text-rose-600 ${selectedNoteId === note.id ? "opacity-100" : ""}`}
                      onClick={(e) => handleDelete(note.id, e)}
                    />
                  </div>
                </div>
                <div className="text-xs font-medium text-[var(--text-primary)] line-clamp-2 leading-relaxed">
                  {documentNoteSource(note).content.split("\n")[0].replace(/[#*`]/g, "") || "无标题笔记"}
                </div>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Right Content Area */}
      <main className="min-h-0 flex-1 flex flex-col min-w-0 bg-[var(--bg-primary)]">
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
            <div className="min-h-0 flex-1 flex overflow-hidden">
              {/* Left Note Content */}
              <div id="note-print-area" className="flex-1 overflow-y-auto p-4 sm:p-8 lg:p-12 bg-white dark:bg-[#1a1a18]">
                <div className="max-w-2xl mx-auto">
                  <div className="mb-8 flex items-center gap-2 text-sm text-[#617a55] font-mono">
                    <Target className="w-4 h-4" />
                    <span>{new Date(selectedNote.created_at).toLocaleString()} / {selectedNote.subject}</span>
                  </div>
                  <div className="prose prose-sm md:prose-base dark:prose-invert max-w-none">
                    {selectedSource?.source&&<details className="mb-4 text-xs"><summary className="min-h-11 cursor-pointer py-3">来源与覆盖范围</summary><p className="break-all">原文版本：{selectedSource.source.sourceHash}</p><p className="mt-2">正文抽样 {selectedSource.source.sampleChars} 字符；原文 {selectedSource.source.sourceChars} 字符，另含章节大纲。</p><Link href={`/reading?document=${encodeURIComponent(selectedSource.source.documentId)}&source_hash=${selectedSource.source.sourceHash}`} className="inline-flex min-h-11 items-center underline">核对原资料 →</Link></details>}
                    {selectedNote.session_id.startsWith("document:")&&!selectedSource?.source&&<p className="mb-4 text-xs">旧笔记未记录来源版本与抽样范围；不能补认定为全文覆盖。</p>}
                    <LatexRenderer content={selectedSource?.content??selectedNote.content} />
                  </div>
                </div>
              </div>
              
              {/* Right Chat Area — document notes have no live session to revisit */}
              <div className="w-[450px] shrink-0 border-l border-[var(--border-primary)] flex flex-col bg-[var(--bg-primary)] hidden xl:flex">
                {selectedNote.session_id.startsWith("document:") ? (
                  <div className="flex flex-1 flex-col items-center justify-center text-[var(--text-muted)] p-8 text-center">
                    <BookOpen className="w-10 h-10 mb-3 opacity-20" />
                    <p className="text-sm max-w-xs">
                      这份笔记由上传的教材整理生成。如需深入探讨，回到对话页针对笔记内容继续提问即可。
                    </p>
                  </div>
                ) : (
                  <NotebookChat sessionId={selectedNote.session_id} subject={selectedNote.subject} />
                )}
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
