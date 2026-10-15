export type ResizablePane = "sidebar" | "learning" | "workspace";

export const PANE_CONSTRAINTS: Record<
  ResizablePane,
  { min: number; max: number; default: number }
> = {
  sidebar: { min: 200, max: 600, default: 260 },
  learning: { min: 200, max: 600, default: 320 },
  workspace: { min: 380, max: 1000, default: 580 },
};

export function clampPaneWidth(pane: ResizablePane, rawWidth: number): number {
  const { min, max } = PANE_CONSTRAINTS[pane];
  if (!Number.isFinite(rawWidth)) return PANE_CONSTRAINTS[pane].default;
  return Math.min(max, Math.max(min, Math.round(rawWidth)));
}

export function defaultPaneWidth(pane: ResizablePane): number {
  return PANE_CONSTRAINTS[pane].default;
}

export interface CompositionEnterContext {
  key: string;
  shiftKey?: boolean;
  isComposing: boolean;
  lastCompositionEndedAt: number;
  now: number;
  keyCode?: number;
  isCoarsePointer?: boolean;
  cooldownMs?: number;
}

/**
 * 借鉴 Claude ChatComposer 交互物理学：
 * 判定当前按键是否属于中文输入法（CJK IME）回车选词或应被拦截的状态。
 * 返回 true 表示应被拦截（禁止提交），返回 false 表示为用户确认的正式提交。
 */
export function shouldInterceptCompositionEnter(ctx: CompositionEnterContext): boolean {
  if (ctx.key !== "Enter") return true;
  if (ctx.shiftKey) return true;
  if (ctx.isCoarsePointer) return true;
  if (ctx.isComposing) return true;
  if (ctx.keyCode === 229) return true;

  const cooldown = ctx.cooldownMs ?? 60;
  const isRecentlyComposing = ctx.now - ctx.lastCompositionEndedAt < cooldown;
  if (isRecentlyComposing) return true;

  return false;
}
