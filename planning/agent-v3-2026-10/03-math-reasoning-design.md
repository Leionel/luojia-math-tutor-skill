# 数学推理设计：先选择需要解决的失败

> 当前交付更新（2026-10-07）：S5.0 已在工作区实现并完成离线工程验收，见[09交付回执](09-delivery-s5-0.md)：API700/Web56，E0 v2 38合同/92实例，S5.0增量10合同/45实例；前端typecheck/lint/build通过。S5.1–S5.2质量runner/gold及live、linear接入仍待实施。下方原审计/规划描述保留日期，不代表当前源码状态。

修订：2026-10-07，依据[独立审阅](07-plan-review.md)。状态：方案比较与条件设计，**未实施**。推荐Option A；优先完成[08核验/学习资格合同](08-s5-0-verifier-contract.md)，用现有字段解决scope、候选绑定和历史来源问题。独立VerificationEvidence模块延期，不先引入四层新抽象。

## 四种方案比较

| 方案 | 预期作用（待评测） | 成本 / 迁移风险 | 评测难度 | 教学体验 | 当前决定 |
|---|---|---|---|---|---|
| A：现有LLM + targeted deterministic tools | 修scope、假设、局部计算、反例证据，能针对已知G1/G2 | 低到中；复用现有worker/guard/meta | 最低；同任务有明确oracle | 学生知道哪一步检查了什么，失败仍能继续问 | **推荐先做**；一次只选1–2个S5失败簇 |
| B：轻量公开ReasoningState | 有望减少多步依赖丢失，帮助定位首错与学生补一步 | 中；新的状态权限/失效规则，但可先单run | 中；需控制相同上下文与额外calls | 可显示目标/条件/未解决步骤，而不是私人思维 | 仅S5证明确有依赖类失败后小规模实验 |
| C：完整Problem IR + Reasoning Graph | 更系统地表达前提、子目标、定理应用 | 高；任意数学解析、图一致性、持久化与UI都扩大范围 | 高；IR错与求解错相互混淆 | 可能清楚，也可能强迫学生适应系统格式 | **Not Now**；没有复杂度收益证据 |
| D：formal prover assisted | 对形式化命题提供可检查的证明证书 | 高；命题翻译、版本/toolchain、库定理选择成为新瓶颈 | 高；还需验证形式命题等同原题 | 对小证明subset有意义，浮点实验主线收益未证实 | 只feasibility，暂不集成Lean |

这些是工程判断，没有假定任何“正确率提升XX%”。B/C/D即使类型或图漂亮，也不能证明能改善数学质量。

## 三层数学能力保留边界

- **领域确定性诊断**：现有root oracle / linear residual / integration estimate。继续复用，它们已经有条件和错误定位价值。增强时仍区分实数定理、浮点计算与采样估计。
- **局部符号检查**：优先处理输入语法、安全工作进程、变量域、等价范围、unknown。只支持明确合同中的表达式，不用LLM把未知句子翻译成代码再执行。
- **开放证明**：LLM生成、LLM review、source support是辅助意见；只有外部checker能支持的具体claim才升级证据状态。不要因为两个模型一致就标verified。

### S5.0最小合同与后续Evidence的区别

S5.0在当前返回值/meta中补足origin、scope、assumptions、unknown原因、原输入/学生候选绑定、checker版本和server决定的学习资格；字段先复用，不能靠类名完成。执行成功、核对学生候选和可写学习事件分别判断。无候选代算仍可提供参考结果，但`is_correct=null`；mistake/mastery两处消费入口均检查资格，heuristic/unknown/reference_help不写学生检查事件。350ms检索窗口不能吞掉固定进程核验，正常输入矩阵、独立deadline和旧消息读路径均按08验收。

先用现有VerifyResult/ToolResult和metadata的一处构造/投影消除误指。只有多个结果错绑定同一学生claim的具体失败仍存在，且Guard/UI/评测至少两处确需共同绑定时，才考虑以下可选artifact；它不是本轮或两周必交。

## VerificationEvidence：局部字段不足时的后续候选

```text
VerificationEvidence (proposed, evidence-v1)
  evidence_id            server-generated
  claim_id / claim_text  公开结论，有限长度，不是私人推理
  input_hash             校验规范化前的输入、域与假设
  scope                  固定枚举
  assumptions            显式前提及其来源
  outcome                verified / supported / contradicted / unsupported / unknown
  basis                  deterministic / source_support / llm_review
  checker_version
  parent_span_id / result_ref
  limitations            排除点、浮点、采样范围等
```

Scope首批按S5失败选择：`expression_equivalence`、`derivative`、`integral_candidate`、`indeterminate_form`、`numerical_witness`、`theorem_precondition`、`counterexample`。`formal_proof` 只在实际拿到形式化证书时可用，不预先开放工具名。

| outcome | 可支持的语义 | 禁止的推断 |
|---|---|---|
| verified | 指定checker在明确域、输入和scope内完成确定核验 | 本步核验→整题证明；CAS→形式化证书 |
| supported | 来源/人工审查或有限观测支持当前说法，范围可见 | LLM同意→verified；教材定理存在→本题条件成立 |
| contradicted | 可确认的矛盾、合法反例或在定义域内的反例见证 | 关键词命中→学生确错；数值不稳定→精确数学反证 |
| unsupported | 当前论断没有所需依据/引用与论断不对应 | 缺证据→数学命题必假 |
| unknown | 缺域、超范围、checker失败、预算中止或无法判定 | 用false替代unknown或给未知结果计分 |

上表是未来内部设计，不要求首版UI展示五个近义标签；若两个状态的消费行为相同，应合并或保持原因字段。真启动Evidence后，由server构造，LLM只能提议公开claim/witness，不能写verified/证书/owner/成绩。checker只处理能力内的claim，课程来源只标source support。学生原句、model inference、tool result、learning evidence、independent outcome、course fact保留来源；reference-help反例不能变成独立完成。

实现边界：复用现有工具dispatcher和worker；先最多8条短Evidence放现有message metadata/评测sidecar，不新建通用Registry、数据库或后台任务。公开RunTrace不放原始输入/输出；复用tool span的ID，初期不加独立“reasoning span”。只有E3需要定位某次核验而现有span不足时，才扩展`clean_step`白名单中的最小scope/ref字段并加隐私回归。

VerificationRequest仅是内部固定operation的请求类型，不是模型自由注册工具接口。规范化前保存输入摘要和域约束，避免约分后忘记排除点。未知域先追问；纯表达式句法不够表达定理全部前提时明确拒绝自动确认。

## 可选MathProblem最小形态

若S5显示经常丢失题意/域，先给单run增加 `{domain, problem_type, givens, assumptions, goal, variables}`；constraints可作为assumptions条目，course theorem是候选引用，不由模型自动当作已应用。

不提前解析任意教材题、完整definitions体系和所有candidate_theorems。输入由学生公开题意/已确认视觉题意生成，LLM的抽取需可见确认；已有LearningContext直接复用可信参数，不能再抽一套与保存记录冲突的Problem对象。

## ReasoningState/ProofStep：条件启动方案

触发条件见S5：跨来源/题型的同机制失败、便宜局部修复已比较、有限公开step干预在新的独立确认中仍有净收益且无新增泄漏/过度验证。题数只是探索投入，不再以“至少3个失败”自动立项。首批只试定理条件检查和一至三步公开修订，不承诺自动解全题。

最小状态：`goal`、`assumptions`、最多8条公开steps、`open_subgoals`、`evidence_refs`、`state_version`。每step有 `id, premises, conclusion, justification, theorem_ref?, status, evidence_refs`；状态语义沿用上述表，而不是correct/wrong二选一。

| 生命周期问题 | 最小答案 |
|---|---|
| 谁创建 | server根据已确认题意创建；model只给受schema校验的proposal |
| 谁更新 | server reducer校验patch；学生编辑公开步骤；checker仅修改自己支持的证据状态 |
| LLM能改什么 | 提议分解/下一提示/候选证明行，保留原学生行；不能改gold、已确认事实来源或独立成功 |
| 持久化 | 首次实验只单run，最终公开卡片保存为message artifact；它不是可恢复的执行checkpoint |
| 下一run继续 | 用学生选择的公开卡片和ref/hash重建上下文并重验，拒绝stale；不自动恢复隐式模型状态 |
| 条件变了怎么办 | 前提版本变化使依赖steps/evidence失效；旧卡片保留历史，不能继续显示为当前已验证 |
| 用户看到什么 | 目标、显式条件、公开理由、待补步骤、已检查scope，能“为什么/给提示/我来补/检查这一行” |
| 私人推理 | 不存、不要求、不展示隐藏chain-of-thought；公开推导是面向学生的可审阅解答 |

Course Graph保留长期课程节点与关系；题目内step依赖只用单run list/refs，**先不用图数据库或完整Reasoning Graph**。只有环/依赖失效需要稳定表达且list不足时，再讨论临时图。

## Counterexample：优先于Lean的有界候选

推荐试三个小模板，依S5实际错误选择其中一个先做：

1. 连续不必可导：`|x|` 在0；确认证明前提与左右差商，不能靠绘图宣称证明。
2. Newton在**迭代点**导数非零不保证任意初值收敛：`x³−2x+2` 从0产生0→1→0，两点导数分别−2和1。它不反驳“全定义域导数非零”版本；需要那个命题时另选并复核witness，不偷换假设。现有root runner/oracle可复用。
3. 按代数重数有n个特征值不保证可对角化：2×2 Jordan块`[[1,1],[0,1]]`，特征值1的代数重数2但特征空间维数1。矩阵关系checker须单独做有界合同，不能声称当前工具已经支持。

流程：学生claim→识别量词/域→从有限教学模板或LLM proposal选witness→固定checker逐项检查约束/违反结论→输出CounterexampleEvidence（claim、witness、constraints_checked、scope、版本/ref）。读到“任意/存在”不够时先澄清；没找到witness不证明命题真。

初期最多3候选、每候选受现有工具/请求预算约束；为回答该题给的witness计reference_help。随机数值搜索只生成待验证候选，不把少量采样变成普遍证明。对浮点反例需误差/不确定性分析或精确见证，否则supported/unknown。

ROI判断是本次工程推断：可复用root诊断、gold容易复核、反馈可解释，预计比首批全面Lean更快提供本科教学价值；**尚未测到质量提升**。

## Strategy Search：更后面的有界实验

只有S5显示提供正确context/tool后仍因单一路线失败，且B方案不足，才试2–3条公开策略（直接/反证/逆否/构造等）。最大3策略、子目标深度2，总模型/工具预算合并计算；先做离线development比较。选中策略必须有独立gold/evidence支持；投票不产生正确性。

不启动MCTS、自博弈、复杂多Agent debate或递归无上限搜索。用户能选一条路线/自己补步骤，比后台无界生成更贴近首版目标。

## Lean feasibility：仅L3、小subset

Lean的tactic构造proof term，kernel检查形式化命题：[Lean Tactic Proofs](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/)。这保证的是**该形式化statement**，不自动保证它等同学生的自然语言题目，也不保证教学解释质量。

适合候选：精确代数恒等式、有限维小矩阵命题、短实数不等式或数列定义证明；先3–5条人工formalize、无`sorry`/新增公理，固定Lean/mathlib版本并检查依赖。暂不做完整Newton收敛定理、任意函数区间分析、浮点舍入/积分采样证书或全教材证明。

进入L3前需在L1（受控CAS/数值）和L2（公开步骤+局部证据）都难以处理的高价值失败，明确人工statement审核；评估formalization工时、现有库覆盖、运行预算、学生能否理解反馈。自然语言→Lean翻译的错误可能成为首要瓶颈，目前无数据支持自动化。

作为可选L3 verifier，不替换Runtime、Course Graph或所有回答。工具失败为unknown；证书有效也不能绕过help boundary或自动计分。本轮不安装Lean、不接新服务。

## Context、可观测性与A8

- 先记录prompt/history/evidence/learning snapshot/tool结果的字节/字符数，以及实际provider输入token。无法可靠分槽token计数就null，不拿固定30%/20%比例分配。
- 若现有硬截断导致必要条件丢失，先压缩冗余history/轨迹并显式标omission；只有profiling证实组装重复/预算冲突，才考虑ContextAssembler。
- 现有model/tool span用于S5调用成本、故障和causal分析；数学scope/origin与候选摘要优先复用meta，不以此要求Evidence refs或Trace SaaS。只有现有receipt/JSON确实不能定位具体失败时才另立Viewer切片。
- A8依赖跨重启继续**同一个公开reasoning state**的实测需求。现在短run、可重试新run和保存引用已覆盖主线；AgentRun不是checkpoint。继续延期，不自动replay。
- 若未来长证明/HITL确实需要A8，使用明确thread/namespace/版本与持久checkpointer，再解决side effect幂等、owner、stale context、帮助边界和重启权限；不以过程内MemorySaver当持久恢复。参考：[LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)。

## 三种价值分别验收

| 项目 | Agent Engineering | Mathematical AI | Educational |
|---|---|---|---|
| VerificationEvidence | typed artifact、trace关联、失败可审计 | claim/scope、反例与定理条件依据 | 告诉学生检查了哪一步、缺什么条件 |
| 轻量ReasoningState | reducer/版本/受控patch | 条件与子目标依赖 | 首错定位、自补步骤/修订 |
| 有界反例 | proposal→checker→receipt | 有效witness及量词判断 | 打破错误规则并解释边界 |
| Lean subset | 可复跑证书adapter | 形式化statement核验 | 是否帮助理解仍需用户研究 |

工程合同通过、数学gold通过、学生学习迁移分别统计，不能相互替代。
