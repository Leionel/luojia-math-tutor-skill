"use client";

import { useState, useEffect } from "react";
import type { TutorMeta } from "@/lib/api";
import { fetchMastery } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Brain, Target, CheckCircle2, XCircle, ChevronUp, ChevronDown, Lightbulb, AlertCircle, History, Sparkles, BarChart2 } from "lucide-react";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";

const intentMap: Record<string, string> = {
  "concept": "概念讲解",
  "solve_step_by_step": "分步引导",
  "check_student_step": "步骤检查",
  "full_solution": "完整解答",
  "generate_exercise": "生成练习",
};

export function LearningPanel({ meta, mistakes }: { meta: TutorMeta | null; mistakes: Array<{ mistake_code: string; concept: string }> }) {
  const [open, setOpen] = useState(false);
  const [overallMastery, setOverallMastery] = useState<Array<{subject: string; A: number; fullMark: number}>>([]);
  const concepts = meta?.concepts?.length ? meta.concepts : ["等待输入题目"];

  useEffect(() => {
    fetchMastery("demo-user").then(setOverallMastery).catch(console.error);
  }, [meta]);

  const content = (
    <div className="flex flex-col gap-6 w-full max-w-full">
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-[11px] font-bold tracking-widest uppercase text-[var(--text-muted)]">
          <Target className="w-3.5 h-3.5 text-[var(--accent)]" /> 当前考点 (Concepts)
        </h2>
        <div className="flex flex-wrap gap-2">
          {concepts.slice(0, 5).map((concept) => (
            <div key={concept} className="rounded-full border border-[var(--border-subtle)] bg-[var(--bg-card)] px-3 py-1 text-[12px] font-medium text-[var(--text-secondary)] shadow-sm">
              {concept}
            </div>
          ))}
        </div>
      </section>
      
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-[11px] font-bold tracking-widest uppercase text-[var(--text-muted)]">
          <Brain className="w-3.5 h-3.5 text-emerald-500" /> 状态与复盘 (Status)
        </h2>
        <div className={cn(
          "space-y-3 rounded-2xl border p-4 shadow-sm backdrop-blur-xl transition-all duration-500 relative overflow-hidden",
          meta?.is_correct 
            ? "border-emerald-500/30 bg-emerald-500/5 shadow-[0_0_15px_rgba(16,185,129,0.1)]" 
            : "border-[var(--border-primary)] bg-[var(--bg-card)]"
        )}>
          {meta?.is_correct && <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-emerald-400 to-teal-400" />}
          
          <div className="flex justify-between items-center text-[13px]">
            <span className="text-[var(--text-muted)]">意图识别</span>
            <span className="font-semibold text-[var(--text-primary)]">
              {meta ? (intentMap[meta.intent] || meta.intent) : "尚未开始"}
            </span>
          </div>
          
          <div className="flex justify-between items-center text-[13px]">
            <span className="text-[var(--text-muted)]">后台验算</span>
            <div className="flex items-center gap-1.5 font-semibold">
              {meta?.verified ? (
                meta.is_correct ? (
                  <span className="flex items-center gap-1 text-emerald-500"><CheckCircle2 className="w-4 h-4" /> 正确</span>
                ) : (
                  <span className="flex items-center gap-1 text-rose-500"><XCircle className="w-4 h-4" /> 发现偏差</span>
                )
              ) : (
                <span className="text-[var(--text-muted)]">等待输入</span>
              )}
            </div>
          </div>
          
          {meta?.mistake && (
            <div className="mt-2 rounded-lg bg-rose-500/10 p-3 text-xs text-rose-500 border border-rose-500/20 flex items-start gap-2 backdrop-blur-md">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span className="font-medium">{meta.mistake}</span>
            </div>
          )}
          
          {meta?.mastery_score !== undefined && (
            <div className="mt-3 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-widest">掌握度 (Mastery)</span>
                <span className="font-bold text-[var(--text-primary)] text-sm">
                  {Math.round(meta.mastery_score * 100)}% <span className="text-[11px] font-medium opacity-60">({meta.mastery_label})</span>
                </span>
              </div>
              
              {meta.mastery_delta !== undefined && meta.mastery_delta !== 0 && (
                <div className={cn(
                  "flex items-center gap-0.5 px-2 py-1 rounded-md text-xs font-bold border",
                  meta.mastery_delta > 0 
                    ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" 
                    : "bg-rose-500/10 text-rose-500 border-rose-500/20"
                )}>
                  {meta.mastery_delta > 0 ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  {Math.abs(Math.round(meta.mastery_delta * 100))}%
                </div>
              )}
            </div>
          )}
          
          {meta?.hint_level !== undefined && meta.hint_level > 0 && (
            <div className="mt-2 flex items-center gap-1.5 text-[11px] font-medium text-amber-500 border border-amber-500/20 px-2.5 py-1.5 w-fit backdrop-blur-md">
              <Lightbulb className="w-3.5 h-3.5" />
              系统已介入提示 (Level {meta.hint_level})
            </div>
          )}
        </div>
      </section>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-[11px] font-bold tracking-widest uppercase text-[var(--text-muted)]">
          <BarChart2 className="w-3.5 h-3.5 text-[var(--accent)]" /> 全局掌握度 (Overall Mastery)
        </h2>
        <div className="flex flex-col gap-3 border border-[var(--border-subtle)] bg-[var(--bg-card)] p-4 rounded-xl min-h-[250px] items-center justify-center relative overflow-hidden">
          {overallMastery.length === 0 ? (
            <div className="text-[12px] text-[var(--text-muted)] italic">暂无记录</div>
          ) : (
            <div className="w-full h-full min-h-[220px] -m-4">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="65%" data={overallMastery}>
                  <PolarGrid stroke="var(--border-subtle)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-secondary)', fontSize: 11, fontFamily: 'var(--font-body)' }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar name="Mastery" dataKey="A" stroke="#617a55" fill="#617a55" fillOpacity={0.6} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </section>
      
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-[11px] font-bold tracking-widest uppercase text-[var(--text-muted)]">
          <History className="w-3.5 h-3.5 text-[var(--text-muted)]" /> 最近错因 (Mistakes)
        </h2>
        <div className="space-y-2">
          {mistakes.length ? mistakes.slice(0, 5).map((mistake, index) => (
            <div key={`${mistake.mistake_code}-${index}`} className="flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2.5 text-[12px] font-medium text-amber-600 dark:text-amber-500 backdrop-blur-sm">
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
              {mistake.concept || mistake.mistake_code}
            </div>
          )) : <div className="text-[12px] text-[var(--text-muted)] italic px-2">暂无错因记录，继续保持！</div>}
        </div>
      </section>
      
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-[11px] font-bold tracking-widest uppercase text-[var(--text-muted)]">
          <Sparkles className="w-3.5 h-3.5 text-[var(--accent)]" /> 下一步建议 (Next Steps)
        </h2>
        <div className={cn(
          "rounded-xl p-4 text-[13px] leading-relaxed shadow-sm border backdrop-blur-xl",
          meta?.verified && meta.is_correct 
            ? "bg-[var(--accent-light)] border-[var(--accent)] text-[var(--accent)] font-medium"
            : "bg-[var(--bg-card)] border-[var(--border-primary)] text-[var(--text-secondary)]"
        )}>
          {meta?.verified 
            ? (meta.is_correct 
                ? "回答正确！您的掌握度正在提升。建议您点击底部「生成类似题」趁热打铁，或直接输入新题目开启新一轮练习。" 
                : "发现了一些逻辑上的漏洞，不要气馁。请根据对话框里的提示先修正这一处错误；如果卡壳了，可随时点击底部「请求提示」。") 
            : "您可以输入一道需要解答的题目，或者写下您目前的思考与推导步骤，系统将实时进行演算。"}
        </div>
      </section>
    </div>
  );

  return (
    <>
      <button
        className="fixed right-4 bottom-24 z-40 flex items-center justify-center gap-2 rounded-full border border-[var(--border-primary)] bg-[var(--bg-secondary)] backdrop-blur-md px-4 py-2.5 text-sm font-medium text-[var(--text-primary)] shadow-lg xl:hidden transition-colors"
        onClick={() => setOpen((v) => !v)}
      >
        <Brain className="w-4 h-4 text-brand" />
        学习面板
      </button>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/20 backdrop-blur-sm xl:hidden transition-opacity"
          onClick={() => setOpen(false)}
        />
      )}
      <aside
        className={cn(
          "fixed right-0 top-16 z-40 h-[calc(100vh-4rem)] w-80 sm:w-80 shrink-0 border-l border-[var(--border-primary)] bg-gray-50 dark:bg-[var(--bg-sidebar)] dark:backdrop-blur-3xl p-6 overflow-y-auto transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] xl:static xl:w-full xl:translate-x-0",
          open ? "translate-x-0 shadow-2xl" : "translate-x-full"
        )}
      >
        {content}
      </aside>
    </>
  );
}

