"use client";

import { useState, useEffect, useRef } from "react";
import { Search, X, BookOpen, AlertCircle, FileText, ArrowRight, Loader2 } from "lucide-react";
import { searchGlobal, type GlobalSearchResultItem } from "@/lib/api";
import { MathMarkdown } from "./math-view";

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectResult?: (textToInsert: string) => void;
}

const CATEGORIES = [
  { key: "all", label: "全部" },
  { key: "curriculum", label: "教材定理" },
  { key: "mistakes", label: "错题复盘" },
  { key: "notes", label: "随堂笔记" },
] as const;

export function GlobalSearchModal({ isOpen, onClose, onSelectResult }: GlobalSearchModalProps) {
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [results, setResults] = useState<GlobalSearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery("");
      setResults([]);
      setSearched(false);
    }
  }, [isOpen]);

  // ESC 键监听
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // 防抖搜索
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSearched(false);
      setLoading(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchGlobal(query.trim(), activeCategory);
        setResults(data.items || []);
        setSearched(true);
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        setLoading(false);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [query, activeCategory]);

  if (!isOpen) return null;

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case "curriculum":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
            <BookOpen className="w-3 h-3" /> 教材定理
          </span>
        );
      case "mistakes":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20">
            <AlertCircle className="w-3 h-3" /> 错题复盘
          </span>
        );
      case "notes":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20">
            <FileText className="w-3 h-3" /> 随堂笔记
          </span>
        );
      default:
        return null;
    }
  };

  const handleInsert = (item: GlobalSearchResultItem) => {
    let insertText = "";
    if (item.category === "curriculum") {
      insertText = item.formula
        ? `请问关于【${item.title}】：\n$$${item.formula}$$\n应如何理解其几何意义与应用？`
        : `请问关于【${item.title}】：${item.content}\n在解题中该如何把握？`;
    } else if (item.category === "mistakes") {
      insertText = `我想针对历史错题【${item.title}】进行变式专项突破，请帮我剖析错因并出题。`;
    } else {
      insertText = `我想探讨笔记中的这部分内容：${item.title}\n${item.content}`;
    }

    if (onSelectResult) {
      onSelectResult(insertText);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-20 px-4 bg-stone-900/40 dark:bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-2xl bg-[var(--bg-card,#fff)] text-[var(--text-primary,#262626)] border border-[var(--border-subtle,#e5e5e5)] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[82vh] animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 顶部搜索条 */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-[var(--border-subtle,#e5e5e5)] bg-[var(--bg-card)]">
          <Search className="w-5 h-5 text-[var(--text-secondary)] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索教材定理、知识图谱、错题复盘与随堂笔记... (如: 泰勒、特征值、极限)"
            className="flex-1 bg-transparent text-sm sm:text-base outline-none placeholder:text-[var(--text-tertiary)]"
          />
          {loading && <Loader2 className="w-4 h-4 animate-spin text-[var(--text-secondary)] shrink-0" />}
          {query && !loading && (
            <button
              onClick={() => setQuery("")}
              className="p-1 rounded-full text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={onClose}
            className="text-xs px-2 py-1 rounded bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            ESC
          </button>
        </div>

        {/* 分类切换栏 */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border-subtle,#e5e5e5)] bg-[var(--bg-card)]/60 text-xs">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.key}
              onClick={() => setActiveCategory(cat.key)}
              className={`px-3 py-1 rounded-full font-medium transition-all ${
                activeCategory === cat.key
                  ? "bg-olive-600 text-white shadow-xs dark:bg-olive-500"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
              }`}
            >
              {cat.label}
            </button>
          ))}
          <span className="ml-auto text-[11px] text-[var(--text-tertiary)]">
            共找到 {results.length} 项
          </span>
        </div>

        {/* 结果列表 */}
        <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3">
          {loading && !results.length && (
            <div className="py-12 flex flex-col items-center justify-center text-[var(--text-secondary)] gap-2">
              <Loader2 className="w-6 h-6 animate-spin text-olive-600 dark:text-olive-400" />
              <p className="text-xs">正在翻阅九章草堂藏书阁...</p>
            </div>
          )}

          {!loading && searched && results.length === 0 && (
            <div className="py-12 text-center text-[var(--text-secondary)]">
              <p className="text-sm font-medium">未检索到与 &quot;{query}&quot; 匹配的内容</p>
              <p className="text-xs text-[var(--text-tertiary)] mt-1">
                可尝试搜索教材核心名词，或在下方开启“联网探微”获取全网资料。
              </p>
            </div>
          )}

          {!searched && !loading && (
            <div className="py-8 text-center text-[var(--text-secondary)]">
              <p className="text-xs text-[var(--text-tertiary)]">
                输入定理名称、数学术语或题目关键字，即可快速带入草堂研讨
              </p>
              <div className="flex flex-wrap justify-center gap-2 mt-3">
                {["泰勒公式", "拉格朗日中值定理", "矩阵的秩", "逆矩阵", "特征值与特征向量", "贝叶斯公式"].map((tag) => (
                  <button
                    key={tag}
                    onClick={() => setQuery(tag)}
                    className="px-2.5 py-1 rounded-full text-xs bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:text-olive-700 dark:hover:text-olive-300 transition-colors"
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {results.map((item) => (
            <div
              key={item.id}
              className="group p-3 sm:p-3.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] hover:border-olive-500/50 hover:shadow-md transition-all flex flex-col gap-2"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {getCategoryBadge(item.category)}
                  <h4 className="font-semibold text-sm text-[var(--text-primary)] group-hover:text-olive-700 dark:group-hover:text-olive-400 transition-colors">
                    {item.title}
                  </h4>
                </div>
                <span className="text-[11px] text-[var(--text-tertiary)] truncate max-w-[180px]">
                  {item.subtitle}
                </span>
              </div>

              {/* 摘要与公式 */}
              <div className="text-xs text-[var(--text-secondary)] line-clamp-3 leading-relaxed">
                <MathMarkdown content={item.content} />
              </div>

              {item.formula && (
                <div className="p-2 rounded-lg bg-[var(--bg-hover)]/70 text-xs overflow-x-auto text-center border border-[var(--border-subtle)]/50">
                  <MathMarkdown content={`$$${item.formula}$$`} />
                </div>
              )}

              {/* 操作栏 */}
              <div className="flex items-center justify-end pt-1">
                <button
                  onClick={() => handleInsert(item)}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-olive-600/10 text-olive-700 dark:text-olive-300 hover:bg-olive-600 hover:text-white transition-all"
                >
                  <span>带入草堂研讨</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
