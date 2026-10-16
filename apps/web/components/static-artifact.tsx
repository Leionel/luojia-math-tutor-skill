"use client";
import {useEffect,useRef,useState} from "react";
import {buildStaticArtifact,staticSvgHeight} from "@/lib/visual-artifact";

export function StaticArtifact({content,ready,interactive=false}:{content:string;ready:boolean;interactive?:boolean}){
 const container=useRef<HTMLElement>(null),manualHeight=useRef(false);
 const [preview,setPreview]=useState(false),[height,setHeight]=useState(320),[document,setDocument]=useState(""),[error,setError]=useState("");
 useEffect(()=>{setPreview(false);setDocument("");setError("");manualHeight.current=false;setHeight(320);},[content,ready]);
 useEffect(()=>{
  if(!ready||!preview)return;
  const refresh=()=>{try{setDocument(buildStaticArtifact(content,window.document.documentElement.classList.contains("dark")));setError("");}catch(e){setError(e instanceof Error?e.message:"预览暂不可用，请查看源码。");setDocument("");}};
  refresh();
  const resize=new ResizeObserver(entries=>{const value=staticSvgHeight(content,entries[0].contentRect.width);if(value!==null&&!manualHeight.current)setHeight(value);});
  if(container.current)resize.observe(container.current);
  const theme=new MutationObserver(refresh);theme.observe(window.document.documentElement,{attributes:true,attributeFilter:["class"]});
  return()=>{resize.disconnect();theme.disconnect();};
 },[content,ready,preview]);
 return <section ref={container} className="my-3 min-w-0 max-w-full overflow-hidden rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)]">
  <div className="flex flex-wrap items-center gap-2 p-2 text-xs"><span>{interactive?"HTML 图示 · 静态查看":"静态 SVG/HTML 图示"}</span><button type="button" className="min-h-11 rounded border px-3 py-2" disabled={!ready} onClick={()=>{setPreview(!preview);setError("");}}>{!ready?"预览待生成完成":preview?"关闭预览，查看源码":"打开静态预览"}</button><button type="button" className="min-h-11 rounded border px-3 py-2" onClick={()=>navigator.clipboard.writeText(content).catch(()=>setError("复制失败，请手动复制源码。"))}>复制源码</button>{!ready&&<span role="status">生成中；完成后可预览</span>}</div>
  {interactive&&<p className="px-3 pb-2 text-xs leading-6" role="status">当前仅显示 HTML 的静态部分，原源码保留，脚本未运行；若画面为空，可继续根据图示说明提问。</p>}
  {error&&<p role="alert" className="px-3 text-cinnabar-600">{error}</p>}
  {preview&&ready&&document&&!error?<><iframe title="静态 HTML/SVG 图示" sandbox="" referrerPolicy="no-referrer" srcDoc={document} className="block w-full border-0" style={{height}} onError={()=>{setError("预览加载失败，原源码仍保留。");setPreview(false);}}/><label className="flex flex-wrap gap-2 p-2 text-xs">预览高度 {height}px<input aria-label="预览高度" type="range" min="180" max="800" step="20" value={height} onChange={e=>{manualHeight.current=true;setHeight(Number(e.target.value));}}/></label><p className="px-3 pb-2 text-xs leading-6">脚本、外部资源与链接已禁用；仅显示静态内容，不表示代码已执行。</p></>:<pre className="m-0 max-h-80 overflow-auto whitespace-pre p-3 text-xs"><code>{content}</code></pre>}
 </section>;
}
