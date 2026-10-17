import type { ExplorationTask, ExperimentPlan } from "./explorations";
import { draftTask, taskDraft } from "./explorations.ts";
export type Domain = ExplorationTask["domain"];
export type TaskDraft = Record<string, string>;
type Field = { name: string; label: string; rows?: number; options?: string[] };
export const experimentDomains: Record<
  Domain,
  {
    label: string;
    fields: Field[];
    empty: TaskDraft;
    observable: string;
    limitations: string;
  }
> = {
  linear_system: {
    label: "GS 线性迭代",
    fields: [
      { name: "matrix", label: "系数矩阵（每行一行）", rows: 3 },
      { name: "rhs", label: "右端项" },
      { name: "initial", label: "初始向量" },
      { name: "tolerance", label: "残差阈值" },
      { name: "limit", label: "迭代上限" },
    ],
    empty: {
      matrix: "",
      rhs: "",
      initial: "",
      tolerance: "0.000001",
      limit: "80",
    },
    observable: "残差、相邻步变化、二阶矩阵谱半径",
    limitations: "有限浮点轨迹不证明一般命题；精确谱半径仅支持二阶GS输入矩阵。",
  },
  root_finding: {
    label: "Newton 求根",
    fields: [
      { name: "function", label: "函数 f(x)" },
      { name: "initial_value", label: "初值" },
      { name: "tolerance", label: "残差阈值" },
      { name: "limit", label: "迭代上限" },
    ],
    empty: {
      function: "",
      initial_value: "0",
      tolerance: "0.000001",
      limit: "20",
    },
    observable: "迭代值、函数值、相邻步变化",
    limitations:
      "只支持标准Newton的实数有限轨迹；残差达标不直接证明根误差或全局收敛，吸引域不假设为单区间。",
  },
  integration: {
    label: "数值积分",
    fields: [
      {
        name: "method",
        label: "积分方法",
        options: ["trapezoid", "simpson", "adaptive_simpson"],
      },
      { name: "expression", label: "被积函数 f(x)" },
      { name: "left", label: "左端点" },
      { name: "right", label: "右端点" },
      { name: "intervals", label: "初始分段数" },
      { name: "tolerance", label: "估计阈值" },
      { name: "limit", label: "细分预算" },
    ],
    empty: {
      method: "simpson",
      expression: "",
      left: "0",
      right: "1",
      intervals: "4",
      tolerance: "0.000001",
      limit: "5",
    },
    observable: "积分近似值、步长细分差、误差估计、求值次数",
    limitations:
      "误差估计依赖光滑性与渐近误差模型，不是严格误差上界；区间解析不能替代光滑性证明。",
  },
};
function number(
  d: TaskDraft,
  key: string,
  min: number,
  max: number,
  integer = false,
) {
  const value = Number(d[key]);
  if (
    !d[key]?.trim() ||
    !Number.isFinite(value) ||
    value < min ||
    value > max ||
    (integer && !Number.isInteger(value))
  )
    throw Error(
      `${key} 须为 ${min} 至 ${max} 的${integer ? "整数" : "有限数"}。`,
    );
  return value;
}
export function parseExperimentTask(
  domain: Domain,
  d: TaskDraft,
): ExplorationTask {
  if (domain === "linear_system")
    return draftTask(d as unknown as Parameters<typeof draftTask>[0]);
  const limit = number(d, "limit", 1, 100, true),
    tolerance = number(
      d,
      "tolerance",
      1e-12,
      domain === "root_finding" ? 0.01 : 0.1,
    );
  if (domain === "root_finding") {
    if (!d.function.trim() || d.function.length > 200)
      throw Error("请填写受控runner支持的函数表达式。");
    return {
      domain,
      method: "newton",
      function: d.function,
      initial_value: number(d, "initial_value", -1e6, 1e6),
      limit,
      tolerance,
    };
  }
  const left = number(d, "left", -1e6, 1e6),
    right = number(d, "right", -1e6, 1e6),
    intervals = number(d, "intervals", 2, 256, true);
  if (
    !["trapezoid", "simpson", "adaptive_simpson"].includes(d.method) ||
    !d.expression.trim() ||
    d.expression.length > 200 ||
    left >= right ||
    (d.method !== "trapezoid" && intervals % 2)
  )
    throw Error("核对积分函数、方法、递增端点；Simpson分段数须为偶数。");
  return {
    domain,
    method: d.method as "simpson" | "trapezoid" | "adaptive_simpson",
    expression: d.expression,
    left,
    right,
    intervals,
    limit,
    tolerance,
  };
}
export function experimentTaskDraft(t: ExplorationTask): TaskDraft {
  if (t.domain === "linear_system") return { ...taskDraft(t) };
  return Object.fromEntries(
    Object.entries(t)
      .filter(([k]) => k !== "domain")
      .map(([k, v]) => [k, String(v)]),
  );
}
export function comparisonFactors(tasks: ExplorationTask[]) {
  const first = tasks[0],
    keys = Object.keys(first).filter((k) => k !== "domain");
  const varying = keys.filter(
    (k) =>
      tasks.length > 1 &&
      JSON.stringify(first[k as keyof typeof first]) !==
        JSON.stringify(tasks[1][k as keyof typeof first]),
  );
  return {
    varying_factors: varying.length
      ? varying
      : [
          first.domain === "linear_system"
            ? "matrix"
            : first.domain === "root_finding"
              ? "initial_value"
              : "intervals",
        ],
    fixed_factors: keys.filter(
      (k) =>
        !varying.includes(k) &&
        k !==
          (first.domain === "linear_system"
            ? "matrix"
            : first.domain === "root_finding"
              ? "initial_value"
              : "intervals"),
    ),
  };
}
export function planForTasks(
  claim: string,
  tasks: ExplorationTask[],
  details?: Partial<ExperimentPlan>,
): ExperimentPlan {
  const domain = experimentDomains[tasks[0].domain];
  return {
    schema_version: "experiment-plan-v1",
    changed_parameter: "task_parameters",
    claim_to_test: claim,
    question_to_test: claim.slice(0, 300),
    known_conditions: [],
    mathematical_reason: "在列明的保持因素下比较参数变化与观测量。",
    observable: domain.observable,
    tool_limitations: [domain.limitations],
    ...comparisonFactors(tasks),
    ...details,
    tasks,
  };
}
