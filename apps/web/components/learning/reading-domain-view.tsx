"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { 
  BookOpen, 
  FileText, 
  Hash, 
  Sparkles, 
  ShieldCheck, 
  PenTool, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  ExternalLink,
  ChevronRight,
  MessageSquare
} from "lucide-react";
import { MathMarkdown, MathView } from "@/components/math-view";
import { 
  AtelierFolioCard, 
  ConditionPillarBadge, 
  Notice, 
  learningButton, 
  learningButtonSecondary, 
  learningInput 
} from "./learning-shell";
import { 
  learningRequest, 
  stableRequestId, 
  type ReadingUnit, 
  type ReadingDocument, 
  type ReadingNote 
} from "@/lib/learning-api";
import { getCurrentUserId } from "@/lib/demo-auth";
import { notesForSource } from "@/lib/learning-input";
import { ReadingExplanation } from "./reading-explanation";
import { ReadingDiscussion } from "./reading-discussion";
import {readingSourceRef, type ReadingContextRef} from "@/lib/learning-context";

export interface ReadingDomainViewProps {
  mode: "full" | "canvas";
  initialUnitId?: string;
  initialReference?: ReadingContextRef;
  onDiscuss?: (ref: ReadingContextRef, prompt: string) => void;
}

export function ReadingDomainView({
  mode,
  initialUnitId,
  initialReference,
  onDiscuss,
}: ReadingDomainViewProps) {
  const initialSelection = useRef({mode, reference: initialReference});
  const [units, setUnits] = useState<ReadingUnit[]>([]);
  const [selected, setSelected] = useState<string>(initialReference?.section_id === null ? initialReference.source_id : initialUnitId || "NA_NEWTON");
  const [documentId, setDocumentId] = useState("");
  const [documents, setDocuments] = useState<{ id: string; filename: string }[]>([]);
  const [doc, setDoc] = useState<ReadingDocument | null>(null);
  const [sectionId, setSectionId] = useState("0");
  const [notes, setNotes] = useState<ReadingNote[]>([]);
  const [note, setNote] = useState("");
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  // 初始化加载真实数据
  useEffect(() => {
    const {mode, reference: initialReference} = initialSelection.current;
    let active = true;
    const params = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;
    const urlUnit = mode === "full" ? params?.get("unit") : null;
    if (urlUnit) setSelected(urlUnit);

    Promise.all([
      learningRequest<{ units: ReadingUnit[] }>("/reading/units"),
      learningRequest<{ notes: ReadingNote[] }>("/reading/notes"),
      learningRequest<{ documents: { id: string; filename: string }[] }>("/reading/documents"),
    ])
      .then(async ([unitsRes, notesRes, docsRes]) => {
        if (!active) return;
        setUnits(unitsRes.units);
        setNotes(notesRes.notes);
        setDocuments(docsRes.documents);

        const savedDocId = mode === "canvas" && initialReference?.section_id != null ? initialReference.source_id : params?.get("document");
        if (savedDocId) {
          const loadedDoc = await learningRequest<ReadingDocument>(`/reading/documents/${encodeURIComponent(savedDocId)}`);
          if (!active) return;
          setDoc(loadedDoc);
          setDocumentId(savedDocId);
          const savedSection = mode === "canvas" ? initialReference?.section_id : params?.get("section");
          setSectionId(
            loadedDoc.sections.some((s) => s.id === savedSection)
              ? savedSection!
              : loadedDoc.sections[0]?.id ?? "0"
          );
        }
      })
      .catch((e) => {
        if (active) setError(e instanceof Error ? e.message : "读取教材文献失败");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const unit = units.find((u) => u.id === selected) || units[0];
  const section = doc?.sections.find((s) => s.id === sectionId) || doc?.sections[0];
  const sourceId = doc ? doc.id : (unit?.id ?? "");
  const sourceHash = doc ? doc.source_hash : (unit?.source_hash ?? "");
  const displayedQuote = doc ? (section?.quote ?? "") : (unit?.quote ?? "");
  const visibleNotes = notesForSource(notes, sourceId, doc ? sectionId : null);
  const draftKey = sourceId ? `reading-note:${getCurrentUserId()}:${sourceId}:${sectionId}` : null;

  // 恢复本地存储的笔记草稿
  useEffect(() => {
    if (draftKey) {
      setNote(localStorage.getItem(draftKey) ?? "");
    }
  }, [draftKey]);

  const act = async (action: () => Promise<void>) => {
    setError("");
    setBusy(true);
    try {
      await action();
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setBusy(false);
    }
  };

  // 严格构造 ReadingContextRef（对齐底层契约）
  const buildCurrentReadingRef = (): ReadingContextRef | null => {
    if (!sourceId || !sourceHash) return null;
    try {
      if (doc && section) return readingSourceRef(doc, displayedQuote, section.id);
      if (unit) return readingSourceRef(unit, displayedQuote);
    } catch (error) {setError(error instanceof Error ? error.message : "来源不可用");}
    return null;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center">
        <div className="size-6 animate-spin rounded-full border-2 border-olive-600 border-t-transparent mb-3" />
        <p className="text-xs text-[var(--text-secondary)]">正在加载经典教材与审阅单元…</p>
      </div>
    );
  }

  if (error && units.length === 0) {
    return (
      <div className="p-6">
        <Notice error={error} />
        <button
          type="button"
          onClick={() => window.location.reload()}
          className={learningButtonSecondary}
        >
          重新加载
        </button>
      </div>
    );
  }

  // -------------------------------------------------------------
  // Mode: "canvas"（紧凑分栏工作区视窗）
  // -------------------------------------------------------------
  if (mode === "canvas") {
    return (
      <div className="p-4 sm:p-5 space-y-5">
        <Notice error={error} />

        {/* 顶部：单元选择器 Pills */}
        <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-card)] p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-[var(--text-secondary)] flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-olive-600" />
              <span>课程整理知识包</span>
            </span>
            <Link
              href="/reading"
              target="_blank"
              className="text-[11px] text-olive-700 dark:text-olive-300 hover:underline inline-flex items-center gap-1 font-medium"
            >
              <span>完整研读大厅</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {units.map((u) => {
              const isSelected = !doc && selected === u.id;
              return (
                <button
                  type="button"
                  key={u.id}
                  onClick={() => {
                    setDoc(null);
                    setSelected(u.id);
                    setFeedback("");
                  }}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                    isSelected
                      ? "bg-olive-600 text-white shadow-2xs font-semibold"
                      : "bg-[var(--bg-input)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-paper-200 dark:border-paper-800"
                  }`}
                >
                  {u.title}
                </button>
              );
            })}
          </div>
        </div>

        {/* 定理正文与来源标注卡片 */}
        <AtelierFolioCard
          index="文献切片"
          title={doc ? section?.title : unit?.title}
          badge={
            doc
              ? `用户上传文献 · ${doc.filename} · 待人工核验`
              : `课程大纲知识包 · 版本 ${unit?.graph_revision || "v1"}`
          }
          badgeVariant={doc ? "dai" : "olive"}
          footer={
            <div className="w-full flex flex-wrap items-center justify-between gap-2 text-[11px] text-[var(--text-muted)] font-mono">
              <span>
                {doc && section
                  ? `原文章节字符跨度 ${section.start}–${section.end}`
                  : `全文引用共 ${Array.from(displayedQuote).length} 字符`}
              </span>
              <span className="flex items-center gap-1">
                <Hash className="w-3 h-3" />
                <span>SHA-256指纹: {sourceHash.slice(0, 16)}</span>
              </span>
            </div>
          }
        >
          {/* 原文正文渲染 */}
          <div className="space-y-4">
            <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-input)]/40 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-mono font-semibold text-olive-700 dark:text-olive-300">
                  {doc ? "【用户上传材料摘录 · 未审核】" : "【课程整理包摘录 · 非教材逐字引文】"}
                </span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">
                  指纹仅绑定版本，不代表数学审核
                </span>
              </div>
              <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed text-[var(--text-primary)] font-serif border-l-2 border-olive-600/70 pl-3">
                <MathMarkdown content={displayedQuote} className="!text-sm !leading-7" />
              </div>
            </div>

            {/* 公式展示 */}
            {!doc && unit?.latex && (
              <div className="p-3 rounded-xl bg-paper-100/70 dark:bg-paper-800/60 border border-paper-200 dark:border-paper-700/60">
                <div className="text-[10px] font-mono text-[var(--text-muted)] mb-1">
                  核心迭代算式 (LaTeX)
                </div>
                <MathView math={unit.latex} display />
              </div>
            )}

            {/* 前置条件判定清单 */}
            {!doc && unit && unit.conditions && unit.conditions.length > 0 && (
              <div className="space-y-2 pt-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)]">
                  <ShieldCheck className="w-3.5 h-3.5 text-olive-600" />
                  <span>定理适用前置条件约束（{unit.conditions.length} 项）</span>
                </div>
                <div className="space-y-1.5">
                  {unit.conditions.map((c, idx) => (
                    <div
                      key={`${unit.condition_hash}-${idx}`}
                      className="p-2.5 rounded-lg bg-olive-500/5 border border-olive-500/15 text-xs text-olive-800 dark:text-olive-200 font-mono"
                    >
                      {c}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 随堂辨析探针 */}
            {!doc && unit && unit.question && (
              <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-linear-to-br from-paper-100/60 to-transparent p-4 space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-olive-700 dark:text-olive-300">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>随堂条件辨析（助教启发探针）</span>
                </div>
                <p className="text-xs text-[var(--text-primary)] font-medium">
                  {unit.question}
                </p>

                {/* 选项按钮 */}
                <div className="flex flex-wrap gap-2">
                  {unit.options.map((opt, i) => (
                    <button
                      type="button"
                      key={opt}
                      disabled={busy}
                      onClick={() =>
                        act(async () => {
                          const res = await learningRequest<{ reference_match: boolean; explanation: string }>(
                            `/reading/units/${unit.id}/condition-attempts`,
                            { option: i, source_hash: unit.source_hash }
                          );
                          setFeedback(`${res.reference_match ? "✓ 判定准确" : "△ 条件未足"}：${res.explanation}`);
                        })
                      }
                      className="px-3 py-1.5 rounded-lg border border-paper-300 dark:border-paper-700 bg-[var(--bg-card)] text-xs hover:border-olive-600 transition-colors"
                    >
                      {opt}
                    </button>
                  ))}
                </div>

                {feedback && (
                  <div className="p-2.5 rounded-lg bg-olive-500/10 border border-olive-500/20 text-xs text-olive-900 dark:text-olive-100">
                    {feedback}
                  </div>
                )}

                {/* 一键带入对话研讨 */}
                {onDiscuss && (
                  <div className="pt-2 border-t border-paper-200/50 dark:border-paper-800/50 flex items-center justify-between">
                    <span className="text-[11px] text-[var(--text-muted)]">
                      遇到未解条件疑惑？
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        const ref = buildCurrentReadingRef();
                        if (ref) {
                          onDiscuss(
                            ref,
                            `请围绕《${unit.title}》的核心前提条件，解答随堂思考题：“${unit.question}”。请引导我推导其反例或收敛阶退化原因。`
                          );
                        }
                      }}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-olive-600 hover:bg-olive-700 text-white shadow-2xs transition-all active:scale-95"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>将选段带入对话研讨</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </AtelierFolioCard>
      </div>
    );
  }

  // -------------------------------------------------------------
  // Mode: "full"（独立阅读大厅完整视窗，带完整三栏与笔记管理）
  // -------------------------------------------------------------
  return (
    <div className="grid gap-8 lg:grid-cols-12 items-start">
      <Notice error={error} />

      {/* 左栏：典籍大纲与文档源 (4 cols) */}
      <aside className="lg:col-span-4 space-y-6">
        <AtelierFolioCard title="课程知识包章节" badge="大纲预置" badgeVariant="olive">
          <p className="text-xs text-[var(--text-secondary)] mb-3">
            聚焦数值分析重点理论前提与收敛性分析：
          </p>
          <div className="space-y-1.5">
            {units.map((u) => {
              const isSelected = !doc && selected === u.id;
              return (
                <button
                  type="button"
                  key={u.id}
                  className={`w-full flex items-center justify-between p-3 rounded-xl text-left text-xs sm:text-sm transition-all duration-200 ${
                    isSelected
                      ? "border-l-4 border-l-olive-600 border-paper-300 dark:border-paper-700 bg-gradient-to-r from-olive-500/10 via-olive-500/5 to-transparent text-olive-900 dark:text-olive-100 font-semibold shadow-xs ring-1 ring-olive-600/20"
                      : "border-l-4 border-l-transparent border-paper-200 dark:border-paper-800/80 bg-[var(--bg-card)] hover:border-paper-300 dark:hover:border-paper-700 hover:shadow-2xs hover:-translate-y-0.5 text-[var(--text-secondary)]"
                  }`}
                  onClick={() => {
                    setDoc(null);
                    setSelected(u.id);
                    setFeedback("");
                    window.history.replaceState(null, "", `/reading?unit=${encodeURIComponent(u.id)}`);
                  }}
                >
                  <span className="truncate pr-2">{u.title}</span>
                  <BookOpen className={`w-4 h-4 shrink-0 ${isSelected ? "text-olive-600" : "text-[var(--text-muted)]"}`} />
                </button>
              );
            })}
          </div>

          {/* 我的上传教材 */}
          <form
            className="mt-6 border-t border-paper-200 dark:border-paper-800 pt-5 space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              act(async () => {
                const value = await learningRequest<ReadingDocument>(`/reading/documents/${encodeURIComponent(documentId.trim())}`);
                setDoc(value);
                setSectionId(value.sections[0]?.id ?? "0");
                setFeedback("");
                window.history.replaceState(null, "", `/reading?document=${encodeURIComponent(value.id)}&section=${value.sections[0]?.id ?? "0"}`);
              });
            }}
          >
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              <FileText className="w-3.5 h-3.5" />
              <span>我的自上传教材 (MinerU)</span>
            </div>
            <p className="text-xs text-[var(--text-secondary)]">按原文章节精准阅读原版 PDF 提取成果：</p>
            <select
              id="documentId"
              name="documentId"
              required
              className={learningInput}
              value={documentId}
              onChange={(e) => setDocumentId(e.target.value)}
            >
              <option value="">选择已解析的教材原书</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                </option>
              ))}
            </select>
            <button type="submit" disabled={busy || !documentId} className={learningButtonSecondary}>
              打开原文章节
            </button>
          </form>

          {doc && (
            <div className="mt-4 pt-3 border-t border-paper-200 dark:border-paper-800">
              <label htmlFor="section" className="block text-xs font-semibold mb-1.5 text-[var(--text-secondary)]">
                当前原文章节
              </label>
              <select
                id="section"
                name="section"
                className={learningInput}
                value={sectionId}
                onChange={(e) => {
                  setSectionId(e.target.value);
                  window.history.replaceState(
                    null,
                    "",
                    `/reading?document=${encodeURIComponent(doc.id)}&section=${encodeURIComponent(e.target.value)}`
                  );
                }}
              >
                {doc.sections.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.title}
                  </option>
                ))}
              </select>
            </div>
          )}
        </AtelierFolioCard>
      </aside>

      {/* 右侧：典籍正文与学者批注主舞台 (8 cols) */}
      <section className="lg:col-span-8 space-y-6">
        {!(doc || unit) ? (
          <div className="p-12 text-center rounded-2xl border border-paper-300/70 bg-[var(--bg-card)] text-sm text-[var(--text-secondary)]">
            暂没有可用的课程材料，请在左侧选择。
          </div>
        ) : (
          <>
            {/* 正文书卷卡片 */}
            <AtelierFolioCard
              title={doc ? section?.title : unit?.title}
              badge={
                doc
                  ? `用户上传文献 · ${doc.filename} · 待人工核验`
                  : `课程知识包精选 · 版本 ${unit?.graph_revision || "v1"}`
              }
              badgeVariant={doc ? "dai" : "olive"}
              footer={
                <div className="w-full flex flex-wrap items-center justify-between text-xs text-[var(--text-muted)] font-mono">
                  <span>{doc && section ? `原文字符跨度 ${section.start}–${section.end}` : "知识图谱版本校验"}</span>
                  <span className="flex items-center gap-1">
                    <Hash className="w-3 h-3" />
                    <span>SHA-256: {sourceHash.slice(0, 16)}</span>
                  </span>
                </div>
              }
            >
              <div className="prose dark:prose-invert max-w-none text-base leading-relaxed text-[var(--text-primary)]">
                <MathMarkdown content={displayedQuote} className="!text-base !leading-8 font-serif" />
              </div>

              {!doc && unit?.latex && (
                <div className="relative group my-6 p-4 sm:p-5 rounded-2xl bg-paper-100 dark:bg-paper-800/60 border border-paper-200 dark:border-paper-700/60 overflow-x-auto shadow-xs">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                      收敛迭代格式 (LaTeX)
                    </span>
                    <button
                      type="button"
                      onClick={() => navigator.clipboard.writeText(unit.latex!)}
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-paper-200 dark:bg-paper-700 text-[var(--text-muted)] hover:text-olive-700 dark:hover:text-olive-300 hover:bg-olive-500/10 transition-all opacity-80 group-hover:opacity-100"
                    >
                      复制 LaTeX
                    </button>
                  </div>
                  <MathView math={unit.latex} display />
                </div>
              )}
            </AtelierFolioCard>

            {/* 定理适用前提与随堂辨析 */}
            {!doc && unit && (
              <AtelierFolioCard
                title="使用这条公式前 · 必备定理条件"
                badge="前置约束"
                badgeVariant="ochre"
              >
                <p className="text-xs text-[var(--text-secondary)] mb-4">
                  任何数值公式的二次收敛定理都不是无条件的。在运用前务必核对以下前提：
                </p>
                <div className="space-y-2 mb-6">
                  {unit.conditions.map((c) => (
                    <ConditionPillarBadge key={c} title={c} status="pending" />
                  ))}
                </div>

                {/* 随堂条件辨析 */}
                <div className="p-4 rounded-xl bg-[var(--bg-tertiary)] border border-paper-200 dark:border-paper-800">
                  <div className="flex items-center gap-2 mb-3 text-xs font-semibold text-olive-800 dark:text-olive-200">
                    <ShieldCheck className="w-4 h-4 text-olive-600" />
                    <span>随堂思考：{unit.question}</span>
                  </div>
                  <div className="flex flex-wrap gap-2.5">
                    {unit.options.map((o, i) => (
                      <button
                        type="button"
                        key={o}
                        disabled={busy}
                        className="rounded-xl border border-paper-300 dark:border-paper-700 bg-[var(--bg-card)] px-3.5 py-2.5 text-xs sm:text-sm font-medium hover:border-olive-600 hover:bg-olive-500/5 transition-all"
                        onClick={() =>
                          act(async () => {
                            const result = await learningRequest<{ reference_match: boolean; explanation: string }>(
                              `/reading/units/${unit.id}/condition-attempts`,
                              { option: i, source_hash: unit.source_hash }
                            );
                            setFeedback(`${result.reference_match ? "与参考判断一致" : "请再仔细核对条件"}：${result.explanation}`);
                          })
                        }
                      >
                        {o}
                      </button>
                    ))}
                  </div>
                  {feedback && (
                    <div className="mt-4 p-3.5 rounded-lg bg-olive-500/10 border border-olive-500/20 text-xs sm:text-sm leading-relaxed text-olive-900 dark:text-olive-100 animate-slide-up">
                      {feedback}
                    </div>
                  )}
                </div>

                <div className="mt-5">
                  <Link
                    href={`/teach-back?unit=${encodeURIComponent(unit.id)}`}
                    className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-olive-700 dark:text-olive-300 hover:underline"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>我来向小珞解释这条条件（费曼讲学） →</span>
                  </Link>
                </div>
              </AtelierFolioCard>
            )}

            {/* 划选即问与段落探讨 */}
            {sourceId && sourceHash && (
              <div className="space-y-6">
                <ReadingExplanation
                  sourceId={sourceId}
                  sourceHash={sourceHash}
                  sectionId={doc ? sectionId : null}
                  quote={displayedQuote}
                  onAnnotate={(annotatedQuote) => {
                    const addition = `原文摘录：\n${annotatedQuote}\n\n我的理解 / 疑问：\n`;
                    const next = note ? `${note}\n\n${addition}` : addition;
                    if (next.length > 4000) {
                      setError("加入后超过笔记的 4000 字符上限，请选择更短的段落或先保存当前笔记。");
                      return;
                    }
                    setNote(next);
                    if (draftKey) localStorage.setItem(draftKey, next);
                    document.getElementById("note")?.focus();
                  }}
                />

                <ReadingDiscussion
                  sourceId={sourceId}
                  sourceHash={sourceHash}
                  sectionId={doc ? sectionId : null}
                  quote={displayedQuote}
                  graphRevision={doc ? null : unit?.graph_revision ?? null}
                  conditions={doc ? [] : unit?.conditions ?? []}
                  conditionHash={doc ? null : unit?.condition_hash ?? null}
                />
              </div>
            )}

            {/* 留存思考笔记 */}
            <AtelierFolioCard title="留下一个问题或理解 · 学者边注" badge="伴读思考" badgeVariant="dai">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  act(async () => {
                    const saved = await learningRequest<ReadingNote>("/reading/notes", {
                      request_id: stableRequestId(localStorage, `note-request:${getCurrentUserId()}:${sourceId}:${sectionId}`, { note, sourceHash }, () => crypto.randomUUID()),
                      source_id: sourceId,
                      source_hash: sourceHash,
                      section_id: doc ? sectionId : null,
                      content: note,
                    });
                    setNotes((prev) => [...prev.filter((n) => n.id !== saved.id), saved]);
                    setNote("");
                    if (draftKey) localStorage.removeItem(draftKey);
                  });
                }}
                className="space-y-3"
              >
                <textarea
                  id="note"
                  name="note"
                  required
                  maxLength={4000}
                  rows={4}
                  className={learningInput}
                  value={note}
                  onChange={(e) => {
                    setNote(e.target.value);
                    if (draftKey) localStorage.setItem(draftKey, e.target.value);
                  }}
                  placeholder="这一步运用了哪些定理条件？为什么仅仅小残差还不足以断定收敛到单根？"
                />
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-[var(--text-muted)] font-mono">{note.length} / 4000 字符</span>
                  <button type="submit" disabled={busy || !note.trim()} className={learningButton}>
                    <PenTool className="w-3.5 h-3.5 mr-1" />
                    保存笔记与来源锚点
                  </button>
                </div>
              </form>

              {visibleNotes.length > 0 && (
                <div className="mt-6 border-t border-paper-200 dark:border-paper-800 pt-5">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
                    本章节的思考笔记存底
                  </h3>
                  <div className="space-y-3">
                    {visibleNotes.map((n) => (
                      <div key={n.id} className="p-3.5 rounded-xl bg-[var(--bg-tertiary)] border border-paper-200 dark:border-paper-800/80">
                        <p className="whitespace-pre-wrap text-xs sm:text-sm leading-relaxed text-[var(--text-primary)] mb-2">
                          {n.content}
                        </p>
                        <div className="flex items-center gap-1 text-[11px] text-[var(--text-muted)] font-mono">
                          <Clock className="w-3 h-3" />
                          <time>{new Date(n.created_at).toLocaleString("zh-CN")}</time>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </AtelierFolioCard>
          </>
        )}
      </section>
    </div>
  );
}
