import type { TextareaHTMLAttributes } from "react";

export function Textarea({ className = "", ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const hasBg = className.includes("bg-");
  const hasBorder = className.includes("border-");
  return (
    <textarea
      className={`w-full resize-none rounded-md p-3 text-sm outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 dark:text-slate-200 ${
        hasBg ? "" : "bg-white dark:bg-slate-950"
      } ${
        hasBorder ? "" : "border border-slate-200 dark:border-slate-800"
      } ${className}`}
      {...props}
    />
  );
}
