"use client";
import {useEffect, useState} from "react";
import {LearningShell, Notice, learningInput, learningButton, learningPanel} from "@/components/learning/learning-shell";
import {learningRequest, parseTrace, stableRequestId, type CodeAssignment, type CodeSubmission} from "@/lib/learning-api";
import {SavedCodeReview} from "@/components/learning/saved-code-review";
import {getCurrentUserId} from "@/lib/demo-auth";

const diagnosticLabels:Record<string,string>={supported:"证据支持",contradicted:"发现偏差",inconclusive:"尚不能确认",tool_error:"诊断失败"};
const diagnosticLabel=(status:string|null|undefined)=>diagnosticLabels[status??""]??"未提交";

export default function CodeWorkshopPage(){
  const [assignment,setAssignment]=useState<CodeAssignment|null>(null);
  const [code,setCode]=useState("");const [trace,setTrace]=useState("");const [stop,setStop]=useState("none");
  const [result,setResult]=useState<CodeSubmission|null>(null);const [history,setHistory]=useState<CodeSubmission[]>([]);
  const [error,setError]=useState("");const [busy,setBusy]=useState(false);const [loading,setLoading]=useState(true);
  const draftKey=`code-workshop:${getCurrentUserId()}:${result?.id??"new"}`;
  const restore=(s:CodeSubmission)=>{const key=`code-workshop:${getCurrentUserId()}:${s.id}`;setResult(s);setCode(localStorage.getItem(`${key}:code`)??s.code);setTrace(localStorage.getItem(`${key}:trace`)??s.iterates.join(", "));setStop(localStorage.getItem(`${key}:stop`)??s.stop_reason);window.history.replaceState(null,"",`/code-workshop?id=${encodeURIComponent(s.id)}`);};
  useEffect(()=>{Promise.all([learningRequest<CodeAssignment>("/code-workshop/assignment"),learningRequest<{submissions:CodeSubmission[]}>("/code-workshop/submissions")]).then(async([a,b])=>{
    setAssignment(a);setHistory(b.submissions);setCode(localStorage.getItem(`code-workshop:${getCurrentUserId()}:new:code`)??a.template);setTrace(localStorage.getItem(`code-workshop:${getCurrentUserId()}:new:trace`)??"");setStop(localStorage.getItem(`code-workshop:${getCurrentUserId()}:new:stop`)??"none");
    const id=new URLSearchParams(window.location.search).get("id");if(id)restore(await learningRequest<CodeSubmission>(`/code-workshop/submissions/${encodeURIComponent(id)}`));
  }).catch(e=>setError(e.message)).finally(()=>setLoading(false));},[]);
  return <LearningShell title="把程序改动讲出依据" description="限定 Newton 作业的静态审阅首版。代码会保存与解析，手动提交的迭代轨迹另行诊断，二者分别呈现。">
    <Notice error={error}/>{loading?<p role="status">正在恢复作业…</p>:!assignment?<p className="leading-7">作业暂不可用，请先处理上方提示后重新加载。</p>:<div className="grid gap-8 lg:grid-cols-[260px_minmax(0,1fr)]">
      <aside><h2 className="text-xl font-semibold">{assignment.title}</h2><p className="mt-4 leading-7">f(x) = x² − 2<br/>x₀ = 1，区间 [1, 2]<br/>根误差目标 ≤ 10⁻⁴</p><p className="mt-4 break-words font-mono text-base sm:text-sm">{assignment.signature}</p><ul className="mt-5 list-disc space-y-3 pl-5 leading-7">{assignment.checks.map(c=><li key={c}>{c}</li>)}</ul><p className="mt-5 text-base sm:text-sm leading-7 text-ochre-700 dark:text-ochre-300">隔离执行环境尚未验收，学生代码不会在服务器运行。静态提示和手动轨迹不能证明代码运行正确。</p>
        <h3 className="mt-7 font-semibold">提交版本</h3>{history.length===0?<p className="mt-3 text-[var(--text-secondary)]">还没有保存的版本。</p>:<ul className="mt-2">{[...history].reverse().map(s=><li key={s.id}><button type="button" disabled={busy} className="w-full rounded-lg p-3 text-left hover:bg-[var(--bg-hover)]" onClick={()=>restore(s)}>{s.previous_id?"修订版本":"首次提交"}<time className="mt-1 block text-base sm:text-xs text-[var(--text-muted)]">{new Date(s.created_at).toLocaleString("zh-CN")}</time></button></li>)}</ul>}
      </aside>
      <section className="min-w-0"><form onSubmit={async e=>{e.preventDefault();setBusy(true);setError("");try{
        const values=trace.trim()?parseTrace(trace):[];
        if(values.some(v=>typeof v!=="number"))throw new Error("作业轨迹暂只接受有限数值；请在实验台核对非有限观察。");
        const body={assignment_id:assignment.id,code,iterates:values,stop_reason:stop,previous_id:result?.id??null};
        const request_id=stableRequestId(localStorage,`${draftKey}:request`,body,()=>crypto.randomUUID());
        const saved=await learningRequest<CodeSubmission>("/code-workshop/submissions",{...body,request_id});restore(saved);setHistory(previous=>[...previous.filter(s=>s.id!==saved.id),saved]);
      }catch(e){setError(e instanceof Error?e.message:"审阅失败，代码仍保留");}finally{setBusy(false);}}}>
        <label htmlFor="student-code" className="mb-3 block text-xl font-semibold">我的 Python 作业</label><p className="mb-3 leading-7 text-[var(--text-secondary)]">模板故意保留待修订的更新，请先检查再修改。提交后只做语法与限定规则审阅。</p><textarea id="student-code" required spellCheck={false} maxLength={8000} rows={14} className={`${learningInput} font-mono`} value={code} onChange={e=>{setCode(e.target.value);localStorage.setItem(`${draftKey}:code`,e.target.value);}}/>
        <label htmlFor="code-trace" className="mt-6 mb-3 block font-semibold">可选：手动提交本地计算轨迹</label><p className="mb-3 text-base sm:text-sm leading-7 text-[var(--text-secondary)]">包含初值 1，用逗号或换行分隔。首版无法验证这些数值由上面的代码产生。</p><textarea id="code-trace" rows={3} className={`${learningInput} font-mono`} value={trace} onChange={e=>{setTrace(e.target.value);localStorage.setItem(`${draftKey}:trace`,e.target.value);}}/>
        <label htmlFor="code-stop" className="mt-4 mb-2 block">轨迹的停止依据</label><select id="code-stop" className={learningInput} value={stop} onChange={e=>{setStop(e.target.value);localStorage.setItem(`${draftKey}:stop`,e.target.value);}}><option value="none">尚未停止 / 未提交轨迹</option><option value="residual">残差达到阈值</option><option value="step">相邻迭代差达到阈值</option><option value="exact">零残差</option><option value="iteration_limit">达到迭代上限</option></select>
        <button type="submit" disabled={busy||!code.trim()} className={`${learningButton} mt-5`}>{busy?"保存与静态审阅中…":result?"保存修订并比较":"保存并静态审阅"}</button>
      </form>
      {result && <section className={`${learningPanel} mt-7`}><h2 className="text-xl font-semibold">已保存版本的静态审阅 · 代码未执行</h2><SavedCodeReview key={result.id} submission={result} edited={code!==result.code}/>
        {result.trace_diagnosis && <div className="mt-5 border-t border-[var(--border-subtle)] pt-5"><h3 className="font-semibold">手动轨迹诊断 · {diagnosticLabel(result.trace_diagnosis.status)}</h3><p className="mt-2 leading-7">{result.trace_diagnosis.summary}</p><p className="mt-2 text-base sm:text-sm text-[var(--text-secondary)]">仅判断本次提交的数值过程，不计为独立成功或代码执行通过。</p></div>}
        {result.comparison && <div className="mt-5 border-t border-[var(--border-subtle)] pt-5"><h3 className="font-semibold">与上一版本比较</h3><p className="mt-2 leading-7">代码{result.comparison.code_changed?"已有修改":"内容相同"}；静态提示 {result.comparison.previous_findings} → {result.comparison.current_findings} 项。</p><p className="mt-2 text-base sm:text-sm leading-7 text-[var(--text-secondary)]">提示数量减少不代表数学正确性提高。轨迹状态：{diagnosticLabel(result.comparison.previous_trace_status)} → {diagnosticLabel(result.comparison.current_trace_status)}。</p></div>}
      </section>}
      </section>
    </div>}
  </LearningShell>;
}
