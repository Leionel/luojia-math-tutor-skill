"use client";

import { useState, useEffect } from "react";
import { LatexRenderer } from "./latex-renderer";
import { ReviewCard, type ReviewData } from "./review-card";
import { motion, AnimatePresence } from "framer-motion";
import { BrainCircuit, ChevronRight, CheckCircle2, CircleDashed, Copy, Edit2, RefreshCcw, Volume2, VolumeX, Search, Terminal, Cpu, ListChecks, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/lib/theme-context";

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

  const pattern = /(\[(?:🎯 解题策略分析|📚 知识点关联|🔍 步骤检查|💬 组织回答|Orchestrator|沙箱执行|执行结果|PLAN|VERIFY|OUTPUT|隐式 RAG|CORRECT)\])/g;
  const stagePattern = /^\[(?:🎯 解题策略分析|📚 知识点关联|🔍 步骤检查|💬 组织回答|Orchestrator|沙箱执行|执行结果|PLAN|VERIFY|OUTPUT|隐式 RAG|CORRECT)\]$/;
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

      if (part.includes("RAG") || part.includes("知识点关联")) currentType = "rag";
      else if (part.includes("Orchestrator")) currentType = "orchestrator";
      else if (part.includes("沙箱执行")) currentType = "sandbox";
      else if (part.includes("执行结果")) currentType = "result";
      else if (part.includes("PLAN") || part.includes("解题策略分析")) currentType = "plan";
      else if (part.includes("VERIFY") || part.includes("步骤检查")) currentType = "verify";
      else if (part.includes("OUTPUT") || part.includes("组织回答")) currentType = "output";
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

function displayThinkingTitle(title: string) {
  const labels: Record<string, string> = {
    PLAN: "解题策略分析",
    "隐式 RAG": "知识点关联",
    VERIFY: "步骤检查",
    OUTPUT: "组织回答",
  };
  return labels[title] || title;
}

function getStepIcon(type: ThinkingStep['type']) {
  switch (type) {
    case 'rag':
      return <Search className="w-3.5 h-3.5 text-[#4b5cc4]" />;
    case 'orchestrator':
      return <BrainCircuit className="w-3.5 h-3.5 text-[#7e4b52]" />;
    case 'sandbox':
      return <Terminal className="w-3.5 h-3.5 text-[#845a33]" />;
    case 'result':
      return <Cpu className="w-3.5 h-3.5 text-[#789262]" />;
    case 'plan':
      return <ListChecks className="w-3.5 h-3.5 text-[#5cb3cc]" />;
    case 'verify':
      return <CheckCircle2 className="w-3.5 h-3.5 text-[#728956]" />;
    case 'output':
      return <Cpu className="w-3.5 h-3.5 text-[#789262]" />;
    case 'correct':
      return <RefreshCcw className="w-3.5 h-3.5 text-[#c44a3d] animate-spin" style={{ animationDuration: '3s' }} />;
    default:
      return <ChevronRight className="w-3.5 h-3.5 text-[#757a6b]" />;
  }
}

function ThinkingIndicator({ elapsed }: { elapsed: number }) {
  const dots = ".".repeat((elapsed % 3) + 1);
  return (
    <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-olive-500/10 dark:bg-olive-400/15 border border-olive-500/20 text-xs text-olive-700 dark:text-olive-300 font-medium animate-pulse shadow-sm">
      <BrainCircuit className="w-3.5 h-3.5 text-olive-600 dark:text-olive-400 animate-spin" style={{ animationDuration: '4s' }} />
      <span>正在构建数理推导步骤（{elapsed}s）{dots}</span>
    </div>
  );
}

function ThinkingChain({ content, isExpanded, onToggle }: { content: string; isExpanded: boolean; onToggle: () => void }) {
  if (!content) return null;
  const steps = parseThinkingChain(content);

  return (
    <div className="mt-2.5 mb-2">
      <button
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] bg-[var(--bg-tertiary)]/70 hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] transition-all shadow-sm group"
        onClick={onToggle}
      >
        <ChevronRight className={cn("w-3.5 h-3.5 transition-transform duration-200 text-olive-600 dark:text-olive-400", isExpanded && "rotate-90")} />
        <span className="font-semibold text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">推导演绎链路</span>
        <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-olive-500/15 text-olive-700 dark:text-olive-300 font-mono">
          {steps.length} 个步骤
        </span>
      </button>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: -4 }}
            animate={{ opacity: 1, height: 'auto', y: 0 }}
            exit={{ opacity: 0, height: 0, y: -4 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="overflow-hidden mt-2"
          >
            <div className="rounded-xl bg-[var(--bg-tertiary)]/80 backdrop-blur-md p-4 text-xs leading-relaxed text-[var(--text-secondary)] border border-[var(--border-primary)] shadow-sm">
              <div className="relative pl-6 border-l-2 border-olive-500/25 dark:border-olive-400/20 ml-3 flex flex-col gap-4 py-1">
                {steps.map((step, idx) => (
                  <div key={idx} className="relative">
                    <div className="absolute -left-[32px] top-0.5 w-6 h-6 rounded-full bg-white dark:bg-[#20211d] border border-olive-500/30 flex items-center justify-center shadow-xs z-10">
                      {getStepIcon(step.type)}
                    </div>
                    <div className="font-semibold text-[var(--text-primary)] mb-1 flex items-center gap-2 select-none">
                      <span className="text-xs text-olive-800 dark:text-olive-200">{displayThinkingTitle(step.title)}</span>
                      <span className="text-[10px] text-[var(--text-muted)] font-mono uppercase tracking-wider px-1.5 py-0.2 rounded bg-black/5 dark:bg-white/5">
                        Stage {idx + 1}
                      </span>
                    </div>
                    <div className="text-[var(--text-secondary)] bg-white/60 dark:bg-black/25 rounded-lg p-3 border border-[var(--border-subtle)] mt-1.5 shadow-xs select-text">
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
    <div className="mt-2.5 mb-2">
      <button
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] bg-[var(--bg-tertiary)]/70 hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] transition-all shadow-sm group"
        onClick={onToggle}
      >
        <ChevronRight className={cn("w-3.5 h-3.5 transition-transform duration-200 text-olive-600 dark:text-olive-400", isExpanded && "rotate-90")} />
        <span className="font-semibold text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">查看推演过程</span>
        {elapsedMs ? (
          <span className="text-[10px] text-[var(--text-muted)] font-mono">
            {elapsedMs >= 1000 ? `${(elapsedMs / 1000).toFixed(1)}s` : `${elapsedMs}ms`}
          </span>
        ) : null}
        {steps.length > 0 && (
          <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-olive-500/15 text-olive-700 dark:text-olive-300 font-mono">
            {steps.length} 阶段
          </span>
        )}
      </button>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: -4 }}
            animate={{ opacity: 1, height: 'auto', y: 0 }}
            exit={{ opacity: 0, height: 0, y: -4 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="overflow-hidden mt-2"
          >
            <div className="rounded-xl bg-[var(--bg-tertiary)]/80 backdrop-blur-md p-4 text-xs leading-relaxed text-[var(--text-secondary)] border border-[var(--border-primary)] shadow-sm">
              <div className="relative pl-6 border-l-2 border-olive-500/25 dark:border-olive-400/20 ml-3 flex flex-col gap-4 py-1">
                {steps.length > 0 ? (
                  steps.map((step, idx) => (
                    <div key={idx} className="relative">
                      <div className="absolute -left-[32px] top-0.5 w-6 h-6 rounded-full bg-white dark:bg-[#20211d] border border-olive-500/30 flex items-center justify-center shadow-xs z-10">
                        {getStepIcon(step.type)}
                      </div>
                      <div className="font-semibold text-[var(--text-primary)] mb-1 flex items-center gap-2 select-none">
                        <span className="text-xs text-olive-800 dark:text-olive-200">{displayThinkingTitle(step.title)}</span>
                        <span className="text-[10px] text-[var(--text-muted)] font-mono uppercase tracking-wider px-1.5 py-0.2 rounded bg-black/5 dark:bg-white/5">
                          Stage {idx + 1}
                        </span>
                      </div>
                      <div className="text-[var(--text-secondary)] bg-white/60 dark:bg-black/25 rounded-lg p-3 border border-[var(--border-subtle)] mt-1.5 shadow-xs select-text">
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
  const { reading } = useTheme();
  const [isChainExpanded, setIsChainExpanded] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  const copyText = () => {
    navigator.clipboard.writeText(content);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

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
      initial={{ opacity: 0, y: 14, scale: 0.99 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 350, damping: 28 }}
      className={cn("flex w-full gap-3 sm:gap-4.5 mb-7 group", isUser ? "justify-end" : "justify-start")}
    >
      {/* Assistant Crest */}
      {!isUser && (
        <div className="shrink-0 mt-1 flex-col items-center hidden sm:flex">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-[#617a55] to-[#4e6344] text-white shadow-sm shadow-[#617a55]/20 border border-[#617a55]/40">
            <span className="font-title font-bold text-sm leading-none">珞</span>
          </div>
        </div>
      )}

      <div className={cn("flex flex-col min-w-0 max-w-full", isUser ? "items-end max-w-[85%] sm:max-w-[78%]" : "items-start flex-1")}>
        {/* Mobile Header indicator */}
        <div className="flex items-center gap-2 mb-1.5 sm:hidden">
          {isUser ? (
            <div className="flex items-center gap-1 text-[var(--text-muted)] text-[11px]">
              <span className="font-medium">我</span>
              <div className="flex h-4 w-4 items-center justify-center rounded-full bg-[var(--bg-tertiary)] border border-[var(--border-subtle)]"><User className="h-2.5 w-2.5" /></div>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-[var(--text-secondary)]">
              <div className="flex h-4 w-4 items-center justify-center rounded bg-[#617a55] text-white"><span className="font-title font-bold text-[9px]">珞</span></div>
              <span className="text-xs font-semibold font-title tracking-wide text-[#617a55] dark:text-[#879f7a]">珞珈数智</span>
            </div>
          )}
        </div>

        {/* Message Container / Bubble */}
        <div className={cn(
          "w-full transition-all duration-300",
          isUser 
            ? "bg-[#617a55] text-[#faf7f2] dark:bg-[#4e6344] px-4.5 py-3 rounded-2xl rounded-tr-xs shadow-sm font-sans" 
            : "text-[var(--text-primary)] bg-[var(--bg-card)]/80 dark:bg-[var(--bg-card)]/90 border border-[var(--border-subtle)] rounded-2xl p-4 sm:p-5 shadow-sm"
        )}>
          {isThinking && (
            <ThinkingIndicator elapsed={thinkingElapsed} />
          )}
          
          {thinkingChain && (
            <ThinkingChain
              content={thinkingChain}
              isExpanded={isThinking ? true : isChainExpanded}
              onToggle={() => setIsChainExpanded(!isChainExpanded)}
            />
          )}

          {!isThinking && thinkingSummary && (
            <ThinkingSummaryView
              summary={thinkingSummary}
              elapsedMs={thinkingElapsedMs}
              isExpanded={isChainExpanded}
              onToggle={() => setIsChainExpanded(!isChainExpanded)}
            />
          )}

          {content && (
            <div className={cn(
              "prose-sm sm:prose max-w-none text-[15px] sm:text-[15.5px] leading-relaxed",
              isUser ? "text-[#faf7f2] font-sans prose-p:my-1 prose-headings:text-white" : "prose-neutral dark:prose-invert prose-p:leading-relaxed text-[var(--text-primary)]",
              reading === "sans" ? "font-ui-sans" : "font-body",
              !isUser && "tracking-[0.01em] leading-[1.8]"
            )}>
              <LatexRenderer content={content} />
            </div>
          )}
            
          {status && !isUser ? (
            <div className="mt-3 flex items-center gap-1.5 border-t border-[var(--border-subtle)] pt-2.5 text-[11px] font-medium text-[var(--text-muted)]">
              {status.includes("未完成") ? <CircleDashed className="w-3.5 h-3.5 text-amber-500" /> : <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />}
              <span>{status}</span>
            </div>
          ) : null}

          {reviewData && !isUser ? (
            <div className="mt-3 pt-2">
              <ReviewCard data={reviewData} onSimilar={onSimilar} />
            </div>
          ) : null}

          {/* Action Bar */}
          <div className={cn("flex items-center gap-1.5 mt-3 pt-2 border-t border-[var(--border-subtle)]/60 transition-opacity duration-200", isUser ? "justify-end text-white/70" : "opacity-0 group-hover:opacity-100")}>
            <button
              onClick={copyText}
              className={cn("flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium transition-colors", isUser ? "hover:bg-white/15 text-white/80 hover:text-white" : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]")}
              title="复制回答"
            >
              {isCopied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{isCopied ? "已复制" : "复制"}</span>
            </button>
            {isUser && onEdit && (
              <button
                onClick={onEdit}
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium hover:bg-white/15 text-white/80 hover:text-white transition-colors"
                title="重新编辑问题"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>编辑</span>
              </button>
            )}
            {!isUser && (
              <button
                onClick={playSpeech}
                className={cn(
                  "flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium transition-colors",
                  isPlaying ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
                )}
                title={isPlaying ? "停止播放" : "朗读数学解答"}
              >
                {isPlaying ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                <span>{isPlaying ? "停止" : "朗读"}</span>
              </button>
            )}
            {!isUser && onRetry && (
              <button
                onClick={onRetry}
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
                title="以此步骤重新生成"
              >
                <RefreshCcw className="w-3.5 h-3.5" />
                <span>重试</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="shrink-0 mt-1 flex-col items-center hidden sm:flex">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-[var(--text-secondary)] shadow-xs">
            <User className="h-4 w-4" />
          </div>
        </div>
      )}
    </motion.div>
  );
}
