"use client";
import {useEffect, useRef, useState} from "react";
import {createSession, getAgentRun, listMessages, streamTutor, type Message, type TutorMeta, type TutorMode} from "./api";
import {mergeAgentRun, type AgentRun} from "./agent-run";
import {ChatLifetime} from "./chat-lifetime";
import {getCurrentUserId} from "./demo-auth";
import {getPreferredModel, getUserApiKey} from "./local-settings";
import type {LearningContextRef} from "./learning-context";

export type ConversationMessage = Message & {status?: "thinking" | "typing" | "error"; thinkingChain?: string};
const pendingMeta: TutorMeta = {intent:"pending", subject:"数值分析", concepts:[], verified:false, is_correct:null, mistake:null, verifier_summary:"本轮进行中"};

/** Shared by notebook and embedded lab; full chat uses the same lifetime and renderer. */
export function useTutorConversation({sessionId, scope, subject, context, onSession}: {
  sessionId?: string; scope: string; subject: string; context?: LearningContextRef; onSession?: (id: string) => void;
}) {
  const lifetime = useRef(new ChatLifetime());
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [activeSession, setActiveSession] = useState(sessionId);
  const activeSessionRef = useRef(sessionId);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const owner = getCurrentUserId();
    const manager = lifetime.current; manager.invalidate();
    const lease = manager.begin(owner)!;
    const valid = () => manager.current(lease, getCurrentUserId()) && !lease.controller.signal.aborted;
    setLoading(true); setBusy(false); setError(""); setMessages([]);
    activeSessionRef.current = sessionId; setActiveSession(sessionId);
    if (sessionId) listMessages(sessionId, lease.controller.signal).then(next => {if (valid()) setMessages(next);})
      .catch(e => {if (valid()) setError(e.message);}).finally(() => {if (valid()) setLoading(false); manager.finish(lease);});
    else {setLoading(false); manager.finish(lease);}
    const authChanged = () => {manager.invalidate(); activeSessionRef.current=undefined; setMessages([]); setError("身份已变化，请刷新后继续。"); setBusy(false);};
    const storageChanged = (event: StorageEvent) => {if (event.key?.startsWith("luojia_auth_") || event.key === null) authChanged();};
    window.addEventListener("luojia-auth-change", authChanged); window.addEventListener("storage", storageChanged);
    return () => {manager.invalidate(); window.removeEventListener("luojia-auth-change", authChanged); window.removeEventListener("storage", storageChanged);};
  }, [sessionId, scope]);

  async function submit(value: string, mode: TutorMode = "socratic") {
    if (loading || error || !value.trim()) return false;
    const manager=lifetime.current, lease=manager.begin(getCurrentUserId());
    if (!lease) return false;
    const valid = () => manager.current(lease, getCurrentUserId());
    setBusy(true); setError("");
    const assistantId = crypto.randomUUID(); let session=activeSessionRef.current;
    let lastRun: AgentRun | undefined;
    const update = (change: (m: ConversationMessage) => ConversationMessage) => {
      if (valid()) setMessages(items=>items.map(m=>m.id===assistantId?change(m):m));
    };
    try {
      if (!session) {
        const created=await createSession(subject, lease.controller.signal);
        if (!valid() || lease.controller.signal.aborted) return false;
        session=created.session_id; activeSessionRef.current=session; setActiveSession(session); onSession?.(session);
      }
      if (!valid()) return false;
      const base={session_id:session, created_at:new Date().toISOString()};
      setMessages(items=>[...items, {...base,id:crypto.randomUUID(),role:"user",content:value},
        {...base,id:assistantId,role:"assistant",content:"",status:"thinking"}]);
      await streamTutor({session_id:session, message:value, subject, mode, learning_context:context,
        web_search_mode:context?"off":"auto", user_api_key:getUserApiKey()||null, model:getPreferredModel(), abortSignal:lease.controller.signal},
        meta=>update(m=>({...m,learning_meta:{...meta,agent_run:mergeAgentRun(m.learning_meta?.agent_run,meta.agent_run)}})),
        token=>update(m=>({...m,content:m.content+token,status:"typing"})),
        chain=>update(m=>({...m,thinkingChain:chain})),
        text=>update(m=>({...m,content:m.content+text})),
        ({summary,elapsedMs})=>update(m=>({...m,thinking_summary:summary,thinking_elapsed_ms:elapsedMs})), undefined,
        run=>{lastRun=run;update(m=>({...m,learning_meta:{...(m.learning_meta??pendingMeta),agent_run:mergeAgentRun(m.learning_meta?.agent_run,run)}}));});
      const history=await listMessages(session, lease.controller.signal);
      if (valid()) setMessages(history);
      return true;
    } catch (e) {
      if (!valid()) return false;
      const cancelled=lease.controller.signal.aborted;
      const detail=cancelled?"本轮已停止，回答尚未完成。":e instanceof Error?e.message:"连接失败";
      update(m=>({...m,status:"error",content:m.content+`\n\n本轮未完成：${detail}`,
        learning_meta:{...(m.learning_meta??pendingMeta),error:{code:cancelled?"client_cancelled":"stream_failed",message:detail}}}));
      // Failed lazy creation has no message bubble: keep a recoverable error visible.
      if (!session) setError(detail);
      return false;
    } finally {
      if (valid() && session && lastRun?.status === "running") {
        const saved=await getAgentRun(session,lastRun.run_id).catch(()=>undefined);
        if (saved) update(m=>({...m,learning_meta:{...(m.learning_meta??pendingMeta),agent_run:mergeAgentRun(m.learning_meta?.agent_run,saved)}}));
      }
      if (valid()) {setBusy(false); update(m=>({...m,status:m.status==="error"?"error":undefined}));}
      manager.finish(lease);
    }
  }
  return {messages, sessionId:activeSession, loading, busy, error, submit,
    cancel:()=>lifetime.current.cancel(), clearError:()=>setError("")};
}
