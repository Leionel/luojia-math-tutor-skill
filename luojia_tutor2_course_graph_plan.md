# 珞珈数智助教 2.0：课程知识图谱与动态教学知识层方案

> 项目仓库：`Leionel/luojia-math-tutor-skill`  
> 首个试点课程：《数值分析》  
> 首个建议试点单元：非线性方程求根（Bisection / Fixed Point / Newton）  
> 文档用途：统一当前知识图谱、问题归并、动态扩展、学生状态叠加与后续 Tutor 2.0 开发方案。

---

## 1. 背景与核心结论

当前项目已经具备较完整的 Tutor 通用底座，包括 FastAPI + SSE、LangGraph 条件式教学工作流、`KnowledgeUnit / KnowledgeRelation / EvidencePack`、RAG、SymPy、BKT、Proof Tutor、React Flow 知识图谱和 LuojiaMathBench 等。

因此 2.0 不建议重新搭一个“数值分析助手”，也不建议把每个学生问题直接写进知识图谱。更合理的核心原则是：

> **Query is Evidence, Case is Abstraction, Knowledge Unit is Ontology.**

中文即：

> **学生问题是交互证据；教学案例是归纳层；知识节点才是课程知识本体。**

---

## 2. 为什么不能把学生问题直接作为知识节点

例如学生可能分别问：

- “牛顿迭代法收敛吗？”
- “Newton 法什么时候收敛？”
- “为什么初值要靠近根？”
- “牛顿法为什么有时候发散？”

这些问法不同，但大多围绕同一组稳定课程知识：

- Newton Method；
- Local Convergence；
- Initial Guess；
- Simple Root；
- Derivative Condition。

如果每个问题都生成知识节点，图谱会迅速退化成“问句图”，而不是课程知识图谱。

因此应采用：

```text
Raw Query
   ↓
Canonical Teaching Case
   ↓
Knowledge Units
```

---

## 3. 总体知识架构

建议 Tutor 2.0 的知识系统分为五层：

```text
┌──────────────────────────────────────────────┐
│                课程资料层                    │
│ 教材 / 讲义 / 老师网站 / 代码 / 习题 / 答案 │
└───────────────────┬──────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ ① Canonical Course Graph                     │
│ 教师认可、版本化的正式课程知识图谱           │
└───────────────────┬──────────────────────────┘
                    │
          ┌─────────┴─────────┐
          ↓                   ↓
┌───────────────────┐  ┌──────────────────────┐
│ ② Teaching Cases  │  │ ③ Candidate Graph    │
│ 教学案例 / 任务层 │  │ 动态候选节点 / 边    │
└─────────┬─────────┘  └──────────┬───────────┘
          ↑                       │
          │                  Teacher Review
┌─────────┴─────────┐             │
│ ④ Query / Attempt │             └──→ Course Graph
│ 学生问题与过程    │
└─────────┬─────────┘
          │
          ↓
┌──────────────────────────────────────────────┐
│ ⑤ Student Overlay                            │
│ mastery / error / hint / revision / history  │
└──────────────────────────────────────────────┘
```

其中：

- **Canonical Course Graph**：正式课程知识真相；
- **Teaching Case**：教学问题抽象；
- **Candidate Graph**：动态扩展候选，不直接污染正式图；
- **Query / Attempt**：保存真实学生交互；
- **Student Overlay**：保存学生在课程图谱上的状态。

---

## 4. Canonical Course Graph：正式课程知识图谱

### 4.1 定位

Canonical Course Graph 回答：

> “这门课程有哪些稳定知识？知识之间是什么关系？边界在哪里？”

例如 Newton 法不应只是一个节点，而应形成：

```text
Taylor Expansion
      │ prerequisite
      ↓
Newton Method
      │
      ├─ requires ───────→ Simple Root
      ├─ requires ───────→ f'(x*) ≠ 0
      ├─ converges_if ───→ Local Conditions
      ├─ has_property ───→ Quadratic Convergence
      ├─ implemented_by ─→ Newton Code
      └─ misconception ←── Arbitrary initial point always converges
```

### 4.2 课程边界

建议为 `KnowledgeUnit` 增加：

```text
scope_level:
    core
    prerequisite
    extension
    external
```

示例：

| Knowledge Unit | Scope |
|---|---|
| Newton 求根法 | core |
| Taylor 展开 | prerequisite |
| 优化中的 Newton 法 | extension |
| BFGS / Quasi-Newton | external |

Tutor 可按边界控制扩展：

```text
核心课程问题
→ core + prerequisite

学生主动追问
→ 可进入 extension

明显超出
→ 提示超出课程核心范围
```

这使“课程专用 Tutor”真正有知识边界，而不是只在 Prompt 中写“你是数值分析老师”。

---

## 5. Teaching Case：教学问题抽象层

### 5.1 为什么需要 Teaching Case

多个 Query 可能对应同一个教学目标，但不应因此把知识节点重复创建。

例如：

```text
Q1：牛顿法什么时候收敛？
Q2：Newton iteration 的收敛条件是什么？
Q3：为什么初值要足够接近根？
```

可以归并到：

```text
CASE_NEWTON_LOCAL_CONVERGENCE
```

再关联：

```text
Newton Method
Local Convergence
Initial Guess
Simple Root
Derivative Condition
```

### 5.2 推荐结构

```python
CanonicalTeachingCase:
    case_id
    title
    task_type
    concept_ids
    required_conditions
    reasoning_signature
    misconception_candidates
    difficulty
    canonical_prompts
    review_status
```

### 5.3 三类对象的边界

| 对象 | 回答的问题 |
|---|---|
| Query | 学生这次具体问了什么 |
| Teaching Case | 这是什么类型的教学问题 |
| KnowledgeUnit | 课程中稳定存在什么知识 |

---

## 6. Query / Attempt：只保存真实交互

建议新增：

```python
QueryRecord:
    query_id
    user_id
    session_id
    raw_text
    normalized_text
    intent
    task_type
    concept_anchors
    canonical_case_id
    created_at
```

示例：

```text
raw_text:
“牛顿迭代为什么有时候会爆掉？”

intent:
WHY_FAILURE

canonical_case:
CASE_NEWTON_DIVERGENCE

concept_anchors:
Newton Method
Initial Guess
Derivative
Convergence Condition
```

这样以后即使积累大量不同表述，也不会形成大量重复知识节点。

---

## 7. 相似问题判定不能只做文本去重

例如：

```text
A：牛顿法什么时候二阶收敛？
B：重根情况下牛顿法是什么收敛阶？
```

文本很像，但核心条件不同：

```text
A → simple root
B → multiple root
```

因此建议三级判定：

```text
New Query
   ↓
① Retrieval
   BM25 / Embedding / Existing Cases
   ↓
② Structural Match
   concept anchors
   task type
   conditions
   reasoning signature
   ↓
③ Semantic Judge
```

最终输出：

```text
SAME_CASE
VARIANT_OF_CASE
RELATED_CASE
NEW_CASE
UNCERTAIN
```

而不是简单 `duplicate=true/false`。

判断依据建议按以下顺序：

1. 教学目标是否相同；
2. 必要知识点是否相同；
3. 条件集合是否相同；
4. 推理路径是否大体一致；
5. 误解诊断空间是否一致。

---

## 8. Dynamic Candidate Graph：动态图谱的正确实现

### 8.1 不建议

```text
学生问到新内容
→ 自动永久写入 Course Graph
```

这种设计容易导致：

- 节点污染；
- 重复；
- 课程边界漂移；
- LLM 错误关系永久化；
- 教师无法控制知识体系。

### 8.2 推荐流程

```text
Student Query
      ↓
Course Graph Retrieval
      ↓
Graph insufficient
      ↓
Candidate Node / Edge
      ↓
Session / Personal Overlay
      ↓
accumulate evidence
      ↓
Teacher Review
      ↓
Approve / Merge / Reject
      ↓
Canonical Course Graph
```

例如学生问：

> “Newton 求根法和优化里的 Newton Method 有什么关系？”

可以生成：

```text
Candidate Unit:
Newton Optimization

scope:
extension

review_status:
draft
```

候选关系：

```text
Newton Root Finding
    ─ related_to →
Newton Optimization
```

教师决定是否批准、合并、拒绝或仅保留为个人扩展。

---

## 9. Student Overlay：学生图谱不是另一套知识图

不建议再建立独立 Student Knowledge Graph。

更合理：

\[
G_{student}=G_{course}+S_{student}
\]

Course Graph：

```text
Taylor
  ↓
Fixed Point
  ↓
Newton
  ↓
Convergence Rate
```

Student Overlay：

```text
Taylor              mastered
Fixed Point         mastered
Newton              learning
Convergence Rate    weak
```

现有 BKT 可继续作为基础 mastery estimator。

后续再逐步增加：

- current task state；
- misconception evidence；
- hint exposure；
- revision history；
- task-specific error streak；
- global struggle signal。

但不应在没有真实纵向数据前过早建立复杂的高维学生画像。

---

## 10. 类似问题应该复用什么

不建议直接做：

```text
Question → Cached Answer
```

建议复用：

```text
Teaching Case
```

例如：

```text
CASE_NEWTON_DIVERGENCE

Graph Anchors:
- Newton Method
- Initial Guess
- Derivative
- Convergence Condition

Possible Causes:
- initial point unsuitable
- derivative near zero
- multiple root
- stopping condition bug
- implementation error

Diagnostic Probes:
- 检查 f'(x_n)
- 查看 iteration trace
- 检查 residual
- 对比 reference run

Teaching Actions:
- Probe
- Hint
- Counterexample
- Numerical Experiment
```

不同学生可以复用同一 Case，但依据学生状态选择不同教学行为。

---

## 11. 与现有项目架构的对接

### 11.1 保留现有底座

继续保留：

```text
FastAPI
SSE
LangGraph
Teacher
Proof Tutor
Examiner
Verifier
BKT
KnowledgeUnit
KnowledgeRelation
EvidencePack
React Flow
LuojiaMathBench
```

### 11.2 重点改造

#### A. Knowledge Schema

建议新增：

```text
scope_level
origin
visibility
version
approved_by
```

推荐：

```text
scope_level:
core / prerequisite / extension / external

origin:
teacher / textbook / llm_candidate / student_query / external_resource

visibility:
canonical / candidate / personal
```

#### B. Graph API

```text
GET /courses/{course_id}/graph

GET /courses/{course_id}/graph/subgraph
    ?concept_id=
    ?depth=
    ?relation_types=

GET /users/{user_id}/course-graph
```

前端只负责渲染，后端 Course Graph 才是真实数据源。

#### C. Teacher Review

教师端至少支持：

```text
Approve Candidate Node
Merge Candidate Node
Reject Candidate Node
Edit Node
Add Edge
Remove Edge
Change Scope
```

并保留：

```text
who
when
why
source
version
```

#### D. Tutor Retrieval

由：

```text
Query
→ text retrieval
→ graph one-hop
```

升级为：

```text
Query
→ Case Retrieval
→ Concept Anchoring
→ Course Boundary Filter
→ Relation-aware Expansion
→ Evidence Pack
```

特别是定理、收敛性等问题必须同时召回：

```text
claim + conditions + prerequisites
```

---

## 12. 数值分析首单元建议结构

建议第一阶段只做：

```text
Bisection
Fixed Point Iteration
Newton Method
```

### 12.1 Canonical Knowledge Units

至少包含：

```text
Root Finding
Intermediate Value Theorem
Bisection
Fixed Point
Contraction Mapping
Newton Method
Taylor Expansion
Local Convergence
Convergence Order
Simple Root
Multiple Root
Residual
True Error
Stopping Criterion
Floating Point Error
```

### 12.2 Code Units

```text
Bisection Implementation
Fixed Point Implementation
Newton Implementation
Reference Runner
Stopping Conditions
```

### 12.3 Misconception Units

```text
Residual = True Error
Newton always converges
More iterations always improve accuracy
High-order method always better
Converged flag = mathematical convergence proof
```

---

## 13. 与已有学术 / 开源经验的对应

### OATutor

借鉴：

- skill / step / hint；
- 学习日志；
- BKT；
- 教学实验组织方式。

不建议迁移整套技术栈。

### KITE / Course-aware RAG Tutor

借鉴：

- 课程资料 grounding；
- intent-aware tutoring；
- revision evaluation。

本项目需要进一步做深数值条件、数值实验与数学—算法—代码跨表示诊断。

### EduGuard

借鉴：

- teacher-curated corpus；
- claim grounding；
- response guard。

注意文本 entailment 不能替代数学与数值验证。

### StatusKT

借鉴：

- 从 problem-solving process 中提取学生证据。

原则：只记录可观察行为，不把模型猜测的“学生心理状态”直接当真值。

### LongTutor

借鉴：

```text
Evidence Acquisition
→ State Diagnosis
→ Teaching Action
```

但长期学生模型应后置，先把过程事件记录稳定。

### Misconception Diagnosis / Generate-Retrieve-Rerank

借鉴：

```text
Generate Candidates
→ Retrieve
→ Rerank
```

本项目应输出多候选、支持证据、反证和诊断性追问，而不是一步给唯一“误解标签”。

### MalruleLib

借鉴：

- executable misconception；
- positive/negative traces；
- cross-template evaluation。

数值分析版本可进一步区分：

```text
mathematical condition error
algorithm error
implementation error
floating-point error
stopping-condition error
interpretation error
```

### SciCode / SciCode-Verified

借鉴：

- executable oracle；
- tolerance audit；
- benchmark 自身也必须验证。

### StratL / Evidence-Decision-Feedback

借鉴：

```text
evidence
→ pedagogical decision
→ feedback
```

说明 Teaching Case 不应绑定固定回答，而应绑定 possible actions、constraints 和 diagnostic probes。

---

## 14. LuojiaMathBench 对应升级

### 14.1 Query → Case

指标：

```text
Case Retrieval Recall@K
Case Classification Accuracy
Variant Detection Accuracy
```

### 14.2 Query → Knowledge Graph

```text
Concept Anchor Recall
Required Condition Recall
Relation Recall
```

### 14.3 Boundary

```text
Boundary Precision
Boundary Violation Rate
Unnecessary Expansion Rate
```

### 14.4 Dynamic Candidate

```text
duplicate candidate rate
teacher approval rate
merge rate
false expansion rate
```

### 14.5 Teaching

最终仍需要测：

```text
student revision
self-correction
unaided transfer
```

不能把“图谱召回更高”直接等价成“学生学得更好”。

---

## 15. 开发优先级

### P0：当前必须做

1. 保持现有仓库继续开发，不另开全新项目；
2. 新建 Tutor 2.0 feature branch；
3. 接入老师《数值分析》课程资料；
4. 建立课程边界；
5. 统一 KnowledgeUnit / KnowledgeRelation 元数据；
6. 建立正式 Course Graph API；
7. 前端取消 hard-coded graph 作为真实数据源；
8. 增加 Teaching Case 数据层；
9. 实现 Query → Case → Concept 基础映射；
10. Teacher Review 基础能力；
11. BKT 映射到稳定 `knowledge_unit_id`。

### P1：首轮闭环完成后

1. Candidate Graph；
2. SAME / VARIANT / RELATED / NEW / UNCERTAIN 分类；
3. Context Subgraph；
4. Similar Teaching Case reuse；
5. 图谱 benchmark；
6. 数值 verifier 与 Case 联动；
7. misconception hypothesis 与 Case 联动；
8. Student Overlay 可视化。

### P2：有真实使用数据后

1. 根据高频 Query 自动推荐知识扩展；
2. personalized path planning；
3. 更复杂 Student Model；
4. automatic graph refinement；
5. longitudinal KT；
6. StudentSim / RL；
7. 跨课程知识网络。

---

## 16. 暂时不要做

目前不建议：

- Neo4j 大迁移；
- 全课程一次性建图；
- 每个 Query 自动永久建节点；
- 多 Agent 自由讨论决定图谱；
- 全自动 LLM ontology generation；
- 为每个学生复制一张完整知识图；
- 八级帮助策略与动态图谱同时大改；
- 为“动态图谱”引入复杂 GNN；
- 把 embedding 相似度直接当 duplicate 判定。

当前最重要的是：

> **稳定 ontology、课程边界、Teaching Case 中间层和教师审核闭环。**

---

## 17. 建议 Repo 组织方式

继续使用现有仓库。

建议逐步整理为：

```text
apps/api/app/
├─ knowledge/
│  ├─ schema.py
│  ├─ course_graph.py
│  ├─ graph_service.py
│  ├─ candidate_graph.py
│  ├─ case_repository.py
│  ├─ case_matcher.py
│  ├─ boundary.py
│  └─ review.py
│
├─ tutor/
│  ├─ orchestrator.py
│  ├─ graph.py
│  ├─ fast_context.py
│  ├─ policy.py
│  └─ ...
│
├─ courses/
│  └─ numerical_analysis/
│     ├─ manifest.json
│     ├─ units/
│     ├─ relations/
│     ├─ cases/
│     ├─ misconceptions/
│     └─ code_tasks/
│
└─ benchmark/
   └─ numerical_analysis/
```

前端：

```text
apps/web/
├─ app/
│  ├─ graph/
│  └─ admin/knowledge/
│
└─ components/
   ├─ knowledge-graph.tsx
   ├─ context-subgraph.tsx
   └─ candidate-review.tsx
```

不要求一次性重构，重点是形成清晰模块边界。

---

## 18. 最终定义

Tutor 2.0 的知识层不应被定义成：

> “一个能动态增加节点的知识图谱”。

更准确的定义是：

> **一个以教师审核课程图谱为正式知识本体，以 Teaching Case 归纳学生问题，以 Candidate Graph 承载动态扩展，以 Student Overlay 描述个人学习状态，并通过 Evidence Pack 向 Tutor 提供受课程边界约束的教学证据系统。**

最终教学链路：

```text
Student Query / Attempt
          ↓
Query Normalization
          ↓
Teaching Case Matching
          ↓
Course Knowledge Anchoring
          ↓
Boundary-aware Graph Retrieval
          ↓
Evidence / Verification
          ↓
Diagnosis
          ↓
Teaching Policy
          ↓
Tutor Response
          ↓
Student Revision
          ↓
Process Event
          ↓
Student Overlay Update
```

知识演化链路：

```text
Student Query
     ↓
Existing Course Graph insufficient?
     ↓ yes
Candidate Node / Edge
     ↓
Accumulate Evidence
     ↓
Teacher Review
     ↓
Approve / Merge / Reject
     ↓
New Course Graph Version
```

---

## 19. 当前阶段应坚持的原则

1. **Course Graph 是课程知识，不是问题日志。**
2. **Query 不直接成为 KnowledgeUnit。**
3. **Teaching Case 是 Query 与知识图谱之间的关键中间层。**
4. **动态知识先进入 Candidate Layer，再经教师审核。**
5. **学生个性化通过 Overlay 实现，而不是复制课程图谱。**
6. **课程边界必须成为数据属性，而不是一句 Prompt。**
7. **复用的是教学案例与诊断结构，不是固定最终答案。**
8. **Graph Retrieval 要检索结论，也要检索适用条件。**
9. **动态图谱首先解决教学组织与证据问题，不急于包装成算法创新。**
10. **所有设计最终都要回到学生修订、迁移和真实学习结果上。**

---

## 20. 一句话总结

> **珞珈数智助教 2.0 应从“RAG + 可视化知识图谱”升级为“教师定义课程本体、学生问题归纳为教学案例、交互产生候选知识扩展、个人状态叠加于课程图谱之上”的课程级 AI Tutor 知识基础设施。**
