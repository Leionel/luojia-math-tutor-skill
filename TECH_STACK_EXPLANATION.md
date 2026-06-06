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

---

## ⚡ 二、后端网关与存储 (Backend Framework & Storage)

### 1. FastAPI 与异步并发设计
*   **技术选型原因**：抛弃了 Django 和 Flask。FastAPI 基于 Starlette 和 Pydantic，不仅原生支持 `async/await`，还能自动生成 OpenAPI Swagger 接口文档，配合 Pydantic 极其严格的数据校验（Type Hints），规避了大量类型错误。
*   **工程细节 (SSE 流的本质)**：
    *   市面上常见的 WebSocket 太重，且需要处理心跳。我们选用了 **SSE (Server-Sent Events)** 技术。
    *   在 FastAPI 中，使用 `StreamingResponse` 配合 Python 异步生成器 (`AsyncGenerator`)，这是一种基于 HTTP/1.1 `Transfer-Encoding: chunked` 的协议。我们将大模型吐出的内容、推导的状态（`thinking`, `token`, `meta`）封装成自定义字典，实现了后端与前端长连接的数据单向穿透。

### 2. SQLite 3 FTS5 本地化轻量存储
*   **技术选型原因**：教育类单用户或局域网场景，若引入 MySQL 会让部署变得极其麻烦（需要 Docker 甚至集群环境）。SQLite 轻如鸿毛，且拥有极强性能。
*   **工程细节**：
    *   没有使用重型 ORM（如 SQLAlchemy），而是用 Python 官方自带的 `sqlite3` 以及 `row_factory` 实现轻量级查询。
    *   **FTS5 虚拟表检索**：我们利用 SQLite 的 FTS5 引擎，直接在关系型库内部挂载了倒排索引（Inverted Index）。这使得即使不接大模型，我们依然能实现类似 Elasticsearch 的高性能本地知识文本搜索，兼顾了存储和轻量搜索需求。

---

## 🧠 三、大模型工作流引擎 (LLM Workflow & Agent Framework)

### 1. 为什么用 LangGraph 取代纯 LLM API？
普通的 LLM 在进行数学计算（特别是矩阵或积分）时常常一本正经地胡说八道。
*   **技术选型原因**：LangChain 原生 Agent 比较黑盒，调试困难；而 **LangGraph** 允许我们将工作流定义为一个有向循环图 (Directed Cyclic Graph)，让系统化身为一个“具备纠错能力的有限状态机 (FSM)”。

### 2. “Label-Driven” 状态机与 SymPy 物理外脑验证
*   **工程细节 (防数学幻觉)**：
    1.  强制大模型按照 `[PLAN]` -> `[VERIFY]` -> `[CORRECT]` -> `[OUTPUT]` 标签流程作答。
    2.  当嗅探到 `[VERIFY]` 附带的 ````python ```` 代码块时，LangGraph 路由拦截大模型。
    3.  系统自动调起 `sandbox_node`（后端的受限执行域），利用 `exec()` 运行大模型生成的 **SymPy (符号计算引擎)** 验证代码（如求导、解方程）。
    4.  系统捕捉 `stdout` 验证结果，将报错或得数以 `System/User` 的名义重新甩回给大模型。
    5.  大模型看到“真实执行结果”后，进入 `[CORRECT]` 反思，再生成最终给用户的 `[OUTPUT]`。这种**“逻辑推演与机器物理运算双结合”**的设计，从根本上降维打击了数学幻觉。

---

## 🔍 四、检索增强与通道控制 (RAG & Stream Optimization)

### 1. Hybrid RAG (双路召回 + RRF)
面对数学概念的模糊问题和精准名词，单一的检索经常会漏查。
*   **工程细节**：
    *   **第一路：稠密向量检索 (Semantic Embedding)**：将用户 Query 和课件利用模型接口变为高维浮点数组，用纯 Python 实现了余弦相似度。
    *   **第二路：BM25 本地检索**：为了实现高容灾，手写了 BM25 算法公式。如果 Embedding 接口挂掉，代码自动 catch 异常，无缝降级为纯本地 BM25。
    *   **RRF 倒排融合 (Reciprocal Rank Fusion)**：因为向量得分和 TF-IDF 得分量纲不一致，采用搜索工业界的 RRF 算法将两者排名平滑叠加（$Score = \frac{1}{60 + Rank_{A}} + \frac{1}{60 + Rank_{B}}$），实现精准与宽泛召回的融合。

### 2. DeepSeek V4 多轮对话隔离机制与防泄漏
*   **工程细节 (防正文污染)**：
    DeepSeek 等深度推理模型会同时返回 `reasoning_content`（碎碎念过程）和 `content`（正式结果）。为了避免模型在推理时提及 `[OUTPUT]` 导致误截断：
    *   我们在流式适配层打上了**强类型 Dict 标签** (`{"type": "reasoning", ...}`)。
    *   在流转图解析时，凡是标为 `reasoning` 的流数据将直接走专门的短路回调，发向前端时间轴，彻底杜绝主解析逻辑的跨区污染。
*   **工程细节 (防 400 Bad Request)**：
    DeepSeek V4 严格规定多轮对话中必须携带上一轮的 `reasoning_content`，否则报 HTTP 400。我们在状态机的末端动态缓存并组装了该历史字段，完美兼容其原生多轮对话要求。
