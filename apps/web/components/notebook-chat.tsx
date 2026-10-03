"use client";
import {TutorConversation} from "./tutor-conversation";
import {getCurrentUserId} from "@/lib/demo-auth";

export function NotebookChat({sessionId,subject}:{sessionId:string;subject:string}) {
  return <div className="h-full border-l border-[var(--border-subtle)] bg-[var(--bg-primary)]">
    <TutorConversation sessionId={sessionId} scope={`notebook-${sessionId}`} subject={subject}
      draftKey={`notebook-chat-draft:${getCurrentUserId()}:${sessionId}`} placeholder="围绕这篇笔记提问…"
      suggestions={[{label:"基于笔记练习",mode:"practice",message:"请基于当前笔记的核心考点，给我一道练习题。先出题，等我作答后再核对。"},
        {label:"解释模糊概念",message:"这篇笔记中的核心概念我还有点模糊，请解释含义和适用条件，并给一个直观例子。"}]}/>
  </div>;
}
