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
    // Replace $$...$$ with block math
    let text = content.replace(/\$\$([\s\S]+?)\$\$/g, (_, eq) => {
      try {
        return `<div class="katex-block my-2 text-center overflow-x-auto">${katex.renderToString(eq.trim(), { displayMode: true, throwOnError: false })}</div>`;
      } catch {
        return eq;
      }
    });
    // Replace $...$ with inline math
    text = text.replace(/\$([^\$\n]+?)\$/g, (_, eq) => {
      try {
        return `<span class="katex-inline">${katex.renderToString(eq.trim(), { displayMode: false, throwOnError: false })}</span>`;
      } catch {
        return eq;
      }
    });
    return text;
  }, [content]);

  return (
    <div
      className={`text-xs text-slate-600 dark:text-slate-300 leading-relaxed ${className}`}
      dangerouslySetInnerHTML={{ __html: rendered }}
    />
  );
}
