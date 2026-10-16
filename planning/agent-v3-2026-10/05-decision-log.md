# Agent v3决策记录

> 2026-10-07 S5.2首版更新：[12交付回执](12-delivery-s5-2.md)。8道公开dev逐题解答/rubric已准备并绑定（agent_prepared_only），2条固定模型ASGI流程/3个run/18项阶段通过；真人审核、独立二审、真实模型内容与4道确认题仍pending。工程/API780/Web56与E0合同通过，不能转写成数学准确率或teacher gold。

> 2026-10-07 S5.1首版更新：offline/dry-run/replay、四类真实图固定fixture采集及解释报告已实现，见[10交付回执](10-delivery-s5-1.md)和[11验证目标](11-s5-1-evaluation-rationale.md)。8道development输入/rubric仍是待复核草案；S5.2内容质量与真人二审、S5.3 live/预算未完成。旧“CLI不存在”或“仅规划”描述以下方日期为历史快照，不代表当前入口。

> 当前交付更新（2026-10-07）：S5.0 已在工作区实现并完成离线工程验收，见[09交付回执](09-delivery-s5-0.md)：API700/Web56，E0 v2 38合同/92实例，S5.0增量10合同/45实例；前端typecheck/lint/build通过。S5.1–S5.2质量runner/gold及live、linear接入仍待实施。下方原审计/规划描述保留日期，不代表当前源码状态。

当前修订：2026-10-07。用户授权按[独立审阅](07-plan-review.md)修改方案；**仅文档，S5.0与新评测尚未实施**。原2026-10-04指令的十二个判断继续回答，但当前顺序由下表和04取代旧日程。

## 决策与重审条件

| 决策 | 依据与有效条件 |
|---|---|
| 两周只承诺S5.0核验与学习资格闭环 | 旧unsafe入口、代算/heuristic、双sink和deadline问题有源码/探针证据；正常矩阵和旧消息合同按08验收 |
| gold与offline准备可并行；全题库不阻塞协议probe | 运行结论用安全版本；协议准入需隔离预算/profile，数学质量需该题gold，消费另行授权 |
| 首版8 dev＋4独立确认候选＋2流程 | 是投入起点和覆盖矩阵，非统计样本量；缺第二复核者只交dev。原32/36/8降为backlog |
| 完成/正确/恰当弃权/coverage一起报 | 防止全unknown降低误确认却不完成学生任务；N/A、未答与not_run分开 |
| 同安全版本局部干预优先 | 各干预从相同初始库/图状态独立运行；历史adapter与整栈对照可选，不混归因 |
| 现有字段/一处投影优先，独立Evidence延期 | 原来也是条件候选；本次进一步明确没有必建模块。多结果误指复现且至少两处消费者确需绑定时再提取 |
| 默认下一产品切片linear只读引用 | owner/保存/轨迹已有，复制痛点明确；大小收益待观察。编辑运行保存复用原实验台，新参数卡另排 |
| 继续LangGraph/既有Runtime，不恢复Python | 修边路与资格，不重建框架/Registry；固定worker不意味着任意eval安全 |
| ProofState/图/Lean/A8保持条件延期 | 需要跨来源失败、便宜方案比较、新的独立确认净收益，或同state恢复/形式化需求；不用题数自动启动 |
| 预算按实际run/request和发送前预留 | 51只适用3 probe＋8单run×6；多轮另算。无可核实费用上界则硬费用预算live不运行 |
| 工期分项与首批校准 | S5.0建议4–7日；原完整形态10–17日含该片，非实测承诺；人工作者/二审/盲评/等待另计 |

## 十二个直接判断

1. **最大五缺口**：旧表达式执行边界；候选/scope/unknown/学习资格；开放推理质量缺证；聚焦任务gold与真实供应商证据；Newton以外可信Chat交接。G3是证据缺口，不是失败比例结论。
2. **Runtime还是Math Reasoning**：先封闭旧边路与学习语义，用聚焦评测指导数学反馈；不继续堆基础设施，也不先造Reasoner。
3. **S5怎样回答**：共用小case池、独立gold、完成/弃权/覆盖、同状态独立干预；新能力coverage与历史/调度对照分开，不估计总体瓶颈占比。
4. **已有与LLM边界**：有界数值诊断可复用；局部符号核验待修；开放证明/反例和定理适用仍需独立内容证据，LLM同意不等于证明。
5. **ProofState核心primitive**：现在不；先复用scope/origin/候选与资格字段，只有局部修复不足且确认净收益才做公开step实验。
6. **Course Graph**：结构检索与教学路由，条件候选not_checked；未核验本题前提/证明依赖，不能当形式推理图。
7. **反例与Lean ROI**：优先复用可验证教学模板，大小收益未测；通用反例引擎与Lean feasibility都非两周/六周必交。
8. **A8**：延期；短run/保存引用/中断回执保留，同state长任务恢复需求未证实，不自动replay。
9. **两周只做一件事**：S5.0诚实的本步检查闭环，正常能力保持、候选资格、两个sink及历史显示都算完成条件。
10. **四至六周**：S5.0→聚焦runner/gold，具备准入才smoke→按具体失败局部修复或linear只读引用→新的独立确认/页面演示。用过确认题调优后不能继续叫未见。
11. **不要重建**：LangGraph、LearningContext/Actions、固定worker生命周期、Guard/RunTrace与root probe；边界修复、版本字段和linear ref可增量改。
12. **Not Now**：完整IR/Reasoning Graph、广泛Lean、ProofState必建、通用反例/策略引擎、MCTS/多Agent、自动路由/新SaaS、任意Python/C0、无需求A8、全部工作区。

## 当前终端摘要

```text
AUDITED SHA
  52373b632013e0808f8939b1fd8876edbc5e2850
  Latest planning revision: 2026-10-07; production unchanged
CURRENT VERIFIED BASELINE
  Historical 2026-10-04 API655/Web51; E0 v2 38 contracts / 92 instances
  2026-10-07 review adds bounded probes; no live-model quality acceptance
WHAT CHANGED SINCE PREVIOUS PLAN
  Normal capability matrix / independent deadline / student claim eligibility
  Two learning sinks and legacy history; small decision-focused evaluation
TOP 5 REMAINING GAPS
  1. Legacy expression execution boundary
  2. Candidate/scope/unknown and learning eligibility
  3. Independent quality evidence for free-form reasoning
  4. Focused gold and real-provider acceptance
  5. Trusted Chat integration beyond Newton
NEXT MILESTONE
  S5.0 honest verification; gold/offline preparation may run in parallel
MATH REASONING DECISION
  Existing LLM plus bounded tools; measure concrete failures before new state
HIGH-LEVERAGE CHANGE
  Reuse scope/origin/claim binding; Evidence type only after measured need
NEXT PRODUCT SLICE
  Linear saved-run read-only context; retain existing edit/run/save
DO NOT DO YET
  Full dataset gate, required historical adapter/Evidence, new parameter cards
  ProofState/IR/Reasoning Graph/Lean/A8 without concrete evidence
DO NOT REBUILD
  LangGraph / LearningContext / LearningActions / fixed worker / Guard / RunTrace
FIRST IMPLEMENTATION SLICE AFTER THIS PLAN
  Implement and validate 08-s5-0-verifier-contract.md; not implemented this round
FILES UPDATED
  00-06 planning docs, roadmap/evaluation/current indexes and project handoff
FILES ADDED
  08-s5-0-verifier-contract.md
```
