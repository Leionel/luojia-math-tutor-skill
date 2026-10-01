"use client";
import { useEffect, useRef, useState } from "react";
import { buildStaticArtifact, staticSvgHeight } from "@/lib/visual-artifact";
export function StaticArtifact({ content, ready }: { content: string; ready: boolean }) {
  const container = useRef<HTMLElement>(null);
  const manualHeight = useRef(false);
  const [preview, setPreview] = useState(false);
  const [height, setHeight] = useState(320);
  const [document, setDocument] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!ready || !preview) return;
    const refresh = () => {
      try { setDocument(buildStaticArtifact(content, window.document.documentElement.classList.contains("dark"))); setError(""); }
      catch (e) { setError(e instanceof Error ? e.message : "无法生成静态预览"); setDocument(""); }
    };
    refresh();
    const resize = new ResizeObserver(entries => {
      const size = staticSvgHeight(content, entries[0].contentRect.width);
      if (size !== null && !manualHeight.current) setHeight(size);
    });
    if (container.current) resize.observe(container.current);
    const observer = new MutationObserver(refresh);
    observer.observe(window.document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => { observer.disconnect(); resize.disconnect(); };
  }, [content, ready, preview]);
  return <section ref={container} className="my-3 min-w-0 max-w-full rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] overflow-hidden">
    <div className="flex flex-wrap items-center gap-2 p-2 text-xs">
      <span>静态图示 · visual-v1</span>
      <button type="button" className="rounded border px-3 py-2" disabled={!ready} onClick={() => setPreview(!preview)}>{!ready ? "预览待生成完成" : preview ? "查看源码" : "打开预览"}</button>
      <button type="button" className="rounded border px-3 py-2" onClick={() => navigator.clipboard.writeText(content).catch(() => setError("复制失败，请手动复制源码。"))}>复制源码</button>
      {!ready && <span role="status">生成中；完成后可预览</span>}
    </div>
    {error && <p role="alert" className="px-3 text-cinnabar-600">{error}</p>}
    {preview && ready && document && !error ? <>
      <iframe title="静态 HTML/SVG 图示" sandbox="" referrerPolicy="no-referrer" srcDoc={document} className="block w-full border-0" style={{ height }} onError={() => setError("预览加载失败，请查看源码。")} />
      <label className="flex flex-wrap gap-2 p-2 text-xs">预览高度 {height}px <input aria-label="预览高度" type="range" min="180" max="800" step="20" value={height} onChange={e => { manualHeight.current = true; setHeight(Number(e.target.value)); }} /></label>
      <p className="px-3 pb-2 text-xs text-[var(--text-muted)]">脚本、外部资源和链接已禁用；可在预览内滚动。</p>
    </> : <pre className="m-0 overflow-auto max-h-80 p-3 text-xs whitespace-pre"><code>{content}</code></pre>}
  </section>;
}
