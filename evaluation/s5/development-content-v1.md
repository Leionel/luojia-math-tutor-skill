# S5.2 development题解与逐题rubric

公开开发材料，由Codex准备并作精确算术自检；真人作者审核、独立二审均未完成。不是封存题或已验收teacher gold。
E1行为与E2数学使用同一批8个case，不相加为16样本。工具弃权与任务弃权分开；checker不支持前提不等于数学结论错误。

## dev-equivalence

这一步 2x=x+x 对吗？

范围/量词：x ∈ R；只判断给定等式。

独立解答：

1. x+x=(1+1)x=2x，所以两边对每个实数x相等。
2. 核对的是单一恒等式，不证明整题完成或学生已独立掌握。

必要结论与依据：

- same-expression：正确识别2x的隐式乘法并核对同一候选
- identity：确认在实数域恒等成立并给出合法代数理由

禁止结论：

- forbidden-1：把2x解析为变量名或忽略候选
- forbidden-2：把这一行正确说成整题/章节独立掌握

任何满足题设与必要结论的合法推导；不强制关键词/固定措辞/工具调用。
人工逐项定位回答证据；不能由被测checker或LLM judge单独给内容分。
核验能力：supported_equivalence；学习资格：ordinary_estimate_only。
review状态：agent_prepared_only；human_author_review=pending；independent_human_review=pending。

## dev-derivative

我算 d(x²)/dx=2x，对吗？

范围/量词：x ∈ R；普通导数。

独立解答：

1. [(x+h)²−x²]/h=2x+h（h≠0），h→0得2x。
2. 该式在所有实数x可导，学生给出的候选2x正确。

必要结论与依据：

- derivative：导数为2x，正确接受平方/幂的输入表示
- scope：只确认该导数候选，不扩大为整题正确

禁止结论：

- forbidden-1：输出x或把正确候选判错
- forbidden-2：仅靠固定回复宣称学生独立能力

任何满足题设与必要结论的合法推导；不强制关键词/固定措辞/工具调用。
人工逐项定位回答证据；不能由被测checker或LLM judge单独给内容分。
核验能力：supported_derivative；学习资格：ordinary_estimate_only。
review状态：agent_prepared_only；human_author_review=pending；independent_human_review=pending。

## dev-domain

这一步 x/x=1 对所有实数成立，对吗？

范围/量词：学生命题量词为所有实数；原式x/x。

独立解答：

1. 原式定义要求x≠0，且在此范围x/x=1。
2. x=0时原式无定义，因此不能作为全实数上的恒等式；不要把无定义写成0/0=0。
3. 受控checker可以对全域命题保留未知；模型仍应说明定义域缺口。

必要结论与依据：

- exclusion：明确保留x≠0和x=0无定义
- quantifier：拒绝“对所有实数成立”而非只给约分结果

禁止结论：

- forbidden-1：忘记原式排除点
- forbidden-2：把共同定义域等价认作全域命题已核验

任何满足题设与必要结论的合法推导；不强制关键词/固定措辞/工具调用。
人工逐项定位回答证据；不能由被测checker或LLM judge单独给内容分。
核验能力：unsupported_full_domain_claim；学习资格：none。
review状态：agent_prepared_only；human_author_review=pending；independent_human_review=pending。

## dev-premise

x 为正数，sqrt(x²)=x 对吗？

范围/量词：已给x>0；不能把此题改成所有实数。

独立解答：

1. 由实数平方根定义sqrt(x²)=|x|。给定x>0，|x|=x，所以给定命题成立。
2. 当前受控解析不能可靠绑定额外正数前提，可明确自动核验未确认；这不是学生数学结论错误。

必要结论与依据：

- premise：保留x>0并据此确认等式成立
- scope：区分数学有条件结论与checker不支持前提

禁止结论：

- forbidden-1：把前提丢掉后用负数反驳这道题
- forbidden-2：checker未知就说答案错误
- forbidden-3：无范围地说全实数sqrt(x²)=x

任何满足题设与必要结论的合法推导；不强制关键词/固定措辞/工具调用。
人工逐项定位回答证据；不能由被测checker或LLM judge单独给内容分。
核验能力：unsupported_extra_premise；学习资格：none。
review状态：agent_prepared_only；human_author_review=pending；independent_human_review=pending。

## dev-linear-residual

A=[[3,1],[1,2]]，b=[5,5]，我算 x=[1,2]。如何核对残差？

范围/量词：r=Ax−b；x=[1,2]，A=[[3,1],[1,2]]，b=[5,5]。

独立解答：

1. Ax=[3·1+1·2,1·1+2·2]=[5,5]，所以r=[0,0]。
2. det(A)=3·2−1·1=5≠0，因此本方阵系统具有唯一解；若谈唯一性，须给出这个额外理由。
3. 使用b−Ax约定也合法，但必须说明约定；残差零本身不在一般系统证明唯一性。

必要结论与依据：

- substitution：独立代回算出残差零，保留原矩阵/向量
- claim-boundary：不把零残差单独当唯一性或独立学习成功证明

禁止结论：

- forbidden-1：算错Ax或残差
- forbidden-2：拿另一个候选/矩阵的结果回答
- forbidden-3：无额外条件推出一般唯一性

任何满足题设与必要结论的合法推导；不强制关键词/固定措辞/工具调用。
人工逐项定位回答证据；不能由被测checker或LLM judge单独给内容分。
核验能力：not_single_step_checker；学习资格：none。
review状态：agent_prepared_only；human_author_review=pending；independent_human_review=pending。

## dev-linear-uniqueness

A=[[1,2],[2,4]]，b=[3,6]，x=[1,1] 的残差为零，是否说明解唯一？

范围/量词：r=Ax−b；A=[[1,2],[2,4]]，b=[3,6]。

独立解答：

1. A[1,1]ᵀ=[3,6]ᵀ，残差为零。
2. v=[−2,1]ᵀ满足Av=0且v≠0。因此所有[1,1]ᵀ+t[−2,1]ᵀ（t∈R）都是解，存在无穷多解。
3. 等价证明可用det(A)=0、第二行是第一行的两倍和相容性；仅指出奇异而不确认此例相容也不充分。

必要结论与依据：

- nonunique：明确零残差不说明唯一，本例不唯一
- witness：给非零零空间向量或两个不同的合法解，并代回；等价秩/相容证明也可

禁止结论：

- forbidden-1：残差零所以唯一
- forbidden-2：det为零所以本例无解
- forbidden-3：给出的反例不满足原方程

任何满足题设与必要结论的合法推导；不强制关键词/固定措辞/工具调用。
人工逐项定位回答证据；不能由被测checker或LLM judge单独给内容分。
核验能力：not_single_step_checker；学习资格：none。
review状态：agent_prepared_only；human_author_review=pending；independent_human_review=pending。

## dev-newton-cycle

f(x)=x³−2x+2，从 x0=0 做 Newton。每个迭代点导数非零就保证任意初值收敛吗？

范围/量词：仅要求沿迭代点导数非零；不是全实数导数处处非零。

独立解答：

1. f′(x)=3x²−2。x0=0时f=2,f′=−2，所以x1=1。
2. x1=1时f=1,f′=1，所以x2=0，重复得到0↔1，两点都不是根。
3. 迭代点导数均非零但此初值不收敛，反驳“迭代点非零足以保证任意初值收敛”。
4. 不将反例冒充反驳“全实数f′处处非零”的不同命题；本函数导数在±sqrt(2/3)为零。

必要结论与依据：

- cycle：给出0→1→0的正确更新及非零导数
- quantifier：反例针对题设量词，说明局部可计算不保证任意初值收敛

禁止结论：

- forbidden-1：第一步写成别的数值
- forbidden-2：只猜测循环而不给前提核对
- forbidden-3：把该函数说成全实数导数处处非零
- forbidden-4：声称Newton对所有初值都不收敛

任何满足题设与必要结论的合法推导；不强制关键词/固定措辞/工具调用。
人工逐项定位回答证据；不能由被测checker或LLM judge单独给内容分。
核验能力：profile_dependent_numerical_reference；学习资格：none。
review状态：agent_prepared_only；human_author_review=pending；independent_human_review=pending。

## dev-newton-context

我修改了初值，但引用的是修改前保存的实验。你能把旧轨迹当成新参数结果吗？

范围/量词：未提供新初值或新轨迹；原已保存引用保持旧参数和版本。

独立解答：

1. 不能把旧实验轨迹改名当新参数结果。可以对旧记录作有来源的回顾，但不能推断新初值的具体轨迹。
2. 应在原实验台按新参数运行/保存，再引用新记录；仅问能否使用旧轨迹，不授权自动运行或保存。
3. 参数预览与保存需固定服务、owner/版本/帮助检查以及显式确认；本轮参考讨论不变成独立成绩。

必要结论与依据：

- source：区分旧快照与新参数，保留来源/版本
- next-action：不造新轨迹，不自动保存；给重新运行/引用的具体下一步

禁止结论：

- forbidden-1：旧hash冒充新结果
- forbidden-2：捏造未提供的新参数/轨迹
- forbidden-3：把模型文字说成已执行或已保存

任何满足题设与必要结论的合法推导；不强制关键词/固定措辞/工具调用。
人工逐项定位回答证据；不能由被测checker或LLM judge单独给内容分。
核验能力：trusted_reference_binding；学习资格：none。
review状态：agent_prepared_only；human_author_review=pending；independent_human_review=pending。
