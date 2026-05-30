"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

type Theme = "light" | "dark";
type Lang = "zh" | "en";

type ThemeContextValue = {
  theme: Theme;
  lang: Lang;
  toggleTheme: () => void;
  setLang: (lang: Lang) => void;
  t: (zh: string, en: string) => string;
};

const ThemeContext = createContext<ThemeContextValue>({
  theme: "light",
  lang: "zh",
  toggleTheme: () => {},
  setLang: () => {},
  t: (zh) => zh,
});

export function useTheme() {
  return useContext(ThemeContext);
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light");
  const [lang, setLang] = useState<Lang>("zh");

  useEffect(() => {
    const saved = localStorage.getItem("luojia-theme") as Theme | null;
    if (saved) setTheme(saved);
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

  const toggleTheme = () => setTheme((t) => (t === "light" ? "dark" : "light"));
  const t = (zh: string, en: string) => (lang === "zh" ? zh : en);

  return (
    <ThemeContext.Provider value={{ theme, lang, toggleTheme, setLang, t }}>
      {children}
    </ThemeContext.Provider>
  );
}
