import test from "node:test";
import assert from "node:assert/strict";
import { draftTask, taskDraft, gsStatus } from "./explorations.ts";
import {
  parseExperimentTask,
  experimentTaskDraft,
  planForTasks,
  comparisonFactors,
  type TaskDraft,
} from "./experiment-plans.ts";

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

test("shared editor keeps domain parameters and comparison factors", () => {
  const a = parseExperimentTask("integration", {
    method: "simpson",
    expression: "x^4",
    left: "0",
    right: "1",
    intervals: "4",
    limit: "3",
    tolerance: "0.000001",
  });
  assert.equal(a.domain, "integration");
  assert.deepEqual(
    parseExperimentTask("integration", experimentTaskDraft(a)),
    a,
  );
  const b = { ...a, intervals: 8 } as typeof a;
  assert.deepEqual(comparisonFactors([a, b]).varying_factors, ["intervals"]);
  const plan = planForTasks("积分误差估计能当严格界吗？", [a, b]);
  assert.ok(plan.tool_limitations[0].includes("不是严格误差上界"));
  const invalid: TaskDraft[] = [
    { left: "1" },
    { intervals: "3" },
    { method: "random" },
    { tolerance: "NaN" },
    { expression: "" },
  ];
  for (const patch of invalid)
    assert.throws(() =>
      parseExperimentTask("integration", {
        ...experimentTaskDraft(a),
        ...patch,
      }),
    );
  const n = parseExperimentTask("root_finding", {
    function: "x^3-2*x+2",
    initial_value: "0",
    limit: "12",
    tolerance: "0.000001",
  });
  assert.deepEqual(
    parseExperimentTask("root_finding", experimentTaskDraft(n)),
    n,
  );
  assert.throws(() =>
    parseExperimentTask("root_finding", {
      ...experimentTaskDraft(n),
      initial_value: "",
    }),
  );
});
