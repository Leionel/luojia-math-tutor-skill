# Agent Runtime 意见审阅与后续日程

日期：2026-10-03。审阅基线：`150553b68a3a63e21e0e92f6e02e31549a9420a9`。状态：**规划已更新，A4–A8 未实施**。本文件与 [主规划](plan.md) 配套，实施偏离记入 [implementation-notes.md](implementation-notes.md) 的 `Deviations`。

后续用户追加聊天/工作区割裂意见，当前日程以 [聊天衔接审阅](chat-workspace-review.md) 为准。本文件保留第一轮八项Runtime判断；相关工具/预算/恢复约束仍有效。本轮另修的帮助入口不一致见该审阅§3，不能从下方第一轮“仅文档”记录推断本轮没有代码变更。

## 1. 结论与基线修正

采纳“补Runtime”的方向：工具请求、权限、计算证据、失败和评测连起来。沿用LangGraph，不增加编排框架。加入产品意见后的顺序是 **A4.1 当前实验 → A6.1/A4.2 动作卡片与内嵌聊天 → A6.2 计算工具 / 旧Python退役 → A7计量 → A5评测**。最小工具权限从首个动作生效；A8持久恢复/C0学生程序执行仍独立验收。

来稿检查的是 `ee373ae`，早于线性方程组和积分实验交付。当前已经有三类实验、类型化 `NumericalTask`、预算和 owner/source hash 校验，但这些新实验尚未成为 Agent 工具，也没有服务端可信的实验到聊天快照。A3 已完成 **19 个协议合同 / 40 个实例**，不是模型质量 benchmark。工程回执见 [A3 与多领域交付](delivery-a3-numerical.md)。

README 确有“A3 尚未完成”的旧句，本轮修正。代码、模型调用与数据库结构本轮均不变；日程中的能力不能写成已交付成果。

## 2. 八项意见逐项处理

下表代码位置均按上述基线核对；源码行号会随实施变化。

| 来稿建议 | 核对结论 | 加入日程的方式 |
| --- | --- | --- |
| Tool Runtime，替换 `[VERIFY]` Python | **采纳并提前。** `tutor/graph.py:767,801,956` 仍抽取代码块并执行；A0 的 `ToolExecutionResult` 只是执行结果合同。已有 Verifier/求根规则，所以“所有验证都只靠 regex”并不准确 | A6 先接一个已有数值工具，再补受限符号操作。schema、policy、预算和 Guard 同批，原生调用另过适配器验收 |
| Durable Execution 属于 P0 | **缺口属实，优先级调整。** `graph.py:256` 无 checkpointer；A2 只保存回执，过期 run 标 interrupted，不恢复图 | A8 先验证一个需要刷新后继续的流程；普通单轮问答继续采用失败回执和新 run 重试。恢复不得重复学习写入 |
| Sandbox 应更强 | **采纳威胁收缩。** `agents/code_executor.py:176–236` 是当前 OS 用户权限的子进程；AST、超时与 kill 不等于 OS 隔离，stdout 在 communicate 后裁剪也不等于采集上限 | A6 迁走模型生成 Python，受限表达式只交给固定计算处理器。子进程硬终止、输入 / 输出 / 复杂度预算仍要验收。开放学生程序前再做 C0 |
| Observability 应有 span / usage | **采纳。** `run_trace.py:45–51` 固定 usage=null；`llm/openai_compatible.py:164–165` 忽略 usage-only chunk，已返回的用量也未传递 | A7 先记录真实调用数据与 tool/span 关联。供应商没有返回的字段保留 null，不能补零或把缓冲耗时叫 TTFT；专门 dashboard 延后 |
| E0–E3 分层评测 | **采纳。** A3 覆盖 E0 协议；没有真实模型工具选择或教学质量证据 | A6 同步建立 E1 开发案例，A5 冻结 E1/E2，并在预算允许时跑 E3 多轮任务。固定基线和分母，人工复核数学标签 |
| Provider capability 路由 | **采纳最小部分。** `config.py:39–43` 只有 name/provider/vision；现有适配器还有 provider 条件分支 | A6 先定义所需的 tool-calling 能力门控；A7 补 usage/streaming/输出预算等实际使用字段。未知能力不视为支持，不按提供方名称猜能力 |
| Context Engineering | **采纳并并入 A4。** prompt 已区分控制与不可信材料，也有条数限制；缺全路径统一 token 预算、实验版本绑定和可见来源 | A4 先实现 F3/numerical-lab → 聊天的只读快照、优先级、去重和裁剪。固定百分比分配不直接采用，先预留输出与工具续轮预算 |
| 统一 Human-in-the-loop | **部分采纳。** 新学习帮助保护已存在，A0 澄清后也不写评估；仍未形成持久 PendingAction | A8 试点 typed PendingAction 与持久恢复。普通数学只读工具无需人为加审批；外部写操作和学生程序执行权限另立合同 |

官方材料支持的是机制，具体排序是本项目的判断：

- [Agents SDK Tools](https://openai.github.io/openai-agents-python/tools/) 提供参数 schema、运行时工具启停和异步工具超时等机制；工具 schema 不替代数学正确性与权限检查。
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) 区分 checkpointer 和 store。[Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) 明确恢复时节点会重新执行，interrupt 前的副作用应幂等或拆开。这是 A8 的约束，不是现有 A2 已支持恢复的证据。
- [Agents SDK Usage](https://openai.github.io/openai-agents-python/usage/) 说明第三方后端的用量报告有差异，需要验证实际适配器；[Tracing](https://openai.github.io/openai-agents-python/tracing/) 提醒 span 可能采集敏感输入输出。本项目继续默认本地白名单元数据。

来稿引用的部分 LangGraph/Agents 文档是 JavaScript 版；实施依据使用 Python API，并核对本地安装版本。当前 `pyproject.toml` 只规定 `langgraph>=1.2.4`，不能据此假定已安装支持最新版 interrupt schema 的 API。

## 3. 日程与投入假设（已由产品衔接日程修订）

以下表格是第一轮Runtime意见的历史估算。当前先打通Newton实验与聊天的闭环，A4/A6拆成更小批次；剩余估算更新为 **12–19个集中开发日，每周约3日约4–7周**，包含回归余量、人工复核另计。当前S1–S5及范围以 [修订日程](chat-workspace-review.md#5-修订后日程) 为准；下面11–17日不再作为当前承诺。保留历史表用于解释范围变化，工具和恢复约束继续沿用。

以下是**从下一轮开发起算的相对日程**，按单人每周约 3 个集中开发日估算。一个开发日包含实现、回归、收尾和提交，不等于等待模型或消耗一个额度窗口。没有硬性投递日期；估算未经本轮实现验证，首个切片结束后重估。

| 顺序 / 建议窗口 | 交付 | 集中开发日 | 真正的启动条件 / 结束门槛 |
| --- | --- | --- | --- |
| S1 / 第 1–2 周 | **A6**：一个工具贯通图、schema/policy、结果证据、Guard、回执；随后受限符号工具与旧路径退役 | 3–5 | A0–A3 已完成；详见 [A6 首批切片](a6-tool-runtime.md)。关闭旧执行路径不得破坏 A0 终止 / 取消合同 |
| S2 / 第 2–3 周 | **A4**：数值实验 → 聊天的 owner/版本绑定快照与统一预算 | 2–3 | 快照读取可先独立准备；工具参与讨论前依赖 A6 的 evidence 合同。原实验 API 无须迁成 Agent 才能继续使用 |
| S3 / 第 3–4 周 | **A7**：模型 / 工具 span、真实 usage、可用能力描述及 owner 历史显示 | 2–3 | 复用 A2 run；工具 span 依赖 A6 call_id，任务来源依赖 A4。先验收保存与指标，后做显示 |
| S4 / 第 4–6 周 | **A5**：冻结 E1/E2、可选真实模型 / E3 多轮任务、演示与求职证据 | 2–3，人工复核另计 | E1 开发集在 S1 即开始；正式对照使用冻结的 S1–S3 候选。真实调用需 Key、费用上限和数学 gold |
| 各批之间 | 回归修复、文档与演示余量 | 2–3 | 已计入下方总投入，不挤掉 owner/取消/泄漏检查 |

主线总计 **11–17 个集中开发日，约 4–6 周**；窗口会重叠，表内不是每一行固定占满对应周。预算或人工复核不到位时，交付离线报告与演示，真实模型结果标待验证，不用 fixture 补数字。可在 S1 结束就演示受控工具，在 S2 结束演示跨领域连续讨论，不必等所有阶段完成才用于项目介绍。

**A8 不挤入上述总量。** 在需要跨刷新 / 重启继续同一任务且重做确有成本的业务路径出现后，安排 1–2 个开发日 PoC；实际集成按 PoC 重估。触发候选是图像解析待确认或多步证明待补条件，不是任意闲聊。C0、MCP、远程执行、完整 trace dashboard 和全提供方路由留在有具体需求的后续池。

顺序调整原则：A6/A4 的数据与权限合同先成立；E1 案例设计可同步，计量基础在真实评测前完成。工期吃紧先减展示和模型数量，不删失败、取消、owner、版本和 probe 门槛。

## 4. 各阶段可验收的结果

### A6：能控制一次工具调用

采用已有 Pydantic 与轻量静态工具表。最小公共字段是 tool_name/version、call_id、严格参数、只读 / 副作用分类、调用状态、error_code、耗时及 evidence scope。Policy 由服务器和当前帮助级别决定，模型不提交 owner 或自行提权。取消、总轮次和输出预算沿用 A0/A2 的约束。

第一条垂直路径用现有 `math_tools/numerical_lab.py` 的 `NumericalTask/run_numerical`，复用计算合同；新模型工具首批不写学习记录。第二条路径只支持明确白名单的符号操作，例如受限表达式求导 / 比较，显式构造符号 AST，禁止将不可信字符串直接交给动态 eval、`sympify` 或 `parse_expr`。无定义域或假设支撑的“恒等”结论保持不确定。

原生 function calling 的 terminal、分片参数、续轮与 call_id 关联是独立适配合同，不能简单允许 `finish_reason=tool_calls` 当作正文完成。首批只验证一个适配通道；不支持的提供方继续普通回答或明确未核验，不静默回退执行 Python。具体迁移和负例见 A6 切片。

### A4：回答引用同一次实验

先接 `/numerical-lab` 已保存实验，再复用同一快照合同接求根记录。请求只带记录类型 / ID / 版本，服务端检查 owner、source hash、记录存活和实时 probe 状态；snapshot 不接受客户端覆写的轨迹、分数或“已验证”标志。回答与“本次参考了什么”展示同一版本，用户可移除引用。

统一 ContextBudget 服务 teacher / examiner / proof 与 fast 路径：先保留系统控制、当前问题、帮助限制、输出上限及工具续轮余量，再选实验摘要、教材引用和最近历史。去重依据记录 ID/版本与来源 ID，不按文本相似性吞掉矛盾证据。超预算先缩减低优先级历史，不能裁掉 owner/probe/证据范围；仍不足就明确追问或失败。未知 context window 使用保守配置，记录计数方法与估算性质；首版不靠模型压缩权威成绩和证据。

验收：越权、删除、版本变化、跨会话、注入指令、长轨迹、预算耗尽、引用移除与 probe 中途开始。F1/F2/F8 延伸和完整可纠正推断记忆留在第二批，不能用“实验快照完成”代表 A4 全部完成。

### A7：成本与失败能归因到实际调用

保持 run 回执与消息终态权威一致。span 带 parent_id、call_id、阶段、起止、终态和有界错误码；取消 / 超时也必须收束 span。模型调用记录安全别名、已知 provider、提供方 usage、模型首个可见内容 delta 时间；缓冲完成与 UI 首次可见正文另命名，reasoning delta 不算正文 TTFT。

能力字段只覆盖当前要用的调用方式、streaming、usage 与输入 / 输出预算；按精确模型 / 配置保存来源与核对时间。未知就是 unknown，离线兼容合同不代表该真实模型支持。usage 来源标 provider_reported/missing；一次 run 内逐请求聚合，重试计费请求也计入，缺失时总量标部分已知。cached/reasoning tokens 语义未确认不参与费用计算；费用只有在价格版本、币种和提供方用量均明确时计算。

白名单不含提示词、原始参数/正文、stdout、密钥、上传内容、用户自定义 base_url 或私有推理。来源 ID 按 owner 可读，导出只用合成案例或去标识 ID。旧 run-v1 缺字段仍可读；新增字段 / migration 必须先验临时旧库和失败原子性，正式库启用前 SQLite backup。界面优先复用折叠回执，不先建 `/dev/traces` 面板。

### A5：从“程序通过”推进到“Agent 做对任务”

| 层级 | 首批案例与范围 | 指标口径 / 使用条件 |
| --- | --- | --- |
| E0 已有 | A3 冻结的终止、取消、Guard、SQLite 合同；新运行时另加合同且升 manifest 版本 | 合同/实例分开报告，不回写旧版 19/40 分母，也不叫模型准确率 |
| E1 新增 | 先准备约 12 条开发案例，覆盖工具必要 / 不必要、错误工具与参数、有限修正、超预算、失败后终止、来源版本、probe。冻结时另留约 8 条未见案例 | 原始工具提议与 policy 拦截分开计数；正确调用精确率=必要且有效的提议/全部提议，召回率=完成必要工具步骤/标注必要步骤；无分母时 null，避免“不调用所以分数高” |
| E2 新增 | 概念、条件解释、推导提示、练习、实验讨论和 F8 静态意见；数学 gold、证据一致与答案泄漏分别标注 | 独立人工核对，保留分歧与依据；规则标签命中不代替语义正确，不让同一模型自评当唯一 gold |
| E3 可选 | 少量合成的实验→讨论→修订多轮任务；先固定成功条件与帮助暴露级别 | task_success=达到预定任务结果的任务/可评估任务；追问、重试和失败计入成本。模型辅助完成不叫学生独立掌握；延迟与 tokens 只在可观测子集报告覆盖率 |

真实对照使用帮助边界修复后的 `612e3a4` 基线与实际交付的 A4/A6/A7 候选 SHA；第一轮所列 `150553b` 仍是当时审阅基线。只比较双方支持的同一任务、模型与参数，新增覆盖单列；先单模型同配置，再考虑第二提供方，不能把模型差异当代码收益。开发/未见分开，修正未见题须披露污染并换集。

新增行为评测命令与 A3、`npm test` 分开，先提交离线解析/案例合同。真实模型批量调用必须显式启用，在隔离库运行；首轮最多 100 请求，同时设置货币费用上限、最大生成 tokens、超时及失败停止阈值。预算计数包括 retries；用量未知时按已核对价格与输入 / 输出上限保守预留每次请求费用，无可验证价格则不批跑。预算和 Key 未落实不阻塞离线工作，也不运行收费评测。

求职交付附版本、复跑命令、架构图和三分钟演示。可以讲工具合同、失败恢复设计与多领域证据；只有完成真实评测才能写其数据。教师 gold / 学生无 AI 测验 / 延迟保持研究仍按六个月主线推进。

## 5. A8 的独立启动与停止条件

PoC 只选一个图像解析后待确认流程，先持久化 PendingAction 与明确恢复输入；不一次把 vision、intent、proof 都迁移。使用与实际安装 LangGraph 相容的持久 checkpointer，必要的 saver 依赖先在隔离库验证，不能用 RAM MemorySaver 宣称重启恢复。

- 对话历史、学习事实、执行回执、checkpoint 各有用途；run/session/owner/thread/checkpoint 映射由服务端生成。`paused` 与 A2 的终态 / 续租 / 过期恢复语义先定义，再迁移。
- PendingAction 绑定 action_id、owner、run、记录版本、所需字段、允许动作、有效期和恢复位置；恢复端点重验 owner/probe/版本，单次消费和并发 CAS。客户端不能指定任意 goto 或修改成绩。
- checkpoint 只含必要的序列化任务状态或记录引用，不保存 API key、私有推理、原始上传文件或整个未筛选的 AgentState。过期清理与取消后删除 / 禁止恢复均有合同。
- 节点重执行、副作用与 checkpoint 提交不是一次全局事务。PoC 用写入前 / 写入后 / checkpoint 前后崩溃注入、重复恢复、并发恢复和第二进程重启验证幂等；不假设拆节点就自动获得 exactly-once。
- 暂停时明确告诉用户所需信息；拒绝/超时/版本变化有界结束，不伪造 completed。恢复输入仍是用户数据，不能绕过工具 Policy、Guard 和独立测验保护。

如果不能保证 owner、幂等、恢复版本兼容或数据收敛，停止生产集成，保留新 run 重试。PoC 报告单独交付后再估集成日程；长任务恢复并非 A6/A4/A7 完成的前提。

## 6. 发布、回滚和验收

每阶段按 feat/fix/test/docs 分批提交并推送，记录代码 SHA 与独立验收；新框架、外部执行和数据库迁移不能藏在文案更新里。只 stage 本批清单，保留既有原型、egg-info、ignored results/env/数据库。

- A6 用独立开关灰度；关闭类型化工具后返回普通未核验回答或明确失败，**不自动开启旧 Python**。数值实验页面原有受控 API 继续可用。需要表达式输入的固定 worker 用硬超时 / kill / 输出采集预算验收，不用 `wait_for(to_thread(...))` 冒充终止 CPU 工作。
- A4 可停止 snapshot 注入，原实验记录保留；scope/owner/probe 门槛始终生效。A7 出错不能修改成功消息或抹去已有 run，新增表/字段代码回滚保留数据；敏感内容不得先入库再靠 UI 隐藏。
- 前述任何独立成绩、原始事件、取消所有权、假完成、owner 或日志脱敏回归失败，停止本批推送 / 扩大灰度，先修复。不得靠降低评测门槛或删除负例变绿。

每批必跑根目录 `npm.cmd test` 和 `git diff --check`；凭证检查使用 `git grep "sk-"` 并判读误匹配。A6/A4/A7 协议变化另跑 `python scripts/eval_agent_reliability.py` 及该批新增离线负例；API 针对测试从 `apps/api` 运行。前端变化再跑 typecheck/lint/build:web，build 前停止自己的 dev server。A8 增加独立进程/持久库的重启与重复恢复验收。真实调用、远端 CI、部署和教学收益分别取证，不能从本地绿色推断。

## 7. 审阅收敛与未验证项

| 规划维度 | 来稿作为实施日程的缺口 | 本轮收敛 |
| --- | --- | --- |
| 完整性 | 八项能力没有迁移 / 错误 / 回滚串联 | §4–6 给出各批输出、失败与回滚 |
| 可行性 | 全提供方与持久恢复被当成可直接套用 | 首批复用已有 typed 数值计算；适配器、符号预算和 A8 必须做垂直验证，真实性能尚未验证 |
| 范围 | 五大运行时层同时落地容易挤掉 A4/A5 | §3 分 S1–S4；A8/C0/MCP 有条件启动 |
| 可测试性 | 建议有指标，缺分母、gold 和污染规则 | E0–E3 分开，开发/未见分开，新增负例和版本门控 |
| 风险 | checkpoint 被误认为恢复即安全 | §5 明确重执行、owner、幂等、过期和停止条件 |
| 假设 | 预算、版本、开发产能未给定 | §2–5 明示配置与相对投入，收费部分保持待验证 |

已核对：当前工具文本路径、无 checkpointer、usage 丢弃、现有 typed 实验和离线回执。未核对：真实提供方原生工具能力 / 用量、实际延迟、A8 saver 兼容和真实数学 gold。前者支撑排期；后者是各批验收条件，不是本轮给出完成承诺的依据。

```text
PLAN VALIDATION: planning/agent-engineering-2026-10/runtime-review-schedule.md
  Answers the request    §1–3：审阅八项意见并合并现有 A4/A5 日程
  Answers landed         岗位 AI 应用/Agent 工程、可靠性/评测优先、先完成本轮再规划
  Scope gate             §3、§5：首批垂直切片；A8/C0/MCP 条件启动
  Assumptions explicit   §2–5、§7：版本、工期、预算、人工 gold 与真实能力待验证
  Verification           §6：npm.cmd test；A3 CLI；各批负例；前端/持久库条件检查
```
