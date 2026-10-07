"use client";
import Link from "next/link";
import {useState} from "react";
import {learningRequest} from "@/lib/learning-api";
import {studyTaskHref,type StudySummary} from "@/lib/study-summary";
const states:Record<string,string>={planned:"待开始",in_progress:"进行中",awaiting_check:"待确认反馈",needs_revision:"待修订",unknown:"结果待核对",read_complete:"阅读完成",assisted_complete:"受助完成",verified_complete:"训练独立完成",missing:"记录已不可用",session_unavailable:"原会话已不可用"};
export function StudyResumeCard({summary}: {summary:StudySummary}){
 const [fresh,setFresh]=useState<StudySummary>(),[error,setError]=useState(""),[busy,setBusy]=useState(false);const value=fresh??summary;
 return <section aria-label="已保存的今日任务" className="my-4 rounded-xl border border-olive-500/25 bg-[var(--bg-card)] p-4">
  <h3 className="font-semibold">{value.local_date} · 已保存任务</h3><p className="mt-2 text-sm leading-6">{value.help_locked?"检验期间只显示任务入口，请回工作区作答。":value.plan_exists?"状态来自服务端记录；打开入口不会自动完成任务。":"今天还没有计划。"}</p>
  <ul className="mt-3 space-y-3">{value.tasks.map(t=><li key={t.id} className="rounded-lg border border-[var(--border-subtle)] p-3"><p>{t.title}</p><p className="mt-1 text-sm text-[var(--text-secondary)]">{t.stale?"课程版本已变化，请先核对任务":states[t.state]??"状态待核对"}</p>{studyTaskHref(t)&&<Link className="inline-flex min-h-12 items-center underline" href={studyTaskHref(t)!}>回到这项任务 →</Link>}</li>)}</ul>
  {value.omitted_tasks>0&&<p className="mt-2 text-sm">另有 {value.omitted_tasks} 项，请到今日学习查看。</p>}
  <div className="mt-3 flex flex-wrap gap-4"><Link className="inline-flex min-h-12 items-center underline" href="/study">{value.plan_exists?"打开今日学习":"安排今日学习"}</Link><button type="button" disabled={busy} className="min-h-12 underline" onClick={async()=>{setBusy(true);setError("");try{setFresh(await learningRequest<StudySummary>("/tutor/study"));}catch{setError("任务读取失败，仍显示此前记录。");}finally{setBusy(false);}}}>{busy?"正在读取…":"重新读取状态"}</button></div>
  <p className="mt-2 text-xs text-[var(--text-muted)]">{fresh?"最新读取":"本轮读取时"}的状态 · <time dateTime={value.read_at}>{value.read_at}</time> · 不计掌握或独立成绩</p>{error&&<p role="alert">{error}</p>}
 </section>;
}
