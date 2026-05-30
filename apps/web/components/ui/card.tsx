import type { HTMLAttributes, ReactNode } from "react";

export function Card({ children, className = "", ...props }: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div className={`rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 p-3 ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100 ${className}`}>{children}</div>;
}
