# 珞珈数智助教低延迟解答架构设计

## 1. 背景与目标

当前 Tutor 请求采用固定的多 Agent 串行链路：

`Intent -> Retrieve -> Planner LLM -> Policy LLM -> Verifier LLM -> Teacher LLM`

这套架构强化了角色分工与教学约束，但普通请求在首个有效回答出现前，可能经历远程 Embedding 和多次非流式 LLM 调用。职责边界清晰，热路径却过长。

本次优化以以下目标为优先级：

- P95 首段有意义内容小于 1 秒。
- 普通请求只进行一次 Teacher 流式 LLM 调用。
- 需要严格数学判断的请求通常不超过两次 LLM 调用。
- 保留 Planner、Policy、Verifier、Teacher、Examiner、RAG、BKT 和 Memory 的原有职责及评测口径。
- 不以未经验证的数学结论换取速度。

可编辑架构图：

- [珞珈数智助教低延迟解答链路](https://www.figma.com/board/xVpZVU6mWcDQbjwVHi2RBU)

## 2. 架构原则

### 2.1 Agent 能力保留，调度改为按需

多 Agent 架构继续存在，但不再要求所有 Agent 都成为每次请求的必经节点：

- **Planner**：常见请求由确定性本地规则生成学习目标；复杂请求才调用 LLM。
- **Policy**：规则路由优先，低置信度或歧义请求才调用 Policy LLM。
- **Verifier**：继续负责高风险数学判断；SymPy 能确定时不调用 Verifier LLM。
- **Teacher**：仍是面向学生生成最终教学内容的唯一 Agent。
- **Examiner**：练习生成请求直接进入 Examiner 分支。
- **RAG**：本地 BM25 进入快速上下文；远程 Embedding 作为增强能力，不阻塞首字。
- **BKT 与 Memory**：快速读取进入当前轮次，非关键增强和持久化可后置。

因此系统仍是“神经符号双轨、多 Agent 分工、可验证教学”，执行模型升级为：

`快速教学主路径 + 按需确定性验证 + 异步学习增强`

### 2.2 首段必须有意义且安全

SSE 建立后立即发送 `opening` 事件。该内容由本地逻辑生成，必须满足：

- 与用户请求相关，不是通用“正在思考”占位文本。
- 只允许复述任务、确认当前步骤、提出下一步观察方向或说明正在检查的对象。
- 不得包含最终答案、正确性判定、关键公式结果或未经验证的数学断言。
- 前端将其展示为助教回答的开场，而不是独立系统通知。

示例：

- 学生提交步骤：“我先检查你目前这一步使用的规则，再一起定位需要调整的位置。”
- 请求概念解释：“我们先抓住这个概念解决的核心问题，再看它在题目里如何出现。”
- 请求练习题：“我会围绕当前考点给你一道同难度练习，并保留独立作答空间。”

## 3. 请求阶段与时间预算

### 3.1 即时阶段：0-150ms

FastAPI 收到请求后：

1. 使用本地规则识别粗粒度意图、请求模式和学科。
2. 生成安全 `opening`。
3. 立即通过 SSE 发送，不等待数据库、RAG 或远程模型。

目标不是空白占位，而是让用户在 1 秒内看到与问题相关的第一段有效内容。

### 3.2 快速上下文阶段：预算 350ms

以下任务并行执行：

- 读取会话历史和当前会话元数据。
- 读取 BKT 掌握度和连续错误次数。
- 本地 BM25 知识检索。
- 本地规则生成 Planner 学习目标。
- 本地规则选择 Policy 教学动作。
- 对明确的学生步骤按需执行 SymPy 检查。
- 对绑定文档执行 SQLite FTS/LIKE 快速检索。

聚合器采用截止时间语义：

- 截止时间内完成的结果进入当前轮 Teacher Prompt。
- 超时的可选任务被取消或转入后台，不阻塞 Teacher。
- 必要的确定性校验不允许静默跳过；超时后进入高风险 Verifier 分支，或输出不带结论的保守引导。

### 3.3 生成阶段

路由规则：

| 请求类型 | 路径 | 典型 LLM 调用数 |
| --- | --- | ---: |
| 概念解释、一般提问 | Fast Context -> Teacher | 1 |
| 明确学生步骤，SymPy 可判断 | Fast Context + SymPy -> Teacher | 1 |
| 复杂证明、开放推导、本地无法判断 | Fast Context -> Verifier -> Teacher | 2 |
| 生成练习题 | Fast Context -> Examiner | 1 |
| 规则路由低置信度 | Policy LLM -> 对应生成 Agent | 2 |

Teacher 和 Examiner 必须流式输出。Verifier、Policy fallback 等内部调用保持非流式，但只在条件分支触发。

### 3.4 后台增强阶段

以下任务移出首字热路径：

- 远程 query Embedding 与语义检索增强。
- 详细考点 LLM 识别。
- 非关键画像增强。
- 分析日志和延迟指标写入。
- 不影响当前回答的持久化工作。

后台结果只能服务于后续轮次或分析系统，不得在当前回答已输出后偷偷改写已展示内容。

## 4. 组件设计

### 4.1 Fast Path Router

新增一个纯本地路由组件，输入为用户消息、模式、显式学科和基础会话状态，输出：

- `intent`
- `subject`
- `pedagogical_action`
- `learning_objective`
- `verification_mode`: `none | symbolic | llm`
- `confidence`

该组件使用明确关键词、请求模式、现有 `route_intent`、`detect_subject` 和教学规则，不访问网络。

### 4.2 Opening Generator

新增无网络依赖的开场生成器，根据 `intent`、`mode` 和 `verification_mode` 返回短文本。模板数量保持有限，避免为文案引入新的复杂系统。

### 4.3 Fast Context Collector

统一管理并行任务和截止时间：

- 使用 `asyncio.gather` 或 `asyncio.TaskGroup` 启动独立任务。
- 同步 SQLite 方法通过 `asyncio.to_thread` 执行，避免阻塞事件循环。
- 每项结果具有默认值和来源标记。
- 输出一个结构化 `FastContext`，供 Prompt Builder 使用。

### 4.4 Knowledge Search 分层

知识检索拆分为两个明确接口：

- `search_knowledge_local`：只使用已加载 BM25 索引，必须快速且不访问网络。
- `search_knowledge_semantic`：调用 Embedding 并进行混合排序，属于增强路径。

向量索引在应用启动或首次空闲时预热。不能在用户首个请求中批量生成整库 Embedding。

### 4.5 LangGraph 路由

保留 LangGraph，并将图调整为条件路由：

`Fast Route -> Fast Context -> Verification Gate -> Teacher / Examiner`

高风险分支：

`Verification Gate -> Verifier LLM -> Teacher`

Planner LLM 和 Policy LLM 变为低置信度 fallback 节点，而不是固定边。

## 5. 数据一致性与错误处理

### 5.1 当前轮次一致性

- 用户消息必须在生成开始前持久化，避免刷新后丢失。
- 助教最终消息在流式完成后持久化。
- 客户端断开时取消不再需要的生成与远程检索任务。
- 后台任务失败不得使当前 SSE 请求失败。

### 5.2 降级策略

- SQLite 读取失败：使用空历史和默认掌握度继续。
- BM25 失败：无 RAG 上下文继续。
- SymPy 失败：升级为 Verifier LLM；若不可用，输出保守提问，不给判定。
- Policy 规则低置信度且 LLM 不可用：回退到 `hint`。
- Teacher LLM 首 token 超时：发送明确的可恢复错误事件，并保留已经发送的安全开场。
- 远程 Embedding 失败：不影响当前轮次。

## 6. 可观测性与性能指标

每个请求记录以下阶段耗时，不记录 API Key 或完整敏感内容：

- `opening_ms`
- `fast_context_ms`
- `local_rag_ms`
- `symbolic_verify_ms`
- `policy_fallback_ms`
- `verifier_ms`
- `teacher_first_token_ms`
- `total_ms`
- `llm_call_count`
- `route`

验收目标：

- 本地测试中 `opening_ms < 150ms`。
- 集成环境 P95 首段有意义内容小于 1 秒。
- 普通请求 `llm_call_count == 1`。
- SymPy 可判定步骤请求 `llm_call_count == 1`。
- 高风险请求 `llm_call_count <= 2`。
- 现有教学泄题、步骤检查、BKT 和 RAG 回归测试保持通过。

## 7. 测试设计

### 7.1 单元测试

- Fast Path Router 对解释、提示、步骤检查和出题请求路由正确。
- Opening Generator 不包含已知答案、判定词和用户输入中的答案复述。
- Local RAG 不调用 `create_embedding`。
- Fast Context 超时后使用默认结果继续。
- SymPy 成功时不调用 Verifier LLM。
- 低置信度请求触发 Policy fallback。

### 7.2 集成测试

- SSE 中 `opening` 必须早于 `meta` 和 `message`。
- 人为延迟 RAG/数据库时，`opening` 仍立即到达。
- 普通请求只调用一次生成模型。
- 客户端取消请求后，后台生成任务被取消。
- 远程 Embedding 异常时 Teacher 仍可输出。

### 7.3 性能测试

使用可控的假 LLM 和延迟注入，分别测量：

- 快速路径首段延迟。
- RAG 超时对首段延迟的影响。
- Verifier 分支调用数。
- 20 个并发 SSE 请求下事件循环是否被同步 SQLite 操作阻塞。

## 8. 文档更新范围

实现完成后同步更新：

- `README.md`：将固定串行双轨图更新为快速主路径和按需验证图，并解释兼容关系。
- `TECH_STACK_EXPLANATION.md`：补充延迟预算、分层 RAG、条件 Agent 调度和可观测指标。
- 必要时更新相关提案文档中的架构描述，避免继续宣称所有 Agent 每轮串行执行。
- 保留 FigJam 链接，方便答辩、评审和后续编辑。

## 9. 非目标

- 本轮不引入 Redis、Celery、Kafka 等新基础设施。
- 本轮不更换 LangGraph、FastAPI、SQLite 或前端框架。
- 本轮不重写教学 Prompt 和 BKT 算法。
- 本轮不把推测式数学结论作为首段内容。
- 本轮不解决完整认证体系和此前安全审查中的全部问题；与本次热路径直接相关的危险执行方式应在实现时避免扩大。
