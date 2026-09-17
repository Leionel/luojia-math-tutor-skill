import { Node, Edge } from "@xyflow/react";

export interface TeachingCaseSummary {
  case_id: string;
  title: string;
  task_type: string;
  learning_objectives: string[];
  concept_ids: string[];
  accepted_variants: string[];
  diagnostic_probes: Array<{ probe_id: string; question: string; correct_answer: string }>;
  disclosure_policy: string;
}

export const teachingCasesList: TeachingCaseSummary[] = [
  {
    case_id: "CASE_BISECTION_REQUIREMENTS",
    title: "二分法使用条件与端点符号判断",
    task_type: "concept_explanation",
    learning_objectives: ["理解二分法成立的两个核心前提：连续性与端点函数值异号"],
    concept_ids: ["NA_BISECTION", "MATH_CONTINUITY", "MATH_IVT"],
    accepted_variants: ["二分法需要满足什么条件", "二分法什么时候可以用", "什么时候不能用二分法求根"],
    diagnostic_probes: [
      {
        probe_id: "PROBE_BISECTION_COND",
        question: "如果一个函数在区间两端 f(a) 和 f(b) 异号，是否一定能在 (a,b) 内用二分法找到根？",
        correct_answer: "不一定，函数必须在 [a,b] 上连续（反例：f(x)=1/x 在 [-1,1]）"
      }
    ],
    disclosure_policy: "direct"
  },
  {
    case_id: "CASE_BISECTION_BRACKET_UPDATE",
    title: "二分法区间端点更新与符号保持",
    task_type: "error_debugging",
    learning_objectives: ["掌握中点求值后如何正确更新左端点或右端点以保持包围不变式"],
    concept_ids: ["NA_BISECTION", "NA_BRACKET_INVARIANT"],
    accepted_variants: ["二分法中点函数值同号怎么更新", "二分法区间怎么缩小", "为什么二分法有时候越算越偏"],
    diagnostic_probes: [
      {
        probe_id: "PROBE_BISECTION_UPDATE",
        question: "若 f(a)<0, f(b)>0，计算中点 c 得 f(c)>0，新的有根区间应该是 [a,c] 还是 [c,b]？",
        correct_answer: "[a,c]，因为 f(a) 与 f(c) 异号"
      }
    ],
    disclosure_policy: "scaffolded"
  },
  {
    case_id: "CASE_NEWTON_DERIVATION",
    title: "牛顿迭代公式几何切线与泰勒展开推导",
    task_type: "derivation",
    learning_objectives: ["推导牛顿迭代公式 x_{k+1} = x_k - f(x_k)/f'(x_k) 的几何切线与一阶泰勒展开本质"],
    concept_ids: ["NA_NEWTON", "MATH_DERIVATIVE", "MATH_TAYLOR"],
    accepted_variants: ["牛顿法公式是怎么推出来的", "牛顿切线法几何意义", "泰勒展开怎么推牛顿法"],
    diagnostic_probes: [],
    disclosure_policy: "direct"
  },
  {
    case_id: "CASE_NEWTON_LOCAL_CONVERGENCE",
    title: "牛顿迭代法局部收敛性与二阶收敛定理",
    task_type: "convergence_analysis",
    learning_objectives: ["掌握牛顿法局部二阶收敛的三个核心条件：单根、二阶连续可微、初值充分靠近"],
    concept_ids: ["NA_NEWTON", "NA_LOCAL_CONVERGENCE", "NA_CONVERGENCE_ORDER", "MATH_SIMPLE_ROOT"],
    accepted_variants: ["牛顿法为什么是二阶收敛", "牛顿法局部收敛的条件是什么", "牛顿法收敛速度有多快"],
    diagnostic_probes: [
      {
        probe_id: "PROBE_NEWTON_CONDITIONS",
        question: "若 f'(x*)=0（即根为重根），牛顿法是否仍然能保持二阶收敛？",
        correct_answer: "不能，重根时牛顿法收敛速度退化为一阶（线性收敛）"
      }
    ],
    disclosure_policy: "direct"
  },
  {
    case_id: "CASE_NEWTON_INITIAL_VALUE",
    title: "牛顿法初值敏感性与发散振荡排查",
    task_type: "error_debugging",
    learning_objectives: ["理解初值选择不当导致切线交点外溢、周期振荡或发散的原因"],
    concept_ids: ["NA_NEWTON", "NA_LOCAL_CONVERGENCE", "NA_COUNTER_NEWTON_CYCLE"],
    accepted_variants: [
      "为什么牛顿法初值选不好会发散",
      "牛顿法为什么初值选不好会发散",
      "为什么牛顿法初值很重要",
      "牛顿迭代死循环怎么回事"
    ],
    diagnostic_probes: [
      {
        probe_id: "PROBE_NEWTON_INIT",
        question: "牛顿法是不是初值选在哪都能找到最近的根？",
        correct_answer: "不是，初值不合适可能导致迭代序列发散或跳到其他非常遥远的根"
      }
    ],
    disclosure_policy: "scaffolded"
  },
  {
    case_id: "CASE_NEWTON_MULTIPLE_ROOT",
    title: "重根情形下牛顿法收敛性退化与改进格式",
    task_type: "convergence_analysis",
    learning_objectives: ["理解 m 重根导致牛顿法退化为线性收敛，并掌握带乘子 m 的修正牛顿法"],
    concept_ids: ["NA_NEWTON", "MATH_MULTIPLE_ROOT", "NA_CONVERGENCE_ORDER", "NA_COUNTER_MULTIPLE_ROOT_LINEAR"],
    accepted_variants: [
      "重根情况下牛顿法的收敛阶是多少",
      "重根情况下牛顿法的收敛速度是多少",
      "牛顿法算重根为什么变慢了",
      "重根怎么修改牛顿法"
    ],
    diagnostic_probes: [],
    disclosure_policy: "scaffolded"
  },
  {
    case_id: "CASE_RESIDUAL_VS_ERROR",
    title: "残差小与真实误差大的辨析 (病态方程求根)",
    task_type: "concept_explanation",
    learning_objectives: ["明晰残差 |f(x)| 与真误差 |x-x*| 的区别，掌握导数平缓时为什么残差不能完全代表收敛"],
    concept_ids: ["NA_RESIDUAL", "NA_APPROX_ERROR", "NA_STOPPING_CRITERIA", "NA_COUNTER_RESIDUAL_SMALL_ERROR_LARGE"],
    accepted_variants: [
      "残差很小是不是就说明算对了",
      "残差和误差有什么区别",
      "为什么不能只用 f(x)<1e-6 当停机准则"
    ],
    diagnostic_probes: [
      {
        probe_id: "PROBE_RESIDUAL_ERROR",
        question: "如果 |f(x_k)| < 10^{-7}，能不能直接断定 x_k 距离真根的误差一定小于 10^{-7}？",
        correct_answer: "不能！当函数斜率很平缓时，残差极小但真实误差可能很大"
      }
    ],
    disclosure_policy: "direct"
  },
  {
    case_id: "CASE_STOPPING_CRITERION",
    title: "科学停机准则与死循环防护设计",
    task_type: "code_task",
    learning_objectives: ["学会构造同时检查步长、残差与最大迭代次数的健壮数值算法终止条件"],
    concept_ids: ["NA_STOPPING_CRITERIA", "NA_RESIDUAL", "NA_APPROX_ERROR"],
    accepted_variants: ["求根算法什么时候停止迭代", "停机准则怎么写最安全", "为什么迭代要加 max_iter"],
    diagnostic_probes: [],
    disclosure_policy: "scaffolded"
  }
];

export function matchLocalCase(query: string) {
  const q = query.trim().toLowerCase();
  for (const c of teachingCasesList) {
    for (const v of c.accepted_variants) {
      if (q.includes(v) || v.includes(q)) {
        return {
          case_id: c.case_id,
          case_info: c,
          decision: "SAME_CASE",
          confidence: 0.96,
          concept_anchors: c.concept_ids
        };
      }
    }
    // Partial word matching
    if (q.includes("重根") && c.case_id.includes("MULTIPLE_ROOT")) {
      return { case_id: c.case_id, case_info: c, decision: "SAME_CASE", confidence: 0.92, concept_anchors: c.concept_ids };
    }
    if (q.includes("初值") && c.case_id.includes("INITIAL_VALUE")) {
      return { case_id: c.case_id, case_info: c, decision: "SAME_CASE", confidence: 0.94, concept_anchors: c.concept_ids };
    }
    if (q.includes("残差") && c.case_id.includes("RESIDUAL")) {
      return { case_id: c.case_id, case_info: c, decision: "SAME_CASE", confidence: 0.95, concept_anchors: c.concept_ids };
    }
    if (q.includes("二分法") && c.case_id.includes("BISECTION")) {
      return { case_id: c.case_id, case_info: c, decision: "SAME_CASE", confidence: 0.90, concept_anchors: c.concept_ids };
    }
  }
  return {
    case_id: null,
    case_info: null,
    decision: "NEW_CASE",
    confidence: 0.15,
    concept_anchors: []
  };
}

export const numericalAnalysisNodes: Node[] = [
  // Level 0: Prerequisite Foundation
  {
    id: "MATH_CONTINUITY",
    position: { x: 100, y: 50 },
    type: "skillNode",
    data: {
      label: "连续性 (Continuity)",
      status: "mastered",
      unit_type: "concept",
      scope: "prerequisite",
      difficulty: 1,
      mastery: 1.0,
      latex: "\\lim_{x \\to x_0} f(x) = f(x_0)",
      content: "函数在定义域内极限等于函数值。连续性是介值定理与泰勒展开适用的基本前提。",
      cases: ["CASE_BISECTION_REQUIREMENTS"]
    }
  },
  {
    id: "MATH_IVT",
    position: { x: 380, y: 50 },
    type: "skillNode",
    data: {
      label: "介值定理 / 零点定理",
      status: "mastered",
      unit_type: "theorem",
      scope: "prerequisite",
      difficulty: 1,
      mastery: 1.0,
      latex: "f(a)f(b) < 0 \\implies \\exists c \\in (a,b), \\; f(c)=0",
      content: "连续函数在区间两端异号则在开区间内至少存在一个实根，此为二分法的理论保证。",
      cases: ["CASE_BISECTION_REQUIREMENTS"]
    }
  },
  {
    id: "MATH_DERIVATIVE",
    position: { x: 680, y: 50 },
    type: "skillNode",
    data: {
      label: "导数与切线斜率",
      status: "mastered",
      unit_type: "definition",
      scope: "prerequisite",
      difficulty: 1,
      mastery: 0.95,
      latex: "f'(x) = \\lim_{h \\to 0} \\frac{f(x+h)-f(x)}{h}",
      content: "瞬时变化率与切线斜率。牛顿迭代法利用导数构造局部线性化切线。",
      cases: ["CASE_NEWTON_DERIVATION"]
    }
  },
  {
    id: "MATH_TAYLOR",
    position: { x: 980, y: 50 },
    type: "skillNode",
    data: {
      label: "泰勒展开公式",
      status: "mastered",
      unit_type: "theorem",
      scope: "prerequisite",
      difficulty: 2,
      mastery: 0.9,
      latex: "f(x) = f(x_k) + f'(x_k)(x-x_k) + \\frac{f''(\\xi)}{2}(x-x_k)^2",
      content: "局部多项式逼近。截断高阶项是推导牛顿法及其二阶收敛定理的基础工具。",
      cases: ["CASE_NEWTON_DERIVATION", "CASE_NEWTON_LOCAL_CONVERGENCE"]
    }
  },
  {
    id: "MATH_SIMPLE_ROOT",
    position: { x: 1280, y: 50 },
    type: "skillNode",
    data: {
      label: "单根 (Simple Root)",
      status: "learning",
      unit_type: "definition",
      scope: "prerequisite",
      difficulty: 2,
      mastery: 0.6,
      latex: "f(x^*) = 0 \\quad \\text{且} \\quad f'(x^*) \\neq 0",
      content: "在单根处，导数非零，牛顿法具备标准的局部二阶收敛特性。",
      cases: ["CASE_NEWTON_LOCAL_CONVERGENCE"]
    }
  },
  {
    id: "MATH_MULTIPLE_ROOT",
    position: { x: 1560, y: 50 },
    type: "skillNode",
    data: {
      label: "重根 (Multiple Root)",
      status: "learning",
      unit_type: "definition",
      scope: "prerequisite",
      difficulty: 3,
      mastery: 0.5,
      latex: "f(x^*) = f'(x^*) = 0, \\quad f''(x^*) \\neq 0 \\quad (m=2)",
      content: "在多重根处，切线趋于水平，牛顿法二阶收敛失效，退化为一阶线性收敛。",
      cases: ["CASE_NEWTON_MULTIPLE_ROOT"]
    }
  },

  // Level 1: Core Methods & Formulations
  {
    id: "NA_ROOT_FINDING",
    position: { x: 100, y: 220 },
    type: "skillNode",
    data: {
      label: "非线性方程求根问题",
      status: "mastered",
      unit_type: "definition",
      scope: "core",
      difficulty: 1,
      mastery: 1.0,
      latex: "f(x^*) = 0",
      content: "求一元连续函数 f(x) 的零点。数值方法通过从初始近似出发的迭代格式逐步逼近解。",
      cases: ["CASE_BISECTION_REQUIREMENTS", "CASE_STOPPING_CRITERION"]
    }
  },
  {
    id: "NA_BISECTION",
    position: { x: 380, y: 220 },
    type: "skillNode",
    data: {
      label: "二分法 (Bisection)",
      status: "mastered",
      unit_type: "algorithm",
      scope: "core",
      difficulty: 2,
      mastery: 0.9,
      latex: "c = \\frac{a+b}{2}, \\quad f(a)f(c) < 0 \\implies b \\leftarrow c",
      content: "基于零点定理对半缩小搜索范围。收敛稳定可靠，但收敛速度较慢（线性一阶）。",
      cases: ["CASE_BISECTION_REQUIREMENTS", "CASE_BISECTION_BRACKET_UPDATE"]
    }
  },
  {
    id: "NA_CONTRACTION_MAPPING",
    position: { x: 680, y: 220 },
    type: "skillNode",
    data: {
      label: "压缩映射定理",
      status: "learning",
      unit_type: "theorem",
      scope: "core",
      difficulty: 4,
      mastery: 0.4,
      latex: "|g'(x)| \\le L < 1 \\implies \\text{存在唯一不动点且必收敛}",
      content: "若迭代映射在区间内导数模长严格小于 1，则不动点迭代必全局收敛。",
      cases: []
    }
  },
  {
    id: "NA_FIXED_POINT",
    position: { x: 980, y: 220 },
    type: "skillNode",
    data: {
      label: "不动点迭代法",
      status: "learning",
      unit_type: "algorithm",
      scope: "core",
      difficulty: 3,
      mastery: 0.55,
      latex: "x_{k+1} = g(x_k)",
      content: "将方程转化为等价形式 x=g(x) 进行递推。格式选取不当会导致序列严重发散。",
      cases: []
    }
  },
  {
    id: "NA_NEWTON",
    position: { x: 1280, y: 220 },
    type: "skillNode",
    data: {
      label: "牛顿迭代法 (Newton)",
      status: "learning",
      unit_type: "algorithm",
      scope: "core",
      difficulty: 3,
      mastery: 0.7,
      latex: "x_{k+1} = x_k - \\frac{f(x_k)}{f'(x_k)}",
      content: "利用切线交点迭代，单根条件下具备局部二阶平方收敛速度，计算效率极高。",
      cases: ["CASE_NEWTON_DERIVATION", "CASE_NEWTON_LOCAL_CONVERGENCE", "CASE_NEWTON_INITIAL_VALUE"]
    }
  },
  {
    id: "NA_NEWTON_UPDATE",
    position: { x: 1560, y: 220 },
    type: "skillNode",
    data: {
      label: "牛顿迭代步公式",
      status: "learning",
      unit_type: "definition",
      scope: "core",
      difficulty: 2,
      mastery: 0.75,
      latex: "\\Delta x_k = -\\frac{f(x_k)}{f'(x_k)}",
      content: "单步步长计算。编程时须设置导数除以零的数值保护机制。",
      cases: ["CASE_NEWTON_DERIVATION"]
    }
  },

  // Level 2: Invariants & Convergence
  {
    id: "NA_BRACKET_INVARIANT",
    position: { x: 380, y: 390 },
    type: "skillNode",
    data: {
      label: "区间包围不变性",
      status: "mastered",
      unit_type: "concept",
      scope: "core",
      difficulty: 2,
      mastery: 0.85,
      latex: "f(a_k)f(b_k) \\le 0, \\quad b_k - a_k = \\frac{b_0-a_0}{2^k}",
      content: "二分法每一步均维持根在区间内的严格不变式，保证算法绝对不会失散。",
      cases: ["CASE_BISECTION_BRACKET_UPDATE"]
    }
  },
  {
    id: "NA_LOCAL_CONVERGENCE",
    position: { x: 980, y: 390 },
    type: "skillNode",
    data: {
      label: "局部收敛性 (Local Conv.)",
      status: "learning",
      unit_type: "theorem",
      scope: "core",
      difficulty: 3,
      mastery: 0.6,
      latex: "x_0 \\in U(x^*, \\delta) \\implies \\lim_{k \\to \\infty} x_k = x^*",
      content: "仅当初值充分靠近真根邻域内才能保证收敛，对较远初值不保证收敛。",
      cases: ["CASE_NEWTON_LOCAL_CONVERGENCE", "CASE_NEWTON_INITIAL_VALUE"]
    }
  },
  {
    id: "NA_CONVERGENCE_ORDER",
    position: { x: 1280, y: 390 },
    type: "skillNode",
    data: {
      label: "收敛阶 (Order of Conv.)",
      status: "learning",
      unit_type: "definition",
      scope: "core",
      difficulty: 4,
      mastery: 0.45,
      latex: "\\lim_{k \\to \\infty} \\frac{|e_{k+1}|}{|e_k|^p} = C",
      content: "度量误差收敛速度。二分法 p=1，单根牛顿法 p=2，重根牛顿法降为 p=1。",
      cases: ["CASE_NEWTON_LOCAL_CONVERGENCE", "CASE_NEWTON_MULTIPLE_ROOT"]
    }
  },
  {
    id: "NA_ITERATION_TRACE",
    position: { x: 1560, y: 390 },
    type: "skillNode",
    data: {
      label: "迭代轨迹与收敛表",
      status: "learning",
      unit_type: "concept",
      scope: "core",
      difficulty: 2,
      mastery: 0.7,
      latex: "\\{(k, x_k, |x_k - x_{k-1}|, |f(x_k)|)\\}",
      content: "数值试验中打印步数、近似解、更新量与残差序列以诊断算法收敛行为。",
      cases: []
    }
  },

  // Level 3: Residual & Stopping Rules
  {
    id: "NA_RESIDUAL",
    position: { x: 380, y: 560 },
    type: "skillNode",
    data: {
      label: "残差 (Residual)",
      status: "learning",
      unit_type: "definition",
      scope: "core",
      difficulty: 2,
      mastery: 0.5,
      latex: "r_k = f(x_k)",
      content: "当前解代入原方程所得偏差量。残差小并不直接代表解误差小（病态问题）。",
      cases: ["CASE_RESIDUAL_VS_ERROR", "CASE_STOPPING_CRITERION"]
    }
  },
  {
    id: "NA_APPROX_ERROR",
    position: { x: 680, y: 560 },
    type: "skillNode",
    data: {
      label: "近似误差 (Approx Error)",
      status: "learning",
      unit_type: "definition",
      scope: "core",
      difficulty: 2,
      mastery: 0.5,
      latex: "e_k = x_k - x^*",
      content: "当前解与真实零点的绝对距离。通常真根未知，需通过后验步长予以估计。",
      cases: ["CASE_RESIDUAL_VS_ERROR", "CASE_STOPPING_CRITERION"]
    }
  },
  {
    id: "NA_STOPPING_CRITERIA",
    position: { x: 980, y: 560 },
    type: "skillNode",
    data: {
      label: "停机准则 (Stopping Rule)",
      status: "learning",
      unit_type: "concept",
      scope: "core",
      difficulty: 2,
      mastery: 0.65,
      latex: "|x_{k+1}-x_k| < \\varepsilon_x \\; \\text{且} \\; |f(x_{k+1})| < \\varepsilon_f",
      content: "综合考察步长判据、残差判据与最大迭代次数三项指标，防范死循环。",
      cases: ["CASE_STOPPING_CRITERION"]
    }
  },

  // Level 4: Counterexamples (Extension)
  {
    id: "NA_COUNTER_DISCONTINUOUS_SIGN_CHANGE",
    position: { x: 100, y: 730 },
    type: "skillNode",
    data: {
      label: "反例: 间断点变号伪根",
      status: "locked",
      unit_type: "counterexample",
      scope: "extension",
      difficulty: 2,
      mastery: 0.2,
      latex: "f(-1)f(1) < 0 \\text{ 但 } f(x)=\\frac{1}{x} \\text{ 无根}",
      content: "函数若在区间内包含奇点跳跃，即使两端异号也无零点，警示必须检查连续性。",
      cases: ["CASE_BISECTION_REQUIREMENTS"]
    }
  },
  {
    id: "NA_COUNTER_RESIDUAL_SMALL_ERROR_LARGE",
    position: { x: 380, y: 730 },
    type: "skillNode",
    data: {
      label: "反例: 残差极小但误差极大",
      status: "locked",
      unit_type: "counterexample",
      scope: "extension",
      difficulty: 3,
      mastery: 0.2,
      latex: "|f(x)| < 10^{-6} \\quad \\text{但} \\quad |x-x^*| > 1.0",
      content: "函数斜率极端平缓时，在离根很远的地方函数值已经极其微小，容易造成虚假收敛误判。",
      cases: ["CASE_RESIDUAL_VS_ERROR"]
    }
  },
  {
    id: "NA_COUNTER_NEWTON_CYCLE",
    position: { x: 980, y: 730 },
    type: "skillNode",
    data: {
      label: "反例: 牛顿 0↔1 振荡环",
      status: "locked",
      unit_type: "counterexample",
      scope: "extension",
      difficulty: 3,
      mastery: 0.15,
      latex: "x_{k+1} = 1 - x_k \\implies x_k \\in \\{0, 1, 0, 1, \\dots\\}",
      content: "特定多项式与初值会导致切线交点在两点间反复横跳死循环，永远无法收敛。",
      cases: ["CASE_NEWTON_INITIAL_VALUE"]
    }
  },
  {
    id: "NA_COUNTER_MULTIPLE_ROOT_LINEAR",
    position: { x: 1280, y: 730 },
    type: "skillNode",
    data: {
      label: "反例: 重根退化线性收敛",
      status: "locked",
      unit_type: "counterexample",
      scope: "extension",
      difficulty: 3,
      mastery: 0.2,
      latex: "f(x)=(x-1)^2 \\implies e_{k+1} = \\frac{1}{2}e_k \\; (p=1)",
      content: "重根处切线趋近于零，牛顿法渐进误差因子恒为 (1 - 1/m)，丧失二次平方加速。",
      cases: ["CASE_NEWTON_MULTIPLE_ROOT"]
    }
  },

  // Level 5: Common Misconceptions
  {
    id: "MISC_SIGN_WITHOUT_CONTINUITY",
    position: { x: 100, y: 880 },
    type: "skillNode",
    data: {
      label: "易错: 忽略连续性用介值定理",
      status: "learning",
      unit_type: "misconception",
      scope: "core",
      difficulty: 2,
      mastery: 0.3,
      latex: "f(a)f(b)<0 \\not\\implies \\text{必有根 (需连续)}",
      content: "学生直接依据端点异号下定论，忽略检查定义域内是否存在奇点与间断。",
      cases: ["CASE_BISECTION_REQUIREMENTS"]
    }
  },
  {
    id: "MISC_RESIDUAL_EQ_ERROR",
    position: { x: 380, y: 880 },
    type: "skillNode",
    data: {
      label: "易错: 误将残差等同于真实误差",
      status: "learning",
      unit_type: "misconception",
      scope: "core",
      difficulty: 2,
      mastery: 0.3,
      latex: "|f(x)| < \\varepsilon \\not\\implies |x-x^*| < \\varepsilon",
      content: "误以为函数值很小就是解很精确，忽视平坦函数与病态条件的影响。",
      cases: ["CASE_RESIDUAL_VS_ERROR"]
    }
  },
  {
    id: "MISC_NEWTON_ALWAYS_CONVERGES",
    position: { x: 980, y: 880 },
    type: "skillNode",
    data: {
      label: "易错: 误以为牛顿法初值任意必收",
      status: "learning",
      unit_type: "misconception",
      scope: "core",
      difficulty: 2,
      mastery: 0.35,
      latex: "x_0 \\notin U(x^*, \\delta) \\implies \\text{可能发散或振荡}",
      content: "误把局部二阶收敛当成全局无条件收敛，忽视初值选取的必要严谨性。",
      cases: ["CASE_NEWTON_INITIAL_VALUE"]
    }
  },
  {
    id: "MISC_NEWTON_ALWAYS_QUADRATIC",
    position: { x: 1280, y: 880 },
    type: "skillNode",
    data: {
      label: "易错: 误以为牛顿法总是二阶收敛",
      status: "learning",
      unit_type: "misconception",
      scope: "core",
      difficulty: 3,
      mastery: 0.25,
      latex: "f'(x^*)=0 \\implies p=1 \\text{ (降阶为线性)}",
      content: "忽视二阶收敛必须以单根为前提，在重根求解时仍默认会快速平方收敛。",
      cases: ["CASE_NEWTON_MULTIPLE_ROOT"]
    }
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
