"use client";

import { useState } from "react";
import { Check, ChevronDown } from "lucide-react";

import type { TutorMode } from "@/lib/api";

const modes: Array<{ value: TutorMode; label: string; desc: string }> = [
  { value: "socratic", label: "引导模式", desc: "苏格拉底式提问，一步步引导你自行推导，不直接给答案。" },
  { value: "direct", label: "直接讲解", desc: "直接给出严谨的推导过程与最终答案，适合快速查漏补缺。" },
  { value: "practice", label: "练习模式", desc: "针对当前知识点生成难度递进的相似练习题，巩固所学。" },
];

export function ModeSwitcher({ value, onChange }: { value: TutorMode; onChange: (mode: TutorMode) => void }) {
  const [open, setOpen] = useState(false);
  const current = modes.find((m) => m.value === value) ?? modes[0];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 h-8 px-3 rounded-full border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] text-xs font-bold text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-primary)] transition-colors"
        title="切换助教模式"
      >
        {current.label}
        <ChevronDown className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute bottom-full right-0 mb-2 w-64 bg-[var(--bg-card)] border border-[var(--border-subtle)] shadow-xl rounded-xl p-1.5 z-50 flex flex-col gap-0.5 animate-in fade-in slide-in-from-bottom-2 duration-200">
            {modes.map((mode) => (
              <button
                key={mode.value}
                onClick={() => {
                  onChange(mode.value);
                  setOpen(false);
                }}
                className={`text-left px-3 py-2 rounded-lg transition-colors ${
                  mode.value === value
                    ? "bg-olive-500/10 text-olive-600 dark:text-olive-400"
                    : "hover:bg-[var(--bg-hover)] text-[var(--text-primary)]"
                }`}
              >
                <span className="flex items-center justify-between text-xs font-bold">
                  {mode.label}
                  {mode.value === value && <Check className="w-3.5 h-3.5" />}
                </span>
                <span className="block mt-0.5 text-[11px] leading-relaxed text-[var(--text-muted)]">
                  {mode.desc}
                </span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
