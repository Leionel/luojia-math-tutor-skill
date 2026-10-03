"use client";
import Link from "next/link";
import {useEffect, useId, useRef, useState} from "react";
import {Check, FlaskConical, Loader2, ArrowRight} from "lucide-react";
import {getCurrentUserId} from "@/lib/demo-auth";
import {finiteNumber, learningRequest, stableRequestId, type LabRun} from "@/lib/learning-api";
import {parseRootProposals, previewMatches, sameContext, type PreviewParameters, type RootActionState, type RootProposal} from "@/lib/learning-actions";
import type {LearningContextRef} from "@/lib/learning-context";
import type {TutorMeta} from "@/lib/api";
import {learningInput} from "./learning-shell";

export function RootActionCards({meta, sessionId, messageId, context, disabled, onSaved}: {
  meta?: TutorMeta | null; sessionId: string; messageId?: string; context?: LearningContextRef;
  disabled?: boolean; onSaved?: (run: LabRun) => void;
}) {
  if (!messageId || !meta || meta.error || !["passed", "repaired"].includes(meta.answer_guard?.status ?? "")
    || meta.agent_run?.status !== "succeeded" || meta.agent_run.message_id !== messageId) return null;
  return parseRootProposals(meta.tutor_artifacts).filter(p => p.run_id === meta.agent_run?.run_id).map(p =>
    <RootActionCard key={p.artifact_id} proposal={p} sessionId={sessionId} messageId={messageId}
      context={context} disabled={disabled} onSaved={onSaved}/>);
}

function RootActionCard({proposal, sessionId, messageId, context, disabled, onSaved}: {
  proposal: RootProposal; sessionId: string; messageId: string; context?: LearningContextRef;
  disabled?: boolean; onSaved?: (run: LabRun) => void;
}) {
  const id = useId();
  const [initial, setInitial] = useState(String(proposal.parameters.initial_value));
  const [tolerance, setTolerance] = useState(String(proposal.parameters.tolerance));
  const [limit, setLimit] = useState(String(proposal.parameters.max_iterations));
  const [observation, setObservation] = useState("");
  const [state, setState] = useState<RootActionState | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [clockExpired, setClockExpired] = useState(false);
  const request = useRef<AbortController | null>(null);
  const locked = useRef(false);
  const generation = useRef(0);
  const path = `/tutor/sessions/${encodeURIComponent(sessionId)}/messages/${encodeURIComponent(messageId)}/artifacts/${encodeURIComponent(proposal.artifact_id)}`;
  const attached = sameContext(context, proposal.context);
  const expired = state?.state === "expired" || clockExpired;
  const saved = state?.saved_run;
  const blocked = disabled || !attached || !state || busy || expired || !!saved;
  useEffect(() => {
    const remaining=Date.parse(proposal.expires_at)-Date.now();
    if(remaining<=0){setClockExpired(true);return;}
    const timer=setTimeout(()=>setClockExpired(true),Math.min(remaining,2147483647));
    return ()=>clearTimeout(timer);
  },[proposal.expires_at]);
  useEffect(() => {
    const owner = getCurrentUserId();
    const version = ++generation.current;
    const controller = new AbortController(); request.current?.abort(); request.current = controller;
    locked.current = false; setBusy(false); setError("");
    learningRequest<RootActionState>(path, undefined, controller.signal).then(next => {
      if (version !== generation.current || owner !== getCurrentUserId()) return;
      setState(next);
      if (next.preview) {
        setInitial(String(next.preview.parameters.initial_value)); setTolerance(String(next.preview.parameters.tolerance));
        setLimit(String(next.preview.max_iterations));
      }
      if (next.saved_run) setObservation(next.saved_run.prediction);
    }).catch(e => {if (!controller.signal.aborted && version === generation.current) setError(e.message);});
    const cancel = () => {generation.current++; controller.abort(); request.current?.abort();};
    window.addEventListener("luojia-auth-change", cancel); window.addEventListener("storage", cancel);
    return () => {cancel(); window.removeEventListener("luojia-auth-change", cancel); window.removeEventListener("storage", cancel);};
  }, [path, attached]);
  let parameters: PreviewParameters | null = null;
  try {
    parameters = {initial_value: finiteNumber(initial, "初值"), tolerance: finiteNumber(tolerance, "阈值"), max_iterations: finiteNumber(limit, "迭代上限")};
    if (Math.abs(parameters.initial_value)>1e25 || parameters.tolerance<=0 || parameters.tolerance>1
      || !Number.isInteger(parameters.max_iterations) || parameters.max_iterations<1 || parameters.max_iterations>100) parameters=null;
  } catch { /* Invalid draft keeps the last preview visible, but cannot save it. */ }
  const matches = !!parameters && previewMatches(state?.preview ?? null, parameters);
  async function act(action: "preview" | "save") {
    if (locked.current || blocked || !parameters || !context) return;
    locked.current = true; setBusy(true); setError("");
    const owner = getCurrentUserId(), version = generation.current;
    const controller = new AbortController(); request.current = controller;
    const current = () => version === generation.current && owner === getCurrentUserId() && !controller.signal.aborted;
    try {
      if (action === "preview") {
        const body = {context, parameters, request_id: stableRequestId(localStorage, `lab-action:${owner}:${proposal.artifact_id}`, {context, parameters}, () => crypto.randomUUID())};
        await learningRequest(`${path}/preview`, body, controller.signal);
      } else {
        if (!state?.preview || !matches || !observation.trim()) return;
        const run = await learningRequest<LabRun>(`${path}/save`, {context, preview_id: state.preview.id,
          preview_hash: state.preview.input_hash, observation: observation.trim()}, controller.signal);
        if (!current()) return;
        setState(previous => previous ? {...previous, state:"saved", saved_run:run} : previous);
        onSaved?.(run);
        return;
      }
      const next = await learningRequest<RootActionState>(path, undefined, controller.signal);
      if (current()) setState(next);
    } catch (e) {if (current()) setError(e instanceof Error ? e.message : "操作未完成，请重试");}
    finally {if (version === generation.current) {locked.current = false; setBusy(false);}}
  }
  return <section aria-label="调整实验参数" className="mt-5 overflow-hidden rounded-2xl border border-olive-500/25 bg-[var(--bg-card)] shadow-[0_6px_24px_-16px_rgba(63,76,49,.35)]">
    <div className="flex items-start gap-3 border-b border-olive-500/15 bg-olive-500/5 px-5 py-4">
      <FlaskConical aria-hidden="true" className="mt-1 size-5 shrink-0 text-olive-700 dark:text-olive-300"/>
      <div><h3 className="font-serif text-lg font-semibold">换一个初值，看看会怎样</h3><p className="mt-1 text-sm leading-6 text-[var(--text-secondary)]">沿用原函数和方法。由你调整参数，确认后预览。</p></div>
    </div>
    <div className="space-y-4 p-5">
      {!attached && <p className="text-sm leading-6 text-ochre-700 dark:text-ochre-300">这张卡片属于另一实验或迭代步骤。<Link href={`/lab?id=${encodeURIComponent(proposal.context.record_id)}`} className="underline">回看原实验</Link>，或针对当前步骤重新提问。</p>}
      <div className="grid grid-cols-2 gap-3">
        <label htmlFor={`${id}-initial`} className="text-sm">初值 x₀<input id={`${id}-initial`} inputMode="decimal" value={initial} disabled={blocked} onChange={e=>setInitial(e.target.value)} className={`${learningInput} mt-2 font-mono`}/></label>
        <label htmlFor={`${id}-tolerance`} className="text-sm">阈值<input id={`${id}-tolerance`} inputMode="decimal" value={tolerance} disabled={blocked} onChange={e=>setTolerance(e.target.value)} className={`${learningInput} mt-2 font-mono`}/></label>
        <label htmlFor={`${id}-limit`} className="col-span-2 text-sm">迭代上限 · 1–100<input id={`${id}-limit`} type="number" min={1} max={100} step={1} value={limit} disabled={blocked} onChange={e=>setLimit(e.target.value)} className={`${learningInput} mt-2 font-mono`}/></label>
      </div>
      {!saved && <button type="button" disabled={blocked || !parameters || (state?.preview_ids.length ?? 0)>=proposal.preview_budget} onClick={()=>void act("preview")} className="flex min-h-12 w-full items-center justify-center gap-2 rounded-lg border border-olive-500/40 text-olive-800 transition-colors hover:bg-olive-500/10 focus-visible:outline-2 focus-visible:outline-olive-600 disabled:opacity-45 dark:text-olive-200">{busy?<Loader2 aria-hidden="true" className="size-4 animate-spin"/>:<FlaskConical aria-hidden="true" className="size-4"/>}预览参数 · {state?.preview_ids.length ?? 0}/{proposal.preview_budget}</button>}
      {state?.preview && <div className="rounded-lg bg-[var(--bg-tertiary)] p-4">
        <p className="text-sm font-medium">{saved?"已保存的预览":"参考预览 · 尚未保存到实验记录"}</p>
        <p className="mt-2 break-all font-mono text-sm leading-6">x₀={state.preview.parameters.initial_value} → x₁={state.preview.rows[1]?.x.toPrecision(7) ?? "无下一步"} → … → xₖ={state.preview.rows.at(-1)?.x.toPrecision(7)}</p>
        <p className="mt-2 text-sm leading-6">{state.preview.stop_detail}</p>
        <p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">{state.preview.diagnosis.summary}</p>
        {!matches && !saved && <p className="mt-2 text-sm text-cinnabar-700 dark:text-cinnabar-300">参数已修改，请重新预览后保存。</p>}
      </div>}
      {state?.preview && !saved && <>
        <label htmlFor={`${id}-observation`} className="block text-sm">预览后的观察<textarea id={`${id}-observation`} rows={3} maxLength={1000} value={observation} disabled={blocked} onChange={e=>setObservation(e.target.value)} placeholder="哪个变化和你的理解一致？还需要核对什么条件？" className={`${learningInput} mt-2`}/></label>
        <button type="button" disabled={blocked || !matches || !observation.trim()} onClick={()=>void act("save")} className="flex min-h-12 w-full items-center justify-center gap-2 rounded-lg bg-olive-700 px-4 font-medium text-paper-50 transition-colors hover:bg-olive-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-olive-600 disabled:opacity-45">保存这次实验<ArrowRight aria-hidden="true" className="size-4"/></button>
      </>}
      {saved && <p className="flex items-center gap-2 text-sm text-olive-700 dark:text-olive-300"><Check aria-hidden="true" className="size-4"/>已保存 · <Link href={`/lab?id=${encodeURIComponent(saved.id)}`} className="inline-flex min-h-12 items-center underline">回看新实验</Link></p>}
      {expired && !saved && <p className="text-sm text-ochre-700 dark:text-ochre-300">卡片已过期，请重新讨论当前实验。</p>}
      {error && <p role="alert" className="text-sm leading-6 text-cinnabar-700 dark:text-cinnabar-300">{error}</p>}
      <p className="text-xs leading-6 text-[var(--text-muted)]">预览计作参考帮助；保存记录你的观察，不计独立完成。</p>
    </div>
  </section>;
}
