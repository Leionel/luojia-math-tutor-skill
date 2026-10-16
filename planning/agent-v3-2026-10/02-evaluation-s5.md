# S5：聚焦核验与数值讨论的首版评测

> 2026-10-07 S5.2首版更新：[12交付回执](12-delivery-s5-2.md)。8道公开dev逐题解答/rubric已准备并绑定（agent_prepared_only），2条固定模型ASGI流程/3个run/18项阶段通过；真人审核、独立二审、真实模型内容与4道确认题仍pending。工程/API780/Web56与E0合同通过，不能转写成数学准确率或teacher gold。

> 2026-10-07 S5.1首版更新：offline/dry-run/replay、四类真实图固定fixture采集及解释报告已实现，见[10交付回执](10-delivery-s5-1.md)和[11验证目标](11-s5-1-evaluation-rationale.md)。8道development输入/rubric仍是待复核草案；S5.2内容质量与真人二审、S5.3 live/预算未完成。旧“CLI不存在”或“仅规划”描述以下方日期为历史快照，不代表当前入口。

> 当前交付更新（2026-10-07）：S5.0 已在工作区实现并完成离线工程验收，见[09交付回执](09-delivery-s5-0.md)：API700/Web56，E0 v2 38合同/92实例，S5.0增量10合同/45实例；前端typecheck/lint/build通过。S5.1–S5.2质量runner/gold及live、linear接入仍待实施。下方原审计/规划描述保留日期，不代表当前源码状态。

修订：2026-10-07；依据[独立审阅](07-plan-review.md)。**待实施，没有冻结题库或真实模型成绩。** 本轮只修改规划。S5.0合同见[08](08-s5-0-verifier-contract.md)，排程见[04](04-roadmap.md)。

## 首版要裁决什么

只回答两件事：修复后的单步检查是否安全、诚实且保留正常能力；数值讨论中具体失败更像输入/引用、工具结果还是模型解释问题。首版不能估计全本科数学准确率、主要瓶颈占比或学生学习收益。

S5.0、离线题目准备和runner开发可以并行；使用学生表达式的执行验证和质量结论须以安全修复后的明确版本为准。固定HTTP协议probe只依赖安全隔离harness、预算与profile，不等S5.0或全部数学题双审；通过应用图的smoke等S5.0，数学质量运行还需该次题目的复核。未来实施授权与live消费授权分别确认，本次“修改规划”不启动它们。

## 数据规模与层次

| 层 | 首版范围 | 判据 / 限制 |
|---|---|---|
| E0 Runtime | 既有v2 38合同/92实例；S5.0增量回归另列版本 | 离线协议/边界断言；不当作数学题成绩 |
| E1 Behavior / E2 Math | 共用8个development case，两个评分视图；4个独立封存确认候选 | 同case_id不能相加成两个样本；缺第二复核者则只交dev，确认集pending |
| E3 End-to-end | 2条development流程 | Newton引用→预览→显式保存→新引用；普通数值Chat→范围解释→用户修订/追问。真实状态与人工内容判据同时成立 |

8+4与2流程是投入起点，不是统计最佳样本量或强制凑数线。首批覆盖矩阵：2个正常/等价表示、2个scope/unknown/误区、2个linear残差/工具决策、2个Newton条件/上下文；重复数学结构不证明独立泛化。

原E1 32、E2 36、E3 8保留为**后续覆盖目录**，取消完整冻结作为smoke或linear接入的前置门槛。A–L数学家族的原种子详见07 §6，已公开反例只可用作dev。Newton命题明确为“迭代点导数非零足以保证任意初值收敛”；x³−2x+2的0↔1只反驳这一版本，不能替代全域导数非零命题。

## Gold与封存

作者先给出输入、域/量词、候选来源、允许帮助、必要/禁止结论、工具支持、独立解答与评分资格；第二位真实复核者检查数学与状态rubric。模型重复生成不算第二人。没有独立复核时标author_reviewed_only；不得宣称教师gold已验收。

拟建evaluation/s5/manifest.json与dev JSONL；封存输入/gold在独立目录，公开manifest仅存ID、结构标签、hash、审核状态。按来源/数学结构分组，不能只换常数；开发prompt、工具和生成器不能读取封存解答。已公开的互斥误判、Newton循环、积分混叠和08矩阵不变成unseen。

固定模型响应验证runner/Guard/SQLite报告合同，不是模型质量。gold不由被测checker、root_runner或生成模型单独产出；小矩阵独立代回、积分用已知解析值、反例逐项核对假设。课程检索允许正常定理，但记录是否含同题完整答案。只用合成或可公开授权材料，不读正式学生会话。

确认集只用于冻结后的独立确认；一旦用于选模块、改prompt、选模型或调rubric，该部分转为dev并记录，不再用于后续“未见改善”证明。再次确认需要新封存题，不能反复刷同题保留旧标签。

## 指标：同时看完成、正确、弃权与覆盖

每case先固定applicable，不能按模型是否输出claim改变任务分母。未运行明确not_run并保留在manifest；缺case、重复ID或意外case令报告完整性失败。

| 指标 | 分母 / 判据 |
|---|---|
| 执行覆盖 | 实际运行case / 计划case；预算中止不能悄悄删题 |
| task completion | 适用且已运行case；满足gold要求的必要输出/动作。应给反例却未给，是未完成，不是N/A |
| mathematical correctness | 适用且已运行数学case；按独立gold判定。应回答却沉默或不当弃权记不正确；不适用与未运行另列null |
| appropriate / inappropriate abstention | 每个适用case分别记录；缺域/不可判定且gold允许澄清或未知为恰当。所有题unknown不得通过正常能力保持 |
| checker coverage | gold规定该operation支持且可判定的case；实际给出匹配input/domain/scope的确定判定 / 该类case。支持矩阵版本冻结 |
| verification overclaim | 实际核验主张中与输入/域/scope不匹配的数量；同时报告发生主张的任务数，作为诊断，不能替代固定任务分母 |
| first-error localization | gold确有错误且可定位的case；找对首错。无错题误报单列；未定位不能因无错误主张而得高分 |
| counterexample validity | gold要求反例的case；满足全部前提且否定结论。未给witness为未完成；数值猜测未被核验不能算有效 |
| routing / clarification | gold有明确允许route/需澄清的case；保存初始与resolved intent、verification_mode及实际分支；允许多条合法轨迹 |
| tool decision | 支持profile已知的case；工具需要/不需要/遗漏按gold；实际call的名称、schema合法、参数数学对应性分别记录，不合成单一“选对工具” |
| action validity | 可见卡片、preview和save分别核对授权/hash/最新preview/确认；server_mapping不当作model_action_choice |
| help / false success | 锁定及故障case中泄露帮助、不合法学习写入或无证据成功；任何一例不通过，不能被均分稀释 |

零分母null/N/A，不显示100%。主表至少包含case_id、applicable、run_status、task_completed、mathematically_correct、appropriate_abstention、inappropriate_abstention、checker_coverage、verification_overclaim、help_violation、not_run_reason及review状态。

内容盲评用匿名arm/随机顺序，优先逐题count/n、差异及wins/ties/losses。样本小且异质，不作总体准确率排名；如给区间必须写明抽样假设和局限。LLM judge只能提示分歧，不能覆盖确定oracle或取代人工。真实页面成功也不等于学习迁移。

## 对照与归因

优先同一安全SHA、相同模型/教学配置、固定检索结果的development单因素干预。每个失败从同一初始临时库/图状态分别干预route、必要context或局部tool结果；不得累计写入history/mastery后把最后成功归因给最后一个因素。记录干预是否泄露答案和增加的calls/tokens，只做针对性复跑。

人工确认的失败码：INPUT_AMBIGUOUS、ROUTE_WRONG、CONTEXT_MISSING/STALE/TRUNCATED、TOOL_MISSED/UNNECESSARY/ARGS/FAILED、MATH_CALCULATION、ASSUMPTION_MISSING、THEOREM_MISAPPLIED、LOGIC_GAP、COUNTEREXAMPLE_INVALID、VERIFICATION_OVERCLAIM、ANSWER_LEAKAGE、EVIDENCE_CONFLICT、ACTION_INVALID/OUTCOME_UNLINKED、PROTOCOL/DELIVERY、ORACLE_UNKNOWN、BUDGET_STOP、PROVIDER_UNSUPPORTED。可多标签，但primary cause只计一个case。

新增native能力、引用或preview-save单列capability coverage；baseline缺能力不能记0分造提升。tool on/off改变能力，是消融，不是假装同能力历史准确率比较。工具未调用不必然错，简单计算可合法直接解释。

历史整栈对照移为可选附录。历史SHA612e3a4e9175edf95041f4cada09b8e73850671a还含旧生成Python路线，不能启动危险旧系统。将来若做，记录安全adapter及prompt/Guard/verifier/evidence hash：两侧相同安全核验与教学规则才能研究调度；否则只叫historical_stack_comparison。首版不建旧版本adapter。

新状态抽象的触发证据是跨来源/题型的同机制失败、正确必要context/tool后仍失败、便宜局部修复已比较、公开step干预在独立确认中仍有收益且无新增泄漏/过度验证。题数只为探索投入，不能“达到3题”自动启动ProofState。

## 协议probe与预算：独立准入，尚未授权live

先做offline/dry-run，再另行明确具体model/endpoint、允许case/run和预算。未知native能力时用隔离的固定HTTP协议probe，不能为了通过生产client门控先写operator_verified/offline_fixture。真实结果绑定实际model/endpoint与时间，供确认；不按品牌推测支持，不执行模型脚本。

probe最多3请求；建议smoke最多8个**单run**纯文本case，无图片、联网、外部embedding、后台enrichment和自动重试。最坏每run routing1 + review1 + generation/tool continuation最多3 + Guard repair1 = 6；总上限3+8×6=51。多轮episode按实际run数另算，重试/修复/取消后新run都占额度；51不是任意8流程的上限。

| 口径 | 合同 |
|---|---|
| 请求上限 | transport在实际HTTP发送前并发安全预留；只准批准host/path/model，拒绝重定向、embedding及旁路。失败/取消不退请求数，恢复不重置消费 |
| 费用上界 | 每请求发送前预留最大可计费input/output/额外项的费用，所有上界须由具体供应商计费合同支持；本地JSON字节上限不能直接当计费token上界 |
| 未知费用 | 价格/币种、reasoning/cache/按次收费或上界未知，则费用硬上限模式不运行。usage缺失不补零、不释放无法核对的已预留额；已知部分不当作总余额 |
| 建议金额 | CNY10仅为smoke配置提案；币种不同重新设原币预算，不用未核实汇率。确认集需另行opt-in，按manifest重算请求/费用；原CNY50也不构成消费授权 |

可复用OpenAICompatibleClient.get_http_client注入harness transport；不新建生产model router或计费服务。若必须改client，最小可选注入并保留默认行为。默认测试仍离线；harness独立进程、临时SQLite、固定retrieval、关后台任务。

preflight打印允许run数、最坏请求数、工具预算、model/endpoint hash、路径、币种/价格版本、计费上界来源与pending原因。第52请求不发送、并发超预算不发送、失败/unknown usage/取消/恢复不免单都必须测试。预算停止后保留已花及not_run，不自动换模型、扩大题库或续跑。

## 拟实施入口与报告

S5.1已实现offline/dry-run/replay与固定图fixture采集，精确接口见evaluation/s5/README.md；下方live profile为原规划，当前只接受脱敏规划字段且不能执行live。

```powershell
python scripts/eval_tutor_quality.py --manifest evaluation/s5/manifest.json --offline --output results/s5-offline.json
python scripts/eval_tutor_quality.py --manifest evaluation/s5/manifest.json --profile results/s5-approved-live-profile.json --dry-run
```

live必须显式profile/run manifest、请求和币种费用预算；不能因完成offline自动启动。公开日志只含合成case/输入hash、版本、span/ref、评分和脱敏错误，不放key、原始endpoint、学生库或隐藏推理；参数断言用局部synthetic sidecar，不扩生产RunTrace原始payload。

```json
{
  "report_version": "s5-quality-v1",
  "scope": "focused_verifier_and_numerical_discussion",
  "candidate_sha": "...",
  "source_dirty": true,
  "source_sha256": {},
  "manifest_sha256": "...",
  "split": "development",
  "gold_status": "pending_second_review",
  "comparison_class": "single_arm",
  "profile": {"model": null, "endpoint_sha256": null, "prompt_version": "...", "guard_version": "...", "checker_version": "..."},
  "planned_cases": 8,
  "executed_cases": 0,
  "e0_report_ref": "...",
  "e1": {}, "e2": {}, "e3": {},
  "cases": [], "not_run_cases": [], "failure_clusters": [],
  "usage": {"requests": 0, "coverage": "not_run", "tokens": null, "cost": null},
  "budget": {"max_requests": null, "currency": null, "max_cost": null, "stopped_reason": "live_not_authorized"},
  "confirmation_status": "pending",
  "limitations": []
}
```

每case带expected/observed、所有适用性与分母、oracle/reviewer、run/span/动作引用、unknown/not_run原因；gold和配置缺失必须能报告pending。fixed fixture不得出现在real_model结果分母。首次验收是可复跑的诊断报告和已知正确/失败例，不要求新增一个总分。

实施后运行npm.cmd test及E0 CLI、新runner offline/dry-run、预算边界和独立状态干预测试；UI改变才做类型/lint/停止dev后的构建与浏览器验证。当前未实施这些评测。原方法参考：[LangSmith output与trajectory评价](https://docs.langchain.com/langsmith/evaluate-llm-application)；本地数学gold与可解释case才决定优先级。
