# 珞珈数智助教 (Luojia Math Tutor) - 全栈核心技术架构与工程答辩指南

> **文档说明**：本文档不仅是系统的技术栈说明，更是**项目深度代码走查与架构答辩**的终极参考。当被问及“为什么这么设计”、“具体怎么实现”时，本文档将为你提供整个全栈链路上的核心考量、算法细节与工程取舍（Trade-offs）原因。

---

## 🌐 一、前端核心架构 (Frontend Stack)

### 1. Next.js 14 (App Router) & React
*   **技术选型原因**：我们放弃了传统的 Vue/SPA 架构，选用了 Next.js 14 的 App Router。
    *   **SSR 与流式渲染 (Streaming SSR)**：Next.js 的 React Server Components (RSC) 允许我们将不常变动的骨架屏或重组件放在服务端渲染，极大提升了首屏加载速度。
    *   **文件系统路由**：`app/` 目录结构天然支持嵌套路由与 Layout 复用，比如 `dashboard` 和 `mistake-book` 共享着同一套带有农场国风配色的侧边栏模板，代码复用率极高。
*   **工程细节**：
    *   我们在全局挂载了 React Context (`useTutorChat`) 管理会话状态。
    *   针对高频的大模型流式输出，并没有频繁触发 React 的全量重渲染。我们在接收 SSE 数据时，仅在组件内部局部触发 State 的增量追加（`content: ${content}${token}`），防止大型 DOM 树（尤其是带复杂公式渲染时）引发明显的 UI 阻塞和卡顿。

### 2. Tailwind CSS & ui/shadcn 组件库
*   **技术选型原因**：传统的 CSS-in-JS (如 Styled-Components) 存在运行时性能损耗，而 SASS 存在命名冲突（BEM 规范）。Tailwind CSS 提供原子化类名，生产环境经 PostCSS 打包后体积极小。
*   **工程细节**：
    *   **国风主题定制**：在 `tailwind.config.ts` 中，我们注入了核心主题色。比如底色 `#faf7f2`、主品牌色 `#617a55`。配合 `clsx` 和 `tailwind-merge` 实现类名的条件渲染，例如根据 `isThinking` 动态增删外边距。
    *   我们并非从零造轮子，而是使用了基于 Radix UI 的 **shadcn/ui** 组件作为底层。这使得下拉框（Select）、弹窗（Dialog）具备极高的可访问性（a11y），同时我们完全掌控其样式层代码以配合国风 UI。

### 3. KaTeX / MathJax 与 Markdown 渲染引擎
*   **技术选型原因**：由于系统定位于数学助教，大量的输出是 LaTeX 格式（如积分 $\int e^x dx$）。
*   **工程细节**：
    *   前端 `math-message.tsx` 集成了定制版的 Markdown 渲染器。
    *   利用正则拦截大模型生成的特定数学块结构，动态将其交给 LaTeX 引擎解析。为了保证流式渲染平滑，我们在底层做了 Buffer 处理，只有检测到完整的 `$` 闭合对，才进行语法树解析，防止数学公式在流式传输一半时产生刺眼的红字报错。

### 4. React Flow 知识图谱动态可视化 (M3 新增核心)
*   **技术选型原因**：单纯的文字或者卡片无法让学生直观建立起知识点之间的“前置关联”与“支撑网络”的脉络感，而 `@xyflow/react` 提供了极具互动性的基于 Node 和 Edge 的图表渲染。
*   **工程细节**：
    *   我们使用 React Flow 编写了 `<KnowledgeGraph />` 组件，接收后端 `EvidencePack` 下发的数据集。
    *   **自适应布局 (Auto Layout)**：组件通过解析节点间的 `prerequisite` 依赖关系层级，实现了自动自左向右布局图谱的排列，同时与主题模式深度融合（支持暗黑模式和主题高亮），作为对数学溯源最直观的技术辅助。

---

---

## 📚 五、离线知识管线与运营后台 (M1 & M2 核心)

### 1. 离线入库管线 (Knowledge Ingestion Pipeline) - M1
*   **工程痛点**：传统的 PDF 或 Word 解析无法准确剥离高等数学中的大量公式，导致检索时“公式丢失”或乱码。
*   **工程细节**：
    *   **大模型辅助切分 (LLM-Assisted Chunking)**：我们没有使用简单的正则或按字数切分（Token Splitter），而是编写了专门的 Ingest Agent。它逐页读取教材文档，通过大模型以**语义为边界**进行逻辑段落提取，生成高内聚的 `KnowledgeUnit`。
    *   **数学元数据保留**：切分过程中，所有行内与行间公式（LaTeX）都被原样剥离并独立存储为元数据（`latex` 字段），不仅保障了 BM25 的准确性，也保障了展示的完整性。
    *   **自动提取拓扑关系**：通过多提示词提取，直接从文本描述中识别知识点之间的关联（例如：`requires`, `supports_proof`），生成 `KnowledgeRelation` 节点，为 M3 的 Graph Expansion 奠定结构化数据基础。

### 2. 运营端审核台 (Admin Review Flow) - M2
*   **技术选型**：为了对教学质量做最终把关，系统绝不能直接上线大模型自动提取的生肉数据。
*   **工程细节**：
    *   **人工校验工作流 (Human-in-the-loop)**：生成的知识单元最初状态皆为 `draft`（草稿）。通过后端的 `/api/admin/knowledge/pending` 等接口将草稿暴露至前端。
    *   **双栏沉浸式校验 UI**：我们在 Next.js 前端构建了双栏 Review Center：左侧为挂载目录树，右侧则是富文本与 LaTeX 所见即所得的预览台。教研员可以在界面直接修改解析错误的公式，并一键点击 Approve (`active`)。
    *   **发布引擎 (Publish Engine)**：当教研员审核完毕后，调用 `POST /publish`。该发布引擎会将所有 `active` 的知识重新序列化、更新倒排索引和 BM25 缓存，同时生成图谱关联数据，实现无缝发布上线。这完全规避了传统重启服务刷数据的笨重流程。

## ⚡ 二、后端网关与存储 (Backend Framework & Storage)

### 1. FastAPI 与异步并发设计
*   **技术选型原因**：抛弃了 Django 和 Flask。FastAPI 基于 Starlette 和 Pydantic，不仅原生支持 `async/await`，还能自动生成 OpenAPI Swagger 接口文档，配合 Pydantic 极其严格的数据校验（Type Hints），规避了大量类型错误。
*   **工程细节 (SSE 流的本质)**：
    *   市面上常见的 WebSocket 太重，且需要处理心跳。我们选用了 **SSE (Server-Sent Events)** 技术。
    *   在 FastAPI 中，使用 `StreamingResponse` 配合 Python 异步生成器 (`AsyncGenerator`)。首个 `opening` 事件由本地规则立即生成，随后再发送 `meta`、`thinking`、`message` 与 `done`，因此数据库、RAG 或模型变慢时，学生仍能先看到与问题相关的有效回应。
    *   事件转发使用 `asyncio.wait(..., FIRST_COMPLETED)`，不再通过固定间隔轮询队列。客户端断开后会取消 LangGraph 任务，避免无用户消费的模型调用继续运行。

### 2. SQLite 3 FTS5 本地化轻量存储
*   **技术选型原因**：教育类单用户或局域网场景，若引入 MySQL 会让部署变得极其麻烦（需要 Docker 甚至集群环境）。SQLite 轻如鸿毛，且拥有极强性能。
*   **工程细节**：
    *   没有使用重型 ORM（如 SQLAlchemy），而是用 Python 官方自带的 `sqlite3` 以及 `row_factory` 实现轻量级查询。
    *   `sqlite3` 是同步接口，Tutor 热路径统一通过 `asyncio.to_thread` 读取历史、写入消息和更新 BKT，避免阻塞 FastAPI 事件循环。
    *   **FTS5 虚拟表检索**：我们利用 SQLite 的 FTS5 引擎，直接在关系型库内部挂载了倒排索引（Inverted Index）。这使得即使不接大模型，我们依然能实现类似 Elasticsearch 的高性能本地知识文本搜索，兼顾了存储和轻量搜索需求。

---

## 🧠 三、大模型工作流引擎 (LLM Workflow & Agent Framework)

### 1. 为什么用 LangGraph 取代纯 LLM API？
普通的 LLM 在进行数学计算（特别是矩阵或积分）时常常一本正经地胡说八道。
*   **技术选型原因**：LangChain 原生 Agent 比较黑盒，调试困难；而 **LangGraph** 允许我们将工作流定义为一个有向循环图 (Directed Cyclic Graph)，让系统化身为一个“具备纠错能力的有限状态机 (FSM)”。

### 2. 条件状态机与确定性 SymPy 验证
*   **工程细节 (防数学幻觉与控制延迟)**：
    1.  `Fast Path Router` 使用本地规则生成 `intent`、`pedagogical_action`、`learning_objective`、`verification_mode` 与置信度，不访问网络。
    2.  `Fast Context Collector` 并行执行历史/BKT、本地 BM25、课件检索和按需 SymPy 检查；可选任务超过 350ms 即降级为空结果。
    3.  明确积分、求导等可解析步骤直接调用受控的 `check_step`/SymPy 函数，不执行模型生成的任意 Python 代码。
    4.  普通路径为 `Fast Context -> Teacher`；出题路径进入 Examiner；复杂证明或本地无法判定时才进入 `Verifier LLM -> Teacher`。
    5.  Policy LLM 仅作为低置信度 fallback。角色职责仍然存在，但不再要求所有 Agent 每轮串行运行。

---

## 🔍 四、检索增强与通道控制 (RAG & Stream Optimization)

### 1. Layered RAG (本地热路径 + 后台语义增强)
面对数学概念的模糊问题和精准名词，单一的检索经常会漏查。
*   **工程细节**：
    *   **热路径：BM25 本地检索**。首次请求只构建本地倒排索引，不批量请求整库 Embedding；即使模型服务完全不可用，也能召回知识条目。
    *   **后台路径：Semantic Embedding**。当前回答完成后异步计算语义召回并放入有界缓存，供后续相同问题使用；异常只写日志，不改变已展示内容。
    *   **混合排序：RRF**。缓存中已有语义向量时，仍可使用 Reciprocal Rank Fusion 合并 BM25 与语义排名，避免比较不同量纲的原始分数。

### 2. Graph-Augmented RAG 与强溯源 Evidence Pack (M3 新增核心)
*   **工程痛点**：传统的 RAG 只能召回“表面相似”的切片，无法理解数学体系中“想要懂微积分，必须先懂极限”的层级逻辑。
*   **工程细节**：
    *   **图谱一跳检索 (1-hop Graph Expansion)**：在传统 RAG 拿到 `direct_hits` 之后，系统会自动去全局图谱映射关系中捞取这些节点的 `prerequisite` 和 `supports_proof`，补全前置知识，最终合并组装为带有拓扑结构的 **Evidence Pack (证据包)**。
    *   **强迫症级溯源提示工程**：通过重构 `prompt_builder`，我们在大模型的系统指令中不仅下发 `Evidence Pack`，还严厉要求大模型在讲解知识时，必须带上类似 `[P.12]` 或 `[节点ID]` 的角标引用。
    *   **对话流拦截与前端卡片联动**：彻底打通了“讲义 -> 检索 -> 组装 -> 生成 -> UI 展示”的完整链路。前端使用正则在 SSE 流中实时拦截引用标记，将其渲染为交互式的 `<SourceSpanCard />`。这是实现“翻书画重点式讲解”的关键。

### 3. 延迟预算与可观测性

每个 Tutor 请求在 `done` SSE 事件中返回无敏感内容的阶段指标：

| 指标 | 含义 |
| --- | --- |
| `opening_ms` | 本地安全开场生成耗时，开发环境目标 `< 150ms` |
| `fast_context_ms` | 历史、BKT、BM25、文档与符号检查聚合耗时 |
| `local_rag_ms` | 本地 BM25 检索耗时 |
| `symbolic_verify_ms` | SymPy 确定性检查耗时 |
| `policy_fallback_ms` | 低置信度 Policy LLM 耗时 |
| `verifier_ms` | 高风险 Verifier LLM 耗时 |
| `teacher_first_token_ms` | Teacher/Examiner 开始生成后的首 token 耗时 |
| `total_ms` | 请求从进入后端到 `done` 的总耗时 |
| `llm_call_count` | 本轮真实模型调用数 |
| `route` | `teacher`、`examiner`、`verifier_teacher` 等实际路径 |

验收目标是集成环境 P95 首段有意义内容小于 1 秒；普通请求和 SymPy 已确认请求只调用一次生成模型，高风险请求不超过两次。

可编辑架构图：[FigJam - 低延迟解答链路](https://www.figma.com/board/xVpZVU6mWcDQbjwVHi2RBU)

### 3. DeepSeek V4 多轮对话隔离机制与防泄漏
*   **工程细节 (防正文污染)**：
    DeepSeek 等深度推理模型会同时返回 `reasoning_content`（碎碎念过程）和 `content`（正式结果）。为了避免模型在推理时提及 `[OUTPUT]` 导致误截断：
    *   我们在流式适配层打上了**强类型 Dict 标签** (`{"type": "reasoning", ...}`)。
    *   在流转图解析时，凡是标为 `reasoning` 的流数据将直接走专门的短路回调，发向前端时间轴，彻底杜绝主解析逻辑的跨区污染。
*   **工程细节 (防 400 Bad Request)**：
    DeepSeek V4 严格规定多轮对话中必须携带上一轮的 `reasoning_content`，否则报 HTTP 400。我们在状态机的末端动态缓存并组装了该历史字段，完美兼容其原生多轮对话要求。
