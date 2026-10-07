"use client";
import Link from "next/link";
import {BookOpen, X} from "lucide-react";
import {referenceDescription,referenceHref,type LearningTaskSnapshot} from "@/lib/learning-context";

export function ContextBanner({snapshot, onRemove, disabled=false}: {
  snapshot: LearningTaskSnapshot; onRemove?: () => void; disabled?: boolean;
}) {
  return <div className="flex min-w-0 items-start gap-3 rounded-xl border border-olive-500/20 bg-olive-500/5 p-4 text-[var(--text-primary)]">
    <BookOpen aria-hidden="true" className="mt-1 size-5 shrink-0 text-olive-600 dark:text-olive-300"/>
    <div className="min-w-0 flex-1">
      <p className="font-medium">正在讨论 · {snapshot.title}</p>
      <p className="mt-1 break-all font-mono text-sm leading-6">{referenceDescription(snapshot)}</p>
      <p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">参考帮助 · 不计掌握度{"omitted_rows" in snapshot && snapshot.omitted_rows > 0 ? ` · 引用 ${snapshot.rows.length}/${snapshot.total_rows} 步` : ""}</p>
      {"content_review_status" in snapshot && <p className="mt-1 text-xs">{snapshot.content_review_status==="development_card"?"开发条件卡，尚非教师金标":"上传来源内容未作数学核验"}</p>}
      {"task" in snapshot && <details className="mt-2 text-sm"><summary className="min-h-12 cursor-pointer py-3">查看引用中的矩阵与右端项</summary><pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all">{JSON.stringify({A:snapshot.task.matrix,b:snapshot.task.rhs,x0:snapshot.task.initial},null,2)}</pre></details>}
      {"citation" in snapshot && <details className="mt-2 text-sm"><summary className="min-h-12 cursor-pointer py-3">查看本轮完整选段</summary><pre className="max-h-48 overflow-auto whitespace-pre-wrap break-words">{snapshot.citation.quote}</pre></details>}
      <Link className="inline-flex min-h-12 items-center text-sm underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-olive-500" href={referenceHref(snapshot)}>回看原始来源</Link>
    </div>
    {onRemove && <button type="button" disabled={disabled} onClick={onRemove} aria-label="移除当前引用" className="flex size-12 shrink-0 items-center justify-center rounded-lg text-[var(--text-secondary)] hover:bg-olive-500/10 focus-visible:outline-2 focus-visible:outline-olive-500 disabled:opacity-50"><X aria-hidden="true" className="size-4"/></button>}
  </div>;
}
