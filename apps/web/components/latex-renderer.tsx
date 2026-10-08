"use client";

import katex from "katex";
import { parseLatex, parseBlocks, type Block } from "@/lib/message-parser";
import { Copy, Check } from "lucide-react";
import { useEffect, useState } from "react";
import { MathPlot } from "./math-plot";
import { VideoRecommend } from "./video-recommend";
import { StaticArtifact } from "./static-artifact";
import { resolveAnswerImage, API_BASE } from "@/lib/api-base";
import { balancedLatex } from "@/lib/latex-balance";
import { SourceSpanCard } from "./source-span-card";
import { getAuthHeaders, isAuthStorageKey } from "@/lib/demo-auth";

function CodeBlock({ language, content, ready }: { language: string; content: string; ready: boolean }) {
  if (["html", "svg"].includes(language.toLowerCase())) return <StaticArtifact content={content} ready={ready} interactive={language.toLowerCase() === "html"} />;
  return <div className="my-3 rounded-lg border border-[var(--border-subtle)] overflow-hidden"><div className="px-3 py-1 text-xs">{language || "text"}</div><pre className="p-3 overflow-auto text-xs whitespace-pre"><code>{content}</code></pre></div>;
}
function AnswerImage({ source, alt }: { source: string; alt: string }) {
  const [failed, setFailed] = useState(false);
  const [requested, setRequested] = useState(false);
  const [authVersion, setAuthVersion] = useState(0);
  const [privateImage, setPrivateImage] = useState<{ source: string; url: string; authVersion: number } | null>(null);
  const src = resolveAnswerImage(source);
  const apiUrl = new URL(API_BASE);
  const resolvedUrl = src ? new URL(src) : null;
  const privateUpload = Boolean(resolvedUrl && resolvedUrl.origin === apiUrl.origin && /^\/api\/uploads\/[0-9a-f-]{36}\.(?:png|jpg|jpeg|gif|webp)$/i.test(resolvedUrl.pathname));
  useEffect(() => {
    const changed = () => setAuthVersion((version) => version + 1);
    const storage = (event: StorageEvent) => { if (isAuthStorageKey(event.key)) changed(); };
    window.addEventListener("luojia-auth-change", changed);
    window.addEventListener("storage", storage);
    return () => {
      window.removeEventListener("luojia-auth-change", changed);
      window.removeEventListener("storage", storage);
    };
  }, []);
  useEffect(() => {
    setPrivateImage(null);
    setFailed(false);
    if (!src || !privateUpload) return;
    const headers = getAuthHeaders();
    if (!headers.Authorization) { setFailed(true); return; }
    const controller = new AbortController();
    let objectUrl: string | null = null;
    fetch(src, { headers, signal: controller.signal, cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Upload unavailable");
        const blob = await response.blob();
        if (!blob.type.startsWith("image/")) throw new Error("Unexpected upload type");
        if (controller.signal.aborted) return;
        objectUrl = URL.createObjectURL(blob);
        setPrivateImage({ source: src, url: objectUrl, authVersion });
      })
      .catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [src, privateUpload, authVersion]);
  if (!src || failed) return <span role="status">图片不可用：{alt || "未命名图片"}</span>;
  const external = new URL(src).origin !== new URL(API_BASE).origin;
  if (external && !requested) return <span className="block"><button type="button" className="rounded border px-3 py-2 text-xs" onClick={() => setRequested(true)}>加载外部图片：{alt || new URL(src).hostname}</button> <a href={src} target="_blank" rel="noopener noreferrer" className="text-xs underline">图片来源</a></span>;
  if (privateUpload && (privateImage?.source !== src || privateImage.authVersion !== authVersion)) return <span role="status">图片加载中</span>;
  const displaySrc = privateUpload ? privateImage?.url : src;
  return <span className="block"><img src={displaySrc} alt={alt} loading="lazy" referrerPolicy="no-referrer" onError={() => setFailed(true)} className="max-w-full h-auto rounded-lg" />{!privateUpload && <a href={src} target="_blank" rel="noopener noreferrer" className="text-xs underline">图片来源</a>}</span>;
}

function renderLatex(value: string, displayMode = false) {
  try {
    return katex.renderToString(balancedLatex(value), { displayMode, throwOnError: false });
  } catch {
    return value;
  }
}

function MathDisplayBlock({ content }: { content: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="group relative math-block my-3 px-4 py-3 rounded-xl border border-olive-500/15 dark:border-olive-400/15 bg-olive-500/[0.03] dark:bg-olive-400/[0.03] overflow-x-auto transition-all hover:border-olive-500/30 shadow-xs">
      <div dangerouslySetInnerHTML={{ __html: renderLatex(content, true) }} />
      <button
        onClick={handleCopy}
        title="复制 LaTeX 源码"
        className="opacity-0 group-hover:opacity-100 transition-opacity absolute top-2 right-2 px-2 py-1 rounded-md bg-[var(--bg-card)]/90 backdrop-blur-sm border border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-[var(--text-primary)] shadow-xs text-xs flex items-center gap-1 cursor-pointer"
      >
        {copied ? (
          <>
            <Check className="w-3 h-3 text-emerald-500" />
            <span className="text-[10px] text-emerald-500 font-mono">已复制</span>
          </>
        ) : (
          <>
            <Copy className="w-3 h-3" />
            <span className="text-[10px] font-mono">LaTeX</span>
          </>
        )}
      </button>
    </div>
  );
}

function renderMarkdownInline(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    const boldMatch = remaining.match(/\*\*([\s\S]+?)\*\*/);
    const italicMatch = remaining.match(/(?<!\*)\*(?!\*)([\s\S]+?)(?<!\*)\*(?!\*)/);
    const codeMatch = remaining.match(/`([^`]+?)`/);
    const imageMatch = remaining.match(/!\[([^\]]*)\]\(([^)]+)\)/);
    const linkMatch = remaining.match(/(?<!!)\[([^\]]*)\]\(([^)]+)\)/);
    const citationMatch = remaining.match(/\[(P\.[a-zA-Z0-9_-]+|\d+)\](?!\()/i);

    const boldIndex = boldMatch?.index ?? Infinity;
    const italicIndex = italicMatch?.index ?? Infinity;
    const codeIndex = codeMatch?.index ?? Infinity;
    const imageIndex = imageMatch?.index ?? Infinity;
    const linkIndex = linkMatch?.index ?? Infinity;
    const citationIndex = citationMatch?.index ?? Infinity;

    const minIndex = Math.min(boldIndex, italicIndex, codeIndex, imageIndex, linkIndex, citationIndex);

    if (minIndex === Infinity) {
      parts.push(<span key={key++}>{remaining}</span>);
      remaining = "";
      continue;
    }

    if (boldIndex === minIndex && boldMatch) {
      const before = remaining.slice(0, boldIndex);
      if (before) parts.push(<span key={key++}>{before}</span>);
      parts.push(<strong key={key++}>{renderMarkdownInline(boldMatch[1])}</strong>);
      remaining = remaining.slice(boldIndex + boldMatch[0].length);
    } else if (italicIndex === minIndex && italicMatch) {
      const before = remaining.slice(0, italicIndex);
      if (before) parts.push(<span key={key++}>{before}</span>);
      parts.push(<em key={key++}>{renderMarkdownInline(italicMatch[1])}</em>);
      remaining = remaining.slice(italicIndex + italicMatch[0].length);
    } else if (citationIndex === minIndex && citationMatch) {
      const before = remaining.slice(0, citationIndex);
      if (before) parts.push(<span key={key++}>{before}</span>);
      parts.push(
        <SourceSpanCard 
          key={key++} 
          sourceSpan={{ id: citationMatch[1] }} 
          className="mx-0.5 inline-flex" 
        />
      );
      remaining = remaining.slice(citationIndex + citationMatch[0].length);
    } else if (codeIndex === minIndex && codeMatch) {
      const before = remaining.slice(0, codeIndex);
      if (before) parts.push(<span key={key++}>{before}</span>);
      parts.push(
        <code key={key++} className="rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-sm font-mono text-[var(--text-primary)]">
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.slice(codeIndex + codeMatch[0].length);
    } else if (imageIndex === minIndex && imageMatch) {
      const before = remaining.slice(0, imageIndex);
      if (before) parts.push(<span key={key++}>{before}</span>);
      parts.push(<AnswerImage key={key++} source={imageMatch![2]} alt={imageMatch![1]} />);
      remaining = remaining.slice(imageIndex + imageMatch[0].length);
    } else if (linkIndex === minIndex && linkMatch) {
      const before = remaining.slice(0, linkIndex);
      if (before) parts.push(<span key={key++}>{before}</span>);
      
      const url = linkMatch[2];
      const text = linkMatch[1];
      if (url.includes("bilibili.com")) {
        parts.push(
          <a key={key++} href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 mt-2 p-3 rounded-xl border border-blue-500/20 bg-blue-50/50 hover:bg-blue-50 dark:border-blue-500/30 dark:bg-blue-900/20 dark:hover:bg-blue-900/40 transition-colors w-full max-w-sm">
             <div className="w-10 h-10 flex items-center justify-center rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400">
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5"><path d="M17.813 4.653h.854c1.51.054 2.769.657 3.773 1.818 1.003 1.16 1.466 2.56 1.389 4.2v5.936c.077 1.64-.386 3.04-1.389 4.2-1.004 1.161-2.263 1.764-3.773 1.818H5.333c-1.51-.054-2.769-.657-3.773-1.818C.557 19.646.094 18.246.171 16.607V10.67c-.077-1.64.386-3.04 1.389-4.2 1.004-1.161 2.263-1.764 3.773-1.818h.854V3.06c-.007-.156.035-.306.126-.45.09-.144.22-.24.389-.288.169-.048.337-.024.505.072.167.096.28.228.338.396l.867 2.112h5.178l.867-2.112c.058-.168.17-.3.338-.396.168-.096.336-.12.505-.072.169.048.3.144.389.288.09.144.133.294.126.45v1.593zm-12.48 2.052h13.334c.767-.03 1.41.222 1.93.756.52.534.808 1.25.864 2.148v5.936c-.056.898-.344 1.614-.864 2.148-.52.534-1.163.786-1.93.756H5.333c-.767.03-1.41-.222-1.93-.756-.52-.534-.808-1.25-.864-2.148V9.609c.056-.898.344-1.614.864-2.148.52-.534 1.163-.786 1.93-.756zm2.464 2.82c-.524 0-.95.19-1.28.57-.33.38-.495.83-.495 1.35 0 .52.165.97.495 1.35.33.38.756.57 1.28.57.524 0 .95-.19 1.28-.57.33-.38.495-.83.495-1.35 0-.52-.165-.97-.495-1.35-.33-.38-.756-.57-1.28-.57zm6.4 0c-.524 0-.95.19-1.28.57-.33.38-.495.83-.495 1.35 0 .52.165.97.495 1.35.33.38.756.57 1.28.57.524 0 .95-.19 1.28-.57.33-.38.495-.83.495-1.35 0-.52-.165-.97-.495-1.35-.33-.38-.756-.57-1.28-.57z"/></svg>
             </div>
             <div className="flex flex-col">
               <span className="text-[13px] font-bold text-slate-800 dark:text-slate-200 line-clamp-1">{text}</span>
               <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">点击前往 Bilibili 观看视频</span>
             </div>
          </a>
        );
      } else {
        parts.push(
          <a key={key++} href={url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
            {text}
          </a>
        );
      }
      remaining = remaining.slice(linkIndex + linkMatch[0].length);
    }
  }

  return <>{parts}</>;
}

function InlineLatex({ content }: { content: string }) {
  const segments = parseLatex(content);
  return (
    <>
      {segments.map((segment, index) => {
        if (segment.type === "inline-math") {
          return (
            <span key={index} dangerouslySetInnerHTML={{ __html: renderLatex(segment.content, false) }} />
          );
        }
        if (segment.type === "display-math") {
          return <MathDisplayBlock key={index} content={segment.content} />;
        }
        return <span key={index}>{renderMarkdownInline(segment.content)}</span>;
      })}
    </>
  );
}

function renderBlock(block: Block, blockIndex: number, complete: boolean): React.ReactNode {
  switch (block.type) {
    case "table":
      return <div key={`table-${blockIndex}`} className="my-3 max-w-full overflow-x-auto"><table className="w-full border-collapse text-sm">
        <thead><tr>{block.headers.map((cell, index) => <th key={index} className="border border-[var(--border-primary)] bg-[var(--bg-tertiary)] p-2 text-left"><InlineLatex content={cell} /></th>)}</tr></thead>
        <tbody>{block.rows.map((row, index) => <tr key={index}>{block.headers.map((_, col) => <td key={col} className="border border-[var(--border-primary)] p-2"><InlineLatex content={row[col] ?? ""} /></td>)}</tr>)}</tbody>
      </table></div>;
    case "h1":
      return (
        <h1 key={`h1-${blockIndex}`} className="mt-6 mb-3 text-xl font-bold text-[var(--text-primary)]">
          <InlineLatex content={block.content} />
        </h1>
      );
    case "h2":
      return (
        <h2 key={`h2-${blockIndex}`} className="mt-5 mb-2 text-lg font-bold text-[var(--text-primary)]">
          <InlineLatex content={block.content} />
        </h2>
      );
    case "h3":
      return (
        <h3 key={`h3-${blockIndex}`} className="mt-4 mb-2 text-base font-bold text-[var(--text-primary)]">
          <InlineLatex content={block.content} />
        </h3>
      );
    case "h4":
      return (
        <h4 key={`h4-${blockIndex}`} className="mt-3 mb-1.5 text-sm font-bold font-title tracking-wider text-olive-600 dark:text-olive-400">
          <InlineLatex content={block.content} />
        </h4>
      );
    case "ul":
      return (
        <ul key={`ul-${blockIndex}`} className="ml-4 list-disc">
          {block.items.map((item, itemIndex) => (
            <li key={`ul-${blockIndex}-${itemIndex}`}>
              <InlineLatex content={item} />
            </li>
          ))}
        </ul>
      );
    case "ol":
      return (
        <ol key={`ol-${blockIndex}`} className="ml-4 list-decimal">
          {block.items.map((item, itemIndex) => (
            <li key={`ol-${blockIndex}-${itemIndex}`}>
              <InlineLatex content={item} />
            </li>
          ))}
        </ol>
      );
    case "blockquote":
      return (
        <blockquote key={`bq-${blockIndex}`} className="border-l-4 border-[var(--border-primary)] pl-4 text-[var(--text-secondary)]">
          <InlineLatex content={block.content} />
        </blockquote>
      );
    case "hr":
      return <hr key={`hr-${blockIndex}`} className="my-4 border-[var(--border-primary)]" />;
    case "br":
      return <br key={`br-${blockIndex}`} />;
    case "display-math":
      return <MathDisplayBlock key={`dm-${blockIndex}`} content={block.content} />;
    case "code-block":
      return <CodeBlock key={`cb-${blockIndex}`} language={block.language} content={block.content} ready={complete && block.closed} />;
    case "plot":
      return <MathPlot key={`plot-${blockIndex}`} function={block.function} domain={block.domain} />;
    case "bilibili-search":
      return <VideoRecommend key={`bili-${blockIndex}`} keyword={block.keyword} />;
    case "html":
      return <StaticArtifact key={`html-${blockIndex}`} content={block.content} ready={complete && block.closed} />;
    case "paragraph":
      return (
        <p key={`p-${blockIndex}`} className="my-1">
          {block.lines.map((line, lineIndex) => (
            <span key={`p-${blockIndex}-${lineIndex}`}>
              <InlineLatex content={line} />
              {lineIndex < block.lines.length - 1 && <br />}
            </span>
          ))}
        </p>
      );
    default:
      return null;
  }
}

export function LatexRenderer({ content, complete = true }: { content: string; complete?: boolean }) {
  const blocks = parseBlocks(content.split("\n"));
  return (
    <div className="message-prose min-w-0 max-w-full break-words whitespace-pre-wrap leading-7">
      {blocks.map((block, blockIndex) => renderBlock(block, blockIndex, complete))}
    </div>
  );
}
