"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { BrandLogo } from "@/components/brand-logo";

export const learningButton = "rounded-lg bg-olive-700 px-4 py-2.5 text-base sm:text-sm font-medium text-paper-50 hover:bg-olive-800 disabled:opacity-50 disabled:cursor-wait transition-colors";
export const learningInput = "w-full rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] p-3 text-base sm:text-sm focus:outline focus:outline-2 focus:outline-olive-600 -outline-offset-1";
export const learningPanel = "rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-5 sm:p-6";

export function LearningShell({title, description, children, wide=false}: {title: string; description: string; children: ReactNode; wide?: boolean}) {
  const pathname = usePathname();
  return <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
    <header className="border-b border-[var(--border-subtle)]">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 sm:px-8">
        <Link href="/" className="flex shrink-0 items-center gap-2.5 font-title text-xl font-semibold"><BrandLogo/>珞珈数智 <span className="hidden sm:inline text-base font-normal text-[var(--text-secondary)]">/ 数值分析</span></Link>
        <div className="flex items-center gap-3"><Link href="/chat" className="text-base sm:text-sm text-olive-700 dark:text-olive-300">对话助教</Link><ThemeToggle /></div>
      </div>
      <nav aria-label="学习工作区" className="mx-auto grid max-w-6xl grid-cols-3 px-5 sm:flex sm:flex-wrap sm:gap-2 sm:px-8">
        {[["/study", "今日学习"], ["/reading", "教材伴读"], ["/lab", "数值实验"], ["/assessment", "章节自检"], ["/teach-back", "讲给助教听"], ["/code-workshop", "代码作业"]].map(([href, label]) =>
          <Link key={href} href={href} aria-current={(pathname === href || (href === "/lab" && pathname === "/numerical-lab")) ? "page" : undefined} className={`shrink-0 border-b-2 px-1 py-3 text-center text-base focus-visible:outline focus-visible:outline-2 focus-visible:outline-olive-600 sm:px-3 sm:text-sm ${(pathname === href || (href === "/lab" && pathname === "/numerical-lab")) ? "border-olive-600 font-semibold text-olive-700 dark:text-olive-300" : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>{label}</Link>)}
      </nav>
    </header>
    <div className={`mx-auto w-full ${wide?"max-w-[1480px] sm:py-8":"max-w-6xl sm:py-12"} px-5 py-8 sm:px-8`}>
      <div className="mb-8 max-w-2xl"><h1 className="font-title text-3xl font-semibold sm:text-4xl">{title}</h1><p className="mt-3 text-base leading-7 text-[var(--text-secondary)]">{description}</p></div>
      {children}
    </div>
  </div>;
}

export function Notice({error}: {error: string}) {
  return error ? <p role="alert" className="mb-5 rounded-lg border border-cinnabar-600/30 bg-cinnabar-600/5 p-4 text-base sm:text-sm text-cinnabar-700 dark:text-cinnabar-300">{error}</p> : null;
}
