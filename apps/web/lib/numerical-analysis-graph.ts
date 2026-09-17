import { Node, Edge } from "@xyflow/react";

export const numericalAnalysisNodes: Node[] = [
  // Level 0: Prerequisite Foundation
  {
    id: "MATH_CONTINUITY",
    position: { x: 100, y: 50 },
    type: "skillNode",
    data: { label: "连续性 (Continuity)", status: "mastered", unit_type: "concept", scope: "prerequisite", difficulty: 1, mastery: 1.0 }
  },
  {
    id: "MATH_IVT",
    position: { x: 380, y: 50 },
    type: "skillNode",
    data: { label: "介值定理 / 零点定理", status: "mastered", unit_type: "theorem", scope: "prerequisite", difficulty: 1, mastery: 1.0 }
  },
  {
    id: "MATH_DERIVATIVE",
    position: { x: 680, y: 50 },
    type: "skillNode",
    data: { label: "导数与切线斜率", status: "mastered", unit_type: "definition", scope: "prerequisite", difficulty: 1, mastery: 0.95 }
  },
  {
    id: "MATH_TAYLOR",
    position: { x: 980, y: 50 },
    type: "skillNode",
    data: { label: "泰勒展开公式", status: "mastered", unit_type: "theorem", scope: "prerequisite", difficulty: 2, mastery: 0.9 }
  },
  {
    id: "MATH_SIMPLE_ROOT",
    position: { x: 1280, y: 50 },
    type: "skillNode",
    data: { label: "单根 (Simple Root)", status: "learning", unit_type: "definition", scope: "prerequisite", difficulty: 2, mastery: 0.6 }
  },
  {
    id: "MATH_MULTIPLE_ROOT",
    position: { x: 1560, y: 50 },
    type: "skillNode",
    data: { label: "重根 (Multiple Root)", status: "learning", unit_type: "definition", scope: "prerequisite", difficulty: 3, mastery: 0.5 }
  },

  // Level 1: Core Methods & Formulations
  {
    id: "NA_ROOT_FINDING",
    position: { x: 100, y: 220 },
    type: "skillNode",
    data: { label: "非线性方程求根问题", status: "mastered", unit_type: "definition", scope: "core", difficulty: 1, mastery: 1.0 }
  },
  {
    id: "NA_BISECTION",
    position: { x: 380, y: 220 },
    type: "skillNode",
    data: { label: "二分法 (Bisection)", status: "mastered", unit_type: "algorithm", scope: "core", difficulty: 2, mastery: 0.9 }
  },
  {
    id: "NA_CONTRACTION_MAPPING",
    position: { x: 680, y: 220 },
    type: "skillNode",
    data: { label: "压缩映射定理", status: "learning", unit_type: "theorem", scope: "core", difficulty: 4, mastery: 0.4 }
  },
  {
    id: "NA_FIXED_POINT",
    position: { x: 980, y: 220 },
    type: "skillNode",
    data: { label: "不动点迭代法", status: "learning", unit_type: "algorithm", scope: "core", difficulty: 3, mastery: 0.55 }
  },
  {
    id: "NA_NEWTON",
    position: { x: 1280, y: 220 },
    type: "skillNode",
    data: { label: "牛顿迭代法 (Newton)", status: "learning", unit_type: "algorithm", scope: "core", difficulty: 3, mastery: 0.7 }
  },
  {
    id: "NA_NEWTON_UPDATE",
    position: { x: 1560, y: 220 },
    type: "skillNode",
    data: { label: "牛顿迭代步公式", status: "learning", unit_type: "definition", scope: "core", difficulty: 2, mastery: 0.75 }
  },

  // Level 2: Invariants & Convergence
  {
    id: "NA_BRACKET_INVARIANT",
    position: { x: 380, y: 390 },
    type: "skillNode",
    data: { label: "区间包围不变性", status: "mastered", unit_type: "concept", scope: "core", difficulty: 2, mastery: 0.85 }
  },
  {
    id: "NA_LOCAL_CONVERGENCE",
    position: { x: 980, y: 390 },
    type: "skillNode",
    data: { label: "局部收敛性 (Local Conv.)", status: "learning", unit_type: "theorem", scope: "core", difficulty: 3, mastery: 0.6 }
  },
  {
    id: "NA_CONVERGENCE_ORDER",
    position: { x: 1280, y: 390 },
    type: "skillNode",
    data: { label: "收敛阶 (Order of Conv.)", status: "learning", unit_type: "definition", scope: "core", difficulty: 4, mastery: 0.45 }
  },
  {
    id: "NA_ITERATION_TRACE",
    position: { x: 1560, y: 390 },
    type: "skillNode",
    data: { label: "迭代轨迹与收敛表", status: "learning", unit_type: "concept", scope: "core", difficulty: 2, mastery: 0.7 }
  },

  // Level 3: Residual & Stopping Rules
  {
    id: "NA_RESIDUAL",
    position: { x: 380, y: 560 },
    type: "skillNode",
    data: { label: "残差 (Residual)", status: "learning", unit_type: "definition", scope: "core", difficulty: 2, mastery: 0.5 }
  },
  {
    id: "NA_APPROX_ERROR",
    position: { x: 680, y: 560 },
    type: "skillNode",
    data: { label: "近似误差 (Approx Error)", status: "learning", unit_type: "definition", scope: "core", difficulty: 2, mastery: 0.5 }
  },
  {
    id: "NA_STOPPING_CRITERIA",
    position: { x: 980, y: 560 },
    type: "skillNode",
    data: { label: "停机准则 (Stopping Rule)", status: "learning", unit_type: "concept", scope: "core", difficulty: 2, mastery: 0.65 }
  },

  // Level 4: Counterexamples (Extension)
  {
    id: "NA_COUNTER_DISCONTINUOUS_SIGN_CHANGE",
    position: { x: 100, y: 730 },
    type: "skillNode",
    data: { label: "反例: 间断点变号伪根", status: "locked", unit_type: "counterexample", scope: "extension", difficulty: 2, mastery: 0.2 }
  },
  {
    id: "NA_COUNTER_RESIDUAL_SMALL_ERROR_LARGE",
    position: { x: 380, y: 730 },
    type: "skillNode",
    data: { label: "反例: 残差极小但误差极大", status: "locked", unit_type: "counterexample", scope: "extension", difficulty: 3, mastery: 0.2 }
  },
  {
    id: "NA_COUNTER_NEWTON_CYCLE",
    position: { x: 980, y: 730 },
    type: "skillNode",
    data: { label: "反例: 牛顿 0↔1 振荡环", status: "locked", unit_type: "counterexample", scope: "extension", difficulty: 3, mastery: 0.15 }
  },
  {
    id: "NA_COUNTER_MULTIPLE_ROOT_LINEAR",
    position: { x: 1280, y: 730 },
    type: "skillNode",
    data: { label: "反例: 重根退化线性收敛", status: "locked", unit_type: "counterexample", scope: "extension", difficulty: 3, mastery: 0.2 }
  },

  // Level 5: Common Misconceptions
  {
    id: "MISC_SIGN_WITHOUT_CONTINUITY",
    position: { x: 100, y: 880 },
    type: "skillNode",
    data: { label: "易错: 忽略连续性用介值定理", status: "learning", unit_type: "misconception", scope: "core", difficulty: 2, mastery: 0.3 }
  },
  {
    id: "MISC_RESIDUAL_EQ_ERROR",
    position: { x: 380, y: 880 },
    type: "skillNode",
    data: { label: "易错: 误将残差等同于真实误差", status: "learning", unit_type: "misconception", scope: "core", difficulty: 2, mastery: 0.3 }
  },
  {
    id: "MISC_NEWTON_ALWAYS_CONVERGES",
    position: { x: 980, y: 880 },
    type: "skillNode",
    data: { label: "易错: 误以为牛顿法初值任意必收", status: "learning", unit_type: "misconception", scope: "core", difficulty: 2, mastery: 0.35 }
  },
  {
    id: "MISC_NEWTON_ALWAYS_QUADRATIC",
    position: { x: 1280, y: 880 },
    type: "skillNode",
    data: { label: "易错: 误以为牛顿法总是二阶收敛", status: "learning", unit_type: "misconception", scope: "core", difficulty: 3, mastery: 0.25 }
  }
];

export const numericalAnalysisEdges: Edge[] = [
  { id: "e1", source: "MATH_CONTINUITY", target: "MATH_IVT", animated: true, style: { stroke: "#10b981", strokeWidth: 2 } },
  { id: "e2", source: "MATH_IVT", target: "NA_BISECTION", animated: true, style: { stroke: "#10b981", strokeWidth: 2 } },
  { id: "e3", source: "NA_BRACKET_INVARIANT", target: "NA_BISECTION", style: { stroke: "#3b82f6", strokeWidth: 1.5 } },
  { id: "e4", source: "MATH_DERIVATIVE", target: "NA_NEWTON", animated: true, style: { stroke: "#3b82f6", strokeWidth: 2 } },
  { id: "e5", source: "MATH_TAYLOR", target: "NA_NEWTON", style: { stroke: "#3b82f6", strokeWidth: 1.5 } },
  { id: "e6", source: "NA_NEWTON_UPDATE", target: "NA_NEWTON", style: { stroke: "#3b82f6", strokeWidth: 1.5 } },
  { id: "e7", source: "MATH_SIMPLE_ROOT", target: "NA_LOCAL_CONVERGENCE", style: { stroke: "#6366f1", strokeWidth: 1.5 } },
  { id: "e8", source: "NA_LOCAL_CONVERGENCE", target: "NA_NEWTON", animated: true, style: { stroke: "#3b82f6", strokeWidth: 2 } },
  { id: "e9", source: "NA_CONVERGENCE_ORDER", target: "NA_NEWTON", style: { stroke: "#6366f1", strokeWidth: 1.5 } },
  { id: "e10", source: "NA_CONTRACTION_MAPPING", target: "NA_FIXED_POINT", animated: true, style: { stroke: "#10b981", strokeWidth: 2 } },
  { id: "e11", source: "NA_STOPPING_CRITERIA", target: "NA_ROOT_FINDING", style: { stroke: "#64748b", strokeWidth: 1.5 } },
  { id: "e12", source: "NA_RESIDUAL", target: "NA_STOPPING_CRITERIA", style: { stroke: "#64748b", strokeWidth: 1.5 } },
  { id: "e13", source: "NA_APPROX_ERROR", target: "NA_STOPPING_CRITERIA", style: { stroke: "#64748b", strokeWidth: 1.5 } },
  { id: "e14", source: "NA_COUNTER_NEWTON_CYCLE", target: "NA_LOCAL_CONVERGENCE", style: { stroke: "#f59e0b", strokeDasharray: "4 4", strokeWidth: 1.5 } },
  { id: "e15", source: "NA_COUNTER_RESIDUAL_SMALL_ERROR_LARGE", target: "NA_RESIDUAL", style: { stroke: "#f59e0b", strokeDasharray: "4 4", strokeWidth: 1.5 } },
  { id: "e16", source: "NA_COUNTER_MULTIPLE_ROOT_LINEAR", target: "NA_CONVERGENCE_ORDER", style: { stroke: "#f59e0b", strokeDasharray: "4 4", strokeWidth: 1.5 } },
  { id: "e17", source: "NA_COUNTER_DISCONTINUOUS_SIGN_CHANGE", target: "MATH_IVT", style: { stroke: "#f59e0b", strokeDasharray: "4 4", strokeWidth: 1.5 } },
  { id: "e18", source: "MISC_RESIDUAL_EQ_ERROR", target: "NA_RESIDUAL", style: { stroke: "#ef4444", strokeDasharray: "4 4", strokeWidth: 1.5 } },
  { id: "e19", source: "MISC_NEWTON_ALWAYS_CONVERGES", target: "NA_LOCAL_CONVERGENCE", style: { stroke: "#ef4444", strokeDasharray: "4 4", strokeWidth: 1.5 } },
  { id: "e20", source: "MISC_NEWTON_ALWAYS_QUADRATIC", target: "NA_CONVERGENCE_ORDER", style: { stroke: "#ef4444", strokeDasharray: "4 4", strokeWidth: 1.5 } },
  { id: "e21", source: "MISC_SIGN_WITHOUT_CONTINUITY", target: "MATH_IVT", style: { stroke: "#ef4444", strokeDasharray: "4 4", strokeWidth: 1.5 } }
];
