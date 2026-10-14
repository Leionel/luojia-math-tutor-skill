"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { BrandLogo } from "@/components/brand-logo";
import { Sparkles, CheckCircle2, HelpCircle, AlertCircle, ArrowUpRight, BookOpen, Layers } from "lucide-react";

export const learningButton = "inline-flex items-center justify-center gap-2 rounded-xl bg-olive-700 px-4 py-2.5 text-base sm:text-sm font-medium text-paper-50 shadow-sm hover:bg-olive-800 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none transition-all";
export const learningButtonSecondary = "inline-flex items-center justify-center gap-2 rounded-xl border border-paper-300 dark:border-paper-700 bg-[var(--bg-card)] px-4 py-2.5 text-base sm:text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-hover)] active:scale-[0.98] disabled:opacity-50 transition-all";
export const learningInput = "w-full rounded-xl border border-paper-300 dark:border-paper-700 bg-[var(--bg-input)] p-3 text-base sm:text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-olive-600/40 focus:border-olive-600 transition-all";
export const learningPanel = "rounded-2xl border border-paper-300/80 dark:border-paper-700/80 bg-[var(--bg-card)] p-5 sm:p-6 shadow-soft";

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
  const navItems = [
    { href: "/study", label: "今日学习", icon: Layers },
    { href: "/reading", label: "教材伴读", icon: BookOpen },
    { href: "/lab", label: "数值实验", icon: Sparkles },
    { href: "/assessment", label: "章节自检", icon: CheckCircle2 },
    { href: "/teach-back", label: "讲给助教听", icon: HelpCircle },
    { href: "/code-workshop", label: "代码作业", icon: ArrowUpRight },
  ];

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans antialiased selection:bg-olive-500/20 selection:text-olive-900 dark:selection:text-olive-100">
      <header className="sticky top-0 z-30 border-b border-paper-300/70 dark:border-paper-800/80 bg-[var(--bg-header)] backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-8">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex shrink-0 items-center gap-2.5 font-title text-xl font-semibold tracking-wide">
              <BrandLogo />
              <span>珞珈数智</span>
              <span className="hidden sm:inline font-sans text-xs font-normal px-2 py-0.5 rounded-full bg-olive-500/10 text-olive-700 dark:text-olive-300 border border-olive-600/20">
                {badgeText}
              </span>
            </Link>
          </div>
          <div className="flex items-center gap-3">
            <Link 
              href="/chat" 
              className="group flex items-center gap-1.5 text-xs sm:text-sm font-medium px-3 py-1.5 rounded-lg border border-olive-600/30 text-olive-700 hover:bg-olive-500/10 dark:text-olive-300 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-olive-600 group-hover:rotate-12 transition-transform" />
              <span>对话助教小珞</span>
            </Link>
            <ThemeToggle />
          </div>
        </div>

        {/* 统一工坊工作区导航条 */}
        <nav aria-label="学习工作区导航" className="mx-auto max-w-7xl px-4 sm:px-8 overflow-x-auto scrollbar-none">
          <div className="flex items-center gap-1 sm:gap-2 border-t border-paper-200/50 dark:border-paper-800/40 py-1.5">
            {navItems.map(({ href, label, icon: Icon }) => {
              const active = pathname === href || (href === "/lab" && pathname === "/numerical-lab");
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium whitespace-nowrap transition-all ${
                    active
                      ? "bg-olive-600/10 text-olive-800 dark:text-olive-200 font-semibold shadow-xs border border-olive-600/25"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]/60"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${active ? "text-olive-600" : "text-[var(--text-muted)]"}`} />
                  <span>{label}</span>
                </Link>
              );
            })}
          </div>
        </nav>
      </header>

      <main className={`mx-auto w-full ${wide ? "max-w-[1520px] py-6 sm:py-8" : "max-w-7xl py-6 sm:py-10"} px-4 sm:px-8`}>
        <div className="mb-8 max-w-3xl animate-fade-in">
          <h1 className="font-title text-2xl sm:text-4xl font-semibold tracking-tight text-[var(--text-primary)]">
            {title}
          </h1>
          <p className="mt-2.5 text-sm sm:text-base leading-relaxed text-[var(--text-secondary)]">
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
    <div role="alert" className="mb-6 flex items-start gap-3 rounded-xl border border-cinnabar-600/30 bg-cinnabar-500/5 p-4 text-sm text-cinnabar-800 dark:text-cinnabar-200 animate-slide-up">
      <AlertCircle className="w-5 h-5 shrink-0 text-cinnabar-600 mt-0.5" />
      <div className="leading-relaxed">{error}</div>
    </div>
  );
}

/** 统一工坊书卷卡片 (Atelier Folio Card) */
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
    olive: "bg-olive-500/10 text-olive-700 dark:text-olive-300 border-olive-500/25",
    ochre: "bg-ochre-500/10 text-ochre-700 dark:text-ochre-300 border-ochre-500/25",
    cinnabar: "bg-cinnabar-500/10 text-cinnabar-700 dark:text-cinnabar-300 border-cinnabar-500/25",
    dai: "bg-dai-500/10 text-dai-700 dark:text-dai-300 border-dai-500/25",
    muted: "bg-paper-200/50 text-[var(--text-muted)] border-paper-300",
  };

  return (
    <section className={`rounded-2xl border border-paper-300/80 dark:border-paper-700/80 bg-[var(--bg-card)] p-5 sm:p-6 shadow-soft transition-all duration-300 hover:shadow-card ${className}`}>
      <div className="flex items-center justify-between border-b border-paper-200/60 dark:border-paper-800/50 pb-3 mb-4 gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          {index !== undefined && (
            <span className="font-mono text-xs px-2 py-0.5 rounded-md bg-paper-200/70 dark:bg-paper-800/80 text-[var(--text-muted)] font-semibold shrink-0">
              {String(index).padStart(2, "0")}
            </span>
          )}
          <h2 className="font-title text-lg sm:text-xl font-semibold text-[var(--text-primary)] truncate">
            {title}
          </h2>
        </div>
        {badge && (
          <span className={`text-xs px-2.5 py-0.5 rounded-full border shrink-0 font-medium ${badgeStyles[badgeVariant]}`}>
            {badge}
          </span>
        )}
      </div>
      <div className="text-[var(--text-primary)] leading-relaxed">
        {children}
      </div>
      {footer && (
        <div className="mt-5 border-t border-paper-200/60 dark:border-paper-800/50 pt-4 flex flex-wrap items-center justify-between gap-3">
          {footer}
        </div>
      )}
    </section>
  );
}

/** 助教苏格拉底思辨气泡 */
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
    <div className="rounded-xl border border-dai-500/20 bg-dai-500/5 p-4 sm:p-5 shadow-xs transition-all">
      <div className="flex items-center gap-2 text-dai-700 dark:text-dai-300 font-medium text-xs sm:text-sm mb-2">
        {icon ?? <Sparkles className="w-4 h-4 text-dai-600" />}
        <span className="tracking-wide">{title}</span>
      </div>
      <div className="text-xs sm:text-sm leading-relaxed text-[var(--text-secondary)]">
        {content}
      </div>
    </div>
  );
}

/** 定理必备条件印章徽标 */
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
    verified: { icon: CheckCircle2, text: "已核实具备", color: "text-olive-700 border-olive-500/30 bg-olive-500/5" },
    pending: { icon: HelpCircle, text: "待补条件", color: "text-ochre-700 border-ochre-500/30 bg-ochre-500/5" },
    violated: { icon: AlertCircle, text: "前提冲突", color: "text-cinnabar-700 border-cinnabar-500/30 bg-cinnabar-500/5" },
    unmapped: { icon: HelpCircle, text: "尚未映射", color: "text-[var(--text-muted)] border-paper-300 bg-transparent" },
  };

  const { icon: Icon, text, color } = statusConfig[status];

  return (
    <div
      onClick={onClick}
      className={`rounded-xl border p-3.5 transition-all text-xs sm:text-sm ${color} ${onClick ? "cursor-pointer hover:shadow-xs hover:scale-[1.005]" : ""}`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-medium">
          <Icon className="w-4 h-4 shrink-0" />
          <span>{title}</span>
        </div>
        <span className="text-[11px] px-2 py-0.5 rounded-full border border-current opacity-85">
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
