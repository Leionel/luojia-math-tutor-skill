"use client";
import Link from "next/link";
import {useState} from "react";
import {useRouter} from "next/navigation";
import {ArrowUp,BookOpen} from "lucide-react";
import {getCurrentUserId} from "@/lib/demo-auth";
import {storeChatEntry} from "@/lib/chat-entry";

export function HomeConversationEntry(){
  const [text,setText]=useState(""),[error,setError]=useState("");const router=useRouter();
  return <section aria-label="直接和小珞对话" className="mt-7 rounded-2xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-4 shadow-soft sm:p-5">
    <form onSubmit={event=>{event.preventDefault();try{if(!text.trim()){router.push("/chat?new=1");return;}const id=crypto.randomUUID();storeChatEntry(sessionStorage,getCurrentUserId(),id,text);router.push(`/chat?draft=${id}`);}catch{setError("浏览器暂时无法转交草稿，请复制问题后打开对话；输入仍保留。");}}}>
      <label htmlFor="home-question" className="text-sm font-medium">想和小珞聊什么？</label>
      <textarea id="home-question" maxLength={4000} value={text} onChange={e=>setText(e.target.value)} rows={3} placeholder="聊一个概念，检查一段推导，或从没想清楚的地方开始。" className="mt-3 w-full resize-y rounded-lg border-0 bg-transparent text-base leading-7 outline-none focus-visible:ring-2 focus-visible:ring-olive-600/40"/>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border-subtle)] pt-3"><Link href="/chat?new=1&workspace=reading" className="inline-flex min-h-11 items-center gap-2 text-sm text-dai-700 dark:text-dai-300 hover:underline"><BookOpen className="size-4"/>选材料一起读</Link><button type="submit" className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-olive-700 px-4 text-sm font-medium text-paper-50 hover:bg-olive-800">开始对话<ArrowUp className="size-4"/></button></div>
      <p className="mt-2 text-xs leading-6 text-[var(--text-muted)]">进入对话后再发送；材料、实验和练习都由你选择。</p>{error&&<p role="alert" className="mt-2 text-sm text-cinnabar-600">{error}</p>}
    </form>
  </section>;
}
