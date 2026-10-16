import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "success" | "danger";
  size?: "sm" | "md" | "lg" | "icon";
  children: ReactNode;
}) {
  const base = "inline-flex items-center justify-center rounded-md font-medium transition-colors disabled:opacity-50";
  const variants: Record<string, string> = {
    primary: "bg-olive-600 text-[#faf7f2] hover:bg-olive-700 dark:bg-olive-500 dark:hover:bg-olive-400",
    secondary: "bg-paper-200 text-ink hover:bg-paper-300 dark:bg-paper-800 dark:hover:bg-paper-700 dark:text-paper-100",
    outline: "border border-paper-300 bg-paper-50 text-paper-600 hover:bg-paper-100 dark:border-paper-700 dark:bg-paper-950 dark:text-paper-200 dark:hover:bg-paper-900",
    ghost: "text-paper-500 hover:bg-paper-200 dark:text-paper-400 dark:hover:bg-paper-800",
    success: "bg-olive-500 text-[#faf7f2] hover:bg-olive-600 dark:bg-olive-400 dark:hover:bg-olive-500",
    danger: "bg-cinnabar-600 text-[#faf7f2] hover:bg-cinnabar-700 dark:bg-cinnabar-500 dark:hover:bg-cinnabar-400",
  };
  const sizes: Record<string, string> = {
    sm: "px-2 py-1 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-5 py-2.5 text-base",
    icon: "p-0 flex items-center justify-center",
  };
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  );
}
