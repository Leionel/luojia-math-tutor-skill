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

test("plot segments preserve poles without splitting continuous steep roots", () => {
  for (const expression of ["1/x", "1/(x-0.013)", "tan(x)"]) {
    const plot = buildPlotPoints(expression, -2, 2, 100)!;
    assert.ok(plot.segments.length > 1, expression);
    for (const segment of plot.segments) {
      if (expression.startsWith("1/")) {
        const pole = expression === "1/x" ? 0 : 0.013;
        assert.ok(!segment.some(p => p.x < pole) || !segment.some(p => p.x > pole));
      }
    }
  }
  assert.equal(buildPlotPoints("1000*x", -2, 2)!.segments.length, 1);
  assert.equal(buildPlotPoints("sin(x)", -2, 2)!.segments.length, 1);
  assert.equal(buildPlotPoints("x", -2, 2, Infinity), null);
});

test("extreme ranges cannot produce nonfinite plot coordinates", () => {
  assert.equal(buildPlotPoints("x", -1e308, 1e308), null);
  assert.equal(buildPlotPoints("exp(709.7)*x", -1, 1), null);
});
