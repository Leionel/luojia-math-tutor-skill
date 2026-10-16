"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {BookOpen,RotateCcw} from "lucide-react";
import {LearningShell,learningButtonSecondary,learningInput} from "@/components/learning/learning-shell";
import {learningRequest,type ReadingNote,type LabRun,type Assessment} from "@/lib/learning-api";
import {documentNoteSource} from "@/lib/document-note-source";
import {listNotes,listUserMistakes} from "@/lib/api";
import {getCurrentUserId,getAuthHeaders,isAuthStorageKey} from "@/lib/demo-auth";
import type {NumericalRun} from "@/lib/numerical-lab";

type Entry={id:string;kind:string;title:string;text:string;source:string;href:string;date:string|null;label:string};
const sourceNames=["随堂笔记","材料笔记","错因记录","求根实验","线性与积分实验","章节自检"];
export default function RecordsPage(){
  const [items,setItems]=useState<Entry[]>([]),[failures,setFailures]=useState<string[]>([]),[loading,setLoading]=useState(true),[retry,setRetry]=useState(0);
  const [filter,setFilter]=useState("全部"),[query,setQuery]=useState("");
  useEffect(()=>{const changed=()=>{setItems([]);setFailures([]);setLoading(true);setRetry(n=>n+1);};const storage=(e:StorageEvent)=>{if(isAuthStorageKey(e.key))changed();};window.addEventListener("luojia-auth-change",changed);window.addEventListener("storage",storage);return()=>{window.removeEventListener("luojia-auth-change",changed);window.removeEventListener("storage",storage);};},[]);
  useEffect(()=>{let active=true;const controller=new AbortController(),owner=getCurrentUserId(),credential=getAuthHeaders().Authorization;setLoading(true);setItems([]);setFailures([]);
    const valid=()=>active&&owner===getCurrentUserId()&&credential===getAuthHeaders().Authorization;
    const jobs:Promise<Entry[]>[]=[
      listNotes(owner).then(rows=>rows.map(n=>({id:`note:${n.id}`,kind:"随堂笔记",title:`${n.subject||"数学"} · 随堂笔记`,text:documentNoteSource(n).content,source:n.session_id?`对话 ${n.session_id}`:"个人笔记",href:n.session_id?.startsWith("document:")?`/notebook?note=${encodeURIComponent(n.id)}`:n.session_id?`/chat?session=${encodeURIComponent(n.session_id)}`:"/notebook",date:n.created_at||null,label:"学习笔记"}))),
      learningRequest<{notes:ReadingNote[]}>("/reading/notes",undefined,controller.signal).then(({notes})=>notes.map(n=>({id:`reading:${n.id}`,kind:"材料笔记",title:"阅读时留下的理解与问题",text:n.content,source:n.source_id,href:n.section_id==null?`/reading?unit=${encodeURIComponent(n.source_id)}`:`/reading?document=${encodeURIComponent(n.source_id)}&section=${encodeURIComponent(n.section_id)}`,date:n.created_at||null,label:"参考阅读记录"}))),
      listUserMistakes(owner).then(rows=>rows.map((m,i)=>({id:`mistake:${m.created_at}:${i}`,kind:"错因记录",title:m.concept||m.mistake_code,text:m.mistake_code,source:m.subject,href:"/mistake-book",date:m.created_at||null,label:"错因线索，回原记录核对"}))),
      learningRequest<{runs:(LabRun&{created_at?:string})[]}>("/root-lab/runs",undefined,controller.signal).then(({runs})=>runs.map(r=>({id:`root:${r.id}`,kind:"求根实验",title:`${r.parameters.method} · ${r.parameters.function}`,text:r.prediction||r.stop_detail,source:`${r.id} · ${r.runner_version}`,href:`/lab?id=${encodeURIComponent(r.id)}`,date:r.created_at||null,label:"参考计算，不计独立完成"}))),
      learningRequest<{runs:(NumericalRun&{created_at?:string})[]}>("/numerical-lab/runs",undefined,controller.signal).then(({runs})=>runs.map(r=>({id:`numerical:${r.id}`,kind:"线性与积分实验",title:r.task.domain==="linear_system"?"线性方程组实验":"数值积分实验",text:r.prediction||"回看保存的参数与轨迹",source:`${r.id} · ${r.schema_version}`,href:`/numerical-lab?id=${encodeURIComponent(r.id)}`,date:r.created_at||null,label:"参考计算，不计独立完成"}))),
      learningRequest<{assessments:(Assessment&{created_at?:string})[]}>("/assessments",undefined,controller.signal).then(({assessments})=>assessments.map(a=>({id:`assessment:${a.id}`,kind:"章节自检",title:a.state==="submitted"?"章节自检回看":"继续章节自检",text:a.score?`与参考答案匹配 ${a.score.correct}/${a.score.total} 题`:a.state==="in_progress"?"当前状态：进行中":"当前状态：待核对",source:a.id,href:`/assessment?id=${encodeURIComponent(a.id)}`,date:a.created_at||null,label:"参考自检，帮助状态见原任务"}))),
    ];
    void Promise.allSettled(jobs).then(results=>{if(!valid())return;setItems(results.flatMap(r=>r.status==="fulfilled"?r.value:[]).sort((a,b)=>(b.date?Date.parse(b.date)||0:0)-(a.date?Date.parse(a.date)||0:0)));setFailures(results.flatMap((r,i)=>r.status==="rejected"?[`${sourceNames[i]}：${r.reason instanceof Error?r.reason.message:"暂时无法读取"}`]:[]));setLoading(false);});
    return()=>{active=false;controller.abort();};
  },[retry]);
  const visible=items.filter(x=>(filter==="全部"||filter===x.kind)&&(!query||`${x.title} ${x.text} ${x.source}`.includes(query)));
  return <LearningShell title="我的学习记录" description="回看自己的提问、材料笔记、错因与实验，从原始来源继续学习。" wide>
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3"><div className="flex flex-wrap gap-2">{["全部",...sourceNames].map(kind=><button type="button" key={kind} aria-pressed={filter===kind} onClick={()=>setFilter(kind)} className={`min-h-11 rounded-lg border px-3 text-sm ${filter===kind?"border-olive-500/50 bg-olive-600/10 text-olive-800 dark:text-olive-200":"border-[var(--border-primary)]"}`}>{kind}</button>)}</div><label className="w-full sm:w-72"><span className="sr-only">查找学习记录</span><input aria-label="查找学习记录" value={query} onChange={e=>setQuery(e.target.value)} className={learningInput} placeholder="查找知识点、问题或原话"/></label></div>
    {!!failures.length&&<div role="status" className="mb-5 rounded-xl border border-ochre-600/30 bg-ochre-500/5 p-4 text-sm"><p>以下记录尚未读取，不能据此判断为空；独立检验期间部分参考实验可能暂不可读。</p><details className="mt-2"><summary className="min-h-11 cursor-pointer py-3">{failures.length} 类记录尚未读取 · 查看原因</summary><ul className="space-y-1">{failures.map(x=><li key={x}>{x}</li>)}</ul></details><button type="button" onClick={()=>setRetry(n=>n+1)} className={`${learningButtonSecondary} mt-3`}><RotateCcw className="size-4"/>重试读取</button></div>}
    {loading?<p role="status" className="py-12 text-center">正在读取当前账号的学习记录…</p>:visible.length?<div className="grid gap-4 md:grid-cols-2">{visible.map(item=><article key={item.id} className="min-w-0 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-5"><div className="flex items-center gap-2 text-xs text-[var(--text-muted)]"><BookOpen className="size-4"/>{item.kind}{item.date&&<time dateTime={item.date} className="ml-auto">{new Date(item.date).toLocaleDateString("zh-CN")}</time>}</div><h2 className="mt-3 break-words font-serif text-xl">{item.title}</h2><p className="mt-3 line-clamp-4 whitespace-pre-wrap break-words text-sm leading-7 text-[var(--text-secondary)]">{item.text}</p><details className="mt-4 text-xs text-[var(--text-muted)]"><summary className="min-h-11 cursor-pointer py-3">来源详情</summary><p className="break-all">{item.source}</p></details><p className="mt-2 text-xs leading-6 text-dai-700 dark:text-dai-300">{item.label}</p><Link href={item.href} className="mt-3 inline-flex min-h-11 items-center text-sm text-olive-700 dark:text-olive-300 underline">回到原始记录继续 →</Link></article>)}</div>:<section className="rounded-xl border border-[var(--border-primary)] p-8 text-center"><h2 className="font-serif text-xl">{items.length?"没有匹配的记录":"这里还没有读取到学习记录"}</h2><p className="mt-3 text-sm text-[var(--text-secondary)]">可以从一个问题开始，也可以带材料来读。</p><Link href="/chat?new=1" className={`${learningButtonSecondary} mt-5`}>和小珞聊聊</Link></section>}
    <p className="mt-6 text-xs leading-6 text-[var(--text-muted)]">按原记录中可用的时间排序；未记录时间的项放在后面。此页聚合现有记录，不把参考学习或参考分数认定为独立掌握。</p>
  </LearningShell>;
}
