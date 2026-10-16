import Image from "next/image";
import Link from "next/link";

/** Original user-supplied artwork; the character is an AI tutor identity. */
export function TutorCompanion({compact = false}: {compact?: boolean}) {
  return <section aria-label="认识小珞" className={compact
    ? "mb-7 flex items-center gap-5 border-b border-[var(--border-subtle)] pb-5"
    : "mt-10 grid items-center gap-5 border-t border-[var(--border-primary)] pt-7 sm:grid-cols-[208px_minmax(0,1fr)] sm:gap-10"}>
    <div className={compact ? "w-24 shrink-0 sm:w-28" : "mx-auto w-40 sm:w-52"}>
      <Image src="/brand/xiaoluo.png" width={1024} height={1536} alt="小珞全身立绘：珞珈山发夹、书页翻领、橄榄绿制服，手持教材与笔" sizes={compact ? "112px" : "(max-width: 640px) 160px, 208px"} className="h-auto w-full" />
    </div>
    <div className="min-w-0">
      <p className="text-base sm:text-sm text-olive-700 dark:text-olive-300">小珞 · 数学学姐</p>
      <h2 className={compact ? "mt-2 font-serif text-xl font-medium" : "mt-3 font-serif text-2xl font-medium sm:text-3xl"}>陪你读教材，也陪你做实验。</h2>
      <p className="mt-3 max-w-[42ch] text-base leading-7 text-[var(--text-secondary)]">一起辨清公式的条件，看看迭代怎样走，再把你的理解讲出来。</p>
      <p className="mt-2 text-base sm:text-xs leading-6 text-[var(--text-muted)]">珞珈数智的 AI 助教形象</p>
      {!compact && <div className="mt-4 flex flex-wrap gap-x-6"><Link href="/reading" className="inline-flex min-h-12 items-center text-base text-olive-700 underline underline-offset-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-olive-600 dark:text-olive-300">一起读教材 →</Link><Link href="/lab" className="inline-flex min-h-12 items-center text-base text-olive-700 underline underline-offset-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-olive-600 dark:text-olive-300">去做一次实验 →</Link></div>}
    </div>
  </section>;
}
