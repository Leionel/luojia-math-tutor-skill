import type {LearningContextRef,RootContextRef} from "./learning-context";
import type {LabRun} from "./learning-api";

export type PreviewParameters = {initial_value: number; tolerance: number; max_iterations: number};
export type RootProposal = {
  version: "tutor-artifact-v1"; kind: "root_parameter_proposal"; action: "preview_root_lab";
  artifact_id: string; run_id: string; origin: "server"; context: RootContextRef;
  parameters: PreviewParameters; created_at: string; expires_at: string;
  evidence_kind: "reference_help"; independent_success: false; preview_budget: number;
};
export type RootPreview = Omit<LabRun, "prediction"> & {context: RootContextRef; max_iterations: number};
export type RootActionState = {state: "proposed" | "previewed" | "saved" | "expired";
  preview_ids: string[]; preview_budget: number; used_help: number; preview: RootPreview | null; saved_run: LabRun | null};

export function sameContext(a: LearningContextRef | undefined, b: LearningContextRef | undefined) {
  return !!a && !!b && a.kind === "root_lab" && b.kind === "root_lab" && a.record_id === b.record_id && a.input_hash === b.input_hash
    && a.runner_version === b.runner_version && a.graph_revision === b.graph_revision && a.selected_step === b.selected_step;
}
export function parseRootProposals(value: unknown): RootProposal[] {
  if (!Array.isArray(value)) return [];
  return value.slice(0, 3).filter((v): v is RootProposal => {
    if (!v || typeof v !== "object") return false;
    const c = v.context, p = v.parameters;
    return v.version === "tutor-artifact-v1" && v.kind === "root_parameter_proposal" && v.action === "preview_root_lab"
      && v.origin === "server" && v.evidence_kind === "reference_help" && v.independent_success === false
      && typeof v.artifact_id === "string" && /^[A-Za-z0-9_-]{1,80}$/.test(v.artifact_id)
      && typeof v.run_id === "string" && /^[A-Za-z0-9_-]{1,80}$/.test(v.run_id)
      && c?.kind === "root_lab" && typeof c.record_id === "string" && /^[A-Za-z0-9_-]{1,80}$/.test(c.record_id)
      && typeof c.input_hash === "string" && /^[a-f0-9]{64}$/.test(c.input_hash)
      && typeof c.runner_version === "string" && typeof c.graph_revision === "string"
      && (c.selected_step === null || (Number.isInteger(c.selected_step) && c.selected_step >= 0 && c.selected_step <= 100))
      && Number.isFinite(p?.initial_value) && Math.abs(p.initial_value) <= 1e25
      && Number.isFinite(p?.tolerance) && p.tolerance > 0 && p.tolerance <= 1
      && Number.isInteger(p?.max_iterations) && p.max_iterations >= 1 && p.max_iterations <= 100
      && Number.isFinite(Date.parse(v.created_at)) && Number.isFinite(Date.parse(v.expires_at)) && v.preview_budget === 3;
  });
}
export function previewMatches(preview: RootPreview | null, parameters: PreviewParameters) {
  return !!preview && preview.parameters.initial_value === parameters.initial_value
    && preview.parameters.tolerance === parameters.tolerance && preview.max_iterations === parameters.max_iterations;
}
