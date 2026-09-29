# 珞珈数智助教 2.0：课程知识图谱、Teaching Case 与动态知识演化的细化调研

> **项目仓库**：`Leionel/luojia-math-tutor-skill`  
> **试点课程**：《数值分析》  
> **首单元建议**：非线性方程求根（Bisection / Fixed Point / Newton）  
> **调研目的**：不是重新设计一个 AI Tutor，而是在现有 Tutor 2.0 与已有研究基础上，回答“课程知识应该如何组织、学生问题如何归并、知识图谱如何动态演化、学生状态如何叠加、这些结构如何服务 Tutor 与后续研究”。
>
> 本文将严格区分：
>
> - **[项目现状]**：当前公开仓库或此前代码审查中已经存在的能力；
> - **[文献/开源证据]**：已有论文或官方 GitHub 能支持的设计经验；
> - **[方案建议]**：针对珞珈数智助教 2.0 的新增设计，不把工程选择包装成已有研究结论。

---

## 0. 先给结论

本轮调研后，推荐把原来较泛的：

```text
Knowledge Graph + RAG + Student State + Tutor
```

收敛为：

```text
Teacher-curated Course Pack
        ↓
Canonical Course Graph
        ↓
Query → Teaching Case → Knowledge Anchors
        ↓
Boundary-aware Evidence Retrieval
        ↓
Verifier / Diagnosis / Teaching Policy
        ↓
Student Revision
        ↓
Process Event
        ↓
Student Overlay
```

同时引入一条独立的知识演化链：

```text
Student Query
    ↓
现有 Course Graph 是否足够？
    ↓ No
Candidate Node / Edge / Case
    ↓
积累来源与使用证据
    ↓
Teacher Review
    ↓
Approve / Merge / Reject / Keep-as-extension
    ↓
New Course Graph Version
```

核心原则仍然是：

> **Query is Evidence, Case is Abstraction, Knowledge Unit is Ontology.**

也就是：

> **问题是交互证据，Teaching Case 是教学问题的抽象层，Knowledge Unit 才是正式课程知识本体。**

这一层划分是本文最重要的新增设计。

---

# 1. 为什么这次要把“知识层”重新设计

## 1.1 当前项目其实已经不缺一个普通 RAG

[项目现状]

当前公开仓库已有：

- `SourceDocument`
- `KnowledgeUnit`
- `KnowledgeRelation`
- `EvidencePack`
- 本地检索与图关系扩展
- React Flow 图谱展示
- BKT 掌握度
- LangGraph Tutor workflow
- Proof / Teacher / Examiner / Verifier 等分支

因此现在的主要问题不是：

> “怎么把文档切片以后丢进向量数据库？”

而是：

1. 什么才算课程里的稳定知识？
2. 一个学生问句是否应该成为图节点？
3. 两个相似问题怎样判断是同一个教学问题还是不同问题？
4. 课程知识边界怎样显式表示？
5. 学生不断追问产生的新知识怎样进入图谱？
6. 教师怎样控制自动扩展？
7. 学生掌握度应该挂在哪里？
8. 知识图谱怎样真正改变 Tutor 的诊断和教学，而不是只做可视化？

---

## 1.2 这和“动态知识图谱”不是一回事

如果简单采用：

```text
学生问新问题
→ LLM 总结一句
→ 建一个新节点
```

很快会得到：

```text
牛顿法收敛吗？
牛顿法什么时候收敛？
Newton 法收敛条件
Newton 初值为什么重要？
牛顿法为什么发散？
……
```

这不是知识图谱，而是问句集合。

真正需要动态变化的是：

- **候选知识**
- **教学案例**
- **课程边界扩展**
- **学生状态**

而不是让正式 Course Graph 无门槛地随聊天增长。

---

# 2. 已有研究和开源项目分别告诉了我们什么

以下不按“论文综述”罗列，而是按它们对本项目设计产生的实际影响组织。

---

## 2.1 OATutor：稳定 Skill Model 比动态问句节点更重要

### 文献 / 仓库

- OATutor: An Open-source Adaptive Tutoring System and Curated Content Library for Learning Sciences Research, CHI 2023
- GitHub: `CAHLR/OATutor`
- Content: `CAHLR/OATutor-Content`

### 已有经验

OATutor 把 Tutor 的基础建立在：

- centralized skill model；
- curated problems / hints / scaffolds；
- BKT；
- adaptive item selection；
- interaction logging。

其内容库和平台代码也是分开的。

### 对我们最重要的启示

课程知识结构应该是相对稳定的：

```text
Skill / KC
Problem
Hint
Scaffold
Student State
```

而不是让每个学生自然语言问句直接改变 ontology。

### 本项目对应决策

保留：

```text
Canonical Course Graph
```

作为正式课程知识。

学生个性化不复制一张新图，而是：

```text
Course Graph + Student Overlay
```

---

## 2.2 MathTutorBench：解题能力和 Tutor 能力必须拆开评

### 文献 / 仓库

- MathTutorBench: A Benchmark for Measuring Open-ended Pedagogical Capabilities of LLM Tutors
- EMNLP 2025
- GitHub: `eth-lre/mathtutorbench`

### 已有经验

公开 benchmark 将 Tutor 能力拆成多个任务，包括：

- problem solving；
- Socratic questioning；
- student solution correctness；
- mistake location；
- mistake correction；
- scaffolding generation；
- pedagogy following。

核心经验是：

> 强 solver 不必然是强 tutor。

### 对我们的启示

`Teaching Case` 不能只是“标准答案缓存”。

它应该说明：

```text
这是什么教学任务？
学生现在在哪一步？
哪些行为是可接受的？
哪些知识和条件必须出现？
Tutor 下一步可以做什么？
```

因此 Teaching Case 更接近：

```text
pedagogical task schema
```

而不是 FAQ。

### 对 LuojiaMathBench 的影响

以后可以分别测：

```text
Query → Case
Case → Knowledge Anchor
Case → Diagnosis
Case + Evidence → Teaching Action
```

而不能只测最终回答质量。

---

## 2.3 StatusKT：Student State 应来自解题过程，而不是聊天印象

### 文献 / 仓库

- Tracing Mathematical Proficiency Through Problem-Solving Processes
- Findings ACL 2026
- GitHub: `jungyangpark/KT-PSP-25`

### 已有经验

StatusKT 强调：

> 只看 correct / incorrect 会丢失大量学生解题过程信息。

其公开实现将 problem-solving process 用于提取数学能力信号，并与 KT 结合。

### 不能直接照搬的地方

StatusKT 的 Mathematical Proficiency 维度和数据来自其特定数学数据集。

不能直接给数值分析学生显示：

```text
Adaptive Reasoning = 0.73
Strategic Competence = 0.64
```

然后当成可靠真值。

### 本项目建议

近期只记录可观察事实：

```text
attempt
claim
code snapshot
numerical trace
hint exposure
revision
independent probe
```

然后让：

```text
BKT / future process model
```

成为这些事件的一个 view。

也就是说：

> **先存 evidence，再建 student model。**

---

## 2.4 LongTutor：历史信息要服务“证据获取 → 诊断 → 教学”，不是单纯塞聊天记录

### 文献 / 仓库

- LongTutor: Benchmarking Large Language Models for Long-term Personalized Tutoring
- ACL 2026
- GitHub: `liano3/LongTutor`

### 已有经验

LongTutor 把长期 tutoring 拆成：

```text
history evidence
→ diagnosis
→ teaching content
```

公开仓库也明确组织：

- student interaction sequences；
- history features；
- human annotations；
- memory / diagnosis / teaching evaluation。

### 对我们最重要的启示

Student Overlay 不应该变成：

```text
把最近 100 条聊天摘要塞给模型
```

而应该能够回答：

```text
当前问题相关的历史证据是什么？
学生以前是否在相同 KC 上出现过相同错误？
之前用了多少帮助？
之后有没有独立完成？
```

### 对我们的结构影响

新增：

```text
Event Store
↓
State Reducer
↓
Course/KC/Case-specific Student Overlay
```

而不是直接维护一个模型自行更新的“学生人格描述”。

---

## 2.5 Misconception Diagnosis / Generate-Retrieve-Rerank：不要过早唯一归因

### 文献

- Misconception Diagnosis From Student-Tutor Dialogue: Generate, Retrieve, Rerank
- 2026

### 已有经验

误解诊断存在两个重要问题：

1. misconception 本身可能有粒度和定义歧义；
2. 多个 misconception 可能产生类似错误结果。

因此工作采用候选生成、检索、重排，而不是只做硬分类。

### 对本项目的直接影响

不能：

```text
student error
→ misconception = M017
```

而应该：

```text
Observed Error
→ Candidate Hypotheses
→ support
→ counterevidence
→ missing evidence
→ diagnostic probe
```

例如 Newton 不收敛：

```text
H1: 初值不合适
H2: 导数接近 0
H3: 多重根
H4: 实现 bug
H5: 只是停止条件写错
```

此时 Teaching Case 的一个重要作用，就是提供：

```text
可区分这些 hypothesis 的 probe
```

---

## 2.6 MalruleLib：错误应该可以“执行”和跨模板验证

### 文献 / 仓库

- MalruleLib: Large-Scale Executable Misconception Reasoning with Step Traces for Modeling Student Thinking in Mathematics

### 已有经验

其重要思想不是“多做几个错误标签”，而是：

> 把错误规则变成可执行过程，并观察错误如何沿步骤传播。

### 对数值分析更有价值

数值分析可以天然建立可执行错误：

```text
错误停止条件
错误区间更新
漏检查 f'(x)
错误 Newton update
把 residual 当 error
忽略 multiple root
```

因此我们应让：

```text
Misconception / Error Family
```

与：

```text
Teaching Case
Numerical Oracle
Code Test
```

建立关系。

但要明确：

> executable error ≠ 已证明某个真实学生具有对应稳定 misconception。

---

## 2.7 Confirming Correct：合法替代路径必须是一等公民

### 文献

- Confirming Correct, Missing the Rest: LLM Tutoring Agents Struggle Where Feedback Matters Most
- BEA 2026

### 已有经验

LLM Tutor 的典型风险包括：

- 错误拒绝合法但非标准的路径；
- 接受看似接近参考答案但实际错误的步骤。

### 对 Teaching Case 的直接要求

每个 Case 不应该只保存一个 `reference_solution`。

需要保存：

```text
required_conditions
accepted_variants
allowed_alternatives
forbidden_shortcuts
unknown cases
```

因此：

```text
same final answer
```

不意味着 same case，

而：

```text
different reasoning wording
```

也不意味着 different case。

---

## 2.8 StratL / Evidence-Decision-Feedback：Case 不能绑定固定回答

### 文献 / 开源

- Towards the Pedagogical Steering of Large Language Models for Tutoring
- StratL
- Findings ACL 2025
- GitHub: `RomainPuech/StratL-Pedagogical-Steering-of-LLMs-for-Tutoring`

以及：

- Evidence-Decision-Feedback: Theory-Driven Adaptive Scaffolding for LLM Agents
- AIED 2026

### 已有经验

教学策略更适合表示为：

```text
state/evidence
→ pedagogical decision
→ feedback
```

而不是：

```text
question
→ canned answer
```

### 对我们的 Teaching Case 定义

Case 应存：

```text
diagnostic probes
possible actions
promotion/escalation rules
disclosure constraints
exit conditions
```

而不是一条标准 Tutor 回复。

---

## 2.9 Answer Withholding / EduGuard：课程模式与披露边界必须显式化

### 已有经验

已有工作已经说明：

- “不要直接给答案”不能只靠一句 prompt；
- course-aware RAG + policy + guard 不是全新的系统概念；
- 不同任务模式对答案披露要求不同。

### 本项目决定

Teaching Case / TaskSpec 中显式加入：

```text
task_mode
disclosure_policy
protected_solution
student_known_values
solution_release_allowed
```

例如：

```text
concept_explanation
→ 可以直接解释概念

independent_practice
→ 默认逐步帮助

worked_example
→ 可展示完整示例

assessment
→ 严格限制
```

---

## 2.10 SciCode / SciCode-Verified：Oracle 自己也必须被审计

### 文献 / 仓库

- SciCode, NeurIPS 2024
- SciCode-Verified, 2026

### 最重要的经验

科学计算 benchmark 中：

```text
测试脚本通过
```

不一定说明：

```text
任务定义正确
oracle 正确
容差合理
参考答案无误
```

### 对本项目的直接要求

Teaching Case 应能链接：

```text
OracleSpec
ToleranceSpec
ReferenceRunner
KnownLimitations
```

并且它们有版本号。

例如：

```text
CASE_NEWTON_LOCAL_CONVERGENCE
    ↓
ORACLE_NEWTON_V2
    ↓
SciPy / high precision / analytic special case
```

---

## 2.11 KITE / ACE-TA / EduGuard：普通“课程 RAG + Tutor + Code”已经不够新

前面的增量调研已经发现：

- KITE 已做 course-aware RAG + tutoring；
- ACE-TA 已覆盖 grounded QA / quiz / code tutoring；
- EduGuard 已覆盖 teacher materials / RAG / policy / claim guard；
- 相邻 scientific computing / process-control 课程已经出现专门 AI Tutor。

因此：

> “我们是数值分析课程专用 AI 助教，有知识库、有图谱、有代码执行”

本身不能成为未来论文的主要 novelty。

真正值得研究的是：

```text
Course Boundary
+
Cross-representation Evidence
+
Error-source Diagnosis
+
Teaching Decision
+
Unaided Transfer
```

---

# 3. 调研后重新定义四个核心对象

---

## 3.1 Knowledge Unit：课程本体

`KnowledgeUnit` 应该是相对稳定、可被教师认可的课程知识对象。

推荐类型：

```text
concept
definition
theorem
condition
derivation
algorithm
error_analysis
example
exercise
code_task
misconception
counterexample
```

其中 `misconception` 可单独维护 typed entity，但不应和普通 concept 完全混为一类。

---

## 3.2 Teaching Case：教学问题抽象

> **这是本轮最建议新增的对象。**

它不是标准知识，也不是某一次学生问题。

定义：

```python
TeachingCase:
    case_id
    course_id
    course_version

    title
    task_type
    learning_objectives

    concept_ids
    required_condition_ids
    related_misconception_ids

    reasoning_signature
    accepted_variants
    allowed_alternatives

    diagnostic_probes
    possible_actions
    disclosure_policy

    oracle_spec_ids
    benchmark_family_id

    provenance
    review_status
```

### 示例

```text
CASE_NEWTON_GLOBAL_VS_LOCAL
```

连接：

```text
Newton Method
Local Convergence
Initial Guess
Derivative Condition
Counterexample: Newton 0↔1 Cycle
```

它描述的是：

> “学生把 Newton 的局部收敛条件错误理解成全局保证”

而不是某一句问法。

---

## 3.3 Query Record：真实交互证据

```python
QueryRecord:
    query_id
    raw_text
    normalized_text

    user_id
    session_id
    task_id
    attempt_id

    intent
    candidate_case_ids
    matched_case_id

    concept_anchor_ids
    boundary_decision

    created_at
```

Query 应永久保留原始表达，以便以后：

- 分析学生真实问法；
- 重新训练 case matcher；
- 发现课程图谱缺口；
- 评估 canonicalization 是否合理。

---

## 3.4 Graph Candidate：课程知识演化候选

推荐单独对象：

```python
GraphCandidate:
    candidate_id

    candidate_type:
        new_unit
        new_relation
        merge_units
        new_case
        new_alias
        scope_change

    payload
    evidence_refs

    proposed_by:
        teacher
        system
        student_query_cluster

    support_count
    first_seen
    last_seen

    status:
        pending
        approved
        merged
        rejected
        deferred

    reviewer_id
    review_note
```

这样“动态图谱”终于是一个可治理的过程，而不是随聊天直接改数据库。

---

# 4. 相似问题到底怎样判

## 4.1 不再做简单 Duplicate Detection

推荐输出：

```text
SAME_CASE
VARIANT_OF_CASE
RELATED_CASE
NEW_CASE
UNCERTAIN
```

---

## 4.2 第一层：候选召回

用：

```text
BM25
+
Embedding
+
Concept Anchor
```

从 `TeachingCase` 而不是 KnowledgeUnit 中召回 Top-K。

---

## 4.3 第二层：结构特征

比较：

```text
task_type
concept overlap
required condition overlap
misconception candidate overlap
reasoning signature
expected evidence
```

例如：

### A

> Newton 法什么时候二阶收敛？

```text
simple root
local convergence
order=2
```

### B

> 重根情况下 Newton 的收敛阶是多少？

```text
multiple root
convergence order
order≈1
```

语义 embedding 很近，

但结构特征明确不同，

因此：

```text
RELATED_CASE / VARIANT
```

而不是 SAME_CASE。

---

## 4.4 第三层：语义 Judge

只有前两层仍模糊时才调用 LLM。

Judge 的输入应是：

```text
new query
top-k case summaries
concept sets
condition sets
reasoning signatures
```

输出结构化 JSON：

```json
{
  "decision": "VARIANT_OF_CASE",
  "parent_case_id": "...",
  "difference_axes": ["required_condition"],
  "confidence": "...",
  "review_required": false
}
```

---

## 4.5 判定标准

### SAME_CASE

同时满足：

- 教学目标相同；
- task type 相同；
- 核心 KC 相同；
- 关键条件相同；
- 推理路径基本相同；
- 允许的 Tutor 动作集合一致。

### VARIANT_OF_CASE

教学目标接近，但至少一项变化：

- 条件；
- 表示；
- difficulty；
- 参数；
- accepted alternative；
- misconception family。

### RELATED_CASE

共享知识，但 Tutor 需要解决的是不同问题。

### NEW_CASE

现有 case 不足以表达。

### UNCERTAIN

证据不足，进入人工审核。

---

# 5. Course Boundary：把“知识边界”做成系统对象

老师提出“基础模型知识几乎无边界，而课程 Tutor 应明确知识圈”的想法，建议做成正式数据契约。

---

## 5.1 Scope Level

```text
core
prerequisite
extension
external
```

### core

课程大纲内必须掌握。

### prerequisite

理解 core 所需，但属于前置课程。

### extension

与当前课程直接相关，可按学生追问展开。

### external

知识图谱可知道它存在，但默认不继续深入。

---

## 5.2 边界不是简单标签

建议：

```python
BoundaryPolicy:
    course_id
    unit_id
    scope_level

    allowed_task_modes
    max_expansion_depth

    teacher_note
    source
```

例如：

```text
Newton Optimization
scope = extension
```

学生主动追问时允许解释，

但不会因为普通“Newton 求根为什么发散”自动把优化内容塞进回答。

---

## 5.3 Boundary Crossing Event

记录：

```text
query
→ graph anchor
→ detected extension
→ user accepted extension?
```

这类数据以后甚至可以帮助教师：

> 哪些“课程外问题”学生高频追问？

从而决定是否正式加入课程补充材料。

---

# 6. Candidate Graph：动态演化应该怎样发生

---

## 6.1 候选来源

允许：

```text
Teacher manual edit
LLM extraction from teacher material
Repeated student queries
Missing retrieval analysis
Benchmark failure analysis
```

---

## 6.2 不允许直接 promotion 的来源

单个：

```text
student question
LLM answer
web search result
```

不能直接成为 canonical node。

---

## 6.3 推荐 Promotion Rule

一个 Candidate 至少需要满足其中一种：

### Route A：教师直接提出

```text
Teacher proposal
→ review
→ publish
```

### Route B：课程资料证据

```text
teacher material
→ source span
→ extraction
→ review
→ publish
```

### Route C：学生高频问题

```text
query cluster
→ candidate case/unit
→ teacher review
→ extension/core decision
```

---

## 6.4 Merge 优先于 New Node

如果新候选只是：

```text
已有概念的新别名
已有 case 的新问法
已有 relation 的另一种描述
```

优先：

```text
add_alias
add_case_variant
add_evidence
```

而不是创建新节点。

---

# 7. Student Overlay：学生学习图应如何落到 Course Graph

---

## 7.1 不复制 Course Graph

错误做法：

```text
student A graph
student B graph
student C graph
```

全部复制知识节点与关系。

推荐：

```text
Canonical Graph
+
Student-specific State Table
```

---

## 7.2 最小状态

```python
StudentUnitState:
    student_id
    unit_id

    mastery_estimate
    independent_evidence_count
    assisted_success_count

    recent_error_refs
    misconception_candidate_refs

    last_practiced_at
    updated_from_event_id
```

---

## 7.3 Case-level State

某些状态不应该挂在知识点，而应该挂在 Case：

```python
StudentCaseState:
    student_id
    case_id

    exposure_count
    attempt_count
    max_help_used
    latest_outcome
    independent_transfer_status
```

这比只在知识点上存 mastery 更适合 Tutor。

---

# 8. Knowledge Graph 与 Tutor Workflow 的真正连接方式

图谱不只是 UI。

推荐在线链路：

```text
Student Query / Attempt
        ↓
TaskSpec
        ↓
Teaching Case Matcher
        ↓
Concept Anchoring
        ↓
Course Boundary Filter
        ↓
Relation-aware Graph Expansion
        ↓
Evidence Pack
        ↓
Verifier
        ↓
Diagnosis
        ↓
Student Overlay
        ↓
Teaching Policy
        ↓
Response Guard
        ↓
Tutor Response
```

---

## 8.1 Evidence Pack 应升级

当前 EvidencePack 可以逐步加入：

```python
EvidencePack:
    direct_hits
    graph_hits

    matched_case
    concept_anchors
    required_conditions

    source_claims
    student_history_refs

    boundary_decision
```

---

## 8.2 Graph Expansion 不能统一 1-hop

不同 Case 类型对应不同 edge：

### 概念解释

```text
prerequisite
contrast_with
example_of
```

### 收敛性问题

```text
requires
converges_if
counterexample_of
```

### 推导

```text
supports_proof
derives_from
requires
```

### Code Task

```text
implemented_by
test_of
common_error_of
```

---

# 9. 知识图谱本身应该如何建模

建议不要急着换 Neo4j。

SQLite / JSON + adjacency index 已足够支持首单元研究。

---

## 9.1 Node Types

```text
Concept
Definition
Theorem
Condition
Algorithm
Derivation
ErrorAnalysis
Example
Exercise
CodeTask
Counterexample
Misconception
TeachingCase
```

注意：

`TeachingCase` 可以作为单独表，

逻辑上与图谱关联，

不一定必须和 `KnowledgeUnit` 使用同一表。

---

## 9.2 推荐 Relation Types

### Ontology / prerequisite

```text
prerequisite_of
part_of
special_case_of
```

### Derivation

```text
derives_from
requires
supports_proof
```

### Numerical method semantics

```text
converges_if
has_error_bound
uses_stopping_rule
implemented_by
```

### Pedagogy

```text
example_of
exercise_of
counterexample_of
misconception_of
remediated_by
```

### Case

```text
case_targets
case_requires
case_tests
case_has_variant
```

---

# 10. 对当前仓库的具体改造

当前 public `main` 不需要重写。

建议新增：

```text
apps/api/app/knowledge/
├─ case_schema.py
├─ case_repository.py
├─ case_matcher.py
├─ boundary.py
├─ candidate_graph.py
├─ graph_repository.py
├─ graph_review.py
└─ evidence_builder.py
```

---

## 10.1 保留 schema.py，但不要继续无限堆字段

现有：

```text
SourceDocument
KnowledgeUnit
KnowledgeRelation
EvidencePack
```

继续保留。

新增：

```text
TeachingCase
GraphCandidate
BoundaryPolicy
```

建议单独文件维护。

---

## 10.2 graph service

新增后端 API：

```text
GET /courses/{course_id}/graph
GET /courses/{course_id}/graph/subgraph
GET /courses/{course_id}/cases/search

GET /users/{user_id}/courses/{course_id}/overlay

POST /admin/graph/candidates/{id}/approve
POST /admin/graph/candidates/{id}/merge
POST /admin/graph/candidates/{id}/reject
```

---

## 10.3 React Flow 前端

当前 `KnowledgeGraph` 组件已经能接 `nodes / edges / items`。

下一步重点不是重写组件，

而是：

```text
删除 hard-coded graph 的“真实数据地位”
```

保留 demo fallback 可以，

正式页面统一从 API 获取：

```text
Course Graph
+
Student Overlay
```

---

# 11. 《数值分析》求根单元的首版图谱

建议先只构建 20–40 个必要正式节点。

---

## 11.1 Core

```text
Root Finding
Bisection Method
Fixed Point Iteration
Newton Method
Local Convergence
Convergence Order
Stopping Criterion
Residual
Approximation Error
```

---

## 11.2 Prerequisite

```text
Continuity
Intermediate Value Theorem
Derivative
Taylor Expansion
Mean Value Theorem
Simple Root
Multiple Root
```

---

## 11.3 Numerical / Code

```text
Iteration Trace
Bracket Invariant
Reference Runner
Newton Update
Fixed Point Mapping
Tolerance
Floating Point
```

---

## 11.4 Counterexample

```text
Newton 0↔1 Cycle
Residual Small but Error Large
Multiple Root Linear Convergence
Discontinuous Sign Change
```

---

## 11.5 Misconception Candidates

```text
Residual = Error
Small Step = Correct Root
Newton Always Converges
Newton Always Quadratic
More Iterations Always Better
Sign Change Always Guarantees Root
```

这些只是课程设计中的 misconception candidates，

不能称为真实学生群体中的频率结论。

---

# 12. Teaching Case 首批建议

比起一开始做几百个 case，

建议先构建约 15–25 个高价值 case family。

例如：

```text
CASE_BISECTION_REQUIREMENTS
CASE_BISECTION_BRACKET_UPDATE
CASE_BISECTION_ERROR_BOUND

CASE_FIXED_POINT_CONTRACTION
CASE_FIXED_POINT_DIVERGENCE

CASE_NEWTON_DERIVATION
CASE_NEWTON_LOCAL_CONVERGENCE
CASE_NEWTON_INITIAL_VALUE
CASE_NEWTON_DERIVATIVE_ZERO
CASE_NEWTON_MULTIPLE_ROOT
CASE_NEWTON_CONVERGENCE_ORDER

CASE_RESIDUAL_VS_ERROR
CASE_STEP_VS_SUCCESS
CASE_STOPPING_CRITERION

CASE_NEWTON_CODE_UPDATE
CASE_NEWTON_CODE_STOPPING
```

---

# 13. Benchmark：专门评“图谱和 Case”是否真的有用

不要只展示图。

---

## 13.1 Query → Case

```text
Case Recall@K
SAME/VARIANT/RELATED classification
New Case detection
Uncertainty calibration
```

---

## 13.2 Case → Graph

```text
Concept Anchor Recall
Required Condition Recall
Relation Recall
Unnecessary Node Rate
```

---

## 13.3 Boundary

```text
Core Coverage
Extension Precision
Boundary Violation Rate
Over-expansion Rate
```

---

## 13.4 Candidate Evolution

```text
Duplicate Candidate Rate
Teacher Approval Rate
Merge Rate
False Expansion Rate
Time-to-review
```

---

## 13.5 Tutor Value

最终仍然要测：

```text
first successful revision
feedback adoption
independent transfer
delayed retention
```

因为：

> graph retrieval accuracy 不是 learning outcome。

---

# 14. 什么有研究价值，什么主要是工程

---

## 14.1 主要是工程基础

以下很有必要，但不能单独包装成论文创新：

```text
Course RAG
React Flow graph
Teacher review
Graph API
Embedding dedup
BKT integration
FastAPI/LangGraph routing
```

---

## 14.2 有潜在研究价值

### RQ-A：Teaching Case abstraction

> Query → Case → Knowledge 是否比直接 Query → RAG 更稳定地支持课程 Tutor？

重点不是提出“Case”这个名词，

而是证明：

- 条件召回更完整；
- 相似问句复用更稳定；
- 无关扩展更少；
- Tutor diagnosis 更好。

---

### RQ-B：Boundary-aware tutoring

> 显式课程边界能否在保持回答帮助性的同时减少无关知识扩张和 unsupported claims？

---

### RQ-C：Dynamic Candidate Graph

> 从学生真实 Query cluster 中产生候选知识扩展，再经教师审核，是否能发现静态教材图谱遗漏的教学需求？

这更像 HCI / learning analytics / system research，

不一定适合纯 NLP paper。

---

### RQ-D：Cross-representation diagnosis

这是目前仍然最值得优先做的研究主线：

```text
derivation
+
numerical behavior
+
code execution
→ error-source diagnosis
→ pedagogical action
```

图谱与 Teaching Case 在这里作为结构化知识支撑，

不是论文唯一贡献。

---

# 15. 与原有 Tutor 2.0 主线如何统一

之前的主线：

```text
Student Attempt
→ Evidence
→ Diagnosis
→ Model
→ Teach
→ Revise
```

现在知识层补成：

```text
Query / Attempt
      ↓
Teaching Case
      ↓
Course Graph
      ↓
Evidence
      ↓
Verification
      ↓
Diagnosis
      ↓
Student Overlay
      ↓
Teaching Policy
      ↓
Revision
```

因此并没有推翻此前调研。

而是解决了原来不够清楚的一层：

> **Course Knowledge 到底如何从文档变成可用于教学决策的结构。**

---

# 16. 开发优先级重新排序

## P0：先做

1. 老师交接求根章节材料；
2. 冻结 20–40 个核心 Knowledge Units；
3. 定义正式 relation types；
4. 增加 TeachingCase schema；
5. 构建 15–25 个 Case family；
6. Query → Case matcher；
7. Course Boundary；
8. Graph API；
9. React Flow 从真实后端获取；
10. Student Overlay 绑定 stable unit_id；
11. 教师基础 review / merge；
12. LuojiaMathBench 增加 Case / Graph 测试。

---

## P1：闭环以后

1. GraphCandidate；
2. query clustering；
3. 自动提出 merge / alias；
4. case-aware graph expansion；
5. misconception hypothesis；
6. numerical verifier 联动；
7. student Case state；
8. adaptive policy 基于 evidence / case 变化。

---

## P2：真实数据成熟以后

1. 自动课程图谱演化推荐；
2. longitudinal process model；
3. sophisticated KT；
4. StudentSim；
5. policy learning；
6. cross-course graph；
7. 自动 curriculum planning。

---

# 17. 最值得复用的开源资产

| 项目 | 直接借什么 | 不建议直接照搬什么 |
|---|---|---|
| OATutor | skill model、BKT、内容/hint/log 组织 | 整套 React/Firebase 架构 |
| OATutor-Content | curated content 的独立管理方式 | 课程内容本身直接迁移 |
| MathTutorBench | mistake/scaffolding/pedagogy 评测维度 | 直接当 NA benchmark |
| StatusKT / KT-PSP-25 | PSP event schema、过程建模 baseline | 直接使用其 proficiency 分数 |
| LongTutor | history evidence→diagnosis→teaching 分解 | 把静态 benchmark 当真实长期干预 |
| StratL | structured policy / transition 思路 | 将状态机本身称为创新 |
| MalruleLib | executable error + trace | 将合成 malrule 当真人 misconception gold |
| SciCode | task decomposition / executable tests | 把研究级 coding task 直接用作课程题 |
| SciCode-Verified | oracle auditing 方法 | 只换更强 LLM judge |
| pyKT | KT baseline | 没数据就提前训练复杂 KT |
| FNC code | 数值方法教学代码与参数实验 | 把教材实现当唯一 oracle |

---

# 18. 关键风险

## 风险 1：Teaching Case 变成 FAQ

避免保存：

```text
question
answer
```

应该保存：

```text
goal
knowledge
conditions
diagnostic space
actions
constraints
```

---

## 风险 2：动态图谱越来越大

解决：

```text
candidate layer
merge-first
scope
teacher review
versioning
```

---

## 风险 3：Embedding 相似度主导 ontology

Embedding 只能召回候选。

最终 Case identity 还必须看：

```text
goal
conditions
reasoning path
knowledge anchors
```

---

## 风险 4：学生图谱“看起来很智能”，但没有证据

Student Overlay 只由 observable events 更新。

---

## 风险 5：把图谱建设当论文创新

图谱是课程 Tutor 的 infrastructure。

真正研究贡献应来自：

```text
新的 evidence use
新的 diagnosis mechanism
新的 tutoring intervention
可信 benchmark
真实 learning outcome
```

---

# 19. 推荐的最终系统命名方式

产品层：

> **珞珈数智助教 2.0：面向专门课程的学习型 AI Tutor**

技术描述：

> **Course-bounded, evidence-grounded and process-aware AI tutoring system**

知识层：

> **Teacher-governed evolving course knowledge graph with canonical teaching cases and student-state overlays**

注意避免直接写：

> “self-evolving autonomous knowledge graph”

因为实际设计是：

> **human-governed candidate evolution**

更准确，也更容易被老师和评审接受。

---

# 20. 最终推荐架构

```text
Teacher Materials
      ↓
Course Pack
      ↓
Canonical Course Graph
      │
      ├───────────────┐
      ↓               ↓
Teaching Case     Candidate Layer
      ↑               ↓
Student Query     Teacher Review
      │               ↓
      └──────→ New Graph Version

Student Query / Attempt
      ↓
Case Matcher
      ↓
Knowledge Anchoring
      ↓
Boundary-aware Retrieval
      ↓
Typed Evidence
      ↓
Verifier
      ↓
Diagnosis
      ↓
Student Overlay
      ↓
Teaching Policy
      ↓
Guard
      ↓
Tutor Response
      ↓
Student Revision
      ↓
Event Store
```

---

# 21. 对当前项目最核心的判断

结合当前仓库、此前 Tutor 2.0 增量调研，以及 OATutor、MathTutorBench、StatusKT、LongTutor、StratL、Misconception Diagnosis、MalruleLib、SciCode 等已有经验，推荐坚持以下判断：

1. **继续在现有仓库开发，不重建项目。**
2. **Course Graph 是课程 ontology，不是学生问题历史。**
3. **Query 和 KnowledgeUnit 之间增加 Teaching Case。**
4. **相似问题首先归并到 Case，而不是合并知识节点。**
5. **Course Boundary 进入正式数据契约。**
6. **动态图谱使用 Candidate → Teacher Review → Publish，而不是自动写正式图。**
7. **学生个性化采用 Overlay，不复制整张图。**
8. **Case 存教学结构，不存固定答案。**
9. **图谱检索必须关注条件完整性，不只关注语义相似。**
10. **真实价值最终仍由 diagnosis、revision 和 unaided transfer 验证。**

---

# 22. 下一步建议

最合适的下一份工程文档不是继续扩大文献数量，而是：

> **《Numerical Analysis Course Pack & Teaching Case Schema v0.1》**

建议直接冻结：

- 20–40 个求根单元 KnowledgeUnit；
- relation vocabulary；
- 15–25 个 Teaching Case family；
- 8 类高价值错误家族；
- 4 级 course boundary；
- Query→Case 判定 contract；
- Candidate review contract；
- Student Overlay event contract；
- 20 个课程查询 gold；
- 第一版 graph / case benchmark。

完成这一层后，再进入 Numerical Verifier、Code Tutor 与 Adaptive Teaching Policy 的深度实现。

---

# 参考文献与开源入口

## AI Tutor / Evaluation

- Mačina et al. **MathTutorBench: A Benchmark for Measuring Open-ended Pedagogical Capabilities of LLM Tutors.** EMNLP 2025.  
  https://aclanthology.org/2025.emnlp-main.11/  
  https://github.com/eth-lre/mathtutorbench

- Pardos et al. **OATutor: An Open-source Adaptive Tutoring System and Curated Content Library for Learning Sciences Research.** CHI 2023.  
  https://doi.org/10.1145/3544548.3581574  
  https://github.com/CAHLR/OATutor  
  https://github.com/CAHLR/OATutor-Content

## Student Modeling

- Park et al. **Tracing Mathematical Proficiency Through Problem-Solving Processes.** Findings ACL 2026.  
  https://aclanthology.org/2026.findings-acl.961/  
  https://github.com/jungyangpark/KT-PSP-25

- Li et al. **LongTutor: Benchmarking Large Language Models for Long-term Personalized Tutoring.** ACL 2026.  
  https://aclanthology.org/2026.acl-long.1371/  
  https://github.com/liano3/LongTutor

## Misconception / Process Diagnosis

- Mitton et al. **Misconception Diagnosis From Student-Tutor Dialogue: Generate, Retrieve, Rerank.** 2026.  
  https://doi.org/10.1145/3774398.3811609

- Chen et al. **MalruleLib: Large-Scale Executable Misconception Reasoning with Step Traces for Modeling Student Thinking in Mathematics.** 2026.  
  https://arxiv.org/abs/2601.03217

- Yasir et al. **Confirming Correct, Missing the Rest: LLM Tutoring Agents Struggle Where Feedback Matters Most.** BEA 2026.  
  https://aclanthology.org/2026.bea-1.56/

## Pedagogical Policy

- Puech et al. **Towards the Pedagogical Steering of Large Language Models for Tutoring.** Findings ACL 2025.  
  https://aclanthology.org/2025.findings-acl.1348/  
  https://github.com/RomainPuech/StratL-Pedagogical-Steering-of-LLMs-for-Tutoring

- Cohn et al. **Evidence-Decision-Feedback: Theory-Driven Adaptive Scaffolding for LLM Agents.** AIED 2026.  
  https://doi.org/10.1007/978-3-032-29744-0_1

## Scientific / Numerical / Code Evaluation

- Tian et al. **SciCode: A Research Coding Benchmark Curated by Scientists.** NeurIPS 2024.  
  https://arxiv.org/abs/2407.13168  
  https://github.com/scicode-bench/SciCode

- Hu et al. **SciCode-Verified: How Benchmark Defects Underestimated the Scientific-Coding Ability of Language Models.** 2026.  
  https://arxiv.org/abs/2608.04975

## 已有本项目增量调研中建议继续关注

- KITE / Retrieval-Augmented Tutoring for Algorithm Tracing and Problem-Solving in AI Education
- ACE-TA
- EduGuard
- LeanTutor
- ProofGrader
- MMTutorBench
- The Missing Evaluation Axis
- StudentSim
- EvalConvoLearn
- FNC teaching code

这些工作主要用于验证“哪些已经被别人做过”，避免把普通 course RAG、Socratic prompt、code execution 或 multi-agent routing 误写成主要创新点。

---

# 23. 全局落地实施状态与 To-Do 清单 (已完成 Deliverables & 待实施 Roadmap)

> 本节记录《珞珈导师 2.0 课程图谱与教学案例演化系统》在工程代码库中的实际落地进展与后续迭代计划。更新时间：2026年9月。

## 23.1 实施进展看板 (Implementation Dashboard)

| 阶段 / 模块 | 核心工作 | 交付状态 | 涉及核心文件 / 模块 |
| :--- | :--- | :---: | :--- |
| **Phase 1.1 图谱数据契约** | Course Pack 种子库构建 (Units/Cases/Misconceptions) | ✅ **已完成 (100%)** | `data/course_packs/numerical_analysis_root_finding.json` |
| **Phase 1.2 规范图谱与边界** | 图谱仓储、4级边界策略、React Flow 拓扑导出 | ✅ **已完成 (100%)** | `apps/api/app/knowledge/graph_repository.py`, `boundary.py` |
| **Phase 1.3 教学案例匹配** | 复合语义与推理签名多路召回排序器 | ✅ **已完成 (100%)** | `apps/api/app/knowledge/case_matcher.py`, `case_schema.py` |
| **Phase 1.4 动态候选演化** | 候选池管理与教师人机审核循环 (入图/合并/驳回) | ✅ **已完成 (100%)** | `apps/api/app/knowledge/candidate_graph.py`, `graph_review.py` |
| **Phase 1.5 学生认知状态** | 学生个性化掌握度与遗忘衰减 Overlay | ✅ **已完成 (100%)** | `apps/api/app/knowledge/student_overlay.py` |
| **Phase 1.6 证据链装配** | 课程图谱 Typed Evidence Pack 结构化组装器 | ✅ **已完成 (100%)** | `apps/api/app/knowledge/evidence_builder.py` |
| **Phase 1.7 RESTful 路由** | 标准化 API 路由系统 (/api/courses/...) | ✅ **已完成 (100%)** | `apps/api/app/api/routes_courses.py` |
| **Phase 1.8 前端图谱交互画板** | React Flow 全景画布、范畴过滤、高对比度节点卡片 | ✅ **已完成 (100%)** | `apps/web/app/graph/page.tsx`, `knowledge-graph.tsx` |
| **Phase 1.9 数学排版引擎** | KaTeX 隔离解析、Markdown 混合排版、Dark mode 适配 | ✅ **已完成 (100%)** | `apps/web/components/math-view.tsx`, `globals.css` |
| **Phase 1.10 导师对话直连** | Tutor Chat 自动锚定 Case、注入认知约束与格式规范 | ✅ **已完成 (100%)** | `apps/api/app/tutor/fast_context.py`, `prompt_builder.py` |
| **Phase 1.11 管理后台审核工作台** | 动态演化候选审核、一键入图/合并/驳回、公式预览 | ✅ **已完成 (100%)** | `apps/web/app/admin/knowledge/page.tsx` |
| **Phase 2.1 数值符号验证器** | SymPy/NumPy 沙箱可执行数值断言，解决 LLM 浮点幻觉 | ⏳ **待实施 (P1)** | `apps/api/app/verifier/numerical_oracle.py` |
| **Phase 2.2 代码沙箱调试器** | Python/C++ 牛顿法代码单步追踪与除零保护静态分析 | ⏳ **待实施 (P1)** | `apps/api/app/tutor/code_verifier.py` |
| **Phase 2.3 自适应支架式策略** | 多轮交互 Help Level 阶梯升级模型 | ⏳ **待实施 (P2)** | `apps/api/app/tutor/scaffolding_policy.py` |
| **Phase 2.4 学情日志自动聚类** | 未命中提问向量聚类与自动生成待审候选 Worker | ⏳ **待实施 (P2)** | `apps/api/app/knowledge/clustering_worker.py` |
| **Phase 2.5 迁移评测基准** | 20-30 道未见变体独立解题 (Unaided Transfer) Benchmark | ⏳ **待实施 (P3)** | `benchmarks/eval_transfer_test.py` |

---

## 23.2 已完成工作清单 (Done / Completed)

- [x] **1. 数值分析 Course Pack 数据契约与种子库**
  - **交付文件**：`data/course_packs/numerical_analysis_root_finding.json`
  - **功能成果**：涵盖 25+ 核心 KnowledgeUnit、10 种规范拓扑关系、25+ 真实 Teaching Case（包含概念解释、代码调试、算法分析等题型）、8 大类高价值易错家族（Misconceptions）。
- [x] **2. 规范图谱仓储与范围边界策略引擎 (Course Graph Repository & Boundary Policy)**
  - **交付文件**：`apps/api/app/knowledge/graph_repository.py`, `boundary.py`, `schema.py`
  - **功能成果**：支持核心知识元、前置知识元、扩展选学与超纲四级边界判定（`ScopeLevel: core | prerequisite | extension | out_of_scope`），实现图谱规范关系的增删查改与 React Flow 规范拓扑导出。
- [x] **3. 教学案例表征与复合语义匹配器 (Teaching Case Matcher)**
  - **交付文件**：`apps/api/app/knowledge/case_schema.py`, `case_matcher.py`
  - **功能成果**：支持针对学生提问的高频变体（`accepted_variants`）与推理签名（`reasoning_signature`）的复合多路打分与重排序，精准锚定教学案例。
- [x] **4. 演化候选池与教师人机审核循环 (Human-Governed Candidate Pool & Review)**
  - **交付文件**：`apps/api/app/knowledge/candidate_graph.py`, `graph_review.py`, `course_service.py`
  - **功能成果**：实现动态演化缓冲区，支持 `new_unit`、`new_case`、`new_alias`、`new_relation` 等类型；支持教师一键批准（`approve`）、合并至已有概念（`merge`）、驳回（`reject`）、重审（`defer`）完整审计动作。
- [x] **5. 学生认知状态覆盖层 (Student Overlay Store)**
  - **交付文件**：`apps/api/app/knowledge/student_overlay.py`
  - **功能成果**：不复制全图，按学生粒度轻量记录掌握度、独立作答率（`is_independent`）、求助等级（`help_level`）与高频误区，计算动态置信度衰减。
- [x] **6. 结构化证据组装器 (Course Evidence Builder)**
  - **交付文件**：`apps/api/app/knowledge/evidence_builder.py`
  - **功能成果**：输入学生查询，自动串联检索 Teaching Case、锚定核心知识元、执行边界策略判定并组装 Typed Evidence Pack。
- [x] **7. 后端 RESTful 路由与数据接口**
  - **交付文件**：`apps/api/app/api/routes_courses.py`
  - **功能成果**：提供 `/api/courses/{course_id}/graph`, `/candidates`, `/review`, `/overlay`, `/events` 全套标准化端点。
- [x] **8. 前端全景交互知识图谱画板 (Interactive Canvas View)**
  - **交付文件**：`apps/web/app/graph/page.tsx`, `components/knowledge-graph.tsx`
  - **功能成果**：基于 `@xyflow/react` 打造全景节点图谱，支持大纲范畴筛选、搜索高亮、学生掌握度 Overlay 渲染、节点侧边抽屉与高保真公式预览。
- [x] **9. 现代数学公式排版与渲染引擎 (KaTeX Math View & Dark Mode)**
  - **交付文件**：`apps/web/components/math-view.tsx`, `apps/web/app/globals.css`
  - **功能成果**：消除 KaTeX 双重 DOM 污染；实现数学公式 slot 隔离提取与 Markdown 混合渲染；全局 dark 模式高对比度样式适配。
- [x] **10. 导师对话流直连课程图谱 2.0 (Tutor Chat Orchestration)**
  - **交付文件**：`apps/api/app/tutor/fast_context.py`, `prompt_builder.py`
  - **功能成果**：学生在聊天框提问时，底层自动调用 `CourseEvidenceBuilder`，命中案例后注入认知目标、苏格拉底逐步引导决策、诊断探针与公式规范约束。
- [x] **11. 管理后台图谱动态演化候选审核工作台 (Admin Candidate Review Dashboard)**
  - **交付文件**：`apps/web/app/admin/knowledge/page.tsx`
  - **功能成果**：新增顶栏“图谱动态演化候选”工作台标签页，提供状态筛选（待审/已入图/已合并/已驳回）、一键批准入图、合并至已有规范概念模态框、教师批注、提议新候选模态框及高保真 KaTeX 公式预览。

---

## 23.3 待实施研发任务清单 (To-Do / Upcoming Roadmap)

- [ ] **1. 数值符号执行验证器 (Numerical Oracle & Executable Verifier) [P1]**
  - **目标**：对接 SymPy / NumPy 沙箱，针对学生计算的迭代步数值、变号区间中点、残差等进行确定性断言验证，解决 LLM 在多位浮点数计算中的幻觉问题。
  - **设计规划**：在 `apps/api/app/verifier/` 模块下实现 `NumericalOracle`，当 Teaching Case 包含可执行公式时，比对学生输入的代数表达式或数值结果。
  - **交付文件**：`apps/api/app/verifier/numerical_oracle.py`, `tests/test_numerical_oracle.py`
- [ ] **2. 代码调试型教学案例沙箱 (Executable Code Tutor Sandbox) [P1]**
  - **目标**：针对学生编写的 Python/NumPy 牛顿法、二分法代码，提供语法静态分析、除零隐患扫描以及沙箱单步跟踪反馈，拦截死循环。
  - **设计规划**：扩展 `FastContext` 与代码执行单元，提供异常类型映射（如把 ZeroDivisionError 关联至 `MISC_DERIVATIVE_ZERO`）。
  - **交付文件**：`apps/api/app/tutor/code_verifier.py`, `tests/test_code_verifier.py`
- [ ] **3. 多轮自适应支架式引导策略 (Adaptive Scaffolding Policy & Help Escalation) [P2]**
  - **目标**：结合学生在当前对话的多次尝试历史与 `help_level`（0: 概念探针提问 -> 1: 提示核心公式 -> 2: 给出一半步骤代入），避免直接披露解法。
  - **设计规划**：在 `prompt_builder.py` 中引入 `ScaffoldingPolicy`，根据学生 Overlay 中的求助等级动态调整 LLM 的引导层级。
  - **交付文件**：`apps/api/app/tutor/scaffolding_policy.py`
- [ ] **4. 学情日志聚类与候选自动沉淀工作流 (Automated Student Query Clustering) [P2]**
  - **目标**：基于向量检索与语义聚类，对未命中现有 Case 的高频学生提问，自动聚类并生成带 `support_count` 的动态待审候选，推送给任课教师审核。
  - **设计规划**：实现后台轻量 worker，定期扫描学生提问日志未命中项，达到支持度阈值（如频次 ≥ 5）后调用 `candidate_mgr.add_candidate()`。
  - **交付文件**：`apps/api/app/knowledge/clustering_worker.py`
- [ ] **5. 课程级迁移能力评测基准 (Transfer & Mastery Benchmark) [P3]**
  - **目标**：构建 20–30 道未见变体测试题，评估经过图谱引导辅导后的学生在独立解题（unaided transfer）中的正确率提升与概念掌握稳定性。
  - **交付文件**：`benchmarks/eval_transfer_test.py`, `data/benchmarks/transfer_gold.json`
- [ ] **6. 跨课程多学科知识图谱扩展 (Multi-Course Extension) [P3]**
  - **目标**：将 Course Graph 2.0 机制扩展至《高等数学》《线性代数》等工科核心数学课程，验证图谱架构的通用性与可复用性。
  - **交付文件**：`data/course_packs/linear_algebra_systems.json`

---

# 24. 第二轮：教材切分粒度与检索接线

> 本节基于一次真实运行：吕锡亮《数值分析》讲义 PDF（150 页、7.2 MB）经 MinerU v4 解析得 320,900 字符 markdown，走 `POST /api/uploads` → `documents.markdown` → `candidate_pipeline` → `CandidateManager` 全链路。所有数字为实测。

## 24.0 与 23.1 看板的关系

23.1 看板把 **Phase 1.6 证据链装配** 与 **Phase 1.10 导师对话直连** 标为 ✅ 已完成 (100%)。本节实测表明这两项存在功能性缺陷（`direct_hits` 恒空、图命中分数为常量、注入无排序），因此 §24.4 的 A、B 两阶段属于**对已交付阶段的 P0 修正**，优先级高于 23.3 中列为 P1 的新功能。按本分支「claim 必须有 artifact 支撑」的约定，看板状态应随之修正。

## 24.1 现状诊断

**[项目现状]** 切分层面，`segment_document` 产出 150 个单元，长度中位数 1,437 字符、p90 5,219、最长 9,943；分布为 ≤600 字 34 个、601–2000 字 56 个、2001–5000 字 43 个、>5000 字 17 个。三个具体缺陷：

1. **附着策略把教学单元糊成块。** `_ATTACH_PATTERNS` 让 `证明`/`例`/`例题`/`推论`/`注` 全部并入上一单元。全书有 56 处行内 `证明`、29 处行内 `例`，结果「定理 5.3」成为 8,993 字符单块，内部含自身证明、多个例题与注。**"例题作为定理的佐证"这一教学关系目前由字符串拼接表达，而非图边。**
2. **类型词表不全。** `_UNIT_TYPE_PATTERNS` 只有 定义/定理/算法，缺 `引理`/`推论`/`注`。实测「引理 2.3 (Sherman-Morrison-Woodbury 公式)」4,352 字符被归为 `concept`。修正标题标记优先级后类型分布为 concept 85 / definition 19 / theorem 46；`algorithm` 为 0 属正常（该书不用 `## 算法 x.y` 标题，「算法」仅出现在散文与目录行）。
3. **管道产出关系候选 0 条。** `build_candidates_from_document` 只发 `new_unit`，而 `CandidateType.NEW_RELATION` 与 `KnowledgeRelation.relation_type` 词表中的 `supports_proof`/`example_of`/`derives`/`common_mistake_of`/`contrast_with` 早已定义，从未被此流水线使用。

**[项目现状]** 检索层面，仓库中存在**两套检索且未接通**：

- `knowledge/search.py` 是完整的混合检索器：BM25 索引（`:137`）、向量检索（`:208`）、`search_hybrid` + **RRF 融合**（`:191`/`:211`/`:176`）、学科命中加权 `+20000`（`:178`）、按分排序（`:181`）、embedding 缓存 `embeddings.json`（`:123`）。
- `knowledge/evidence_builder.py`（Course Graph 2.0 路径）：`direct_hits=[]` 恒为空（`:98`）；`graph_hits` 全部硬编码 `score=85`（`:94`），即所有命中同分、无排序信号；包装为 `KnowledgeItem` 时 `prerequisite=[]`（`:90`）丢掉前置关系。
- 二者在 `tutor/fast_context._collect_local_hits` 中是**互斥二选一**：先试课程图谱，若返回 `matched_case` 或 `concept_anchors` 就直接采用，**混合检索被完全绕过**；只有课程图谱未命中时，混合检索才作为兜底被调用。两条路径从不融合，因此课程图谱命中时丢掉混合检索的排序，未命中时丢掉案例与边界证据。
- 命中后 `tutor/fast_context.py:103` 以 `hits = pack.direct_hits + pack.graph_hits` **纯拼接、不重排**；`tutor/prompt_builder._hits_text` 再取 `hits[:3]`，每条 `description[:240]`。

结论：**课程图谱命中时等价于没有检索**——注入模型的是子图中前 3 个节点，与学生提问无关；总注入量约 720 字符，对数学讲解是硬天花板。且 `search.py` 的 RRF 分数量级为数万，常量 85 一旦真正参与合并排序会被完全淹没，因此融合必须按**排名**而非原始分数进行。

**[项目现状]** 文档入库侧，`routes_uploads.chunk_markdown` 为 500 字符定长窗口 + 50 字符重叠，纯字符偏移、不认结构。实测该重叠使重建文本比原文长 11.3%（357,263 vs 320,900 字符），是候选重复与 `support_count` 虚增的直接原因（已改为读 `documents.markdown` 原文修复）。

## 24.2 可借鉴的做法

**[文献/开源证据]**

- **Graph-aware late chunking**（arXiv 2603.22633）：切分边界由文档结构/图决定，跨边界上下文在**检索期**恢复而非入库期烘死；论文报告可从多至 15.6× 的章节中检索并收窄生成差距。对应 §24.3 第三层。
- **AutoMathKG**（arXiv 2505.13406）：从数学文本抽取 Definition / Theorem / Problem 三类实体，**先规则抽取、再 LLM 增强**，并把证明切分为带 `premise`/`assumption`/`conclusion` 战术标签的逻辑步。印证"确定性切分 + 模型只做模糊部分"的顺序。
- **KGGen**（arXiv 2502.09956）：LLM 抽取的节点会"specific 到唯一"，导致 embedding 欠规范；用迭代聚类对齐实体、降低稀疏度，在 MINE 上比基线高 18%。**警示：跨节关系可由模型提议，但必须经既有 `case_matcher`/别名比对给出合并建议，不得自动建节点。**
- 工程共识：固定长度切分会 "fragment semantic context"，结构感知 + 父子分块 + small-to-big 检索为当前主流组合（Atlan 2026 chunking guide）；RAPTOR 的递归摘要树是可选的更重方案。

## 24.3 方案

**[方案建议]** 三层，逐层可独立验收：

**第一层 · 切细成教学原子。** 类型词表扩为 `definition / theorem / lemma(引理) / corollary(推论) / proof / example / algorithm / remark / section`；`证明`与`例`**不再并入定理**，各自成节点。保持纯规则、可复现、零调用成本，与 §16「抽取必须可审计」一致。

**第二层 · 连贯性用图边表达，不用文本拼接。** 产出 `NEW_RELATION` 候选：`proof --supports_proof--> theorem`、`example --example_of--> theorem|definition`、`corollary --derives_from--> theorem`、`lemma --supports_proof--> theorem`，并为每个原子挂 `part_of --> 所属小节` 形成层次父子。**无需扩 schema**：`KnowledgeRelation.relation_type` 与 `graph_repository.TASK_TYPE_RELATIONS` 中 `part_of`/`supports_proof`/`example_of`/`derives_from` 均已存在，且 `graph_review.py:115-124` 早已能审 `new_relation`——缺的只是流水线去产出它们。

**第三层 · 上下文在检索期组装。** 命中原子（小而准）→ 沿 `supports_proof`/`example_of`/`part_of` 扩展出证明、例题与所属小节引言 → 按 **token 预算**注入，取代 `hits[:3] × 240 字`。每个原子存 `context_header`（章/节路径 + 一行锚点），避免"这段属于哪一节"在检索后丢失。同时接通两套检索：因 `build_evidence_pack` 是同步的，融合放在异步的 `fast_context._collect_local_hits`——两套检索**并发**执行，混合检索带独立子预算（200ms），使其慢速 embedding 调用不会连带取消课程图谱结果；再按 **RRF 排名融合**（而非原始分数，两者量纲不可比）产出单一有序列表，课程图谱的 case/boundary/hints 元数据保留不变。

## 24.4 分期与代价

| 阶段 | 内容 | 量级 | 验收 |
| :--- | :--- | :--- | :--- |
| **A** | 补 `引理/推论/注/例` 类型；停止附着合并；产出 `supports_proof`/`example_of`/`derives`/`part_of` 关系候选 | 1 天，纯规则 | 真教材重跑后 relation 候选 > 0；引理归类正确；定理不再吞并证明与例题 |
| **B** | `evidence_builder` 接 hybrid 检索、去掉 `score=85`、统一排序、注入改 token 预算 | 1 天 | 同一问题的 top-3 与子图遍历顺序无关且可复现 |
| **C** | 层次父子 + `context_header` + 检索期邻域扩展（small-to-big） | 2–3 天 | 查一个定理能连带取其证明与例题，注入总量受预算约束 |
| **D** | 结构感知切分替换 500 字定长窗口；FTS5 分块降级为纯检索派生物 | 2–3 天 | 分块无重叠注水、跨块标题不断裂 |

**代价必须写明**：切细后候选数预计由 150 增至 400–600，教师审核量翻倍以上。缓解方式——按小节批量审；`proof`/`example` 这类**逐字来自教材、非模型生成**的原子默认低风险快速通过，人工只审 `definition`/`theorem`/`lemma` 与跨节关系。A、B 不引入新依赖，且 B 的收益可能高于更换任何检索算法，因为它修的是"新链路没有排序"这一结构性缺口。

## 24.5 本轮已修复的前置缺陷

以下四项在 §24 定稿前已修复合入，是 A–D 的地基：

- `documents.markdown` 持久化 + migration 004：候选抽取改读原文，不再从重叠分块重建（消除 11.3% 注水、重复候选与 `support_count` 虚增）；无原文时 409 fail-closed。
- MinerU v4 端点 `file-urls/bear` → `file-urls/batch`：原拼写错误使教材上传全链路失效，且被 `Response.json()` 报成 `Extra data: line 1 column 5` 而掩盖真因。
- 标记优先级：MinerU 把 `定义/定理` 渲染为 `## 定义 1.1`，既是标题又是标记，原分支顺序使类型判定失效（4/65 → 65/65）。
- 取消 `_MAX_CONTENT_CHARS = 600` 写入期截断：原上限丢弃全书 75% 正文、截断 46 个定理中的 44 个且切断 LaTeX；截断下移到展示层 `app/text_preview.truncate_text`（LaTeX 安全边界）。内容保留率 25% → 99.9%。

## 24.6 A–C 实施结果（实测）

**A · 切细教学原子 + 关系候选**（同一本 150 页教材，320,900 字符）：

| | 改造前 | 改造后 |
| :--- | :--- | :--- |
| 候选 | 150 单元 / **0 关系** | **240 单元 / 242 关系** |
| 类型 | concept 146, definition 2, theorem 2 | concept 78, proof 55, theorem 46, definition 19, example 16, corollary 11, lemma 8, algorithm 4, remark 3 |
| 关系 | — | part_of 162, supports_proof 57, example_of 13, derives_from 10 |
| 单元长度中位数 | 1,437 | **774**（p90 5,219 → 3,358） |
| 正文保留率 | 99.9% | 99.8% |

定理 2.4 从 2,210 字符的大块（命题+证明+例题）变成 293 字符的命题，其证明独立成原子并由 `supports_proof` 连回。

**B · 两套检索融合**：`_collect_local_hits` 由互斥二选一改为并发 + RRF 排名融合；混合检索带 200ms 独立子预算，避免慢速 embedding 调用把课程图谱结果一起拖过 350ms 窗口而被取消。图命中分数由常量 85 改为「锚点 1.0 / 一跳邻居 0.6」× case 置信度并预排序；`prerequisite` 不再被丢成 `[]`。注入预算由 `hits[:3] × 240 字`（约 720 字）改为 2400 字按排名填充，被省略的命中显式报告而非静默丢弃。

**C · 章节路径与溯源**：实施中发现两个新缺陷。

1. **MinerU 把层级压平了**：该书 158 个标题**全部**输出为 `##`，markdown 的 `#` 数完全不携带层级信息。改为从章节编号推断深度（`第 N 章`→1，`N.M`→2，`N.M.K`→3）后，`chapter_path` 深度分布由「239/240 都是 1」变为 `{1: 10, 2: 135, 3: 94}`，每个定理都能定位到「第 2 章 非线性方程（组）的数值求解 › 2.1 单个方程求解问题 › 2.1.3 Newton 法」。
2. **审核入图会丢溯源**：`graph_review.py` 批准候选时构造 `KnowledgeUnit` 未映射 `chapter_path` / `source_document_id` / `page_start` / `page_end`，候选上的 `evidence_ref` 又留在候选里，于是入图后的规范单元无法回答"我来自哪份材料的哪一节"——违反 §2 约定第 7 条。已补映射。

另：`KnowledgeItem` 已有 `chapter` / `section` 字段，`evidence_builder` 现将 `chapter_path` 填入，`_hits_text` 渲染为 `来源 · 章 › 节`，使注入的片段带出处。

测试：`pytest -q` → **229 passed**（离线，约 9s）。

## 24.7 参考入口

- Graph-Aware Late Chunking for RAG — https://arxiv.org/html/2603.22633v1
- AutoMathKG: automated mathematical knowledge graph — https://arxiv.org/html/2505.13406v1
- KGGen: Extracting Knowledge Graphs from Plain Text with LLMs — https://arxiv.org/html/2502.09956v1
- Chunking Strategies for RAG: A Complete Guide for 2026 — https://atlan.com/know/chunking-strategies-rag/
- 12 Advanced RAG Techniques: Beyond Naive Retrieval — https://atlan.com/know/advanced-rag-techniques/
- RAG 文档切分策略全景解析：固定长度 vs 语义切分 — https://blog.csdn.net/bumblebee16/article/details/164758378
- RAPTOR vs 传统 RAG：树状检索 — https://m.blog.csdn.net/gitblog_00949/article/details/154681514

