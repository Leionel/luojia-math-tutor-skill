# Spec 设计文档：Agent Trace 可视化与 RAG / LangGraph 重构

## 1. 业务目标与需求背景

本项目当前版本（v4）虽然具备了初级的错题匹配和简单的流程处理，但其后端处理逻辑呈线性瀑布式，无法处理复杂的工具循环调用。此外，前端的“思考过程”展示仅为一整坨大段文本，体验不够丝滑且显得不够专业。

为打造“工业级 Agent”系统，本迭代的目标是：
1. **前端 Trace 轨迹可视化**：将模型思考、工具调用、沙箱报错通过结构化 Timeline 美观渲染。
2. **后端 LangGraph 重构**：基于状态机重构后端，实现 `Intent -> Orchestrator <-> Tools (RAG/Sandbox) -> Pedagogy` 的闭环链路。
3. **语义 RAG 升级**：引入本地向量嵌入与检索，结合 BM25 形成混合检索，并采用 RRF（倒数排名融合）对检索结果进行归一化融合。

---

## 2. 架构设计与状态机模型 (LangGraph)

### 2.1 状态定义 (Agent State)
基于 Python `typing.TypedDict` 及 LangGraph 提供的 `add_messages` 与 `operator.add` 增量追加机制：

```python
import operator
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]        # 消息历史列表，由 LangGraph 自动拼接
    intent: str                                                 # 当前意图 (Intent)
    subject: str                                                # 学科科目 (calculus, linear_algebra, probability)
    concepts: List[str]                                         # 涉及的概念考点
    verifier_result: Optional[dict]                             # 验算器的静态检查结果
    mistake: Optional[dict]                                     # 诊断出的错题详情
    thinking_steps: Annotated[list[dict], operator.add]        # 关键：Trace Steps，使用 operator.add 自动累加拼接列表
```

### 2.2 节点拓扑图 (Nodes Topology)
工作流由以下节点和路由组成：

1. **`intent_node`**：进行静态分析与初步分词，判定当前意图（例如是否是 `CHECK_STEP`）。
2. **`orchestrator_node`**：LLM 主脑。绑定了 `search_knowledge`（RAG 工具）和 `execute_code`（代码沙箱工具）。
3. **`tools_router`**：条件路由。判断 `orchestrator` 输出的 `AIMessage` 是否包含 `tool_calls`。如果是，将其分配到具体的 `rag_node` 或 `sandbox_node` 执行。
4. **`rag_node`**：执行语义检索，返回 `ToolMessage` 并追加当前 Trace 步骤。
5. **`sandbox_node`**：运行 Python 代码，捕获输出并返回 `ToolMessage` 并追加当前 Trace 步骤。
6. **`pedagogy_node`**：在没有工具调用且 LLM 完成最终思考时，后置处理掌握度更新、错题入库，整理最终的 SSE 响应。

---

## 3. 本地混合检索 RAG 引擎设计

### 3.1 文本切片 (Chunking) 与合并策略
在索引阶段，使用带重叠的滑动窗口切片：
*   **块大小 (Chunk Size)**：$256$ 字符。
*   **重叠大小 (Overlap Size)**：$50$ 字符。
*   每个切片保存原知识条目的概念 ID（`concept_id`）及块序号作为元数据。
*   **相邻块合并 (Context Merge)**：检索返回 Top-K 块后，如果检测到同一个 `concept_id` 的相邻块同时被检索出，则自动合并它们，恢复更连贯的推导段落，以防上下文被中途打断。

### 3.2 向量检索与 Fallback
*   通过 `OpenAICompatibleClient` 的 `/v1/embeddings` API 将切片文本转化为 $1536$ 维向量。
*   **API 故障 Fallback 方案**：若 Embedding API 调用失败或无配置，则将语义权重系数 $\alpha$ 强制降为 $0$，检索机制完全降级为纯关键字检索，保障系统离线不崩溃。

### 3.3 稀疏向量检索 (BM25)
*   本地实现一套纯 Python 的 BM25 文本打分算法。
*   在索引阶段预先构建全局词频（TF）和逆文档频率（IDF）索引。知识库更新时重构该词典。

### 3.4 倒数排名融合 (RRF) 与混合评分
采用 RRF 对语义向量相似度排序（稠密检索）与 BM25 排序（稀疏检索）进行无量纲融合：
$$RRF\_Score(d) = \sum_{m \in \{Dense, Sparse\}} \frac{1}{k + r_m(d)}$$
其中常数 $k$ 设为 $60$，$r_m(d)$ 为文档 $d$ 在该检索通道中的排名。排序后取出 Top-3 的切片作为大模型的 Tools 输入上下文。

---

## 4. 传输协议与 Trace UI 交互

### 4.1 SSE 结构化消息格式
后端运行 LangGraph 过程中，将通过外层 `astream_events` 实时捕获节点执行或工具调用的生命周期事件（如 `on_chain_start` / `on_tool_start` 等），在管道流式转换为 SSE 推送：
```text
event: trace
data: {"step": "intent_detect", "status": "success", "content": "检查步骤"}

event: trace
data: {"step": "rag_tool", "status": "running", "query": "特征多项式计算"}

event: trace
data: {"step": "rag_tool", "status": "success", "content": "检索到行列式展开法则"}
```

### 4.2 前端 Timeline 渲染样式
*   **交互状态**：默认可折叠/展开。
*   **节点样式**：
    *   `intent_detect`：常规通知。
    *   `rag_tool`：展示搜索关键字及卡片式概念。
    *   `sandbox_tool`：展示内嵌代码终端（带报错高亮及运行结果）。
    *   以纵向虚线 timeline 连接各步骤，使用不同 icon 与状态色区别运行成功/失败。

---

## 5. 安全性与可靠性设计
1. **防止死循环**：在 LangGraph 编译和调用时，强制限制模型迭代 recursion limit 上限为 $15$。
2. **沙箱隔离**：代码沙箱限制超时时间为 $5$ 秒，屏蔽含有 `os`、`subprocess` 等高危系统调用关键字。
3. **[TODO] AST 安全加固**：MVP 阶段对受信任的本地用户开放，后续需引入 `ast` 进行语法树解析，实现只允许特定安全语法节点类型的严格沙箱执行，或者在 Docker/Docker-Compose 隔离环境中隔离运行 Python Sandbox 进程。
4. **输入兜底**：大模型如果偏离工具调用格式，未输出 `tool_call_id`，沙箱节点捕获并向图状态返回 `ToolMessage` 报错说明，引导模型自我纠正。
