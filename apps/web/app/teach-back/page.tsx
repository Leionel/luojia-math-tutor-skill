"use client";
import Link from "next/link";
import {useEffect, useState} from "react";
import {MathMarkdown} from "@/components/math-view";
import {TeachBackEvidence} from "@/components/learning/teachback-evidence";
import {LearningShell, Notice, learningInput, learningButton, learningPanel} from "@/components/learning/learning-shell";
import {learningRequest, stableRequestId, type ReadingUnit, type TeachBack} from "@/lib/learning-api";
import {getCurrentUserId} from "@/lib/demo-auth";

function evidenceDraft(key:string, fallback:Record<number,string>):Record<number,string>{
  try{const value=JSON.parse(localStorage.getItem(`${key}:evidence`)??"null");return value && typeof value==="object" && !Array.isArray(value) && Object.values(value).every(v=>typeof v==="string")?value:fallback;}catch{return fallback;}
}

export default function TeachBackPage(){
  const [units,setUnits]=useState<ReadingUnit[]>([]);
  const [selected,setSelected]=useState("NA_NEWTON");
  const [text,setText]=useState("");
  const [evidence,setEvidence]=useState<Record<number,string>>({});
  const [result,setResult]=useState<TeachBack|null>(null);
  const [history,setHistory]=useState<TeachBack[]>([]);
  const [focusedCondition,setFocusedCondition]=useState<string|null>(null);
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const [loading,setLoading]=useState(true);
  const unit=units.find(u=>u.id===selected);
  const draftKey=`teach-back-draft:${getCurrentUserId()}:${selected}:${result?.id??"new"}`;
  const restore=(r:TeachBack,conditionId:string|null=null)=>{const key=`teach-back-draft:${getCurrentUserId()}:${r.unit_id}:${r.id}`;setResult(r);setSelected(r.unit_id);setFocusedCondition(conditionId&&r.conditions.some(c=>c.condition_id===conditionId)?conditionId:null);setText(localStorage.getItem(key)??r.text);setEvidence(evidenceDraft(key,Object.fromEntries(r.conditions.map((c,i)=>[i,c.student_quote??""]))));window.history.replaceState(null,"",`/teach-back?id=${encodeURIComponent(r.id)}${conditionId&&r.conditions.some(c=>c.condition_id===conditionId)?`&condition=${encodeURIComponent(conditionId)}`:""}`);};
  useEffect(()=>{
    const params=new URLSearchParams(window.location.search);
    const unitId=params.get("unit")??"NA_NEWTON";
    setFocusedCondition(params.get("condition"));
    setSelected(unitId);
    const key=`teach-back-draft:${getCurrentUserId()}:${unitId}:new`;
    setText(localStorage.getItem(key)??"");setEvidence(evidenceDraft(key,{}));
    Promise.all([learningRequest<{units:ReadingUnit[]}>("/reading/units"),learningRequest<{submissions:TeachBack[]}>("/teach-back/submissions")]).then(async([a,b])=>{
      setUnits(a.units);setHistory(b.submissions);
      if(params.get("id")) restore(await learningRequest<TeachBack>(`/teach-back/submissions/${encodeURIComponent(params.get("id")!)}`),params.get("condition"));
    }).catch(e=>setError(e.message)).finally(()=>setLoading(false));
  },[]);
  return <LearningShell title="这一次，你来解释" description="用自己的话讲清公式为什么可用、为什么停止。把原句与条件对应起来，再补上遗漏的理解。">
    <Notice error={error}/>
    {loading?<p role="status">正在恢复讲回记录…</p>:<div className="grid gap-8 lg:grid-cols-[260px_minmax(0,1fr)]">
      <aside><label htmlFor="teach-unit" className="mb-3 block font-semibold">选择要讲清的知识点</label><select id="teach-unit" className={learningInput} value={selected} disabled={busy} onChange={e=>{const id=e.target.value;setSelected(id);setResult(null);const key=`teach-back-draft:${getCurrentUserId()}:${id}:new`;setEvidence(evidenceDraft(key,{}));setText(localStorage.getItem(key)??"");window.history.replaceState(null,"",`/teach-back?unit=${encodeURIComponent(id)}`);}}>{units.map(u=><option key={u.id} value={u.id}>{u.title}</option>)}</select>
        <h2 className="mt-7 mb-3 font-semibold">我的讲回记录</h2>{history.length===0?<p className="leading-7 text-[var(--text-secondary)]">还没有保存的讲回。</p>:<ul className="space-y-2">{[...history].reverse().map(r=><li key={r.id}><button type="button" disabled={busy} className="w-full rounded-lg p-3 text-left hover:bg-[var(--bg-hover)]" onClick={()=>restore(r)}><span className="block">{r.title}{r.parent_id?" · 补充":""}</span><time className="text-base sm:text-xs text-[var(--text-muted)]">{new Date(r.created_at).toLocaleString("zh-CN")}</time></button></li>)}</ul>}
      </aside>
      <section className="min-w-0">{!unit?<p>当前来源不可用，请选择其他知识点。</p>:<>
        <div className={learningPanel}><h2 className="text-xl font-semibold">{unit.title}</h2><p className="my-3 leading-7 text-[var(--text-secondary)]">先解释适用条件，再给一个不能直接套用结论的例子。条件卡为开发版课程参考。</p><Link href={`/reading?unit=${encodeURIComponent(unit.id)}`} className="text-olive-700 dark:text-olive-300 underline">回看对应材料 →</Link></div>
        <form className="mt-6" onSubmit={async e=>{e.preventDefault();setBusy(true);setError("");try{
          const body={unit_id:unit.id,source_hash:unit.source_hash,text,evidence:Object.fromEntries(Object.entries(evidence).filter(([,v])=>v.trim())),parent_id:result?.id??null};
          const request_id=stableRequestId(localStorage,`teach-back-request:${getCurrentUserId()}:${unit.id}`,body,()=>crypto.randomUUID());
          const saved=await learningRequest<TeachBack>("/teach-back/submissions",{...body,request_id});
          restore(saved);setHistory(previous=>[...previous.filter(r=>r.id!==saved.id),saved]);
        }catch(e){setError(e instanceof Error?e.message:"保存失败，输入仍保留");}finally{setBusy(false);}}}>
          <label htmlFor="teach-text" className="mb-3 block text-xl font-semibold">{result?"补充我的解释":"我的解释"}</label><textarea id="teach-text" required maxLength={4000} rows={7} className={learningInput} value={text} onChange={e=>{setText(e.target.value);localStorage.setItem(draftKey,e.target.value);}} placeholder="为什么这个方法可用？结论用了什么条件？如何判断能停止？"/>
          <fieldset className="mt-5 space-y-4"><legend className="mb-3 font-semibold">把我的原句与条件对应起来</legend><p className="leading-7 text-[var(--text-secondary)]">从上面的解释复制原句。不确定的条件可以留空，保存后逐项补充；对应原句不代表已验证理解正确。</p>{unit.conditions.map((c,i)=><div key={c}><label htmlFor={`teach-evidence-${i}`} className="mb-2 block leading-7">{c}</label><input id={`teach-evidence-${i}`} maxLength={4000} className={learningInput} value={evidence[i]??""} onChange={e=>{const value={...evidence,[i]:e.target.value};setEvidence(value);localStorage.setItem(`${draftKey}:evidence`,JSON.stringify(value));}} placeholder="引用我上面写的一句原话，或留空"/></div>)}</fieldset>
          <button type="submit" disabled={busy||!text.trim()} className={`${learningButton} mt-6`}>{busy?"保存与对照中…":result?"保存补充版本":"保存讲回并对照条件"}</button>
        </form>
        {result && <section className="mt-8 border-t border-[var(--border-subtle)] pt-6"><h2 className="text-xl font-semibold">已保存版本的条件对照</h2><p className="mt-3 leading-7 text-[var(--text-secondary)]">保留你的原话和来源，不以讲回评价更新独立成绩。{result.model_status==="self_review"?"当前未配置模型，使用自我讲回与条件对照。":result.model_status==="unavailable"?"模型暂不可用；文字与条件对照已保存。":"模型评语尚未经数学核验。"}</p>
          <TeachBackEvidence saved={result} focusedCondition={focusedCondition}/>
          {result.model_commentary && !result.evidence_version && <div className="mt-6 rounded-lg bg-olive-600/5 p-4"><h3 className="mb-3 font-semibold">历史模型意见 · 未核验，未记录原句跨度</h3><MathMarkdown content={result.model_commentary}/></div>}
          <details className="mt-6"><summary className="cursor-pointer py-3">查看本次绑定的课程来源</summary><p className="my-3 break-all text-base sm:text-xs text-[var(--text-muted)]">{result.source_hash}</p><MathMarkdown content={result.source_quote}/></details>
        </section>}
      </> }</section>
    </div>}
  </LearningShell>;
}
