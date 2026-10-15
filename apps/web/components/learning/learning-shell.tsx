"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { BrandLogo } from "@/components/brand-logo";
import { 
  Sparkles, 
  CheckCircle2, 
  HelpCircle, 
  AlertCircle, 
  ArrowUpRight, 
  BookOpen, 
  Layers, 
  TrendingDown,
  Activity,
  Cpu,
  ChevronRight
} from "lucide-react";

export const learningButton = "inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-b from-olive-600 to-olive-700 px-4 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs hover:from-olive-500 hover:to-olive-600 hover:shadow-sm hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none border border-olive-500/30 transition-all duration-200 cursor-pointer";
export const learningButtonSecondary = "inline-flex items-center justify-center gap-2 rounded-xl border border-paper-300 dark:border-paper-700 bg-[var(--bg-card)] px-4 py-2.5 text-xs sm:text-sm font-medium text-[var(--text-primary)] hover:border-paper-400 dark:hover:border-paper-600 hover:bg-paper-100/70 dark:hover:bg-paper-800/60 shadow-2xs hover:shadow-xs active:scale-[0.98] disabled:opacity-50 transition-all duration-200 cursor-pointer";
export const learningInput = "w-full rounded-xl border border-paper-300 dark:border-paper-700 bg-[var(--bg-input)] p-3 text-xs sm:text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-olive-600/30 focus:border-olive-600 shadow-[inset_0_1px_2px_rgba(0,0,0,0.03)] dark:shadow-[inset_0_1px_2px_rgba(0,0,0,0.2)] transition-all duration-200";
export const learningPanel = "rounded-2xl border border-paper-300/80 dark:border-paper-700/80 bg-[var(--bg-card)] p-5 sm:p-6 shadow-soft transition-all";

export function LearningShell({
  title, 
  description, 
  children, 
  wide = false,
  badgeText = "非线性方程求根 · 研学工坊",
}: {
  title: string; 
  description: string; 
  children: ReactNode; 
  wide?: boolean;
  badgeText?: string;
}) {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const navItems = [
    { href: "/study", label: "今日研学", keyHint: "1", icon: Layers },
    { href: "/reading", label: "定理研读", keyHint: "2", icon: BookOpen },
    { href: "/lab", label: "数值实验", keyHint: "3", icon: Sparkles },
    { href: "/assessment", label: "认知自检", keyHint: "4", icon: CheckCircle2 },
    { href: "/teach-back", label: "费曼讲坛", keyHint: "5", icon: HelpCircle },
    { href: "/code-workshop", label: "算法工坊", keyHint: "6", icon: ArrowUpRight },
    { href: "/admin/knowledge", label: "教师审核", keyHint: "", icon: CheckCircle2 },
  ];

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans antialiased relative selection:bg-olive-500/20 selection:text-olive-900 dark:selection:text-olive-100">
      {/* 数学工程草纸微网格背景 (Engineering Graph Paper Subtle Grid) */}
      <div 
        className="fixed inset-0 pointer-events-none opacity-[0.25] dark:opacity-[0.10]" 
        style={{
          backgroundImage: "radial-gradient(var(--border-primary) 1px, transparent 1px)",
          backgroundSize: "28px 28px"
        }}
        aria-hidden="true"
      />

      {/* 顶部环境微光光晕 (Ambient Warm Light) */}
      <div 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[320px] bg-gradient-to-b from-olive-500/5 via-olive-500/[0.02] to-transparent blur-3xl pointer-events-none" 
        aria-hidden="true" 
      />

      {/* 现代玻璃化研学顶栏 (Glassmorphic Atelier Header) */}
      <header className="sticky top-0 z-40 border-b border-paper-300/80 dark:border-paper-800/80 bg-[var(--bg-header)] backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-8">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex shrink-0 items-center gap-2.5 font-title text-xl font-semibold tracking-wide hover:opacity-90 transition-opacity">
              <BrandLogo />
              <span className="text-[var(--text-primary)]">珞珈数智</span>
              <div className="hidden sm:flex items-center gap-1.5 font-sans text-xs px-2.5 py-0.5 rounded-full bg-olive-500/10 text-olive-800 dark:text-olive-200 border border-olive-600/25">
                <span className="w-1.5 h-1.5 rounded-full bg-olive-600 animate-pulse" />
                <span>{badgeText}</span>
              </div>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <Link 
              href="/chat" 
              className="group flex items-center gap-1.5 text-xs sm:text-sm font-medium px-3.5 py-1.5 rounded-xl border border-olive-600/30 bg-olive-500/5 text-olive-800 dark:text-olive-200 hover:bg-olive-500/15 active:scale-95 transition-all shadow-xs"
            >
              <Sparkles className="w-3.5 h-3.5 text-olive-600 group-hover:rotate-12 transition-transform" />
              <span>对话助教小珞</span>
              <span className="hidden md:inline font-mono text-[10px] px-1.5 py-0.2 rounded bg-olive-600/15 text-olive-700 dark:text-olive-300 ml-1">
                Chat
              </span>
            </Link>
            <ThemeToggle />
          </div>
        </div>

        {/* 悬浮胶囊工作区导航条 (Floating Pill Atelier Navigation) */}
        <nav aria-label="学习工作区导航" className="mx-auto max-w-7xl px-4 sm:px-8 overflow-x-auto scrollbar-none">
          <div className="flex items-center gap-1 sm:gap-1.5 border-t border-paper-200/50 dark:border-paper-800/40 py-2">
            {navItems.map(({ href, label, keyHint, icon: Icon }) => {
              const active = pathname === href || (href === "/lab" && pathname === "/numerical-lab");
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={`group relative flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium whitespace-nowrap transition-all duration-200 ${
                    active
                      ? "bg-olive-600/15 text-olive-800 dark:text-olive-200 font-semibold shadow-xs border border-olive-600/30"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]/70"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 transition-colors ${active ? "text-olive-600" : "text-[var(--text-muted)] group-hover:text-[var(--text-secondary)]"}`} />
                  <span>{label}</span>
                  <span className={`hidden lg:inline font-mono text-[10px] px-1 rounded opacity-50 ${active ? "bg-olive-600/20 text-olive-900 dark:text-olive-100" : "bg-paper-200 dark:bg-paper-800 text-[var(--text-muted)]"}`}>
                    {keyHint}
                  </span>
                  {active && (
                    <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-[2px] bg-olive-600 rounded-full" />
                  )}
                </Link>
              );
            })}
          </div>
        </nav>
      </header>

      {/* 核心工作区主舞台 */}
      <main className={`relative z-10 mx-auto w-full ${wide ? "max-w-[1540px] py-6 sm:py-8" : "max-w-7xl py-6 sm:py-10"} px-4 sm:px-8`}>
        <div className="mb-8 max-w-3xl animate-fade-in">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-olive-700 dark:text-olive-300 font-semibold tracking-wider uppercase mb-1">
            <Activity className="w-3.5 h-3.5" />
            <span>认知工坊 · 研学中枢</span>
          </div>
          <h1 className="font-title text-2xl sm:text-4xl font-semibold tracking-tight text-[var(--text-primary)]">
            {title}
          </h1>
          <p className="mt-2 text-xs sm:text-base leading-relaxed text-[var(--text-secondary)]">
            {description}
          </p>
        </div>
        {children}
      </main>
    </div>
  );
}

export function Notice({ error }: { error: string }) {
  if (!error) return null;
  return (
    <div role="alert" className="mb-6 flex items-start gap-3 rounded-2xl border border-cinnabar-600/30 bg-cinnabar-500/5 p-4 text-xs sm:text-sm text-cinnabar-800 dark:text-cinnabar-200 animate-slide-up shadow-xs">
      <AlertCircle className="w-5 h-5 shrink-0 text-cinnabar-600 mt-0.5" />
      <div className="leading-relaxed">{error}</div>
    </div>
  );
}

/** 统一高质感工坊书卷卡片 (Atelier Folio Card) */
export function AtelierFolioCard({
  index,
  title,
  badge,
  badgeVariant = "olive",
  children,
  footer,
  className = "",
}: {
  index?: string | number;
  title: ReactNode;
  badge?: ReactNode;
  badgeVariant?: "olive" | "ochre" | "cinnabar" | "dai" | "muted";
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}) {
  const badgeStyles = {
    olive: "bg-olive-500/10 text-olive-800 dark:text-olive-200 border-olive-500/25",
    ochre: "bg-ochre-500/10 text-ochre-800 dark:text-ochre-200 border-ochre-500/25",
    cinnabar: "bg-cinnabar-500/10 text-cinnabar-800 dark:text-cinnabar-200 border-cinnabar-500/25",
    dai: "bg-dai-500/10 text-dai-800 dark:text-dai-200 border-dai-500/25",
    muted: "bg-paper-200/60 dark:bg-paper-800/60 text-[var(--text-muted)] border-paper-300 dark:border-paper-700",
  };

  return (
    <section className={`relative rounded-2xl atelier-hairline border border-paper-300/80 dark:border-paper-700/80 bg-[var(--bg-card)] p-5 sm:p-6 shadow-soft hover:shadow-card hover:border-paper-400 dark:hover:border-paper-600 transition-all duration-300 overflow-hidden ${className}`}>
      {/* 顶部微光发丝线 (Top Hairline Highlight) */}
      <div className="absolute inset-x-0 top-0 h-[var(--hairline)] bg-gradient-to-r from-transparent via-white/50 dark:via-white/10 to-transparent pointer-events-none" />

      <div className="flex items-center justify-between border-b border-paper-200/60 dark:border-paper-800/60 pb-3.5 mb-4 gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          {index !== undefined && (
            <span className="font-mono text-[11px] px-2 py-0.5 rounded-md bg-paper-200/70 dark:bg-paper-800/80 text-[var(--text-muted)] font-bold shrink-0">
              {String(index).padStart(2, "0")}
            </span>
          )}
          <h2 className="font-title text-base sm:text-xl font-semibold text-[var(--text-primary)] truncate">
            {title}
          </h2>
        </div>
        {badge && (
          <span className={`text-[11px] sm:text-xs px-2.5 py-0.5 rounded-full border shrink-0 font-medium ${badgeStyles[badgeVariant]}`}>
            {badge}
          </span>
        )}
      </div>

      <div className="text-[var(--text-primary)] leading-relaxed">
        {children}
      </div>

      {footer && (
        <div className="mt-5 border-t border-paper-200/60 dark:border-paper-800/60 pt-4 flex flex-wrap items-center justify-between gap-3 text-xs">
          {footer}
        </div>
      )}
    </section>
  );
}

/** 助教苏格拉底思辨气泡 (Socratic Companion Bubble) */
export function SocraticCompanionBubble({
  title = "助教小珞的思辨探针",
  content,
  icon,
}: {
  title?: string;
  content: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="relative rounded-2xl border border-dai-500/25 bg-gradient-to-br from-dai-500/[0.07] to-dai-500/[0.02] p-4 sm:p-5 shadow-xs transition-all">
      <div className="flex items-center gap-2 text-dai-800 dark:text-dai-200 font-semibold text-xs sm:text-sm mb-2">
        {icon ?? <Sparkles className="w-4 h-4 text-dai-600 animate-pulse" />}
        <span className="tracking-wide font-title">{title}</span>
      </div>
      <div className="text-xs sm:text-sm leading-relaxed text-[var(--text-secondary)]">
        {content}
      </div>
    </div>
  );
}

/** 定理必备条件印章徽标 (Condition Pillar Badge) */
export function ConditionPillarBadge({
  title,
  desc,
  status = "pending",
  studentQuote,
  onClick,
}: {
  title: string;
  desc?: string;
  status?: "verified" | "pending" | "violated" | "unmapped";
  studentQuote?: string;
  onClick?: () => void;
}) {
  const statusConfig = {
    verified: { icon: CheckCircle2, text: "已核实具备", color: "text-olive-800 dark:text-olive-200 border-olive-500/30 bg-olive-500/5" },
    pending: { icon: HelpCircle, text: "待补条件", color: "text-ochre-800 dark:text-ochre-200 border-ochre-500/30 bg-ochre-500/5" },
    violated: { icon: AlertCircle, text: "前提冲突", color: "text-cinnabar-800 dark:text-cinnabar-200 border-cinnabar-500/30 bg-cinnabar-500/5" },
    unmapped: { icon: HelpCircle, text: "尚未映射", color: "text-[var(--text-muted)] border-paper-300 dark:border-paper-700 bg-transparent" },
  };

  const { icon: Icon, text, color } = statusConfig[status];

  return (
    <div
      onClick={onClick}
      className={`rounded-xl border p-3.5 transition-all duration-200 text-xs sm:text-sm ${color} ${
        onClick ? "cursor-pointer hover:shadow-xs hover:scale-[1.005] active:scale-[0.99]" : ""
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-medium">
          <Icon className="w-4 h-4 shrink-0" />
          <span>{title}</span>
        </div>
        <span className="text-[10px] sm:text-[11px] font-mono px-2 py-0.5 rounded-full border border-current opacity-90">
          {text}
        </span>
      </div>
      {desc && <p className="mt-1.5 text-xs text-[var(--text-secondary)] leading-normal pl-6">{desc}</p>}
      {studentQuote && (
        <div className="mt-2.5 pl-6">
          <div className="rounded-lg bg-[var(--bg-tertiary)] border-l-2 border-olive-600 p-2 text-xs text-[var(--text-secondary)] italic">
            “{studentQuote}”
          </div>
        </div>
      )}
    </div>
  );
}

/** 动态数值轨迹收敛阶微雷达 (Numerical Trace Visualizer & Order Estimator) */
export function NumericalTraceVisualizer({
  values,
}: {
  values: number[];
}) {
  if (!values || values.length === 0) return null;

  // 计算相邻步长差与收敛比率
  const steps = values.slice(1).map((curr, idx) => {
    const prev = values[idx];
    const diff = Math.abs(curr - prev);
    return { curr, prev, diff };
  });

  const isRapidlyDecreasing = steps.length >= 2 && steps[steps.length - 1].diff < steps[steps.length - 2].diff * 0.5;

  return (
    <div className="mt-3 p-3.5 rounded-xl bg-paper-100 dark:bg-paper-800/50 border border-paper-200 dark:border-paper-700/60 space-y-2.5 animate-fade-in">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 font-semibold text-olive-800 dark:text-olive-200">
          <TrendingDown className="w-3.5 h-3.5" />
          <span>已捕获迭代步数序列（共 {values.length} 个点）：</span>
        </div>
        {isRapidlyDecreasing && (
          <span className="px-2 py-0.5 rounded-full bg-olive-500/15 text-olive-800 dark:text-olive-200 text-[10px] font-mono font-medium border border-olive-500/30">
            ✨ 展现快速超线性/二次收敛阶特征
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5 font-mono text-xs">
        {values.map((val, i) => (
          <span 
            key={i} 
            className="px-2 py-1 rounded-lg bg-[var(--bg-card)] border border-paper-300 dark:border-paper-700 text-[var(--text-primary)] shadow-2xs"
          >
            <span className="text-[var(--text-muted)] mr-1">x_{i}=</span>
            <strong>{typeof val === "number" ? val.toFixed(6) : String(val)}</strong>
          </span>
        ))}
      </div>
    </div>
  );
}
