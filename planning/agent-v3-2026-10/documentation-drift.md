# 当前状态与历史规划的差异

> 2026-10-07 S5.2首版更新：[12交付回执](12-delivery-s5-2.md)。8道公开dev逐题解答/rubric已准备并绑定（agent_prepared_only），2条固定模型ASGI流程/3个run/18项阶段通过；真人审核、独立二审、真实模型内容与4道确认题仍pending。工程/API780/Web56与E0合同通过，不能转写成数学准确率或teacher gold。

> 2026-10-07 S5.1首版更新：offline/dry-run/replay、四类真实图固定fixture采集及解释报告已实现，见[10交付回执](10-delivery-s5-1.md)和[11验证目标](11-s5-1-evaluation-rationale.md)。8道development输入/rubric仍是待复核草案；S5.2内容质量与真人二审、S5.3 live/预算未完成。旧“CLI不存在”或“仅规划”描述以下方日期为历史快照，不代表当前入口。

> 当前交付更新（2026-10-07）：S5.0 已在工作区实现并完成离线工程验收，见[09交付回执](09-delivery-s5-0.md)：API700/Web56，E0 v2 38合同/92实例，S5.0增量10合同/45实例；前端typecheck/lint/build通过。S5.1–S5.2质量runner/gold及live、linear接入仍待实施。下方原审计/规划描述保留日期，不代表当前源码状态。

原审计：2026-10-04，SHA `52373b6`。当前规划修订：2026-10-07；旧回执与07独立审阅保留，不把历史验证数字改成今天结果。

| 位置 | 漂移/风险 | 本轮处置 |
|---|---|---|
| `agent-engineering-2026-10/plan.md` 顶部 | 仍称A6.2/A7待做、下一批计算工具；尾部§12已经记录S3/S4完成 | 顶部加current status与v3索引；下方旧日期段落明确历史，保留当时决策 |
| `runtime-review-schedule.md` | 早期A6/A7设计和当前用户未提交修改共存 | **不编辑**该用户dirty文件；current优先由v3和S3/S4回执给出，旧“未实现”不再作为新缺口 |
| `chat-workspace-review.md` | 开头基线0340c49，讲未有LearningContext/native tools等当时问题 | 加历史设计标记与current索引，保留原审阅与计算修正，不抹掉历史 |
| `delivery-s1-s2.md` | 当时说A6.2/A7尚待、下一步S3/S4 | 原样保留；它是交付当时状态，后续状态看S3/S4和v3 |
| `delivery-a0-a2.md` / `delivery-a3-numerical.md` | 旧测试总数/19合同40实例 | 原样保留，与默认v2 38/92清楚区分 |
| README Agent段/验证段 | 仍用默认19/40和API600/Web48 | 当前段更新为v2和本轮655/51，保留历史交付链接；明确本轮只复跑离线，不冒称新build/live |
| `root_diagnostic_manifest.json` | frozen工程候选含旧prompt版本/hash，仍teacher pending | 不改成当前评测manifest、不覆盖历史hash；S5新建自己的冻结记录 |
| 三份项目交接/记忆 | 最近S3/S4后尚未记录本轮新审计与S5.0前置缺口 | 写入本轮审计事实、规划路径和未实施状态，不把计划描述成完成 |

## 权威顺序

当前source/HEAD/dirty状态 → 本轮00基线与原始结果 → 当前交付回执 → 标注日期的历史设计。新规划不是运行证据；历史文本不是当前缺口的唯一依据。Agent onboarding先读最新`CODEX_HANDOFF.md`段，再读00/02/04；实现时重新核对SHA差异。

本轮只修改current索引/文档，不改变业务源码、测试、冻结知识/评测数据、私人env或数据库。没有为了让文档“整齐”改掉未完成的gold/真实供应商状态。

## 2026-10-07 修订后的入口

当前执行顺序以02/04/08为准；00明确区分旧审计工作区快照与当前修订，03/05不再将Evidence视作必须下一模块，06收紧普通核验/真实供应商简历口径。README与两份旧索引、三份项目记忆同步新顺序；runtime-review-schedule.md用户修改不碰，07报告原样保留。

取消全32/36/8冻结和历史adapter作为首版硬门槛；两周只承诺核验闭环，gold/runner可并行，协议smoke独立准入。旧“6–9日完整S5”和“linear须带新参数卡”的排期不再适用。07中的原方案行号指改前版本，修订前快照在ignored results/agent-v3-plan-revision-20261007-before；不能用新行号冒充原引用。

权威顺序：当前源码/工作区→带日期的验证与07证据→当前02/04/08规划→历史设计。规划字段、矩阵、预算和估算都不是已交付能力。
