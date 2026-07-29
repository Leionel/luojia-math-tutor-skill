"use client";

import { useState } from "react";

export interface SourceSpan {
  source_document_id?: string;
  page_start?: number;
  page_end?: number;
  quote?: string;
  id?: string;
}

export function SourceSpanCard({ sourceSpan, className = "" }: { sourceSpan: SourceSpan; className?: string }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sourceSpan) return null;

  const displayLabel = sourceSpan.id || (sourceSpan.page_start ? `P.${sourceSpan.page_start}` : "来源");
  const title = `📖 来源 ${displayLabel}`;

  return (
    <span className={`inline-block relative ${className}`}>
      {!isExpanded ? (
        <sup
          onClick={() => setIsExpanded(true)}
          className="cursor-pointer text-[10px] font-bold text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 ml-0.5 px-1 rounded-sm bg-amber-100/50 dark:bg-amber-900/30 transition-colors"
          title="点击查看原文出处"
        >
          [{displayLabel}]
        </sup>
      ) : (
        <div 
          className="relative block mt-2 mb-2 bg-amber-50 dark:bg-[#2a2416] border border-amber-200 dark:border-amber-800/50 rounded-lg p-4 shadow-sm max-w-lg cursor-pointer transition-all hover:shadow-md"
          onClick={() => setIsExpanded(false)}
        >
          <div className="absolute top-2 right-2 text-amber-400 hover:text-amber-600 dark:text-amber-600 dark:hover:text-amber-400">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </div>
          <h4 className="text-xs font-semibold text-amber-800 dark:text-amber-500 uppercase tracking-wider mb-2">
            {title}
          </h4>
          {sourceSpan.quote ? (
            <blockquote className="text-sm text-amber-900 dark:text-amber-200/90 border-l-2 border-amber-400 dark:border-amber-700 pl-3 py-1 font-serif leading-relaxed">
              &quot;{sourceSpan.quote}&quot;
            </blockquote>
          ) : (
            <div className="text-sm text-amber-700 dark:text-amber-500/70 italic">
              （未提供原文摘录）
            </div>
          )}
          <div className="mt-2 text-[10px] text-amber-600/60 dark:text-amber-500/40 text-right">
            点击卡片任意位置收起
          </div>
        </div>
      )}
    </span>
  );
}
