import assert from "node:assert/strict";
import test from "node:test";
import {numericMatrix, numericVector, comparableNumerical, discussionDraft, type NumericalRun} from "./numerical-lab.ts";

test("numeric input rejects code, Infinity, empty cells and malformed matrices", () => {
  assert.deepEqual(numericMatrix("4 1\n2,3"), [[4, 1], [2, 3]]);
  assert.deepEqual(numericVector("-1 .5 2e-3"), [-1, .5, .002]);
  for (const value of ["", "Infinity", "NaN", "1+2", "0x10", "1e999"]) assert.throws(() => numericVector(value));
  assert.throws(() => numericMatrix("1 2\n3"));
});

test("comparison requires same problem and tolerance; discussion labels help scope", () => {
  const run = {id: "r", source_hash: "s", prediction: "收敛", stop_detail: "残差达标", evidence_scope: "floating_point_residual", rows: [], task: {domain: "linear_system", method: "jacobi", matrix: [[4, 1], [2, 3]], rhs: [1, 2], initial: [0, 0], tolerance: 1e-6, limit: 50}} as unknown as NumericalRun;
  assert.ok(comparableNumerical(run, {...run, task: {...run.task, method: "gauss_seidel"}} as NumericalRun));
  assert.ok(!comparableNumerical(run, {...run, task: {...run.task, tolerance: 1e-3}}));
  assert.match(discussionDraft(run), /系统参考实验/);
  assert.match(discussionDraft(run), /不是独立测验/);
  const integral = {...run, task: {domain: "integration", expression: "sin(16*pi*x)^2", left: 0, right: 1, method: "simpson", intervals: 4, tolerance: 1e-6, limit: 50}} as NumericalRun;
  assert.ok(comparableNumerical(integral, {...integral, task: {...integral.task, intervals: 6}} as NumericalRun));
});
