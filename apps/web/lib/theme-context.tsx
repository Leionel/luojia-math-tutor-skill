"use client";

import {
  createContext,
  useContext,
  useEffect,
  useLayoutEffect,
  useState,
  type ReactNode,
} from "react";

type Theme = "light" | "dark";
type Lang = "zh" | "en";
type Reading = "serif" | "sans";

type ThemeContextValue = {
  theme: Theme;
  lang: Lang;
  reading: Reading;
  toggleTheme: () => void;
  setLang: (lang: Lang) => void;
  setReading: (reading: Reading) => void;
  t: (zh: string, en: string) => string;
};

const ThemeContext = createContext<ThemeContextValue>({
  theme: "light",
  lang: "zh",
  reading: "serif",
  toggleTheme: () => {},
  setLang: () => {},
  setReading: () => {},
  t: (zh) => zh,
});

export function useTheme() {
  return useContext(ThemeContext);
}

function initialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const saved = window.localStorage.getItem("luojia-theme") as Theme | null;
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function initialReading(): Reading {
  if (typeof window === "undefined") return "serif";
  const saved = window.localStorage.getItem("luojia-reading") as Reading | null;
  return saved === "sans" ? "sans" : "serif";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  // First render must match SSR; stored preferences are synced before paint.
  const [theme, setTheme] = useState<Theme>("light");
  const [lang, setLang] = useState<Lang>("zh");
  const [reading, setReading] = useState<Reading>("serif");

  useLayoutEffect(() => {
    setTheme(initialTheme());
    setReading(initialReading());
  }, []);

  useEffect(() => {
    const savedLang = localStorage.getItem("luojia-lang") as Lang | null;
    if (savedLang) setLang(savedLang);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("luojia-theme", theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("luojia-lang", lang);
  }, [lang]);

  useEffect(() => {
    localStorage.setItem("luojia-reading", reading);
  }, [reading]);

  const toggleTheme = () => setTheme((t) => (t === "light" ? "dark" : "light"));
  const t = (zh: string, en: string) => (lang === "zh" ? zh : en);

  return (
    <ThemeContext.Provider
      value={{ theme, lang, reading, toggleTheme, setLang, setReading, t }}
    >
      {children}
    </ThemeContext.Provider>
  );
}
