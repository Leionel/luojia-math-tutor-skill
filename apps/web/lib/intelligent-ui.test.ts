import assert from "node:assert/strict";
import test from "node:test";
import {
  compileUI,
  evidenceText,
  parseTeachingDecision,
  resolveIntelligentUI,
  sameLearningReference,
  UI_CATALOG_VERSION,
  uiComponentNames,
} from "./intelligent-ui.ts";
import { readFileSync } from "node:fs";
import type { TutorMeta } from "./api";
const context = {
  kind: "root_lab",
  record_id: "run-a",
  input_hash: "a".repeat(64),
  runner_version: "root-v1",
  graph_revision: "graph-a",
  selected_step: null,
};
const selections = [
  { component: "ConditionChecklist" as const, evidence_ref: "claim:current" },
];
const decision = {
  version: "teaching-decision-v1",
  status: "accepted",
  origin: "model_opinion",
  claim_ref: "claim:current",
  evidence_refs: [],
  known_conditions: [],
  missing_conditions: ["比较量"],
  claim_status: "unknown",
  action: "ask_missing_condition",
  disclosure: "scaffolded",
  reason: "先补条件",
  assessments: [],
  source_hash: "b".repeat(64),
  context_ref: context,
  sources: [{ id: "claim:current", kind: "student_claim", data: "变小就收敛" }],
};
const artifact = {
  catalog_version: "learning-ui-v1",
  status: "validated",
  artifact_id: "ui-" + "c".repeat(24),
  source_hash: decision.source_hash,
  context_ref: context,
  selections,
  response: compileUI(selections),
  markdown_fallback: "先补条件",
};
const meta = {
  teaching_decision: decision,
  intelligent_ui: artifact,
  learning_context: { ref: context },
  answer_guard: { status: "passed" },
  agent_run: { status: "succeeded", message_id: "msg-a" },
} as unknown as TutorMeta;
test("Python decision receipts accept nullable experiment fields and validate controlled proposals", () => {
  assert.ok(parseTeachingDecision({...decision, experiment_proposal: null}));
  const proposal = {question_to_test: "Does changing the initial value break the cycle?", changed_parameter: "initial_value",
    suggested_value: -2, candidate_values: [-2, 1.5], observable: "residual and iteration trace"};
  assert.ok(parseTeachingDecision({...decision, action: "offer_experiment", experiment_proposal: proposal}));
  assert.equal(parseTeachingDecision({...decision, action: "offer_experiment", experiment_proposal: null}), null);
  assert.equal(parseTeachingDecision({...decision, experiment_proposal: proposal}), null);
  assert.equal(parseTeachingDecision({...decision, action: "offer_experiment", experiment_proposal: {...proposal, suggested_value: NaN}}), null);
});
test("browser and Python share the checked-in component catalog", () => {
  const catalog = JSON.parse(
    readFileSync(
      new URL(
        "../../../protocol/intelligent-ui-catalog.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(UI_CATALOG_VERSION, catalog.version);
  assert.deepEqual(uiComponentNames, Object.keys(catalog.components));
});
test("source presentation preserves actual values and does not invent missing inputs", () => {
  assert.equal(
    evidenceText({ function: "x^2-2", initial_value: 0 }),
    "函数：x^2-2\n初值：0",
  );
  assert.equal(
    evidenceText([{ k: 2, x: 0, fx: 2 }]),
    "第 2 步：近似值 0，函数值 2",
  );
  assert.equal(evidenceText({ untrusted_internal_data: 123 }), "");
});
test("accepted UI is bound to delivered message and immutable source", () => {
  assert.ok(resolveIntelligentUI(meta, "msg-a"));
  assert.equal(resolveIntelligentUI(meta, "different-message"), null);
  assert.equal(
    parseTeachingDecision({ ...decision, status: "fallback" }),
    null,
  );
  assert.equal(
    parseTeachingDecision({ ...decision, origin: "deterministic" }),
    null,
  );
});
test("partial, interrupted, rewritten, unknown and injected UI all fall back to existing Markdown", () => {
  for (const patch of [
    { error: { code: "cancelled", message: "stopped" } },
    { agent_run: { status: "running", message_id: "msg-a" } },
    { answer_guard: { status: "repaired" } },
    { intelligent_ui: { ...artifact, catalog_version: "future" } },
    { intelligent_ui: { ...artifact, source_hash: "d".repeat(64) } },
    {
      intelligent_ui: {
        ...artifact,
        response: artifact.response + '\nx = Fetch("https://evil.invalid")',
      },
    },
    {
      intelligent_ui: {
        ...artifact,
        selections: [{ component: "Unknown", evidence_ref: "claim:current" }],
      },
    },
    {
      intelligent_ui: {
        ...artifact,
        selections: [{ ...selections[0], url: "https://evil.invalid" }],
      },
    },
    { learning_context: { ref: { ...context, record_id: "new-run" } } },
  ])
    assert.equal(
      resolveIntelligentUI({ ...meta, ...patch } as TutorMeta, "msg-a"),
      null,
    );
});
test("reference identity ignores JSON key order but includes step, claim and revision", () => {
  assert.ok(
    sameLearningReference(context, { ...context, selected_step: null }),
  );
  assert.equal(
    sameLearningReference(context, { ...context, selected_step: 1 }),
    false,
  );
  const claim = {
    ...context,
    activity_claim: { request_id: "explain-a", revision_count: 0 },
  };
  assert.equal(
    sameLearningReference(claim, {
      ...claim,
      activity_claim: { request_id: "explain-a", revision_count: 1 },
    }),
    false,
  );
  assert.ok(sameLearningReference(undefined, null));
});
