import { z } from "zod";
import type { LearningContextRef } from "./learning-context";
import type { TutorMeta } from "./api";

export const UI_CATALOG_VERSION = "learning-ui-v1";
export const uiComponentNames = [
  "SourceExcerpt",
  "ConditionChecklist",
  "PredictionForm",
  "ParameterCompare",
  "RunTraceChart",
] as const;
const selectionSchema = z
  .object({
    component: z.enum(uiComponentNames),
    evidence_ref: z.string().min(1).max(160),
  })
  .strict();
const sourceSchema = z
  .object({
    id: z.string(),
    kind: z.enum([
      "student_claim",
      "scoped_check",
      "reference",
      "model_opinion",
      "personal_judgment",
      "unavailable",
    ]),
    data: z.unknown(),
  })
  .strict();
const status = z.enum([
  "supported",
  "partially_supported",
  "contradicted",
  "unknown",
]);
const decisionSchema = z
  .object({
    version: z.literal("teaching-decision-v1"),
    status: z.literal("accepted"),
    origin: z.literal("model_opinion"),
    claim_ref: z.literal("claim:current"),
    evidence_refs: z.array(z.string()).max(12),
    known_conditions: z.array(z.string().max(500)).max(8),
    missing_conditions: z.array(z.string().max(500)).max(8),
    claim_status: status,
    action: z.enum([
      "confirm_local",
      "correct_claim",
      "ask_missing_condition",
      "offer_experiment",
      "explain",
      "offer_probe",
    ]),
    disclosure: z.enum(["full", "scaffolded"]),
    reason: z.string().max(360),
    source_hash: z.string().regex(/^[a-f0-9]{64}$/),
    context_ref: z.unknown(),
    sources: z.array(sourceSchema),
    assessments: z
      .array(
        z.object({
          claim: z.string().max(500),
          status,
          evidence_refs: z.array(z.string()),
        }),
      )
      .max(6),
    ui_status: z.literal("fallback").optional(),
    experiment_proposal: z.object({
      question_to_test: z.string().min(1).max(300),
      changed_parameter: z.literal("initial_value"),
      suggested_value: z.number().finite().min(-1e25).max(1e25),
      candidate_values: z.array(z.number().finite().min(-1e25).max(1e25)).max(2).default([]),
      observable: z.string().min(1).max(200),
    }).strict().nullable().optional(),
  })
  .strict().refine(value => value.action === "offer_experiment" ? !!value.experiment_proposal : !value.experiment_proposal,
    "Experiment proposal must match the teaching action");
const artifactSchema = z
  .object({
    catalog_version: z.literal(UI_CATALOG_VERSION),
    source_hash: z.string().regex(/^[a-f0-9]{64}$/),
    status: z.literal("validated"),
    artifact_id: z.string().regex(/^ui-[a-f0-9]{24}$/),
    response: z.string().max(5000),
    markdown_fallback: z.string(),
    context_ref: z.unknown(),
    selections: z.array(selectionSchema).min(1).max(4),
  })
  .strict();
export type TeachingDecision = z.infer<typeof decisionSchema>;
export type IntelligentArtifact = z.infer<typeof artifactSchema>;
export type WorkspaceIntent = { ref?: LearningContextRef; prediction?: string };

/** Present source data without exposing storage field names as product copy. */
export function evidenceText(data: unknown): string {
  if (typeof data === "string") return data;
  if (Array.isArray(data))
    return data
      .map((value) => (typeof value === "string" ? value : evidenceText(value)))
      .filter(Boolean)
      .join("\n");
  if (!data || typeof data !== "object") return "";
  const value = data as Record<string, unknown>;
  if (typeof value.function === "string")
    return [
      `函数：${value.function}`,
      typeof value.method === "string" ? `方法：${value.method}` : "",
      typeof value.initial_value === "number"
        ? `初值：${value.initial_value}`
        : "",
      typeof value.tolerance === "number" ? `阈值：${value.tolerance}` : "",
    ]
      .filter(Boolean)
      .join("\n");
  if (typeof value.k === "number" && typeof value.x === "number")
    return `第 ${value.k} 步：近似值 ${value.x}${typeof value.fx === "number" ? `，函数值 ${value.fx}` : ""}`;
  return [
    value.title,
    value.concept,
    value.excerpt,
    value.quote,
    value.summary,
    value.message,
    value.reason,
    value.conclusion,
    value.derivative,
    Array.isArray(value.steps) ? value.steps.join("\n") : null,
    Array.isArray(value.assumptions)
      ? `适用前提：${value.assumptions.join("；")}`
      : null,
    value.data ? evidenceText(value.data) : null,
    typeof value.provenance === "string" ? `来源：${value.provenance}` : null,
    value.scope === "reference_provenance_only" ? "资料摘录用于核对前提；检索命中不代表本题已满足条件。" : null,
  ]
    .filter(
      (part): part is string => typeof part === "string" && part.length > 0,
    )
    .join("\n\n");
}

export function parseTeachingDecision(value: unknown): TeachingDecision | null {
  const parsed = decisionSchema.safeParse(value);
  return parsed.success ? parsed.data : null;
}
export function compileUI(selections: IntelligentArtifact["selections"]) {
  return (
    `root = LearningUI([${selections.map((_, i) => `c${i}`).join(", ")}])\n` +
    selections
      .map(
        (item, i) =>
          `c${i} = ${item.component}(${JSON.stringify(item.evidence_ref)})`,
      )
      .join("\n")
  );
}
function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object")
    return `{${Object.entries(value)
      .filter(([, v]) => v !== undefined)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${JSON.stringify(k)}:${canonical(v)}`)
      .join(",")}}`;
  return JSON.stringify(value ?? null);
}
export function sameLearningReference(a: unknown, b: unknown) {
  return canonical(a) === canonical(b);
}

/** The permissive OpenUI parser is never the authority for data or actions. */
export function resolveIntelligentUI(
  meta: TutorMeta | null | undefined,
  messageId?: string,
) {
  const decision = parseTeachingDecision(meta?.teaching_decision),
    parsed = artifactSchema.safeParse(meta?.intelligent_ui);
  if (
    !decision ||
    !parsed.success ||
    !messageId ||
    meta?.error ||
    meta?.agent_run?.status !== "succeeded" ||
    meta.agent_run.message_id !== messageId ||
    meta.answer_guard?.status !== "passed"
  )
    return null;
  const artifact = parsed.data;
  if (
    artifact.source_hash !== decision.source_hash ||
    !sameLearningReference(artifact.context_ref, decision.context_ref) ||
    !sameLearningReference(artifact.context_ref, meta.learning_context?.ref) ||
    artifact.response !== compileUI(artifact.selections)
  )
    return null;
  const ids = new Set(decision.sources.map((source) => source.id));
  if (artifact.selections.some((item) => !ids.has(item.evidence_ref)))
    return null;
  return { decision, artifact };
}
