"""Authoring helper for developer-authored v2 gold; teacher review is still required."""
import json
from pathlib import Path

FAMILIES = {
"CASE_BISECTION_REQUIREMENTS": ["二分法要保证有根，连续性和端点异号分别起什么作用？", "端点异号但函数在区间内有跳跃，能用零点定理吗？", "Does bisection require continuity throughout the bracket?", "f(x)=1/x在[-1,1]端点异号，为什么并不能推出区间有根？", "二分法要求端点函数值乘积小于零还是小于等于零？", "若其中一个端点恰是根，如何处理二分法的初始化？", "区间内有不连续点时，端点异号的结论还成立吗？", "Explain why opposite signs alone are insufficient without continuity.", "二分法是找到一个根还是能保证枚举区间内全部根？", "零点存在条件和二分迭代更新不变式有什么关系？"],
"CASE_BISECTION_BRACKET_UPDATE": ["中点与左端同号，二分下一步该替换哪一个端点？", "端点乘积为负，中点与右端同号，应保留哪半段？", "If f(a)f(c)>0 in bisection, which endpoint changes?", "代码把 a=c 和 b=c 两端都执行了，括区间为何失效？", "二分中点恰好使函数为零时应如何结束？", "每一步怎么证明根仍被新的区间包住？", "我的二分区间更新后两端变成同号，可能是哪类分支错误？", "How do I preserve the bracket invariant in the update branch?", "请检查 if f(a)*f(c)<0: a=c 这段代码的逻辑。", "二分法中点函数值和左端符号相反时，为什么保留左半区间？"],
"CASE_BISECTION_ERROR_BOUND": ["初始区间宽度L，做n次二分后根的误差如何上界？", "要求根误差小于ε，如何推导二分最少迭代步数？", "How many bisections guarantee midpoint error below a tolerance?", "区间长度界与中点误差界相差因子2，怎么区分？", "为什么先验步数公式的对数结果要向上取整？", "二分迭代次数能否在不知道真根时预先估计？", "给定区间[2,5]，第k步的近似根误差最多多大？", "Derive the a priori bisection count from bracket width and tolerance.", "若要求误差小于δ，停机时区间宽度应控制在什么范围？", "误差估计公式里的初始长度是b-a还是半长？"],
"CASE_FIXED_POINT_CONTRACTION": ["不动点迭代的压缩映射充分条件有哪些？", "|g′|<1但g没有把区间映回自身，还能推出收敛吗？", "State a sufficient condition for convergence of fixed-point iteration.", "闭区间自映射和Lipschitz常数小于1共同保证什么？", "为什么压缩映射的不动点是唯一的？", "局部导数绝对值小于1能否说明整个区间都收敛？", "g(x)=cos(x)如何借助压缩条件分析迭代？", "Does a contraction guarantee convergence from every point in the interval?", "导数上界为0.7但像集超出区间，定理缺少哪一项？", "压缩映射定理是必要条件还是充分条件？"],
"CASE_FIXED_POINT_DIVERGENCE": ["同一个方程换成另一种x=g(x)形式后，迭代为什么发散？", "若|g′(x*)|>1，局部误差会怎样变化？", "Fixed-point iteration oscillates with an expanding amplitude; diagnose it.", "初值远离解且局部收缩，为什么依然不能保证这次迭代收敛？", "迭代序列交替且振幅增大，是何种稳定性信号？", "不动点格式发散时，重新构造g有什么依据？", "|g′|=1时压缩映射判据能下结论吗？", "g把迭代点推出计算区间，哪项假设失效？", "How can an algebraically equivalent rearrangement change convergence?", "区分不动点迭代收敛慢与真正发散。"],
"CASE_NEWTON_DERIVATION": ["从切线与x轴交点推导牛顿更新公式。", "一阶Taylor展开如何得到x_next=x-f(x)/f′(x)？", "Derive Newton-Raphson from the tangent at the current iterate.", "牛顿法几何解释中，切线交点为什么是下一近似？", "令一阶Taylor多项式等于零，整理后得到哪个迭代式？", "Why does the Newton update subtract f divided by f prime?", "牛顿迭代步Δx=-f/f′的符号怎么确定？", "从切线方程求横轴交点，推导中用了什么局部近似？", "牛顿法与割线法推导所需的信息有什么差别？", "Explain the linearization behind a Newton step."],
"CASE_NEWTON_LOCAL_CONVERGENCE": ["牛顿法局部二阶收敛需要根满足什么条件？", "单根、二阶连续可微和初值充分接近各自起什么作用？", "State the assumptions for quadratic Newton convergence near a simple root.", "局部收敛定理能否保证任意初值都收敛？", "重根时标准牛顿法的二阶收敛结论为何失效？", "初值在收敛邻域外，局部定理能预测轨迹吗？", "How should local convergence be distinguished from global convergence?", "初值邻域半径未知时，“充分接近”该如何理解？", "远处初值导致发散，是否和局部收敛定理矛盾？", "牛顿法二阶收敛证明对函数光滑性有什么要求？"],
"CASE_NEWTON_INITIAL_VALUE": ["牛顿法从远处初值出发跳到另一个根，如何排查？", "初值不当引起周期振荡，应检查迭代轨迹的哪些特征？", "Newton converges to an unintended root from a different starting guess; explain.", "局部二阶收敛很快，为什么牛顿法仍可能失败？", "初值落在切线斜率很小的地方后数值爆炸，是哪个风险？", "改变初始猜测后结果大幅改变，反映了什么收敛边界？", "迭代在两个点间循环属于哪种初值敏感性表现？", "为什么不能说牛顿法总会找到最近的根？", "怎样用二分法给Newton初值提供保护？", "The initial value may lie outside the convergence basin; what can happen?"],
"CASE_NEWTON_DERIVATIVE_ZERO": ["当前迭代点f′(x_k)=0，牛顿公式为什么无法更新？", "导数很小但非零时，Newton步长会有什么风险？", "Newton code divides by a near-zero derivative; identify the direct failure.", "迭代点处切线水平，标准更新式发生了什么？", "区分重根造成根处导数为零与某步偶然导数为零。", "程序报ZeroDivisionError，首先应检查哪个计算值？", "如何在牛顿代码中加入导数阈值保护？", "导数估计因下溢为0时应怎样处理？", "没有函数和导数值，能确定报错一定由零导数造成吗？", "A tiny derivative produces an enormous Newton step; why?"],
"CASE_NEWTON_MULTIPLE_ROOT": ["m重根处标准Newton迭代渐近收敛阶是多少？", "对(x-1)^2使用牛顿法为何只有线性收敛？", "Derive the error factor 1-1/m for a root of multiplicity m.", "带重数m的修正Newton公式为何能恢复二阶收敛？", "f(x*)=f′(x*)=0时还能使用单根二阶定理吗？", "重根降阶和中间迭代点分母为零是同一个问题吗？", "二重根误差每步约减半，说明收敛阶是多少？", "不知道重数时能直接套用修正Newton格式吗？", "Why does multiplicity reduce Newton's order?", "重根使牛顿法变慢是否等同于发散？"],
"CASE_NEWTON_CONVERGENCE_ORDER": ["如何从连续误差值估计数值迭代的收敛阶p？", "用误差表检验牛顿法是否进入二阶收敛阶段。", "Estimate p from three successive errors.", "真根未知时，能否用真实误差直接验证收敛阶？", "双对数拟合的斜率怎样解释为收敛阶？", "收敛早期估得p不接近2，可能尚未进入渐近区吗？", "误差接近浮点精度时阶数估计为何不稳定？", "怎样从误差比区分线性收敛与二次收敛？", "Newton order estimation from a computed error table?", "只有残差序列时能可靠算真实误差的收敛阶吗？"],
"CASE_RESIDUAL_VS_ERROR": ["残差很小是否足以证明近似根的真实误差很小？", "平坦函数处残差小但离真根远，如何理解？", "Does a tiny residual imply small forward error for an ill-conditioned root?", "定义残差和真实误差，并说明二者为何不等同。", "|f′|很小时，从残差估计误差会有什么困难？", "只用残差停机可能产生什么误判？", "真根未知时为何不能将残差直接当作误差？", "函数斜率不同，相同残差对应的误差是否相同？", "A residual of 1e-10 is reported; can accuracy be certified from that alone?", "区分后向误差和求根问题的前向误差。"],
"CASE_STOPPING_CRITERION": ["为什么求根停机应兼看步长、残差和最大步数？", "只用相邻迭代步长很小作为成功标准有什么风险？", "Design a stopping rule using residual, step size, and an iteration cap.", "步长已小但残差仍大，是否应报告收敛？", "达到最大迭代次数但容差未满足时应返回什么状态？", "相对步长和绝对步长分别适合什么情况？", "停机判据中的残差和步长条件如何组合？", "循环保护应怎样避免求根代码无限运行？", "Why is an iteration cap needed in addition to a residual test?", "浮点下步长为零能否单独说明找到了根？"],
"CASE_NEWTON_CODE_UPDATE": ["写一个带导数接近零保护的Newton单步更新函数。", "Python中计算牛顿步时怎样检查f′(x)再相除？", "Implement x_next=x-f(x)/df(x) with denominator validation.", "牛顿代码把更新写成x+f/df，错误在哪里？", "调用f和df函数时Newton更新核心逻辑是什么？", "导数非零时如何记录本次更新量Δx？", "Give a robust Newton update with a near-zero derivative guard.", "怎样区分分母异常与达到最大迭代次数？", "Newton function should validate the derivative before division; explain.", "实现牛顿更新应使用当前迭代点的函数值还是旧值？"],
"CASE_NEWTON_CODE_STOPPING": ["Newton循环达到max_iter仍未满足容差，应怎样返回？", "给牛顿代码加上迭代上限和明确的未收敛错误。", "Add a loop guard and explicit non-convergence outcome to Newton code.", "停机条件放在更新前后会影响检查哪个残差？", "只检查步长就break而不检查残差有什么风险？", "用k<max_iter怎样防止Newton循环无限运行？", "如何同时记录每步残差、步长并安全终止？", "Should exhausting the iteration cap be reported as convergence?", "Newton应在何时抛出异常表示未收敛？", "循环上限为零时应该如何处理输入边界？"]}

rows=[]
for family, queries in FAMILIES.items():
    for query in queries:
        rows.append({"id":f"V2-{len(rows)+1:03d}","query":query,"gold_reason":f"问题的目标/条件直接对应{family}所描述的课程Case；金标准按教材数学条件和该Case语义确定。","family":family,"split":"in_domain","expected_case_id":[family],"expected_decision":["SAME_CASE","VARIANT_OF_CASE","RELATED_CASE"],"context":{},"ontology_limit":None})

extras=[
 ("Newton does not converge.","CASE_NEWTON_INITIAL_VALUE","insufficient_information","可定位Newton失败/初值排查入口，但没有函数、初值和轨迹，无法确定具体根因。",{}),
 ("残差为1e-9，真根和导数界均未知，能保证误差小于1e-6吗？","CASE_RESIDUAL_VS_ERROR","insufficient_information","可定位残差与真实误差辨析；现有信息不能推出误差上界。",{}),
 ("二分程序结果不对，但没提供代码或端点值。","CASE_BISECTION_BRACKET_UPDATE","insufficient_information","能定位区间更新排查，缺少代码和符号数据，不能确定哪一分支错。",{}),
 ("迭代发散，函数、初值和g(x)都没有。","CASE_FIXED_POINT_DIVERGENCE","insufficient_information","可定位不动点发散诊断，不能判断映射区间或导数条件哪项失效。",{}),
 ("我还没算当前导数，程序报错能确定是除零吗？","CASE_NEWTON_DERIVATIVE_ZERO","insufficient_information","可定位分母异常检查，但缺少导数证据，不能确认根因。",{}),
 ("迭代变慢了，但没有重数或误差表。","CASE_NEWTON_MULTIPLE_ROOT","insufficient_information","可定位重根降阶假设检查，但不能据此认定是重根。",{}),
 ("Please diagnose the previous Newton run using our earlier chat.","CASE_NEWTON_INITIAL_VALUE","insufficient_information","benchmark不含历史对话；仅可泛化定位Newton诊断，不能声称用到了上下文。",{}),
 ("当前是代码调试任务，请检查二分中点同号时端点更新。","CASE_BISECTION_BRACKET_UPDATE","context_task","明确任务上下文为代码调试，目标是二分端点分支。",{"task_mode":"error_debugging"}),
 ("Task mode is code_task; add a maximum-iteration guard to Newton.","CASE_NEWTON_CODE_STOPPING","context_task","任务模式与目标都指向Newton代码停机。",{"task_mode":"code_task"}),
 ("先解释Newton公式，再给带导数保护的Python实现。","CASE_NEWTON_CODE_UPDATE","mixed_intent","推导与代码两个目标并存；单标签按可执行代码更新目标归类，本体不能拆分多意图。",{}),
 ("解释重根降阶，并写出已知m时的修正公式。","CASE_NEWTON_MULTIPLE_ROOT","mixed_intent","解释和格式设计聚焦同一重根Case。",{}),
 ("请推导Newton并证明它对任意初值全局二阶收敛。","CASE_NEWTON_LOCAL_CONVERGENCE","mixed_intent","Newton收敛条件为主目标；gold理由须纠正全局、任意初值的错误命题。",{}),
 ("求抛物型PDE的有限元稳定性条件。",None,"out_of_domain","PDE有限元不属于当前求根课程Case本体。",{}),
 ("求矩阵特征值QR迭代的收敛速度。",None,"out_of_domain","特征值算法在当前冻结的15个root-finding Case之外。",{}),
 ("Explain the residue theorem for contour integration.",None,"out_of_domain","复分析围道积分不属于数值求根主题。",{}),
 ("强化学习PPO的clip目标函数是什么？",None,"out_of_domain","强化学习主题在当前课程Case本体之外。",{}),
 ("单根、初值充分接近时Newton局部二阶收敛条件是什么？","CASE_NEWTON_LOCAL_CONVERGENCE","near_neighbor","明确单根和局部邻域，区别于重根降阶Case。",{}),
 ("二重根处导数为零，和中间迭代点偶然导数为零有何不同？","CASE_NEWTON_MULTIPLE_ROOT","near_neighbor","提问重根渐近阶；不是单步除零故障。",{}),
 ("根是单根，但本次迭代点f′恰为零。","CASE_NEWTON_DERIVATIVE_ZERO","near_neighbor","当前点分母失效，与根本身重数不同。",{}),
 ("端点异号但函数不连续，零点存在结论成立吗？","CASE_BISECTION_REQUIREMENTS","near_neighbor","条件缺失问题归到二分适用条件，而非单纯端点更新。",{}),
 ("区间长度4，要求误差小于1e-5，二分要几步？","CASE_BISECTION_ERROR_BOUND","near_neighbor","目标是误差界和迭代数，不是分支更新。",{}),
 ("步长小但残差仍大，可以宣布停止吗？","CASE_STOPPING_CRITERION","near_neighbor","联合停机判据不能只看步长。",{}),
 ("|g′|=0.3但g不映回区间，压缩定理条件齐全吗？","CASE_FIXED_POINT_CONTRACTION","near_neighbor","导数收缩不替代区间自映射条件。",{}),
 ("牛顿残差极小但函数很平，能认证前向误差吗？","CASE_RESIDUAL_VS_ERROR","near_neighbor","残差与前向误差受斜率和病态性影响。",{}),
 ("循环没停但Newton更新正确，最需要补什么保护？","CASE_NEWTON_CODE_STOPPING","near_neighbor","聚焦循环停机和上限，而非更新公式。",{}),
 ("只说‘数值分析作业有问题’，能确定是哪种Newton错误吗？","CASE_NEWTON_INITIAL_VALUE","uncertainty","泛化求根诊断入口仅暂定映射；无法确定具体算法或根因，ontology缺少信息需求状态。",{}),
 ("Tell me the exact Newton bug; there is no code or output.","CASE_NEWTON_INITIAL_VALUE","uncertainty","可识别Newton诊断主题，但缺少证据，不能确认具体bug；需教师复核本体表达边界。",{}),
 ("请结合我刚上传的历史记录判断根的重数。","CASE_NEWTON_MULTIPLE_ROOT","uncertainty","没有历史附件输入，不能假装上下文已用；提到重数不构成重根证据。",{}),
 ("讲解所有迭代算法并给出完整运行程序。","CASE_STOPPING_CRITERION","uncertainty","范围过宽且混合意图，暂定停机为路由标签，单标签本体无法表达分解。",{}),
 ("How do I stop Newton and estimate its order from the same run?","CASE_STOPPING_CRITERION","mixed_intent","停机与收敛阶是不同目标，单标签按循环退出主目标归类。",{}),
 ("残差和误差区别是什么？另外只给我Python停机代码。","CASE_STOPPING_CRITERION","mixed_intent","概念辨析兼代码请求，以代码停机目标作为主要可执行意图。",{}),
]
for q,cid,split,reason,context in extras:
    rows.append({"id":f"V2-{len(rows)+1:03d}","query":q,"gold_reason":reason,"family":cid or "OUT_OF_DOMAIN","split":split,"expected_case_id":[cid] if cid else [None],"expected_decision":["NEW_CASE","UNCERTAIN"] if cid is None else (["UNCERTAIN","SAME_CASE","VARIANT_OF_CASE","RELATED_CASE"] if split in ("uncertainty","insufficient_information") else ["SAME_CASE","VARIANT_OF_CASE","RELATED_CASE"]),"context":context,"ontology_limit":"single-label ontology lacks explicit evidence-sufficiency or multi-intent representation" if split in ("uncertainty","insufficient_information","mixed_intent") else None})

more=[
 ("端点异号且函数连续，介值定理能保证根的唯一性吗？","CASE_BISECTION_REQUIREMENTS","in_domain","连续性和异号只保证至少一个根，不保证唯一。"),
 ("二分区间长度已足够小，但我更新错了端点，最终误差界还可信吗？","CASE_BISECTION_BRACKET_UPDATE","in_domain","端点更新错误会破坏有效括根，误差界依赖括区间不变式。"),
 ("二分停止时返回区间中点，绝对误差为何不超过区间半长？","CASE_BISECTION_ERROR_BOUND","in_domain","中点最坏误差由包含真根的最终区间半长控制。"),
 ("g在区间上Lipschitz常数恰等于1，压缩映射定理能保证唯一解吗？","CASE_FIXED_POINT_CONTRACTION","in_domain","严格小于1的压缩条件不满足。"),
 ("不动点迭代数值有界但不趋于单点，是否可据此称收敛？","CASE_FIXED_POINT_DIVERGENCE","in_domain","有界序列不必收敛，需分析迭代映射与轨迹。"),
 ("由Taylor余项推导Newton公式时忽略二阶项，近似发生在哪一步？","CASE_NEWTON_DERIVATION","in_domain","单步公式来自当前点的一阶线性化。"),
 ("f二阶连续且x*为单根，但初值距离根多远才能用定理？","CASE_NEWTON_LOCAL_CONVERGENCE","insufficient_information","可定位局部定理条件，未给函数/邻域不能给出具体数值半径。"),
 ("Newton迭代初值不变却每次结果不同，是否还需要检查随机性或并发？","CASE_NEWTON_INITIAL_VALUE","insufficient_information","可定位初值与运行轨迹诊断，但证据不足以断定初值是唯一根因。"),
 ("f′非常小但程序没报除零，应该把它按零处理吗？","CASE_NEWTON_DERIVATIVE_ZERO","near_neighbor","数值阈值保护关注近零分母，不限于精确零。"),
 ("已知三重根，标准Newton误差约按什么比例线性缩小？","CASE_NEWTON_MULTIPLE_ROOT","in_domain","重数m=3时渐近线性因子为1-1/m。"),
 ("误差比公式算出p为负数，先检查收敛阶还是数据假设？","CASE_NEWTON_CONVERGENCE_ORDER","near_neighbor","估阶公式依赖误差趋零及有效渐近数据，负值可能表示数据/索引问题。"),
 ("函数值量纲和根误差量纲不同，残差阈值能直接当精度阈值吗？","CASE_RESIDUAL_VS_ERROR","near_neighbor","残差和根的前向误差含义与尺度不同。"),
 ("停止条件把小步长当成功，即使迭代因舍入停滞也会误判吗？","CASE_STOPPING_CRITERION","near_neighbor","步长小可能是停滞，应结合残差/状态判断。"),
 ("Newton更新公式正确，但没有检查df接近浮点零，补在哪里？","CASE_NEWTON_CODE_UPDATE","near_neighbor","实现更新步骤时需先检查分母，再进行除法。"),
 ("请在每轮打印Newton步数，超限后返回未收敛状态。","CASE_NEWTON_CODE_STOPPING","context_task","代码任务目标明确是循环计数和超限状态。"),
 ("A discontinuous function changes sign across the bracket; is a root guaranteed?","CASE_BISECTION_REQUIREMENTS","in_domain","端点异号但连续性缺失，考查二分适用条件；这属于根求解范围内。"),
 ("请讲椭圆曲线上的数论算法。",None,"out_of_domain","数论主题不属于数值分析求根课程包。"),
 ("历史记录显示的初值是多少？", "CASE_NEWTON_INITIAL_VALUE","uncertainty","样例无历史记录，不能声称知道具体初值；仅能定位初值主题。"),
 ("Context says task_mode=code_task: fix Newton's missing derivative guard.","CASE_NEWTON_CODE_UPDATE","context_task","明确代码任务，故障目标是更新过程的分母保护。"),
 ("先给二分误差推导，再解释端点更新。","CASE_BISECTION_ERROR_BOUND","mixed_intent","误差推导和更新规则是双目标，以明确的误差推导为主标签；本体不能拆分。"),
 ("Newton has a double root and a zero derivative at the current iterate; discuss both order and runtime failure.","CASE_NEWTON_MULTIPLE_ROOT","mixed_intent","重根降阶与运行时分母失败为两项不同目标，按重根收敛阶主目标单标签标注。",)
]
for entry in more:
    q,cid,split,reason=entry[:4]
    rows.append({"id":f"V2-{len(rows)+1:03d}","query":q,"gold_reason":reason,"family":cid or "OUT_OF_DOMAIN","split":split,"expected_case_id":[cid] if cid else [None],"expected_decision":["NEW_CASE","UNCERTAIN"] if cid is None else (["UNCERTAIN","SAME_CASE","VARIANT_OF_CASE","RELATED_CASE"] if split=="uncertainty" else ["SAME_CASE","VARIANT_OF_CASE","RELATED_CASE"]),"context":{"task_mode":"code_task"} if split=="context_task" else {},"ontology_limit":"single-label ontology lacks explicit evidence-sufficiency or multi-intent representation" if split in ("uncertainty","insufficient_information","mixed_intent") else None})

# Precise, item-specific rationales: state the requested goal, key mathematical
# predicate, and nearest misleading Case excluded by that predicate.
semantics = {
"CASE_BISECTION_REQUIREMENTS": ("二分法可用性", "函数在闭区间连续且端点异号；只变号不能替代连续性", "CASE_BISECTION_BRACKET_UPDATE，因为问题问定理前提，不是某一步更新"),
"CASE_BISECTION_BRACKET_UPDATE": ("保留含根子区间", "比较端点与中点符号并保持端点异号不变式", "CASE_BISECTION_REQUIREMENTS，因为问题聚焦迭代分支而非初始适用条件"),
"CASE_BISECTION_ERROR_BOUND": ("先验误差/步数界", "区间宽度每轮减半，中点误差至多半个当前区间", "CASE_BISECTION_BRACKET_UPDATE，因为问题目标是精度估计而非更新方向"),
"CASE_FIXED_POINT_CONTRACTION": ("不动点收敛充分条件", "闭区间自映射并且sup|g'|<1", "CASE_FIXED_POINT_DIVERGENCE，因为询问的是定理正条件而非失稳现象"),
"CASE_FIXED_POINT_DIVERGENCE": ("不动点格式稳定性/失败", "分析|g'|、自映射和初值，不能从等价代数变形推出同样收敛", "CASE_FIXED_POINT_CONTRACTION，因为问句描述失败而非满足条件时的定理结论"),
"CASE_NEWTON_DERIVATION": ("推导单步更新", "在当前点作一阶线性化并令近似函数值为零", "CASE_NEWTON_CODE_UPDATE，因为目标是公式来源，不是程序防护"),
"CASE_NEWTON_LOCAL_CONVERGENCE": ("局部二阶收敛的适用条件", "单根f'(x*)!=0、足够光滑、初值在充分小邻域", "CASE_NEWTON_MULTIPLE_ROOT，因为单根定理不覆盖重根"),
"CASE_NEWTON_INITIAL_VALUE": ("初值与全局失败诊断", "Newton结论是局部的；需迭代轨迹和初值证据才能归因", "CASE_NEWTON_DERIVATIVE_ZERO，因为未给出当前分母为零的证据"),
"CASE_NEWTON_DERIVATIVE_ZERO": ("单步分母失效", "检查当前迭代点|f'(x_k)|是否为零或相对尺度上过小", "CASE_NEWTON_MULTIPLE_ROOT，因为中间点分母故障不等价于根具有重数"),
"CASE_NEWTON_MULTIPLE_ROOT": ("重根下Newton阶数/修正", "m重根标准Newton渐近因子1-1/m；只有问收敛阶/乘子修正时才用此标签", "CASE_NEWTON_DERIVATIVE_ZERO，因为若只问当前点无法除法则应归分母故障"),
"CASE_NEWTON_CONVERGENCE_ORDER": ("由误差序列估渐近阶", "需有效、趋零的连续误差数据；舍入/非渐近阶段会误导", "CASE_NEWTON_LOCAL_CONVERGENCE，因为问题问观测阶估计而非定理条件"),
"CASE_RESIDUAL_VS_ERROR": ("区分残差和根的真实误差", "r=f(x_k)，e=x_k-x*；斜率/条件性决定二者不能直接等同", "CASE_STOPPING_CRITERION，因为问题若只问阈值组合才属于停机设计"),
"CASE_STOPPING_CRITERION": ("设计安全停机判据", "联合检查残差、步长并用max_iter兜底；小步长不等价于找到根", "CASE_RESIDUAL_VS_ERROR，因为目标是迭代退出逻辑而非术语辨析"),
"CASE_NEWTON_CODE_UPDATE": ("实现Newton单步", "先评估并保护当前df，再计算x-f/df", "CASE_NEWTON_CODE_STOPPING，因为问题聚焦单步更新，不是循环退出"),
"CASE_NEWTON_CODE_STOPPING": ("控制Newton循环终止", "容差判据之外必须有迭代上限和未收敛状态", "CASE_NEWTON_CODE_UPDATE，因为问题聚焦循环退出而非分母计算")
}
for row in rows:
    family = row["family"]
    if family in semantics and row["split"] == "in_domain":
        goal, predicate, exclude = semantics[family]
        row["gold_reason"] = f"本题问“{row['query']}”；主要目标是{goal}。必要判据：{predicate}。排除近邻Case {exclude}。此标签依据教材条件和问题目标确定，不代表matcher已证明学生根因。"
        row["expected_decision"] = ["SAME_CASE"]
    elif row["split"] == "near_neighbor":
        row["expected_decision"] = ["VARIANT_OF_CASE"]
        goal, predicate, exclude = semantics[family]
        row["gold_reason"] = f"本题问“{row['query']}”；目标为{goal}。关键判据：{predicate}。相对常规Case条件，本题明确对照了题干中的条件变化，因此是VARIANT_OF_CASE；排除近邻{exclude}，不能推断未给出的根因。"
    elif row["split"] in ("insufficient_information", "context_task"):
        row["expected_decision"] = ["SAME_CASE"]
        row["gold_reason"] += " 可按明确算法/任务定位Case；缺少函数、轨迹或代码时不应声称已确定故障原因。"

# Remove unjustified routing guesses and represent two explicit mixed goals as
# acceptable Case sets rather than choosing one based on convenience.
for row in rows:
    if row["query"].startswith("只说‘数值分析作业") or row["query"].startswith("讲解所有迭代算法"):
        row.update({"family":"UNROUTABLE_INSUFFICIENT","expected_case_id":[None],"expected_decision":["UNCERTAIN"],"split":"unroutable","gold_reason":"问句没有指出算法、错误现象或目标；不支持选择任何现有Case，应显式返回UNCERTAIN并请求具体题目/轨迹，而非臆定Newton或停机主题。","ontology_limit":"gold uses UNCERTAIN as proxy for insufficient routing evidence; matcher API has no explicit ask-for-evidence decision"})
    if row["query"].startswith("残差和误差区别是什么？另外"):
        row.update({"family":"MIXED_RESIDUAL_AND_STOPPING","expected_case_id":["CASE_RESIDUAL_VS_ERROR","CASE_STOPPING_CRITERION"],"expected_decision":["UNCERTAIN","RELATED_CASE"],"gold_reason":"问句并列要求术语辨析与Python停机代码；前者映射残差/误差，后者映射停机准则。单标签无法选出唯一Case，因此接受集合并标出多意图限制。","ontology_limit":"one request has two independent intents; evaluation accepts either related route or uncertainty"})
    if "二重根处导数为零，和中间迭代点偶然导数为零" in row["query"]:
        row.update({"family":"MIXED_MULTIPLE_ROOT_AND_DERIVATIVE","expected_case_id":["CASE_NEWTON_MULTIPLE_ROOT","CASE_NEWTON_DERIVATIVE_ZERO"],"expected_decision":["UNCERTAIN","RELATED_CASE"],"gold_reason":"问句明确比较根的重数性质和某一步分母失效，是两个相关但不同对象；多重根影响渐近阶，当前点导数为零导致单步无法相除，使用集合而非单一预设标签。","ontology_limit":"comparative query spans two Cases; a single selected Case loses one requested distinction"})

# Add literal code fragments as inert query text. The evaluator only passes
# strings to the matcher; no code in benchmark rows is ever executed.
code_queries = [
 ("def newton(f, df, x):\n    return x + f(x) / df(x)\n\n这段更新的符号哪里错？","CASE_NEWTON_CODE_UPDATE","SAME_CASE","代码片段把Newton减号写成加号；目标是单步更新公式。"),
 ("if df(x) == 0: pass\nx = x - f(x) / df(x)\n这段零导数保护为什么没有效果？","CASE_NEWTON_CODE_UPDATE","SAME_CASE","保护分支没有退出/阻止后续除法，问题在更新代码防除零。"),
 ("while abs(f(x)) > tol:\n    x = x - f(x)/df(x)\n循环可能无限运行，缺什么？","CASE_NEWTON_CODE_STOPPING","SAME_CASE","循环只有残差条件，缺最大迭代数和未收敛出口。"),
 ("if abs(x_new-x) < tol: return x_new\n残差很大也返回成功，判据哪里不足？","CASE_STOPPING_CRITERION","SAME_CASE","小步长不能单独认证根，停机应检查残差并定义状态。"),
 ("if f(a)*f(c) < 0:\n    a = c\n二分法这段端点赋值对吗？","CASE_BISECTION_BRACKET_UPDATE","SAME_CASE","中点与左端异号时应保留[a,c]，赋a=c会丢掉变号区间。"),
 ("if f(a)*f(c) > 0:\n    b = c\n判断这一支保留的区间是否正确。","CASE_BISECTION_BRACKET_UPDATE","SAME_CASE","若a与中点同号则根在[c,b]，应更新a而非b。"),
 ("for k in range(max_iter):\n    x = x - f(x)/df(x)\n若跑满循环，函数应怎样报告？","CASE_NEWTON_CODE_STOPPING","SAME_CASE","代码已有上限，缺少耗尽上限后的显式未收敛状态。"),
 ("x = x - f(x)/df(x)\n没有检查df接近0，加入检查应放在哪里？","CASE_NEWTON_CODE_UPDATE","SAME_CASE","分母检查必须先于除法，目标是更新实现防护。"),
 ("while abs(dx)>tol:\n    ...\n没有max_iter时有什么失效风险？","CASE_NEWTON_CODE_STOPPING","SAME_CASE","循环可能永不终止，目标是循环上限设计。"),
 ("if abs(f(x)) < tol: break\n是否还应限制迭代次数？","CASE_STOPPING_CRITERION","SAME_CASE","只按残差break而无安全上限不能防止条件永不满足。"),
 ("c=(a+b)/2\nif f(a)*f(c)<0: b=c\n说明区间不变式如何维持。","CASE_BISECTION_BRACKET_UPDATE","SAME_CASE","该分支保留左侧异号区间[a,c]，目标是验证端点更新。"),
 ("dfx = derivative(x)\nstep = fx / dfx\nx -= step\n哪里应处理浮点近零？","CASE_NEWTON_CODE_UPDATE","SAME_CASE","需在除法前检查dfx是否相对尺度上近零。"),
 ("while k < max_iter:\n    ...\nelse: raise RuntimeError('not converged')\n这个else代表什么状态？","CASE_NEWTON_CODE_STOPPING","SAME_CASE","循环耗尽后的else应报告未收敛，目标是终止状态语义。")
]
for q,cid,decision,reason in code_queries:
    rows.append({"id":f"V2-{len(rows)+1:03d}","query":q,"gold_reason":reason+" 代码只作为静态文本匹配输入，不会执行。","family":cid,"split":"code_snippet","expected_case_id":[cid],"expected_decision":[decision],"context":{},"ontology_limit":None})

extra_topics = [
 ("如何用Romberg积分提高复合梯形公式精度？","out_of_domain","数值积分，不是当前求根课程范围。"),
 ("QR算法计算矩阵特征值的移位策略怎么选？","out_of_domain","矩阵特征值属于其他数值分析专题，不在此Case包。"),
 ("有限元求二维Poisson方程如何处理边界条件？","out_of_domain","偏微分方程有限元不属于求根范围。"),
 ("复变函数留数定理怎样计算围道积分？","out_of_domain","复分析积分不属于当前课程包。"),
 ("用梯度下降训练神经网络时学习率如何调整？","out_of_domain","机器学习优化不属于非线性方程求根。"),
 ("有限差分解热方程时如何做稳定性分析？","out_of_domain","PDE时间推进稳定性不是此求根Case集的主题。"),
 ("请推导弦截法并诊断割线斜率为零的情形。","new_case","弦截法是求根主题内需求，但当前15个Case没有其独立算法/退化斜率诊断。"),
 ("False position法端点长期不动时如何加速？","new_case","假位法属于求根，但当前Case本体没有端点停滞及加速专题。"),
 ("Brent方法怎样在二分与插值间切换？","new_case","Brent混合算法的切换规则不在现有二分/Newton/fixed-point Case内。"),
 ("给Newton加阻尼因子并选择线搜索步长。","new_case","阻尼Newton和线搜索控制是域内新算法需求，当前Case未覆盖。"),
 ("怎样隔离多项式的全部实根并证明没有遗漏？","new_case","多项式全根隔离不同于单根Newton收敛或二分单区间误差界。"),
 ("复平面上的Newton迭代盆地边界如何可视化？","new_case","复根与复平面吸引域超出现有实数求根Case。"),
 ("求解F(x,y)=0的非线性方程组Newton雅可比更新。","new_case","多变量Newton需要Jacobian和方程组Case，当前本体是一元求根。"),
]
for q,split,reason in extra_topics:
    rows.append({"id":f"V2-{len(rows)+1:03d}","query":q,"gold_reason":reason,"family":"OUT_OF_DOMAIN" if split=="out_of_domain" else "NEW_CASE_REQUIRED","split":split,"expected_case_id":[None],"expected_decision":["NEW_CASE"],"context":{},"ontology_limit":"new_case is in course domain but absent from the frozen Case ontology" if split=="new_case" else None})

# Promote 11 explicit implementation-oriented existing examples to carry task
# context, bringing the full benchmark context coverage to at least 15.
context_candidates = [r for r in rows if r["family"] in ("CASE_NEWTON_CODE_UPDATE","CASE_NEWTON_CODE_STOPPING") and r["split"] == "in_domain"]
for row in context_candidates[:11]:
    row["split"] = "context_task"
    row["context"] = {"task_mode":"code_task"}
    row["gold_reason"] += " The explicit task_mode=code_task context is supplied to match(); it does not add unsupplied dialogue history."

# Multi-intent examples preserve each requested route; no arbitrary primary goal.
for row in rows:
    q = row["query"]
    if q.startswith("先解释Newton公式"):
        row.update({"family":"MIXED_NEWTON_DERIVATION_CODE","expected_case_id":["CASE_NEWTON_DERIVATION","CASE_NEWTON_CODE_UPDATE"],"expected_decision":["UNCERTAIN","RELATED_CASE"],"gold_reason":"请求同时包含Newton公式推导和带导数保护的Python实现，分别对应推导与代码更新两个Case；接受集合保留两项目标，单标签评测不计严格决策。","ontology_limit":"two independent intents map to separate Cases"})
    elif q.startswith("请推导Newton并证明"):
        row.update({"split":"near_neighbor","expected_decision":["VARIANT_OF_CASE"],"gold_reason":"核心问题是Newton局部收敛条件，但“任意初值全局二阶”是错误加强；标为条件变化的VARIANT，答案必须指出单根、光滑性和局部初值前提。"})
    elif q.startswith("先给二分误差推导"):
        row.update({"family":"MIXED_BISECTION_BOUND_UPDATE","expected_case_id":["CASE_BISECTION_ERROR_BOUND","CASE_BISECTION_BRACKET_UPDATE"],"expected_decision":["UNCERTAIN","RELATED_CASE"],"gold_reason":"同时要误差上界推导和端点更新解释，对应两个独立Case；以可接受集合记录，不臆定主意图。","ontology_limit":"two independent intents map to separate Cases"})
    elif q.startswith("How do I stop Newton and estimate"):
        row.update({"family":"MIXED_NEWTON_STOP_ORDER","expected_case_id":["CASE_STOPPING_CRITERION","CASE_NEWTON_CONVERGENCE_ORDER"],"expected_decision":["UNCERTAIN","RELATED_CASE"],"gold_reason":"同一运行中的停机设计与收敛阶估计是两个目标，分别对应两个Case；需多意图本体才能严格单标签评估。","ontology_limit":"two independent intents map to separate Cases"})
    elif q.startswith("残差和误差区别是什么"):
        row.update({"family":"MIXED_RESIDUAL_AND_STOPPING","expected_case_id":["CASE_RESIDUAL_VS_ERROR","CASE_STOPPING_CRITERION"],"expected_decision":["UNCERTAIN","RELATED_CASE"],"gold_reason":"前半问残差/真实误差概念，后半要求Python停机代码；两者分别映射残差辨析和停机准则。","ontology_limit":"two independent intents map to separate Cases"})
    elif q.startswith("解释重根降阶"):
        row.update({"expected_decision":["SAME_CASE"],"gold_reason":"问题聚焦重根下标准Newton降阶及已知重数时的修正格式，两部分属于同一个Case的解释和方法目标。"})
    elif "二重根处导数为零，和中间迭代点偶然导数为零" in q or "double root and a zero derivative" in q:
        row.update({"family":"MIXED_MULTIPLE_ROOT_AND_DERIVATIVE","split":"mixed_intent","expected_case_id":["CASE_NEWTON_MULTIPLE_ROOT","CASE_NEWTON_DERIVATIVE_ZERO"],"expected_decision":["UNCERTAIN","RELATED_CASE"],"gold_reason":"问句比较根的重数性质和某一步分母失效：前者影响渐近阶，后者导致单步除法失败，是两个不同目标，故保留双Case集合。","ontology_limit":"comparative query spans two Cases"})

for row in rows:
    # A near-neighbor split is a coverage category, not a decision label.
    # Research spec section 4.5 requires SAME_CASE when the target and
    # canonical premises are unchanged, even if a neighboring case is excluded.
    if row["query"] == "单根、初值充分接近时Newton局部二阶收敛条件是什么？":
        row["expected_decision"] = ["SAME_CASE"]
        row["gold_reason"] = "目标是Newton局部二阶收敛条件，单根与充分接近的初值正是该Case的原有前提；没有改变条件、表示或任务目标。依研究文档§4.5标SAME_CASE；排除重根降阶Case。仍须检查光滑性条件是否满足。"
    elif row["query"] == "根是单根，但本次迭代点f′恰为零。":
        row["expected_decision"] = ["SAME_CASE"]
        row["gold_reason"] = "目标是诊断当前迭代点分母为零，这正是导数失效Case的原有条件。根是单根只排除重根误归因，没有改变该Case的任务或分母前提；依研究文档§4.5标SAME_CASE。不能把当前点误当成已求得的根。"
    if row["split"] == "out_of_domain":
        row["expected_decision"] = ["NEW_CASE"]
    elif row["split"] == "uncertainty":
        row["expected_decision"] = ["UNCERTAIN"]
        row["gold_reason"] += " 有明确主题时仍可定位Case，但缺少材料不能确定事实或根因；决策gold仅为UNCERTAIN。"

if not 180 <= len(rows) <= 240: raise SystemExit(f"unexpected count: {len(rows)}")
if len({x['query'] for x in rows}) != len(rows): raise SystemExit("duplicate query")
Path(__file__).with_name("case_matching_benchmark_v2.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"wrote {len(rows)} unique rows")
