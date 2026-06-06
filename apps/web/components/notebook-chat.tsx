"use client";

import { useEffect, useRef, useState } from "react";
import { type Message, type TutorMode, listMessages, streamTutor } from "@/lib/api";
import { MathMessage } from "./math-message";
import { TutorInput } from "./tutor-input";
import { Loader2 } from "lucide-react";
import { getUserApiKey, getPreferredModel } from "@/lib/local-settings";

export function NotebookChat({ sessionId, subject }: { sessionId: string; subject: string }) {
  const [messages, setMessages] = useState<Array<Message & { status?: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLoading(true);
    listMessages(sessionId)
      .then(msgs => {
        setMessages(msgs);
        messagesEndRef.current?.scrollIntoView();
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  async function submit(value: string, mode: TutorMode = "socratic") {
    const userMsg = { id: crypto.randomUUID(), session_id: sessionId, role: "user" as const, content: value, created_at: new Date().toISOString() };
    const assistantId = crypto.randomUUID();
    
    setMessages(prev => [...prev, userMsg, { id: assistantId, session_id: sessionId, role: "assistant", content: "", status: "thinking", created_at: new Date().toISOString() }]);
    setIsStreaming(true);
    abortControllerRef.current = new AbortController();

    try {
      await streamTutor(
        {
          session_id: sessionId,
          message: value,
          subject: subject as any,
          mode,
          user_api_key: getUserApiKey() || null,
          model: getPreferredModel() || undefined,
          abortSignal: abortControllerRef.current.signal
        },
        () => {}, // ignore meta
        (text) => {
          setMessages(current => current.map(m => 
            m.id === assistantId 
              ? { ...m, content: m.content + text, status: "typing" }
              : m
          ));
        },
        () => {} // ignore thinking chain
      );
      
      setMessages(current => current.map(m => 
        m.id === assistantId ? { ...m, status: undefined } : m
      ));
    } catch (e: any) {
      if (e.name !== "AbortError") {
        setMessages(current => current.map(m => 
          m.id === assistantId ? { ...m, content: m.content + "\n\n[网络错误，请重试]", status: "error" } : m
        ));
      }
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <div className="flex flex-col h-full bg-[var(--bg-primary)] border-l border-[var(--border-subtle)]">
      <div className="flex-1 overflow-y-auto p-4 space-y-4 relative">
        {loading ? (
          <div className="flex justify-center items-center h-full text-[var(--text-muted)]">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center text-[var(--text-muted)] text-sm pt-10">
            暂无历史对话。在这里输入内容开启新的讨论！
          </div>
        ) : (
          messages.map(m => (
            <MathMessage key={m.id} content={m.content} role={m.role} isThinking={m.status === "thinking"} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-card)]">
        <div className="flex flex-wrap gap-2 mb-2">
           <button 
             disabled={isStreaming}
             onClick={() => submit("我已经阅读完这份随堂笔记。请基于笔记中的核心考点与易错陷阱，为我出一份包含 3 道题的针对性小测验（先出第一题，不要直接给答案，让我一步步来练习）。", "practice")}
             className="px-3 py-1.5 text-xs font-bold bg-[#617a55]/10 text-[#617a55] border border-[#617a55]/20 hover:bg-[#617a55]/20 rounded-md transition-colors"
           >
             基于笔记发起测验
           </button>
           <button 
             disabled={isStreaming}
             onClick={() => submit("这篇笔记中有几个概念我还有点模糊，能用生活中的例子再给我讲解一下吗？", "socratic")}
             className="px-3 py-1.5 text-xs font-bold bg-indigo-500/10 text-indigo-500 border border-indigo-500/20 hover:bg-indigo-500/20 rounded-md transition-colors"
           >
             请教模糊概念
           </button>
           {isStreaming && (
             <button
               onClick={() => abortControllerRef.current?.abort()}
               className="px-3 py-1.5 text-xs font-bold bg-rose-500 text-white rounded-md transition-colors"
             >
               停止生成
             </button>
           )}
        </div>
        <TutorInput 
          value={inputValue}
          onChange={setInputValue}
          onSubmit={val => {
            setInputValue("");
            submit(val);
          }}
          disabled={isStreaming}
          placeholder="围绕这篇笔记进行提问..."
        />
      </div>
    </div>
  );
}
