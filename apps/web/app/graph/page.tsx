"use client";

import Link from "next/link";
import { ArrowLeft, Network } from "lucide-react";
import { KnowledgeGraph } from "@/components/knowledge-graph";

export default function GraphPage() {
  return (
    <div className="flex flex-col h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden">
      <header className="flex-shrink-0 h-16 px-6 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md relative z-10">
        <div className="flex items-center gap-4">
          <Link 
            href="/chat"
            className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            返回对话
          </Link>
          <div className="h-4 w-px bg-slate-200 dark:bg-slate-800" />
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
            <Network className="w-5 h-5" />
            <h1 className="text-lg font-bold font-title tracking-widest">全局知识图谱 (Knowledge Network)</h1>
          </div>
        </div>
      </header>
      
      <main className="flex-1 relative bg-white dark:bg-black">
        {/* Full-screen graph, removing borders to make it immersive */}
        <KnowledgeGraph className="w-full h-full border-0 rounded-none bg-transparent" />
      </main>
    </div>
  );
}
