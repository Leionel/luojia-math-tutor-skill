"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import type { Message, Subject, TutorMeta, TutorMode } from "@/lib/api";
import type { ReviewData } from "./review-card";
import { createSession, listMessages, listMistakes, listSessions, streamTutor, generateSimilarExercises, truncateSession, renameSession } from "@/lib/api";
import { getPreferredModel, getUserApiKey } from "@/lib/local-settings";
import { AppHeader } from "./app-header";
import { LearningPanel } from "./learning-panel";
import { MathMessage } from "./math-message";
import { Sidebar } from "./sidebar";
import { TutorInput } from "./tutor-input";

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
    let isNewSession = false;
    if (!activeSession) {
      const created = await createSession(subject === "auto" ? "foundations" : subject);
      activeSession = created.session_id;
      setSessionId(activeSession);
      isNewSession = true;
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
      if (isNewSession) {
        const autoTitle = value.length > 15 ? value.slice(0, 15) + "..." : value;
        await renameSession(activeSession, autoTitle).catch(() => {});
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
    <div className="flex h-[100dvh] flex-col bg-transparent text-[var(--text-primary)] transition-colors duration-300">
      <AppHeader
        subject={subject}
        mode={mode}
        onSubjectChange={setSubject}
        onModeChange={setMode}
        onNewSession={() => void newSession()}
      />
      <div id="main-layout" className="flex min-h-0 flex-1">
        <div className="hidden shrink-0 flex-col lg:flex" style={{ width: sidebarWidth }}>
          <Sidebar sessions={sessions} activeSessionId={sessionId} onSelect={(id) => void selectSession(id)} onRefresh={() => void bootstrap()} />
        </div>
        <ResizeHandle target="sidebar" className="hidden lg:block" />
        <main className="flex min-w-0 flex-1 flex-col">
          <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="mx-auto flex max-w-4xl flex-col gap-4">
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
          <TutorInput
            value={inputValue}
            onChange={setInputValue}
            disabled={isStreaming}
            onSubmit={(value) => void submit(value)}
            onHint={() => void submit("请给我下一层提示。", undefined, true)}
            onDirect={() => {
              setMode("direct");
              void submit("请给出完整解答。", "direct");
            }}
            onSimilar={() => {
              if (meta?.concepts?.[0]) {
                const concept = meta.concepts[0];
                const masteryScore = meta.mastery_score ?? 0.5;
                const difficulty = masteryScore >= 0.8 ? 3 : masteryScore >= 0.5 ? 2 : 1;
                
                generateSimilarExercises(concept, difficulty, 1)
                  .then(exercises => {
                    if (exercises && exercises.length > 0) {
                      const exercise = exercises[0];
                      const msg = `请练习这道关于“${concept}”的类似题：\n\n${exercise.text}\n\n（完成解答后可告诉我你的答案或步骤）`;
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
        </main>
        <ResizeHandle target="learning" className="hidden xl:block" />
        <div className="hidden shrink-0 flex-col xl:flex" style={{ width: learningWidth }}>
          <LearningPanel meta={meta} mistakes={mistakes} />
        </div>
      </div>
    </div>
  );
}
