import type {LabRun, RootParameters} from "./learning-api";

export type LearningContextRef = {
  kind: "root_lab"; record_id: string; input_hash: string;
  runner_version: string; graph_revision: string; selected_step: number | null;
};
export type LearningTaskSnapshot = {
  version: "learning-context-v1"; ref: LearningContextRef; title: string;
  evidence_kind: "reference_help"; independent_success: false;
  parameters: RootParameters; rows: LabRun["rows"]; total_rows: number; omitted_rows: number;
  stop_detail: string; diagnosis_summary: string; max_iterations: number;
  iteration_budget_source: "saved" | "legacy_default";
};
export function rootContextRef(run: LabRun, selectedStep: number | null = null): LearningContextRef {
  if (!/^[a-f0-9]{64}$/.test(run.input_hash) || !run.runner_version || !run.graph_revision) {
    throw new Error("实验缺少版本信息，请重新运行后讨论。");
  }
  if (selectedStep !== null && (!Number.isInteger(selectedStep) || selectedStep < 0 || selectedStep >= run.rows.length)) {
    throw new Error("所选迭代步骤不存在。");
  }
  return {kind: "root_lab", record_id: run.id, input_hash: run.input_hash,
    runner_version: run.runner_version, graph_revision: run.graph_revision, selected_step: selectedStep};
}
export function labChatKey(owner: string, runId: string) {return `luojia_lab_chat:${owner}:${runId}`;}
