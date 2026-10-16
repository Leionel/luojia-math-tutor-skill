import test from "node:test";
import assert from "node:assert/strict";
import { draftTask, taskDraft, gsStatus } from "./explorations.ts";

test("exploration editor reuses bounded numerical parsing and preserves parameters", () => {
  const task = {
    domain: "linear_system" as const,
    method: "gauss_seidel" as const,
    matrix: [
      [1, 2],
      [0.1, 1],
    ],
    rhs: [1, 1],
    initial: [0, 0],
    tolerance: 1e-6,
    limit: 80,
  };
  assert.deepEqual(draftTask(taskDraft(task)), task);
  for (const patch of [
    { matrix: "1 2\n3" },
    { matrix: "0 2\n1 1" },
    { rhs: "NaN 1" },
    { initial: "0" },
    { tolerance: "Infinity" },
    { limit: "1000000" },
  ])
    assert.throws(() => draftTask({ ...taskDraft(task), ...patch }));
  assert.equal(gsStatus("residual_met"), "残差达到阈值");
  assert.equal(gsStatus("unfamiliar"), "状态待核对");
});
