"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConfirmDialogProps {
  open: boolean;
  /** Either a sync void function, or an async function that returns a Promise.
   * If async and it throws, the dialog stays open and shows the error. */
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "default" | "destructive";
}

export function ConfirmDialog({
  open,
  onConfirm,
  onCancel,
  title,
  description,
  confirmText = "确定",
  cancelText = "取消",
  variant = "default",
}: ConfirmDialogProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const confirmBtnRef = useRef<HTMLButtonElement | null>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);

  // Reset transient state every time the dialog opens.
  useEffect(() => {
    if (open) {
      setBusy(false);
      setError(null);
      previouslyFocusedRef.current = document.activeElement as HTMLElement | null;
      // Autofocus the confirm button after mount.
      requestAnimationFrame(() => confirmBtnRef.current?.focus());
    } else if (previouslyFocusedRef.current) {
      previouslyFocusedRef.current.focus();
    }
  }, [open]);

  // ESC to cancel, Tab trap inside panel.
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !busy) {
        e.preventDefault();
        onCancel();
      } else if (e.key === "Tab" && panelRef.current) {
        const focusables = panelRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, busy, onCancel]);

  const handleConfirm = async () => {
    if (busy) return;
    setError(null);
    try {
      const result = onConfirm();
      if (result && typeof (result as Promise<void>).then === "function") {
        setBusy(true);
        await result;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败，请稍后重试。");
      setBusy(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-dialog-title"
          aria-describedby={description ? "confirm-dialog-desc" : undefined}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => !busy && onCancel()}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          {/* Panel */}
          <motion.div
            ref={panelRef}
            className={cn(
              "relative w-full max-w-sm overflow-hidden rounded-2xl border bg-white dark:bg-[var(--bg-card)] p-6 shadow-2xl",
              variant === "destructive"
                ? "border-rose-500/20"
                : "border-[var(--border-primary)]",
            )}
            initial={{ opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 20 }}
            transition={{ type: "spring", stiffness: 300, damping: 28 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Decorative gradient blob */}
            <div
              className={cn(
                "pointer-events-none absolute -top-12 -right-12 h-32 w-32 rounded-full opacity-20 blur-3xl",
                variant === "destructive"
                  ? "bg-rose-500"
                  : "bg-[var(--accent, #617a55)]",
              )}
            />

            <h3
              id="confirm-dialog-title"
              className="text-lg font-bold text-[var(--text-primary)] mb-2"
            >
              {title}
            </h3>

            {description && (
              <p
                id="confirm-dialog-desc"
                className="text-sm leading-relaxed text-[var(--text-secondary)] mb-6"
              >
                {description}
              </p>
            )}

            {error && (
              <div className="mb-4 flex items-start gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-500">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-3">
              {cancelText && (
                <button
                  onClick={onCancel}
                  disabled={busy}
                  className="rounded-lg px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors disabled:opacity-50"
                >
                  {cancelText}
                </button>
              )}
              <button
                ref={confirmBtnRef}
                onClick={handleConfirm}
                disabled={busy}
                className={cn(
                  "inline-flex items-center gap-2 rounded-lg px-5 py-2 text-sm font-bold text-white shadow-lg transition-all active:scale-95 disabled:opacity-70 disabled:active:scale-100",
                  variant === "destructive"
                    ? "bg-rose-500 hover:bg-rose-600 shadow-rose-500/30"
                    : "bg-[#617a55] hover:bg-[#4e6344] shadow-[#617a55]/30",
                )}
              >
                {busy && <Loader2 className="h-4 w-4 animate-spin" />}
                {busy ? "处理中…" : confirmText}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
