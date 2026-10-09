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
      {"student_claim" in snapshot && snapshot.student_claim && <div className="mt-2 rounded-lg border border-olive-500/20 bg-[var(--bg-card)] p-3 text-sm"><p className="text-xs text-[var(--text-muted)]">学生选中的原话 · 尚未审核</p><p className="mt-1 whitespace-pre-wrap break-words leading-6">{snapshot.student_claim.text}</p></div>}
      {"condition" in snapshot && <div className="mt-2 rounded-lg border border-olive-500/20 bg-[var(--bg-card)] p-3 text-sm"><p className="font-medium">选中的条件：{snapshot.condition.condition}</p><p className="mt-2 whitespace-pre-wrap break-words leading-6">{snapshot.condition.student_quote??"尚未对应原句"}</p><p className="mt-2 text-xs text-[var(--text-muted)]">{snapshot.model_status==="model_review"?"模型意见未核验":"尚无可用模型意见"} · 不计掌握度</p></div>}
      {"content_review_status" in snapshot && <p className="mt-1 text-xs">{snapshot.content_review_status==="development_card"?"开发条件卡，尚非教师金标":"上传来源内容未作数学核验"}</p>}
      {"condition_review" in snapshot && snapshot.condition_review && <div className="mt-3 rounded-lg border border-olive-500/20 bg-[var(--bg-card)] p-3 text-sm"><p className="font-medium">题目条件对照 · 尚未经数学核验</p><p className="mt-2 whitespace-pre-wrap break-words">{snapshot.condition_review.problem_text}</p><ul className="mt-2 space-y-1">{snapshot.condition_review.conditions.map(row=><li key={row.index}>{row.status==="student_reported_known_unverified"?"我标记为已给出（未核验）":"尚不确定"}：{row.condition}</li>)}</ul><p className="mt-2 font-medium">下一问：{snapshot.condition_review.next_question}</p><p className="mt-1 text-xs text-[var(--text-muted)]">开发条件卡 · 不计掌握度</p></div>}
      {"task" in snapshot && snapshot.task.domain==="linear_system" && <details className="mt-2 text-sm"><summary className="min-h-12 cursor-pointer py-3">查看引用中的矩阵与右端项</summary><pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all">{JSON.stringify({A:snapshot.task.matrix,b:snapshot.task.rhs,x0:snapshot.task.initial},null,2)}</pre></details>}
      {"linear_check" in snapshot && <p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">第 {snapshot.linear_check.checked_step} 步已按保存的方法复算；残差是 ∥Ax−b∥∞，不等于解误差。{snapshot.linear_check.condition_sufficient?"本例满足严格行对角占优的充分条件；显示的理论误差界不含舍入误差。":"严格行对角占优未证，不能据此判定收敛或发散；解误差仍待其他依据。"}</p>}
      {"citation" in snapshot && <details className="mt-2 text-sm"><summary className="min-h-12 cursor-pointer py-3">查看本轮完整选段</summary><pre className="max-h-48 overflow-auto whitespace-pre-wrap break-words">{snapshot.citation.quote}</pre></details>}
      {"task" in snapshot && snapshot.task.domain==="integration" && <p className="mt-2 text-sm leading-6">误差估计依赖光滑性与渐近模型，可能漏掉振荡；求值次数是成本记录，估计不是严格误差界。</p>}
      {"code_excerpt" in snapshot&&<><p className="mt-2 text-sm">{snapshot.finding?.message??"本轮仅查看静态代码"} · 手动轨迹不是程序执行证据</p><details><summary className="min-h-12 cursor-pointer py-3">查看引用的已保存代码范围</summary><pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all">{snapshot.code_excerpt}</pre></details></>}
      <Link className="inline-flex min-h-12 items-center text-sm underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-olive-500" href={referenceHref(snapshot)}>回看原始来源</Link>
    </div>
    {onRemove && <button type="button" disabled={disabled} onClick={onRemove} aria-label="移除当前引用" className="flex size-12 shrink-0 items-center justify-center rounded-lg text-[var(--text-secondary)] hover:bg-olive-500/10 focus-visible:outline-2 focus-visible:outline-olive-500 disabled:opacity-50"><X aria-hidden="true" className="size-4"/></button>}
  </div>;
}
