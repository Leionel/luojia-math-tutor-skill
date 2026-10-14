"use client";
import Link from "next/link";
import { notesForSource } from "@/lib/learning-input";
import { useEffect, useState } from "react";
import { MathMarkdown, MathView } from "@/components/math-view";
import { 
  LearningShell, 
  Notice, 
  learningButton, 
  learningButtonSecondary,
  learningInput, 
  AtelierFolioCard,
  ConditionPillarBadge,
  SocraticCompanionBubble
} from "@/components/learning/learning-shell";
import { 
  learningRequest, 
  stableRequestId, 
  type ReadingUnit, 
  type ReadingDocument, 
  type ReadingNote 
} from "@/lib/learning-api";
import { getCurrentUserId } from "@/lib/demo-auth";
import { ReadingDiscussion } from "@/components/learning/reading-discussion";
import { ReadingExplanation } from "@/components/learning/reading-explanation";
import { 
  BookOpen, 
  FileText, 
  ArrowRight, 
  HelpCircle, 
  PenTool, 
  ShieldCheck, 
  Hash, 
  Clock, 
  Sparkles 
} from "lucide-react";

export default function ReadingPage() {
  const [units, setUnits] = useState<ReadingUnit[]>([]);
  const [selected, setSelected] = useState("NA_NEWTON");
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

  useEffect(() => {
    const unit = new URLSearchParams(window.location.search).get("unit");
    if (unit) setSelected(unit);
    Promise.all([
      learningRequest<{ units: ReadingUnit[] }>("/reading/units"),
      learningRequest<{ notes: ReadingNote[] }>("/reading/notes"),
      learningRequest<{ documents: { id: string; filename: string }[] }>("/reading/documents"),
    ])
      .then(async ([a, b, c]) => {
        setUnits(a.units);
        setNotes(b.notes);
        setDocuments(c.documents);
        const params = new URLSearchParams(window.location.search);
        const savedId = params.get("document");
        if (savedId) {
          const value = await learningRequest<ReadingDocument>(`/reading/documents/${encodeURIComponent(savedId)}`);
          setDoc(value);
          setDocumentId(savedId);
          setSectionId(value.sections.some((s) => s.id === params.get("section")) ? params.get("section")! : value.sections[0]?.id ?? "0");
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const unit = units.find((u) => u.id === selected);
  const section = doc?.sections.find((s) => s.id === sectionId);
  const sourceId = doc?.id ?? unit?.id;
  const sourceHash = doc?.source_hash ?? unit?.source_hash;
  const visibleNotes = notesForSource(notes, sourceId, doc ? sectionId : null);
  const draftKey = sourceId ? `reading-note:${getCurrentUserId()}:${sourceId}:${sectionId}` : null;

  useEffect(() => {
    if (draftKey) setNote(localStorage.getItem(draftKey) ?? "");
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

  return (
    <LearningShell
      title="定理研读 · 前提与边界"
      description="精读教材经典选段与公式推导，严密辨析定理适用的前置约束条件，留下学者思考与证据锚点。"
    >
      <Notice error={error} />

      <div className="grid gap-8 lg:grid-cols-12 items-start">
        {/* 左栏：典籍大纲与文档源 (3.5 cols) */}
        <aside className="lg:col-span-4 space-y-6">
          <AtelierFolioCard title="课程知识包章节" badge="核心摘录" badgeVariant="olive">
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

        {/* 右侧：典籍正文与学者批注主舞台 (8.5 cols) */}
        <section className="lg:col-span-8 space-y-6">
          {loading ? (
            <div className="p-12 text-center rounded-2xl border border-paper-300/70 bg-[var(--bg-card)] text-sm text-[var(--text-secondary)]">
              正在展开教材文献来源…
            </div>
          ) : !(doc || unit) ? (
            <div className="p-12 text-center rounded-2xl border border-paper-300/70 bg-[var(--bg-card)] text-sm text-[var(--text-secondary)]">
              暂没有可用的课程材料，请在左侧选择。
            </div>
          ) : (
            <>
              {/* 正文书卷卡片 */}
              <AtelierFolioCard
                title={doc ? section?.title : unit?.title}
                badge={doc ? `原版 · ${doc.filename}` : "课程知识包精选"}
                badgeVariant={doc ? "dai" : "olive"}
                footer={
                  <div className="w-full flex flex-wrap items-center justify-between text-xs text-[var(--text-muted)] font-mono">
                    <span>{doc && section ? `原文字符跨度 ${section.start}–${section.end}` : "知识图谱版本校验"}</span>
                    <span className="flex items-center gap-1">
                      <Hash className="w-3 h-3" />
                      SHA: {sourceHash?.slice(0, 16)}
                    </span>
                  </div>
                }
              >
                <div className="prose dark:prose-invert max-w-none text-base leading-relaxed text-[var(--text-primary)]">
                  <MathMarkdown content={doc ? section?.quote ?? "" : unit?.quote ?? ""} className="!text-base !leading-8 font-serif" />
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
                    quote={doc ? section?.quote ?? "" : unit?.quote ?? ""}
                    onAnnotate={(quote) => {
                      const addition = `原文摘录：\n${quote}\n\n我的理解 / 疑问：\n`;
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
                    quote={doc ? section?.quote ?? "" : unit?.quote ?? ""}
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
    </LearningShell>
  );
}
