import Link from "next/link";

export function ExperimentNavigation({active}: {active: "root" | "numerical"}) {
  return <nav aria-label="实验领域" className="mb-6 flex flex-wrap gap-3 text-base">
    {[{href: "/lab", label: "非线性求根", key: "root"}, {href: "/numerical-lab", label: "线性方程组 · 数值积分", key: "numerical"}].map(item =>
      <Link key={item.key} href={item.href} aria-current={active === item.key ? "page" : undefined} className={`min-h-11 rounded-lg border px-4 py-3 focus-visible:outline focus-visible:outline-2 focus-visible:outline-olive-600 ${active === item.key ? "border-olive-600 bg-olive-600/10 text-olive-700 dark:text-olive-300" : "border-[var(--border-subtle)]"}`}>{item.label}</Link>)}
  </nav>;
}
