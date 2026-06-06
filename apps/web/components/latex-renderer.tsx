"use client";

import katex from "katex";
import { Copy, Check, Eye, Code } from "lucide-react";
import { useState } from "react";
import { MathPlot } from "./math-plot";
import { VideoRecommend } from "./video-recommend";

function CodeBlock({ language, content }: { language: string; content: string }) {
  const [copied, setCopied] = useState(false);
  const [mode, setMode] = useState<"code" | "preview">("preview");
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const isHtml = language?.toLowerCase() === "html" || language?.toLowerCase() === "xml";

  return (
    <div className="my-4 rounded-xl overflow-hidden bg-[#0d1117] border border-[#30363d] shadow-lg">
      <div className="flex items-center justify-between px-4 py-2 bg-[#161b22] border-b border-[#30363d]">
        <div className="flex items-center gap-4">
          <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">{language || "text"}</span>
          {isHtml && (
            <div className="flex items-center bg-[#0d1117] rounded p-0.5 border border-[#30363d]">
               <button onClick={() => setMode("preview")} className={`px-2 py-1 text-xs rounded-sm transition-colors flex items-center gap-1.5 ${mode === "preview" ? "bg-[#21262d] text-cyan-400 font-medium" : "text-slate-500 hover:text-slate-300"}`}>
                 <Eye className="w-3.5 h-3.5"/> Preview
               </button>
               <button onClick={() => setMode("code")} className={`px-2 py-1 text-xs rounded-sm transition-colors flex items-center gap-1.5 ${mode === "code" ? "bg-[#21262d] text-cyan-400 font-medium" : "text-slate-500 hover:text-slate-300"}`}>
                 <Code className="w-3.5 h-3.5"/> Source
               </button>
            </div>
          )}
        </div>
        <button onClick={handleCopy} className="text-slate-400 hover:text-slate-200 transition-colors" title="Copy code">
          {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
        </button>
      </div>
      {isHtml && mode === "preview" ? (
        <iframe 
          className="w-full bg-white border-none min-h-[300px]" 
          sandbox="allow-scripts" 
          srcDoc={`<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>${content}</body></html>`} 
          title="HTML Preview"
        />
      ) : (
        <div className="p-4 overflow-x-auto text-[13px] font-mono leading-relaxed text-slate-300 selection:bg-cyan-500/30">
          <pre><code>{content}</code></pre>
        </div>
      )}
    </div>
  );
}

function renderLatex(value: string, displayMode = false) {
  try {
    return katex.renderToString(value, { displayMode, throwOnError: false });
  } catch {
    return value;
  }
}

type Segment =
  | { type: "text"; content: string }
  | { type: "inline-math"; content: string }
  | { type: "display-math"; content: string };

function parseLatex(content: string): Segment[] {
  const segments: Segment[] = [];
  let remaining = content;

  while (remaining.length > 0) {
    const displayBlockRegex = /\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]/;
    const inlineRegex = /\\\(([\s\S]+?)\\\)|\$([^\$]+?)\$/;

    const displayMatch = remaining.match(displayBlockRegex);
    const inlineMatch = remaining.match(inlineRegex);

    const displayIndex = displayMatch?.index ?? Infinity;
    const inlineIndex = inlineMatch?.index ?? Infinity;

    if (displayIndex === Infinity && inlineIndex === Infinity) {
      segments.push({ type: "text", content: remaining });
      remaining = "";
      continue;
    }

    if (displayIndex < inlineIndex) {
      const match = displayMatch!;
      const beforeText = remaining.slice(0, match.index);
      if (beforeText) {
        segments.push({ type: "text", content: beforeText });
      }

      const latex = match[1] ?? match[2] ?? "";
      segments.push({ type: "display-math", content: latex });
      remaining = remaining.slice(match.index! + match[0].length);
    } else {
      const match = inlineMatch!;
      const beforeText = remaining.slice(0, match.index);
      if (beforeText) {
        segments.push({ type: "text", content: beforeText });
      }

      const latex = match[1] ?? match[2] ?? "";
      segments.push({ type: "inline-math", content: latex });
      remaining = remaining.slice(match.index! + match[0].length);
    }
  }

  return segments;
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

    const boldIndex = boldMatch?.index ?? Infinity;
    const italicIndex = italicMatch?.index ?? Infinity;
    const codeIndex = codeMatch?.index ?? Infinity;
    const imageIndex = imageMatch?.index ?? Infinity;
    const linkIndex = linkMatch?.index ?? Infinity;

    const minIndex = Math.min(boldIndex, italicIndex, codeIndex, imageIndex, linkIndex);

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
    } else if (codeIndex === minIndex && codeMatch) {
      const before = remaining.slice(0, codeIndex);
      if (before) parts.push(<span key={key++}>{before}</span>);
      parts.push(
        <code key={key++} className="rounded bg-slate-100 px-1.5 py-0.5 text-sm font-mono text-slate-800">
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.slice(codeIndex + codeMatch[0].length);
    } else if (imageIndex === minIndex && imageMatch) {
      const before = remaining.slice(0, imageIndex);
      if (before) parts.push(<span key={key++}>{before}</span>);
      const imgSrc = imageMatch[2].startsWith("/api") ? `http://127.0.0.1:8000${imageMatch[2]}` : imageMatch[2];
      parts.push(
        <img key={key++} src={imgSrc} alt={imageMatch[1]} className="max-w-full rounded-lg border border-[var(--border-subtle)] shadow-sm my-2 object-cover" />
      );
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
          return (
            <div
              key={index}
              className="math-block my-2"
              dangerouslySetInnerHTML={{ __html: renderLatex(segment.content, true) }}
            />
          );
        }
        return <span key={index}>{renderMarkdownInline(segment.content)}</span>;
      })}
    </>
  );
}

type Block =
  | { type: "h1"; content: string }
  | { type: "h2"; content: string }
  | { type: "h3"; content: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "blockquote"; content: string }
  | { type: "hr" }
  | { type: "br" }
  | { type: "display-math"; content: string }
  | { type: "code-block"; language: string; content: string }
  | { type: "plot"; function: string; domain?: string }
  | { type: "bilibili-search"; keyword: string }
  | { type: "html"; content: string }
  | { type: "paragraph"; lines: string[] };

function parseBlocks(lines: string[]): Block[] {
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("### ")) {
      blocks.push({ type: "h3", content: line.slice(4) });
      i++;
    } else if (line.startsWith("## ")) {
      blocks.push({ type: "h2", content: line.slice(3) });
      i++;
    } else if (line.startsWith("# ")) {
      blocks.push({ type: "h1", content: line.slice(2) });
      i++;
    } else if (line.startsWith("- ") || line.startsWith("* ")) {
      const items: string[] = [];
      while (i < lines.length && (lines[i].startsWith("- ") || lines[i].startsWith("* "))) {
        items.push(lines[i].slice(2));
        i++;
      }
      blocks.push({ type: "ul", items });
    } else if (/^\d+\.\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        const match = lines[i].match(/^(\d+)\.\s(.*)/);
        if (match) items.push(match[2]);
        i++;
      }
      blocks.push({ type: "ol", items });
    } else if (line.startsWith("> ")) {
      blocks.push({ type: "blockquote", content: line.slice(2) });
      i++;
    } else if (line.startsWith("---") || line.startsWith("***")) {
      blocks.push({ type: "hr" });
      i++;
    } else if (/^\\\[/.test(line.trim()) && !/\\\\\[/.test(line.trim())) {
      const endMarker = "\\]";
      const startMarker = "\\[";
      
      const mathLines: string[] = [];
      const firstLine = line.trim();
      const afterStart = firstLine.slice(startMarker.length).trim();
      if (afterStart && afterStart !== endMarker) {
        mathLines.push(afterStart);
      }
      i++;
      
      while (i < lines.length) {
        const currentLine = lines[i];
        const trimmed = currentLine.trim();
        if (trimmed === endMarker) {
          i++;
          break;
        }
        if (trimmed.endsWith(endMarker) && !trimmed.endsWith("\\\\]")) {
          const beforeEnd = trimmed.slice(0, -endMarker.length).trim();
          if (beforeEnd) {
            mathLines.push(beforeEnd);
          }
          i++;
          break;
        }
        mathLines.push(currentLine);
        i++;
      }
      
      blocks.push({ type: "display-math", content: mathLines.join("\n") });
    } else if (/^\$\$/.test(line.trim())) {
      const endMarker = "$$";
      const startMarker = "$$";
      
      const mathLines: string[] = [];
      const firstLine = line.trim();
      const afterStart = firstLine.slice(startMarker.length).trim();
      if (afterStart && afterStart !== endMarker) {
        mathLines.push(afterStart);
      }
      i++;
      
      while (i < lines.length) {
        const currentLine = lines[i];
        const trimmed = currentLine.trim();
        if (trimmed === endMarker) {
          i++;
          break;
        }
        if (trimmed.endsWith(endMarker)) {
          const beforeEnd = trimmed.slice(0, -endMarker.length).trim();
          if (beforeEnd) {
            mathLines.push(beforeEnd);
          }
          i++;
          break;
        }
        mathLines.push(currentLine);
        i++;
      }
      
      blocks.push({ type: "display-math", content: mathLines.join("\n") });
    } else if (line.startsWith("```")) {
      const language = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) i++;
      blocks.push({ type: "code-block", language, content: codeLines.join("\n") });
    } else if (line.trim() === "") {
      blocks.push({ type: "br" });
      i++;
    } else if (line.trim().startsWith("<plot ")) {
      const matchFn = line.match(/function="([^"]+)"/);
      const matchDomain = line.match(/domain="([^"]+)"/);
      if (matchFn) {
        blocks.push({ type: "plot", function: matchFn[1], domain: matchDomain?.[1] });
      }
      i++;
    } else if (line.trim().startsWith("<bilibili-search ")) {
      const matchKw = line.match(/keyword="([^"]+)"/);
      if (matchKw) {
        blocks.push({ type: "bilibili-search", keyword: matchKw[1] });
      }
      i++;
    } else if (/^<\/?(?:div|table|tbody|thead|tr|td|th|svg|ul|ol|li|h[1-6]|p|details|summary|section|article|nav|header|footer|main|aside|span)(?:>|\s)/i.test(line.trim())) {
      const htmlLines: string[] = [];
      while (i < lines.length && lines[i].trim() !== "") {
        htmlLines.push(lines[i]);
        i++;
      }
      blocks.push({ type: "html", content: htmlLines.join("\n") });
    } else {
      const paragraphLines: string[] = [];
      while (
        i < lines.length &&
        !lines[i].startsWith("# ") &&
        !lines[i].startsWith("## ") &&
        !lines[i].startsWith("### ") &&
        !lines[i].startsWith("- ") &&
        !lines[i].startsWith("* ") &&
        !/^\d+\.\s/.test(lines[i]) &&
        !lines[i].startsWith("> ") &&
        !lines[i].startsWith("---") &&
        !lines[i].startsWith("***") &&
        !/^\\\[/.test(lines[i].trim()) &&
        !/^\$\$/.test(lines[i].trim()) &&
        !lines[i].startsWith("```") &&
        !/^<\/?(?:div|table|tbody|thead|tr|td|th|svg|ul|ol|li|h[1-6]|p|details|summary|section|article|nav|header|footer|main|aside|span)(?:>|\s)/i.test(lines[i].trim()) &&
        lines[i].trim() !== ""
      ) {
        paragraphLines.push(lines[i]);
        i++;
      }
      if (paragraphLines.length > 0) {
        blocks.push({ type: "paragraph", lines: paragraphLines });
      }
    }
  }

  return blocks;
}

function renderBlock(block: Block, blockIndex: number): React.ReactNode {
  switch (block.type) {
    case "h1":
      return (
        <h1 key={`h1-${blockIndex}`} className="mt-6 mb-3 text-xl font-bold text-slate-900">
          <InlineLatex content={block.content} />
        </h1>
      );
    case "h2":
      return (
        <h2 key={`h2-${blockIndex}`} className="mt-5 mb-2 text-lg font-bold text-slate-900">
          <InlineLatex content={block.content} />
        </h2>
      );
    case "h3":
      return (
        <h3 key={`h3-${blockIndex}`} className="mt-4 mb-2 text-base font-bold text-slate-900">
          <InlineLatex content={block.content} />
        </h3>
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
        <blockquote key={`bq-${blockIndex}`} className="border-l-4 border-slate-300 pl-4 text-slate-600">
          <InlineLatex content={block.content} />
        </blockquote>
      );
    case "hr":
      return <hr key={`hr-${blockIndex}`} className="my-4 border-slate-200" />;
    case "br":
      return <br key={`br-${blockIndex}`} />;
    case "display-math":
      return (
        <div
          key={`dm-${blockIndex}`}
          className="math-block my-3 overflow-x-auto"
          dangerouslySetInnerHTML={{ __html: renderLatex(block.content, true) }}
        />
      );
    case "code-block":
      return <CodeBlock key={`cb-${blockIndex}`} language={block.language} content={block.content} />;
    case "plot":
      return <MathPlot key={`plot-${blockIndex}`} function={block.function} domain={block.domain} />;
    case "bilibili-search":
      return <VideoRecommend key={`bili-${blockIndex}`} keyword={block.keyword} />;
    case "html": {
      const safeContent = block.content
        .replace(/<style[\s\S]*?<\/style>/gi, "")
        .replace(/<script[\s\S]*?<\/script>/gi, "");
      return (
        <div 
          key={`html-${blockIndex}`} 
          className="my-3 overflow-x-auto html-container"
          dangerouslySetInnerHTML={{ __html: safeContent }} 
        />
      );
    }
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

export function LatexRenderer({ content }: { content: string }) {
  const blocks = parseBlocks(content.split("\n"));
  return (
    <div className="message-prose whitespace-pre-wrap leading-7">
      {blocks.map((block, blockIndex) => renderBlock(block, blockIndex))}
    </div>
  );
}
