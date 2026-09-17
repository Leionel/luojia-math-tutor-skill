"use client";

import React, { useMemo } from "react";
import katex from "katex";

interface MathViewProps {
  math: string;
  display?: boolean;
  className?: string;
}

export function MathView({ math, display = false, className = "" }: MathViewProps) {
  const html = useMemo(() => {
    if (!math) return "";
    try {
      return katex.renderToString(math.trim(), {
        displayMode: display,
        throwOnError: false,
        strict: false,
      });
    } catch {
      return math;
    }
  }, [math, display]);

  if (!html) return null;

  return (
    <span
      className={`katex-container ${display ? "block my-2 overflow-x-auto text-center" : "inline"} ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

interface MathMarkdownProps {
  content: string;
  className?: string;
}

export function MathMarkdown({ content, className = "" }: MathMarkdownProps) {
  const rendered = useMemo(() => {
    if (!content) return "";

    const mathSlots: string[] = [];

    // 1. Extract $$...$$ display math blocks
    let text = content.replace(/\$\$([\s\S]+?)\$\$/g, (_, eq) => {
      try {
        const html = katex.renderToString(eq.trim(), {
          displayMode: true,
          throwOnError: false,
          strict: false,
        });
        const idx = mathSlots.length;
        mathSlots.push(
          `<div class="katex-block my-2.5 py-1 text-center overflow-x-auto text-indigo-950 dark:text-indigo-100 font-serif">${html}</div>`
        );
        return `___MATH_SLOT_${idx}___`;
      } catch {
        return eq;
      }
    });

    // 2. Extract $...$ inline math
    text = text.replace(/\$([^\$\n]+?)\$/g, (_, eq) => {
      try {
        const html = katex.renderToString(eq.trim(), {
          displayMode: false,
          throwOnError: false,
          strict: false,
        });
        const idx = mathSlots.length;
        mathSlots.push(
          `<span class="katex-inline text-indigo-900 dark:text-indigo-200 mx-0.5 font-serif">${html}</span>`
        );
        return `___MATH_SLOT_${idx}___`;
      } catch {
        return eq;
      }
    });

    // 3. Parse Markdown bold: **text** -> strong
    text = text.replace(
      /\*\*(.+?)\*\*/g,
      '<strong class="font-bold text-slate-900 dark:text-slate-100">$1</strong>'
    );

    // 4. Parse Markdown italics: *text* -> em
    text = text.replace(
      /(?<!\*)\*([^*]+?)\*(?!\*)/g,
      '<em class="italic text-slate-800 dark:text-slate-200">$1</em>'
    );

    // 5. Parse line breaks (\n -> <br />)
    text = text.replace(/\n/g, '<br />');

    // 6. Restore KaTeX math slots
    text = text.replace(/___MATH_SLOT_(\d+)___/g, (_, idx) => {
      return mathSlots[parseInt(idx, 10)] || "";
    });

    return text;
  }, [content]);

  return (
    <div
      className={`text-xs text-slate-700 dark:text-slate-200 leading-relaxed break-words ${className}`}
      dangerouslySetInnerHTML={{ __html: rendered }}
    />
  );
}
