"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Network, BookOpen, Layers, Sparkles } from "lucide-react";
import { KnowledgeGraph } from "@/components/knowledge-graph";

export default function GraphPage() {
  const [courseId, setCourseId] = useState("numerical_analysis");
  const [scopeFilter, setScopeFilter] = useState<string | undefined>(undefined);

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
            <h1 className="text-lg font-bold font-title tracking-wider">课程知识图谱 2.0 (Course Graph)</h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Course select */}
          <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300">
            <BookOpen className="w-3.5 h-3.5 text-indigo-500" />
            <span>《数值分析》求根单元</span>
          </div>

          {/* Scope Filters */}
          <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
            {[
              { label: "全部", value: undefined },
              { label: "核心 (Core)", value: "core" },
              { label: "前置 (Prereq)", value: "prerequisite" },
              { label: "拓展 (Extension)", value: "extension" },
            ].map((btn) => (
              <button
                key={btn.label}
                onClick={() => setScopeFilter(btn.value)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  scopeFilter === btn.value
                    ? "bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>
      </header>
      
      <main className="flex-1 relative bg-white dark:bg-black">
        {/* Full-screen graph, removing borders to make it immersive */}
        <KnowledgeGraph 
          courseId={courseId}
          scopeFilter={scopeFilter}
          className="w-full h-full border-0 rounded-none bg-transparent" 
        />
      </main>
    </div>
  );
}
