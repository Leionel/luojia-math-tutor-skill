# Agent Trace 可视化与 RAG / LangGraph 重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 本计划将重构数学助教后端为 LangGraph 循环工作流状态机，支持本地 BM25 + Embedding 向量语义混合检索 (RAG)，并通过 SSE 输出结构化 Trace 步骤，在前端对话框内嵌渲染为精致的步骤时间轴。

**Architecture:** 后端弃用原有的瀑布式 `stream_reply` 逻辑，在 `graph.py` 中编排 Intent、Orchestrator、RAG、Sandbox、Pedagogy 节点，用 `astream_events` 实时抓取节点运行状态流式推送到前端；前端对结构化数据进行 Timeline 动态渲染。

**Tech Stack:** LangGraph, LangChain Core, FastAPI, SSE, React, Lucide React, Tailwind CSS

---

### Task 1: 升级 LLM 客户端以支持 Embedding API

**Files:**
- Modify: `apps/api/app/llm/openai_compatible.py`
- Test: `apps/api/tests/test_embeddings.py` [NEW]

- [ ] **Step 1: 编写嵌入 API 的测试用例（包括 API 故障降级 Fallback）**
  创建 `apps/api/tests/test_embeddings.py`：
  ```python
  import pytest
  from app.llm.openai_compatible import OpenAICompatibleClient
  from app.config import get_settings

  @pytest.mark.asyncio
  async def test_create_embedding_fallback():
      client = OpenAICompatibleClient(get_settings())
      # 测试在无 Key 或异常时的降级
      vec = await client.create_embedding("极限与连续", api_key="invalid_key")
      # 降级时返回空列表或全零向量以做识别，此处我们设计为返回空列表
      assert isinstance(vec, list)
      assert len(vec) == 0
  ```

- [ ] **Step 2: 运行测试并确认失败**
  运行：`pytest apps/api/tests/test_embeddings.py -v`
  预期：FAIL（`create_embedding` 方法未定义）

- [ ] **Step 3: 实现 `create_embedding` 方法**
  修改 `apps/api/app/llm/openai_compatible.py`：
  ```python
  # 导入 httpx 并在类中添加方法
  async def create_embedding(
      self, text: str, api_key: str | None = None, model: str = "text-embedding-3-small"
  ) -> list[float]:
      key = api_key if self.settings.allow_user_api_key and api_key else self.settings.llm_api_key
      if not key:
          return []
      base_url = self.settings.resolve_base_url(self.settings.resolve_model(model))
      url = f"{base_url.rstrip('/')}/embeddings"
      payload = {
          "model": model,
          "input": text
      }
      headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
      try:
          async with httpx.AsyncClient(timeout=10) as client:
              response = await client.post(url, json=payload, headers=headers)
              response.raise_for_status()
              data = response.json()
              return data["data"][0]["embedding"]
      except Exception:
          return []
  ```

- [ ] **Step 4: 运行测试验证通过**
  运行：`pytest apps/api/tests/test_embeddings.py -v`
  预期：PASS

- [ ] **Step 5: 提交代码**
  ```bash
  git add apps/api/app/llm/openai_compatible.py apps/api/tests/test_embeddings.py
  git commit -m "feat: add create_embedding to OpenAI client with fallback support"
  ```

---

### Task 2: 实现本地向量缓存与 BM25/RRF 混合检索

**Files:**
- Create: `apps/api/app/knowledge/vector_store.py`
- Modify: `apps/api/app/knowledge/search.py`
- Test: `apps/api/tests/test_vector_store.py` [NEW]

- [ ] **Step 1: 编写 RAG 混合检索及倒数排名融合的测试**
  创建 `apps/api/tests/test_vector_store.py`：
  ```python
  import pytest
  from app.knowledge.vector_store import LocalVectorStore

  def test_bm25_and_rrf():
      store = LocalVectorStore()
      # 测试文档
      docs = [
          {"id": "doc1", "text": "微积分基本定理描述了微分与积分的关系。"},
          {"id": "doc2", "text": "矩阵特征多项式用来求解矩阵的特征值。"}
      ]
      store.build_bm25_index(docs)
      # 验证 BM25 检索评分结构
      scores = store.score_bm25("特征多项式")
      assert "doc2" in scores
      assert scores["doc2"] > 0
  ```

- [ ] **Step 2: 运行测试确认失败**
  运行：`pytest apps/api/tests/test_vector_store.py -v`
  预期：FAIL（未定义 `LocalVectorStore`）

- [ ] **Step 3: 实现 `LocalVectorStore` 混合检索引擎**
  创建 `apps/api/app/knowledge/vector_store.py`，实现分词、BM25 词频计算、余弦相似度（纯 Python）与 RRF 融合逻辑：
  ```python
  import math
  import re
  from typing import List, Dict

  class LocalVectorStore:
      def __init__(self):
          self.docs = []
          self.tf = {}
          self.df = {}
          self.idf = {}
          self.avg_dl = 0.0

      def _tokenize(self, text: str) -> List[str]:
          parts = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
          return [p for p in parts if len(p) > 1]

      def build_bm25_index(self, docs: List[Dict[str, str]]):
          self.docs = docs
          total_dl = 0
          for doc in docs:
              tokens = self._tokenize(doc["text"])
              total_dl += len(tokens)
              doc_tf = {}
              for token in tokens:
                  doc_tf[token] = doc_tf.get(token, 0) + 1
              self.tf[doc["id"]] = doc_tf
              for token in set(tokens):
                  self.df[token] = self.df.get(token, 0) + 1
          
          self.avg_dl = total_dl / len(docs) if docs else 0
          for token, df_val in self.df.items():
              self.idf[token] = math.log((len(docs) - df_val + 0.5) / (df_val + 0.5) + 1.0)

      def score_bm25(self, query: str, k1: float = 1.5, b: float = 0.75) -> Dict[str, float]:
          query_tokens = self._tokenize(query)
          scores = {}
          for doc in self.docs:
              doc_id = doc["id"]
              doc_tf = self.tf.get(doc_id, {})
              dl = sum(doc_tf.values())
              score = 0.0
              for token in query_tokens:
                  if token not in doc_tf:
                      continue
                  tf_val = doc_tf[token]
                  idf_val = self.idf.get(token, 0.0)
                  numerator = tf_val * (k1 + 1)
                  denominator = tf_val + k1 * (1 - b + b * (dl / self.avg_dl))
                  score += idf_val * (numerator / denominator)
              if score > 0:
                  scores[doc_id] = score
          return scores

      def rrf_merge(self, vector_results: List[str], bm25_results: List[str], k: int = 60) -> List[str]:
          scores = {}
          for rank, doc_id in enumerate(vector_results):
              scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
          for rank, doc_id in enumerate(bm25_results):
              scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
          sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
          return [doc[0] for doc in sorted_docs]

      def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
          dot = sum(a*b for a, b in zip(v1, v2))
          norm1 = sum(a*a for a in v1) ** 0.5
          norm2 = sum(b*b for b in v2) ** 0.5
          return dot / (norm1 * norm2) if norm1 and norm2 else 0.0
  ```

- [ ] **Step 4: 在 `search.py` 中串联 RAG 检索**
  重构 `apps/api/app/knowledge/search.py` 里的 `search_knowledge`：如果 API 可用，加载本地 `embeddings.json` 并调用 `cosine_similarity` 计算与 BM25 进行 RRF 混合排序；不可用则优雅降级为纯关键字打分。

- [ ] **Step 5: 验证测试通过并提交**
  运行：`pytest apps/api/tests/test_vector_store.py -v`
  预期：PASS
  ```bash
  git add apps/api/app/knowledge/vector_store.py apps/api/app/knowledge/search.py apps/api/tests/test_vector_store.py
  git commit -m "feat: implement LocalVectorStore with BM25, Cosine Similarity, and RRF merging"
  ```

---

### Task 3: 构建 LangGraph 工作流拓扑结构

**Files:**
- Modify: `apps/api/pyproject.toml`
- Create: `apps/api/app/tutor/graph.py` [NEW]
- Test: `apps/api/tests/test_agent_graph.py` [NEW]

- [ ] **Step 1: 添加 `langgraph` 依赖项**
  修改 `apps/api/pyproject.toml`，在 `dependencies` 中追加：
  ```toml
  "langgraph",
  "langchain-core"
  ```
  执行安装命令验证依赖：
  ```bash
  pip install langgraph langchain-core
  ```

- [ ] **Step 2: 编写 LangGraph 状态图连接测试**
  创建 `apps/api/tests/test_agent_graph.py`：
  ```python
  import pytest
  from app.tutor.graph import compile_tutor_graph

  def test_graph_compile():
      app = compile_tutor_graph()
      assert app is not None
      # 验证编译好的 Graph 结构中包含节点
      assert "intent_node" in app.nodes
      assert "orchestrator_node" in app.nodes
  ```

- [ ] **Step 3: 运行测试确认失败**
  运行：`pytest apps/api/tests/test_agent_graph.py -v`
  预期：FAIL（未定义 `compile_tutor_graph`）

- [ ] **Step 4: 实现 `AgentState` 与节点拓扑**
  创建 `apps/api/app/tutor/graph.py`，编排 StateGraph 并设置 `add_messages` 与 `thinking_steps` 累加逻辑：
  ```python
  import operator
  from typing import TypedDict, Annotated, List, Optional
  from langgraph.graph import StateGraph, END
  from langgraph.graph.message import add_messages
  from langchain_core.messages import BaseMessage

  class AgentState(TypedDict):
      messages: Annotated[list[BaseMessage], add_messages]
      intent: str
      subject: str
      concepts: List[str]
      verifier_result: Optional[dict]
      mistake: Optional[dict]
      thinking_steps: Annotated[list[dict], operator.add]

  def intent_node(state: AgentState):
      # 静态意图与学科提取
      return {"intent": "CHECK_STEP", "thinking_steps": [{"step": "intent_detect", "status": "success", "content": "确认用户意图"}]}

  def orchestrator_node(state: AgentState):
      # 模型决策
      return {"thinking_steps": [{"step": "orchestrator", "status": "success", "content": "分析步骤"}]}

  def rag_node(state: AgentState):
      return {"thinking_steps": [{"step": "rag_tool", "status": "success", "content": "检索完成"}]}

  def sandbox_node(state: AgentState):
      return {"thinking_steps": [{"step": "sandbox_tool", "status": "success", "content": "执行成功"}]}

  def pedagogy_node(state: AgentState):
      return {"thinking_steps": [{"step": "pedagogy", "status": "success", "content": "教学评价完毕"}]}

  def should_continue(state: AgentState) -> str:
      return "pedagogy"

  def compile_tutor_graph():
      workflow = StateGraph(AgentState)
      workflow.add_node("intent_node", intent_node)
      workflow.add_node("orchestrator_node", orchestrator_node)
      workflow.add_node("rag_node", rag_node)
      workflow.add_node("sandbox_node", sandbox_node)
      workflow.add_node("pedagogy_node", pedagogy_node)

      workflow.set_entry_point("intent_node")
      workflow.add_edge("intent_node", "orchestrator_node")
      workflow.add_conditional_edges(
          "orchestrator_node",
          should_continue,
          {
              "rag": "rag_node",
              "sandbox": "sandbox_node",
              "pedagogy": "pedagogy_node"
          }
      )
      workflow.add_edge("rag_node", "orchestrator_node")
      workflow.add_edge("sandbox_node", "orchestrator_node")
      workflow.add_edge("pedagogy_node", END)
      
      return workflow.compile()
  ```

- [ ] **Step 5: 验证并提交代码**
  运行：`pytest apps/api/tests/test_agent_graph.py -v`
  预期：PASS
  ```bash
  git add apps/api/pyproject.toml apps/api/app/tutor/graph.py apps/api/tests/test_agent_graph.py
  git commit -m "feat: construct LangGraph AgentState and SateGraph schema"
  ```

---

### Task 4: 替换 Orchestrator 核心并推送流式 Trace 事件

**Files:**
- Modify: `apps/api/app/tutor/orchestrator.py`
- Modify: `apps/api/app/api/routes_tutor.py`

- [ ] **Step 1: 接入 `astream_events` 到 Orchestrator 中**
  在 `apps/api/app/tutor/orchestrator.py` 中，使用编译好的 LangGraph 实例重构 `stream_reply`。
  使用 `async for event in graph.astream_events(..., version="v2")` 监听状态流转：
  - 当节点启动时，推送对应的结构化 SSE 事件：`yield sse("trace", {"step": node_name, "status": "running"})`
  - 当节点运行成功，推送事件：`yield sse("trace", {"step": node_name, "status": "success", "content": ...})`
  - 推送中间 Token 时使用：`yield sse("token", {"text": token})`

- [ ] **Step 2: 实地调测路由接口响应**
  启动 FastAPI 进程，向 `/api/tutor/stream` 发起请求，确保返回的数据流中包含符合 Spec 规划的 `event: trace` 元数据块。

- [ ] **Step 3: 提交修改**
  ```bash
  git add apps/api/app/tutor/orchestrator.py apps/api/app/api/routes_tutor.py
  git commit -m "feat: plug LangGraph astream_events into orchestrator and stream structured trace SSE events"
  ```

---

### Task 5: 前端对接结构化 Trace 并完成 Timeline 渲染

**Files:**
- Modify: `apps/web/components/tutor-chat.tsx`
- Modify: `apps/web/components/math-message.tsx`

- [ ] **Step 1: 在前端 API 解析 `trace` 事件**
  修改 `apps/web/lib/api.ts` 的流式接收逻辑：
  增加 `onTrace` 回调：
  ```typescript
  export async function streamTutor(
      payload: TutorStreamRequest,
      onMeta: (meta: TutorMeta) => void,
      onToken: (token: string) => void,
      onTrace?: (trace: any) => void
  )
  ```
  在 `EventSource`/`fetch` 读取管道中，捕获 `event: trace` 并回调 `onTrace`。

- [ ] **Step 2: 绑定 Trace 状态到消息气泡**
  修改 `apps/web/components/tutor-chat.tsx`：
  - 维护一个本地 state 数组或在消息对象中追加 `traceSteps` 字段。
  - 调用 `streamTutor` 时传入 `onTrace`，将接收到的结构化步骤追加进去。

- [ ] **Step 3: 重构 Timeline 并使用 Lucide 渲染 Icons**
  修改 `apps/web/components/math-message.tsx`：
  - 重构 `<ThinkingChain />`。当展开思考轨迹时，按纵向 Timeline 连接渲染 `traceSteps`。
  - `intent_detect` 渲染罗盘/定位 Icon，`rag_tool` 渲染 `Search` Icon，`sandbox_tool` 渲染 `Terminal` 终端窗口。
  - 处理代码运行报错，当出现错误状态时，高亮显示错误信息。

- [ ] **Step 4: 进行端到端联调测试**
  在网页端发送“我想算 \int x^2 dx = x^3”，展开“查看思考过程”，确认步骤渲染出精美的时间轴、终端代码块。

- [ ] **Step 5: 提交前端代码**
  ```bash
  git add apps/web/lib/api.ts apps/web/components/tutor-chat.tsx apps/web/components/math-message.tsx
  git commit -m "feat: render gorgeous interactive agent trace timeline in math message bubble"
  ```
