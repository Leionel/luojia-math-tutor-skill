"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import type { Exploration } from "@/lib/explorations";
import { learningInput } from "./learning-shell";

export function ExplorationGuide({record, originSession}: {record: Exploration | null; originSession: string}) {
  const session = record?.origin_session_id || originSession;
  return <aside aria-label="探索下一步" className="mb-5 min-w-0 space-y-3 rounded-xl border border-olive-600/25 bg-[var(--bg-card)] p-4 text-sm leading-7">
    <p>{!record ? "先写下一个想检查的判断，保存后再选实验。" : !record.runs.length ? "下一步：请助教建议，或手工填写参数；写下预测后确认计算。" : "已有计算已保存。比较两组证据，再写下修订理由；也可带着证据回到对话。"}</p>
    <div className="flex flex-wrap gap-x-5 gap-y-1">
      {record && <a className="inline-flex min-h-11 items-center underline" href="#exploration-experiment">设计或继续实验</a>}
      {!!record?.runs.length && <a className="inline-flex min-h-11 items-center underline" href="#exploration-revision">记录主张修订</a>}
      <Link className="inline-flex min-h-11 items-center underline" href={session ? `/chat?session=${encodeURIComponent(session)}` : "/chat"}>{session ? "返回原会话" : "返回自由对话"}</Link>
      {record && <Link className="inline-flex min-h-11 items-center underline" href={`/graph?view=personal&exploration=${encodeURIComponent(record.id)}`}>查看这次探索的私人图</Link>}
    </div>
    <details><summary className="min-h-11 cursor-pointer py-2 text-xs">课程、私人、模型和计算标记怎么读？</summary>
      <p className="text-xs text-[var(--text-secondary)]">课程来源保留原审核状态；私人关系是学生确认的意见；助教建议是模型意见，尚待核对；受控计算只说明指定参数下的结果。这些标记都不表示你已独立掌握。</p>
    </details>
  </aside>;
}

export function ExplorationHistory({record}: {record: Exploration}) {
  const [selected, setSelected] = useState<number | null>(null);
  useEffect(() => {
    const read = () => {
      const raw = new URLSearchParams(window.location.search).get("revision");
      setSelected(raw === null ? null : /^\d{1,6}$/.test(raw) ? Number(raw) : -1);
    };
    read(); window.addEventListener("popstate", read);
    return () => window.removeEventListener("popstate", read);
  }, [record.id]);
  const snapshot = record.history.find(h => h.revision === selected);
  return <details open={selected !== null} className="mb-5 min-w-0 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-4">
    <summary className="min-h-11 cursor-pointer py-2 text-sm">查看已保存的历史版本</summary>
    <label className="block text-sm">选择探索历史版本<select aria-label="选择探索历史版本" className={learningInput} value={snapshot?.revision ?? ""} onChange={e => {
      const value = e.target.value ? Number(e.target.value) : null;
      setSelected(value);
      const url = new URL(window.location.href);
      if (value === null) url.searchParams.delete("revision"); else url.searchParams.set("revision", String(value));
      window.history.replaceState(null, "", url.pathname + url.search + url.hash);
    }}><option value="">选择一个已保存版本</option>{[...record.history].reverse().map(h => <option key={h.revision} value={h.revision}>版本 {h.revision} · {new Date(h.at).toLocaleString("zh-CN")}</option>)}</select></label>
    {selected !== null && !snapshot && <p role="alert" className="mt-3 text-sm">找不到指定历史版本。没有替换为其他版本；请选择已有记录。</p>}
    {snapshot && <section aria-label={`历史版本 ${snapshot.revision}`} className="mt-3 min-w-0 space-y-2 text-sm leading-7">
      <h2 className="font-semibold">正在查看历史版本 {snapshot.revision}</h2>
      <p className="whitespace-pre-wrap break-words">当时的主张：{snapshot.claim}</p>
      {snapshot.payload.reason && <p className="whitespace-pre-wrap break-words">当时的修订理由：{snapshot.payload.reason}</p>}
      {snapshot.payload.prediction && <p className="whitespace-pre-wrap break-words">计算前预测：{snapshot.payload.prediction}</p>}
      <p>私人节点 {snapshot.graph.nodes.length} · 私人关系 {snapshot.graph.edges.length} · 本次计算 {snapshot.payload.runs?.length ?? 0} 组</p>
      <p className="text-xs text-[var(--text-secondary)]">历史仅供查看，不会回退数据。下方表单始终编辑最新版本 {record.revision}。</p>
      <button type="button" className="min-h-11 underline" onClick={() => {
        setSelected(null); const url = new URL(window.location.href); url.searchParams.delete("revision"); window.history.replaceState(null,"",url.pathname+url.search);
      }}>收起历史，继续最新版本</button>
    </section>}
  </details>;
}
