"use client";

import { useRef, useState } from "react";
import { BookOpen, FileUp, Loader2 } from "lucide-react";
import { generateDocumentNote, uploadTextbook } from "@/lib/api";

type Phase = "idle" | "uploading" | "organizing" | "done";

export function DocumentNoteUpload({
  withMistakes = false,
  description,
  onGenerated,
}: {
  withMistakes?: boolean;
  description: string;
  onGenerated: () => void;
}) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setError(null);
    setMessage(null);
    setPhase("uploading");
    try {
      const result = await uploadTextbook(file);
      if (!result.document_id) {
        throw new Error("请上传 PDF / Word / PPT 教材文件，图片无法用于整理笔记。");
      }
      setPhase("organizing");
      await generateDocumentNote("demo-user", result.document_id, withMistakes);
      setPhase("done");
      setMessage("笔记已生成，可在列表中查看。");
      onGenerated();
    } catch (err) {
      setPhase("idle");
      setError(err instanceof Error ? err.message : "上传或整理失败");
      return;
    }
    // Allow the success message to linger before resetting the button.
    setTimeout(() => setPhase("idle"), 4000);
  }

  const busy = phase === "uploading" || phase === "organizing";

  return (
    <div className="rounded-xl border border-[#617a55]/20 bg-gradient-to-br from-[#617a55]/10 to-transparent p-4">
      <div className="mb-2 flex items-center gap-1.5 text-xs font-bold tracking-wider text-[#617a55]">
        <BookOpen className="w-4 h-4" />
        教材整理
      </div>
      <p className="mb-3 text-[11px] leading-relaxed text-[var(--text-secondary)]">
        {description}
      </p>
      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.docx,.pptx,.doc"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          e.target.value = "";
          if (file) void handleFile(file);
        }}
      />
      <button
        disabled={busy}
        onClick={() => fileRef.current?.click()}
        className="flex w-full items-center justify-center gap-2 rounded-lg py-2 text-xs font-bold bg-[#617a55] text-white transition-colors hover:bg-[#4e6344] disabled:opacity-60"
      >
        {phase === "uploading" ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> MinerU 解析中（可能需要 1–2 分钟）…
          </>
        ) : phase === "organizing" ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> AI 整理笔记中…
          </>
        ) : (
          <>
            <FileUp className="w-3.5 h-3.5" /> 选择教材文件
          </>
        )}
      </button>
      {error ? (
        <div className="mt-2 text-[11px] text-rose-600 dark:text-rose-400">{error}</div>
      ) : message ? (
        <div className="mt-2 text-[11px] text-emerald-600 dark:text-emerald-400">{message}</div>
      ) : null}
    </div>
  );
}
