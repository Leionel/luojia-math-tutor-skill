import type { Metadata } from "next";
import type { ReactNode } from "react";
import { ThemeProvider } from "@/lib/theme-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "\u73de\u73c8\u6570\u667a\u52a9\u6559",
  description:
    "\u9762\u5411\u5927\u5b66\u6570\u5b66\u8bfe\u7a0b\u7684 AI Tutor",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        <script src="https://www.desmos.com/api/v1.9/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6" async />
      </head>
      <body>
        <div className="bg-noise" />
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
