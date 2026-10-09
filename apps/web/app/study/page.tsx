"use client";
import Link from "next/link";
import {useCallback, useEffect, useState} from "react";
import {LearningShell, Notice, learningButton, learningInput, learningPanel} from "@/components/learning/learning-shell";
import {learningRequest, parseTrace, stableRequestId, type StudyToday, type StudyTask, type LearningOverview} from "@/lib/learning-api";
import {getCurrentUserId} from "@/lib/demo-auth";
import {recommendationHref} from "@/lib/study-summary";
import type {LearningRecommendation} from "@/lib/learning-api";

const states: Record<string, string> = {planned: "待开始", in_progress: "进行中", awaiting_check: "反馈待确认", verified_complete: "独立检验通过", assisted_complete: "练习已完成", needs_revision: "需要修订", unknown: "尚不能确认", read_complete: "已读"};

function PendingTasks({tasks,busy,start}:{tasks:StudyTask[];busy:boolean;start:(id:string)=>void}){
  return tasks.length>0?<section className="mt-6 border-t border-[var(--border-subtle)] pt-5"><h3 className="font-semibold">其他未完成任务</h3><p className="mt-2 text-base sm:text-sm leading-7 text-[var(--text-secondary)]">包括此前开始的独立检验；刷新或跨日后仍可继续。</p><ul className="mt-3 space-y-3">{tasks.map(t=><li key={t.id}><button type="button" disabled={busy} onClick={()=>start(t.id)} className="min-h-12 text-left text-olive-700 dark:text-olive-300 underline">{t.title} · {states[t.state]??t.state}</button></li>)}</ul></section>:null;
}

export default function StudyPage() {
  const [today, setToday] = useState<StudyToday | null>(null);
  const [task, setTask] = useState<StudyTask | null>(null);
  const [trace, setTrace] = useState("");
  const [stop, setStop] = useState("residual");
  const [minutes, setMinutes] = useState(15);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [pending,setPending]=useState<StudyTask[]>([]);
  const [recommendation,setRecommendation]=useState<LearningRecommendation|null>(null);
  const reload = useCallback(async () => {
    const [value,overview]=await Promise.all([learningRequest<StudyToday>("/study/today"),learningRequest<LearningOverview>("/learning/overview")]);
    setToday(value);setPending(overview.pending_tasks.filter(t=>!value.plan?.tasks.some(p=>p.id===t.id)));setRecommendation(overview.recommendation);
  }, []);
  const openTask = useCallback((value: StudyTask) => {
    setTask(value);
    const key = `learning-trace:${getCurrentUserId()}:${value.id}`;
    setTrace(localStorage.getItem(key) ?? value.feedback?.input?.iterates?.join(",") ?? "");
    setStop(localStorage.getItem(`${key}:stop`) ?? value.feedback?.input?.stop_reason ?? "residual");
    window.history.replaceState(null,"",`/study?task=${encodeURIComponent(value.id)}`);
  },[]);
  useEffect(() => {
    reload().then(async()=>{
      const selected = new URLSearchParams(window.location.search).get("task");
      if (selected) openTask(await learningRequest<StudyTask>(`/study/tasks/${encodeURIComponent(selected)}`));
    }).catch(e=>setError(e.message));
  },[reload,openTask]);
  const act = async (action: () => Promise<void>) => {
    setBusy(true); setError("");
    try {await action(); await reload();} catch(e) {setError(e instanceof Error ? e.message : "请求失败");} finally {setBusy(false);}
  };
  const locked = busy || !!task && ["planned", "awaiting_check", "assisted_complete", "verified_complete"].includes(task.state);
  const start = (id: string) => act(async () => {openTask(await learningRequest<StudyTask>(`/study/tasks/${id}/start`, {}));});
  const recommendedTaskId=recommendation&&/^\/study\?task=([A-Za-z0-9_-]{1,80})$/.exec(recommendationHref(recommendation))?.[1];
  return <LearningShell title="今天，向前一步" description="从到期复习和过程修订开始。完成阅读后，提交自己的求根轨迹，再用新题检查理解。">
    <Notice error={error} />
    {!today ? <p role="status">{error ? "连接失败，可重新加载。" : "正在读取今日任务…"}</p> : <>
      {!today.persistent && <p className="mb-5 text-base sm:text-sm text-ochre-700 dark:text-ochre-300">当前为内存演示模式，服务重启会清空记录。设置 COURSE_STORE_PATH 后可持久保存。</p>}
      {recommendation&&<section aria-label="建议的下一步" className="mb-6 rounded-2xl border border-olive-500/25 bg-olive-500/5 p-5"><p className="text-xs font-medium tracking-wider text-olive-700 dark:text-olive-300">基于已保存状态 · 只读建议</p><h2 className="mt-2 font-title text-xl font-semibold">{recommendation.title}</h2><p className="mt-2 leading-7 text-[var(--text-secondary)]">{recommendation.reason}</p>{recommendedTaskId?<button type="button" disabled={busy} onClick={()=>act(async()=>openTask(await learningRequest<StudyTask>(`/study/tasks/${recommendedTaskId}`)))} className="mt-3 min-h-11 text-olive-700 underline underline-offset-4 dark:text-olive-300">打开原任务 →</button>:recommendationHref(recommendation)==="/study"?<a href="#study-content" className="mt-3 inline-flex min-h-11 items-center text-olive-700 underline underline-offset-4 dark:text-olive-300">在下方选择 →</a>:<Link href={recommendationHref(recommendation)} className="mt-3 inline-flex min-h-11 items-center text-olive-700 underline underline-offset-4 dark:text-olive-300">查看下一步 →</Link>}</section>}
      <div id="study-content"/>
      {!today.plan && !task ? <><div className={`${learningPanel} max-w-xl`}><h2 className="text-xl font-semibold">留一段时间给数值分析</h2><p className="my-4 text-base sm:text-sm text-[var(--text-secondary)]">最多安排三项任务，未完成的记录会保留。</p><label htmlFor="minutes" className="block mb-2">今日时长</label><select id="minutes" name="minutes" className={`${learningInput} mb-4`} value={minutes} onChange={e=>setMinutes(Number(e.target.value))}><option value={15}>15 分钟</option><option value={30}>30 分钟</option></select><button type="button" disabled={busy} className={learningButton} onClick={()=>act(async()=>setToday(await learningRequest<StudyToday>("/study/plans", {minutes})))}>生成今日任务</button></div><PendingTasks tasks={pending} busy={busy} start={start}/></> :
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
        <section><div className="mb-5 flex items-baseline justify-between"><h2 className="text-xl font-semibold">{today.local_date}</h2><span className="text-[var(--text-secondary)]">{today.plan ? `${today.plan.minutes} 分钟` : "此前任务"}</span></div>{today.plan?.stale && <p role="status" className="mb-4 text-cinnabar-700">课程版本已变化，旧任务保留供核对。</p>}
          <ol className="divide-y divide-[var(--border-subtle)]">{(today.plan?.tasks??[]).map(t=><li key={t.id} className="py-5"><div className="flex items-start justify-between gap-3"><h3 className="text-lg font-medium">{t.title}</h3><span className="shrink-0 text-base sm:text-sm text-olive-700 dark:text-olive-300">{states[t.state] ?? t.state}</span></div><p className="mt-2 mb-3 text-base sm:text-sm leading-6 text-[var(--text-secondary)]">{t.reason}</p><button type="button" disabled={busy} onClick={()=>start(t.id)} className="text-olive-700 dark:text-olive-300 underline underline-offset-4">{t.state === "planned" ? "开始任务" : "继续 / 回看"}</button></li>)}</ol>
          {today.reviews.length > 0 && <div className="mt-6 border-t border-[var(--border-subtle)] pt-5"><h3 className="font-semibold">后续复习</h3>{today.reviews.map(r=><p key={r.id} className="mt-2 text-base sm:text-sm text-[var(--text-secondary)]">{r.id === "NA_NEWTON" ? "牛顿法" : r.id} · {new Date(r.due_at).toLocaleDateString("zh-CN")} · 阶段 {Math.max(0,r.stage+1)}</p>)}</div>}
          <PendingTasks tasks={pending} busy={busy} start={start}/>
          {!today.plan && <button type="button" className="mt-5 min-h-12 text-olive-700 dark:text-olive-300 underline" onClick={()=>{setTask(null);window.history.replaceState(null,"","/study");}}>安排今天的新计划</button>}
        </section>
        <section className={`${learningPanel} min-w-0 self-start`}>
          {!task ? <><h2 className="text-xl font-semibold">从左侧选一项任务</h2><p className="mt-3 leading-7 text-[var(--text-secondary)]">阅读记录、参考实验、练习完成与独立检验会分别保存。</p><Link href="/reading" className="mt-6 inline-block text-olive-700 underline">先看看教材伴读</Link></> : <>
            <h2 className="text-xl font-semibold">{task.title}</h2>
            {task.state === "planned" && <button type="button" disabled={busy} className={`${learningButton} mt-4`} onClick={()=>start(task.id)}>开始这项任务</button>}
            {task.kind === "reading" ? <><p className="my-4 text-[var(--text-secondary)]">阅读课程摘录，核对适用条件，尝试条件辨析。</p><Link href={`/reading?unit=${task.unit_id}`} className="inline-block text-olive-700 dark:text-olive-300 underline">打开对应材料 →</Link><button type="button" disabled={busy || task.state === "read_complete"} className={`${learningButton} block mt-5`} onClick={()=>act(async()=>openTask(await learningRequest<StudyTask>(`/study/tasks/${task.id}/read-complete`,{})))}>标记已读</button></> : task.challenge && <>
              <p className="mt-4 break-words font-mono">f(x) = {task.challenge.function}</p><p className="mt-2 text-base sm:text-sm text-[var(--text-secondary)]">初值 {task.challenge.initial_value}；目标：{task.challenge.goal === "root_error" ? "根误差" : "残差"} ≤ {task.challenge.tolerance}</p>
              {task.challenge.interval && <p className="mt-2 text-base sm:text-sm text-[var(--text-secondary)]">核对区间 [{task.challenge.interval.join(", ")}]；轨迹至少含初值与一次更新。</p>}
              {task.state === "awaiting_check" && <p role="status" className="mt-4 leading-7 text-ochre-700 dark:text-ochre-300">本次反馈等待确认。先点击下方“已读反馈，保存结果”，再按反馈修订或换题。</p>}
              <form className="mt-5 space-y-4" onSubmit={e=>{e.preventDefault(); act(async()=>{const attempt={...task.challenge, iterates:parseTrace(trace), brackets:[], stop_reason:stop}; const request_id=stableRequestId(localStorage,`learning-request:${getCurrentUserId()}:${task.id}`,attempt,()=>crypto.randomUUID()); openTask(await learningRequest<StudyTask>(`/study/tasks/${task.id}/attempts`,{request_id,attempt}));});}}>
                <label className="block" htmlFor="trace">我的迭代值（包含初值）</label><textarea disabled={locked} id="trace" name="trace" className={`${learningInput} font-mono`} rows={5} placeholder="用逗号或换行分隔，填写自己算出的轨迹" value={trace} onChange={e=>{setTrace(e.target.value); localStorage.setItem(`learning-trace:${getCurrentUserId()}:${task.id}`,e.target.value);}} />
                <label className="block" htmlFor="stop">我的停止依据</label><select disabled={locked} id="stop" name="stop" className={learningInput} value={stop} onChange={e=>{setStop(e.target.value);localStorage.setItem(`learning-trace:${getCurrentUserId()}:${task.id}:stop`,e.target.value);}}><option value="residual">残差达到阈值</option><option value="step">相邻迭代差达到阈值</option><option value="exact">零残差</option><option value="iteration_limit">达到迭代上限</option><option value="none">尚未停止</option></select><button type="submit" disabled={locked} className={learningButton}>核对我的过程</button>
              </form>
              {task.feedback && <div className="mt-6 border-t border-[var(--border-subtle)] pt-5"><h3 className="font-semibold">过程反馈</h3><p className="mt-3 leading-7">{task.feedback.summary}</p>{task.feedback.next_probe && <p className="mt-2 leading-7 text-[var(--text-secondary)]">{task.feedback.next_probe}</p>}<p className="mt-3 text-olive-700 dark:text-olive-300">{states[task.state]}</p>
                {task.feedback.delivery === "pending" && <button type="button" disabled={busy} className={`${learningButton} mt-4`} onClick={()=>act(async()=>openTask(await learningRequest<StudyTask>(`/study/tasks/${task.id}/ack`,{attempt_id:task.feedback?.attempt_id,feedback_id:task.feedback?.feedback_id})))}>已读反馈，保存结果</button>}
                {["assisted_complete","verified_complete"].includes(task.state) && <button type="button" disabled={busy} className={`${learningButton} mt-4`} onClick={()=>act(async()=>openTask(await learningRequest<StudyTask>(`/study/tasks/${task.id}/probe`,{})))}>换一题独立检验</button>}
              </div>}
            </>}
          </>}
        </section>
      </div>}
    </>}
  </LearningShell>;
}
