"use client";
import { useEffect, useRef, useState } from "react";
import { buildStaticArtifact, buildDynamicArtifact, staticSvgHeight } from "@/lib/visual-artifact";
export function StaticArtifact({ content, ready, interactive = false }: { content: string; ready: boolean; interactive?: boolean }) {
  const frame = useRef<HTMLIFrameElement>(null);
  const [run, setRun] = useState(0);
  const [runtime, setRuntime] = useState("");
  const container = useRef<HTMLElement>(null);
  const manualHeight = useRef(false);
  const [preview, setPreview] = useState(false);
  const [height, setHeight] = useState(320);
  const [document, setDocument] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!ready) {setPreview(false);setRuntime("");setDocument("");return;}
    if (!preview) return;
    const channel = crypto.randomUUID();
    let deadline: ReturnType<typeof setTimeout> | undefined;
    const refresh = () => {
      try { const dark = window.document.documentElement.classList.contains("dark"); setDocument(interactive ? buildDynamicArtifact(content, dark, channel) : buildStaticArtifact(content, dark)); setError(""); setRuntime(interactive ? "运行中，每次最多30秒" : ""); }
      catch (e) { setError(e instanceof Error ? e.message : "无法生成静态预览"); setDocument(""); setRuntime(""); }
    };
    const receive = (event: MessageEvent) => {
      if (event.source !== frame.current?.contentWindow || event.data?.channel !== channel) return;
      if (event.data.kind === "error") {setError(`预览脚本错误：${String(event.data.value).slice(0,300)}`);setRuntime("运行已停止");setDocument("");}
      if (event.data.kind === "height" && Number.isFinite(event.data.value) && !manualHeight.current) setHeight(Math.max(180,Math.min(800,event.data.value)));
    };
    if (interactive) {
      window.addEventListener("message",receive);
      deadline = setTimeout(()=>{setPreview(false);setDocument("");setRuntime("本次运行已到30秒，可重新运行。");},30000);
    }
    refresh();
    const resize = new ResizeObserver(entries => {
      const size = staticSvgHeight(content, entries[0].contentRect.width);
      if (size !== null && !manualHeight.current) setHeight(size);
    });
    if (container.current) resize.observe(container.current);
    const observer = new MutationObserver(refresh);
    observer.observe(window.document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => { observer.disconnect(); resize.disconnect(); clearTimeout(deadline); window.removeEventListener("message",receive); };
  }, [content, ready, preview, interactive, run]);
  return <section ref={container} className="my-3 min-w-0 max-w-full rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] overflow-hidden">
    <div className="flex flex-wrap items-center gap-2 p-2 text-xs">
      <span>{interactive ? "动态 HTML 图示" : "静态 SVG/HTML 图示"}</span>
      <button type="button" className="min-h-11 rounded border px-3 py-2" disabled={!ready} onClick={() => {setPreview(!preview);setRuntime("");setError("");}}>{!ready ? "预览待生成完成" : preview ? "停止并查看源码" : interactive ? "运行动态预览" : "打开预览"}</button>
      <button type="button" className="min-h-11 rounded border px-3 py-2" onClick={() => navigator.clipboard.writeText(content).catch(() => setError("复制失败，请手动复制源码。"))}>复制源码</button>
      {interactive && preview && ready && <button type="button" className="min-h-11 rounded border px-3 py-2" onClick={()=>setRun(v=>v+1)}>重启</button>}
      {!ready && <span role="status">生成中；完成后可预览</span>}
    </div>
    {runtime && <p className="px-3 text-xs text-[var(--text-muted)]" role="status">{runtime}</p>}
    {error && <p role="alert" className="px-3 text-cinnabar-600">{error}</p>}
    {preview && ready && document && !error ? <>
      <iframe ref={frame} title={interactive ? "动态 HTML 图示" : "静态 HTML/SVG 图示"} sandbox={interactive ? "allow-scripts" : ""} referrerPolicy="no-referrer" srcDoc={document} className="block w-full border-0" style={{ height }} onError={() => setError("预览加载失败，请查看源码。")} />
      <label className="flex flex-wrap gap-2 p-2 text-xs">预览高度 {height}px <input aria-label="预览高度" type="range" min="180" max="800" step="20" value={height} onChange={e => { manualHeight.current = true; setHeight(Number(e.target.value)); }} /></label>
      <p className="px-3 pb-2 text-xs text-[var(--text-muted)]">{interactive ? "支持本地 DOM、Canvas 与动画；外部资源、父页面访问和链接已禁用。" : "脚本、外部资源和链接已禁用；可在预览内滚动。"}</p>
    </> : <pre className="m-0 overflow-auto max-h-80 p-3 text-xs whitespace-pre"><code>{content}</code></pre>}
  </section>;
}
