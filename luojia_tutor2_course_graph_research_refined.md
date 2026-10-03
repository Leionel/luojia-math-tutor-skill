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

> **执行入口（2026-10-01 更新）**：下一阶段排期与验收以本文 [§27 六个月推进时间线](#27-六个月推进时间线2026-10-01--2027-03-31) 为准，§27.7 给出至2027年9月的一年滚动展望。§16、§23、§26 保留为设计与历史基线；“模块已存在”不等于诊断闭环或学习效果已验收。

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

> **状态**：A–D 四阶段均已实施完成，实测结果见 §24.6。表中「量级」为事前估计，实际 A+C+D 合并为三个提交完成。

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

**D · 结构感知切分**（同一本教材）：

| | 旧（500 字定长 + 50 重叠） | 新（按教学单元 + 段落边界） |
| :--- | :--- | :--- |
| 块数 | 714 | **430** |
| 重拼 vs 源文本 | 357,263 字（**+11.3% 注水**） | 正文 320,049 字，**无丢失、无重复** |
| 块正文长度 | 固定 500 | 中位数 810 / p90 1,160 / max 1,285 |
| 标题完整性 | 会被窗口切断 | **158/158 完整且仅出现一次** |
| 上下文头部 | 无 | 429/430 块带 `[章 › 节 › 小节] 标题` |

切分复用 `segment_document`，因此一个 chunk 绝不跨两个教学单元；超长小节按段落边界切，单段落超限时退到 `text_preview.safe_cut` 的 LaTeX 安全边界，不再产生未闭合的 `\frac{`。块被明确定义为**有损派生物**（含头部，拼接不等于原文），原文重建一律走 `documents.markdown`。`routes_uploads.chunk_markdown` 已删除。

测试：`pytest -q` → **238 passed**（离线，约 8s）。A–D 四阶段全部落地。

## 24.7 参考入口

- Graph-Aware Late Chunking for RAG — https://arxiv.org/html/2603.22633v1
- AutoMathKG: automated mathematical knowledge graph — https://arxiv.org/html/2505.13406v1
- KGGen: Extracting Knowledge Graphs from Plain Text with LLMs — https://arxiv.org/html/2502.09956v1
- Chunking Strategies for RAG: A Complete Guide for 2026 — https://atlan.com/know/chunking-strategies-rag/
- 12 Advanced RAG Techniques: Beyond Naive Retrieval — https://atlan.com/know/advanced-rag-techniques/
- RAG 文档切分策略全景解析：固定长度 vs 语义切分 — https://blog.csdn.net/bumblebee16/article/details/164758378
- RAPTOR vs 传统 RAG：树状检索 — https://m.blog.csdn.net/gitblog_00949/article/details/154681514


## 25. 检索评测基线（2026-09-30 实测）

### 25.1 评测集

`evaluation/retrieval_eval.json` 由 `scripts/build_retrieval_eval.py` 从 229 个 pending 教学单元 + 260 条类型化关系确定性生成，共 **244 条不重复 query，覆盖 57 个小节，gold 零悬挂**，不依赖人工标注，且每条带 `expected_marker / subject_marker / expected_section`，重切分后仍可解析 gold。七种问法：

| style | 条数 | 示例 |
| --- | --- | --- |
| title | 81 | `Romberg 算法` |
| scoped_marker | 79 | `Newton 法里的定义 2.1讲了什么？` |
| colloquial | 25 | `三次样条插值这块我没听懂，能讲讲吗` |
| definition | 22 | `什么是机器精度？`（术语抽自单元正文的「称为/叫做」句式） |
| howto | 18 | `Jacobi矩阵是怎么算的？` |
| hierarchy | 15 | `介值定理属于哪一节？`（经 part_of 反查） |
| relation | 4 | `二分法的误差估计有哪些例题？`（example_of，双 gold） |

### 25.2 评测暴露并修掉的缺陷

1. **`Repository.search_document_chunks` 不存在**：`fast_context._collect_document_chunks` 一直在调一个没有的方法，异常被 `logger.exception` 吞掉——教材 chunk 检索在运行时**从未生效过**。已实现（FTS5 MATCH + LIKE 兜底）。
2. **SQLite 默认分词器切不动中文**：整段 CJK 落成一个 token，「牛顿迭代法」匹配不到「牛顿迭代」。新增 migration 005 建 `document_chunks_index`（CJK bigram 索引），`insert/clear/search` 三路同步（`app/memory/text_index.py`）。
3. **问句脚手架毒化 AND 查询**：「…里的定义 1.1讲了什么？」整句 AND 后 gold 被排除。`cjk_query_groups` 现在剥离问句框架（属于哪一节/是什么/讲了…）并按功能字切分再取 bigram。

### 25.3 结果（430 chunks，244 cases，gold 244/244 解析成功；2026-09-30 第二轮补齐）

| 配置 | 口径 | Recall@3 | Recall@5 | MRR@10 |
| --- | --- | --- | --- | --- |
| BM25（bigram FTS，生产同路径） | chunk | **0.752** | 0.798 | **0.708** |
| vector（本地 TF-IDF+LSA k=256，无 API 降级臂） | chunk | 0.581 | 0.685 | 0.498 |
| hybrid（BM25 ⊕ vector 的 RRF） | chunk | 0.688 | **0.805** | 0.657 |
| 图层（候选单元级，**审核前 dry-run**，加权 IDF + 标题×3/关键词×2/正文×1 + sqrt 长度归一） | unit | 0.725 | 0.820 | 0.625 |

分风格（BM25 chunk 级）：title 0.864 / colloquial 0.900 / scoped_marker 0.857 / howto 0.574 / definition 0.447 / relation 0.250 / hierarchy 0.133。
分风格（图层 unit 级）：colloquial 1.000 / title 0.988 / scoped_marker 0.582 / definition 0.500 / howto 0.500 / relation 0.500 / **hierarchy 0.267，且「top1 命中单元 + part_of 父节点即正确节」的 hierarchy@1 = 0.867**。

结论与下一步：

- 问句框架剥离一项改动就把 chunk 级整体 R@3 从 0.379 拉到 0.752，是本轮收益最大的单点。
- **hierarchy 短板被图层解决**：chunk 检索答不了「X 属于哪一节」（0.133），但同一评测里图层 dry-run 的 hierarchy@1 = 0.867——前提是把 495 条候选真正审核入图；当前是拿 pending 集代理测的。**审核量是解锁这个数字的前提。**
- vector 臂目前是本地 LSA 降级（无 neural embedding key），R@3 0.581 低于 BM25 属预期；`DASHSCOPE_API_KEY` 一到（读环境变量即可，代码无需改），重跑就能得到真神经向量与 hybrid 的真实水位——hybrid 的 R@5 0.805 已经是全场最高，说明融合方向正确，换强向量臂后 R@3/MRR 大概率跟涨。
- 自出题偏「贴标题」，指标整体偏乐观；colloquial/hierarchy/relation 三类用于对冲。definition 0.447 与 howto 0.574 是下一轮 chunk 检索改进的主攻区间。

# 26. 接手核查与下一轮推进计划（2026-09-30）

> 本节补充 §23 的工程完成声明与 §25 的检索结论。以下区分本轮核实结果和待实施任务；本轮未修改生产代码、教材数据库或教师审核状态。

## 26.1 当前证据与必须纠正的口径

- 当前分支为 `feature/course-graph-2.0`。`npm test` 本轮通过：知识 JSON 校验、API **256 passed**、前端 **12 passed**；未运行生产 build、浏览器上传验收或在线模型评测。
- 求根种子包实际含 **27 units / 21 relations / 15 Teaching Cases**。§23 的“25+ 真实 Teaching Case”不成立；这些是课程设计案例，不能等同于真实学生交互案例。
- 教材候选数据库实际位于 `apps/api/data/course_store.db`：**495 pending = 235 units + 260 relations**，另有 283 superseded。评测脚本采用其中筛选后的 229 个单元，不能把这两个分母混用。
- `StudentOverlayStore` 存过程证据计数，`mastery_estimate=None`；掌握度归 BKT。§23 的“掌握度与遗忘衰减 Overlay 已完成”需理解为接口/证据层存在，不能理解为完整学生模型已验收。当前聊天路径没有自动调用 `record_process_event`，该方法的生产调用点为课程 events API。
- 旧 Case benchmark 本轮离线重跑：域内 Recall@1 **16/16**、可接受决策集合命中率 **20/20**、域外检测 **4/4**。旧报告称第二项为 Decision Accuracy，但20题 gold 均接受多个决策，不能当作严格单标签准确率。20 个 query 均不与种子包 `accepted_variants` 完全相同，但样本小，不足以验证复杂条件、近邻 Case 或不确定性的泛化。
- 当前 `TeachingCaseMatcher` 是 token 重叠与条件规则基线，schema 中的 `reasoning_signature` 尚未用于匹配；§23 的“语义与推理签名排序器已完成”不能理解为已获得语义判别能力。扩充集将用于定位其真实召回与决策缺口，不能与 LLM 答题正确率直接比较。
- 现有检索 JSON：BM25 R@3/MRR 为 **0.752/0.708**，hybrid 为 **0.688/0.657**；hybrid 仅 R@5 略高（0.805 vs 0.798）。不能据此声称融合整体优于 BM25，也不能预断强 embedding 必然改善。

**阻塞 A：正式图的审核结果不能完整跨重启恢复（已复现）。** `CourseStore` 持久化候选、事件和 revision；`GraphReviewService` 把批准的实体写入内存 `graph_repo`。`CourseService` 启动仅加载种子包，没有恢复审核后的正式图。使用临时 SQLite、无 dotenv，批准测试单元后重新创建服务，输出如下；未触碰真实教材库：

```text
approved_unit_before_restart True
candidate_after_restart approved
approved_unit_after_restart False
```

同轮纯内存复现还发现审核事务顺序问题：缺 `target_unit_id` 的关系候选批准时抛出 `KeyError('target_unit_id')`，但候选已变为 `approved`。因此第一轮不仅要补恢复，还须先验证 payload/端点，再原子提交实体、候选状态与 revision。

**阻塞 B：图层 dry-run 不是生产检索结果（代码核查）。** `scripts/eval_retrieval.py` 自行对 pending 单元执行加权 IDF 排序；`CourseEvidenceBuilder` 当前从 Case matcher 的 `concept_anchor_ids` 扩子图，没有等价的教材单元召回。因此 hierarchy@1=0.867 是 **13/15 个合成问题的代理结果**，审核入图是必要环节，但不足以保证生产复现该指标。

## 26.2 建议拆成四轮，按依赖推进

| 轮次 | 范围与主要文件 | 完成条件 |
| --- | --- | --- |
| **第一轮：审核结果可恢复** | `course_store.py`、`course_service.py`、`graph_review.py`；明确种子包初始化与正式图权威状态，持久化 units/relations/cases/boundaries，审核与 revision 同事务提交 | approve/merge 后重建服务，实体、别名、Case 变体、来源、边界均保留；重复请求不重复入图；无效端点/merge target 不留下已批准状态；提交失败不造成内存与 DB 分歧 |
| **第二轮：Case 召回与求根小节正式检索** | `case_matcher.py`、`graph_repository.py`、`evidence_builder.py`、`fast_context.py` 和检索 evaluator；用新 benchmark 定位词面变体/条件混淆，复用现有中文索引/召回工具，为正式单元提供 Query 召回，与 Case 锚点和 typed relations 合并 | 教师只试审求根小节所需节点与关系，不先清空495条库存；未审候选不作正式证据；无 Case 命中也能找到相关正式单元；旧20题不退化，新增冻结题集分层报告改进与失败；关系端点可追溯；生产 Evidence Pack 与评测走同一检索入口 |
| **第三轮：数值证据改变教学** | 首先复用 `math_tools/verifier.py`、现有 Case 和 `hint_policy.py`，新增必要的求根数值 Oracle 与诊断接线 | 二分区间不变量、Newton 导数近零/循环/重根、残差与误差区分均有可审 reference 和容差；结果区分 supported/contradicted/inconclusive/tool_error；同一表面错误有不同证据时产生不同 probe/action |
| **第四轮：过程事件与对照评测** | 聊天工作流接 `StudentOverlayStore`，补实际帮助暴露和修订事件；在冻结题集上对照裸模型、普通 RAG、Case+Graph、Case+Graph+Oracle/Policy | event 带 unit/case/revision、实际 help level、验证来源，幂等且可重放；独立作答与受助成功分开；单次独立成功不能直接宣称迁移能力；回答质量与真实学生独立迁移/延迟保持分别报告 |

前两轮是下一次实施的推荐范围，第三、四轮仍是后续路线，不能一次全部标为“已完成”。第一轮优先于大批人工审核，否则教师审核会产生不可恢复的正式图改动。第二轮先用小范围教师确认的材料和已有15个Case验证链路，再根据失败家族补案例。

## 26.3 本轮授权的 benchmark 扩充

用户要求扩充 benchmark，最初指定 **AGY Staff / Gemini 3.8 Flash High**，网络阻塞后明确改用 **GPT-6 Luna 子代理**。交付保留旧20题回归，新增 **228题 v2**，覆盖15个现有Case family、条件最小对、13条静态代码片段、15条任务上下文、口语/英文、信息不足、11条课程域外与7条域内新Case需求；另有2条无法确定路由的样本，Case Recall分母明确排除这两条。

- gold 按数学前提、学习目标和允许教学行为设计，带理由与可接受集合；不以当前 matcher 输出反推标注，不改生产 matcher 来迎合本轮评测。
- 输出分层结果、错误样本、分母、版本/哈希、context 与能力限制；不支持的多轮信息须显式标注，不假装模型使用了历史。
- 普通运行可报告能力失败；评测器自身的计分/context/失败处理测试必须通过。真实 baseline 的付费模型调用另行安排，本轮保持离线。
- 244条检索集保留，pending dry-run 与正式图生产评测分别呈现，chunk/unit Recall 与 hierarchy accuracy 保持各自口径。

benchmark 的价值是确定下一轮该修哪些失败家族，而非通过增加题量证明教学效果。标注仍需要教师抽查；该条件未满足前，只称开发评测集。

**本轮已交付并复核。** AGY 因 Google 端点超时、代理续跑 `unexpected EOF` 未交付；未修改系统代理。Luna完成数据、评测器、评分测试与协议文档，主代理修复评测口径并按§4.5纠正两条未改变Case前提的标签。最终数据：`evaluation/case_matching_benchmark_v2.json`；协议与运行命令：`evaluation/CASE_BENCHMARK_V2.md`；生成器：`evaluation/build_case_v2.py`。数据哈希 `0c263dfc9c8646bcd43f0a77987439f8e97776e45d5efa94edf3e0903ab9e6a0`，生成器逐字节复现。原20题、种子包和生产matcher的SHA256保持一致，244条检索集未修改。

最终离线结果：Case Recall@1 **11/208 (5.3%)**；严格单标签决策 **34/222 (15.3%)**，6条多标签题不进此分母；全228题可接受决策集合命中 **34/228 (14.9%)**；域外检测 **10/11**，域内新Case需求检测 **7/7**。204题至少一项不匹配，198项Case不匹配、194项决策不匹配（有重叠），matcher异常0。输出保留所有失败样本、分层结果、题集/课程包/matcher源码哈希，异常仍计失败，严格模式可返回非零。缺失gold、空集合、未知Case或决策标签在匹配前报输入错误；评测不实例化CourseService、不读.env、不打开正式库、不执行题目代码。

最终 `npm test`：知识JSON校验通过、API **265 passed**（含新增9项评分回归）、前端 **12 passed**。低分说明该冻结开发集暴露了词面变体与条件路由的缺口，不是LLM数学答题质量评估；标注尚未经教师审核，不能直接作为正式教学验收门槛。第二轮因此需要同时改进Case召回与生产图检索，再进入Oracle/教学事件联动。

## 26.4 验证、范围和实施记录

第一轮使用临时数据库验证审核恢复、事务失败、重复审核、关系端点和 seed/revision 一致性；第二轮使用固定求根 fixture 验证正式图召回及来源，禁止直接拿真实 pending 候选自动批准。回归入口：

```powershell
npm test
$env:LUOJIA_NO_DOTENV='1'
python evaluation/evaluate_case_benchmark.py
python evaluation/evaluate_case_benchmark.py --benchmark evaluation/case_matching_benchmark_v2.json --output results/case_benchmark_v2.json
```

本阶段不扩跨课程、不做自动 curriculum planning、RL/StudentSim、全量自动审批或 Python/C++ 通用调试器；现有 `agents/code_executor.py` 禁止循环/函数定义，不能简单放开 AST 后就宣称已获得安全学生程序运行环境。先做受控 reference runner，学生任意代码执行另设隔离与资源限制任务。

实施遇到教材身份/来源不明、gold 无法确认、数据库迁移无可恢复备份或权限边界不满足时，停止对应写入并记录事实，不默认批准。每轮偏离计划及实测验收记录回写 `luojia_tutor2_branch_log.md`，复核后的优先级更新到 `CODEX_HANDOFF.md`。

## 2026-09-30 Prompt全面重塑（teaching-v2.1）

用户授权将prompt审查所列问题全部实施。主规范与三份参考指南已统一并真正加载，新增prompt_policy唯一策略入口，明确完整答案/direct优先。后台策略与不可信资料分开，Case条件/推理要点/匹配决策/来源进入prompt，探针不注入答案键。证明先审查，Verifier严格schema；工具执行成功与数学命题成立分开，失败降级。图片识别后真暂停，前端确认/编辑，草稿通过learning_meta持久化恢复。公开文案区分LLM意见与本步检查，错题卡不再使用硬编码的错误原因或正解。

详见 PROMPT_ARCHITECTURE_V2.md（按文件整改与证据范围）。最终离线npm test：API294、前端12、知识JSON通过；tsc通过；lint退出0、保留现有告警。测试进程使用SYMPY_GROUND_TYPES=python、MPMATH_NOGMPY=1绕开本机gmpy2本地扩展错误，conftest离线门控未变。新增20项prompt/流程回归。没有真实模型A/B、教师验收、真实浏览器上传或学习效果实验；v2题集/课程包/matcher哈希未变。已有服务需重启加载新prompt。未commit/push/deploy。


## 2026-10-01 — 响应式聊天 UI 与公式渲染修复

- 修复窄屏左右空白抽屉：Sidebar/LearningPanel 只渲染内容，由 MobileDrawer 统一控制显示、遮罩、关闭、焦点循环及跨断点恢复；桌面断点为 1024/1280px。
- 学习抽屉复用桌面状态/笔记内容，补齐移动端随堂笔记入口。顶部品牌/新会话避免换行，次要导航收进“更多”；输入区移动端取消常驻算子滚动条，简化工具文案，保持 16px 输入字体与底部安全区。中文 IME 确认不提交，粗指针设备 Enter 保留换行。
- 提取 message-parser.ts，修复同一行 $$…$$ 和 \[ … \] 的闭合处理，未闭合公式不吞后续空行/标题，保留代码与转义美元符号；加入 Markdown 表格渲染。原“膜振动方程”会话现已正常显示全部公式与后续标题，DOM 中 KaTeX 错误为 0。
- 学习面板取消未检查/无知识点时的默认 50% 展示，区分模型复核与本步检查；掌握度明确为估计。
- 验证：npm test（API 294、前端 17、知识 JSON 均通过）；tsc --noEmit 通过；lint 0 errors，原有 10 warnings。浏览器检查 320/390/768/1100/1440px、390x480 短视口，无整页横向溢出；Esc/关闭按钮/遮罩、Tab 焦点循环、跨断点关闭、移动端笔记切换与“更多”菜单通过。截图：results/ui-2026-10-01/mobile.jpg。
- 边界：未进行真实手机软键盘验证；开发服务器继续运行，因此未运行 next build；未提交/推送。框架仍为 Next.js 14.2.35。官方支持政策已将 14.x 列为不支持，建议后续独立迁移到 16.x 稳定补丁版，核对 React/API/lint 后再构建，不在本轮混入升级。

## 2026-10-01 Next.js 16 升级记录

前端已升级到 Next.js 16.3.8，React/React DOM 与类型依赖对齐19.3.0，`eslint-config-next`同步16.3.8。Next16移除`next lint`，改为flat config与ESLint9.39.5；增加`next typegen && tsc --noEmit`及CI独立lint。停Web dev后生产构建通过，完整离线npm test（API294、前端17、知识JSON）、typecheck通过，lint为0 errors/10已有warnings，前端全依赖npm audit为0漏洞。服务已恢复于`http://127.0.0.1:3000`；浏览器原会话48处公式0 KaTeX错误，390px抽屉可用且无横向溢出，图谱27节点/21关系，控制台0 error。业务API、正式图数据和matcher未在升级中改变；真实手机软键盘、线上模型及远端CI未验收，未提交/推送/部署。


# 27. 六个月推进时间线（2026-10-01 → 2027-03-31）

> **本轮交付**：完成前端框架升级，制定长期实施计划；本节中的课程图持久化、生产 Case 检索、数值 Oracle 和教学事件联动仍为待实施。保留既有研究与历史指标，不把计划写成完成声明。
>
> **计划口径**：日期是目标窗口，不是交付承诺。前半段以约每周 3 个集中开发日估算，首次闭环约需 14–19 个开发日；未确认团队产能、教师时间和学生招募。若产能不足或某道门槛未通过，移动后续日期，保持下列依赖顺序。2027 年的真人实验必须以教师合作、知情同意和适用的研究审查流程落实为前提。

## 27.1 本轮确认的主线与第一条可交付体验

按用户要求保留此前判断，作为未来六个月的优先级依据：

> 我觉得现在最缺的是 **“能根据学生的解题过程，定位错误并给出可验证反馈”的诊断闭环**。这是 Tutor 2.0 最值得优先做的功能。
>
> 结合这轮检查，建议按下面顺序推进：
>
> 1. **先让审核后的课程图真正保存下来。** 当前批准的节点重启后会消失，审核失败还可能留下“已批准”状态。这是后续功能的基础，优先修。
> 2. **让真实提问能找到正确的教学 Case。** 新增的 228 题里，当前规则 matcher 的 Case Recall@1 只有 **11/208**。学生换一种表述、贴代码或带任务上下文，就容易匹配失败。应接入实际生产检索，再判断对应哪个 Case、是否需要追问。
> 3. **做一个求根章节的过程诊断闭环。** 学生提交公式、迭代结果或代码片段，系统通过受控数值验证，区分“条件不满足、公式错误、停止准则错误、数值异常”，再给一个针对性提示，并检查学生修改后是否解决。
>
> 最后补上 **聊天过程事件记录**，才能回答“学生是在提示帮助下完成，还是已经能独立完成”，为学习效果评估提供依据。
>
> 如果只选下一轮的功能目标，我会选：**学生提交一次错误的求根过程 → 系统找到对应 Case → 验证并定位错误 → 给提示 → 验证修改结果。** 先把这一条做通，比继续扩大题库或课程范围更有价值。

实施顺序保留上述判断，但最小事件链随第一条诊断闭环一起接入；后续再完善状态归约和研究数据质量。否则闭环完成后仍不能复核提示是否展示、修订如何发生、一次成功是否受帮助。

第一条贯穿前后端的体验优先选 **Newton 更新公式错误**：学生提供 `f(x)`、初值及一个错误迭代步骤 → 召回 Case 和已审核条件 → 受控 runner 计算可核对的差异 → 给一条不越过当前帮助预算的提示 → 学生改写 → 再验算。缺导数、函数定义或任务目标时先追问；只根据一次数值执行描述该次轨迹，不宣称一般收敛定理被证明。

## 27.2 重新核实的起点与计划假设

| 项目 | 2026-10-01 证据 | 对排期的影响 |
| --- | --- | --- |
| 前端底座 | Next.js 16.3.8；React/React DOM 19.3.0；ESLint 9 flat config；升级验收见本轮交接记录 | 只做必要维护，不继续重做 UI |
| 审核结果 | `course_store.py` 没有正式 units/relations/cases/boundaries 表；`course_service.py` 只载入种子包；`graph_review.py` 先更新候选状态再验证/写实体 | 持久化与审核原子性为 G0，暂缓批量真实审核 |
| 课程起点 | 冻结种子包 27 units、21 relations、15 Cases；候选数量 495 是 9 月 30 日快照，不能当成本日库存 | 围绕求根小节少量教师核对，不要求清空候选库 |
| Case 匹配 | 本日离线复跑：228 题，Case Recall@1 11/208，严格单标签决策 34/222；0 matcher 异常；三项哈希与 §26 相同 | 先定位召回、条件判别和追问问题；不得用旧 20 题满分证明泛化 |
| 图检索 | `evidence_builder.py` 仍依赖 Case 锚点扩子图，未提供独立的正式单元 Query 召回 | pending 图层 dry-run 不是生产基线，需统一生产评测入口 |
| 过程数据 | `student_overlay.py` 和课程 events API 已存在；聊天未调用 `record_process_event`。现实现先 append event 再检查必填 outcome，事件与状态更新分开提交 | 先验证再提交，修复重复/失败语义；原始 attempt 可为未知结果，不能为适配 reducer 捏造失败 |
| 数值执行 | `code_executor.py` 仍禁止循环/函数定义；没有求根专用数值轨迹 verifier | 首版用受控 reference runner；学生代码先作静态证据或要求补轨迹 |
| 评测与合作 | 228 题为开发者标注，未教师复核；本轮无正式模型 A/B、真人试验和教师评审 | 教师 gold、独立测试集及合作窗口是后续外部依赖，不能由时间表替代 |

复跑输出：`results/case_benchmark_2026-10-01_plan.json`。历史 244 题 retrieval eval 与新 228 题 Case eval 测的是不同对象，保持两个分母与数据文件独立。

## 27.3 六个月里程碑与阶段门槛

| 目标窗口 | 阶段与交付 | 主要依赖 / 估算投入 | 退出门槛 |
| --- | --- | --- | --- |
| **10/01–10/07** | **M0 正式图可恢复**：正式图持久化、seed/version 初始化契约、审核事务、幂等及恢复说明；少量临时 fixture 验证 | 3–4 开发日；不操作真实候选批量审核 | **G0**：approve/merge → 重建服务后 units、relation、Case、alias、来源和 boundary 均保留；无效 payload/端点、不存在的 merge target、注入提交失败不改变已审状态；重复请求不重复 revision/实体；备份可恢复 |
| **10/08–10/21** | **M1 能找到教学 Case**：Query 对已审核 Case/units 的真实召回，条件与任务模式判别、UNCERTAIN 追问、生产 EvidencePack 一致评测 | G0；5–7 开发日；教师确认求根最小材料包与少量 Case | **G1**：生产与 evaluator 走同一入口；教材节点来源/版本明确，pending 不入教学证据；冻结开发集分层改进，建议目标 R@1≥70%、Case R@3≥90%，阈值须在教师 gold 校准前确认；旧 20 题兼容集合全过，OOD 至少维持 10/11且关键域外反例不误路由 |
| **10/22–11/11** | **M2 第一条可验证诊断闭环**：先做 Newton 公式错误，再纳入停止准则/数值异常；公式或轨迹输入、受控 Oracle、证据驱动提示、修订再验证、最小事件链、聊天反馈卡 | G1；6–8 开发日；可信函数表达式与容差 fixture | **G2**：10 条固定端到端 episode（含至少 3 条合法正确/替代路径）全部通过；错误可定位到具体步骤和证据；修订重验；缺条件追问；工具失败降级；合法替代路径不被误拒绝；无条件泄露 protected solution 的关键用例 0 失败 |
| **11/12–11/25** | **M3 求根单元完整化**：二分法/不动点/Newton，共 8–12 个可执行错误家族；事件与 Overlay 正式联动，提示暴露、帮助预算、独立探针；教师逐条核对输出 | G2；4–6 开发日；复用已有 CourseStore/Overlay，而非另建事件平台 | **G3**：同一 episode 可重放，重复、取消、流式失败和服务重启不重复记成功；有提示的修订只记 assisted；独立探针成功才记独立证据；用户与课程隔离测试通过；每个错误家族含错误、修订及合法路径控制例 |
| **11/26–12/16** | **M4 教师复核与冻结评测**：开发集标注校对；独立未见题/跨表示/合法替代路径集；Oracle 审计、版本 manifest、诊断/追问/披露分层评测与小型审阅台 | G3；4–6 开发日 + 2–3 次教师审阅；教师档期未确认 | **G4**：真实 gold 审核记录、分歧裁决、模板/函数/措辞族隔离、哈希冻结；只在开发集调阈值；独立集仅在候选版本冻结后运行，失败结果保留；可复现一整次评测，不以 R@1 单指标验收 |
| **12/17–2027/01/13** | **M5 小规模学生试用**：建议 10–20 名自愿参与者做可用性/误诊发现；记录真实设备、输入形式、延迟、失败、人工纠正和退出体验；准备评估协议 | G4；招募/教师许可/数据告知先落实；此规模只是试用目标，不是功效计算 | **G5**：阻断级误诊、用户数据混淆、不可解释验证全部清零或关闭相应功能；界面可区分证据/模型意见；跨表示与延迟测验流程可执行；只报告试用结果，不声称学习收益 |
| **2027/01/14–02/10** | **M6 冻结研究协议与系统版本**：确定对照、分配方式、主终点、样本量估算、缺失数据处理、教师盲评、成本/延迟预算；建立实验导出及版本锁定 | G5；用试用方差/可招募人数决定设计；假期和课程安排为缓冲条件 | **G6**：合作与适用研究流程落实；协议和分析计划先冻结再采数；对照条件可复现，保护任务难度与可用帮助量的可比性；缺样本时明确改为可行性研究 |
| **2027/02/11–03/17** | **M7 有对照的学习效果评估**：求根任务中的错误修订、无 AI 跨表示迁移、延迟保持；完成事先指定的消融与成本评测 | G6；招募与课程时间允许才开始；不在主试验中途调 matcher/Oracle/prompt | **G7**：主要结果按冻结协议报告效应与区间、退出与缺失；模型复核/数值证据/Case 路由版本可追溯；反面结果同样保留；教师评分分歧有记录 |
| **2027/03/18–03/31** | **M8 复核与扩展决策**：复现包、失败样例、贡献边界、研究报告/论文草稿；决定继续求根、扩一章或暂停学习收益主张 | G7；没有真人证据时交付工程/可行性报告，实验排期顺延 | **G8**：结论与证据匹配；不能把 BKT 上升、满意度或提示后成功当成学习效果；只有 G0–G4 稳定且教师资源落实才批准下一章节 |

G1 的数值目标是工程建议，不是既得结果，也不是保证真实学习收益的标准。独立集未建好前，70%/90% 只用于开发观察；不能反复看测试集并继续调参后仍称其为独立验证。若召回达不到目标，优先修代表性失败/任务条件/缺失输入；不通过把所有低置信度样本硬判为 SAME_CASE 来提高表面成绩。

## 27.4 接下来三轮具体任务（仅规划，未在本轮实施）

### 第一轮：持久化 + 审核一致性

改动边界：`apps/api/app/knowledge/{course_store,course_service,graph_review,graph_repository}.py`，必要迁移与 `tests/test_candidate_graph.py`、`tests/test_course_routes.py` 的回归。正式图保留 stable ID 和 course/version；种子包只用于初始化，不得每次重启覆盖教师已审核内容。第一轮明确“数据库是权威状态”，事务成功后再更新/重载内存；审核校验先于候选状态变化。revision 保留完整变更/来源，不能只保存实体 ID 就称可回滚。

实施前用 SQLite backup API 备份真实 course store 并检查 integrity；首轮开发和故障注入全部用临时数据库。校验 course_id/引用端点/教师权限、冲突审核和幂等键，测试单位/关系/Case/alias/boundary、失败提交及 seed 升级。现有 approved 但实体缺失的历史候选须先 dry-run 列表和来源检查，再做受控恢复；不能批量重置或再次审批。无可靠备份、来源不可确认或跨课程冲突时停止该数据库写入，保留异常报告。

### 第二轮：生产召回 + 条件判别

改动边界：`knowledge/case_matcher.py`、`case_repository.py`、`graph_repository.py`、`evidence_builder.py`、`tutor/fast_context.py`、`evaluation/evaluate_case_benchmark.py`。先复用现有 BM25/中文索引与元数据，再按结果决定是否用 embedding 或 reranker；没 key 时保留可复现的离线基线。把“召回候选”与“判 SAME/VARIANT/RELATED/NEW/UNCERTAIN”分开，记录 top-K、条件差异、任务上下文与追问原因。

让 Case 与正式单元检索共享明确课程/版本边界；将返回来源、Case 锚点、条件、typed relations 和 boundary decision 合成 EvidencePack。诊断所需的数据缺失只触发追问，不从 prompt 想象学生代码执行结果。以静态代码片段测试路由，不执行题目中的代码。生产评测同入口，case/top-K、unit recall、来源与边界分别报；保留未见 family/表述的失败样例，禁改冻结 gold 迎合 matcher。

### 第三轮：最小诊断闭环 + 最小事件链

建议新增求根专用受控 Oracle 模块（实施时确定路径，例如 `app/math_tools/root_finding.py`），复用安全表达式解析、已有 verifier 返回契约和当前 TutorWorkflow；不要另建多 Agent 框架。记录 `k, x_k, f(x_k), step_size, bracket, stop_reason, finite_flag`，Oracle/ToleranceSpec 显式带版本。至少覆盖 Newton 0↔1 循环、近零导数、残差小但根误差未证实、二分端点/变号与区间更新、不动点收敛条件、NaN/Inf/迭代上限和合法替代停止条件。用解析特例/高精度或独立参考算法交叉核对容差；不把 Python 运行成功等同命题成立。

诊断输出保留观察错误、候选假设、支持/反证、缺失条件、定位步骤、下一步 probe、建议行动；至少区分 `supported/contradicted/inconclusive/tool_error`。当前 runner 的 AST 限制保持，学生任意代码执行另设进程/文件系统/网络隔离与资源限制验收；没有隔离条件时只解析允许的参数/公式和已提交轨迹，不扩大执行权限。

最小原始事件：`attempt → verifier_evidence → diagnosis → hint_exposed → revision → verifier_evidence → outcome`；每条关联 `user/session/task/episode/attempt_id`、graph revision、Case/Oracle/prompt/model version、帮助等级、证据引用及原始输入摘要/受控存储引用。outcome 初始为未知，成功由 verifier evidence 产生；实际响应交付/展示后才确认 hint exposure。浏览器中断不能被当成已独立完成；直接讲解请求应按现有 policy 允许披露并记录帮助，研究测验的任务边界另行明确。

将观察事件与 Overlay 归约分开，验证通过后同事务存事件与状态，幂等按 episode/attempt/event；先验证必填字段再 append，失败不能“留下事件却没有更新，重试又被跳过”。用户身份来自认证 principal，不信前端 user_id 或 is_independent/is_success 自报；试用前补齐事件读写、Overlay、消息和证据导出的权限/租户隔离测试。

## 27.5 学习效果评估与后续扩展规则

工程指标：Case Recall@1/@3、条件区分、缺输入追问、边界违规、Oracle 正确性、错误定位、合法路径误拒绝、提示泄露、事件完整性、延迟和成本。过程结果：提示后的修订成功率、帮助量、重复同类错误与独立 probe 表现。主要学习结果：**无 AI 的跨表示迁移**；延迟保持作为预先指定的次要结果。三个层面分别报告，不能互相替代。

优先比较同一底座的普通课程 RAG 与“Case + verifier 证据 + 诊断反馈”版本；任务、底层模型版本和可用帮助量尽量一致，随机/分层分配或其他设计在 M6 说明理由。先用离线消融分析 Case 和数值证据各自改变了什么，再决定真实试验是否有足够样本做多个实验组；不预先承诺三四组同时上线。教师评分尽量不显示系统组别，评分规范与合法路径控制例先冻结。样本量按主要终点与试用方差估算，不预编显著性或效应大小。

下一章节以“同样可以验证算法过程”作为选择依据，候选为线性方程迭代法或数值积分；最多增加一章，先有教师材料/课程边界/Oracle/错误家族再排期。没有达到 G4/G5 时，继续修求根失败样例，不扩大题库与课程范围。复杂 KT、跨课程图、RL/StudentSim、30 天自动模拟、Lean 和完整运营后台暂不进入这六个月的承诺。

## 27.6 回归命令、记录与停止条件

本轮实际升级/离线复跑证据与未来验收命令分开；下列全量回归在每次实施轮结束执行：

```powershell
# 仓库根目录；测试继续离线，本机扩展兼容变量只设在测试进程
$env:SYMPY_GROUND_TYPES='python'
$env:MPMATH_NOGMPY='1'
npm test
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
# 停掉 web dev server 后再构建，完成后恢复服务
npm run build:web
$env:LUOJIA_NO_DOTENV='1'
python evaluation/evaluate_case_benchmark.py --benchmark evaluation/case_matching_benchmark_v2.json --output results/case_benchmark_v2.json
```

新增恢复/事务测试必须从 `apps/api` 跑，使用临时 SQLite；缺陷、Oracle、episode 重放、取消/重试、权限和教师 gold 回归随阶段补入全量 suite。Case evaluator 的非 strict 模式退出 0 表示运行完成，不表示所有能力样本通过；正式验收需检查结果和阶段门槛，必要时用 `--strict`，但不能要求尚未改进的基线全绿而删掉失败样本。

每轮记录到 `luojia_tutor2_branch_log.md`，同时更新 `CODEX_HANDOFF.md` 与本节状态表：实测、未验证、计划偏离和下个阻塞。新增模块的位置以实现时的最小改动为准，偏离方案须说明原因。生产数据库恢复不可靠、材料许可/来源未知、跨用户泄漏或任意代码隔离不足时停对应功能；未有招募/审查条件时不采真人研究数据。每两周复核日期与投入，每月复核错误家族/课程范围；不自动增加每周工时来追赶排期。

**计划复核**：覆盖用户要求、保留原判断、按依赖分期、列出失败/恢复和回归入口；功能扩展门槛与真实学习主终点明确。可行性仍受教师、标注与招募依赖影响，这些是未确认项，不能称所有研究阶段已就绪。本轮未实施 M0–M8 的业务改动；下一轮执行起点为 M0，首个检查为临时库重启恢复与审核失败原子性。

## 27.7 一年滚动展望（2027/04–09，暂不锁定开发任务）

前六个月集中验证求根闭环；后六个月根据G8结论选择方向，每月滚动修订。以下是条件性目标，不是与M0–M8并行实施的新增承诺。

| 目标窗口 | 条件性方向 | 启动条件与验收 |
| --- | --- | --- |
| **2027/04–05** | 若系统与教师gold稳定，最多迁移到线性方程迭代法或数值积分中的一章；若学习实验未完成，优先补完实验和求根失败家族 | 不降低G0–G5门槛；有教师材料、课程边界、独立Oracle与合法路径控制例。记录哪些诊断契约可复用、哪些必须重写，以迁移成本和诊断质量评估通用性 |
| **2027/06–07** | 对冻结求根版本做另一批次/课程的复核，或在新章做独立未见任务验收；完善教师审阅、材料版本更新和脱敏导出 | 合作与数据使用条件落实；保留课程/批次差异，不把不同终点直接合并。确认更新材料不会覆盖已审内容，旧episode可按原版本重放 |
| **2027/08–09** | 形成可复现研究包、教学演示和可维护的小范围试运行；根据证据决定论文投稿、课程合作或继续工程验证 | 汇总系统失败、学习结果、成本、延迟、教师投入和权限/恢复证据。是否提供公开服务另做容量、隐私、任意代码隔离与运维验收；此计划不等于授权上线。没有学习证据时只报告诊断/工程结果 |

一年后的成功标准是“教师能核对诊断、学生能完成可验证修订、研究能区分受帮助与独立表现、维护者能复现证据”。章节数量、题库规模和模型数量不作为主目标；未见收益或误诊风险持续时收缩范围并报告负面结果。

## 27.8 M0 / M1 工程实施记录（2026-10-01）

本节是最新执行状态，27.6 中“本轮未实施 M0–M8”指之前的规划轮。完整证据与恢复命令见 [M0/M1 实施记录](COURSE_GRAPH_M0_M1.md)。

| 阶段 | 本轮状态 | 剩余门槛与计划影响 |
| --- | --- | --- |
| M0 | 正式图完整 SQLite 保存、审核原子事务、CAS、重复回执、来源恢复与备份副本演练已完成，临时库回归通过 | 真实库未大批审核；已备份并初始化正式快照，候选计数保持。历史已批准丢失实体需人工核对，不自动重审 |
| M1 | 同一生产 matcher 接 API / EvidenceBuilder / evaluator；verified 单元召回、范围过滤、上下文任务重排与缺信息追问已完成 | 开发集参考门槛达标；教师 gold、独立未见任务验收和真实教学效果仍待完成，不能宣称 G1 全部通过 |
| M2 | 尚未实施 | 教师抽查失败家族及少量来源材料；随后建立受控数值 Oracle、诊断输入契约与提示后修订重验 |
| M3–M8 | 仍按 27.4–27.7 的长期计划滚动推进 | 保留每周投入与教师/标注/招募依赖，不因工程提前完成自动扩大范围 |

228题冻结开发集：Case R@1 从11/208提升至162/208（77.9%），R@3=200/208（96.2%），单gold决策200/222，域外11/11，新Case7/7；仍保留61题至少一项失败、0工具异常。原20题的Case16/16、可接受决策集合20/20，不能称多标签严格决策全对。题集和种子包哈希未改；此集已用于开发，不是独立泛化/学习效果证据。

本轮 npm test 为 API329、前端17、知识JSON通过；生产构建/typecheck通过，lint0错误/10已有警告。分批提交M0、M1+Prompt、基准、UI、框架和交接文档；未push、未部署。下一轮优先完成“错误求根过程 → Case → 数值验证定位 → 提示 → 修改后重验”，随后补事件链以区分受帮助与独立表现。

## 27.9 同轮图谱呈现修订（2026-10-01）

按用户指定的 Obsidian 设计语言，图谱采用圆点、细线、按关系数量调整大小、悬停/选中聚焦邻域，详细公式/教学内容留在侧栏。有界确定性力导向布局替代旧长带；卡片网格中间方案未提交。完整真实关系保留，布局表示关联而非教材学习顺序，节点大小不是掌握度。此轮不改变M0/M1数据、冻结基准或M2时间线。

修复选择触发重载、拖动回位、窄屏画布不居中与过滤旧请求；前端新增3项布局回归。最新全量离线API329/Web20/知识JSON通过，构建/typecheck通过，lint0错误/10已有警告；浏览器检查桌面、移动端、节点详情和问题定位。UI改动另批提交；证据见COURSE_GRAPH_M0_M1.md追加段。下一业务目标仍是教师复核、受控数值诊断与修改重验，不能以视觉改善替代阶段门槛。

## 27.10 联网检索修复（2026-10-01）

用户实测“OpenAI证明Navier–Stokes的思路”没有联网资料，且新闻提问错误进入证明审查。旧实现默认手动关闭，DDG非200/解析空/超时统一丢成空列表，1.8秒HTTP预算与2秒上下文窗口不足，逐轮无搜索状态。

本轮加入auto/on/off（显式关闭优先，设置本机保存）、时效/明确搜索/机构证明声称及猜想状态路由、常见Navier拼写归一化；新闻解释不进证明审查或无关课程检索/异步embedding。应用统一负责检索，不依赖未实现工具执行循环的模型原生搜索。Tavily可选优先，DDG失败或空结果转Bing RSS；公共通道仅尽力而为。总预算10秒，本地0.35秒窗口独立；取消请求清理全部检索任务。

success/empty/error/timeout/disabled、提供方尝试、来源与耗时沿提示词→SSE→learning_meta.web_search持久化。成功仅表示拿到摘要，不核验全文、日期、证明或用户前提；失败不得转成“已查证不存在”。来源文本视为不可信资料，过滤非http(s)/带凭据链接。回答框显示状态与来源链接，旧历史不补造搜索记录，无数据库schema变化。

验证：npm test API345/Web20/知识JSON通过；build/typecheck通过；lint0错误/10原有警告。离线回归覆盖DDG202转RSS、Tavily空转备用、超时/取消、链接过滤、失败敏感信息隔离、显式off、普通证明保留审查、新闻不进审查、提示词/SSE/数据库状态一致。独立联网烟测同主题返回3条摘要（含OpenAI链接）；这不等于已核验网页内容或证明。未调用真实模型做本轮答复验收。浏览器验证三档、刷新保存、390px无横向溢出/控件48px；截图results/search-repair-{desktop,mobile}.png；日志results/search-repair-*.log。前端服务http://127.0.0.1:3000/chat，API8000已恢复。分批本地提交，未push/部署。

界面使用ui-design Build模式，读取SKILL、aesthetic-direction、design-guidelines、colors、form-controls、surfaces、responsive-design。下一任务：只读审查代码生成图标/HTML/图表嵌入回答框的触发、隔离、移动端及失败状态；M2受控数值诊断计划不变。

## 回答框图标、图表与HTML审查（2026-10-01）

联网修复已分三批本地提交：c566913后端/回归、8bfffa0前端模式/来源、64188a4交接。随后按用户要求只读审查嵌入链路，详细逐文件9项见ANSWER_EMBED_AUDIT.md。P1是默认HTML脚本执行无网络/资源策略、未闭合流式预览、1/x跨间断点连成假零点、模型缺前端可视化能力协议；P2是SVG被清空、块边界吞内容、固定400px函数图、iframe高度/主题/失败反馈、图片API写死localhost。现有表达式Parser/HTML白名单/iframe非同源隔离必须保留，不夸大成已证明的主站XSS。辅助函数复现证据results/answer-embed-audit-repro.json，MDN支持sandbox/CSP边界。审查没有修改渲染代码或执行攻击样例；下一轮若实施，先静态安全与完成态渲染、再artifact协议/提示词/移动端/分段曲线。

## 回答图示安全与展示修复（2026-10-01）

用户授权修复 ANSWER_EMBED_AUDIT.md 的9项并分批 commit/push。新增 visual-v1：静态 HTML/SVG 主动预览、闭合与生成完成双门控、空 iframe sandbox、CSP 禁脚本/外联、惰性 template 白名单（60KB/1500节点）；不扩大原宿主 sanitizer。SVG viewBox 自适应高度，HTML 手动有界高度、深浅主题、失败/源码回退；XML仅源码。图片复用统一 API 基址，协议/凭据过滤、来源/失败提示，外部图片点击后才加载。裸 HTML 根边界及 plot/bilibili 段落边界修复。

函数图保存 segments 并探测采样间隔，奇异点不跨段连线；响应式 SVG，范围内才画零轴，异常数值范围拒绝。间断检测仍为启发式，图示不能作为连续性/根存在性/证明证据。teaching-v2.2 加载 references/visual-artifacts.md，前端声明图形与后端 math/SymPy 验证能力分清。

离线 npm test：API346/Web26/知识JSON通过；build/typecheck通过；lint0错误/10已有警告。日志 results/embed-repair-*.log；浏览器临时独立预览验证静态清洗、无脚本沙箱、生成中0 iframe、XML源码、主题、390px无横向溢出，截图 results/embed-repair-{desktop,mobile}.png。临时路由已删除，未改真实会话、未调用真实模型、未做正式渗透验收。完整关闭项与限制见 ANSWER_EMBED_AUDIT.md 实施回执。

服务已恢复 Web3000/API8000。M2求根过程诊断闭环、独立教师gold与学习事件评估仍为后续主线，任意生成JavaScript不作为诊断Oracle。提交分为静态渲染安全、函数图语义/响应式、提示词协议、实施回执四批；推送结果以当前回合最终输出为准。

本轮实现提交：dfd8792 静态预览与生成门控；25ca8fb 分段函数图与响应式；e646c16 visual-v1 提示词协议。文档回执另批提交，用户已明确要求 push 当前分支。

# 28. 竞品启发的功能规划与六个月主线整合（2026-10-02）

本节补充§27，保留原“可验证诊断闭环”的判断和历史排期全文。用户已选择融入现有主线，并希望利用AI加快开发、保留后续功能；据此形成[完整规划入口](planning/learning-experience-2026-10/README.md)。新的产品功能目标窗口见该文§5，原§27各数学/数据/研究门槛保持，历史完成状态以实际验收回执更新。

| 优先层 | 方向 | 详细方案 | 与现有主线的关系 |
| --- | --- | --- | --- |
| 基线 | 核对当前求根WIP与旧文档差异 | [B0](planning/learning-experience-2026-10/00-baseline-and-gates.md) | 先确认已有Oracle/修订/ack/probe/重放，不重做同名功能，不凭源码存在宣布M2/M3通过 |
| 核心 | 今日任务＋间隔复习 | [F1](planning/learning-experience-2026-10/01-daily-study-and-review.md) | 复用M2/M3结果与实际帮助暴露；从静态复练/一次低掌握提醒走向可恢复任务与持续到期调度 |
| 核心 | 教材伴读＋条件卡 | [F2](planning/learning-experience-2026-10/02-source-reading.md) | 复用正式图、原文与来源；材料授权/版本确认后可先做，不等全套任务系统 |
| 核心 | 交互数值实验台 | [F3](planning/learning-experience-2026-10/03-root-lab.md) | 提交轨迹Oracle与生成参考轨迹runner分工；先预测再操作，自动轨迹记帮助 |
| 后续 | 章节诊断、文字讲回、视频伴学、教师简报、代码作业 | [F4–F8](planning/learning-experience-2026-10/04-extensions.md) | 全部有首版与启动条件；测评接M4/M6，简报服务M4/M5，字幕/代码隔离单独验收 |

规划估算58–85开发日，另留约10日集成/返工；沿用每周约3开发日的未确认假设，首两周校准实际产能。AI可加快代码与回归草拟，不能代替教师gold、真实反馈交付、学生招募、独立评分与延迟测验间隔。没有承诺所有高位估算在2027/03前交付；产品候选开发不得改变冻结的学习实验版本。

成绩与学习结果边界：阅读/实验操作完成、受助解对、独立解对分别记录；未知/失败/过期保留恢复路径；LLM讲回评价不独立提升数值表现；一次独立probe不称迁移能力已验证。课程图、任务、来源、Oracle、帮助与模型/policy保留版本，可复核与重放。

本轮仅写七份规划文档及项目记忆，未主动改业务代码/真实数据/冻结gold/seed，未运行应用测试、构建、正式模型或真人验收，未commit/push/deploy。实施偏离、真实工时与回执写[implementation-notes](planning/learning-experience-2026-10/implementation-notes.md)。下一步为B0现有求根流程验收；教材伴读可在材料权限与版本已确认时独立开展。


# 29. M2/M3 工程候选验收（2026-10-02）

本节更新§27.8的“尚未实施”历史状态，保留原长期计划与新增产品规划。用户授权 M2/M3 与动态 HTML 恢复。实施/运行方式/数据与限制见 [COURSE_GRAPH_M2_M3.md](COURSE_GRAPH_M2_M3.md)。

| 阶段 | 当前证据 | 仍需完成 |
| --- | --- | --- |
| M2/G2 工程 | 受控公式/轨迹Oracle、Case→错误步骤→提示→修订重验；10生产LangGraph/SSE固定episode含3合法替代；缺条件/工具异常/披露门控回归 | 教师核对开发例数学与教学输出；自由文字/截图不能假装已结构化验算 |
| M3/G3 工程 | 三种求根法12家族、13/13错误/修订/合法控制三元组；事务事件/Overlay、显示ACK、提示预算、服务器探针、重复/取消/断流/重启/并发/隔离 | 教师逐条复核仍待完成，未宣布完整G3；尚无真人帮助暴露/独立过程观测 |
| M4 | 未实施，接下来优先 | Oracle与容差独立审计、教师gold、分歧裁决、未见函数/表示族、冻结与可复现评测 |
| M5–M8 | 原长期计划继续滚动 | 招募、无AI独立测验、延迟保持、研究对照与写作不能被工程提前完成替代 |

受控输入与数值参考不执行任意学生程序；小残差不冒充根误差，g不动点界不冒充f根误差，区间无法确认不宣判发散。Oracle/Tolerance版本v1，工程源码/fixture哈希见 evaluation/root_diagnostic_manifest.json，开发集不是教师gold。Case是数值家族引导的生产matcher调用，不将它解释成自由提问检索泛化成绩；原228题及244题数据不改。

成功仅由服务端证据与反馈显示ACK产生，初态未知；有帮助修订只记assisted，普通正确记observed，首次服务器探针成功仅一次独立证据/probe_observed。任务参数和初值锁定，至少两步；已发探针函数避免重发记新证据。图示、讲回、自动实验不替代独立完成；课程事件与消息库不声称跨库原子。

动态HTML按visual-v2恢复：闭合完成态/主动运行、独立无同源allow-scripts沙箱、禁止外联/eval，错误/停止/重启与30秒定时卸载；任意JS不是Oracle，浏览器定时器不是死循环CPU强杀隔离。原“开场白后无回答”的SSE鉴权/超时/EOF状态已修，失败部分回答不可运行预览；未改模型凭证，未做真实模型生成或正式渗透验收。

本地验收npm test：知识JSON/API415/Web30；build/typecheck通过，lint0错误/10既有警告；浏览器390px主表单/Canvas交互/停止/重启/错误/门控通过。日志results/m2-m3-*，临时验收路由删除。§28的新增功能规划是独立并行文档变更，未随本轮代码打包提交；研究冻结版与候选功能仍须隔离。


## 2026-10-02 — F1–F4首版实施与本地验收

用户授权“先开干f1-f4”，并补充自检通过后可升级。实现今日任务/间隔复习、课程摘录/私有教材选段伴读、三种受控求根参考实验、六题章节诊断；自检后开放参考计分、薄弱知识点和复习入口。页面 /study /reading /lab /assessment，共用LearningWorkspace与CourseStore.learning_records，复用RootEpisodeService/Oracle；数学状态、显示ACK、owner和重复请求均由服务器决定。每日study session限制复习升级；实验曝光从probe池排除，进行中的首次独立probe不允许新参考实验或伴读解释；未知不计成功。

原规划及回执：`planning/learning-experience-2026-10/f1-f4-delivery.md`。runtime课程库优先COURSE_STORE_PATH，文件SQLite缺配置则派生 `.course.db` 持久库；测试临时库/离线门控保留并在结束时关闭连接。原文从markdown按实际字符范围读取，哈希变化拒绝旧请求；模型输出仍未数学验证。F4是章节练习参考计分，不是研究gold/独立测验。

最终本地npm test：知识JSON/API445/Web34；typecheck/build通过；lint0错误/10既有警告。隔离演示库浏览器完成练习→确认→probe→复习、伴读/笔记刷新、原文引用/无模型降级、参考轨迹对照、六题83分/复习入口、弃测与390px/1440px布局。证据results/f1-f4-*；没有真实模型、真人学习收益、教师gold或远端CI证据，未修改冻结seed/gold，未commit/push/deploy。

首版取舍：四张开发条件卡、固定Newton练习及开发probe池；旧版本已开始任务不自动替换；未完成完整PDF标注、研究测验隔离/监考、人工评分和F5–F8。保持原六个月求根诊断/迁移/延迟保持主线，不用工程验收替代学习效果。

## 2026-10-02 — 首页与F1–F4增强、F5/F8候选交付

用户授权加强F1–F4，更新首页并启动F5/F8首版。首页接入只读学习记录与未完成任务，不在GET时生成计划/更新学习证据；来源版本过期任务不推荐直接开始。F1支持计划外/跨日任务继续，F2原文章节笔记隔离，F3参数/预测草稿和实验链接恢复，F4自检指定结果链接恢复。六入口与现有对话/笔记/错题/图谱衔接；用户提供Logo原样接入，中文字体层级、留白和减少动画适配完成。

F5绑定课程来源/哈希，保存讲回、条件引用、自我对应与补充版本；引用真实性不等于条件正确，模型意见不提升独立成绩。F8在C0未验收时走原规划静态降级：AST有限提示、手动轨迹复用RootAttempt Oracle、版本对照；代码未执行，轨迹支持不能证明程序正确。F5/F8在未完成独立probe期间阻止参考帮助。没有新增数据库表或依赖，原学生代码执行边界保持。

当前本地证据API458/Web35/知识JSON、生产build/类型检查通过，lint0错误/10原有警告；隔离演示库浏览器验证桌面/手机、状态恢复、版本、帮助保护与确认。实现回执planning/learning-experience-2026-10/home-f5-f8-delivery.md；不替代§27教师gold、无AI独立学习测验、迁移/延迟保持或C0/C1执行验收。F6/F7仍在规划。真实模型/真人学习收益/教师/远端CI未验证，未commit/push/deploy。


## 2026-10-03 小珞、教学流程审查与 F1–F4/F8 加强

用户授权加入数学学姐形象“小珞”、检查明显不符的流程/设定/提示并直接修复，随后授权在五小时额度耗尽前继续加强薄弱处。本轮原样接入小珞 PNG 到首页/聊天欢迎区，明确 AI 身份；统一独立 probe 的新帮助保护（普通聊天/笔记/相似题/求根提交），保存每条回答自身教学模式和检查状态，修正模式与任务意图冲突、相似题未持久保存、抽样教材笔记全书措辞及提示数据边界，新增根主题开发参考题。teaching-v2.4；计算执行与数学语义验证明确分开。

F1 反馈待确认时锁定输入和新提交，保留幂等重试；F2 原文段落追加笔记草稿且刷新恢复；F3 逐步/播放/暂停/同条件轨迹对照/历史回看与按实验保存的本地复盘；F4 未确认选项按 owner/测评恢复、题号导航与确认进度；F8 已保存行号定位、未提交修改提示、两版原文对照、tol/max_iter 使用与 solve 本体作用域静态检查。学生代码仍不执行，提示/手动轨迹不提升独立成功。无新增表/依赖。

本地最终 npm test：知识JSON/API469/Web39；生产build及TypeScript通过；lint0错误/10原有警告；diff check通过。浏览器在隔离演示库验证五类增强、首页与聊天形象，以及390px实验布局；未调用真实模型。日志 results/f1-f4-f8-strengthened-*.log。完整审查、修复与剩余弱项见 planning/learning-experience-2026-10/xiaoluo-chat-lab-review.md。真实模型/教师gold/真人学习收益/C0/C1/远端CI未验证。数学语义Answer Guard及动态HTML同步JS的CPU强制隔离仍未闭合；历史内容/外部帮助无法由当前应用保护排除；完整PDF标注、跨设备本地草稿与静态规则版本回执后续再做。未commit/push/deploy，保留原工作区成果与无关原型。额度读数91%时结束新功能扩展并收尾。

## 2026-10-03 登录体验补查

用户指出登录系统未同步更新。当前Git历史显示真实Web鉴权接入于2026-09-08，后端后来有课程权限维护；本次没有重写鉴权协议。已修复聊天退出只跳转不清凭证：清除token/owner/演示键，完整跳转以卸载owner相关页面状态，保留学习草稿；桌面/手机均可退出。注册移除不保存的院校/专业，称呼/账号区分，账号格式与服务端一致，补齐label/自动填充。登录/注册成功进入今日学习。鉴权布局加入Logo/主题/首页返回，删除无依据的SECURE CONNECTION标语。

本轮前端40项通过（新增退出清理回归）、生产build/类型检查通过，lint0错误/10既有警告；后端未改，本轮未重复API suite，上一轮API469是之前的证据。截图results/auth-login-updated.jpg。没有实际注册/登录真实账号、密码重置或远端验证；当前isolated demo API没有配置token secret，不能以演示界面验证真实签发。剩余：密码找回、邮箱验证、服务端token撤销/刷新、过期引导与跨标签页状态；注册在签发配置缺失时先创建用户的非原子流程也需后续修复。未commit/push/deploy，五小时额度约94%时只做收尾。

## 2026-10-03 分批提交准备

用户明确授权分批提交并推送，按四个边界：后端学习与教学规则、学习工作区与品牌形象、登录体验、规划及交接记录。提交前重跑npm test：知识JSON/API469/Web40全部通过；最新auth-followup生产build与类型检查通过，lint0错误/10既有警告，diff check通过。git grep sk-检查仅发现说明文字/普通标识符/既有二进制匹配，新增源码/规划未检出匹配的凭证格式。既有egg-info、demo-jiuzhang-hybrid.html、style-explorer.html、ui-proposals、ignored results/数据库/env不纳入。

首版后端包含learning_records表、课程持久库派生路径和tzdata依赖；COURSE_STORE_PATH显式优先，离线测试门控保留。当前分支feature/course-graph-2.0。远端fetch首次因GitHub443连接失败，当前remote-tracking ref不是实时远端证据；推送将在提交后单独尝试并报告，本文不提前宣称已推送。


## 2026-10-03 README 更新与海报提示词交接

用户要求更新 README 与海报提示词，后要求直接生图，再明确表示海报由自己生成。README 改为当前六入口 F1–F5/F8、快速开始、Newton 循环/收敛体验例与能力边界；历史 V8 样本结果不冒充当前求根效果。`.env.example` 只更正课程库派生持久路径的旧注释，没有修改配置值、业务源码或冻结数据。完整/精简生图请求保存于 planning/learning-experience-2026-10，入口 poster-update-prompt.md。

本轮 npm test：知识JSON/API469/Web40通过；本地文档链接无缺失、Newton 示例离线核对与diff check通过。日志 results/readme-update-tests.log。未从干净环境重装依赖，未重复build/真实模型/教师gold/真人评测。内置imagegen两次网络错误，第三次请求按用户指示停止；没有新图，旧海报/原Logo/原小珞保留。交付PNG与视觉核验由后续生成结果决定，不承诺提示词分辨率、可编辑文字层或效果。

此前四批047f134/f875b3e/381c0d6/65ece36已推送，fetch核对本轮开始时本地与远端feature/course-graph-2.0一致。当前文档及提示词按明确清单提交，提交/推送回执在最终交付分别报告；无关原型/egg-info、ignored results、数据库/env不纳入。研究主线、教师/独立与延迟测验门槛不变；没有远端CI或部署证据。


## 2026-10-03 用户新版海报接入与 v1 归档

用户自行提供新版 PNG，并明确要求原海报改名为 v1poster。新附件原样接入根目录 LJ_Tutor_Poster.png；原图归档为 v1poster.png。两图实际1055×1491，SHA256分别为3803c9ed3683cc6dc3c03b0aa85c2c5371ef910531c55095c57e8ee1ceb3a8e4、5935f08d8171c0c8f1042dd0e1c481506ff2db955d42b8bdbabf8edc711e115b，均与各自原文件一致。README 展示新版、折叠保留第一版，poster-update-prompt.md 更新实际交付记录；未重新生图或修改 Logo/小珞素材。

已核对六项功能、代码未执行标注、Newton 四个近似值与先越过再趋近的示意。海报为静态展示，不是生产运行或学习效果验收。文件哈希、文档链接和 diff check 通过；业务源码/配置/冻结数据未改。本轮离线 npm test：知识JSON/API469/Web40全部通过，日志 results/poster-asset-update-tests.log；提交/推送回执单独报告；只提交本轮图片及相关文档，保留既有无关原型/egg-info，未部署或重跑真实模型/教师/真人评测。上一节“未替换海报”是当时历史状态。


## 2026-10-03 Agent 可靠性修复与实习方向规划

用户要求参考成熟 Agent 项目提升工程能力，目标岗位为 AI 应用 / Agent 工程；随后要求修完后先交规划，已确认可靠性与评测优先。本轮只实施 A0：模型 finish_reason / EOF / 空正文 / 缺配置等 typed failure，不发送假 done；不确定意图在 context 学习写入前确认，仍未确定先澄清；最终 intent 重新选择核验模式；数学工具用类型化结果和退出码判断成功，取消 / 超时 kill、通信回收并清理脚本；缓冲时间改名 generation_buffer_ms。未增加依赖、数据库表或放宽 AST / F8 学生代码执行边界。

最终完整 npm.cmd test 退出 0：知识JSON/API501/Web40全部通过（API较上轮新增32项）；5条既有弃用/绘图警告。首轮两个旧API用例依赖缺配置文案当正常回复，已换显式离线成功fixture并补缺配置/无上下文澄清回归，生产未加fake。日志 results/agent-reliability-tests.log。diff check、规划链接及新增源码凭证格式扫描通过；前端源码未改，未重复build/lint。

规划入口 planning/agent-engineering-2026-10/plan.md，配套 audit.md / implementation-notes.md：A1有界交付Guard → A2本地持久执行回执 → A3离线失败评测为首个里程碑；A4任务快照与可纠正记忆、A5真实模型评测及求职展示随后。参考 LangGraph、OpenAI Agents SDK、Dify、Letta 官方文档，不迁移框架。后续A1–A5尚未实施，先供用户评审；完整数学语义Guard、学生代码C0、教师gold/真人学习收益、远端CI/部署未验证，已有回归通过不代替独立benchmark或真实模型质量。

限定聊天/服务端数学工具两surface的AX审查记录18检查、16唯一规则；12pass/1warn/1fail/4unknown，观测型缺真实交互保持unknown，未夸大整体发布验收。剩余缺口是正文/实际执行证据关联和记忆来源/纠正。六个月求根主线、独立probe帮助保护及原始事件/成绩权限不变。

实现025ec54已推送feature/course-graph-2.0并核对远端SHA；规划与交接另批，最终推送以本轮回执为准。之前12255a5是新版海报/v1归档已推送状态。仅提交清单内内容，保留无关egg-info、三个Web原型目录/文件以及ignored结果、数据库和env。

### 2026-10-03 A1 交付守卫

A0 45 项针对回归再次通过。A1 默认交付检查、一次文字修复、未通过候选拦截和 UI 证据边界已实现；全量 API537/Web41/知识 JSON、typecheck 通过，lint 无错误。检查通过不表示数学正确，规则首版是显式高精度模式，语义覆盖待 A5。用户已授权继续 A2 持久执行回执；构建/界面及推送将在集成验收后完成。

### 2026-10-03 A0–A2 Agent 工程实施结束

用户授权顺序实施；A0 已完成并复验，A1 5197ddf 交付检查 / 一次文字修复后继续 A2。A2 新 schema6 / run-v1 持久回执、原子消息终态、64事件上限、owner与seq条件更新、取消 / 重启过期、重试关联、折叠过程与刷新历史。ASGI断连有主动监听，取消会等待图 / 子进程和数据库写入清理；租约30s续租/120s过期，启动或读历史恢复过期记录，不自动重放。回滚保留新表，正式库启动前SQLite backup；本轮仅临时/隔离演示库迁移。

离线API559/Web43/知识JSON、typecheck、lint0错误10现存警告、生产构建通过；浏览器桌面/390px、修复/拦截/取消/刷新/键盘检查通过。所有run仅执行范围，交付守卫不证明数学正确；F8仍不执行学生代码，usage和未审定自定义模型别名为null。A3独立失败评测CLI未做，A4记忆/A5真实模型待实施。完整回执：planning/agent-engineering-2026-10/delivery-a0-a2.md。远端CI/部署/教师与真人学习效果未验收。

### 2026-10-03 A3 与多领域扩展

用户授权 A3 → 线性方程组 → 数值积分。A3 已新增版本化 manifest 和独立离线 CLI，19 个合同 / 40 个实例通过首跑；缺失、跳过、失败、重复实例不能绿色。CI 增加该命令及报告 artifact。复用实际图 / SQLite / 工具 fixture，结果限定为离线协议。多领域模块待实现，A4/A5 未实现。

A3 全量复验：知识 JSON、API 563 / Web 43 均通过（results/a3-full-tests.log）；报告解析器另覆盖缺失 / 重复 / 跳过 / 失败。无模型调用或部署。

### 2026-10-03 多领域数值实验首版

A3 已实现，终止门控 / Guard 两次临时破坏均被 CLI 检出，源码已恢复。线性方程组（Jacobi / Gauss–Seidel）及积分（梯形 / Simpson / 自适应 Simpson）共用 numerical-lab-v1 请求 / 结果与既有 owner 学习记录，入口 /numerical-lab。支持预测、步进 / 播放、方法对照、历史 / 参数复用、数值核对；source hash 与幂等请求 ID，自检 / probe 未完成时阻止参考读取、运行及核对。无新依赖 / 迁移 / 学生代码执行 / 独立成绩更新。积分估计不是严格界，sin(16*pi*x)^2 提供采样遗漏反例。聊天入口仍是复制用户上下文，A4 可信任务快照与 A5 真实模型评测未完成。交付细节见 planning/agent-engineering-2026-10/delivery-a3-numerical.md。

最终全量：知识 JSON、API 583 / Web 45；生产 build / typecheck 通过，lint 0 错误 / 10 既有警告。新实验计入首页实验记录总数，保留 owner 隔离；无数学掌握度写入。隔离浏览器完成迭代 / 积分 / 参数复用 / 刷新 / 390px 与反例分段对照；截图 results/numerical-lab-desktop.jpg 不提交，演示 DB 与服务均保持隔离。

### 2026-10-03 Runtime 意见审阅与六个月主线衔接

以当前150553b审阅用户提供的意见（其代码基线ee373ae），确认模型生成Python文本协议、usage丢弃、无图checkpoint为实际缺口；新线性/积分实验已交付但尚未形成可信实验聊天快照。意见不是实现授权，本轮只更新规划/README与交接，不实施A4–A8。

推荐 A6 工具类型/权限/预算/计算证据 → A4 可信实验快照与统一上下文预算 → A7 span/真实用量/必要模型能力 → A5 E1/E2/可选真实E3，原A4/A5编号保留。A8单路径持久暂停恢复PoC有条件启动，不叠加会话/学习事实权威；interrupt恢复会重执行节点，需崩溃注入、owner、过期和重复恢复幂等验证。C0学生程序执行仍独立验收。

主线11–17个集中开发日含回归余量，单人每周约3日为4–6周；人工数学gold复核另计，收费批量受预算/Key/价格与用量条件约束。S1工具、S2跨领域讨论可分阶段展示。E0合同通过、E1工具行为、E2数学教学质量和E3模型辅助任务完成分别报告，均不替代教师gold、学生无AI独立测验与延迟保持效果；数值参考/积分误差估计不抬升独立成绩。

详见planning/agent-engineering-2026-10/runtime-review-schedule.md、a6-tool-runtime.md与主规划第7节；README“A3尚未完成”已修正，代码/配置/研究冻结材料不变。本轮提交前完整npm.cmd test：知识JSON/API583/Web45通过，日志results/runtime-planning-tests.log；65个本地文档链接/锚点、UTF-8、范围和diff check通过。仅文档变更，未重复build/lint；提交/推送以最终回执为准，无新增真实模型/教学收益/远端CI/部署证据。

### 2026-10-03 产品衔接意见与保护边界校准

用户追加聊天/工作区意见。审阅0340c49确认缺可信当前任务引用、动作卡片与六工作区内嵌聊天；已有RootDiagnosticCard/probe/run与NotebookChat，不应称“只有Markdown”。来稿Newton f=x³−2x+2从-2出发第一步-1.75有误，实际-1.8。

发现共享helper只管probe、旧root-lab缓存/历史绕过与伴读选区检查不一致。局部修复612e3a4，章节自检期间也保护新参考帮助；新run/缓存重试/历史读取/伴读解释共用检查。新增检查6红1绿复现后，针对72项、完整JSON/API589/Web45通过。原始题目、首次作答、分数、独立成功/掌握度规则不变，无迁移/新依赖/前端改动或真实模型调用；不能声称收回旧材料、外部帮助与全部在途请求。

主线顺序修订A4.1可信Newton实验→A6.1/A4.2业务动作/卡片/内嵌聊天→A6.2计算工具及旧Python退役→A7→A5，先一条实验讨论/参数预览/显式保存闭环。12–19个集中开发日含回归余量，每周约3日约4–7周、人工复核另计；全F1/F2/F5/F8、A8/C0另估。已有线性/积分保留，后续复用合同；LearningAction不建第二工具层，预览help事件必须进入probe选题与预算，系统轨迹不作为学生attempt/BKT/独立成绩证据。章节自检仍是开发参考题训练，不能升级为研究独立probe。

当前规划入口planning/agent-engineering-2026-10/chat-workspace-review.md；主规划、Runtime/A6、README与Deviations同步，A4–A8未实施。A5对照基线改为修复后的612e3a4；工程/模型辅助多轮结果继续与教师gold、未见题无AI迁移和延迟保持分开。A3离线契约19/19、实例40/40通过，报告SHA=612e3a4且文档修改期间tracked_worktree_dirty=true；75个本地链接/锚点与UTF-8检查通过。最终提交/推送以本轮回执为准，未宣称远端CI/部署/学习收益。
