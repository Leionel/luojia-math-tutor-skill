"use client";

import Link from "next/link";
import {useCallback, useEffect, useState} from "react";
import {ArrowRight, BookOpen, CalendarDays, FlaskConical, ClipboardCheck, MessageCircle, Code2} from "lucide-react";
import {motion, MotionConfig} from "framer-motion";
import {ThemeToggle} from "@/components/theme-toggle";
import {BrandLogo} from "@/components/brand-logo";
import {TutorCompanion} from "@/components/tutor-companion";
import {HomeRootIllustration} from "@/components/learning/home-root-illustration";
import {learningRequest, LearningRequestError, type LearningOverview} from "@/lib/learning-api";

const focus = "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-olive-600";
const features = [
  {href:"/study", title:"今日学习", description:"安排 15 或 30 分钟，从到期复习到自己的求根过程。", icon:CalendarDays, detail:"任务与复习"},
  {href:"/reading", title:"教材伴读", description:"带着适用条件读课程摘录，把问题与原文来源一起保存。", icon:BookOpen, detail:"材料与笔记"},
  {href:"/lab", title:"数值实验台", description:"从求根到线性方程组与积分，逐步观察并核对数值依据。", icon:FlaskConical, detail:"参数与轨迹"},
  {href:"/assessment", title:"章节自检", description:"用六道参考题检查条件理解，交卷后回看薄弱知识点。", icon:ClipboardCheck, detail:"参考评分与解析"},
  {href:"/teach-back", title:"讲给助教听", description:"用自己的话解释公式，逐项对照条件，再补充你的理解。", icon:MessageCircle, detail:"文字讲回首版"},
  {href:"/code-workshop", title:"数值代码作业", description:"审阅限定 Newton 作业，提交手动轨迹，比较修改前后。", icon:Code2, detail:"静态审阅 · 代码未执行"},
];
const unitNames: Record<string,string> = {NA_ROOT_FINDING:"残差与根误差",NA_BISECTION:"二分法",NA_NEWTON:"牛顿法",NA_FIXED_POINT:"不动点迭代"};

export default function HomePage() {
  const [overview,setOverview]=useState<LearningOverview|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const [loginRequired,setLoginRequired]=useState(false);
  const [refresh,setRefresh]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();
    let live=true;
    const timer=setTimeout(()=>controller.abort(),10000);
    learningRequest<LearningOverview>("/learning/overview",undefined,controller.signal).then(value=>{
      if(live){setOverview(value);setError("");setLoginRequired(false);}
    }).catch(e=>{
      if(live){setOverview(null);setLoginRequired(e instanceof LearningRequestError && e.status===401);setError(e instanceof LearningRequestError && e.status===401 ? "登录后查看属于你的任务与记录。" : "暂时无法读取学习记录，请重试。各学习入口仍可打开。");}
    }).finally(()=>{clearTimeout(timer);if(live)setLoading(false);});
    return()=>{live=false;clearTimeout(timer);controller.abort();};
  },[refresh]);
  const retry=useCallback(()=>{setLoading(true);setError("");setRefresh(value=>value+1);},[]);
  const next=overview?.next_task;
  const href=next?`/study?task=${encodeURIComponent(next.id)}`:overview?.active_assessment?`/assessment?id=${encodeURIComponent(overview.active_assessment.id)}`:"/study";
  const nextLabel=next?.state==="awaiting_check"?"确认过程反馈":next?.kind==="review"?"继续独立检验":next?"继续这项任务":overview?.active_assessment?"继续章节自检":overview?.plan?"查看今日任务":"安排今日学习";
  return <MotionConfig reducedMotion="user"><div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
    <a href="#home-content" className={`sr-only focus:not-sr-only focus:absolute focus:left-5 focus:top-2 focus:z-50 focus:bg-[var(--bg-card)] focus:p-3 ${focus}`}>跳到学习入口</a>
    <header className="border-b border-[var(--border-primary)]">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-5 py-4 sm:px-8 sm:py-5">
        <Link href="/" aria-label="珞珈数智首页" className={`flex min-h-12 items-center gap-3 font-title text-xl font-semibold ${focus}`}><BrandLogo className="h-12 w-12"/>珞珈数智</Link>
        <nav aria-label="首页导航" className="flex items-center gap-2 sm:gap-5">
          <Link href="/chat" className={`inline-flex min-h-12 items-center px-2 text-base sm:text-sm hover:text-olive-700 dark:hover:text-olive-300 ${focus}`}>对话助教</Link>
          {overview?.access_mode!=="account" && <Link href="/auth/login" className={`inline-flex min-h-12 items-center px-2 text-base sm:text-sm text-[var(--text-secondary)] ${focus}`}>登录</Link>}
          <div className="flex h-12 w-12 items-center justify-center [&_button]:h-12 [&_button]:w-12"><ThemeToggle/></div>
        </nav>
      </div>
    </header>
    <div id="home-content" className="mx-auto max-w-6xl px-5 pb-10 pt-10 sm:px-8 sm:pt-16">
      <motion.section initial={{y:16}} animate={{y:0}} transition={{duration:0.6,ease:[0.22,1,0.36,1]}} aria-labelledby="home-title" className="grid items-start gap-8 lg:grid-cols-[1.2fr_1fr] lg:gap-16">
        <div>
          <p className="mb-7 flex items-center gap-3 text-base sm:text-sm font-medium text-olive-700 dark:text-olive-300"><span className="h-px w-8 bg-olive-600" aria-hidden="true"/>数值分析 · 非线性方程求根</p>
          <h1 id="home-title" className="font-serif text-4xl font-medium leading-[1.45] tracking-tight sm:text-6xl sm:leading-[1.35] lg:text-[4rem]">把条件讲清，<br/>把过程算明。</h1>
          <p className="mt-7 max-w-[48ch] text-base leading-8 text-[var(--text-secondary)]">从今天的一项任务开始。读懂适用条件，提交自己的迭代过程，再用新题检查理解。</p>
          <p className="mt-5 text-base sm:text-xs tracking-wide text-[var(--text-muted)]">二分法 / 不动点迭代 / Newton 法</p>
        </div>
        <section aria-labelledby="next-step" aria-busy={loading} className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-6 sm:p-8 lg:mt-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2"><h2 id="next-step" className="text-lg font-semibold">接着上次，向前一步</h2><span className="text-base sm:text-sm text-[var(--text-muted)]">{overview?.local_date ?? "学习工作区"}</span></div>
          {loading?<p role="status" className="my-6 leading-7 text-[var(--text-secondary)]">正在读取你的学习记录…</p>:error?<div className="my-6"><p role={loginRequired?"status":"alert"} className="leading-7 text-[var(--text-secondary)]">{error}</p>{!loginRequired && <button type="button" onClick={retry} className={`mt-2 min-h-12 text-olive-700 dark:text-olive-300 underline ${focus}`}>重新读取记录</button>}</div>:<>
            <p className="mt-5 text-xl font-medium">{next?.title ?? (overview?.active_assessment?"还有一份章节自检未交卷":overview?.plan?.stale?"课程来源已更新，请核对旧任务":overview?.plan?"今日计划已完成，可回看过程":"给数值分析留一段时间")}</p>
            <p className="mt-2 leading-7 text-[var(--text-secondary)]">{next?.reason ?? (overview?.active_assessment?`已保存 ${overview.active_assessment.answered} / ${overview.active_assessment.total} 题，继续完成这次自检。`:"安排 15 或 30 分钟。阅读、练习与独立检验会分别记录。")}</p>
            {overview?.plan && <div className="mt-5"><div className="mb-2 flex justify-between text-base sm:text-sm"><span>今日计划 · {overview.plan.minutes} 分钟</span><span>{overview.plan.completed} / {overview.plan.total} 项完成</span></div><progress aria-label="今日计划完成项数" max={Math.max(1,overview.plan.total)} value={overview.plan.completed} className="h-2 w-full overflow-hidden rounded-full [&::-webkit-progress-bar]:bg-[var(--bg-tertiary)] [&::-webkit-progress-value]:bg-olive-600 [&::-moz-progress-bar]:bg-olive-600"/></div>}
          </>}
          <Link href={loginRequired?"/auth/login":href} className={`mt-6 inline-flex min-h-12 items-center gap-3 rounded-lg bg-olive-700 py-3 pl-4 pr-3 text-paper-50 hover:bg-olive-800 ${focus}`}>{loginRequired?"登录查看任务":nextLabel}<ArrowRight className="h-4 w-4" aria-hidden="true"/></Link>
          {overview?.access_mode==="demo" && <p className="mt-4 text-base sm:text-xs leading-6 text-[var(--text-muted)]">当前显示本地演示记录；登录后使用自己的学习记录。</p>}
        </section>
      </motion.section>
      <TutorCompanion/>
      <HomeRootIllustration/>
      {overview && <section aria-label="学习记录概览" className="mt-9 border-y border-[var(--border-primary)] py-5">
        <dl className="grid grid-cols-2 gap-x-8 gap-y-4 sm:grid-cols-4">
          {[["到期复习",overview.due_reviews,"项"],["阅读记录",overview.counts.reading,"项"],["练习完成",overview.counts.practice,"次"],["独立检验通过",overview.counts.independent,"次"]].map(([label,count,unit])=><div key={label}><dt className="text-base sm:text-sm text-[var(--text-secondary)]">{label}</dt><dd className="mt-1 text-2xl font-medium">{count}<span className="ml-2 text-base sm:text-sm font-normal text-[var(--text-muted)]">{unit}</span></dd></div>)}
        </dl>
        <p className="mt-3 text-base sm:text-xs leading-6 text-[var(--text-muted)]">以上为已保存的过程记录，不表示课程总体掌握度。{overview.stale_tasks>0?`另有 ${overview.stale_tasks} 项旧课程版本任务待核对。`:""}</p>
      </section>}
      <section aria-labelledby="learning-entries" className="mt-12">
        <div className="mb-5 flex flex-wrap items-baseline justify-between gap-3"><h2 id="learning-entries" className="font-title text-2xl font-semibold">选择今天的学习方式</h2><p className="text-base sm:text-sm text-[var(--text-secondary)]">读材料 → 做过程 → 讲清楚 → 再检查</p></div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{features.map(({href,title,description,icon:Icon,detail})=><Link key={href} href={href} className={`group flex flex-col rounded-xl border border-[var(--border-primary)] p-5 transition-[transform,background-color,border-color] duration-200 hover:-translate-y-1 hover:border-olive-600 hover:bg-olive-600/5 motion-reduce:transform-none motion-reduce:transition-none ${focus}`}>
          <div className="flex items-center justify-between"><Icon className="h-5 w-5 text-olive-700 dark:text-olive-300" aria-hidden="true"/><ArrowRight className="h-4 w-4 text-[var(--text-muted)] transition-transform group-hover:translate-x-1 group-hover:text-olive-600 motion-reduce:transform-none" aria-hidden="true"/></div><h3 className="mt-4 font-serif text-xl font-semibold">{title}</h3><p className="mt-2 flex-1 text-base sm:text-sm leading-7 text-[var(--text-secondary)]">{description}</p><p className="mt-4 text-base sm:text-xs text-olive-700 dark:text-olive-300">{detail}</p>
        </Link>)}</div>
      </section>
      {overview?.latest_assessment && <section aria-label="最近章节自检" className="mt-8 border-l-2 border-olive-600 pl-5"><h2 className="font-semibold">最近一次章节自检 · 参考 {overview.latest_assessment.score.percentage} 分</h2><p className="mt-2 text-base sm:text-sm leading-7 text-[var(--text-secondary)]">{overview.latest_assessment.review_units.length?"建议回看：":"这组参考题全部匹配，可继续核对自己的求根过程。"}{overview.latest_assessment.review_units.map((id,i)=><span key={id}>{i>0?"、":""}<Link href={`/reading?unit=${encodeURIComponent(id)}`} className={`text-olive-700 dark:text-olive-300 underline ${focus}`}>{unitNames[id] ?? id}</Link></span>)} 参考分数用于训练自查。</p><Link href={`/assessment?id=${encodeURIComponent(overview.latest_assessment.id)}`} className={`mt-2 inline-flex min-h-12 items-center text-olive-700 dark:text-olive-300 underline ${focus}`}>查看本次解析 →</Link></section>}
      <section aria-label="其他学习工具" className="mt-10 border-t border-[var(--border-primary)] pt-6"><h2 className="text-lg font-semibold">已有工具，也在这里</h2><nav aria-label="其他工具" className="mt-2 flex flex-wrap gap-x-6">{[["/chat","对话助教"],["/mistake-book","错题本"],["/notebook","随堂笔记"],["/graph","知识图谱"]].map(([href,label])=><Link key={href} href={href} className={`inline-flex min-h-12 items-center text-base sm:text-sm text-[var(--text-secondary)] hover:text-olive-700 dark:hover:text-olive-300 ${focus}`}>{label} ↗</Link>)}</nav></section>
      <footer className="mt-8 text-base sm:text-xs text-[var(--text-muted)]">珞珈数智助教 · 以条件和过程为线索，留下可回看的理解。</footer>
    </div>
  </div></MotionConfig>;
}
