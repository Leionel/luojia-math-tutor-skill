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
      unit_type: "definition",
      scope: "prerequisite",
      difficulty: 1,
      mastery: 1.0,
      latex: "\\lim_{x \\to x_0} f(x) = f(x_0)",
      content: "函数在定义域内极限等于函数值。连续性是介值定理与泰勒展开适用的基本前提。",
      formal_statement: "**定义 (函数连续性)**：设函数 $f: D \\to \\mathbb{R}, D \\subset \\mathbb{R}$。若对于点 $x_0 \\in D$，满足：\n$$\\lim_{x \\to x_0} f(x) = f(x_0)$$\n即 $\\forall \\varepsilon > 0, \\exists \\delta > 0$，使得当 $0 < |x - x_0| < \\delta$ 且 $x \\in D$ 时恒有 $|f(x) - f(x_0)| < \\varepsilon$，则称 $f$ 在点 $x_0$ 处连续。若在闭区间 $[a,b]$ 上处处连续，记作 $f \\in C[a,b]$。",
      geometric_meaning: "曲线在区间 $[a,b]$ 上是一条连绵不断、无断开、无跳跃、无空心奇点的连续折线或平滑弧线。",
      conditions_and_failure: "若函数存在跳跃间断点或无穷奇点（如 $f(x)=1/x$ 在 $[-1,1]$），介值定理失效，数值求根可能收敛于不存在真根的伪间断点。",
      cases: ["CASE_BISECTION_REQUIREMENTS"]
    }
  },
  {
    id: "MATH_IVT",
    position: { x: 380, y: 50 },
    type: "skillNode",
    data: {
      label: "介值定理 / 零点定理 (IVT)",
      status: "mastered",
      unit_type: "theorem",
      scope: "prerequisite",
      difficulty: 1,
      mastery: 1.0,
      latex: "f(a)f(b) < 0 \\implies \\exists c \\in (a,b), \\; f(c)=0",
      content: "连续函数在区间两端异号则在开区间内至少存在一个实根，此为二分法的理论保证。",
      formal_statement: "**定理 (Bolzano 零点存在定理)**：设函数 $f(x)$ 满足两个条件：\n1. $f(x) \\in C[a,b]$（在闭区间 $[a,b]$ 上处处连续）；\n2. $f(a) \\cdot f(b) < 0$（在区间端点取值异号）。\n则在开区间 $(a, b)$ 内至少存在一点 $\\xi \\in (a, b)$，使得：\n$$f(\\xi) = 0$$\n该点 $\\xi$ 即为方程 $f(x) = 0$ 的一个真实解（零点）。",
      geometric_meaning: "一条连续曲线从横轴下方连到横轴上方，必定至少横穿 $x$ 轴一次，其交点坐标即为方程零点。",
      conditions_and_failure: "若函数不连续（如存在奇点）或两端同号（包含偶数重根如 $f(x)=(x-1)^2$ 在 $[0,2]$），该定理不适用，无法判定根的存在性。",
      cases: ["CASE_BISECTION_REQUIREMENTS"]
    }
  },
  {
    id: "MATH_DERIVATIVE",
    position: { x: 680, y: 50 },
    type: "skillNode",
    data: {
      label: "导数与切线斜率 (Derivative)",
      status: "mastered",
      unit_type: "definition",
      scope: "prerequisite",
      difficulty: 1,
      mastery: 0.95,
      latex: "f'(x_0) = \\lim_{\\Delta x \\to 0} \\frac{f(x_0+\\Delta x)-f(x_0)}{\\Delta x}",
      content: "瞬时变化率与切线斜率。牛顿迭代法利用导数构造局部线性化切线。",
      formal_statement: "**定义 (导数与切线方程)**：设函数 $f(x)$ 在点 $x_0$ 的某邻域内有定义。若极限：\n$$f'(x_0) = \\lim_{h \\to 0} \\frac{f(x_0 + h) - f(x_0)}{h}$$\n存在有限值，则称 $f$ 在 $x_0$ 处可导。过曲线点 $(x_0, f(x_0))$ 的切线方程为：\n$$y - f(x_0) = f'(x_0)(x - x_0)$$\n令 $y=0$ 即可解出切线与 $x$ 轴交点横坐标 $x = x_0 - \\frac{f(x_0)}{f'(x_0)}$。",
      geometric_meaning: "割线在割点趋于重合时的极限状态，代表曲线在该点处的最优一阶局部线性逼近直线。",
      conditions_and_failure: "若在某点导数 $f'(x_k) = 0$，切线平行于 $x$ 轴，无交点；若 $f'(x_k) \\approx 0$，交点将漂移到无穷远处。",
      cases: ["CASE_NEWTON_DERIVATION"]
    }
  },
  {
    id: "MATH_TAYLOR",
    position: { x: 980, y: 50 },
    type: "skillNode",
    data: {
      label: "泰勒展开公式 (Taylor Expansion)",
      status: "mastered",
      unit_type: "theorem",
      scope: "prerequisite",
      difficulty: 2,
      mastery: 0.9,
      latex: "f(x) = f(x_k) + f'(x_k)(x-x_k) + \\frac{f''(\\xi)}{2}(x-x_k)^2",
      content: "局部多项式逼近。截断高阶项是推导牛顿法及其二阶收敛定理的基础工具。",
      formal_statement: "**定理 (带拉格朗日余项的泰勒展开)**：若函数 $f \\in C^2[a,b]$，则对区间内任意 $x$ 与基准点 $x_k$，存在介于 $x$ 与 $x_k$ 之间的 $\\xi$，满足：\n$$f(x) = f(x_k) + f'(x_k)(x - x_k) + \\frac{f''(\\xi)}{2}(x - x_k)^2$$\n令 $x = x^*$（真根，使 $f(x^*)=0$），忽略二次余项即得到线性近似方程 $0 \\approx f(x_k) + f'(x_k)(x^* - x_k)$，进而解出牛顿格式。",
      geometric_meaning: "用二次抛物线在基准点附近逼近复杂曲线，一阶项给出切线方向，二阶项量化切线与原曲线的弯曲偏离程度。",
      conditions_and_failure: "要求二阶导数 $f''(x)$ 在求根邻域内有界连续。若 $f''$ 无界或不存在，二阶收敛性证明将不复成立。",
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
      content: "在单根处导数非零，牛顿法具备标准的局部二阶收敛特性。",
      formal_statement: "**定义 (一重单根)**：设 $x^*$ 为方程 $f(x)=0$ 的零点，即 $f(x^*)=0$。若满足导数：\n$$f'(x^*) \\neq 0$$\n则称 $x^*$ 为方程的**单根**（一重根）。在代数因式分解上，等价于存在连续函数 $h(x)$ 满足 $f(x) = (x - x^*)h(x)$ 且 $h(x^*) \\neq 0$。",
      geometric_meaning: "曲线以非水平的非零倾角斜穿 $x$ 轴，与横轴呈现横截相交（非相切），根处切线斜率保持显著非零。",
      conditions_and_failure: "单根是牛顿法获得二阶平方加速收敛的核心先决条件。若导数为 0（重根），二阶收敛性质将破灭。",
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
      latex: "f(x^*) = f'(x^*) = \\cdots = f^{(m-1)}(x^*) = 0, \\; f^{(m)}(x^*) \\neq 0",
      content: "在多重根处切线趋于水平，牛顿法二阶收敛失效，退化为一阶线性收敛。",
      formal_statement: "**定义 ($m$ 重根)**：设 $m \\in \\mathbb{N}, m \\ge 2$。若函数 $f(x)$ 在 $x^*$ 处满足：\n$$f(x^*) = f'(x^*) = \\cdots = f^{(m-1)}(x^*) = 0, \\quad \\text{且} \\quad f^{(m)}(x^*) \\neq 0$$\n则称 $x^*$ 为方程 $f(x)=0$ 的 **$m$ 重根**。因式分解满足 $f(x) = (x - x^*)^m h(x)$，其中 $h(x^*) \\neq 0$。",
      geometric_meaning: "曲线在 $x^*$ 处与 $x$ 轴相切。偶数重根（如 $(x-1)^2$）在 $x^*$ 处触碰横轴并折返，不穿越横轴；奇数重根呈现平坦拐点穿轴。",
      conditions_and_failure: "在重根处，牛顿迭代分母 $f'(x_k) \\to 0$，导致牛顿法收敛速率降为线性一阶收敛，渐进误差常数变为 $C = 1 - 1/m$。",
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
      latex: "f(x^*) = 0, \\quad x^* \\in [a, b]",
      content: "求一元连续函数 f(x) 的零点。数值方法通过从初始近似出发的迭代格式逐步逼近解。",
      formal_statement: "**问题定义 (非线性求根)**：给定连续映射 $f: [a,b] \\to \\mathbb{R}$，求解未知数 $x^* \\in [a,b]$ 满足：\n$$f(x^*) = 0$$\n在实际计算中，解析解往往不存在，数值求解的目标是构造序列 $\\{x_k\\}$ 使得 $\\lim_{k \\to \\infty} x_k = x^*$，并在误差 $|x_k - x^*| \\le \\varepsilon$ 满足给定容差时安全终止。",
      geometric_meaning: "在二维直角坐标系中，寻找曲线 $y=f(x)$ 与直线 $y=0$ 的所有交点横坐标。",
      conditions_and_failure: "当方程呈现病态（如根附近导数极小，或高阶重根），微小的函数值扰动将导致解的巨大漂移。",
      cases: ["CASE_BISECTION_REQUIREMENTS", "CASE_STOPPING_CRITERION"]
    }
  },
  {
    id: "NA_BISECTION",
    position: { x: 380, y: 220 },
    type: "skillNode",
    data: {
      label: "二分法 (Bisection Method)",
      status: "mastered",
      unit_type: "algorithm",
      scope: "core",
      difficulty: 2,
      mastery: 0.9,
      latex: "c_k = \\frac{a_k+b_k}{2}, \\quad |c_k - x^*| \\le \\frac{b_0-a_0}{2^{k+1}}",
      content: "基于零点定理对半缩小搜索范围。收敛稳定可靠，但收敛速度较慢（线性一阶）。",
      formal_statement: "**算法原理 (区间对分法)**：已知 $f \\in C[a_0, b_0]$ 且 $f(a_0)f(b_0) < 0$。第 $k$ 步计算中点 $c_k = \\frac{a_k + b_k}{2}$。\n根据函数值符号更新有根区间：\n$$[a_{k+1}, b_{k+1}] = \\begin{cases} [a_k, c_k], & f(a_k)f(c_k) < 0 \\\\ [c_k, b_k], & f(a_k)f(c_k) > 0 \\end{cases}$$\n区间长度满足 $b_k - a_k = \\frac{b_0 - a_0}{2^k}$，近似值 $x_k = c_k$ 的先验误差界为：\n$$|x_k - x^*| \\le \\frac{b_0 - a_0}{2^{k+1}}$$",
      geometric_meaning: "像游标卡尺一样，每步以中点为基准切分区间，每次将包含横截交点的区间测度严格减半。",
      conditions_and_failure: "必须保证 $f \\in C[a,b]$ 且两端异号；无法求解偶数重根；收敛速度为线性（$p=1$），每迭代约 3.32 次增加 1 位有效十进制精度。",
      algorithm_steps: "1. 校验端点变号 $f(a_0)f(b_0) < 0$；\n2. 计算中点 $c_k = a_k + (b_k - a_k)/2$；\n3. 若 $(b_k - a_k)/2 < \\varepsilon_x$ 或 $|f(c_k)| < \\varepsilon_f$，终止并输出 $c_k$；\n4. 若 $f(a_k)f(c_k) < 0$，更新 $b_{k+1}=c_k$；否则更新 $a_{k+1}=c_k$。",
      cases: ["CASE_BISECTION_REQUIREMENTS", "CASE_BISECTION_BRACKET_UPDATE"]
    }
  },
  {
    id: "NA_CONTRACTION_MAPPING",
    position: { x: 680, y: 220 },
    type: "skillNode",
    data: {
      label: "压缩映射原理 (Banach Fixed-Point)",
      status: "learning",
      unit_type: "theorem",
      scope: "core",
      difficulty: 4,
      mastery: 0.4,
      latex: "\\max_{x \\in [a,b]}|g'(x)| \\le L < 1 \\implies \\exists! x^* = g(x^*)",
      content: "若迭代映射在区间内导数模长严格小于 1，则不动点迭代必全局收敛。",
      formal_statement: "**定理 (压缩映射与不动点存在唯一性)**：设映射 $g: [a,b] \\to [a,b]$ 且 $g \\in C[a,b]$。若存在常数 $L \\in (0,1)$，使得 $\\forall x, y \\in [a,b]$ 满足 Lipschitz 条件：\n$$|g(x) - g(y)| \\le L |x - y| \\quad (\\text{可微时等价于 } \\max_{x \\in [a,b]}|g'(x)| \\le L < 1)$$\n则：\n1. $g(x)$ 在 $[a,b]$ 内存在唯一的不动点 $x^* = g(x^*)$；\n2. 从任意初始点 $x_0 \\in [a,b]$ 出发的不动点迭代序列 $x_{k+1} = g(x_k)$ 均收敛于 $x^*$；\n3. 误差估计满足：$|x_k - x^*| \\le \\frac{L^k}{1-L}|x_1 - x_0|$ 及 $|x_k - x^*| \\le \\frac{L}{1-L}|x_k - x_{k-1}|$。",
      geometric_meaning: "曲线 $y=g(x)$ 的倾斜度绝对值严格平于 $45^\\circ$ 直线 $y=x$，迭代在两条线之间往复映射，形成必然向中心不动点螺旋收拢的闭合蛛网。",
      conditions_and_failure: "若 $|g'(x^*)| > 1$，不动点为排斥子，蛛网图呈发散螺旋，迭代序列将向外逃逸而无法收敛。",
      cases: []
    }
  },
  {
    id: "NA_FIXED_POINT",
    position: { x: 980, y: 220 },
    type: "skillNode",
    data: {
      label: "不动点迭代法 (Fixed-Point Iteration)",
      status: "learning",
      unit_type: "algorithm",
      scope: "core",
      difficulty: 3,
      mastery: 0.55,
      latex: "x_{k+1} = g(x_k), \\quad k=0,1,2,\\dots",
      content: "将方程转化为等价形式 x=g(x) 进行递推。格式选取不当会导致序列严重发散。",
      formal_statement: "**算法原理 (不动点迭代)**：将非线性方程 $f(x)=0$ 恒等变形为等价的解耦不动点形式 $x = g(x)$。选取初值 $x_0$，生成递推点列：\n$$x_{k+1} = g(x_k), \\quad k=0,1,2,\\dots$$\n当 $g(x)$ 连续且序列极限 $x^* = \\lim_{k \\to \\infty} x_k$ 存在时，两端取极限即得 $x^* = g(x^*)$，即 $x^*$ 为原方程的根。",
      geometric_meaning: "蛛网图递推：从点 $(x_k, x_k)$ 出发沿垂直方向走到曲线 $(x_k, g(x_k))$，再沿水平方向走到对角线 $(x_{k+1}, x_{k+1})$。",
      conditions_and_failure: "同一方程可改写成多种 $g(x)$ 形式。若所选变形满足 $|g'(x^*)| > 1$，算法将严重发散；仅当 $|g'(x^*)| < 1$ 时才局部收敛。",
      algorithm_steps: "1. 变形构造 $g(x)$ 使得 $|g'(x)| < 1$；\n2. 输入初值 $x_0$ 与停机门限 $\\varepsilon$；\n3. 循环计算 $x_{new} = g(x_{curr})$；\n4. 检验步长 $|x_{new} - x_{curr}| < \\varepsilon$，满足则输出，否则继续。",
      cases: []
    }
  },
  {
    id: "NA_NEWTON",
    position: { x: 1280, y: 220 },
    type: "skillNode",
    data: {
      label: "牛顿迭代法 (Newton-Raphson)",
      status: "learning",
      unit_type: "algorithm",
      scope: "core",
      difficulty: 3,
      mastery: 0.7,
      latex: "x_{k+1} = x_k - \\frac{f(x_k)}{f'(x_k)}",
      content: "利用切线交点迭代，单根条件下具备局部二阶平方收敛速度，计算效率极高。",
      formal_statement: "**算法原理与推导**：将 $f(x)$ 在当前近似值 $x_k$ 处作一阶泰勒线性化展开：\n$$0 = f(x^*) \\approx f(x_k) + f'(x_k)(x^* - x_k)$$\n由此解出下一个更精确的近似值 $x_{k+1}$，确立牛顿迭代公式：\n$$x_{k+1} = x_k - \\frac{f(x_k)}{f'(x_k)}, \\quad k=0,1,2,\\dots$$\n在单根（$f'(x^*) \\neq 0$）与 $f \\in C^2$ 条件下，牛顿法具备局部二阶收敛速度，渐进误差满足：\n$$\\lim_{k \\to \\infty} \\frac{|e_{k+1}|}{|e_k|^2} = \\left| \\frac{f''(x^*)}{2f'(x^*)} \\right|$$",
      geometric_meaning: "切线法：在曲线点 $(x_k, f(x_k))$ 处作一切线，切线与横轴的交点坐标即为下一个迭代近似值 $x_{k+1}$。",
      conditions_and_failure: "1. 导数除零风险：若某步 $f'(x_k) \\approx 0$，切线近乎水平，交点溢出；\n2. 振荡环与发散：初值选取远离吸引盆时可能陷入周期往复死循环；\n3. 重根退化：重根处导数为 0，收敛速度降为一阶线性。",
      algorithm_steps: "1. 给定初值 $x_0$，容差 $\\varepsilon_x, \\varepsilon_f$，最大迭代步数 $K_{\\max}$；\n2. For $k=0, 1, \\dots, K_{\\max}$：\n   a. 计算函数值 $y = f(x_k)$ 与导数值 $d = f'(x_k)$；\n   b. 若 $|d| < 10^{-12}$，报警退出（切线近乎水平，除零危险）；\n   c. 计算增量 $\\Delta x = -y / d$，更新 $x_{k+1} = x_k + \\Delta x$；\n   d. 若 $|\\Delta x| < \\varepsilon_x$ 且 $|f(x_{k+1})| < \\varepsilon_f$，成功收敛退出。",
      cases: ["CASE_NEWTON_DERIVATION", "CASE_NEWTON_LOCAL_CONVERGENCE", "CASE_NEWTON_INITIAL_VALUE"]
    }
  },
  {
    id: "NA_NEWTON_UPDATE",
    position: { x: 1560, y: 220 },
    type: "skillNode",
    data: {
      label: "牛顿迭代步公式 (Newton Step)",
      status: "learning",
      unit_type: "definition",
      scope: "core",
      difficulty: 2,
      mastery: 0.75,
      latex: "\\Delta x_k = -\\frac{f(x_k)}{f'(x_k)}, \\quad x_{k+1} = x_k + \\Delta x_k",
      content: "单步步长计算。编程时须设置导数除以零的数值保护机制。",
      formal_statement: "**定义 (增量式牛顿步)**：单步牛顿修正向量定义为：\n$$\\Delta x_k \\triangleq -\\frac{f(x_k)}{f'(x_k)}$$\n等价于求解线性方程 $f'(x_k) \\Delta x_k = -f(x_k)$。更新公式写作 $x_{k+1} = x_k + \\Delta x_k$。步长模长 $|\\Delta x_k|$ 可作为评估迭代收敛程度的后验判据。",
      geometric_meaning: "直角三角形底边水平长度，表征从当前点沿切线斜坡滑行至横轴水平切口所需的位移增量。",
      conditions_and_failure: "当导数极小时步长发生数值爆炸。生产环境需引入线搜索 (Line Search) 或阻尼因子 $\\lambda \\in (0, 1]$ 构造阻尼牛顿步 $x_{k+1} = x_k + \\lambda \\Delta x_k$。",
      cases: ["CASE_NEWTON_DERIVATION"]
    }
  },

  // Level 2: Invariants & Convergence
  {
    id: "NA_BRACKET_INVARIANT",
    position: { x: 380, y: 390 },
    type: "skillNode",
    data: {
      label: "区间包围不变性 (Bracket Invariant)",
      status: "mastered",
      unit_type: "concept",
      scope: "core",
      difficulty: 2,
      mastery: 0.85,
      latex: "f(a_k)f(b_k) \\le 0, \\quad b_k - a_k = \\frac{b_0-a_0}{2^k}",
      content: "二分法每一步均维持根在区间内的严格不变式，保证算法绝对不会失散。",
      formal_statement: "**定义 (区间包围归纳不变式)**：在二分算法的每次循环迭代中，当前区间 $[a_k, b_k]$ 始终满足逻辑谓词：\n$$\\mathcal{I}(k) \\iff (f(a_k) \\cdot f(b_k) \\le 0) \\;\\land\\; (x^* \\in [a_k, b_k]) \\;\\land\\; (b_k - a_k = 2^{-k}(b_0 - a_0))$$\n该不变式由数学归纳法保证：初始条件 $\\mathcal{I}(0)$ 成立，每步按变号选择子区间保证了 $\\mathcal{I}(k) \\implies \\mathcal{I}(k+1)$。",
      geometric_meaning: "真根始终被两块坚固的端点铁板牢牢夹在中间，随着铁板间距每轮压缩一半，真根无处遁形。",
      conditions_and_failure: "代码中若在中点函数值同号时错误更新了异号端点，将直接破坏该不变式，导致后续迭代在无根区间内空转。",
      cases: ["CASE_BISECTION_BRACKET_UPDATE"]
    }
  },
  {
    id: "NA_LOCAL_CONVERGENCE",
    position: { x: 980, y: 390 },
    type: "skillNode",
    data: {
      label: "局部收敛性定理 (Local Convergence)",
      status: "learning",
      unit_type: "theorem",
      scope: "core",
      difficulty: 3,
      mastery: 0.6,
      latex: "x_0 \\in U(x^*, \\delta) \\implies \\lim_{k \\to \\infty} x_k = x^*",
      content: "仅当初值充分靠近真根邻域内才能保证收敛，对较远初值不保证收敛。",
      formal_statement: "**定理 (牛顿法局部二阶收敛定理)**：设 $f \\in C^2[a,b]$。若 $x^* \\in (a,b)$ 为 $f(x)=0$ 的单根（$f'(x^*) \\neq 0$），则存在常数 $\\delta > 0$ 和 $M > 0$，使得当初始值落在邻域：\n$$x_0 \\in [x^* - \\delta, x^* + \\delta]$$\n内时，牛顿迭代序列 $\\{x_k\\}$ 必定单调或交替收敛到 $x^*$，且误差满足：\n$$|x_{k+1} - x^*| \\le M |x_k - x^*|^2$$\n其中 $M = \\frac{\\max |f''(x)|}{2 \\min |f'(x)|}$。",
      geometric_meaning: "在真根附近存在一个有限大小的‘吸引盆地’ (Basin of Attraction)，只有落入盆地内的初值才会被快速吸入中心零点。",
      conditions_and_failure: "当初始点选在吸引盆之外时，切线可能将迭代点抛离目标区域，引发振荡或无穷发散。",
      cases: ["CASE_NEWTON_LOCAL_CONVERGENCE", "CASE_NEWTON_INITIAL_VALUE"]
    }
  },
  {
    id: "NA_CONVERGENCE_ORDER",
    position: { x: 1280, y: 390 },
    type: "skillNode",
    data: {
      label: "收敛阶 (Order of Convergence)",
      status: "learning",
      unit_type: "definition",
      scope: "core",
      difficulty: 4,
      mastery: 0.45,
      latex: "\\lim_{k \\to \\infty} \\frac{|e_{k+1}|}{|e_k|^p} = C > 0",
      content: "度量误差收敛速度。二分法 p=1，单根牛顿法 p=2，重根牛顿法降为 p=1。",
      formal_statement: "**定义 (收敛阶与渐进常数)**：设数列 $x_k \\to x^*$，令第 $k$ 步误差为 $e_k = x_k - x^*$。若存在实数 $p \\ge 1$ 与常数 $C > 0$（若 $p=1$ 要求 $C < 1$），使得：\n$$\\lim_{k \\to \\infty} \\frac{|e_{k+1}|}{|e_k|^p} = C$$\n则称该算法具有 **$p$ 阶收敛速度**，$C$ 称为渐进误差常数。\n- **$p=1$ (线性收敛)**：$|e_{k+1}| \\approx C |e_k|$，如二分法（$C=0.5$）、重根牛顿法（$C=1-1/m$）；\n- **$p=2$ (二阶平方收敛)**：$|e_{k+1}| \\approx C |e_k|^2$，如单根牛顿法，有效精度位数每代翻番！",
      geometric_meaning: "衡量随着步数增加，迭代点距离真解的距离坍缩的速度等级，决定了算法从粗解到双精度极限定额所需的总算力成本。",
      conditions_and_failure: "若误差比值极限发散或为 0，需使用超线性阶（如弦截法 $p \\approx 1.618$）进行精细分析。",
      cases: ["CASE_NEWTON_LOCAL_CONVERGENCE", "CASE_NEWTON_MULTIPLE_ROOT"]
    }
  },
  {
    id: "NA_ITERATION_TRACE",
    position: { x: 1560, y: 390 },
    type: "skillNode",
    data: {
      label: "迭代轨迹与收敛表 (Iteration Trace)",
      status: "learning",
      unit_type: "concept",
      scope: "core",
      difficulty: 2,
      mastery: 0.7,
      latex: "\\mathcal{T} = \\{(k, x_k, |\\Delta x_k|, |f(x_k)|)\\}",
      content: "数值试验中打印步数、近似解、更新量与残差序列以诊断算法收敛行为。",
      formal_statement: "**定义 (数值轨迹诊断表)**：记录算法执行期间的状态序列四元组集合：\n$$\\mathcal{T} = \\left\\{ (k, \\; x_k, \\; |x_k - x_{k-1}|, \\; |f(x_k)|) \\right\\}_{k=0}^N$$\n并在实验中通过对数差分估算经验收敛阶：\n$$\\hat{p}_k \\approx \\frac{\\ln|x_k - x_{k-1}| - \\ln|x_{k-1} - x_{k-2}|}{\\ln|x_{k-1} - x_{k-2}| - \\ln|x_{k-2} - x_{k-3}|}$$",
      geometric_meaning: "在相空间中记录迭代点跳跃落下的脚印图，直观展现收敛速度是匀速收缩还是指数级暴跌。",
      conditions_and_failure: "在接近浮点机器精度界限（如 $10^{-16}$）时，数值舍入误差占主导，收敛阶估计会产生伪振荡。",
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
      latex: "r_k \\triangleq f(x_k)",
      content: "当前解代入原方程所得偏差量。残差小并不直接代表解误差小（病态问题）。",
      formal_statement: "**定义 (代数残差)**：对任意求出的近似数值解 $x_k$，残差量定义为将其直接代入目标方程所得的函数值：\n$$r_k \\triangleq f(x_k)$$\n残差度量了当前近似点满足方程约束条件 $f(x)=0$ 的物理偏离程度，是程序运行时唯一无需真解即可直接计算的即时判据。",
      geometric_meaning: "曲线点 $(x_k, f(x_k))$ 垂直投影到横轴 $y=0$ 的纵向代数高度差。",
      conditions_and_failure: "残差趋于 0 绝不保证近似解靠近真解！当函数斜率极平缓时，在距离真根很远的地方残差就已小于 $10^{-8}$。",
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
      latex: "e_k \\triangleq x_k - x^* = \\frac{f(x_k)}{f'(\\xi_k)}",
      content: "当前解与真实零点的绝对距离。通常真根未知，需通过后验步长予以估计。",
      formal_statement: "**定义 (真误差与残差关系)**：近似解 $x_k$ 与理论真解 $x^*$ 之间的真实绝对误差定义为：\n$$e_k \\triangleq x_k - x^*$$\n由一阶微分中值定理：$f(x_k) - f(x^*) = f'(\\xi_k)(x_k - x^*)$，由于 $f(x^*)=0$，推得：\n$$e_k = \\frac{r_k}{f'(\\xi_k)}$$\n由此可知，当根处导数 $|f'| \\ll 1$ 极小时，即便残差 $r_k$ 极小，真误差 $e_k$ 也可能异常巨大！",
      geometric_meaning: "数轴上近似数值点与真实交点之间的水平物理距离。",
      conditions_and_failure: "因真根 $x^*$ 实际未知，生产代码不可直接访问 $e_k$，通常利用后验相邻步长 $|x_{k+1} - x_k|$ 作为可计算的保守估计上界。",
      cases: ["CASE_RESIDUAL_VS_ERROR", "CASE_STOPPING_CRITERION"]
    }
  },
  {
    id: "NA_STOPPING_CRITERIA",
    position: { x: 980, y: 560 },
    type: "skillNode",
    data: {
      label: "科学停机准则 (Stopping Rules)",
      status: "learning",
      unit_type: "concept",
      scope: "core",
      difficulty: 2,
      mastery: 0.65,
      latex: "|\\Delta x_k| < \\varepsilon_x(1+|x_k|) \\; \\land \\; |f(x_k)| < \\varepsilon_f",
      content: "综合考察步长判据、残差判据与最大迭代次数三项指标，防范死循环。",
      formal_statement: "**工程级复合停机判定体系**：工业与学术级求解器均采用三重联锁保护：\n$$\\text{Stop} \\iff \\begin{cases} |x_{k+1} - x_k| \\le \\varepsilon_x \\cdot (1 + |x_{k+1}|) & (\\text{自适应步长判据}) \\\\ |f(x_{k+1})| \\le \\varepsilon_f & (\\text{残差约束判据}) \\\\ k \\ge K_{\\max} & (\\text{最大循环步数熔断}) \\end{cases}$$\n只有同时通过步长与残差检验，或触发最大步数熔断告警时，迭代流程方才终止。",
      geometric_meaning: "同时确保点位不再水平晃动且纵向高度已经贴合于横坐标轴，才判定收敛着陆成功。",
      conditions_and_failure: "只用单一残差准则会导致平缓函数处假收敛；只用步长准则会导致极慢序列（如调和级数样移动）误判收敛。",
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
      latex: "f(x)=\\frac{1}{x} \\text{ on } [-1, 1], \\; f(-1)f(1) < 0",
      content: "函数若在区间内包含奇点跳跃，即使两端异号也无零点，警示必须检查连续性。",
      formal_statement: "**反例剖析**：考虑反比例函数 $f(x) = \\frac{1}{x}$ 在闭区间 $[-1, 1]$：\n- 左端点：$f(-1) = -1 < 0$；\n- 右端点：$f(1) = 1 > 0$；\n满足端点变号条件 $f(-1) \\cdot f(1) = -1 < 0$。\n然而方程 $\\frac{1}{x} = 0$ 在 $[-1, 1]$ 内**根本不存在任何实数解**！若盲目运行二分法，程序将把区间不断缩拢至奇点 $x=0$，误将无穷间断点判定为根。",
      geometric_meaning: "双曲线在 $x=0$ 处直接向上下两极飞散断裂，是通过无穷跃迁变号，而不是连续穿轴变号。",
      conditions_and_failure: "证明了：连续性是零点定理与二分法的前提条件，仅靠端点变号是绝不能草率下定论的。",
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
      latex: "f(x)=(x-1)^{10}, \\; f(1.1)=10^{-10} < \\varepsilon, \\; e=0.1",
      content: "函数斜率极端平缓时，在离根很远的地方函数值已经极其微小，容易造成虚假收敛误判。",
      formal_statement: "**反例剖析**：考虑方程 $f(x) = (x - 1)^{10} = 0$，真实精确根为 $x^* = 1$。\n考察候选近似点 $x_k = 1.1$：\n- 代数残差：$r_k = f(1.1) = (0.1)^{10} = 10^{-10}$；\n若停机阈值设为 $\\varepsilon_f = 10^{-6}$，此时残差已远小于门限，程序会过早宣布收敛；\n- 真实误差：$|x_k - x^*| = |1.1 - 1.0| = 0.1$（相对误差高达 $10\\%$）！",
      geometric_meaning: "曲线在根附近由于高阶平坦性紧贴横轴，形成极其宽阔的‘浅水洼区’，微小的水深掩盖了巨大的岸边距离。",
      conditions_and_failure: "揭示了病态问题与重根场景下单一残差停机的致命缺陷，必须依赖步长准则联合判定。",
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
      formal_statement: "**反例剖析**：考虑方程 $f(x) = x^3 - 5x = 0$（真实实根为 $0, \\pm\\sqrt{5}$）。\n选取初始值 $x_0 = 1$ 执行牛顿迭代：\n$$x_1 = 1 - \\frac{f(1)}{f'(1)} = 1 - \\frac{1 - 5}{3(1)^2 - 5} = 1 - \\frac{-4}{-2} = 1 - 2 = -1$$\n再计算下一步 $x_2$：\n$$x_2 = -1 - \\frac{f(-1)}{f'(-1)} = -1 - \\frac{-1 + 5}{3(-1)^2 - 5} = -1 - \\frac{4}{-2} = 1$$\n产生周期序列 $\\{1, -1, 1, -1, \\dots\\}$，迭代陷入死循环闭环，永远无法收敛到任何一个真根！",
      geometric_meaning: "在点 1 处的切线交于 -1，而在 -1 处的切线又精确交回到 1，两条切线在几何上互为镜像倒影，锁死在封闭二周期轨道中。",
      conditions_and_failure: "实锤反驳了‘牛顿法初值任意必收’的错误认知，彰显了设置最大迭代次数熔断保护的不可或缺性。",
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
      formal_statement: "**反例剖析**：考虑双重根方程 $f(x) = (x - 1)^2 = 0$，$x^* = 1$ ($m=2$)。\n应用牛顿公式：\n$$x_{k+1} = x_k - \\frac{(x_k - 1)^2}{2(x_k - 1)} = x_k - \\frac{x_k - 1}{2} = \\frac{x_k + 1}{2}$$\n两边减去真根 $x^*=1$ 得误差递推式：\n$$e_{k+1} = x_{k+1} - 1 = \\frac{1}{2}(x_k - 1) = \\frac{1}{2} e_k$$\n收敛阶 $p=1$（线性收敛），渐进误差常数恒为 $C = 1 - 1/2 = 0.5$。牛顿法引以为傲的‘位数成倍翻番’二阶优势彻底丧失！",
      geometric_meaning: "重根处曲线与横轴相切，切线斜率极小，每次切线交点只能往前挪动当前误差的一半。",
      conditions_and_failure: "若已知根的重数为 $m$，须采用修正牛顿法 $x_{k+1} = x_k - m\\frac{f(x_k)}{f'(x_k)}$ 方可恢复二阶平方收敛速度。",
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
      latex: "f(a)f(b)<0 \\not\\implies \\exists \\xi \\text{ (需满足 } f \\in C)",
      content: "学生直接依据端点异号下定论，忽略检查定义域内是否存在奇点与间断。",
      formal_statement: "**典型思维误区**：认为‘只要两端一正一负，中间就一定有零点’。实际上若定义域内包含无穷奇点、分段跳跃或未定义孔洞，端点变号完全可能是跨越奇点导致的伪变号，区间内并不存在任何根。",
      geometric_meaning: "未核实曲线是否断裂，把上下跳跃错当成横穿坐标轴。",
      conditions_and_failure: "二分法使用前必须严格验证 $f \\in C[a,b]$ 的连续性前提。",
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
      latex: "|f(x_k)| < \\varepsilon \\not\\implies |x_k - x^*| < \\varepsilon",
      content: "误以为函数值很小就是解很精确，忽视平坦函数与病态条件的影响。",
      formal_statement: "**典型思维误区**：误认为 $|f(x_k)| < 10^{-6}$ 就代表计算结果已精确到小数点后 6 位。由误差传递式 $e_k = r_k / f'(\\xi)$ 可知，一旦斜率小于 $10^{-5}$，真实误差将大于 $10^{-1}$，精度相差数个数量级！",
      geometric_meaning: "混淆了直角坐标系中 $y$ 方向的高度误差与 $x$ 方向的位置误差。",
      conditions_and_failure: "必须坚持步长与残差联合停机准则，不可偏废任何一项。",
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
      latex: "x_0 \\notin U(x^*, \\delta) \\implies \\text{可能发散、溢出或陷入死循环}",
      content: "误把局部二阶收敛当成全局无条件收敛，忽视初值选取的必要严谨性。",
      formal_statement: "**典型思维误区**：以为牛顿法速度快，因而初值随便设一个数（如 0 或 100）就能迅速收敛。实际上牛顿法仅具备局部收敛性，初值偏离根的吸引盆会导致切线乱跳、越算越远，甚至陷入周期振荡环死循环。",
      geometric_meaning: "初值选在平缓山峰顶部，切线交点被猛烈弹射到宇宙深空。",
      conditions_and_failure: "实际应用中通常先用二分法将有根区间压缩到足够小，再切换至牛顿法加速收敛。",
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
      latex: "f'(x^*)=0 \\implies p=1 \\text{ (重根处二阶收敛必降阶为一阶)}",
      content: "忽视二阶收敛必须以单根为前提，在重根求解时仍默认会快速平方收敛。",
      formal_statement: "**典型思维误区**：认为‘牛顿法收敛阶永远是 2’。这是完全片面的——牛顿法二阶收敛的前提条件是单根（$f'(x^*) \\neq 0$）。一旦遇到 $m$ 重根（$m \\ge 2$），分母导数趋于零，收敛速度必降阶为普通的一阶线性收敛。",
      geometric_meaning: "相切状态剥夺了切线高速斜交的几何杠杆效应，使得每次迭代修正量受阻。",
      conditions_and_failure: "遇到重根需改用修正牛顿法 $x_{k+1} = x_k - m \\frac{f(x_k)}{f'(x_k)}$ 恢复二阶速度。",
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
