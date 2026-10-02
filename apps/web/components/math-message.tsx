"use client";

import type { WebSearchReport, RootDiagnosis } from "@/lib/api";
import { useState, useEffect } from "react";
import { RootDiagnosticCard } from "./root-diagnostic-card";
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
    PLAN: "审题立意 · 策略规划",
    "隐式 RAG": "知识图谱 · 脉络与学情",
    VERIFY: "符号推求 · 代数公理验算",
    OUTPUT: "落笔点拨 · 启发式讲解",
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

function ThinkingProgressBanner({
  elapsed,
  chain,
  isExpanded,
  onToggle,
}: {
  elapsed: number;
  chain?: string;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const steps = chain ? parseThinkingChain(chain) : [];
  const dots = ".".repeat((elapsed % 3) + 1);

  return (
    <div className="mb-3">
      <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-olive-500/10 dark:bg-olive-400/15 border border-olive-500/25 text-xs text-olive-800 dark:text-olive-300 font-serif shadow-xs">
        <BrainCircuit className="w-3.5 h-3.5 text-olive-700 dark:text-olive-400 animate-spin" style={{ animationDuration: '4s' }} />
        <span className="font-semibold tracking-wide">
          珞珈师说：推演构思中（{elapsed}s）{dots}
        </span>
        {steps.length > 0 && (
          <button
            onClick={onToggle}
            className="inline-flex items-center gap-1 ml-1 px-2 py-0.5 rounded-full bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/15 text-[11px] font-mono text-olive-900 dark:text-olive-200 transition-colors cursor-pointer"
          >
            <span>{isExpanded ? "收起规划" : `查看 ${steps.length} 步演练`}</span>
            <ChevronRight className={cn("w-3 h-3 transition-transform duration-200", isExpanded && "rotate-90")} />
          </button>
        )}
      </div>

      <AnimatePresence>
        {isExpanded && steps.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: -4 }}
            animate={{ opacity: 1, height: 'auto', y: 0 }}
            exit={{ opacity: 0, height: 0, y: -4 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="overflow-hidden mt-2"
          >
            <div className="rounded-xl bg-[#f8f5ee]/90 dark:bg-[#1c1e19]/90 border border-[#dfd7c2] dark:border-[#383a32] p-3.5 shadow-xs">
              <div className="relative pl-5 border-l-2 border-olive-600/30 dark:border-olive-400/25 ml-2.5 flex flex-col gap-3 py-0.5">
                {steps.map((step, idx) => (
                  <div key={idx} className="relative">
                    <div className="absolute -left-[27px] top-0.5 w-5 h-5 rounded-full bg-white dark:bg-[#20211d] border border-olive-600/40 flex items-center justify-center shadow-2xs z-10">
                      {getStepIcon(step.type)}
                    </div>
                    <div className="flex items-center gap-2 select-none mb-0.5">
                      <span className="text-xs font-serif font-bold text-olive-900 dark:text-olive-200">
                        {displayThinkingTitle(step.title)}
                      </span>
                      <span className="text-[10px] text-[var(--text-muted)] font-mono uppercase tracking-wider px-1.5 py-0.2 rounded bg-black/5 dark:bg-white/5">
                        阶段 {idx + 1}
                      </span>
                    </div>
                    <div className="text-xs text-[var(--text-secondary)] leading-relaxed pl-0.5">
                      <LatexRenderer content={step.content} complete={false} />
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

function ThinkingSummaryView({
  summary,
  elapsedMs,
  isExpanded,
  onToggle
}: {
  summary: string;
  elapsedMs?: number;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const steps = parseThinkingChain(summary);

  return (
    <div className="mt-2.5 mb-2">
      <button
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] bg-[var(--bg-tertiary)]/70 hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] transition-all shadow-sm group cursor-pointer"
        onClick={onToggle}
      >
        <ChevronRight className={cn("w-3.5 h-3.5 transition-transform duration-200 text-olive-600 dark:text-olive-400", isExpanded && "rotate-90")} />
        <span className="font-semibold text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">推导演绎链路</span>
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
            <div className="rounded-xl bg-[#f8f5ee]/90 dark:bg-[#1c1e19]/90 border border-[#dfd7c2] dark:border-[#383a32] p-3.5 shadow-xs">
              <div className="relative pl-5 border-l-2 border-olive-600/30 dark:border-olive-400/25 ml-2.5 flex flex-col gap-3 py-0.5">
                {steps.length > 0 ? (
                  steps.map((step, idx) => (
                    <div key={idx} className="relative">
                      <div className="absolute -left-[27px] top-0.5 w-5 h-5 rounded-full bg-white dark:bg-[#20211d] border border-olive-600/40 flex items-center justify-center shadow-2xs z-10">
                        {getStepIcon(step.type)}
                      </div>
                      <div className="flex items-center gap-2 select-none mb-0.5">
                        <span className="text-xs font-serif font-bold text-olive-900 dark:text-olive-200">
                          {displayThinkingTitle(step.title)}
                        </span>
                        <span className="text-[10px] text-[var(--text-muted)] font-mono uppercase tracking-wider px-1.5 py-0.2 rounded bg-black/5 dark:bg-white/5">
                          阶段 {idx + 1}
                        </span>
                      </div>
                      <div className="text-xs text-[var(--text-secondary)] leading-relaxed pl-0.5">
                        <LatexRenderer content={step.content} complete={true} />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-[var(--text-muted)] italic text-xs">{summary}</div>
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
  isGenerating = false,
  isIncomplete = false,
  rootDiagnosis, sessionId = "", onRootRevision, onRootProbe,
  thinkingElapsed = 0,
  thinkingChain = "",
  thinkingSummary,
  thinkingElapsedMs,
  webSearchReport,
  reviewData,
  onSimilar,
  onEdit,
  onRetry,
}: {
  role: "user" | "assistant";
  content: string;
  status?: string;
  isThinking?: boolean;
  isGenerating?: boolean;
  isIncomplete?: boolean;
  rootDiagnosis?: RootDiagnosis;
  sessionId?: string;
  onRootRevision?: (report: RootDiagnosis) => void;
  onRootProbe?: (report: RootDiagnosis) => void;
  thinkingElapsed?: number;
  thinkingChain?: string;
  thinkingSummary?: string;
  thinkingElapsedMs?: number;
  webSearchReport?: WebSearchReport;
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
      initial={{ opacity: 0, y: 12, scale: 0.99 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 350, damping: 28 }}
      className="flex w-full mb-6 group justify-start"
    >
      <div className="flex flex-col w-full min-w-0">
        {/* 角色标识与阶段指示 (学子立论 vs 珞珈师说) */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {isUser ? (
              <>
                <span className="px-2.5 py-0.5 rounded text-[11px] font-serif font-bold tracking-wider bg-[#3e3f36] text-[#faf7f2] dark:bg-[#2b2c26] shadow-xs">
                  「学子立论」
                </span>
                <span className="text-[11px] font-mono text-[var(--text-muted)]">
                  草稿演练步骤
                </span>
              </>
            ) : (
              <>
                <span className="px-2.5 py-0.5 rounded text-[11px] font-serif font-bold tracking-wider bg-[#4e6344] text-[#faf7f2] dark:bg-[#3f5137] shadow-xs">
                  「珞珈师说」
                </span>
                <span className="text-xs font-serif font-semibold tracking-wide text-olive-800 dark:text-olive-200">
                  启发辨析与证明
                </span>
              </>
            )}
          </div>

          {/* 状态徽标 (如后台验算通过) */}
          {status && !isUser && (
            <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono text-olive-800 dark:text-olive-300 bg-olive-500/10 border border-olive-500/20">
              {status.includes("未完成") ? (
                <CircleDashed className="w-3 h-3 text-amber-500" />
              ) : (
                <CheckCircle2 className="w-3 h-3 text-olive-600 dark:text-olive-400" />
              )}
              <span>{status}</span>
            </div>
          )}
        </div>

        {/* 手稿推导承载主体 (消除笨重的双重气泡卡片，保证长公式视窗宽裕) */}
        <div
          className={cn(
            "w-full transition-all duration-200",
            isUser
              ? "border-l-[3.5px] border-[#c4ba9d] dark:border-[#525447] bg-[#f5f1e6]/45 dark:bg-[#252621]/45 rounded-r-xl p-4 sm:p-5 shadow-xs"
              : "border border-[#e2dcc8]/80 dark:border-[#383a32]/80 bg-white/70 dark:bg-[#20211d]/70 rounded-xl p-4 sm:p-6 shadow-xs"
          )}
        >
          {isThinking && (
            <ThinkingProgressBanner
              elapsed={thinkingElapsed}
              chain={thinkingChain}
              isExpanded={isChainExpanded}
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
            <div
              className={cn(
                "prose-sm sm:prose max-w-none text-[15px] sm:text-[15.5px] leading-relaxed select-text overflow-x-auto",
                isUser
                  ? "text-[var(--text-primary)] font-serif prose-p:my-1"
                  : "prose-neutral dark:prose-invert text-[var(--text-primary)] prose-p:leading-[1.8]",
                reading === "sans" ? "font-ui-sans" : "font-serif",
                !isUser && "tracking-[0.01em]"
              )}
            >
              {webSearchReport && webSearchReport.status !== "disabled" && (
                <div className="mb-3 rounded-lg border border-[var(--border-subtle)] p-3 text-xs text-[var(--text-secondary)]" role="status">
                  <p>{webSearchReport.status === "success"
                    ? `联网检索返回 ${webSearchReport.result_count} 条摘要，尚未核验全文与发布日期。`
                    : webSearchReport.status === "timeout" ? "联网检索超时，本轮未完成事实核实。"
                    : webSearchReport.status === "empty" ? "联网检索未返回可用结果，本轮未完成事实核实。"
                    : "联网检索服务暂不可用，本轮未完成事实核实。"}</p>
                  {webSearchReport.sources?.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {webSearchReport.sources.filter((source) => /^https?:\/\//i.test(source.url)).map((source) => (
                        <li key={source.id}><a href={source.url} target="_blank" rel="noopener noreferrer" className="text-olive-700 dark:text-olive-300 underline underline-offset-2 break-words">[{source.id}] {source.title}</a></li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
              {rootDiagnosis && <RootDiagnosticCard report={rootDiagnosis} sessionId={sessionId} complete={!isGenerating && !isThinking && !isIncomplete} onRevision={onRootRevision} onProbe={onRootProbe}/> }
              <LatexRenderer content={content} complete={!isGenerating && !isThinking && !isIncomplete} />
              {isThinking && (
                <span className="inline-flex items-center gap-1.5 ml-1.5 text-xs text-olive-700/80 dark:text-olive-400/80 font-serif italic select-none">
                  <span className="inline-block w-1.5 h-4 bg-olive-700 dark:bg-olive-400 rounded-xs animate-pulse align-middle" />
                  <span>正在提笔运思展开...</span>
                </span>
              )}
            </div>
          )}

          {/* 步骤复盘卡 (融入 C 方案双栏对照学案) */}
          {reviewData && !isUser && (
            <div className="mt-3 pt-2">
              <ReviewCard data={reviewData} onSimilar={onSimilar} />
            </div>
          )}

          {/* 轻量操作工具栏 */}
          <div className="flex items-center gap-2 mt-3 pt-2 border-t border-[var(--border-subtle)]/70 text-[var(--text-muted)] text-[11px]">
            <button
              onClick={copyText}
              className="inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors"
              title="复制内容"
            >
              {isCopied ? <CheckCircle2 className="w-3.5 h-3.5 text-olive-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{isCopied ? "已复制" : "复制"}</span>
            </button>

            {isUser && onEdit && (
              <button
                onClick={onEdit}
                className="inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors"
                title="重新编辑本步立论"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>编辑</span>
              </button>
            )}

            {!isUser && (
              <button
                onClick={playSpeech}
                className={cn(
                  "inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors",
                  isPlaying && "text-olive-600 font-bold"
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
                className="inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors"
                title="以此步骤重新推导"
              >
                <RefreshCcw className="w-3.5 h-3.5" />
                <span>重试</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
