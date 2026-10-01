import assert from "node:assert/strict";
import test from "node:test";
import { layoutCourseNodes } from "./course-graph-layout.ts";

test("force graph remains finite and separated, including orphans", () => {
  const nodes = Array.from({ length: 27 }, (_, i) => ({ id: String(i) }));
  const result = layoutCourseNodes(nodes, []);
  assert.equal(new Set(result.map((n) => `${n.position.x}:${n.position.y}`)).size, 27);
  assert.ok(result.every((n) => Number.isFinite(n.position.x) && Number.isFinite(n.position.y)));
  for (let i = 0; i < result.length; i++) for (let j = i + 1; j < result.length; j++) {
    assert.ok(Math.hypot(result[i].position.x - result[j].position.x, result[i].position.y - result[j].position.y) > 48);
  }
});

test("same graph layout is stable despite API node order", () => {
  const nodes = [{ id: "condition" }, { id: "algorithm" }, { id: "counterexample" }];
  const edges = [{ source: "condition", target: "algorithm" }, { source: "counterexample", target: "algorithm" }];
  const result = layoutCourseNodes(nodes, edges);
  assert.deepEqual(result, layoutCourseNodes([...nodes].reverse(), edges).reverse());
});

test("cycles and missing endpoints cannot grow layout indefinitely", () => {
  const nodes = [{ id: "a" }, { id: "b" }];
  const edges = [{ source: "a", target: "b" }, { source: "b", target: "a" }, { source: "missing", target: "a" }];
  assert.deepEqual(layoutCourseNodes(nodes, edges), layoutCourseNodes(nodes, edges.slice(0, 2)));
  assert.ok(layoutCourseNodes(nodes, edges).every((n) => Math.abs(n.position.x) < 1000 && Math.abs(n.position.y) < 1000));
  assert.deepEqual(layoutCourseNodes([], edges), []);
});
