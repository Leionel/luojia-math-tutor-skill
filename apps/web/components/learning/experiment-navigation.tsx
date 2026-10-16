import Link from "next/link";

export function ExperimentNavigation({active}: {active: "root" | "numerical"}) {
  return <nav aria-label="实验领域" className="sticky top-0 z-30 -mx-5 mb-8 flex flex-wrap gap-2 border-b border-[var(--border-subtle)] bg-[var(--bg-primary)]/95 px-5 py-3 text-sm shadow-[0_12px_24px_-25px_rgba(22,29,19,.6)] backdrop-blur-xl sm:-mx-8 sm:px-8">
    {[{href: "/lab", label: "非线性求根", key: "root"}, {href: "/numerical-lab", label: "线性方程组 · 数值积分", key: "numerical"}].map(item =>
      <Link key={item.key} href={item.href} aria-current={active === item.key ? "page" : undefined} className={`inline-flex min-h-11 items-center rounded-xl border px-4 py-2.5 font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-olive-600 ${active === item.key ? "border-olive-600 bg-olive-700 text-paper-50 shadow-sm" : "border-[var(--border-subtle)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:border-olive-500/50 hover:text-[var(--text-primary)]"}`}>{item.label}</Link>)}
  </nav>;
}
