"use client";

import { useState, useEffect } from "react";
import { LatexRenderer } from "./latex-renderer";
import { ReviewCard, type ReviewData } from "./review-card";
import { motion, AnimatePresence } from "framer-motion";
import { BrainCircuit, ChevronRight, CheckCircle2, CircleDashed, Copy, Edit2, RefreshCcw } from "lucide-react";
import { cn } from "@/lib/utils";

function ThinkingIndicator({ elapsed }: { elapsed: number }) {
  const dots = ".".repeat((elapsed % 3) + 1);
  return (
    <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)] font-medium">
      <BrainCircuit className="w-4 h-4 text-emerald-500 animate-pulse" />
      <span>思考中（已耗时 {elapsed} 秒）{dots}</span>
    </div>
  );
}

function ThinkingChain({ content, isExpanded, onToggle }: { content: string; isExpanded: boolean; onToggle: () => void }) {
  if (!content) return null;
  return (
    <div className="mt-3 border-t border-[var(--border-subtle)] pt-2">
      <button
        className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
        onClick={onToggle}
      >
        <ChevronRight className={cn("w-3.5 h-3.5 transition-transform duration-200", isExpanded && "rotate-90")} />
        <span className="font-medium">查看思考过程</span>
      </button>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden mt-2"
          >
            <div className="rounded-md bg-[var(--bg-tertiary)] backdrop-blur-sm p-3 text-xs leading-relaxed text-[var(--text-secondary)] border border-[var(--border-primary)]">
              <LatexRenderer content={content} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function MathMessage({
  role,
  content,
  status,
  isThinking = false,
  thinkingElapsed = 0,
  thinkingChain = "",
  reviewData,
  onSimilar,
  onEdit,
  onRetry,
}: {
  role: "user" | "assistant";
  content: string;
  status?: string;
  isThinking?: boolean;
  thinkingElapsed?: number;
  thinkingChain?: string;
  reviewData?: ReviewData | null;
  onSimilar?: () => void;
  onEdit?: () => void;
  onRetry?: () => void;
}) {
  const isUser = role === "user";
  const [isChainExpanded, setIsChainExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 15, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      className={cn("flex w-full mb-4", isUser ? "justify-end" : "justify-start")}
    >
      <div
        className={cn(
          "max-w-[85%] sm:max-w-[75%] rounded-3xl px-6 py-5 shadow-bubble transition-all duration-300 border",
          isUser
            ? "rounded-tr-sm border-[var(--border-accent)] text-white shadow-[0_4px_20px_var(--accent-light)]"
            : "rounded-tl-sm border-[var(--border-primary)] bg-white dark:bg-[var(--bg-assistant-bubble)] text-[var(--text-primary)] shadow-sm"
        )}
        style={isUser ? { background: 'var(--bg-user-bubble)' } : undefined}
      >
        {isThinking ? (
          <ThinkingIndicator elapsed={thinkingElapsed} />
        ) : (
          <>
            <div className={cn("prose-sm sm:prose max-w-none prose-neutral dark:prose-invert prose-p:leading-relaxed prose-pre:bg-[var(--bg-tertiary)] prose-pre:border prose-pre:border-[var(--border-primary)]", isUser ? "text-white prose-p:text-white" : "text-[var(--text-primary)]")}>
              <LatexRenderer content={content} />
            </div>
            
            <ThinkingChain
              content={thinkingChain}
              isExpanded={isChainExpanded}
              onToggle={() => setIsChainExpanded(!isChainExpanded)}
            />
            
            {status && !isUser ? (
              <div className="mt-3 flex items-center gap-1.5 border-t border-[var(--border-subtle)] pt-3 text-[11px] font-medium text-[var(--text-muted)]">
                {status.includes("未完成") ? <CircleDashed className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />}
                {status}
              </div>
            ) : null}

            {reviewData && !isUser ? (
              <div className="mt-3 pt-2">
                <ReviewCard data={reviewData} onSimilar={onSimilar} />
              </div>
            ) : null}

            {/* Action Bar */}
            <div className={cn("flex items-center gap-2 mt-4 pt-2 border-t", isUser ? "border-white/20 justify-end" : "border-[var(--border-subtle)] justify-start")}>
              <button
                onClick={() => navigator.clipboard.writeText(content)}
                className="flex items-center gap-1 text-[10px] font-medium text-inherit opacity-70 hover:opacity-100 transition-opacity"
                title="复制"
              >
                <Copy className="w-3 h-3" />
                <span className="hidden sm:inline">复制</span>
              </button>
              {isUser && onEdit && (
                <button
                  onClick={onEdit}
                  className="flex items-center gap-1 text-[10px] font-medium text-inherit opacity-70 hover:opacity-100 transition-opacity"
                  title="编辑"
                >
                  <Edit2 className="w-3 h-3" />
                  <span className="hidden sm:inline">编辑</span>
                </button>
              )}
              {!isUser && onRetry && (
                <button
                  onClick={onRetry}
                  className="flex items-center gap-1 text-[10px] font-medium text-inherit opacity-70 hover:opacity-100 transition-opacity"
                  title="重新生成"
                >
                  <RefreshCcw className="w-3 h-3" />
                  <span className="hidden sm:inline">重试</span>
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
}
