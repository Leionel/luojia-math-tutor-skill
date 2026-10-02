import type { Metadata } from "next";
import type { ReactNode } from "react";
import { ThemeProvider } from "@/lib/theme-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "珞珈数智助教",
  icons: { icon: "/brand/luojia-logo.png", apple: "/brand/luojia-logo.png" },
  description:
    "面向大学数学课程的 AI Tutor",
};

const desmosKey = process.env.NEXT_PUBLIC_DESMOS_API_KEY;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@400;500;700&family=ZCOOL+XiaoWei&display=swap"
          rel="stylesheet"
        />
        <script
          dangerouslySetInnerHTML={{
            __html:
              '(function(){try{var t=localStorage.getItem("luojia-theme");var d=t?t==="dark":window.matchMedia("(prefers-color-scheme: dark)").matches;if(d){document.documentElement.classList.add("dark");}}catch(e){}})();',
          }}
        />
        {desmosKey ? (
          <script
            src={`https://www.desmos.com/api/v1.9/calculator.js?apiKey=${desmosKey}`}
            async
          />
        ) : null}
      </head>
      <body>
        <ThemeProvider>
          <div className="min-h-screen flex flex-col">
            <main className="flex-1 flex flex-col">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
