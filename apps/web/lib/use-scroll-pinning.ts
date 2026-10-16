import { useState, useRef, useEffect, useCallback } from "react";
import {
  computePinState,
  shouldShowJumpControl,
  isUserScrollCooldownActive,
  computeEdgeFades,
} from "./interaction-physics";

export interface ScrollPinningOptions {
  pinTolerance?: number; // 默认 40px：底部边缘吸附容差
  jumpThreshold?: number; // 默认 120px：离开底部多远显示“跳至最新”
  userCooldownMs?: number; // 默认 150ms：用户主动操作冷却保护窗口
  fadeSize?: number; // 默认 24px：边缘羽化尺寸
}

export function useScrollPinning(
  dependencies: unknown[],
  options: ScrollPinningOptions = {}
) {
  const {
    pinTolerance = 40,
    jumpThreshold = 120,
    userCooldownMs = 150,
    fadeSize = 24,
  } = options;

  const containerRef = useRef<HTMLDivElement>(null);
  const [isPinned, setIsPinned] = useState(true);
  const [showJumpControl, setShowJumpControl] = useState(false);
  const [fadeTop, setFadeTop] = useState(0);
  const [fadeBottom, setFadeBottom] = useState(0);

  const lastUserInputAt = useRef(0);
  const programmaticScroll = useRef(false);
  const isPinnedRef = useRef(true);

  // 用户主动滚轮、触摸、键盘上下翻页时记录时间戳
  const markUserInput = useCallback(() => {
    lastUserInputAt.current = performance.now();
  }, []);

  const updateScrollState = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;

    const { scrollTop, scrollHeight, clientHeight } = el;
    const { isPinned: pinned, distanceFromBottom } = computePinState(
      scrollHeight,
      scrollTop,
      clientHeight,
      pinTolerance
    );

    isPinnedRef.current = pinned;
    setIsPinned(pinned);
    setShowJumpControl(shouldShowJumpControl(distanceFromBottom, jumpThreshold));

    const { fadeTop: top, fadeBottom: bottom } = computeEdgeFades(
      scrollTop,
      distanceFromBottom,
      fadeSize
    );
    setFadeTop(top);
    setFadeBottom(bottom);
  }, [pinTolerance, jumpThreshold, fadeSize]);

  const handleScroll = useCallback(() => {
    if (programmaticScroll.current) {
      programmaticScroll.current = false;
      const el = containerRef.current;
      if (el) {
        const dist = Math.max(0, el.scrollHeight - el.scrollTop - el.clientHeight);
        const { fadeTop: top, fadeBottom: bottom } = computeEdgeFades(el.scrollTop, dist, fadeSize);
        setFadeTop(top);
        setFadeBottom(bottom);
      }
      return;
    }
    updateScrollState();
  }, [updateScrollState, fadeSize]);

  const scrollToBottom = useCallback((smooth = false) => {
    const el = containerRef.current;
    if (!el) return;

    programmaticScroll.current = true;
    el.scrollTo({
      top: el.scrollHeight,
      behavior: smooth ? "smooth" : "auto",
    });

    isPinnedRef.current = true;
    setIsPinned(true);
    setShowJumpControl(false);
    setFadeBottom(0);
  }, []);

  // 依赖项变化（Token 流式追加、消息增加、思考状态切换）时执行图钉重锚定
  useEffect(() => {
    // 150ms 冷却保护窗口：用户刚滚轮/滑动时，绝不抢夺视口
    if (isUserScrollCooldownActive(lastUserInputAt.current, performance.now(), userCooldownMs)) {
      return;
    }

    if (isPinnedRef.current) {
      scrollToBottom(false);
    }
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps

  // ResizeObserver 监听容器尺寸变化（如分栏拖动改变宽度导致文本折行重新计算高度）
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const ro = new ResizeObserver(() => {
      updateScrollState();
      if (isPinnedRef.current) {
        scrollToBottom(false);
      }
    });

    ro.observe(el);
    return () => ro.disconnect();
  }, [updateScrollState, scrollToBottom]);

  // 构建精密 7-Stop 非线性幂律渐变遮罩样式
  const maskStyle: React.CSSProperties = {
    WebkitMaskImage: `linear-gradient(to bottom,
      transparent,
      rgba(0, 0, 0, 0.05) calc(${fadeTop}px * 0.15),
      rgba(0, 0, 0, 0.15) calc(${fadeTop}px * 0.30),
      rgba(0, 0, 0, 0.30) calc(${fadeTop}px * 0.45),
      rgba(0, 0, 0, 0.50) calc(${fadeTop}px * 0.60),
      rgba(0, 0, 0, 0.70) calc(${fadeTop}px * 0.75),
      rgba(0, 0, 0, 0.85) calc(${fadeTop}px * 0.87),
      #000 ${fadeTop}px,
      #000 calc(100% - ${fadeBottom}px),
      rgba(0, 0, 0, 0.85) calc(100% - ${fadeBottom}px * 0.87),
      rgba(0, 0, 0, 0.70) calc(100% - ${fadeBottom}px * 0.75),
      rgba(0, 0, 0, 0.50) calc(100% - ${fadeBottom}px * 0.60),
      rgba(0, 0, 0, 0.30) calc(100% - ${fadeBottom}px * 0.45),
      rgba(0, 0, 0, 0.15) calc(100% - ${fadeBottom}px * 0.30),
      rgba(0, 0, 0, 0.05) calc(100% - ${fadeBottom}px * 0.15),
      transparent
    )`,
    maskImage: `linear-gradient(to bottom,
      transparent,
      rgba(0, 0, 0, 0.05) calc(${fadeTop}px * 0.15),
      rgba(0, 0, 0, 0.15) calc(${fadeTop}px * 0.30),
      rgba(0, 0, 0, 0.30) calc(${fadeTop}px * 0.45),
      rgba(0, 0, 0, 0.50) calc(${fadeTop}px * 0.60),
      rgba(0, 0, 0, 0.70) calc(${fadeTop}px * 0.75),
      rgba(0, 0, 0, 0.85) calc(${fadeTop}px * 0.87),
      #000 ${fadeTop}px,
      #000 calc(100% - ${fadeBottom}px),
      rgba(0, 0, 0, 0.85) calc(100% - ${fadeBottom}px * 0.87),
      rgba(0, 0, 0, 0.70) calc(100% - ${fadeBottom}px * 0.75),
      rgba(0, 0, 0, 0.50) calc(100% - ${fadeBottom}px * 0.60),
      rgba(0, 0, 0, 0.30) calc(100% - ${fadeBottom}px * 0.45),
      rgba(0, 0, 0, 0.15) calc(100% - ${fadeBottom}px * 0.30),
      rgba(0, 0, 0, 0.05) calc(100% - ${fadeBottom}px * 0.15),
      transparent
    )`,
    transition: "mask-image 0.2s ease, -webkit-mask-image 0.2s ease",
  };

  return {
    containerRef,
    isPinned,
    showJumpControl,
    markUserInput,
    handleScroll,
    scrollToBottom,
    maskStyle,
    fadeTop,
    fadeBottom,
  };
}
