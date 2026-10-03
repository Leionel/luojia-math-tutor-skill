# A6：类型化工具首批实施切片

日期：2026-10-03。状态：待实施。目标：一次数学工具请求经过参数、权限、预算、计算、证据、交付和回执检查；失败能解释且可复跑。日程与取舍见 [Runtime 审阅](runtime-review-schedule.md)，偏离写入 [implementation-notes.md](implementation-notes.md) 的 `Deviations`。

## 1. 先证明一条完整路径

先用已有 `NumericalTask/run_numerical` 接入只读 `numerical.run`。以线性迭代 / 数值积分两类参数共用同一工具入口，不另造各领域 Agent。编译图在离线模型请求 fixture 下运行：合法完整请求 → 固定工具表 → policy → 计算 → 带 scope 的结果 → 教学正文 → A1 Guard → A2 run 回执。用户可在折叠回执看到工具名、状态和耗时，不显示模型代码或私有推理。

首个切片不自动保存新学习尝试，不改原数值实验 API，不把工具结果更新到掌握度。工具只能读当前调用的受限参数，owner/run/policy 由服务器注入，模型不能提供。纯计算与业务记录持久化分离，避免一次重试产生两条学习记录。

## 2. 最小合同

| 对象 | 首批必需内容 |
| --- | --- |
| ToolSpec / 静态表 | 固定 name/version、参数 model、固定处理器、只读属性和计算/输出预算；不加载模型指定模块或任意插件 |
| ToolCall | call_id、name/version、严格参数；限制字节、深度、列表长度和单轮数量，未知字段拒绝 |
| ToolPolicy | 服务器解析 intent、帮助等级、独立 probe、允许工具与剩余总预算；调用前检查，必要时返回 rejected |
| ToolResult | succeeded/failed/timeout/cancelled/rejected/unavailable、固定错误码、耗时、schema 版本、受限数据和 evidence scope；状态与数学结论分开 |
| ModelTurn | 普通答案和完整工具请求是不同结果类型；终止状态与是否有正文分别判断，部分请求不能执行 |

首批总工具轮数保持最多 2，每轮最多 1 个调用，默认不自动重试。参数错误允许一次模型修正，修正占同一总轮数预算；超时/取消不能被修复文案覆盖，Guard 修复阶段不得再执行工具。重复 call_id 只接受同一参数 hash，重复读请求可复用本 run 内结果；改参数复用 ID 拒绝。call_id 由模型提出时仍需严格格式校验并在服务端关联 run，不能当作授权令牌。

初始预算：单次请求 JSON 最多 8 KiB；工具处理含 worker 启动最多 10 秒；单次输出采集最多 64 KiB，超限停止并明确失败，不裁掉证据范围后伪造成功。数值任务继续使用既有维数2–8、迭代/细分100、均匀分段4096、函数求值8193上限。符号首版只有求导：表达式最多512字符、64个AST节点、深度12，符号仅x；常数文本最多32字符，幂指数仅[-8,8]整数字面量，运算与函数按显式白名单构造。结果表达式最多8 KiB，超限不可核验。正常/边界 fixtures 校准这些上限；放宽必须补预算负例，不能仅为通过一题而删限制。

无论调用状态如何，结果不能声称验证整段回答。沿用现有积分估计/残差证据合同；增加符号工具时，结论必须带假设/定义域与核验范围。答案 Guard 应检查候选是否与本轮结果矛盾，不能仅因为出现 tool_call 就显示“已核验”。

## 3. 原生调用适配与旧协议迁移

1. 将提供方输出转换为 `ModelTurn`，保持 A0 EOF/length/content_filter/损坏 JSON 合同。首批用离线完整/分片流 fixtures 验证一个 OpenAI-compatible 通道，不据此宣称真实提供方已经支持。
2. 工具名称及参数分片有总长度、完整 JSON/schema 和终止门控；原生 `finish_reason=tool_calls` 只能完成工具请求阶段，不能直接发送普通回答 `done`。缺 call_id、未知工具、参数残缺、超量调用或混乱续轮均失败。
3. 将响应结果用同一个 call_id 送回续轮；模型用量 / 真实 TTFT 在 A7 增强，首批只保留可用且安全的调用关联。能力未知时不发送未经验证的 tools 参数，保留普通教学并明确未核验；不加未经验证的文本 JSON 兼容回退。
4. 首条 typed 路径证明后，再接第二个受限符号工具，例如 `math.differentiate`。显式 AST → 白名单 SymPy 构造器，定义输入规模、指数 / 常量 / 输出预算与固定 worker 硬超时；无通用 solve/integrate/Python 接口。解析器和预算必须有攻击性边界负例。
5. 迁走提示词的“生成 `[VERIFY]` Python”指令，同时检查 Teacher/Examiner/Proof/修复提示的协议残留。旧标记不执行，可被 Guard 拦截或明示未核验；不做代码到 DSL 的猜测转换。
6. 首批正式验收时关闭默认模型生成 Python 路径，旧 executor 只在明确未迁移的受限内部用途保留，调用点清单写入回执；若仍有生产模型代码执行点，该退役切片未完成。关闭 typed 开关也不能自动开启旧路径。

函数工具超时不是 OS 隔离。固定 worker 不接受源代码，仍以应用 OS 用户运行；超时必须结束并回收实际进程，输出上限须在采集阶段执行。允许的符号计算若不能建立可接受的预算，拒绝该操作并保持未核验，不开放任意程序补缺口。F8 学生代码执行仍未开放。

## 4. 实施次序与交付

| 批次 | 预计投入 | 可独立验收的内容 |
| --- | --- | --- |
| A6.1 | 1–2 日 | 合同、单通道离线适配、numerical.run 与真实编译图/Guard/run 贯通；开始 E1 开发案例 |
| A6.2 | 2–3 日 | 第二个受限符号工具、执行预算、提示词与旧生成代码路径退役；兼容与失败显示 |

没有新 Agent SDK、向量库、MCP 依赖或 checkpoint。复用 Pydantic、现有数值计算与 A0 子进程所有权机制；抽取公共进程 helper 仅在两处确有同一约束时进行。首批没有 DB 迁移；若现有 run 白名单无法容纳最小公共工具字段，先记录必要 schema/兼容变更，再独立验收，不存放原始参数绕过白名单。

代表性修改边界：`llm/openai_compatible.py` 与 completion protocol、`agents/` 的工具合同/固定处理器、`tutor/graph.py` 与 prompt、run 白名单、API tests；UI 只增公共工具摘要与失败显示。不要同时重构全部 provider 条件分支或数据库。

## 5. 验收与停止条件

离线案例必须经过生产编译图和实际固定处理器；只有适配器或数学 worker 层的网络/进程边界允许对应替身。用临时 SQLite 检查 owner 与学习记录计数。

- 合法线性/积分请求得到相同数值合同；积分遗漏采样反例不能被称为严格误差保证。普通概念问答无需工具仍可交付。
- 参数注入、未知字段 / 工具 / 版本、极端规模、非有限值、表达式越界、超量 / 重复 call_id 均拒绝。被拒请求不调用处理器。
- 工具分片未终止、模型截断、length、错误 EOF 都不执行、不假完成；完整 tool_calls 经结果续轮后才交付正文。
- 超时、取消、进程失败、采集超预算、空结果有独立终态；实际受控固定 worker 的取消要证明进程已退出，不能只有 mock kill 断言。
- probe 中途开始重新检查允许帮助范围；记录访问越权不泄漏数据。重试与参数修正不写新的掌握度/独立成绩，不重复业务记录。
- 原生工具失败 / 不可用不能被模型写成成功；Guard 一次修复不执行工具；旧 `[VERIFY]` 不触发 Python。回执无参数原文、stdout、prompt 或密钥。
- E1 开发集记录原始提议、policy 拒绝、有效调用和必要步骤；先验证报告分母与失败退出，不用离线 fixture 声称模型会选对工具。

每批根目录 `npm.cmd test`、`python scripts/eval_agent_reliability.py`、`git diff --check`；针对 pytest 从 `apps/api` 运行并保留离线 conftest。新增回归文件名由实现决定，不预写不存在的命令。UI 改动再跑 typecheck/lint/build:web，build 前停止自己的 dev server。

STOP：假完成/取消所有权/owner/probe 回退；Guard 把执行状态当数学正确；固定 worker 无法结束或无输出采集预算；未知能力仍自动发送 tool_calls；仍依赖旧生成 Python 才能完成 typed 首版。发生时先修正该切片，其他离线案例设计可继续，不降低检查规则。

回滚：关闭 typed 路径后只提供原有普通回答/明确未核验或失败；受控数值实验 API 可继续使用。保留既有 A0/A1/A2 门控与历史回执，禁止自动恢复生成 Python。真实模型烟测留给明确配置与预算后的 A5，单独记录模型/适配器版本。

```text
PLAN VALIDATION: planning/agent-engineering-2026-10/a6-tool-runtime.md
  Answers the request    §1–3：类型化工具到交付回执的首条数学路径
  Answers landed         复用现有实验；可靠性/评测优先；旧路径渐进退役
  Scope gate             §4：两批；无新编排框架、checkpoint 或学生程序执行
  Assumptions explicit   §3–5：真实能力/符号预算待验，失败则收缩
  Verification           §5：全量离线 suite、A3 CLI、图/固定 worker 负例与回滚
```
