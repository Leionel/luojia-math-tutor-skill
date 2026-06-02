"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import type { Message, Subject, TutorMeta, TutorMode } from "@/lib/api";
import type { ReviewData } from "./review-card";
import { createSession, listMessages, listMistakes, listSessions, streamTutor, generateSimilarExercises, truncateSession, renameSession, generateNote, generateTitle } from "@/lib/api";
import { FileText, X, Printer, Loader2, Maximize, Minimize, Target } from "lucide-react";
import { getPreferredModel, getUserApiKey } from "@/lib/local-settings";
import { AppHeader } from "./app-header";
import { LearningPanel } from "./learning-panel";
import { MathMessage } from "./math-message";
import { Sidebar } from "./sidebar";
import { TutorInput } from "./tutor-input";
import { LatexRenderer } from "./latex-renderer";
import { ZenOverlay } from "./zen-overlay";
import { Button } from "./ui/button";

type LocalMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: string;
};

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
  const [subject, setSubject] = useState<Subject>("auto");
  const [mode, setMode] = useState<TutorMode>("socratic");
  const [meta, setMeta] = useState<TutorMeta | null>(null);
  const [mistakes, setMistakes] = useState<Array<{ mistake_code: string; concept: string; subject: string; created_at: string }>>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [thinkingElapsed, setThinkingElapsed] = useState(0);
  const [thinkingChains, setThinkingChains] = useState<Record<string, string>>({});
  const [inputValue, setInputValue] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [noteContent, setNoteContent] = useState("");
  const [isGeneratingNote, setIsGeneratingNote] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isMobileLearningOpen, setIsMobileLearningOpen] = useState(false);
  const [isZenMode, setIsZenMode] = useState(false);
  const [showZenConfirm, setShowZenConfirm] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_SIDEBAR_WIDTH);
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

  useEffect(() => {
    if (!isStreaming) {
      setThinkingElapsed(0);
      return;
    }
    const interval = setInterval(() => {
      setThinkingElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [isStreaming]);

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
      await newSession();
    }
  }

  async function newSession() {
    const created = await createSession(subject === "auto" ? "foundations" : subject);
    const refreshed = await listSessions().catch(() => []);
    setSessions(refreshed);
    setSessionId(created.session_id);
    
    let initialMessages: LocalMessage[] = [{ id: "welcome", role: "assistant", content: welcome }];
    const pendingQuiz = sessionStorage.getItem("pendingQuiz");
    if (pendingQuiz) {
      initialMessages.push({ id: crypto.randomUUID(), role: "assistant", content: pendingQuiz });
      sessionStorage.removeItem("pendingQuiz");
    }
    
    setMessages(initialMessages);
    setMeta(null);
    setMistakes([]);
  }

  async function selectSession(nextSessionId: string) {
    setSessionId(nextSessionId);
    const [serverMessages, serverMistakes] = await Promise.all([
      listMessages(nextSessionId).catch(() => [] as Message[]),
      listMistakes(nextSessionId).catch(() => [])
    ]);
    
    let currentMessages = serverMessages.map((item) => ({ id: item.id, role: item.role, content: item.content }));
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
  }

  async function submit(value: string, forcedMode?: TutorMode, requestedHint: boolean = false) {
    let activeSession = sessionId;
    if (!activeSession) {
      const created = await createSession(subject === "auto" ? "foundations" : subject);
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
        generateTitle(value, getUserApiKey() || null, getPreferredModel() || null).then(async (autoTitle) => {
          await renameSession(activeSession, autoTitle).catch(() => {});
          listSessions("demo-user", searchQuery).then((s) => setSessions(s)).catch(() => {});
        }).catch(() => {});
      }

      await streamTutor(
        {
          session_id: activeSession,
          message: value,
          subject,
          mode: forcedMode || mode,
          user_api_key: getUserApiKey() || null,
          model: getPreferredModel(),
          requested_hint: requestedHint,
          abortSignal: abortControllerRef.current.signal,
        },
        (nextMeta) => {
          setMeta(nextMeta);
        },
        (token) => {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId ? { ...message, content: `${message.content}${token}` } : message
            )
          );
        },
        (chain) => {
          setThinkingChains((prev) => ({ ...prev, [assistantId]: chain }));
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
    setShowNoteModal(true);
    setNoteContent("");
    try {
      const res = await generateNote(sessionId);
      setNoteContent(res.note);
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
        }
        setIsZenMode(true);
      } else {
        if (document.exitFullscreen && document.fullscreenElement) {
          await document.exitFullscreen();
        }
        setIsZenMode(false);
      }
    } catch (err) {
      console.error("Fullscreen API error", err);
      setIsZenMode(!isZenMode);
    }
  };

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
          subject={subject}
          mode={mode}
          onSubjectChange={setSubject}
          onModeChange={setMode}
          onNewSession={() => void newSession()}
          onToggleSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
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

        {!isZenMode && (
          <div className="hidden shrink-0 flex-col lg:flex" style={{ width: sidebarWidth }}>
            <Sidebar sessions={sessions} activeSessionId={sessionId} onSelect={(id) => void selectSession(id)} onRefresh={() => void bootstrap()} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          </div>
        )}
        {!isZenMode && <ResizeHandle target="sidebar" className="hidden lg:block" />}
        <main className={`flex min-w-0 flex-1 flex-col ${isZenMode ? "px-4 sm:px-20 lg:px-40" : ""}`}>
          <div className={`flex-1 overflow-y-auto ${isZenMode ? "scrollbar-hide" : ""}`}>
            <div className="mx-auto max-w-3xl px-4 py-8 pb-32">
              <div className="flex justify-end mb-2">
                <button onClick={handleGenerateNote} disabled={isGeneratingNote || !sessionId} className="flex items-center gap-1.5 text-xs font-bold bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] px-4 py-2 rounded-full border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors shadow-sm">
                  {isGeneratingNote ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileText className="w-3.5 h-3.5 text-indigo-500" />}
                  生成随堂笔记
                </button>
              </div>
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
                    thinkingChain={message.role === "assistant" && !isStreaming ? (thinkingChains[message.id] || "") : ""}
                    reviewData={idx === lastAssistantIdx && !isStreaming ? reviewData : null}
                    onEdit={message.role === "user" ? async () => {
                      if (!sessionId) return;
                      await truncateSession(sessionId, message.id);
                      setInputValue(message.content);
                      const msgs = await listMessages(sessionId);
                      setMessages(msgs.map((item) => ({ id: item.id, role: item.role, content: item.content })));
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
                        setMessages(msgs.map((item) => ({ id: item.id, role: item.role, content: item.content })));
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
          <div className="hidden shrink-0 flex-col xl:flex" style={{ width: learningWidth }}>
            <LearningPanel meta={meta} mistakes={mistakes} />
          </div>
        )}
      </div>

      {showNoteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 sm:p-8">
          <div className="bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-2xl shadow-2xl w-full max-w-3xl h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-300">
            <div className="flex justify-between items-center p-4 border-b border-[var(--border-primary)] bg-[var(--bg-header)]">
              <div className="flex items-center gap-2 font-bold text-[var(--text-primary)]">
                <FileText className="w-5 h-5 text-indigo-500" />
                智能随堂笔记
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => {
                  const printContent = document.getElementById("note-print-area");
                  if (printContent) {
                    const originalBody = document.body.innerHTML;
                    document.body.innerHTML = printContent.innerHTML;
                    window.print();
                    document.body.innerHTML = originalBody;
                    window.location.reload(); // Quick restore hack
                  }
                }} disabled={isGeneratingNote} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] rounded-md transition-colors disabled:opacity-50">
                  <Printer className="w-3.5 h-3.5" /> 打印 / 导出 PDF
                </button>
                <button onClick={() => setShowNoteModal(false)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] p-1.5 rounded-md transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div id="note-print-area" className="flex-1 overflow-y-auto p-6 md:p-8 bg-white dark:bg-[#1a1a18]">
              {isGeneratingNote ? (
                <div className="h-full flex flex-col items-center justify-center space-y-4 text-[var(--text-muted)]">
                  <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                  <p className="animate-pulse">正在为您提炼本节课核心考点与易错陷阱...</p>
                </div>
              ) : (
                <div className="prose prose-sm md:prose-base dark:prose-invert max-w-none">
                  <LatexRenderer content={noteContent} />
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Zen Mode Confirmation Modal */}
      {showZenConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden animate-in zoom-in-95 duration-300">
            <div className="p-6">
              <div className="w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center mb-4 text-indigo-500">
                <Target className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2">进入心流模式</h3>
              <p className="text-[var(--text-secondary)] text-sm mb-4 leading-relaxed">
                即将为您打造绝对专注的沉浸空间。这将会：
              </p>
              <ul className="space-y-2 text-sm text-[var(--text-secondary)] mb-6">
                <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-indigo-500" /> 将页面最大化全屏</li>
                <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-indigo-500" /> 隐藏侧边栏等所有干扰信息</li>
                <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-indigo-500" /> 开启 25 分钟番茄钟与粉红噪音</li>
              </ul>
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
    </div>
  );
}
