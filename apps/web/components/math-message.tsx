"use client";

import { useState, useEffect } from "react";
import { LatexRenderer } from "./latex-renderer";
import { ReviewCard, type ReviewData } from "./review-card";
import { motion, AnimatePresence } from "framer-motion";
import { BrainCircuit, ChevronRight, CheckCircle2, CircleDashed, Copy, Edit2, RefreshCcw, Volume2, VolumeX, Search, Terminal, Cpu, ListChecks } from "lucide-react";
import { cn } from "@/lib/utils";

function cleanMathForSpeech(text: string) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "$1") // bold
    .replace(/\*(.*?)\*/g, "$1")     // italic
    .replace(/\\frac{([^}]+)}{([^}]+)}/g, "$2分之$1")
    .replace(/\\int/g, "积分")
    .replace(/\\to/g, "趋向于")
    .replace(/\\infty/g, "无穷大")
    .replace(/\$\$/g, "")
    .replace(/\$/g, "");
}

interface ThinkingStep {
  title: string;
  type: 'rag' | 'orchestrator' | 'sandbox' | 'result' | 'plan' | 'verify' | 'output' | 'correct' | 'generic';
  content: string;
}

function parseThinkingChain(text: string): ThinkingStep[] {
  const steps: ThinkingStep[] = [];
  if (!text) return steps;

  const pattern = /(\[(?:隐式 RAG|Orchestrator|沙箱执行|执行结果|PLAN|VERIFY|OUTPUT|CORRECT)\])/g;
  const stagePattern = /^\[(?:隐式 RAG|Orchestrator|沙箱执行|执行结果|PLAN|VERIFY|OUTPUT|CORRECT)\]$/;
  const parts = text.split(pattern);

  let currentTitle = "内部思考";
  let currentType: ThinkingStep['type'] = "generic";
  let currentContent = "";

  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    if (!part) continue;

    if (stagePattern.test(part)) {
      if (currentContent.trim()) {
        steps.push({
          title: currentTitle,
          type: currentType,
          content: currentContent.trim()
        });
      }
      currentTitle = part.replace(/[\[\]]/g, "");
      currentContent = "";

      if (part.includes("RAG")) currentType = "rag";
      else if (part.includes("Orchestrator")) currentType = "orchestrator";
      else if (part.includes("沙箱执行")) currentType = "sandbox";
      else if (part.includes("执行结果")) currentType = "result";
      else if (part.includes("PLAN")) currentType = "plan";
      else if (part.includes("VERIFY")) currentType = "verify";
      else if (part.includes("OUTPUT")) currentType = "output";
      else if (part.includes("CORRECT")) currentType = "correct";
      else currentType = "generic";
    } else {
      currentContent += part;
    }
  }

  if (currentContent.trim()) {
    steps.push({
      title: currentTitle,
      type: currentType,
      content: currentContent.trim()
    });
  }

  return steps;
}

function getStepIcon(type: ThinkingStep['type']) {
  switch (type) {
    case 'rag':
      return <Search className="w-3.5 h-3.5 text-blue-500" />;
    case 'orchestrator':
      return <BrainCircuit className="w-3.5 h-3.5 text-purple-500" />;
    case 'sandbox':
      return <Terminal className="w-3.5 h-3.5 text-amber-500" />;
    case 'result':
      return <Cpu className="w-3.5 h-3.5 text-emerald-500" />;
    case 'plan':
      return <ListChecks className="w-3.5 h-3.5 text-cyan-500" />;
    case 'verify':
      return <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />;
    case 'output':
      return <Cpu className="w-3.5 h-3.5 text-emerald-500" />;
    case 'correct':
      return <RefreshCcw className="w-3.5 h-3.5 text-red-500 animate-spin" style={{ animationDuration: '3s' }} />;
    default:
      return <ChevronRight className="w-3.5 h-3.5 text-slate-500" />;
  }
}

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
  const steps = parseThinkingChain(content);

  return (
    <div className="mt-3 border-t border-[var(--border-subtle)] pt-2">
      <button
        className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
        onClick={onToggle}
      >
        <ChevronRight className={cn("w-3.5 h-3.5 transition-transform duration-200", isExpanded && "rotate-90")} />
        <span className="font-medium">查看思考过程 ({steps.length} 步)</span>
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
            <div className="rounded-md bg-[var(--bg-tertiary)] backdrop-blur-sm p-4 text-xs leading-relaxed text-[var(--text-secondary)] border border-[var(--border-primary)] flex flex-col gap-4">
              <div className="relative pl-6 border-l border-slate-200 dark:border-slate-800 ml-2.5 flex flex-col gap-5 py-1">
                {steps.map((step, idx) => (
                  <div key={idx} className="relative">
                    <div className="absolute -left-[31px] top-0.5 w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center shadow-sm z-10">
                      {getStepIcon(step.type)}
                    </div>
                    <div className="font-semibold text-[var(--text-primary)] mb-1 flex items-center gap-2 select-none">
                      <span>{step.title}</span>
                      <span className="text-[10px] text-[var(--text-muted)] font-normal uppercase tracking-wider">
                        步骤 {idx + 1}
                      </span>
                    </div>
                    <div className="prose-xs text-[var(--text-secondary)] bg-white/40 dark:bg-black/10 rounded-lg p-2.5 border border-slate-100 dark:border-slate-800/50 mt-1 select-text">
                      <LatexRenderer content={step.content} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ThinkingSummaryView({ summary, elapsedMs, isExpanded, onToggle }: { summary: string; elapsedMs?: number; isExpanded: boolean; onToggle: () => void }) {
  const steps = parseThinkingChain(summary);

  return (
    <div className="mt-3 border-t border-[var(--border-subtle)] pt-2">
      <button
        className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
        onClick={onToggle}
      >
        <ChevronRight className={cn("w-3.5 h-3.5 transition-transform duration-200", isExpanded && "rotate-90")} />
        <span className="font-medium">
          查看思考过程
          {elapsedMs ? `（本轮思考约 ${elapsedMs >= 1000 ? `${(elapsedMs / 1000).toFixed(1)} 秒` : `${elapsedMs} 毫秒`}）` : ''}
          {steps.length > 0 && ` · ${steps.length} 步`}
        </span>
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
            <div className="rounded-md bg-[var(--bg-tertiary)] backdrop-blur-sm p-4 text-xs leading-relaxed text-[var(--text-secondary)] border border-[var(--border-primary)] flex flex-col gap-4">
              <div className="relative pl-6 border-l border-slate-200 dark:border-slate-800 ml-2.5 flex flex-col gap-5 py-1">
                {steps.length > 0 ? (
                  steps.map((step, idx) => (
                    <div key={idx} className="relative">
                      <div className="absolute -left-[31px] top-0.5 w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center shadow-sm z-10">
                        {getStepIcon(step.type)}
                      </div>
                      <div className="font-semibold text-[var(--text-primary)] mb-1 flex items-center gap-2 select-none">
                        <span>{step.title}</span>
                        <span className="text-[10px] text-[var(--text-muted)] font-normal uppercase tracking-wider">
                          步骤 {idx + 1}
                        </span>
                      </div>
                      <div className="prose-xs text-[var(--text-secondary)] bg-white/40 dark:bg-black/10 rounded-lg p-2.5 border border-slate-100 dark:border-slate-800/50 mt-1 select-text">
                        <LatexRenderer content={step.content} />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-[var(--text-muted)] italic">{summary}</div>
                )}
              </div>
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
  thinkingSummary,
  thinkingElapsedMs,
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
  thinkingSummary?: string;
  thinkingElapsedMs?: number;
  reviewData?: ReviewData | null;
  onSimilar?: () => void;
  onEdit?: () => void;
  onRetry?: () => void;
}) {
  const isUser = role === "user";
  const [isChainExpanded, setIsChainExpanded] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  const playSpeech = () => {
    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      return;
    }

    const cleanedText = cleanMathForSpeech(content);
    const utterance = new SpeechSynthesisUtterance(cleanedText);
    utterance.lang = 'zh-CN';
    utterance.onend = () => setIsPlaying(false);
    utterance.onerror = () => setIsPlaying(false);

    setIsPlaying(true);
    window.speechSynthesis.speak(utterance);
  };

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
        <>
          {isThinking && (
            <ThinkingIndicator elapsed={thinkingElapsed} />
          )}
          
          {thinkingChain && (
            <div className={cn(isThinking ? "mt-2 mb-2" : "mb-2")}>
              <ThinkingChain
                content={thinkingChain}
                isExpanded={isThinking ? true : isChainExpanded}
                onToggle={() => setIsChainExpanded(!isChainExpanded)}
              />
            </div>
          )}

          {!isThinking && thinkingSummary && (
            <div className="mb-2">
              <ThinkingSummaryView
                summary={thinkingSummary}
                elapsedMs={thinkingElapsedMs}
                isExpanded={isChainExpanded}
                onToggle={() => setIsChainExpanded(!isChainExpanded)}
              />
            </div>
          )}

          {content && (
            <div className={cn("prose-sm sm:prose max-w-none prose-neutral dark:prose-invert prose-p:leading-relaxed prose-pre:bg-[var(--bg-tertiary)] prose-pre:border prose-pre:border-[var(--border-primary)]", isUser ? "text-white prose-p:text-white" : "text-[var(--text-primary)]", (isThinking || thinkingChain) ? "mt-3 pt-3 border-t border-[var(--border-subtle)]" : "")}>
              <LatexRenderer content={content} />
            </div>
          )}
            
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
              {!isUser && (
                <button
                  onClick={playSpeech}
                  className={cn(
                    "flex items-center gap-1 text-[10px] font-medium transition-opacity",
                    isPlaying ? "text-emerald-500 opacity-100" : "text-inherit opacity-70 hover:opacity-100"
                  )}
                  title={isPlaying ? "停止播放" : "朗读"}
                >
                  {isPlaying ? <VolumeX className="w-3 h-3" /> : <Volume2 className="w-3 h-3" />}
                  <span className="hidden sm:inline">{isPlaying ? "停止" : "朗读"}</span>
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
      </div>
    </motion.div>
  );
}
