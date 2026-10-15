import assert from "node:assert/strict";
import test from "node:test";
import {
  clampPaneWidth,
  defaultPaneWidth,
  shouldInterceptCompositionEnter,
  PANE_CONSTRAINTS,
  computePinState,
  shouldShowJumpControl,
  isUserScrollCooldownActive,
  computeEdgeFades,
  computeThinkingAccordionState,
  formatThoughtAsQuote,
} from "./interaction-physics.ts";

test("interaction physics: clamps split pane widths within safe hardware boundaries", () => {
  // Sidebar (200 - 600, default 260)
  assert.equal(clampPaneWidth("sidebar", 150), 200);
  assert.equal(clampPaneWidth("sidebar", 400), 400);
  assert.equal(clampPaneWidth("sidebar", 800), 600);
  assert.equal(clampPaneWidth("sidebar", NaN), 260);
  assert.equal(clampPaneWidth("sidebar", Infinity), 260);

  // Learning Panel (200 - 600, default 320)
  assert.equal(clampPaneWidth("learning", 100), 200);
  assert.equal(clampPaneWidth("learning", 350), 350);
  assert.equal(clampPaneWidth("learning", 750), 600);
  assert.equal(clampPaneWidth("learning", -Infinity), 320);

  // Workspace Split Canvas (380 - 1000, default 580)
  assert.equal(clampPaneWidth("workspace", 200), 380);
  assert.equal(clampPaneWidth("workspace", 650), 650);
  assert.equal(clampPaneWidth("workspace", 1200), 1000);
  assert.equal(clampPaneWidth("workspace", NaN), 580);
});

test("interaction physics: double click baseline returns golden pane defaults", () => {
  assert.equal(defaultPaneWidth("sidebar"), 260);
  assert.equal(defaultPaneWidth("learning"), 320);
  assert.equal(defaultPaneWidth("workspace"), 580);
  assert.equal(defaultPaneWidth("workspace"), PANE_CONSTRAINTS.workspace.default);
});

test("interaction physics: IME guard prevents Chinese pinyin enter misfire", () => {
  const baseTime = 1000;

  // 1. Normal standalone Enter without IME -> Not intercepted (Allowed to send)
  assert.equal(
    shouldInterceptCompositionEnter({
      key: "Enter",
      shiftKey: false,
      isComposing: false,
      lastCompositionEndedAt: 0,
      now: baseTime,
    }),
    false,
    "Standard Enter must proceed to submit"
  );

  // 2. Shift + Enter -> Intercepted (Newline, no submit)
  assert.equal(
    shouldInterceptCompositionEnter({
      key: "Enter",
      shiftKey: true,
      isComposing: false,
      lastCompositionEndedAt: 0,
      now: baseTime,
    }),
    true,
    "Shift+Enter must be intercepted"
  );

  // 3. Actively composing (User typing Chinese pinyin letters) -> Intercepted
  assert.equal(
    shouldInterceptCompositionEnter({
      key: "Enter",
      shiftKey: false,
      isComposing: true,
      lastCompositionEndedAt: 0,
      now: baseTime,
    }),
    true,
    "Active IME composition must be intercepted"
  );

  // 4. Composition ended just 20ms ago (OS-level key event race condition) -> Intercepted!
  assert.equal(
    shouldInterceptCompositionEnter({
      key: "Enter",
      shiftKey: false,
      isComposing: false,
      lastCompositionEndedAt: baseTime - 20,
      now: baseTime,
      cooldownMs: 60,
    }),
    true,
    "Enter within 20ms of compositionend must be intercepted by cooldown window"
  );

  // 5. Composition ended 80ms ago (Valid prompt submission after confirmation) -> Allowed
  assert.equal(
    shouldInterceptCompositionEnter({
      key: "Enter",
      shiftKey: false,
      isComposing: false,
      lastCompositionEndedAt: baseTime - 80,
      now: baseTime,
      cooldownMs: 60,
    }),
    false,
    "Enter after cooldown window expires must proceed to submit"
  );

  // 6. IME KeyCode 229 -> Intercepted
  assert.equal(
    shouldInterceptCompositionEnter({
      key: "Enter",
      shiftKey: false,
      isComposing: false,
      lastCompositionEndedAt: 0,
      now: baseTime,
      keyCode: 229,
    }),
    true,
    "KeyCode 229 must be intercepted"
  );

  // 7. Mobile coarse pointer -> Intercepted
  assert.equal(
    shouldInterceptCompositionEnter({
      key: "Enter",
      shiftKey: false,
      isComposing: false,
      lastCompositionEndedAt: 0,
      now: baseTime,
      isCoarsePointer: true,
    }),
    true,
    "Coarse touch pointer must be intercepted"
  );

  // 8. Non-enter keys
  assert.equal(
    shouldInterceptCompositionEnter({
      key: "a",
      isComposing: false,
      lastCompositionEndedAt: 0,
      now: baseTime,
    }),
    true,
    "Non-Enter keys must return true (not submit)"
  );
});

test("interaction physics: scroll pinning calculations and tolerance", () => {
  // 1. Bottom edge within 40px tolerance -> Pinned
  const pin1 = computePinState(1000, 570, 400, 40); // distanceFromBottom = 30px
  assert.equal(pin1.distanceFromBottom, 30);
  assert.equal(pin1.isPinned, true);

  // 2. Exact boundary at 40px -> Pinned
  const pin2 = computePinState(1000, 560, 400, 40); // distanceFromBottom = 40px
  assert.equal(pin2.isPinned, true);

  // 3. Beyond 40px -> Not pinned
  const pin3 = computePinState(1000, 550, 400, 40); // distanceFromBottom = 50px
  assert.equal(pin3.isPinned, false);

  // 4. Overscrolled past bottom -> Distance bounded at 0, pinned
  const pin4 = computePinState(1000, 610, 400, 40);
  assert.equal(pin4.distanceFromBottom, 0);
  assert.equal(pin4.isPinned, true);
});

test("interaction physics: jump control visibility threshold", () => {
  assert.equal(shouldShowJumpControl(50, 120), false);
  assert.equal(shouldShowJumpControl(120, 120), false);
  assert.equal(shouldShowJumpControl(121, 120), true);
  assert.equal(shouldShowJumpControl(300, 120), true);
});

test("interaction physics: user scroll cooldown protection window", () => {
  const baseTime = 5000;
  // User scrolled 100ms ago -> within 150ms window -> cooldown ACTIVE (no autoscroll)
  assert.equal(isUserScrollCooldownActive(baseTime - 100, baseTime, 150), true);
  // User scrolled 150ms ago -> active
  assert.equal(isUserScrollCooldownActive(baseTime - 150, baseTime, 150), true);
  // User scrolled 160ms ago -> cooldown EXPIRED (safe to autoscroll)
  assert.equal(isUserScrollCooldownActive(baseTime - 160, baseTime, 150), false);
});

test("interaction physics: 7-stop edge fade calculation with top/bottom boundary detection", () => {
  // At top: fadeTop must be 0 (no white fringe on header)
  const atTop = computeEdgeFades(0, 500, 24);
  assert.equal(atTop.fadeTop, 0);
  assert.equal(atTop.fadeBottom, 24);

  // Scrolled into content: fadeTop is 24px
  const inMiddle = computeEdgeFades(50, 200, 24);
  assert.equal(inMiddle.fadeTop, 24);
  assert.equal(inMiddle.fadeBottom, 24);

  // At bottom: fadeBottom must be 0
  const atBottom = computeEdgeFades(800, 1, 24);
  assert.equal(atBottom.fadeTop, 24);
  assert.equal(atBottom.fadeBottom, 0);
});

test("interaction physics: thinking accordion state machine locking during live generation", () => {
  // 1. Live thinking active -> MUST be open, CANNOT toggle (Locked to avoid layout jitter)
  const liveState = computeThinkingAccordionState({
    isThinkingLive: true,
    userExpanded: false, // Even if user preferred collapsed, live generation overrides
  });
  assert.equal(liveState.isOpen, true, "Must be forced open during active streaming thought");
  assert.equal(liveState.canToggle, false, "Must revoke collapse capability during streaming");

  // 2. Finished thinking -> Yields control back to user preference
  const finishedCollapsed = computeThinkingAccordionState({
    isThinkingLive: false,
    userExpanded: false,
  });
  assert.equal(finishedCollapsed.isOpen, false);
  assert.equal(finishedCollapsed.canToggle, true);

  const finishedExpanded = computeThinkingAccordionState({
    isThinkingLive: false,
    userExpanded: true,
  });
  assert.equal(finishedExpanded.isOpen, true);
  assert.equal(finishedExpanded.canToggle, true);
});

test("interaction physics: thought formatting as quote for mathematical discussion", () => {
  assert.equal(formatThoughtAsQuote(""), "");
  assert.equal(
    formatThoughtAsQuote("推演残差条件\n假设导数非零"),
    "> 推演残差条件\n> 假设导数非零"
  );
});


