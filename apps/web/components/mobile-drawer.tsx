"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { X } from "lucide-react";

export function MobileDrawer({ title, side, breakpoint, onClose, children }: {
  title: string; side: "left" | "right"; breakpoint: number;
  onClose: () => void; children: ReactNode;
}) {
  const dialog = useRef<HTMLDivElement>(null);
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const backgrounds: Array<{ element: HTMLElement; inert: boolean }> = [];
    let branch: HTMLElement | null = dialog.current?.parentElement ?? null;
    while (branch && branch !== document.body) {
      for (const sibling of Array.from(branch.parentElement?.children ?? [])) {
        if (sibling !== branch && sibling instanceof HTMLElement) {
          backgrounds.push({ element: sibling, inert: sibling.inert });
          sibling.inert = true;
        }
      }
      branch = branch.parentElement;
    }
    dialog.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (dialog.current?.querySelector('[role="dialog"]')) return;
      if (event.key === "Escape") close.current();
      if (event.key !== "Tab") return;
      const items = Array.from(dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], input, textarea, select, [tabindex="0"]') ?? []).filter(item => item.getClientRects().length);
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    const handleResize = () => { if (window.innerWidth >= breakpoint) close.current(); };
    document.addEventListener("keydown", handleKey);
    window.addEventListener("resize", handleResize);
    return () => {
      document.removeEventListener("keydown", handleKey);
      window.removeEventListener("resize", handleResize);
      backgrounds.forEach(({element, inert}) => { element.inert = inert; });
      document.body.style.overflow = previousOverflow;
      if (previous?.isConnected) previous.focus();
    };
  }, [breakpoint]);
  return <div className="fixed inset-0 z-[80] bg-black/40 backdrop-blur-sm" onClick={onClose}>
    <div ref={dialog} role="dialog" aria-modal="true" aria-label={title} className={`absolute inset-y-0 ${side === "left" ? "left-0" : "right-0"} flex w-[min(360px,calc(100vw-32px))] min-h-0 flex-col bg-[var(--bg-card)] shadow-xl`} onClick={event => event.stopPropagation()}>
      <div className="flex shrink-0 items-center justify-between border-b border-[var(--border-primary)] px-4 py-3">
        <h2 className="font-semibold text-[var(--text-primary)]">{title}</h2>
        <button type="button" aria-label={`关闭${title}`} className="flex size-12 items-center justify-center rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] focus-visible:outline-2 focus-visible:outline-olive-600" onClick={onClose}><X className="h-5 w-5" /></button>
      </div>
      <div className="min-h-0 flex-1 overflow-hidden">{children}</div>
    </div>
  </div>;
}
