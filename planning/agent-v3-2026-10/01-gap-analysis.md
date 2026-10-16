# Agent v3：缺口分析

> 当前交付更新（2026-10-07）：S5.0 已在工作区实现并完成离线工程验收，见[09交付回执](09-delivery-s5-0.md)：API700/Web56，E0 v2 38合同/92实例，S5.0增量10合同/45实例；前端typecheck/lint/build通过。S5.1–S5.2质量runner/gold及live、linear接入仍待实施。下方原审计/规划描述保留日期，不代表当前源码状态。

基线及验证口径见 [00-current-baseline.md](00-current-baseline.md)。这是源码、既有离线回归和固定探针的审计；不推断未运行模型的失败比例。

> 2026-10-07补充：07 R1/R2确认350ms collector与固定worker冷启动的调度冲突、无学生候选代算可进入mastery、unknown若仍携带mistake可进入另一写入入口。原G1/G2仍未修复；S5.0现在按[08](08-s5-0-verifier-contract.md)验收正常能力、独立deadline、候选绑定与两个sink。G3仅是开放推理质量证据缺口，不能据此推断主要失败来自缺ProofState。先用现有字段修复，Evidence不是必建模块。

## 最大的五个真实缺口

| ID / 优先级 | 已确认事实及影响 | 源码证据 | 测试/评测证据 | 后续最小动作 |
|---|---|---|---|---|
| **G1 / P0** 旧学生表达式入口绕过受控解析 | `parse_math` 用默认 `parse_expr`；自动单步检查在应用进程的线程里运行，未复用 typed AST/固定 worker。检查预算到期取消 await，不等于终止计算线程。属于服务端表达式执行边界缺口 | `math_tools/verifier.py:58` `parse_math`；`step_checker.py:85` `check_step`、`:101` 字符串 `sp.diff`；`fast_context.py:381` `_collect_symbolic_result`；`routes_tutor.py:25` 请求入口 | 本轮 `check_step` 能把固定无副作用的 builtins 字符串长度计算当作合法等价式；同一表达式被 `typed_tools.expression_tree` 拒绝。`test_typed_math_runtime.py:test_symbolic_attack_budget` 只证明新 typed 路径，不能覆盖旧入口 | S5.0 将旧检查统一到明确操作+受控语法+固定 worker；缺少支持就 unknown，不转到任意代码执行 |
| **G2 / P1** 验证范围与学习证据语义不够严格 | 关键词命中可返回 `verified=True, is_correct=False`；`x/x=1` 的排除点丢失；未定式类型被写成洛必达全部条件已满足；未确定的等价性被压成 false。这些结果可能进入 mistake/BKT | `step_checker.py:129` 末尾 heuristic fallback；`misconception.py:29` `detect_mistake`、`:60` 关键词判定；`verifier.py:63` / `:227`；`fast_context.py:605`、`:629` `_update_learning_state` | 正确陈述“互斥和独立不是一回事，对吗”被判错误；`(x*sin(1/x))/sin(x)` 的极限被标为满足洛必达条件。现有 `test_verifier*.py` 偏简单正负例，没有覆盖这些范围；探针见 `results/agent-v3-audit-probes.json` | S5.0 先把 heuristic 与可计分核验分开；scope/assumptions/unknown 最小合同，之后才决定更广的 VerificationEvidence |
| **G3 / P1** 开放推理缺少独立证据 | 证明/反例任务经过 LLM review 再 LLM 教学；没有命题→前提→检查证据的稳定绑定；模型可能一致地误判，但工程回归仍绿 | `fast_path.py:62` `verification_mode_for`；`graph.py:642` `verifier_node`、proof route；`proof_tutor.py:4`；`prompt_builder.py:146` | `test_agent_graph.py`、`test_prompt_restructure.py` 检查路由和标注；不提供真实模型证明正确率。`VerificationReview` JSON 类型严格不等于逻辑严格 | S5 先量 first-error、假设、反例有效性；只对失败集里的 1–2 类补局部证据，暂不全量 ProofState |
| **G4 / P1** 缺 E1/E2/E3 公平对照与 live smoke | E0 强，但未冻结任务级行为、人工数学 gold、闭环成功与真实调用预算，尚不能知道主瓶颈在哪 | `evaluation/agent_reliability_v2.json`；`scripts/eval_agent_reliability.py:75`；`evaluation/root_diagnostic_manifest.json` | 本轮 38/92 通过；求根 fixture 明确 developer-only / teacher pending。retrieval/case benchmark 只评各自召回/匹配任务，不能替代 Tutor 质量 | 实施 [S5 协议](02-evaluation-s5.md)，先离线 runner/gold，再显式 opt-in 小样本 live |
| **G5 / P2** 产品上下文与动作闭环只在 Newton 达到同等级 | `LearningContextRef.kind` 只有 root_lab，resolver 只接受 Newton；线性/积分仍复制文本后跳聊天；卡片每次由固定映射提供；预览结果未作为同 run 的数学 evidence 自动回灌 | `learning_context.py:11` / `:21`；`learning_actions.py:35` `root_proposal`；`orchestrator.py:560`；`numerical-lab/page.tsx:111`；`lab-tutor.tsx:32` | `test_learning_context.py` / `test_learning_actions.py` 证明 Newton 合同。保存后的新实验会更新当前引用，下一次提问能读取它；因此不能声称“Agent 完全不知道动作结果” | 先补可关联的 action outcome 评测；下一产品切片接 linear，再 integration；教材选段为第二候选 |

G1 的探针不读文件、不写系统状态、不访问网络、不接触密钥。它证明**执行表达式能力越界**，不证明已经遭受攻击。SymPy 官方明确提醒 `parse_expr` 使用 eval，不适合未经清理的输入：[Parsing](https://docs.sympy.org/latest/modules/parsing.html)。不能把 `evaluate=False` 或字符黑名单作为解决办法。

## G2 的数学复核

- `x/x` 只在 `x ≠ 0` 定义；化简得到 1 不证明原式在所有实数上与 1 是同一个函数。核验应保存原始定义域并说明比较范围。
- `sqrt(x²)=|x|` 对实数成立；当前符号没有实数假设，接口也没有域参数。应说明域缺失或用明确的实数约定，不直接给学生“错误”的结论。
- 对 `f(x)=x sin(1/x)`、`g(x)=sin x`，二者在 0 的极限都是 0，但 `f'/g'=[sin(1/x)-cos(1/x)/x]/cos x` 无极限；原比值也随 `sin(1/x)` 振荡。仅检查 0/0 不能宣布洛必达适用。
- `detect_mistake` 在正确的“互斥≠独立”陈述中看到两个关键词就命中误区；它可以产生待核对的教学假设，不能充当作答错误的确定证据。

这些是局部已确认缺陷；不等于整个数值诊断模块失效。SymPy 的假设系统保留 unknown；项目也应保留这种语义：[Assumptions](https://docs.sympy.org/latest/guides/assumptions.html)。

## 七类审计判断

| 类别 | 已经足够复用的部分 | 剩余问题/证据 | 处置 |
|---|---|---|---|
| Agent Runtime | strict native envelope、能力绑定、两轮预算、固定进程回收、原子终态 | G1 是未迁移的 pre-context 边路；不是要求第二套 Registry | 先堵边路，不重写 graph |
| Product integration | Newton 引用/参数卡/预览/保存/刷新，NotebookChat 内嵌会话 | G5；独立模型 tool loop 与人工业务动作是两条受控路径，缺跨路径评测关联 | 保留两种授权语义，增加 outcome/link，而非合并所有 service |
| Math reasoning | root oracle；线性残差/充分条件；积分估计；受控求导 | G3；`ProofStep`、子目标和数学状态不存在但尚未证明值得做 | S5 定位 failure cluster |
| Verification | execution 与 mathematical validity 的免责声明 | G2；ToolResult 不绑定具体数学 claim/assumptions，布尔 verified 不同来源不同含义 | 先 scope，后轻量 VerificationEvidence |
| Evaluation | E0、检索/case/求根工程 fixtures | G4；模型/数学/学习质量的分母混用风险 | 四层独立报告 |
| Context | history 6000 字符、hit 2400、document 6000/引用时3000、snapshot8KiB等局部预算 | `prompt_builder.py:56`；输入实际 token 分槽、工具结果累计占用尚未 profiling。S3 request bytes gate 不是实测 token | 先采样 size/tokens 与截断后条件保留率；不设臆测比例或先建 ContextAssembler |
| Production | owner、帮助边界、span私密字段投影；不开学生代码执行 | G1；typed worker无OS/CPU内存强隔离；HTML同步死循环；README账号缺令牌撤销等；真实供应商/负载/部署未知 | G1 发版前修复，其余沿既有 C0/发布门槛；本轮非完整渗透或部署验收 |

补充验证指针（以下 app 路径相对 `apps/api/app/`，web 路径相对 `apps/web/`）：

| 结论 | file / function | 测试与本轮验证范围 |
|---|---|---|
| 求根确定诊断可复用，仍须保留条件/unknown | `math_tools/root_runner.py:run_reference`、`math_tools/root_finding.py:diagnose` | `test_root_oracle.py:test_newton_root_error_against_independent_decimal_reference`、`test_missing_conditions_and_tool_failure_are_unknown`；本轮完整离线套件通过，不是模型教学验收 |
| linear与积分各有明确数值范围 | `math_tools/numerical_lab.py:linear_reference` / `integration_reference` / `check_result` | `test_numerical_lab.py:test_missing_sufficient_condition_does_not_claim_divergence_or_error_bound`、`test_aliasing_can_meet_estimate_without_true_accuracy_and_never_claims_proof`；估计达到阈值不等于真实误差保证 |
| prompt局部字符预算存在，分槽token profiling缺失 | `tutor/prompt_builder.py:build_messages`、`tutor/learning_context.py:resolve_learning_context` | `test_prompt_restructure.py` 与 `test_learning_context.py` 验证提示/引用合同；不能验证未采集的真实供应商分槽token |
| 账号生产能力和动态HTML强终止仍有局限 | `api/routes_auth.py:register` / `login` / `me`、`auth.py:issue_token` / `decode_token`；web `components/static-artifact.tsx:StaticArtifact` 的30秒timer、`lib/visual-artifact.ts` | README §账号/动态图示明确记录限制；`visual-artifact.test.ts` 和 `html-sanitize.test.ts` 是构造/清理回归，本轮未做同步死循环强终止或部署验收，不能据此声称OS隔离 |

## Course Graph：参与了哪些推理工作

`CourseEvidenceBuilder.build_evidence_pack` 会按任务召回案例、概念锚点和一跳子图，注入 required conditions、prerequisite 和 forbidden shortcuts；这比无结构 RAG 更有约束作用。`_condition_details` 明确返回 `verification_status=not_checked`，案例声明条件也不冒充已成立事实。

因此准确定位为 **课程结构引导的证据检索与教学路由**，不是本题的 premise checker 或 Reasoning Graph。`supports_proof`、`derives` 边存在，不证明当前学生推导的逻辑依赖已被核验。来源：`knowledge/evidence_builder.py:28` / `:46`、`knowledge/schema.py:KnowledgeRelation`、`test_course_retrieval_production.py:test_endpoint_evidence_builder_and_offline_evaluator_use_identical_ranking` / `test_prompt_restructure.py:test_case_conditions_and_uncertainty_reach_prompt_without_probe_answer`。当前未验证条件不要升级成 mastery truth。

## 接哪 1–2 条工作区

下面是源码复用与风险的定性判断，不是用户实验得分或实测工期。

| 候选 | 用户收益 / 复用 | 状态与帮助风险 | Agent 展示 / 数学价值 | 决定 |
|---|---|---|---|---|
| linear saved experiment | 高 / 高，已有 NumericalTask、owner 保存记录 | 中：矩阵、selected iteration、残差/解误差范围不同于 root | 高 / 高，可展示非求根与条件诊断 | **第一条**，先 linear 的单条闭环 |
| integration saved experiment | 高 / 高，沿用同一 numerical 记录 | 中高：估计不能升为误差保证；选中的是细分层级/子区间 | 高 / 高，天然反例与 scope 演示 | 第一条的后续分批扩展，不与 linear 同时全做 |
| reading selected source | 高 / 高，已有 `reading_explanation.source_excerpt` 的 owner/hash/section/offset | 中：资料指令、删文/改版、摘录截断和版权范围 | 高 / 中，定理前提来源透明 | **第二条**，S5 后只接一个选段引用，不增全PDF编辑器 |
| code selected finding | 中高 / 中，现有 code_hash、finding、静态版本对照 | 中高：模型容易误说已运行；源代码是数据 | 高 / 中 | 下一候选，仍只静态审阅 |
| study active task | 中 / 中，已有task状态与待反馈确认 | 高：不能越过 ack/probe 或变成自动成绩写入 | 中 / 中 | 后置；先只读任务状态再考虑动作 |
| teach-back | 中 / 中，已有source_hash与模型意见区分 | 中高：模型评价不等于验证，不更新独立成绩 | 中 / 中高 | 等E2讲回rubric与模型质量证据 |
| assessment result | 中 / 中 | 高：题目/答案泄漏与未完成测评的帮助边界 | 中 / 中 | 首批不接；仅已结束且允许披露的结果摘要候选 |
| notebook | 已有内嵌Chat，共享控制器；会话绑定资料 | 中：选中笔记段落没有同等级版本化LearningContext | 中 / 中 | 保留，复用reading能力再升级；不是从零做NotebookChat |

当前产品取舍以修订04为准：S5.0后默认先linear已保存实验的只读Chat引用，继续用原实验台编辑/保存；不强制新参数卡，也不等待开放证明全题库。integration/reading后续按观察择一，教材接入不是必然第二名。上表为原定性候选比较，不是已测收益或同时开工要求。

## AX 子审计：Chat 与受控动作面板

候选文件实际扫描：`tutor-chat.tsx`、`tutor-conversation.tsx`、`use-tutor-conversation.ts`、`chat-lifetime.ts`、`math-message.tsx`、`agent-run-receipt.tsx`、`lab-tutor.tsx`、`root-action-card.tsx`、`routes_tutor.py`、`orchestrator.py`、`graph.py`、`learning_actions.py`。配置编辑器/独立Agent Dashboard不在这次 playbook 范围。

| Playbook 检查 | 结果 | 证据/限制 |
|---|---|---|
| Chat progress | pass | `use-tutor-conversation.ts:61` 订阅消息/run；receipt展示阶段 |
| Chat escape hatch | pass | `chat-lifetime.ts` abort；`use-tutor-conversation.ts` cancel；`test_agent_runs.py:test_asgi_disconnect_cancels_buffered_model_without_next_chunk` |
| Chat context injection | pass | `prompt_builder.py:56` 与 `learning_context.py:21`，并非只有静态system |
| Chat confidence cues | warn / fix-this-sprint | `graph.py:479` / `step_checker.py:129` 的heuristic会被包装成确定核验；最小修复见S5.0，不是多添一个思考动画 |
| Chat uncertainty markers | unknown | 代码有未知/范围提示；没有真实模型内容样本，不据grep判模型是否恰当表达不确定性 |
| Chat intent handshake | pass | `policy_router.py` 澄清；写入靠显式save，读取/计算不增重复确认 |
| Chat direct manipulation | unknown | 参数输入/预览/保存按钮存在；本轮没有新交互观察，不给体验判定 |
| Chat memory visibility | warn / fix-this-sprint | `fast_context.py:629`、`routes_mastery.py:9`；读取得到估计，但可追溯依据与误判申诉链不足。不能让用户随手改写客观独立成绩 |
| Chat generative momentum | unknown | 未观察空白入口，不新增自动代写/付费生成要求 |
| Tool human escalation | n/a | 固定工具只有有限计算；没有支付、外部发布或自主删除工具，不凭技能模板加入客服平台 |
| Tool approval UI | pass | `root-action-card.tsx:72` 预览、显式save；只读计算不强制审批 |
| Tool execution gate | pass，限定当前集合 | `ToolCall` literal白名单、`ToolRuntime.policy`、`LearningActions`重读已交付卡片；没有通用可注册写工具入口 |
| Tool escape hatch | pass，限定路径 | 固定worker取消/回收回归；参考记录可用新参数重新实验；不宣称已保存记录可自动逆转 |
| Tool progress visibility | pass | `graph.py:_traced_node`、`call_observation.py:span`、RunTrace事件 |
| Tool explicit completion | pass | `model_turn.py:TurnAssembler`、completion protocol、原子delivery；EOF不等于成功 |
| Tool intent handshake | pass | preview参数哈希和最新preview的显式保存；无模型自主保存 |
| Tool context use | pass，Newton范围 | `LearningActions._proposal`重验上下文；其他工作区缺口是G5，未冒称支持 |
| Tool API granularity | pass，规则排除项 | 只有两类不同参数的固定数学工具，稳定小集合；没有几十个同形API机械包装 |

AX 自检：计划/执行 **18/18**，unknown **3/18**，suppressed **0**；两项源码警示都有定位与S5.0修复方向。两项警示同属 sprint，按技能的同档自检要求保留 **INCOMPLETE** 子审计结论，不能用它签发生产上线许可，也不为凑档位臆造 blocker。整体审计另有 G1/P0，应先修复。

AX Relationship Summary：当前能理解并引用已保存的具体实验，用户确认后预览/保存，跨会话保留历史与学习估计；最高动作能力是受控 preview→save receipt，未自主维护学习状态。信任信号为 **moderate**：owner、取消和原子终态有证据，核验措辞与学习估计仍可能误导。关键缺口是把核验范围和真实证据来源绑定到结论。后续需要原型/用户研究回答：学生能否区分“模型意见”“本步核验”与“整题证明”？
