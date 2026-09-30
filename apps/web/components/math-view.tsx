"use client";

import React, { useMemo } from "react";
import katex from "katex";
import { LatexRenderer } from "./latex-renderer";
import { balancedLatex } from "@/lib/latex-balance";

interface MathViewProps {
  math: string;
  display?: boolean;
  className?: string;
}

export function MathView({ math, display = false, className = "" }: MathViewProps) {
  const html = useMemo(() => {
    if (!math) return "";
    try {
      return katex.renderToString(balancedLatex(math.trim()), {
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

// Thin wrapper over the shared renderer so candidate text and chat messages
// parse markdown/LaTeX through one code path.
export function MathMarkdown({ content, className = "" }: MathMarkdownProps) {
  return (
    <div className={`text-sm text-slate-700 dark:text-slate-200 leading-relaxed break-words ${className}`}>
      <LatexRenderer content={content || ""} />
    </div>
  );
}
