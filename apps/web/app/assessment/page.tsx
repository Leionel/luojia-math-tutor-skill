"use client";
import Link from "next/link";
import {useCallback, useEffect, useState} from "react";
import {LearningShell, Notice, learningButton, learningPanel} from "@/components/learning/learning-shell";
import {learningRequest, type Assessment} from "@/lib/learning-api";
import {assessmentDraft} from "@/lib/learning-input";
import {getCurrentUserId} from "@/lib/demo-auth";

export default function AssessmentPage(){
  const [assessment,setAssessment]=useState<Assessment|null>(null);
  const [history,setHistory]=useState<Assessment[]>([]);
  const [draft,setDraft]=useState<Record<string,number>>({});
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const [loading,setLoading]=useState(true);
  const setCurrent=useCallback((value:Assessment|null)=>{
    setAssessment(value);
    const key=value?`assessment-draft:${getCurrentUserId()}:${value.id}`:null;
    const restored=value?.state==="in_progress"?assessmentDraft(localStorage.getItem(key!),value.questions,value.answers):{};
    setDraft(restored);
    if(key) {if(value?.state==="in_progress")localStorage.setItem(key,JSON.stringify(restored));else localStorage.removeItem(key);}
    window.history.replaceState(null,"",value?`/assessment?id=${encodeURIComponent(value.id)}`:"/assessment");
  },[]);
  const choose=(id:string,option:number)=>{
    const next={...draft,[id]:option};setDraft(next);
    if(assessment)localStorage.setItem(`assessment-draft:${getCurrentUserId()}:${assessment.id}`,JSON.stringify(next));
  };
  useEffect(()=>{learningRequest<{assessments:Assessment[]}>("/assessments").then(async a=>{setHistory(a.assessments);const id=new URLSearchParams(window.location.search).get("id");setCurrent(id?await learningRequest<Assessment>(`/assessments/${encodeURIComponent(id)}`):a.assessments.find(item=>item.state==="in_progress")??null);}).catch(e=>setError(e.message)).finally(()=>setLoading(false));},[setCurrent]);
  const act=async(action:()=>Promise<void>)=>{setBusy(true);setError("");try{await action();}catch(e){setError(e instanceof Error?e.message:"请求失败");}finally{setBusy(false);}};
  const completed=assessment?.state==="completed";
  const ended=assessment?.state==="abandoned";
  const closed=completed||ended;
  return <LearningShell title="检查这一章的理解" description="六道题，覆盖适用条件、一次更新和停止依据。首次有效作答会保存，交卷后查看参考解析与复习入口。">
    <Notice error={error}/>
    {loading?<p role="status">正在恢复测评记录…</p>:!assessment?<div className={`${learningPanel} max-w-2xl`}><h2 className="text-xl font-semibold">非线性方程求根 · 章节自检</h2><p className="my-4 leading-7 text-[var(--text-secondary)]">约 5–8 分钟。开发版参考题用于自查，不作为正式研究测验成绩，也不更新独立掌握状态。</p><button type="button" disabled={busy} className={learningButton} onClick={()=>act(async()=>{setCurrent(await learningRequest<Assessment>("/assessments",{}));setDraft({});})}>开始自检</button>{history.length>0 && <div className="mt-6 border-t border-[var(--border-subtle)] pt-4"><h3 className="mb-3 font-semibold">历史记录</h3>{history.map(a=><button type="button" key={a.id} disabled={busy} onClick={()=>{setCurrent(a);}} className="block py-2 text-olive-700 dark:text-olive-300 underline">{a.state==="completed"?`参考匹配 ${a.reference_matches}/${a.questions.length}`:a.state==="abandoned"?"已结束，不计分":"继续作答"} · {a.id.slice(0,8)}</button>)}</div>}</div>:<div className="max-w-3xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold">{completed?`参考计分 ${assessment.score?.percentage ?? Math.round(100*(assessment.reference_matches??0)/assessment.questions.length)} 分 · ${assessment.reference_matches} / ${assessment.questions.length}`:`已保存 ${Object.keys(assessment.answers).length} / ${assessment.questions.length}`}</h2><span className="text-base sm:text-sm text-[var(--text-secondary)]">{completed?"已交卷":ended?"已结束，不计分":"首次选择保存后不能覆盖"}</span></div>
      {completed && <p className="mb-6 leading-7 text-[var(--text-secondary)]">{assessment.review_units?.length ? `建议回看 ${assessment.review_units.length} 个知识点，解析下方可直接打开材料。后续今日计划会优先安排回顾。` : "这组参考题全部匹配。可以继续用新的求根轨迹检查过程理解。"} 参考计分用于章节练习，不作为正式研究测验成绩。</p>}
      {ended && <p className="mb-5 leading-7">作答记录已保留，本次未交卷，未生成参考分数。可以再开始一份自检。</p>}
      {!closed && <nav aria-label="自检答题导航" className="mb-6 rounded-xl bg-[var(--bg-tertiary)] p-4"><p className="mb-3 leading-7">选项草稿会在当前浏览器恢复；点击确认后才保存到作答记录。</p><div className="flex flex-wrap gap-3">{assessment.questions.map((q,i)=><a key={q.id} href={`#assessment-question-${q.id}`} className="min-h-11 rounded-lg border border-[var(--border-primary)] px-3 py-2 text-olive-700 dark:text-olive-300">{i+1} · {q.id in assessment.answers?"已确认":q.id in draft?"草稿":"未答"}</a>)}</div><progress className="mt-4 h-2 w-full accent-olive-600" aria-label="已确认题目进度" max={assessment.questions.length} value={Object.keys(assessment.answers).length}/></nav>}
      <ol className="space-y-6">{assessment.questions.map((q,index)=>{const selected=assessment.answers[q.id]??draft[q.id];const saved=q.id in assessment.answers;const feedback=assessment.feedback?.find(f=>f.id===q.id);return <li key={q.id} id={`assessment-question-${q.id}`} className={`${learningPanel} scroll-mt-24`}><fieldset disabled={saved||busy||closed}><legend className="mb-4 text-lg font-medium">{index+1}. {q.prompt}</legend><div className="space-y-3">{q.options.map((o,i)=><label key={o} className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 leading-7 ${selected===i?"border-olive-600 bg-olive-600/5":"border-[var(--border-subtle)]"}`}><input type="radio" name={q.id} value={i} checked={selected===i} onChange={()=>choose(q.id,i)} className="mt-1 h-5 w-5 shrink-0 accent-olive-600"/><span>{o}</span></label>)}</div></fieldset>
        {!closed && <button type="button" disabled={busy||saved||selected===undefined} className={`${learningButton} mt-4`} onClick={()=>act(async()=>setCurrent(await learningRequest<Assessment>(`/assessments/${assessment.id}/answers`,{question_id:q.id,option:selected})))}>{saved?"已保存":"确认本题作答"}</button>}
        {feedback && <div className="mt-5 border-t border-[var(--border-subtle)] pt-4"><p className="font-medium text-olive-700 dark:text-olive-300">{feedback.reference_match?"与参考判断一致":"建议再核对"}</p><p className="mt-2 leading-7">{feedback.explanation}</p><Link href={`/reading?unit=${feedback.unit_id}`} className="mt-3 inline-block text-olive-700 dark:text-olive-300 underline">回到对应条件 →</Link></div>}
      </li>;})}</ol>
      {!closed && <button type="button" disabled={busy} className="mt-6 text-[var(--text-secondary)] underline" onClick={()=>act(async()=>{const result=await learningRequest<Assessment>(`/assessments/${assessment.id}/end`,{});setCurrent(result);setHistory(previous=>[...previous.filter(a=>a.id!==result.id),result]);})}>结束本次自检，保留记录且不计分</button>}
      {!closed?<button type="button" disabled={busy||Object.keys(assessment.answers).length!==assessment.questions.length} className={`${learningButton} mt-7`} onClick={()=>act(async()=>{const result=await learningRequest<Assessment>(`/assessments/${assessment.id}/submit`,{});setCurrent(result);setHistory(previous=>[...previous.filter(a=>a.id!==result.id),result]);})}>交卷并查看参考解析</button>:<div className="mt-7 flex flex-wrap gap-5"><Link href="/study" className={learningButton}>回到今日学习</Link><button type="button" disabled={busy} className="text-olive-700 dark:text-olive-300 underline" onClick={()=>{setCurrent(null);setDraft({});}}>查看历史 / 再做一份</button></div>}
    </div>}
  </LearningShell>;
}
