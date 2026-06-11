"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import type { Message, Subject, TutorMeta, TutorMode } from "@/lib/api";
import type { ReviewData } from "./review-card";
import { createSession, listMessages, listMistakes, listSessions, listNotes, streamTutor, generateSimilarExercises, truncateSession, renameSession, generateNote, saveNote, generateTitle } from "@/lib/api";
import { FileText, X, Printer, Loader2, Maximize, Minimize, Target, PenTool, Sparkles, ChevronLeft, ChevronRight } from "lucide-react";
import { getPreferredModel, getUserApiKey } from "@/lib/local-settings";
import { AppHeader } from "./app-header";
import { ConfirmDialog } from "./confirm-dialog";
import { LearningPanel } from "./learning-panel";
import { MathMessage } from "./math-message";
import { Sidebar } from "./sidebar";
import { TutorInput } from "./tutor-input";
import { LatexRenderer } from "./latex-renderer";
import { ZenOverlay } from "./zen-overlay";
import { Button } from "./ui/button";
import Link from "next/link";

type LocalMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: string;
  thinkingSummary?: string;
  thinkingElapsedMs?: number;
  learningMeta?: TutorMeta | null;
};

function mapServerMessages(items: Message[]): LocalMessage[] {
  return items.map((item) => ({
    id: item.id,
    role: item.role,
    content: item.content,
    thinkingSummary: item.thinking_summary,
    thinkingElapsedMs: item.thinking_elapsed_ms,
    learningMeta: item.learning_meta,
  }));
}

function latestLearningMeta(items: Message[]): TutorMeta | null {
  for (let index = items.length - 1; index >= 0; index -= 1) {
    if (items[index].role === "assistant" && items[index].learning_meta) {
      return items[index].learning_meta ?? null;
    }
  }
  return null;
}

const welcome = `### 欢迎来到珞珈数智助教
你好！我是一款专为东方美学与深层逻辑打造的数学助教。
你可以随时与我探讨**高等数学**、**线性代数**或**概率论与数理统计**的问题。

#### ✨ 核心功能指南
- **🎓 启发式教学**：我不会直接告诉你答案，而是以苏格拉底式的提问引导你思考。你可以点击右下角的“直接解答”切换模式。
- **📊 实时掌握度追踪**：在右侧的学习面板，你可以看到每个知识点的精确掌握度，如同草木生长般清晰可见。
- **📝 自动错题本**：推导中的谬误会被自动记录成册，随时从侧边栏的“全局错题本”回顾并生成针对性练习。
- **🎨 动态可视化**：你可以随时对我说“帮我画出 $y = x^2$ 的图像”或者“画出正态分布的图像”，抽象的数学将在水墨之间展现。

准备好了吗？试试发送：
> 我算 $\\int x^2 dx = x^3$，对吗？`;

const MIN_WIDTH = 200;
const MAX_WIDTH = 600;
const DEFAULT_SIDEBAR_WIDTH = 260;
const DEFAULT_LEARNING_WIDTH = 320;

export function TutorChat() {
  const [sessions, setSessions] = useState<Array<{ id: string; title: string; subject: string; user_id: string; created_at: string; updated_at: string }>>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([{ id: "welcome", role: "assistant", content: welcome }]);

  const [mode, setMode] = useState<TutorMode>("socratic");
  const [meta, setMeta] = useState<TutorMeta | null>(null);
  const [mistakes, setMistakes] = useState<Array<{ mistake_code: string; concept: string; subject: string; created_at: string }>>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [thinkingElapsed, setThinkingElapsed] = useState(0);
  const [thinkingChains, setThinkingChains] = useState<Record<string, string>>({});
  const [inputValue, setInputValue] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [rightPanelMode, setRightPanelMode] = useState<"learning" | "note">("learning");
  const [noteContent, setNoteContent] = useState("");
  const [isGeneratingNote, setIsGeneratingNote] = useState(false);
  const [showNoteToast, setShowNoteToast] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isMobileLearningOpen, setIsMobileLearningOpen] = useState(false);
  const [isZenMode, setIsZenMode] = useState(false);
  const [showZenConfirm, setShowZenConfirm] = useState(false);
  const [showNewSessionConfirm, setShowNewSessionConfirm] = useState(false);
  const [newSessionBlocked, setNewSessionBlocked] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_SIDEBAR_WIDTH);

  // Sync collapsed state from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("luojia_sidebar_collapsed");
    if (saved === "true") {
      setIsSidebarCollapsed(true);
    }
  }, []);

  const handleToggleSidebar = (collapsed: boolean) => {
    setIsSidebarCollapsed(collapsed);
    localStorage.setItem("luojia_sidebar_collapsed", String(collapsed));
  };
  const [learningWidth, setLearningWidth] = useState(DEFAULT_LEARNING_WIDTH);
  const [isResizing, setIsResizing] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isStreaming, thinkingElapsed]);

  const status = useMemo(() => {
    if (!meta) return undefined;
    return `${meta.verified ? "已后台验算" : "未完成后台验算"} · ${mode === "direct" ? "直接讲解" : mode === "practice" ? "练习模式" : "引导模式"}`;
  }, [meta, mode]);

  const reviewData = useMemo<ReviewData | null>(() => {
    if (!meta || meta.verified === false || meta.is_correct === null) return null;
    return {
      concepts: meta.concepts || [],
      is_correct: meta.is_correct,
      mistake: meta.mistake,
      mastery_score: meta.mastery_score ?? 0.5,
      mastery_label: meta.mastery_label ?? "一般",
      mastery_delta: meta.mastery_delta ?? 0,
    };
  }, [meta]);

  useEffect(() => {
    const timer = setTimeout(() => {
      listSessions("demo-user", searchQuery).then((data) => setSessions(data)).catch(() => {});
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    void bootstrap();
  }, []);

  const isThinkingActive = messages.some(
    (message) => message.status === "thinking"
  );

  useEffect(() => {
    if (!isThinkingActive) {
      setThinkingElapsed(0);
      return;
    }
    const interval = setInterval(() => {
      setThinkingElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [isThinkingActive]);

  const sidebarWidthRef = useRef(sidebarWidth);
  const learningWidthRef = useRef(learningWidth);

  useEffect(() => {
    sidebarWidthRef.current = sidebarWidth;
  }, [sidebarWidth]);

  useEffect(() => {
    learningWidthRef.current = learningWidth;
  }, [learningWidth]);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const container = document.getElementById("main-layout");
      if (!container) return;

      const containerRect = container.getBoundingClientRect();
      const mouseX = e.clientX - containerRect.left;

      if (isResizing === "sidebar") {
        const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, mouseX));
        setSidebarWidth(newWidth);
      } else if (isResizing === "learning") {
        const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, containerRect.width - mouseX));
        setLearningWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(null);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizing]);

  async function bootstrap() {
    const existing = await listSessions().catch(() => []);
    setSessions(existing);
    if (existing[0]) {
      await selectSession(existing[0].id);
    } else {
      resetToDraftSession();
    }
  }

  function resetToDraftSession() {
    setSessionId(null);
    let initialMessages: LocalMessage[] = [{ id: "welcome", role: "assistant", content: welcome }];
    const pendingQuiz = sessionStorage.getItem("pendingQuiz");
    if (pendingQuiz) {
      initialMessages.push({ id: crypto.randomUUID(), role: "assistant", content: pendingQuiz });
      sessionStorage.removeItem("pendingQuiz");
    }
    setMessages(initialMessages);
    setMeta(null);
    setMistakes([]);
    setNoteContent("");
    setRightPanelMode("learning");
  }

  async function newSession() {
    // No DB call here — show local "draft" session. The real session row
    // will be created lazily by submit() when the user sends a message.
    resetToDraftSession();
  }

  async function selectSession(nextSessionId: string) {
    setSessionId(nextSessionId);
    const [serverMessages, serverMistakes, savedNotes] = await Promise.all([
      listMessages(nextSessionId).catch(() => [] as Message[]),
      listMistakes(nextSessionId).catch(() => []),
      listNotes("demo-user").catch(() => []),
    ]);
    
    let currentMessages: LocalMessage[] = mapServerMessages(serverMessages);
    if (!currentMessages.length) {
      currentMessages = [{ id: "welcome", role: "assistant", content: welcome }];
    }

    const pendingQuiz = sessionStorage.getItem("pendingQuiz");
    if (pendingQuiz) {
      currentMessages.push({ id: crypto.randomUUID(), role: "assistant", content: pendingQuiz });
      sessionStorage.removeItem("pendingQuiz");
    }
    
    setMessages(currentMessages);
    setMistakes(serverMistakes);
    setMeta(latestLearningMeta(serverMessages));
    setNoteContent(
      savedNotes.find((note) => note.session_id === nextSessionId)?.content
      || ""
    );
  }

  async function submit(value: string, forcedMode?: TutorMode, requestedHint: boolean = false) {
    let activeSession = sessionId;
    if (!activeSession) {
      const created = await createSession("综合");
      activeSession = created.session_id;
      setSessionId(activeSession);
    }

    const userMessage: LocalMessage = { id: crypto.randomUUID(), role: "user", content: value };
    const assistantId = crypto.randomUUID();
    setMessages((current) => [...current, userMessage, { id: assistantId, role: "assistant", content: "", status: "thinking" }]);
    setIsStreaming(true);
    setMeta(null);
    setThinkingChains({});
    setThinkingElapsed(0);
    abortControllerRef.current = new AbortController();

    try {
      const isFirstUserMessage = messages.filter((m) => m.role === "user").length === 0;
      if (isFirstUserMessage) {
        generateTitle(value, getUserApiKey() || null, getPreferredModel() || null).then(async ({ title: autoTitle, label: autoLabel }) => {
          await renameSession(activeSession, autoTitle, autoLabel).catch(() => {});
          listSessions("demo-user", searchQuery).then((s) => setSessions(s)).catch(() => {});
        }).catch(() => {});
      }

      await streamTutor(
        {
          session_id: activeSession,
          message: value,
          subject: "综合" as any,
          mode: forcedMode || mode,
          user_api_key: getUserApiKey() || null,
          model: getPreferredModel(),
          requested_hint: requestedHint,
          image_urls: undefined,
          abortSignal: abortControllerRef.current.signal
        },
        (nextMeta) => {
          setMeta(nextMeta);
        },
        (token) => {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId ? {
                ...message,
                content: `${message.content}${token}`,
                status: message.status === "thinking" ? "typing" : message.status
              } : message
            )
          );
        },
        (chain) => {
          setThinkingChains((prev) => ({ ...prev, [assistantId]: chain }));
        },
        (content) => {
          // onOpening: append content but keep thinking status
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId ? {
                ...message,
                content: `${message.content}${content}`,
                status: message.status || "thinking"
              } : message
            )
          );
        },
        ({ summary, elapsedMs }) => {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId ? {
                ...message,
                thinkingSummary: summary,
                thinkingElapsedMs: elapsedMs,
              } : message
            )
          );
          setThinkingChains((current) => {
            const next = { ...current };
            delete next[assistantId];
            return next;
          });
        }
      );
      const [refreshedSessions, refreshedMistakes] = await Promise.all([
        listSessions().catch(() => sessions),
        listMistakes(activeSession).catch(() => mistakes)
      ]);
      setSessions(refreshedSessions);
      setMistakes(refreshedMistakes);
    } catch (error) {
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId
            ? { ...message, content: `### 当前判断\n接口调用失败：${error instanceof Error ? error.message : "未知错误"}` }
            : message
        )
      );
    } finally {
      setIsStreaming(false);
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId ? { ...message, status: undefined } : message
        )
      );
    }
  }

  async function handleGenerateNote() {
    if (!sessionId) return;
    setIsGeneratingNote(true);
    setRightPanelMode("note");
    setNoteContent("");
    try {
      const res = await generateNote(sessionId);
      setNoteContent(res.note);
      
      const currentSession = sessions.find((s) => s.id === sessionId);
      const sessionSubject = currentSession?.subject || "综合";
      
      // Auto-save to notebook
      await saveNote("demo-user", {
        session_id: sessionId,
        subject: sessionSubject,
        content: res.note
      });
      
      setShowNoteToast(true);
      setTimeout(() => setShowNoteToast(false), 3000);
    } catch (e) {
      setNoteContent("生成笔记失败，请重试。");
    } finally {
      setIsGeneratingNote(false);
    }
  }

  const toggleZenMode = async () => {
    try {
      if (!isZenMode) {
        if (document.documentElement.requestFullscreen) {
          await document.documentElement.requestFullscreen();
          setIsZenMode(true);
        } else {
          // Fallback: browser doesn't support fullscreen API
          setIsZenMode(true);
        }
      } else {
        setIsZenMode(false);
        if (document.exitFullscreen && document.fullscreenElement) {
          await document.exitFullscreen();
        }
      }
    } catch (err) {
      console.error("Fullscreen API error", err);
      // On error, revert to safe state
      setIsZenMode(false);
    }
  };

  // Sync isZenMode when browser exits fullscreen via ESC / F11
  useEffect(() => {
    const handleFSChange = () => {
      if (!document.fullscreenElement) {
        setIsZenMode(false);
      }
    };
    document.addEventListener("fullscreenchange", handleFSChange);
    return () => document.removeEventListener("fullscreenchange", handleFSChange);
  }, []);

  const ResizeHandle = ({ target, className = "" }: { target: string; className?: string }) => (
    <div
      className={`group relative z-10 w-1.5 cursor-col-resize transition-colors hover:bg-blue-400/50 active:bg-blue-500/70 ${className}`}
      onMouseDown={(e) => {
        e.preventDefault();
        setIsResizing(target);
      }}
    >
      <div className="absolute inset-y-0 -left-2 -right-2" />
      <div className="absolute inset-y-3 left-1/2 w-0.5 -translate-x-1/2 rounded-full bg-slate-300 opacity-0 transition-opacity group-hover:opacity-100" />
    </div>
  );

  return (
    <div className="flex h-screen flex-col bg-[var(--bg-primary)] transition-colors duration-300 overflow-hidden relative">
      <ZenOverlay isZenMode={isZenMode} />
      {isZenMode && (
        <Button 
          variant="ghost" 
          onClick={toggleZenMode}
          className="fixed top-6 left-6 z-50 text-white/50 hover:text-white hover:bg-white/10 transition-colors rounded-full px-4"
        >
          <Minimize className="w-4 h-4 mr-2" />
          退出沉浸模式
        </Button>
      )}

      {!isZenMode && (
        <AppHeader
          mode={mode}
          onModeChange={setMode}
          onNewSession={() => {
            // If already on an empty draft (no real session yet), nothing to do.
            if (!sessionId && !messages.some((m) => m.role === "user")) {
              setNewSessionBlocked(true);
            } else {
              setShowNewSessionConfirm(true);
            }
          }}
          onToggleSidebar={() => {
            if (window.innerWidth >= 1024) {
              handleToggleSidebar(!isSidebarCollapsed);
            } else {
              setIsMobileSidebarOpen(!isMobileSidebarOpen);
            }
          }}
          onToggleLearning={() => setIsMobileLearningOpen(!isMobileLearningOpen)}
          onToggleZenMode={() => {
            if (!isZenMode) setShowZenConfirm(true);
            else void toggleZenMode();
          }}
        />
      )}
      
      <div id="main-layout" className="flex min-h-0 flex-1 relative">
        {/* Mobile Sidebar Overlay */}
        {isMobileSidebarOpen && (
          <div className="fixed inset-0 z-40 lg:hidden bg-black/50 backdrop-blur-sm" onClick={() => setIsMobileSidebarOpen(false)}>
            <div className="absolute left-0 top-0 bottom-0 w-[280px] bg-white dark:bg-[var(--bg-card)] shadow-xl" onClick={e => e.stopPropagation()}>
              <Sidebar sessions={sessions} activeSessionId={sessionId} onSelect={(id) => { void selectSession(id); setIsMobileSidebarOpen(false); }} onRefresh={() => void bootstrap()} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
            </div>
          </div>
        )}
        
        {/* Mobile Learning Overlay */}
        {isMobileLearningOpen && (
          <div className="fixed inset-0 z-40 xl:hidden bg-black/50 backdrop-blur-sm" onClick={() => setIsMobileLearningOpen(false)}>
            <div className="absolute right-0 top-0 bottom-0 w-[320px] bg-white dark:bg-[var(--bg-card)] shadow-xl" onClick={e => e.stopPropagation()}>
              <LearningPanel meta={meta} mistakes={mistakes} />
            </div>
          </div>
        )}

        {!isZenMode && !isSidebarCollapsed && (
          <div className="group hidden shrink-0 flex-col lg:flex relative" style={{ width: sidebarWidth }}>
            <Sidebar sessions={sessions} activeSessionId={sessionId} onSelect={(id) => void selectSession(id)} onRefresh={() => void bootstrap()} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
            <button
              onClick={() => handleToggleSidebar(true)}
              className="absolute -right-3 top-20 z-20 flex h-6 w-6 items-center justify-center rounded-full border border-[var(--border-primary)] bg-white dark:bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-[#617a55] hover:scale-110 transition-all shadow-sm opacity-0 group-hover:opacity-100"
              title="收起侧边栏"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
        {!isZenMode && !isSidebarCollapsed && <ResizeHandle target="sidebar" className="hidden lg:block" />}

        {!isZenMode && isSidebarCollapsed && (
          <button
            onClick={() => handleToggleSidebar(false)}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-30 group flex h-20 w-4 items-center justify-center rounded-r-md border border-l-0 border-[var(--border-primary)] bg-white/80 dark:bg-[var(--bg-card)] backdrop-blur-sm text-[var(--text-muted)] hover:text-[#617a55] hover:w-5 transition-all shadow-sm"
            title="展开侧边栏"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
        <main className={`flex min-w-0 flex-1 flex-col ${isZenMode ? "px-4 sm:px-20 lg:px-40" : ""}`}>
          <div className={`flex-1 overflow-y-auto ${isZenMode ? "scrollbar-hide" : ""}`}>
            <div className="mx-auto max-w-3xl px-4 py-8 pb-32">

              {(() => {
                const lastAssistantIdx = messages.reduce((acc, m, i) =>
                  m.role === "assistant" && m.status !== "thinking" ? i : acc, -1);
                return messages.map((message, idx) => (
                  <MathMessage
                    key={message.id}
                    role={message.role}
                    content={message.content}
                    status={message.role === "assistant" && message.status !== "thinking" ? status : undefined}
                    isThinking={message.status === "thinking" && isStreaming}
                    thinkingElapsed={thinkingElapsed}
                    thinkingChain={message.role === "assistant" ? (thinkingChains[message.id] || "") : ""}
                    thinkingSummary={message.thinkingSummary}
                    thinkingElapsedMs={message.thinkingElapsedMs}
                    reviewData={idx === lastAssistantIdx && !isStreaming ? reviewData : null}
                    onEdit={message.role === "user" ? async () => {
                      if (!sessionId) return;
                      await truncateSession(sessionId, message.id);
                      setInputValue(message.content);
                      const msgs = await listMessages(sessionId);
                      setMessages(mapServerMessages(msgs));
                      setMeta(latestLearningMeta(msgs));
                    } : undefined}
                    onRetry={message.role === "assistant" ? async () => {
                      if (!sessionId) return;
                      let prevUserMsg = null;
                      for(let j=idx-1; j>=0; j--){
                        if(messages[j].role === "user"){ prevUserMsg = messages[j]; break;}
                      }
                      if(prevUserMsg) {
                        await truncateSession(sessionId, prevUserMsg.id);
                        const msgs = await listMessages(sessionId);
                        setMessages(mapServerMessages(msgs));
                        setMeta(latestLearningMeta(msgs));
                        void submit(prevUserMsg.content);
                      }
                    } : undefined}
                    onSimilar={() => {
                      if (meta?.concepts?.[0]) {
                        const concept = meta.concepts[0];
                        const masteryScore = meta.mastery_score ?? 0.5;
                        const difficulty = masteryScore >= 0.8 ? 3 : masteryScore >= 0.5 ? 2 : 1;
                        generateSimilarExercises(concept, difficulty, 1)
                          .then(exercises => {
                            if (exercises && exercises.length > 0) {
                              const exercise = exercises[0];
                              const msg = `请练习这道关于"${concept}"的类似题：\n\n${exercise.text}\n\n（完成解答后可告诉我你的答案或步骤）`;
                              const assistantId = crypto.randomUUID();
                              setMessages((current) => [...current, { id: assistantId, role: "assistant", content: msg }]);
                              setMode("practice");
                            } else {
                              void submit("请给我生成一道类似的练习题。", "practice");
                            }
                          })
                          .catch(() => {
                            void submit("请给我生成一道类似的练习题。", "practice");
                          });
                      } else {
                        void submit("请给我生成一道类似的练习题。", "practice");
                      }
                    }}
                  />
                ));
              })()}
              <div ref={messagesEndRef} />
            </div>
          </div>
          {isStreaming && (
            <div className="flex justify-center mb-2">
              <button 
                onClick={() => abortControllerRef.current?.abort()}
                className="flex items-center gap-2 bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] border border-[var(--border-primary)] rounded-full px-4 py-1.5 text-xs font-bold text-rose-500 hover:text-rose-600 transition-colors shadow-sm"
              >
                <div className="w-2 h-2 rounded-sm bg-current animate-pulse" />
                停止生成
              </button>
            </div>
          )}
          <div className="shrink-0 p-4 relative z-10 mx-auto w-full max-w-4xl">
            <TutorInput
              value={inputValue}
              onChange={setInputValue}
              disabled={isStreaming}
              onSubmit={(val, forcedMode) => void submit(val, forcedMode)}
              onDirect={() => void submit("我需要完整的推导过程和最终答案。请直接告诉我怎么做，不要反问我。", "direct")}
              onHint={() => void submit("能不能给我一点提示？", "socratic")}
              onSimilar={() => void submit("出一道类似的题目给我练习。", "practice")}
            />
          </div>
        </main>

        {!isZenMode && <ResizeHandle target="learning" className="hidden xl:block" />}
        {!isZenMode && (
          <div className="hidden shrink-0 flex-col xl:flex bg-[var(--bg-tertiary)] border-l border-[var(--border-subtle)]" style={{ width: learningWidth }}>
            <div className="flex items-center gap-2 p-2 border-b border-[var(--border-subtle)] shrink-0">
              <button 
                onClick={() => setRightPanelMode("learning")}
                className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-colors ${rightPanelMode === "learning" ? "bg-[var(--bg-card)] shadow-sm text-emerald-500 border border-[var(--border-primary)]" : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"}`}
              >
                状态复盘
              </button>
              <button 
                onClick={() => setRightPanelMode("note")}
                className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-colors ${rightPanelMode === "note" ? "bg-[var(--bg-card)] shadow-sm text-indigo-500 border border-[var(--border-primary)]" : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"}`}
              >
                随堂笔记
              </button>
            </div>
            
            <div className="flex-1 overflow-hidden relative">
              {rightPanelMode === "learning" ? (
                <LearningPanel meta={meta} mistakes={mistakes} />
              ) : (
                <div className="absolute inset-0 flex flex-col bg-[var(--bg-card)]">
                  <div className="flex justify-between items-center p-3 border-b border-[var(--border-primary)] shrink-0">
                    <div className="flex items-center gap-1.5 font-bold text-[var(--text-primary)] text-sm">
                      <FileText className="w-4 h-4 text-indigo-500" />
                      随堂笔记
                      {!isGeneratingNote && noteContent && (
                        <Link href="/notebook" className="ml-1 text-[10px] font-normal text-[#617a55] bg-[#617a55]/10 hover:bg-[#617a55]/20 px-1.5 py-0.5 rounded-sm border border-[#617a55]/20 transition-colors">
                          ✓ 已保存
                        </Link>
                      )}
                    </div>
                    {!isGeneratingNote && noteContent && (
                      <button onClick={() => {
                        void submit("我已经阅读完这份随堂笔记。请基于笔记中的核心考点与易错陷阱，为我出一份包含 3 道题的针对性小测验（先出第一题，不要直接给答案，让我一步步来练习）。", "practice");
                      }} className="flex items-center gap-1 px-2 py-1 text-[10px] font-bold bg-[#617a55] text-white hover:bg-[#617a55]/90 rounded-md transition-colors">
                        <PenTool className="w-3 h-3" /> 基于笔记测验
                      </button>
                    )}
                  </div>
                  <div id="note-print-area" className="flex-1 overflow-y-auto p-4 md:p-5">
                    {isGeneratingNote ? (
                      <div className="h-full flex flex-col items-center justify-center space-y-3 text-[var(--text-muted)]">
                        <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                        <p className="text-xs animate-pulse">正在提炼核心考点...</p>
                      </div>
                    ) : !noteContent ? (
                      <div className="h-full flex flex-col items-center justify-center space-y-4 text-[var(--text-muted)] text-center px-4">
                        <div className="w-16 h-16 rounded-full bg-indigo-500/10 flex items-center justify-center">
                          <FileText className="w-8 h-8 text-indigo-500/50" />
                        </div>
                        <div className="space-y-1">
                          <h3 className="font-bold text-[var(--text-primary)]">智能笔记总结</h3>
                          <p className="text-xs">复习完当前内容后，点击下方按钮，AI将为你提炼核心考点与易错陷阱。</p>
                        </div>
                        <button 
                          onClick={handleGenerateNote} 
                          disabled={!sessionId}
                          className="mt-4 flex items-center gap-2 px-6 py-2.5 text-sm font-bold bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-lg shadow-indigo-500/20 transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100"
                        >
                          <Sparkles className="w-4 h-4" /> 
                          一键生成笔记
                        </button>
                      </div>
                    ) : (
                      <div className="prose prose-sm dark:prose-invert max-w-none text-[13px] leading-relaxed">
                        <LatexRenderer content={noteContent} />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            {/* Sticky Generate Button for Learning Panel */}
            {rightPanelMode === "learning" && !noteContent && !isGeneratingNote && (
              <div className="p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-tertiary)] shrink-0">
                <button 
                  onClick={handleGenerateNote}
                  disabled={!sessionId}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-bold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-lg shadow-indigo-500/20 transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100"
                >
                  <FileText className="w-4 h-4" /> 
                  生成本节课专属笔记
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* New Session Confirmation Dialog */}
      <ConfirmDialog
        open={showNewSessionConfirm}
        onConfirm={() => {
          setShowNewSessionConfirm(false);
          void newSession();
        }}
        onCancel={() => setShowNewSessionConfirm(false)}
        title="开启新会话？"
        description="开启新会话后，当前会话仍会在侧边栏中保留，你可以随时切换回来继续学习。"
        confirmText="确认开启"
        cancelText="取消"
      />

      {/* Blocked: no conversation yet */}
      <ConfirmDialog
        open={newSessionBlocked}
        onConfirm={() => setNewSessionBlocked(false)}
        onCancel={() => setNewSessionBlocked(false)}
        title="已经在新会话中"
        description="当前已经是一个未开始的新会话，请先发送一条消息开始学习，再创建另一个新会话。"
        confirmText="知道了"
        cancelText=""
      />

      {/* Zen Mode Confirmation Modal */}
      {showZenConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200" onClick={() => setShowZenConfirm(false)}>
          <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden animate-in zoom-in-95 duration-300" onClick={e => e.stopPropagation()}>
            <div className="p-6">
              <div className="w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center mb-4 text-indigo-500">
                <Target className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2">进入心流模式</h3>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-6">
                沉浸模式将全屏并隐藏侧边栏与学习面板，带给你无干扰的极致心流体验。
                <br/><br/>
                ✨ 附带专注番茄钟（支持自定义时长）与白噪音（右上角）。
                <br/>
                <span className="text-[var(--text-muted)] italic">提示：随时可以按 ESC 键，或点击右上角的“退出”按钮恢复原状。</span>
              </p>
              <div className="flex items-center justify-end gap-3">
                <Button 
                  variant="ghost" 
                  onClick={() => setShowZenConfirm(false)}
                  className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
                >
                  取消
                </Button>
                <Button 
                  onClick={() => {
                    setShowZenConfirm(false);
                    void toggleZenMode();
                  }}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-6 shadow-md transition-colors"
                >
                  确认进入
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      <div className={`fixed top-4 left-1/2 -translate-x-1/2 z-[150] transition-all duration-300 ${showNoteToast ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-4 pointer-events-none"}`}>
        <div className="bg-emerald-500/10 backdrop-blur-md border border-emerald-500/20 text-emerald-500 font-bold px-4 py-2 rounded-full shadow-lg flex items-center gap-2 text-sm">
          <FileText className="w-4 h-4" />
          笔记已在右侧边栏生成！
        </div>
      </div>
    </div>
  );
}
