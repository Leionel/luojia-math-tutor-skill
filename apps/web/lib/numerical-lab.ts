export type LinearTask = {domain: "linear_system"; method: "jacobi" | "gauss_seidel"; matrix: number[][]; rhs: number[]; initial: number[]; tolerance: number; limit: number};
export type IntegrationTask = {domain: "integration"; method: "trapezoid" | "simpson" | "adaptive_simpson"; expression: string; left: number; right: number; intervals: number; tolerance: number; limit: number};
export type NumericalTask = LinearTask | IntegrationTask;
export type NumericalRow = {k: number; vector: number[] | null; value: number | null; residual: number | null; step: number | null; error_estimate: number | null; error_bound: number | null; work: number; intervals?: number};
export type NumericalRun = {id: string; source_hash: string; schema_version: string; task: NumericalTask; prediction: string; created_at: string; rows: NumericalRow[]; status: string; stop_detail: string; conditions: string[]; evidence_scope: string; independent_success: false};
export type NumericalCheck = {scope: string; matches: boolean; residual?: number; difference?: number; message: string};

export function numericVector(text: string, max = 8): number[] {
  const tokens = text.trim().split(/[\s,，]+/);
  if (!text.trim() || tokens.length > max) throw new Error(`请填写 1–${max} 个数值`);
  const values = tokens.map(token => {
    if (!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(token)) throw new Error("请用空格或逗号分隔有限数值");
    const value = Number(token);
    if (!Number.isFinite(value)) throw new Error("不能使用无穷或非数值");
    return value;
  });
  return values;
}

export function numericMatrix(text: string): number[][] {
  const rows = text.trim().split(/[\n;；]+/).map(row => numericVector(row));
  if (rows.length < 2 || rows.length > 8 || rows.some(row => row.length !== rows.length)) throw new Error("请按每行一个方程填写 2–8 阶方阵");
  return rows;
}

export function comparableNumerical(a: NumericalRun, b: NumericalRun): boolean {
  if (a.task.domain === "integration" && b.task.domain === "integration") {
    return a.task.expression === b.task.expression && a.task.left === b.task.left &&
      a.task.right === b.task.right && a.task.tolerance === b.task.tolerance;
  }
  const left = {...a.task, method: "", limit: 0};
  const right = {...b.task, method: "", limit: 0};
  return JSON.stringify(left) === JSON.stringify(right);
}

export function discussionDraft(run: NumericalRun): string {
  const last = run.rows.at(-1);
  return `我在数值实验台查看了系统参考实验，不是独立测验，也没有执行学生代码。\n实验版本：${run.id} / ${run.source_hash}\n参数：${JSON.stringify(run.task)}\n我的预测：${run.prediction}\n末步记录：${JSON.stringify(last)}\n停止说明：${run.stop_detail}\n证据范围：${run.evidence_scope}\n请帮我理解适用条件、停止依据，以及如何改变一个参数检验预测。积分的误差估计不能当作严格误差上界。`;
}
