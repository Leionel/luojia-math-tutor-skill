import type { LinearTask, NumericalRow } from "./numerical-lab";
import { numericMatrix, numericVector } from "./numerical-lab.ts";
import type {
  ReadingContextRef,
  LinearContextRef,
  RootContextRef,
} from "./learning-context";
export type Source =
  | ReadingContextRef
  | { kind: "course"; unit_id: string; graph_revision: string }
  | { kind: "note"; note_id: string; source_hash: string };
export type PersonalNode = {
  id: string;
  label: string;
  description: string;
  source_ref: Source | null;
};
export type PersonalEdge = {
  id: string;
  source: string;
  target: string;
  relation: "implies" | "supports" | "challenges" | "related" | "unknown";
  reason: string;
};
export type PersonalGraph = { nodes: PersonalNode[]; edges: PersonalEdge[] };
export type Evidence = {
  status: string;
  scope: string;
  reason?: string;
  iteration_matrix?: string[][];
  spectral_radius_exact?: string;
  strict_row_dominant?: boolean;
  rho_less_than_one?: boolean;
  is_counterexample_to_necessity?: boolean;
  statement_scope?: string;
};
export type NewtonTask = {
  domain: "root_finding";
  method: "newton";
  function: string;
  initial_value: number;
  tolerance: number;
  limit: number;
};
export type ExplorationTask = LinearTask | NewtonTask;
export type ExplorationAdvice = {
  status: string;
  reason?: string;
  based_on_revision: number;
  decision?: {
    known_conditions: string[];
    missing_conditions: string[];
    reason: string;
    experiment_proposal?: {
      question_to_test: string;
      observable: string;
      tasks: ExplorationTask[];
    } | null;
  };
  suggested_graph?: PersonalGraph;
  follow_up?: string;
  exploration?: Exploration;
};
export type Run = {
  ref: LinearContextRef | RootContextRef;
  task: ExplorationTask;
  matrix_evidence?: Evidence;
  stop_detail?: string;
  next_question?: string;
  status: string;
  rows: (Partial<NumericalRow> & { k: number; x?: number; fx?: number })[];
  evidence_scope: string;
};
export type History = {
  revision: number;
  at: string;
  action: string;
  claim: string;
  claim_status: string;
  graph: PersonalGraph;
  payload: {
    reason?: string;
    prediction?: string;
    metrics?: string[];
    runs?: Run[];
    target_revision?: number;
  };
};
export type Exploration = {
  id: string;
  owner_id: string;
  title: string;
  claim: string;
  revision: number;
  updated_at: string;
  graph: PersonalGraph;
  history: History[];
  runs: (LinearContextRef | RootContextRef)[];
  origin_session_id?: string;
  advice?: ExplorationAdvice;
  relation_candidates?: { id: string; version: number; status: "pending" | "accepted" | "rejected"; origin: string; graph: PersonalGraph; reason?: string }[];
  decision_receipts?: Record<string, { candidate_id: string; candidate_version: number; status: string; revision: number }>;
  help_exposure: boolean;
  independent_success: false;
  linked_chats: { id: string; title: string }[];
  source_bindings: Record<
    string,
    { title: string; review_state: string; ref: Source }
  >;
  reference_health: { node_id?: string; run_id?: string; state: string }[];
};
export type DraftTask = {
  matrix: string;
  rhs: string;
  initial: string;
  tolerance: string;
  limit: string;
};
export function taskDraft(task: LinearTask): DraftTask {
  return {
    matrix: task.matrix.map((row) => row.join(" ")).join("\n"),
    rhs: task.rhs.join(" "),
    initial: task.initial.join(" "),
    tolerance: String(task.tolerance),
    limit: String(task.limit),
  };
}
export function draftTask(draft: DraftTask): LinearTask {
  const matrix = numericMatrix(draft.matrix),
    rhs = numericVector(draft.rhs),
    initial = numericVector(draft.initial),
    tolerance = Number(draft.tolerance),
    limit = Number(draft.limit);
  if (rhs.length !== matrix.length || initial.length !== matrix.length)
    throw Error("右端项和初值的维数必须与矩阵一致。");
  if (
    !Number.isFinite(tolerance) ||
    tolerance < 1e-12 ||
    tolerance > 0.1 ||
    !Number.isInteger(limit) ||
    limit < 1 ||
    limit > 100
  )
    throw Error("阈值范围为 1e−12 至 0.1；迭代上限为 1–100。");
  if (
    matrix.some((row, i) => Math.abs(row[i]) < 1e-12) ||
    [...matrix.flat(), ...rhs, ...initial].some((x) => Math.abs(x) > 1e6)
  )
    throw Error("对角元素不能为零或过小；各输入绝对值最多 1e6。");
  return {
    domain: "linear_system",
    method: "gauss_seidel",
    matrix,
    rhs,
    initial,
    tolerance,
    limit,
  };
}
export const emptyTask: DraftTask = {
  matrix: "",
  rhs: "",
  initial: "",
  tolerance: "0.000001",
  limit: "80",
};
export function gsStatus(status: string) {
  return (
    (
      {
        residual_met: "残差达到阈值",
        iteration_limit: "达到迭代预算",
        numerical_overflow: "数值超出预算",
      } as Record<string, string>
    )[status] ?? "状态待核对"
  );
}
