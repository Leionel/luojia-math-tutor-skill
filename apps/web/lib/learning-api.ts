import { API_BASE } from "./api-base";
import { getAuthHeaders } from "./demo-auth";
export {parseTrace, finiteNumber, stableRequestId} from "./learning-input";

export type RootParameters = {
  method: "newton" | "bisection" | "fixed_point"; function: string;
  initial_value?: number | null; interval?: number[] | null; phi?: string | null;
  tolerance: number; goal: "root_error" | "residual";
  iterates?: (number | string)[]; brackets?: number[][]; stop_reason?: string;
  variant?: string; damping?: number; multiplicity?: number; derivative?: string | null; update?: string | null;
};
export type Diagnosis = {
  summary: string; status: string; complete: boolean; next_probe?: string;
  attempt_id?: string; feedback_id?: string; outcome?: string; delivery?: string; input?: RootParameters;
};
export type StudyTask = {
  id: string; kind: string; title: string; reason: string; state: string;
  unit_id: string; challenge?: RootParameters; feedback?: Diagnosis; next_task_id?: string;
};
export type StudyToday = {
  local_date: string; persistent: boolean;
  plan: null | {id: string; minutes: number; stale: boolean; tasks: StudyTask[]};
  reviews: {id: string; stage: number; due_at: string}[];
};
export type ReadingUnit = {
  id: string; title: string; quote: string; latex: string; source_hash: string;
  conditions: string[]; question: string; options: string[]; source_span?: string | null;
  page_start?: number | null; source_document_id?: string | null;
};
export type ReadingDocument = {
  id: string; filename: string; source_hash: string;
  sections: {id: string; title: string; quote: string; start: number; end: number}[];
};
export type ReadingNote = {id: string; source_id: string; section_id?: string | null; source_hash?: string; content: string; created_at: string};
export type LabRun = {
  input_hash: string; runner_version: string; graph_revision: string; max_iterations?: number;
  prediction_timing?: "after_preview";
  id: string; prediction: string; parameters: RootParameters; stop_detail: string;
  rows: {k: number; x: number; fx: number; step: number | null; bracket: number[] | null}[];
  diagnosis: Diagnosis;
};
export type Assessment = {
  id: string; state: string; content_version: string; mode: string;
  answers: Record<string, number>; questions: {id: string; prompt: string; options: string[]}[];
  feedback?: {id: string; reference_match: boolean; reference_answer: number; explanation: string; unit_id: string}[];
  reference_matches?: number;
  score?: {correct: number; total: number; percentage: number}; review_units?: string[];
};

export type LearningOverview = {
  local_date: string; persistent: boolean; access_mode: "account" | "demo";
  plan: null | {minutes: number; total: number; completed: number; stale: boolean};
  next_task: StudyTask | null; pending_tasks: StudyTask[]; stale_tasks: number; due_reviews: number;
  counts: {reading: number; practice: number; independent: number; notes: number; labs: number; teach_backs: number; code_submissions: number};
  active_assessment: null | {id: string; answered: number; total: number};
  latest_assessment: null | {id: string; score: {correct: number; total: number; percentage: number}; review_units: string[]};
};
export type TeachBack = {
  id: string; unit_id: string; title: string; source_hash: string; source_quote: string; text: string; parent_id: string | null;
  conditions: {condition_id: string; condition: string; student_quote: string | null; status: string; followup: string}[];
  model_commentary: string; model_status: string; created_at: string; independent_success: false;
};
export type CodeAssignment = {
  id: string; title: string; template: string; signature: string; checks: string[]; execution_available: false;
};
export type CodeSubmission = {
  id: string; assignment_id: string; code: string; iterates: number[]; stop_reason: string;
  findings: {kind: string; line: number | null; message: string}[]; trace_diagnosis: Diagnosis | null;
  previous_id: string | null; created_at: string; code_executed: false;
  comparison: null | {code_changed: boolean; previous_findings: number; current_findings: number; previous_trace_status: string | null; current_trace_status: string | null};
};

export class LearningRequestError extends Error {
  constructor(message: string, public readonly status: number) { super(message); }
}

export async function learningRequest<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}/api${path}`, {
    method: body === undefined ? "GET" : "POST", cache: "no-store",
    signal,
    headers: {...getAuthHeaders(), ...(body === undefined ? {} : {"Content-Type": "application/json"})},
    ...(body === undefined ? {} : {body: JSON.stringify(body)}),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new LearningRequestError(typeof payload?.detail === "string" ? payload.detail : "请求失败，请保留输入后重试", response.status);
  }
  return payload as T;
}
