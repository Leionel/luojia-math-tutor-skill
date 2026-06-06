"use client";

import type { TutorMode } from "@/lib/api";

const modes: Array<{ value: TutorMode; label: string; desc: string }> = [
  { value: "socratic", label: "引导模式", desc: "采用苏格拉底式提问，绝不直接给答案，而是一步步引导你自行推导，培养数学直觉与底层思维。" },
  { value: "direct", label: "直接讲解", desc: "拒绝谜语人，直接给出详尽、严谨的数学推导过程和最终答案，适合快速查漏补缺。" },
  { value: "practice", label: "练习模式", desc: "针对当前知识点，智能生成难度递进的相似练习题，辅助巩固所学概念。" }
];

export function ModeSwitcher({ value, onChange }: { value: TutorMode; onChange: (mode: TutorMode) => void }) {
  return (
    <div className="flex flex-wrap rounded-md border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-1 text-sm transition-all duration-300">
      {modes.map((mode) => (
        <div key={mode.value} className="relative group">
          <button
            className={`min-w-[72px] rounded px-2.5 py-1.5 text-center font-medium transition-all ${
              value === mode.value
                ? "bg-[var(--accent)] text-white shadow-sm"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
            }`}
            onClick={() => onChange(mode.value)}
          >
            {mode.label}
          </button>
          
          {/* HOVER TOOLTIP */}
          <div className="absolute left-1/2 -translate-x-1/2 top-full mt-3 w-56 opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 z-[100] translate-y-1 group-hover:translate-y-0">
            <div className="bg-white dark:bg-[#1e1e1b] border border-[#d6d0ba] dark:border-[#3e3f36] shadow-xl rounded-xl p-3 text-left">
              <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white dark:bg-[#1e1e1b] border-l border-t border-[#d6d0ba] dark:border-[#3e3f36] rotate-45"></div>
              <p className="font-bold text-[var(--text-primary)] text-xs mb-1 relative z-10">{mode.label}</p>
              <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed relative z-10">{mode.desc}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

