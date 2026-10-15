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

/**
 * 视口图钉与吸附算法（逆向自 Claude useClaudeScrollPinning）：
 * 当距离底部小于容差 (默认 40px) 时判定为吸附状态 (Pinned)
 */
export function computePinState(
  scrollHeight: number,
  scrollTop: number,
  clientHeight: number,
  pinTolerance = 40
): { isPinned: boolean; distanceFromBottom: number } {
  const distanceFromBottom = Math.max(0, scrollHeight - scrollTop - clientHeight);
  return {
    distanceFromBottom,
    isPinned: distanceFromBottom <= pinTolerance,
  };
}

/**
 * 是否浮出“跳至最新”快捷按钮：
 * 远离底部超过阈值 (默认 120px) 时展示
 */
export function shouldShowJumpControl(distanceFromBottom: number, threshold = 120): boolean {
  return distanceFromBottom > threshold;
}

/**
 * 用户交互冷却保护判定：
 * 距离用户最后一次主动滚轮/触控小于冷却窗口 (默认 150ms) 时，禁止自动滚底
 */
export function isUserScrollCooldownActive(
  lastUserInputAt: number,
  now: number,
  cooldownMs = 150
): boolean {
  return now - lastUserInputAt <= cooldownMs;
}

/**
 * 7-Stop 非线性边缘渐变羽化尺寸感知计算：
 * 触顶 (scrollTop <= 2) 时 top 为 0，避免顶栏白边；触底时 bottom 为 0
 */
export function computeEdgeFades(
  scrollTop: number,
  distanceFromBottom: number,
  fadeSize = 24
): { fadeTop: number; fadeBottom: number } {
  return {
    fadeTop: scrollTop <= 2 ? 0 : fadeSize,
    fadeBottom: distanceFromBottom <= 2 ? 0 : fadeSize,
  };
}

/**
 * 思维链折叠状态机计算（逆向自 Claude ThinkingAccordion）：
 * 生成活跃态 (isThinkingLive = true) 下强制锁定展开 (open = true)，禁止用户收起；
 * 生成结束后交还控制权，遵循用户本地展开偏好 (userExpanded)。
 */
export function computeThinkingAccordionState(params: {
  isThinkingLive: boolean;
  userExpanded: boolean;
}): { isOpen: boolean; canToggle: boolean } {
  if (params.isThinkingLive) {
    return { isOpen: true, canToggle: false };
  }
  return { isOpen: params.userExpanded, canToggle: true };
}

/**
 * 格式化思维链为引用探讨文本
 */
export function formatThoughtAsQuote(rawThought: string): string {
  const trimmed = rawThought.trim();
  if (!trimmed) return "";
  return trimmed
    .split("\n")
    .map((line) => `> ${line}`)
    .join("\n");
}


