"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function SiteHeader() {
  const pathname = usePathname();

  // Hide the global site header on main app routes where they have their own headers
  if (['/chat', '/notebook', '/mistake-book'].some(p => pathname.startsWith(p))) {
    return null;
  }

  const links = [
    { href: "/", label: "首页 (Home)" },
    { href: "/chat", label: "进入对话 (AI Tutor)" },
    { href: "/admin/knowledge", label: "知识审核台 (Admin)" },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/50 dark:border-slate-800/50 bg-white/80 dark:bg-slate-950/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center space-x-2">
            <span className="font-serif font-bold text-lg tracking-wider text-emerald-900 dark:text-emerald-100">
              珞珈数智助教
            </span>
          </Link>
          <nav className="flex items-center space-x-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  pathname === link.href
                    ? "bg-emerald-100/50 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-100"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/50 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800/50"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center">
          {/* User profile / settings could go here */}
          <div className="text-xs text-slate-500 font-mono">v1.2.0-beta</div>
        </div>
      </div>
    </header>
  );
}
