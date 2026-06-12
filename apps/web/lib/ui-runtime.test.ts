import assert from "node:assert/strict";
import test from "node:test";

import {
  advanceMasteryTrend,
  nextVisibleSessionCount,
  parseMasteryTrendSnapshot,
  projectRadarValues,
} from "./ui-runtime.ts";

test("unassessed radar values project to the center", () => {
  assert.deepEqual(
    projectRadarValues([
      { value: 0.74, assessed: true },
      { value: 0.15, assessed: false },
      { value: 1.4, assessed: true },
      { value: -0.2, assessed: true },
    ]),
    [0.74, 0, 1, 0],
  );
});

test("session batches reveal thirty rows at a time", () => {
  assert.equal(nextVisibleSessionCount(30, 168), 60);
  assert.equal(nextVisibleSessionCount(150, 168), 168);
  assert.equal(nextVisibleSessionCount(30, 12), 12);
});

test("trend snapshot survives reload without comparing current to itself", () => {
  const first = advanceMasteryTrend(null, "demo-user|69", 74);
  assert.equal(first.trend, null);
  assert.equal(first.previousAverage, null);

  const changed = advanceMasteryTrend(first.snapshot, "demo-user|70", 78);
  assert.equal(changed.trend, "up");
  assert.equal(changed.previousAverage, 74);

  const reload = advanceMasteryTrend(changed.snapshot, "demo-user|70", 78);
  assert.equal(reload.trend, "up");
  assert.equal(reload.previousAverage, 74);
});

test("small mastery changes are treated as flat", () => {
  const first = advanceMasteryTrend(null, "demo-user|70", 74);
  const changed = advanceMasteryTrend(first.snapshot, "demo-user|71", 75);

  assert.equal(changed.trend, "flat");
  assert.equal(changed.previousAverage, 74);
});

test("invalid stored trend snapshots are ignored", () => {
  assert.equal(parseMasteryTrendSnapshot(null), null);
  assert.equal(parseMasteryTrendSnapshot("not-json"), null);
  assert.equal(
    parseMasteryTrendSnapshot(
      JSON.stringify({
        currentFingerprint: "demo-user|70",
        currentAverage: "74",
      }),
    ),
    null,
  );
});
