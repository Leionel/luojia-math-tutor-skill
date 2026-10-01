"use client";

import { useState } from "react";
import { Check, ChevronDown, Sparkles, BookOpen, Target } from "lucide-react";
import type { TutorMode } from "@/lib/api";

const modes: Array<{ value: TutorMode; label: string; desc: string; icon: typeof Sparkles }> = [
  { value: "socratic", label: "引导模式", desc: "苏格拉底式提问，一步步引导你自行推导，不直接给答案。", icon: Sparkles },
  { value: "direct", label: "直接讲解", desc: "直接给出严谨的推导过程与最终答案，适合快速查漏补缺。", icon: BookOpen },
  { value: "practice", label: "练习模式", desc: "针对当前知识点生成难度递进的相似练习题，巩固所学。", icon: Target },
];

export function ModeSwitcher({ value, onChange }: { value: TutorMode; onChange: (mode: TutorMode) => void }) {
  const [open, setOpen] = useState(false);
  const current = modes.find((m) => m.value === value) ?? modes[0];
  const Icon = current.icon;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 h-7 sm:h-7.5 px-2.5 sm:px-3 rounded-full border border-[var(--border-subtle)] bg-[var(--bg-card)]/90 hover:bg-[var(--bg-hover)] text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-primary)] transition-all shadow-xs group shrink-0"
        title="切换助教教学模式"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-olive-500 animate-pulse" />
        <Icon className="w-3.5 h-3.5 text-olive-600 dark:text-olive-400" />
        <span>{current.label}</span>
        <ChevronDown className={`w-3 h-3 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute bottom-full right-0 mb-2 w-72 bg-[var(--bg-card)]/95 backdrop-blur-xl border border-[var(--border-subtle)] shadow-xl rounded-2xl p-2 z-50 flex flex-col gap-1 animate-in fade-in slide-in-from-bottom-2 duration-200">
            <div className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] font-mono border-b border-[var(--border-subtle)] pb-1.5 mb-0.5">
              教学交互模式选择
            </div>
            {modes.map((mode) => {
              const ItemIcon = mode.icon;
              const isSelected = mode.value === value;
              return (
                <button
                  key={mode.value}
                  onClick={() => {
                    onChange(mode.value);
                    setOpen(false);
                  }}
                  className={`text-left px-3 py-2.5 rounded-xl transition-all flex items-start gap-2.5 ${
                    isSelected
                      ? "bg-olive-500/10 text-olive-700 dark:text-olive-300 border border-olive-500/20 shadow-xs"
                      : "hover:bg-[var(--bg-hover)] text-[var(--text-primary)] border border-transparent"
                  }`}
                >
                  <div className={`p-1.5 rounded-lg mt-0.5 shrink-0 ${isSelected ? "bg-olive-500/20 text-olive-700 dark:text-olive-300" : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"}`}>
                    <ItemIcon className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="flex items-center justify-between text-xs font-bold">
                      {mode.label}
                      {isSelected && <Check className="w-3.5 h-3.5 text-olive-600 dark:text-olive-400" />}
                    </span>
                    <span className="block mt-0.5 text-[11px] leading-relaxed text-[var(--text-muted)] line-clamp-2">
                      {mode.desc}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
