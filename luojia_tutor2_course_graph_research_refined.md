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
