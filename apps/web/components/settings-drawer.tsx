"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { useTheme } from "@/lib/theme-context";
import { ModelSettings } from "./model-settings";

export function SettingsDrawer() {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { theme, lang, toggleTheme, setLang, t } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <>
      <button
        className="rounded-lg p-2 transition-colors"
        style={{ color: "var(--text-secondary)" }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.background = "var(--bg-hover)")
        }
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
        onClick={() => setIsOpen(true)}
        title={t("\u8bbe\u7f6e", "Settings")}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
      </button>

      {isOpen &&
        mounted &&
        createPortal(
          <div className="fixed inset-0 z-[100] flex">
            <div
              className="fixed inset-0 bg-black/40 dark:bg-black/60"
              onClick={() => setIsOpen(false)}
            />
            <div
              className="relative z-10 w-80 overflow-y-auto bg-[var(--bg-primary)]"
              style={{
                boxShadow: "var(--shadow-lg)",
              }}
            >
              <div
                className="flex items-center justify-between px-5 py-4"
                style={{ borderBottom: "1px solid var(--border-primary)" }}
              >
                <h2
                  className="text-base font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  {t("\u8bbe\u7f6e", "Settings")}
                </h2>
                <button
                  className="rounded-lg p-1.5 transition-colors"
                  style={{ color: "var(--text-muted)" }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "var(--bg-hover)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background = "transparent")
                  }
                  onClick={() => setIsOpen(false)}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
              <div className="p-5 space-y-6">
                {/* Theme toggle */}
                <div>
                  <label
                    className="mb-2 block text-sm font-medium"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {t("\u5916\u89c2\u4e3b\u9898", "Theme")}
                  </label>
                  <div className="flex gap-2">
                    <button
                      className="flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-medium transition-all"
                      style={{
                        background:
                          theme === "light"
                            ? "var(--accent)"
                            : "var(--bg-tertiary)",
                        color:
                          theme === "light" ? "white" : "var(--text-secondary)",
                        border: `1px solid ${theme === "light" ? "var(--accent)" : "var(--border-primary)"}`,
                      }}
                      onClick={() => {
                        if (theme === "dark") toggleTheme();
                      }}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                        />
                      </svg>
                      {t("\u767d\u5929", "Light")}
                    </button>
                    <button
                      className="flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-medium transition-all"
                      style={{
                        background:
                          theme === "dark"
                            ? "var(--accent)"
                            : "var(--bg-tertiary)",
                        color:
                          theme === "dark" ? "white" : "var(--text-secondary)",
                        border: `1px solid ${theme === "dark" ? "var(--accent)" : "var(--border-primary)"}`,
                      }}
                      onClick={() => {
                        if (theme === "light") toggleTheme();
                      }}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                        />
                      </svg>
                      {t("\u591c\u95f4", "Dark")}
                    </button>
                  </div>
                </div>

                {/* Language toggle */}
                <div>
                  <label
                    className="mb-2 block text-sm font-medium"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {t("\u8bed\u8a00", "Language")}
                  </label>
                  <div className="flex gap-2">
                    <button
                      className="flex flex-1 items-center justify-center rounded-lg py-2.5 text-sm font-medium transition-all"
                      style={{
                        background:
                          lang === "zh"
                            ? "var(--accent)"
                            : "var(--bg-tertiary)",
                        color:
                          lang === "zh" ? "white" : "var(--text-secondary)",
                        border: `1px solid ${lang === "zh" ? "var(--accent)" : "var(--border-primary)"}`,
                      }}
                      onClick={() => setLang("zh")}
                    >
                      {"\u4e2d\u6587"}
                    </button>
                    <button
                      className="flex flex-1 items-center justify-center rounded-lg py-2.5 text-sm font-medium transition-all"
                      style={{
                        background:
                          lang === "en"
                            ? "var(--accent)"
                            : "var(--bg-tertiary)",
                        color:
                          lang === "en" ? "white" : "var(--text-secondary)",
                        border: `1px solid ${lang === "en" ? "var(--accent)" : "var(--border-primary)"}`,
                      }}
                      onClick={() => setLang("en")}
                    >
                      English
                    </button>
                  </div>
                </div>

                {/* Divider */}
                <div style={{ borderTop: "1px solid var(--border-primary)" }} />

                {/* Model settings */}
                <ModelSettings />

                {/* Practical Feature Description */}
                <div style={{ borderTop: "1px solid var(--border-primary)", paddingTop: "1.5rem", marginTop: "1.5rem" }}>
                  <label className="mb-2 block text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {t("系统功能说明", "Feature Overview")}
                  </label>
                  <div className="rounded-lg p-3 text-xs leading-relaxed" style={{ background: "var(--bg-tertiary)", color: "var(--text-secondary)", border: "1px solid var(--border-primary)" }}>
                    <ul className="space-y-2 list-disc pl-4">
                      <li><strong>启发引导：</strong>系统采用苏格拉底式提问，不会直接给答案，而是通过多轮对话引导您自己推导。</li>
                      <li><strong>自动错题本：</strong>对话中暴露的薄弱知识点会被自动捕捉并收录进错题本，支持一键 A4 排版打印。</li>
                      <li><strong>多模态与画板：</strong>支持图片上传 OCR 提取，也可在输入框调出全屏草稿板手绘公式、打草稿。</li>
                      <li><strong>动态交互几何：</strong>支持解析并渲染可拖拽的 JSXGraph 交互式数学函数与几何图形。</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>,
          document.body,
        )}
    </>
  );
}
