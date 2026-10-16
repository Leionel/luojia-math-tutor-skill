"use client";
import { useEffect, useRef, useState } from "react";
import { acknowledgeRootFeedback, type RootDiagnosis } from "@/lib/api";

export function RootDiagnosticCard({ report, sessionId, complete, onRevision, onProbe }: {
  report: RootDiagnosis; sessionId: string; complete: boolean;
  onRevision?: (report: RootDiagnosis) => void; onProbe?: (report: RootDiagnosis) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const [receipt, setReceipt] = useState("");
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!complete || !sessionId) return;
    let alive = true, sending = false, visible = false;
    const acknowledge = async () => {
      if (sending || !visible || document.visibilityState !== "visible") return;
      sending = true;
      try {
        const response = await acknowledgeRootFeedback(sessionId, report);
        if (alive) { setReceipt(response.outcome); setError(""); }
      } catch (e) { if (alive) setError(e instanceof Error ? e.message : "回执保存失败。"); }
    };
    const observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting; void acknowledge(); });
    if (container.current) observer.observe(container.current);
    document.addEventListener("visibilitychange", acknowledge);
    return () => { alive = false; observer.disconnect(); document.removeEventListener("visibilitychange", acknowledge); };
  }, [report, sessionId, complete, retry]);
  const outcomes: Record<string, string> = {unknown:"本轮完成状态未知",failed:"已记录过程偏差",observed_success:"已记录本次验证成功",assisted_success:"已记录受助修订成功",independent_probe_success:"已记录一次独立探针成功"};
  return <div ref={container} className="my-4 min-w-0 rounded-xl border border-olive-500/25 bg-olive-500/5 p-3 text-sm">
    <div className="flex flex-wrap justify-between gap-2"><strong>求根过程证据</strong><span className="text-xs text-[var(--text-muted)]">{report.oracle_version}</span></div>
    <p className="text-xs break-words">Case：{report.case_id || "尚未匹配"} · {report.case_decision}</p>
    {report.error_step !== null && <p>定位到步骤 k={report.error_step}</p>}
    {report.trace.length > 0 && <div className="max-h-48 overflow-auto"><table className="w-full text-xs"><thead><tr><th>k</th><th>xₖ</th><th>f(xₖ)</th><th>步长</th></tr></thead><tbody>{report.trace.map(row => <tr key={row.k}><td>{row.k}</td><td>{row.x_k.toPrecision(7)}</td><td>{row.f_x.toPrecision(5)}</td><td>{row.step_size?.toPrecision(4) ?? "—"}</td></tr>)}</tbody></table></div>}
    <p className="text-xs text-[var(--text-muted)]">本次帮助等级 {report.help_level} · 剩余提示预算 {report.remaining_help} · {receipt ? outcomes[receipt] || receipt : "显示后保存回执；结果暂未计入"}</p>
    {error && <p role="alert" className="text-cinnabar-600">{error} <button type="button" className="underline" onClick={() => setRetry(v => v + 1)}>重试回执</button></p>}
    <div className="flex flex-wrap gap-2 mt-2">
      {onRevision && <button type="button" disabled={!complete} onClick={() => onRevision(report)} className="min-h-11 rounded border px-3 py-2 text-xs">修改轨迹再验证</button>}
      {onProbe && report.complete && report.kind === "practice" && <button type="button" disabled={!receipt || !complete} onClick={() => onProbe(report)} className="min-h-11 rounded border px-3 py-2 text-xs">开始独立探针</button>}
    </div>
    <p className="text-xs text-[var(--text-muted)]">单次成功是过程证据，不代表已掌握或具有迁移能力。</p>
  </div>;
}
