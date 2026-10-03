"use client";
import Link from "next/link";
import {BookOpen, X} from "lucide-react";
import type {LearningTaskSnapshot} from "@/lib/learning-context";

export function ContextBanner({snapshot, onRemove, disabled=false}: {
  snapshot: LearningTaskSnapshot; onRemove?: () => void; disabled?: boolean;
}) {
  return <div className="flex min-w-0 items-start gap-3 rounded-xl border border-olive-500/20 bg-olive-500/5 p-4 text-[var(--text-primary)]">
    <BookOpen aria-hidden="true" className="mt-1 size-5 shrink-0 text-olive-600 dark:text-olive-300"/>
    <div className="min-w-0 flex-1">
      <p className="font-medium">正在讨论 · {snapshot.title}{snapshot.ref.selected_step !== null ? ` · 第 ${snapshot.ref.selected_step} 步` : ""}</p>
      <p className="mt-1 break-all font-mono text-sm leading-6">f(x) = {snapshot.parameters.function} · x₀ = {snapshot.parameters.initial_value}</p>
      <p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">参考帮助 · 不计掌握度{snapshot.omitted_rows > 0 ? ` · 引用 ${snapshot.rows.length}/${snapshot.total_rows} 步` : ""}</p>
      <Link className="inline-flex min-h-12 items-center text-sm underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-olive-500" href={`/lab?id=${encodeURIComponent(snapshot.ref.record_id)}`}>回看完整实验</Link>
    </div>
    {onRemove && <button type="button" disabled={disabled} onClick={onRemove} aria-label="移除当前实验引用" className="flex size-12 shrink-0 items-center justify-center rounded-lg text-[var(--text-secondary)] hover:bg-olive-500/10 focus-visible:outline-2 focus-visible:outline-olive-500 disabled:opacity-50"><X aria-hidden="true" className="size-4"/></button>}
  </div>;
}
