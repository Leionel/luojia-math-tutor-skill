# 架构与源码入口

系统以一次学生主张为编排单位。Chat 与学习工作区共用对话和引用协议；每次使用保存结果，都由服务端重新检查归属、版本、内容和帮助状态。

## 一次回复经过哪些步骤

```mermaid
flowchart LR
    A[学生输入与工作区引用] --> B[上下文与教学策略]
    B --> C[有限数学核验与课程检索]
    C --> D[模型教学决策与回复]
    D --> E[交付检查与一次修复]
    E --> F[流式交付与来源记录]
    C --> G[符合资格的候选记录]
```

| 层 | 源码入口 | 作用 |
| --- | --- | --- |
| 编排 | [graph.py](../apps/api/app/tutor/graph.py)、[fast_context.py](../apps/api/app/tutor/fast_context.py) | 收集当前输入、历史、学生状态和引用；组织 Teacher 调用与交付 |
| 教学策略 | [teaching_decision.py](../apps/api/app/tutor/teaching_decision.py)、[proof_tutor.py](../apps/api/app/tutor/proof_tutor.py) | 限定教学动作、证据引用和提示方式；证明辅导沿用模型审查 |
| 数学核验 | [step_checker.py](../apps/api/app/math_tools/step_checker.py)、[safe_symbolic.py](../apps/api/app/math_tools/safe_symbolic.py)、[verifier.py](../apps/api/app/math_tools/verifier.py) | 抽取有限候选，用显式数学构造器在受控 worker 中计算，保留定义域和适用范围 |
| 回复交付 | [answer_guard.py](../apps/api/app/tutor/answer_guard.py) | 检查直接泄露、核验越界及部分显式结论冲突；失败进入一次修复或停止交付 |
| 定向检索 | [targeted_retrieval.py](../apps/api/app/knowledge/targeted_retrieval.py) | 针对教学动作读取少量本地课程条件证据，附来源摘要与版本 |
| 学习工作区 | [learning_workspace.py](../apps/api/app/tutor/learning_workspace.py)、[learning_extensions.py](../apps/api/app/tutor/learning_extensions.py) | 保存实验、阅读、讲回、自检与代码版本，校验讨论引用和操作资格 |
| 策略比较 | [policy_comparison.py](../apps/api/app/tutor/policy_comparison.py) | 在资源和帮助状态匹配时比较记录；当前是离线工具，尚无真实教学效果结论 |

## 模型意见与数学核验

模型负责解释、诊断和反馈选择。`TeachingDecision` 是受 schema 和证据引用约束的模型决策，不能替代数学真值或直接写入掌握度。

确定性核验只覆盖有限语法中的局部候选。结果携带核验器版本、输入与候选摘要、来源、范围、执行状态、条件和学习证据资格。系统计算出的参考值、未定式分类、模型审查和学生步骤核对保持不同标记。

`step-v2` 从原始十进制字面量构造精确有理数，并在构造前限制位数和指数。旧 `step-v1` 记录保留原版本，不当作当前核验事实。服务端只用匹配当前输入的完整学生候选结果约束模型决策；`delivery-v3` 回复检查还能阻止部分明确的反向判词。前端兼容保留的交付检查版本。该检查不能识别所有自然语言数学错误，反例见[数学反馈边界](../evaluation/math-feedback-boundaries.md)。

模型工具调用与上述固定步骤检查是不同入口。类型化模型工具由 `TYPED_MATH_TOOLS_ENABLED` 和 `LLM_CAPABILITIES_JSON` 控制，默认关闭；配置必须对应实际 endpoint/model 已验证的能力。可选 `LLM_PRICES_JSON` 是运维提供的计价信息，不能自动证明供应商支持某项能力或费用预算已生效。

## Course Graph 与来源

课程存储维护知识点、教材来源、定理条件、候选内容、审核记录与正式快照。检索将本地词法结果、课程关系及可选语义信号用于上下文；定向检索再按当前教学需要读取经过发布筛选的条件片段。当前定向分支受数值分析求根主题限制，不代表其他数学领域已有同样覆盖。

正式图更新经过审核及版本冲突检查；学生覆盖层与正式课程内容分开。教材选段绑定来源与内容摘要，历史引用不应无声切换到新版。`verified` 表示内容在这套发布流程中的状态，独立数学审校仍需真实审核者与记录。

关系与来源可帮助定位遗漏条件，但未形成任意证明的形式推导系统。检索准确性需按独立题集评价，不能由图中节点数推断。

## Chat 与工作区的统一

前端通过共享对话控制器和工作区承载同一会话。领域数据继续由各自 API 保存，Chat 使用规范引用读取指定版本；仅凭前端文本或 URL 无法授权引用。

OpenUI 使用受限组件目录。模型生成的交互先经过解析、语义校验和降级处理，再触发服务端允许的动作。实验提案要求真实预测和获准参数，预览与保存分别校验。自检中的帮助锁和独立任务资格由服务端执行，组件显示状态不能放宽这些规则。

## 状态、成本与持久化

SQLite 保存会话、实验与学习记录，课程库可单独配置路径。普通掌握度和错因更新发生在上下文收集阶段，依据学生候选核验，不以 Teacher 最终交付为事务门槛；独立任务的帮助资格另由领域服务校验。历史摘要、近期过程、帮助状态和掌握度参与后续教学上下文，个性化是否更有效仍需验证。

主路径复用现有 Teacher 与固定计算，定向检索限制调用数、结果数和时间。失败路径记录 unknown、拒绝或超时；没有引入额外 Planner 或多 Agent 层。真实模型的请求数、token 与费用需要由获准采集配置约束，离线测试不会验证供应商计费。

## 私人数学探索

GS / Newton 探索复用学习记录、TeachingDecision、模型适配器和现有运行器。版本绑定的探索引用把主张、修订、受控计算与私人关系带回 Chat；私人关系参与后续条件追问，不写入课程图。双视角网络和上下文选择见 [R6.1 连续探索](r6.1-exploration.md)。正式课程写入与旧文件退役路径见 [R6 实现与兼容图](r6-exploration.md)，代码执行准入见 [隔离执行门禁](code-execution-gate.md)。
