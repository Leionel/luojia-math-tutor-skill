import assert from "node:assert/strict";
import test from "node:test";

import { evaluateMathExpression, buildPlotPoints } from "./math-expression.ts";

test("evaluates allowed math expressions", () => {
  assert.equal(evaluateMathExpression("sin(pi / 2) + x^2", 3), 10);
});

test("rejects expressions with browser globals or constructors", () => {
  assert.throws(() => evaluateMathExpression("window.alert(1)", 1), /Unsupported/);
  assert.throws(() => evaluateMathExpression("x.constructor.constructor('alert(1)')()", 1), /Unsupported/);
});

test("builds finite plot points and ignores singular values", () => {
  const points = buildPlotPoints("1 / x", -1, 1, 8);

  assert.ok(points);
  assert.ok(points.pts.length > 0);
  assert.ok(points.pts.every((point) => Number.isFinite(point.y)));
});
