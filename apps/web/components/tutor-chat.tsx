"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import type { Message, Subject, TutorMeta, TutorMode, WebSearchMode, RootSubmission, RootDiagnosis } from "@/lib/api";
import type { ReviewData } from "./review-card";
import { mergeAgentRun, type AgentRun } from "@/lib/agent-run";
import { getAgentRun, startRootProbe, createSession, listMessages, listMistakes, listSessions, listNotes, streamTutor, truncateSession, renameSession, generateNote, saveNote, generateTitle } from "@/lib/api";
import { messageStatus } from "@/lib/message-status";
import { FileText, X, Printer, Loader2, Maximize, Minimize, Target, PenTool, Sparkles, ChevronLeft, ChevronRight } from "lucide-react";
import { getPreferredModel, getUserApiKey } from "@/lib/local-settings";
import { AppHeader } from "./app-header";
import { TutorCompanion } from "./tutor-companion";
import { ConfirmDialog } from "./confirm-dialog";
import { LearningPanel } from "./learning-panel";
import { MathMessage } from "./math-message";
import { Sidebar } from "./sidebar";
import { MobileDrawer } from "./mobile-drawer";
import { RootAttemptForm } from "./root-attempt-form";
import { TutorInput } from "./tutor-input";
import { LatexRenderer } from "./latex-renderer";
import { ZenOverlay } from "./zen-overlay";
import { Button } from "./ui/button";
import { GlobalSearchModal } from "./global-search-modal";
import type { ReasoningEffortLevel } from "./tutor-input";
import Link from "next/link";
import {learningRequest, type LabRun} from "@/lib/learning-api";
import {rootContextRef, referenceChatKey, studyRequested, type LearningContextRef, type LearningTaskSnapshot} from "@/lib/learning-context";
import {getCurrentUserId} from "@/lib/demo-auth";
import {ChatLifetime} from "@/lib/chat-lifetime";
import {ContextBanner} from "./learning/context-banner";

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

const welcome = `### 从你正在读的一页、正在算的一步开始
我是小珞，珞珈数智的 AI 数学助教。我们可以一起读教材、核对推导、做数值实验，也可以讨论高等数学、线性代数和概率统计。

- **读懂条件**：说明公式在什么条件下适用；教材伴读会保留原文来源。
- **检查过程**：把自己的步骤发来；求根轨迹可用数值规则核对，其他回答会注明检查依据与限制。
- **按需帮助**：默认给适量提示；切换“直接讲解”或明确索取时可以给完整过程。练习先给题目，作答后再核对。
- **回看记录**：学习面板的估计与错题记录供复习参考，不等于已证明掌握。

试试问我：
> 牛顿法的残差很小，就一定接近根了吗？`;

const PROMPT_SUGGESTIONS = [
  {
    category: "数值分析",
    icon: "xₖ",
    title: "残差与根误差",
    desc: "残差很小，为什么还需要误差依据？",
    prompt: "牛顿法得到的残差很小，是否一定接近根？请解释两者关系与需要的条件。",
  },
  {
    category: "数值分析",
    icon: "[a,b]",
    title: "二分法的前提",
    desc: "端点异号之外，还需确认什么？",
    prompt: "对函数 1/x 在 [-1,1] 上用二分法，因为端点异号所以一定有根，对吗？",
  },
  {
    category: "线性代数",
    icon: "A·x",
    title: "特征值与几何变换",
    desc: "如何从几何拉伸与旋转的角度理解矩阵特征向量？",
    prompt: "请用几何变换与空间拉伸的直观语言，帮我理解矩阵的特征值与特征向量是什么意义？",
  },
  {
    category: "概率统计",
    icon: "P(A)",
    title: "贝叶斯逆向推断",
    desc: "为什么先验概率与后验概率常颠覆我们的直觉？",
    prompt: "请通过一个生动直观的经典例子（如罕见病筛查），引导我理解贝叶斯公式与逆向推断思维。",
  },
];

const MIN_WIDTH = 200;
const MAX_WIDTH = 600;
const DEFAULT_SIDEBAR_WIDTH = 260;
const DEFAULT_LEARNING_WIDTH = 320;

function ResizeHandle({target,className="",onStart}:{target:string;className?:string;onStart:(target:string)=>void}) {
  return <div
    className={`group relative z-10 w-1.5 cursor-col-resize transition-colors hover:bg-olive-400/50 active:bg-olive-500/70 ${className}`}
    onMouseDown={event=>{event.preventDefault();onStart(target);}}
  >
    <div className="absolute inset-y-0 -left-2 -right-2" />
    <div className="absolute inset-y-3 left-1/2 w-0.5 -translate-x-1/2 rounded-full bg-[var(--border-primary)] opacity-0 transition-opacity group-hover:opacity-100" />
  </div>;
}

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
  const [rootForm, setRootForm] = useState(false);
  const [rootDraft, setRootDraft] = useState<Partial<RootSubmission> | undefined>();
  useEffect(() => { setRootForm(false); setRootDraft(undefined); }, [sessionId]);
  const [rootInstruction, setRootInstruction] = useState("");
  const [rootError, setRootError] = useState("");
  const [learningContext, setLearningContext] = useState<LearningTaskSnapshot | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState("");
  const [visionDraft, setVisionDraft] = useState<string | null>(null);
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
  const lifetime=useRef(new ChatLifetime());
  const viewGeneration=useRef(0);
  const alive=useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const activeRunRef = useRef<AgentRun | undefined>(undefined);

  const [webSearch, setWebSearch] = useState<WebSearchMode>("auto");
  useEffect(() => {
    const stored = window.localStorage.getItem("luojia_web_search_mode");
    if (stored === "auto" || stored === "on" || stored === "off") setWebSearch(stored);
  }, []);
  function changeWebSearch(value: WebSearchMode) {
    setWebSearch(value);
    window.localStorage.setItem("luojia_web_search_mode", value);
  }
  const [reasoningEffort, setReasoningEffort] = useState<ReasoningEffortLevel>("medium");
  const [isGlobalSearchOpen, setIsGlobalSearchOpen] = useState(false);

  // Ctrl+K 全局搜索快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsGlobalSearchOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

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
  const [isLearningCollapsed, setIsLearningCollapsed] = useState(false);
  const [isResizing, setIsResizing] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isStreaming, thinkingElapsed, autoScroll]);

  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
      setAutoScroll(isAtBottom);
    }
  };

  const reviewData = useMemo<ReviewData | null>(() => {
    if (!meta || meta.verified === false || meta.is_correct === null) return null;
    return {
      concepts: meta.concepts || [],
      is_correct: meta.is_correct,
      mistake: meta.mistake,
      mastery_score: meta.mastery_score ?? 0.5,
      mastery_label: meta.mastery_label ?? "一般",
      mastery_delta: meta.mastery_delta ?? 0,
      verification_kind: meta.verification_kind,
      verifier_summary: meta.verifier_summary,
      legacy_scope: !meta.step_check,
      mastery_estimate_notice: meta.mastery_estimate_notice,
      learning_update_eligible: meta.step_check?.eligible_learning_evidence,
    };
  }, [meta]);

  useEffect(() => {
    const timer = setTimeout(() => {
      listSessions("demo-user", searchQuery).then((data) => setSessions(data)).catch(() => {});
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    alive.current=true;
    const manager=lifetime.current,generation=viewGeneration;
    void bootstrap();
    const ownerChanged=()=>{viewGeneration.current++;lifetime.current.invalidate();setMessages([]);setLearningContext(null);setContextError("身份已变化，请刷新后继续。");setIsStreaming(false);};
    const storage=(event:StorageEvent)=>{if(event.key?.startsWith("luojia_auth_")||event.key===null)ownerChanged();};
    window.addEventListener("luojia-auth-change",ownerChanged);window.addEventListener("storage",storage);
    return()=>{alive.current=false;generation.current++;manager.invalidate();window.removeEventListener("luojia-auth-change",ownerChanged);window.removeEventListener("storage",storage);};
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
    const generation=++viewGeneration.current, owner=getCurrentUserId();
    const valid=()=>alive.current && generation===viewGeneration.current && owner===getCurrentUserId();
    setContextLoading(true);
    const existing=await listSessions().catch(()=>[]);
    if(!valid())return;
    setSessions(existing);
    const params=new URLSearchParams(window.location.search),labId=params.get("lab"),encodedRef=params.get("ref");
    if(labId||encodedRef){
      try{
        const step=params.get("step");
        const requested:LearningContextRef=labId?rootContextRef(await learningRequest<LabRun>(`/root-lab/runs/${encodeURIComponent(labId)}`,undefined,AbortSignal.timeout(15000)),step===null?null:Number(step)):JSON.parse(encodedRef!);
        const snapshot=await learningRequest<LearningTaskSnapshot>("/tutor/context",requested,AbortSignal.timeout(15000));
        if(!valid())return;
        const mapped=localStorage.getItem(referenceChatKey(owner,snapshot.ref));
        if(mapped&&existing.some(s=>s.id===mapped)) await selectSession(mapped,snapshot);
        else {resetToDraftSession();setLearningContext(snapshot);setContextLoading(false);}
      }catch(e){if(valid()){setContextError(e instanceof Error?e.message:"来源引用不可用");setContextLoading(false);}}
      return;
    }
    const selected=existing.find(s=>s.id===params.get("session"))??existing[0];
    if(selected)await selectSession(selected.id);else resetToDraftSession();
  }

  function resetToDraftSession() {
    viewGeneration.current++;lifetime.current.invalidate();setIsStreaming(false);setContextLoading(false);
    window.history.replaceState(null,"","/chat");
    setLearningContext(null); setContextError("");
    setVisionDraft(null);
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

  async function selectSession(nextSessionId: string, override?:LearningTaskSnapshot) {
    const generation=++viewGeneration.current,owner=getCurrentUserId();
    lifetime.current.invalidate();setIsStreaming(false);setContextLoading(true);
    const valid=()=>alive.current && generation===viewGeneration.current && owner===getCurrentUserId();
    setVisionDraft(null);
    setSessionId(nextSessionId);
    const [serverMessages, serverMistakes, savedNotes] = await Promise.all([
      listMessages(nextSessionId).catch(() => [] as Message[]),
      listMistakes(nextSessionId).catch(() => []),
      listNotes("demo-user").catch(() => []),
    ]);

    if(!valid())return;
    let currentMessages: LocalMessage[] = mapServerMessages(serverMessages);
    const lastMeta = serverMessages.at(-1)?.learning_meta;
    let snapshot=override??null, contextFailure="";
    if(!override&&lastMeta?.learning_context){
      try{snapshot=await learningRequest<LearningTaskSnapshot>("/tutor/context",lastMeta.learning_context.ref,AbortSignal.timeout(15000));}
      catch(e){contextFailure=e instanceof Error?e.message:"实验引用不可用";}
    }
    if(!valid())return;
    setLearningContext(snapshot);setContextError(contextFailure);setContextLoading(false);
    const query=new URLSearchParams({session:nextSessionId});
    if(snapshot){if(snapshot.ref.kind==="root_lab"&&!snapshot.ref.activity_claim){query.set("lab",snapshot.ref.record_id);if(snapshot.ref.selected_step!==null)query.set("step",String(snapshot.ref.selected_step));}else{query.set("ref",JSON.stringify(snapshot.ref));}localStorage.setItem(referenceChatKey(owner,snapshot.ref),nextSessionId);}
    window.history.replaceState(null,"",`/chat?${query}`);
    if (lastMeta?.awaiting_confirmation && lastMeta.vision_draft) setVisionDraft(lastMeta.vision_draft);
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

  async function handleSessionDeleted(deletedId: string) {
    // Re-fetch the session list, then decide whether to keep the current view.
    const refreshed = await listSessions("demo-user", searchQuery).catch(() => sessions);
    setSessions(refreshed);
    if (deletedId !== sessionId) {
      // Deleted a session that wasn't being viewed — nothing else to do.
      return;
    }
    // The active session was deleted: pick another, or fall back to a draft.
    const next = refreshed.find((s) => s.id !== deletedId);
    if (next) {
      await selectSession(next.id);
    } else {
      resetToDraftSession();
    }
  }

  async function submit(value: string, forcedMode?: TutorMode, requestedHint: boolean = false, imageUrls?: string[], rootSubmission?: RootSubmission, parentRunId?:string) {
    if (isStreaming || contextLoading || contextError) return;
    if (learningContext && (rootSubmission || imageUrls?.length)) {
      setRootError("请先移除实验引用，再发送自己的作答或图片。"); return;
    }
    const manager=lifetime.current,lease=manager.begin(getCurrentUserId());
    if(!lease)return;
    const valid=()=>alive.current && manager.current(lease,getCurrentUserId());
    abortControllerRef.current=lease.controller;
    setIsStreaming(true);setVisionDraft(null);
    const assistantId=crypto.randomUUID();
    let activeSession=sessionId;
    try {
      if(!activeSession){
        const created=await createSession("综合",lease.controller.signal);
        if(!valid())return;
        activeSession=created.session_id;setSessionId(activeSession);
      }
      if(learningContext)localStorage.setItem(referenceChatKey(getCurrentUserId(),learningContext.ref),activeSession);
      const userMessage:LocalMessage={id:crypto.randomUUID(),role:"user",content:value};
      setMessages(current=>[...current,userMessage,{id:assistantId,role:"assistant",content:"",status:"thinking"}]);
      setMeta(null);setThinkingChains({});setThinkingElapsed(0);activeRunRef.current=undefined;
      const isFirstUserMessage = messages.filter((m) => m.role === "user").length === 0;
      if (isFirstUserMessage && !studyRequested(value)) {
        generateTitle(value, getUserApiKey() || null, getPreferredModel() || null).then(async ({ title: autoTitle, label: autoLabel }) => {
          if(!valid())return;
          await renameSession(activeSession!, autoTitle, autoLabel).catch(() => {});
          listSessions("demo-user", searchQuery).then((s) => {if(valid())setSessions(s);}).catch(() => {});
        }).catch(() => {});
      }

      await streamTutor(
        {
          study_action: !learningContext && !rootSubmission && !imageUrls?.length && studyRequested(value)?"current_tasks":undefined,
          root_submission: rootSubmission,
          learning_context: learningContext?.ref,
          parent_run_id:parentRunId,
          session_id: activeSession,
          message: value,
          subject: "auto",
          mode: forcedMode || mode,
          user_api_key: !learningContext && studyRequested(value)?null:getUserApiKey() || null,
          model: !learningContext && studyRequested(value)?undefined:getPreferredModel(),
          requested_hint: requestedHint,
          image_urls: imageUrls,
          abortSignal: abortControllerRef.current.signal,
          web_search_mode: learningContext?"off":webSearch,
          reasoning_effort: reasoningEffort,
        },
        (nextMeta) => {
          if(!valid())return;
          setMeta(nextMeta);
          setMessages((current) => current.map((message) => message.id === assistantId ? { ...message, learningMeta: {...nextMeta,agent_run:mergeAgentRun(message.learningMeta?.agent_run,nextMeta.agent_run)} } : message));
        },
        (token) => {
          if(!valid())return;
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
          if(!valid())return;
          setThinkingChains((prev) => ({ ...prev, [assistantId]: chain }));
        },
        (content) => {
          if(!valid())return;
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
          if(!valid())return;
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
        },
        (draft) => {if(valid())setVisionDraft(draft);},
        (run) => { if(!valid())return; activeRunRef.current=run; setMessages(current=>current.map(message=>message.id===assistantId ? {
          ...message, learningMeta:{...(message.learningMeta || {intent:"pending",subject:"综合",concepts:[],verified:false,is_correct:null,mistake:null,verifier_summary:"本轮进行中"}),agent_run:mergeAgentRun(message.learningMeta?.agent_run,run)}
        }:message)); }
      );
      const [refreshedSessions, refreshedMistakes] = await Promise.all([
        listSessions().catch(() => sessions),
        listMistakes(activeSession).catch(() => mistakes)
      ]);
      if(!valid())return;
      setSessions(refreshedSessions);
      setMistakes(refreshedMistakes);
      const history = await listMessages(activeSession,lease.controller.signal);
      if(!valid())return;
      setMessages(mapServerMessages(history));
    } catch (error) {
      if(!valid())return;
      if(!activeSession)setRootError(error instanceof Error?error.message:"创建会话失败");
      const cancelled = abortControllerRef.current?.signal.aborted || (error instanceof Error && error.name === "AbortError");
      const failureText = cancelled ? "已停止生成，本轮没有收到完整回答。" : error instanceof Error ? error.message : "未知错误";
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId
            ? { ...message, content: `${message.content}\n\n本轮未完成：${failureText}`, learningMeta: {...message.learningMeta,intent:"generation_failed",subject:"综合",concepts:[],verified:false,is_correct:null,mistake:null,verifier_summary:"本轮未完成",error:message.learningMeta?.error || {code:cancelled ? "client_cancelled" : "stream_failed",message:failureText}} }
            : message
        )
      );
    } finally {
      if(!valid()){manager.finish(lease);return;}
      const run = activeRunRef.current as AgentRun | undefined;
      if (activeSession && run?.status === "running") {
        let saved=await getAgentRun(activeSession,run.run_id).catch(()=>undefined);
        if (saved?.status === "running") {
          // The disconnect listener may still be draining owned work. One
          // bounded recheck keeps the UI honest without waiting indefinitely.
          await new Promise(resolve=>setTimeout(resolve,150));
          saved=await getAgentRun(activeSession,run.run_id).catch(()=>undefined);
        }
        if (saved && valid()) setMessages(current=>current.map(message=>message.id===assistantId && message.learningMeta ? {
          ...message, learningMeta:{...message.learningMeta,agent_run:mergeAgentRun(message.learningMeta.agent_run,saved)}
        }:message));
      }
      if(!valid()){manager.finish(lease);return;}
      manager.finish(lease);
      setThinkingChains(current => { const next = {...current}; delete next[assistantId]; return next; });
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

  const rightPanelContent = <>
            <div className="flex items-center gap-2 p-2 border-b border-[var(--border-subtle)] shrink-0">
              <button
                onClick={() => setRightPanelMode("learning")}
                className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-colors ${rightPanelMode === "learning" ? "bg-[var(--bg-card)] shadow-sm text-[var(--text-accent)] border border-[var(--border-primary)]" : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"}`}
              >
                状态复盘
              </button>
              <button
                onClick={() => setRightPanelMode("note")}
                className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-colors ${rightPanelMode === "note" ? "bg-[var(--bg-card)] shadow-sm text-[var(--text-accent)] border border-[var(--border-primary)]" : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"}`}
              >
                随堂笔记
              </button>
              <button
                onClick={() => { setIsLearningCollapsed(true); setIsMobileLearningOpen(false); }}
                className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
                title="收起数理仪器面板"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex-1 overflow-hidden relative">
              {rightPanelMode === "learning" ? (
                <LearningPanel meta={meta} mistakes={mistakes} />
              ) : (
                <div className="absolute inset-0 flex flex-col bg-[var(--bg-card)]">
                  <div className="flex justify-between items-center p-3 border-b border-[var(--border-primary)] shrink-0">
                    <div className="flex items-center gap-1.5 font-bold text-[var(--text-primary)] text-sm">
                      <FileText className="w-4 h-4 text-[var(--text-accent)]" />
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
                        <Loader2 className="w-6 h-6 animate-spin text-[var(--text-accent)]" />
                        <p className="text-xs animate-pulse">正在提炼核心考点...</p>
                      </div>
                    ) : !noteContent ? (
                      <div className="h-full flex flex-col items-center justify-center space-y-4 text-[var(--text-muted)] text-center px-4">
                        <div className="w-16 h-16 rounded-full bg-[var(--accent-light)] flex items-center justify-center">
                          <FileText className="w-8 h-8 text-[var(--accent)] opacity-60" />
                        </div>
                        <div className="space-y-1">
                          <h3 className="font-bold text-[var(--text-primary)]">本次笔记</h3>
                          <p className="text-xs">复习完当前内容后，点击下方按钮，AI将为你提炼核心考点与易错陷阱。</p>
                        </div>
                        <button
                          onClick={handleGenerateNote}
                          disabled={!sessionId}
                          className="mt-4 flex items-center gap-2 px-6 py-2.5 text-sm font-bold bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white rounded-full shadow-lg shadow-[var(--accent-light)] transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100"
                        >
                          <Sparkles className="w-4 h-4" />
                          一键生成笔记
                        </button>
                      </div>
                    ) : (
                      <div className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed">
                        <LatexRenderer content={noteContent} complete={!isStreaming} />
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
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-bold bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white rounded-xl shadow-lg shadow-[var(--accent-light)] transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100"
                >
                  <FileText className="w-4 h-4" />
                  整理本次笔记
                </button>
              </div>
            )}
  </>;

  return (
    <div className="flex h-dvh flex-col bg-[var(--bg-primary)] transition-colors duration-300 overflow-hidden relative">
      <ZenOverlay isZenMode={isZenMode} />
      {isZenMode && (
        <Button
          variant="ghost"
          onClick={toggleZenMode}
          className="fixed top-6 left-6 z-50 text-white/50 hover:text-white hover:bg-white/10 transition-colors rounded-full px-4"
        >
          <Minimize className="w-4 h-4 mr-2" />
          退出全屏学习
        </Button>
      )}

      {!isZenMode && (
        <AppHeader
          onOpenSearch={() => setIsGlobalSearchOpen(true)}
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
              setIsMobileLearningOpen(false);
              setIsMobileSidebarOpen(!isMobileSidebarOpen);
            }
          }}
          onToggleLearning={() => {
            if (typeof window !== "undefined" && window.innerWidth >= 1280) {
              setIsLearningCollapsed(!isLearningCollapsed);
            } else {
              setIsMobileSidebarOpen(false);
              setIsMobileLearningOpen(!isMobileLearningOpen);
            }
          }}
          onToggleZenMode={() => {
            if (!isZenMode) setShowZenConfirm(true);
            else void toggleZenMode();
          }}
        />
      )}

      <div id="main-layout" className="flex min-h-0 flex-1 relative">
        {/* Mobile Sidebar Overlay */}
        {isMobileSidebarOpen && (
          <MobileDrawer title="历史会话" side="left" breakpoint={1024} onClose={() => setIsMobileSidebarOpen(false)}>
            <Sidebar sessions={sessions} activeSessionId={sessionId} onSelect={(id) => { void selectSession(id); setIsMobileSidebarOpen(false); }} onRefresh={() => listSessions("demo-user", searchQuery).then(setSessions).catch(() => {})} onDeleted={handleSessionDeleted} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          </MobileDrawer>
        )}

        {isMobileLearningOpen && (
          <MobileDrawer title="学习面板" side="right" breakpoint={1280} onClose={() => setIsMobileLearningOpen(false)}>
            <div className="flex h-full min-h-0 flex-col">{rightPanelContent}</div>
          </MobileDrawer>
        )}

        {!isZenMode && !isSidebarCollapsed && (
          <div className="group hidden shrink-0 flex-col lg:flex relative" style={{ width: sidebarWidth }}>
            <Sidebar sessions={sessions} activeSessionId={sessionId} onSelect={(id) => void selectSession(id)} onRefresh={() => listSessions("demo-user", searchQuery).then(setSessions).catch(() => {})} onDeleted={handleSessionDeleted} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
            <button
              onClick={() => handleToggleSidebar(true)}
              className="absolute -right-3 top-20 z-20 flex h-6 w-6 items-center justify-center rounded-full border border-[var(--border-primary)] bg-white dark:bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-[#617a55] hover:scale-110 transition-all shadow-sm opacity-0 group-hover:opacity-100"
              title="收起侧边栏"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
        {!isZenMode && !isSidebarCollapsed && <ResizeHandle onStart={setIsResizing} target="sidebar" className="hidden lg:block" />}

        {!isZenMode && isSidebarCollapsed && (
          <button
            onClick={() => handleToggleSidebar(false)}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-30 group hidden lg:flex h-20 w-4 items-center justify-center rounded-r-md border border-l-0 border-[var(--border-primary)] bg-white/80 dark:bg-[var(--bg-card)] backdrop-blur-sm text-[var(--text-muted)] hover:text-[#617a55] hover:w-5 transition-all shadow-sm"
            title="展开侧边栏"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
        <main className={`flex min-w-0 flex-1 flex-col ${isZenMode ? "px-4 sm:px-20 lg:px-40" : ""}`}>
          {(learningContext || contextError || contextLoading) && <div className="mx-auto w-full max-w-4xl px-4 pt-4">
            {learningContext && <ContextBanner snapshot={learningContext} disabled={isStreaming} onRemove={() => {lifetime.current.invalidate();setLearningContext(null); setContextError(""); window.history.replaceState(null, "", "/chat");}}/>}
            {contextLoading && <p role="status" className="p-3">正在核对实验引用…</p>}
            {contextError && <div role="alert" className="rounded-lg bg-cinnabar-500/5 p-4 leading-7"><p>{contextError}</p><button type="button" className="min-h-12 underline" onClick={() => {setLearningContext(null); setContextError(""); window.history.replaceState(null, "", "/chat");}}>移除失效引用，继续普通聊天</button></div>}
          </div>}
          <div
            className={`flex-1 overflow-y-auto ${isZenMode ? "scrollbar-hide" : ""}`}
            ref={scrollContainerRef}
            onScroll={handleScroll}
          >
            <div className="mx-auto max-w-4xl px-4 py-8 pb-32">
              {messages.length === 1 && messages[0].id === "welcome" && <TutorCompanion compact/>}

              {(() => {
                const lastAssistantIdx = messages.reduce((acc, m, i) =>
                  m.role === "assistant" && m.status !== "thinking" ? i : acc, -1);
                return messages.map((message, idx) => (
                  <MathMessage
                    learningMeta={message.learningMeta} messageId={message.id} learningContext={learningContext?.ref} actionsDisabled={isStreaming || contextLoading || !!contextError}
                    key={message.id}
                    role={message.role}
                    content={message.content}
                    status={message.role === "assistant" && message.status !== "thinking" ? messageStatus(message.learningMeta) : undefined}
                    isGenerating={isStreaming && idx === messages.length - 1 && message.role === "assistant"}
                    isThinking={message.status === "thinking" && isStreaming}
                    thinkingElapsed={thinkingElapsed}
                    thinkingChain={message.role === "assistant" ? (thinkingChains[message.id] || "") : ""}
                    webSearchReport={message.learningMeta?.web_search}
                    answerGuard={message.learningMeta?.answer_guard}
                    agentRun={message.learningMeta?.agent_run}
                    isIncomplete={!!message.learningMeta?.error}
                    rootDiagnosis={message.learningMeta?.root_diagnosis}
                    sessionId={sessionId || ""}
                    onRootRevision={(report: RootDiagnosis) => {setRootDraft({episode_id:report.episode_id,attempt_id:report.attempt_id,attempt:report.input});setRootInstruction(report.kind === "probe" ? "继续独立探针；首次提交后的修订不计为新的独立证据。" : "");setRootForm(true);}}
                    onRootProbe={async (report: RootDiagnosis) => {try {const probe=await startRootProbe(sessionId || "",report.episode_id);setRootDraft({episode_id:probe.episode_id,attempt:probe.challenge});setRootInstruction(probe.instruction);setRootForm(true);setRootError("");} catch(e) {setRootError(e instanceof Error ? e.message : "无法开启独立探针。");}}}
                    thinkingSummary={message.thinkingSummary}
                    thinkingElapsedMs={message.thinkingElapsedMs}
                    reviewData={idx === lastAssistantIdx && !isStreaming ? reviewData : null}
                    onEdit={message.role === "user" && !isStreaming ? async () => {
                      if (!sessionId || isStreaming) return;
                      const generation=viewGeneration.current,owner=getCurrentUserId();
                      await truncateSession(sessionId, message.id);
                      if(generation!==viewGeneration.current||owner!==getCurrentUserId())return;
                      setInputValue(message.content);
                      const msgs = await listMessages(sessionId);
                      if(generation!==viewGeneration.current||owner!==getCurrentUserId())return;
                      setMessages(mapServerMessages(msgs));
                      setMeta(latestLearningMeta(msgs));
                    } : undefined}
                    onRetry={message.role === "assistant" && !isStreaming ? async () => {
                      if (!sessionId || isStreaming) return;
                      const generation=viewGeneration.current,owner=getCurrentUserId();
                      let prevUserMsg = null;
                      for(let j=idx-1; j>=0; j--){
                        if(messages[j].role === "user"){ prevUserMsg = messages[j]; break;}
                      }
                      if(prevUserMsg) {
                        await truncateSession(sessionId, prevUserMsg.id);
                        const msgs = await listMessages(sessionId);
                        if(generation!==viewGeneration.current||owner!==getCurrentUserId())return;
                        setMessages(mapServerMessages(msgs));
                        setMeta(latestLearningMeta(msgs));
                        void submit(prevUserMsg.content,undefined,false,undefined,undefined,message.learningMeta?.agent_run?.run_id);
                      }
                    } : undefined}
                    onSimilar={() => {
                      const concept = message.learningMeta?.concepts?.[0];
                      void submit(`请围绕${concept ? `“${concept}”和` : ""}下面这段讲解出一道条件完整的类似练习题，先不要答案：\n\n${message.content.slice(0,2000)}`, "practice");
                    }}
                  />
                ));
              })()}
              {messages.length === 1 && messages[0].id === "welcome" && (
                <div className="mt-8 pt-6 border-t border-[var(--border-subtle)] animate-in fade-in slide-in-from-bottom-3 duration-500">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="w-1.5 h-4 rounded-full bg-olive-500" />
                    <span className="text-xs font-bold tracking-wider text-[var(--text-secondary)] uppercase">
                      从这些问题开始
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {(learningContext&&learningContext.ref.kind!=="root_lab"?[{category:"当前引用",icon:"↗",title:"解释当前来源",desc:"区分原文、条件与推断",prompt:"请只依据本轮引用解释必要条件与不能确定的结论。"}]:learningContext?[{category:"当前实验",icon:"xₖ",title:"解释迭代现象",desc:"从已保存的真实轨迹出发",prompt:"请解释这次实验的迭代现象，说明相关条件与局限。"},{category:"当前实验",icon:"x₀",title:"换一个初值",desc:"编辑参数后亲自预览",prompt:"我想改变初值做对照。请解释应该观察什么，然后让我调整参数预览。"}]:[{category:"今日学习",icon:"✓",title:"查看今日任务",desc:"读取已有计划，不自动创建",prompt:"今天学什么"},...PROMPT_SUGGESTIONS]).map((item, pIdx) => (
                      <button
                        key={pIdx}
                        onClick={() => void submit(item.prompt)}
                        className="group text-left p-3.5 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] hover:border-olive-500/40 hover:bg-olive-500/[0.03] transition-all duration-200 shadow-xs hover:shadow-card flex flex-col justify-between cursor-pointer"
                      >
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-olive-500/10 text-olive-700 dark:text-olive-300">
                            {item.category}
                          </span>
                          <span className="font-mono text-xs text-[var(--text-muted)] group-hover:text-olive-600 transition-colors">
                            {item.icon}
                          </span>
                        </div>
                        <h4 className="text-xs font-bold text-[var(--text-primary)] group-hover:text-olive-700 dark:group-hover:text-olive-300 transition-colors mb-1">
                          {item.title}
                        </h4>
                        <p className="text-[11px] text-[var(--text-secondary)] line-clamp-1">
                          {item.desc}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>
              )}
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
          <div className="shrink-0 p-3 sm:p-4 pb-[max(12px,env(safe-area-inset-bottom))] relative z-10 mx-auto w-full max-w-4xl">
            {visionDraft && !isStreaming && (
              <div className="mb-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-card)] p-3 text-sm">
                <p className="mb-2">请核对上方识别出的公式与条件，再继续解题。</p>
                <div className="flex gap-3">
                  <button type="button" className="text-[var(--text-accent)]" onClick={() => void submit(`图片题目已核对，请继续：\n${visionDraft}`)}>确认题目，继续</button>
                  <button type="button" onClick={() => { setInputValue(visionDraft); setVisionDraft(null); }}>编辑题目</button>
                </div>
              </div>
            )}
            <div className="mx-auto max-w-4xl px-4 flex flex-wrap gap-2 items-center">
              <button type="button" disabled={isStreaming} className="text-xs rounded border px-3 py-2" onClick={() => {setRootDraft(undefined);setRootInstruction("");setRootForm(!rootForm);}}>求根过程验证</button>
              {rootError && <span role="alert" className="text-xs text-cinnabar-600">{rootError}</span>}
            </div>
            {rootForm && <RootAttemptForm key={`${rootDraft?.episode_id || "new"}-${rootDraft?.attempt_id || "first"}`} initial={rootDraft} instruction={rootInstruction} disabled={isStreaming} onClose={()=>setRootForm(false)} onSubmit={submission => {setRootForm(false);void submit(`求根过程：${submission.attempt.function}\n\n\`\`\`root-attempt\n${JSON.stringify(submission, null, 2)}\n\`\`\``, mode, false, undefined, submission);}}/>}
            <TutorInput
              value={inputValue}
              onChange={setInputValue}
              disabled={isStreaming || contextLoading || !!contextError}
              mode={mode}
              onModeChange={setMode}
              webSearch={webSearch}
              onWebSearchChange={changeWebSearch}
              reasoningEffort={reasoningEffort}
              onReasoningEffortChange={setReasoningEffort}
              onSubmit={(val, forcedMode, images) => void submit(val, forcedMode, false, images)}
              onDirect={() => void submit("我需要完整的推导过程和最终答案。请直接告诉我怎么做，不要反问我。", "direct")}
              onHint={() => void submit("能不能给我一点提示？", "socratic")}
              onSimilar={() => void submit("出一道类似的题目给我练习。", "practice")}
            />
          </div>
        </main>

        {!isZenMode && !isLearningCollapsed && <ResizeHandle onStart={setIsResizing} target="learning" className="hidden xl:block" />}
        {!isZenMode && !isLearningCollapsed && (
          <div className="hidden shrink-0 flex-col xl:flex bg-[var(--bg-tertiary)] border-l border-[var(--border-subtle)]" style={{ width: learningWidth }}>
            {rightPanelContent}
          </div>
        )}

        {!isZenMode && isLearningCollapsed && (
          <button
            onClick={() => setIsLearningCollapsed(false)}
            className="hidden xl:flex absolute right-0 top-1/2 -translate-y-1/2 z-30 group h-20 w-4 items-center justify-center rounded-l-md border border-r-0 border-[var(--border-primary)] bg-white/80 dark:bg-[var(--bg-card)] backdrop-blur-sm text-[var(--text-muted)] hover:text-[#617a55] hover:w-5 transition-all shadow-sm"
            title="展开数理仪器与状态复盘"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
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
              <div className="w-12 h-12 rounded-full bg-[var(--accent-light)] flex items-center justify-center mb-4 text-[var(--text-accent)]">
                <Target className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2">进入全屏学习</h3>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-6">
                展开聊天区域，隐藏侧栏和学习面板。浏览器支持时会进入全屏。
                <br/><br/>
                可在右上角设置计时和背景音。
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
                  className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white rounded-full px-6 shadow-md transition-colors"
                >
                  确认进入
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      <div aria-hidden={!showNoteToast} role="status" className={`fixed top-4 left-1/2 -translate-x-1/2 z-[150] transition-all duration-300 ${showNoteToast ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-4 pointer-events-none"}`}>
        <div className="bg-emerald-500/10 backdrop-blur-md border border-emerald-500/20 text-emerald-500 font-bold px-4 py-2 rounded-full shadow-lg flex items-center gap-2 text-sm">
          <FileText className="w-4 h-4" />
          笔记已生成，可在学习面板查看。
        </div>
      </div>

      {/* 全局搜索抽屉 (Ctrl+K) */}
      <GlobalSearchModal
        isOpen={isGlobalSearchOpen}
        onClose={() => setIsGlobalSearchOpen(false)}
        onSelectResult={(text) => {
          setInputValue((prev) => (prev ? `${prev}\n${text}` : text));
        }}
      />
    </div>
  );
}
