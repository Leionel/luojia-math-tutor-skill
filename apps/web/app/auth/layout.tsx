import {ReactNode} from "react";
import Link from "next/link";
import {BrandLogo} from "@/components/brand-logo";
import {ThemeToggle} from "@/components/theme-toggle";

export default function AuthLayout({children}:{children:ReactNode}) {
  return <main className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] px-5 py-6 sm:px-8">
    <header className="mx-auto flex max-w-5xl items-center justify-between"><Link href="/" className="inline-flex items-center gap-3 font-title text-lg"><BrandLogo className="h-10 w-10"/>珞珈数智</Link><ThemeToggle/></header>
    <section className="mx-auto mt-10 w-full max-w-md sm:mt-16">{children}<Link href="/" className="mt-6 inline-flex min-h-11 items-center text-olive-700 dark:text-olive-300 underline">返回首页</Link></section>
  </main>;
}
