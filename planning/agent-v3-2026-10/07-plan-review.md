# Agent v3 规划独立审阅

审阅日期：2026-10-07（Asia/Hong_Kong）。性质：质疑、源码核对与有界离线验证；不是实施回执。仅新增本报告，不修改原规划、生产代码、配置或已有用户文件。

## 1. 总体判断

**需要重排，保留底座和安全修复方向，不照原日程串行执行完整 S5。**

原方案最有价值的判断成立：旧核验边路必须处理；E0 不等于数学质量；不应凭缺少某个类就重建 Reasoner；Newton 引用、固定工具、Guard、AgentRun 应复用。原文已经明确未知 usage、人工 gold 未完成、真实模型未运行等限制，不能把这些诚实披露反过来算作方案错误。

最大问题是：**把一个尚未闭合的核验修复，与跨度过大的评测包绑成前置主线，却没有先规定修复后哪些正常题仍可检查、什么结果有资格影响学生记录，以及一个小评测究竟要裁决哪项产品决策。** 这会导致实现者以大量 unknown 换取安全回归通过，或者完成漂亮的报告而仍无法决定学生最需要的改进。

建议主线：

1. 一个可交付的 S5.0：安全执行、明确核验范围、不会把模型代算或 heuristic 当学生作答、历史状态可识别；带小型正常能力与错误语义回归。
2. 并行准备少量人工 gold；S5.0 后做聚焦诊断，供应商协议 smoke 不等待全题库双审。live 仍须另行授权和预算准入。
3. 核验边界达标后，默认产品候选是 **linear 已保存实验的只读可信聊天引用**；先复用独立实验台的编辑/运行/保存，不强制同时复制 Newton 参数卡体系。
4. 只有局部字段不能承载已观测问题时，才抽取 VerificationEvidence；完整 IR、Reasoning Graph、Lean、A8 继续延期。

本报告中的 P0 表示发布前必须封闭的安全边界，P1 表示影响正确性或评测结论，P2 表示范围、成本或产品顺序问题。置信度针对证据充分程度，不是发生概率；未测用户收益均标为待验证。

## 2. 审阅身份、状态和证据边界

### 2.1 当前工作区

- 仓库：`D:\Projects\na-tutor\luojia-math-tutor-skill`。
- HEAD：`52373b632013e0808f8939b1fd8876edbc5e2850`。
- 分支：`feature/course-graph-2.0`。
- 起始 tracked 修改：`CODEX_HANDOFF.md`、`README.md`、`luojia_tutor2_branch_log.md`、`luojia_tutor2_course_graph_research_refined.md`、`planning/agent-engineering-2026-10/chat-workspace-review.md`、`plan.md`、`runtime-review-schedule.md`。
- 起始 untracked：`apps/api/luojia_math_tutor_api.egg-info/`、`apps/web/public/demo-jiuzhang-hybrid.html`、`style-explorer.html`、`ui-proposals/`、整个 `planning/agent-v3-2026-10/`。
- 已读取根目录 AGENTS.md、指定九份规划全文、CODEX_HANDOFF 当前段及相关历史段、S1/S2 和 S3/S4 回执；结合源码、测试、旧评测报告核对。

原审计与现在 HEAD 相同，没有发现 tracked 生产源码变动。旧 `results/agent-v3-audit-reliability.json` 所列 **175 个文件 SHA-256 全部匹配当前文件**，报告为 38/38 合同、92/92 实例。旧完整测试日志记录 API 655 passed / 5 warnings、Web 51 passed，作为历史证据复用，没有冒称本轮重跑全套。

收尾对起始 30 个已有修改/未跟踪文件逐一比对 SHA-256，全部保持不变；新增项仅本报告。项目交接和原规划未回写，遵循本轮“仅新增审阅报告”的具体边界。

**失效的是起始工作区描述，不是这些源码事实**：00 第 27 行“起始仅 runtime-review-schedule.md 修改”属于上次审计；本轮已有上述七份 tracked 修改和未跟踪规划。00 的文档检查与旧构建、浏览器回执仍只是当时证据，不构成本报告或当前真实模型的验收。

### 2.2 本轮新增验证

| 验证 | 结果 | 能证明的范围 |
|---|---|---|
| 五个现有测试文件定向复跑 | **34 passed，1 warning，pytest 3.66s** | 旧核验、降级和 LearningContext 现有合同仍通过；并不覆盖下面所有反例 |
| 真实编译图 + 固定模型响应 + mock Repository | 正确概念句触发 mistake/mastery 写入调用；无学生答案的求导也可触发 mastery 写入调用 | 已到写入接口，非正式库污染规模证明；没有真实模型参与 |
| 正常数学函数探针 | x/x 排除点丢失、实数假设未传入、洛必达过度结论重现 | 指定输入的实现行为，不是失败率 |
| 固定 worker 对 x**2 求导，两次独立进程 | succeeded，1324.70ms / 1299.91ms | 本机两次观测已超过 collector 的 350ms；不是延迟分布或性能承诺 |
| 受控解析兼容性探针 | 接受 2*x、x^2、exp(x)；拒绝 2x、x²、e^x、Abs(x)、x+y、x**(1/2) | 直接复用现有 typed grammar 的限制，不代表未来安全规范化也做不到 |

pytest 从 `apps/api` 执行；保留 conftest 离线门控，额外清除进程内相关供应商 key，将数据库指向新临时目录，禁止 HTTPX 外发。图探针使用 mock Repository，固定 worker 只计算普通多项式。没有运行危险 payload，没有读取正式学生库，没有 paid model call、next build、安装、提交、推送或部署。

探针准备曾因 Windows asyncio 的内部 socketpair 被过宽的网络禁用拦截、以及终端 GBK 无法打印上标字符而失败；调整为事件循环创建后禁止连接、JSON ASCII 输出后成功。失败发生在验证设施，不作为产品失败证据。旧安全探针脚本只读取，未重新执行。

下文路径均相对上述仓库；`A/` 表示 `apps/api/app/`，`T/` 表示 `apps/api/tests/`，`W/` 表示 `apps/web/`。规划文件名均位于本报告同目录。行号指本轮读取的原文件。

## 3. 最重要的五个问题

### R1 — S5.0 的迁移合同没有覆盖真实时间预算与正常输入兼容性

**P1，置信度高；所修复的 G1 本身仍是 P0 安全缺口。**

- **原主张**：04 第 29–37 行要求复用 typed AST/固定 worker、先保留安全等价/求导子集、其余 unknown，估计 2–3 日；02 第 9 行要求受支持正常任务继续运行。
- **源码/复现**：`A/tutor/fast_context.py:115,138–164,381–403` 只有 0.35 秒共享上下文窗口；超时取消 symbolic task。`A/agents/typed_tools.py:120–183` 每次启动新固定进程，默认最多 10 秒；本轮普通 x**2 的两次执行约 1.3 秒。`typed_tools.py:57–89` 只接受 x/pi/e、有限函数及整数幂；`A/math_tools/verifier.py:13,26–60` 旧路径原来支持隐式乘法、部分 LaTeX/Unicode 和更多符号。`A/agents/math_worker.py:16–41,44–58` 目前只有求导和 numerical operation，没有旧等价、积分候选、未定式操作。
- **影响**：直接把 worker await 塞回现有 collector，会在本机普通题上被外层先取消；不是把 worker 的 10 秒参数设好就解决。原文允许降级，但没有“必须保留”的输入矩阵，可能让常用 2x、平方根恒等式和积分候选全部失去检查而仍通过安全验收。尤其 E2-K 要求 Abs(x)，现有 grammar 正好不支持。
- **最小修改**：在 S5.0 验收中列出运算×输入表示×域×预期状态的白名单。复用进程拥有/回收代码，但将本步检查与可选检索的 350ms deadline 分开，保留总请求超时和取消传播；不预设进程池。为正常一元表达式做有限、可审查的表示规范化；等价/候选检查需要明确固定 operation，不能以“能求导”冒充“已核对学生答案”。暂时关闭的操作在新旧消息和评测中均标 coverage regression。
- **代价/取舍**：增加一小块调度集成和正常题回归，可能增加等待时间；减少首批 operation 可以控范围，但需明确丢失能力。2–3 日只适合作为安全止血假设，不能同时保证所有旧能力兼容。建议完整切片预留 4–7 个集中开发日，见第 10 节的估算条件。

G1 不需要重复危险测试来证明：`A/api/routes_tutor.py:43–92 → orchestrator.stream_reply → graph.fast_context_node → _collect_symbolic_result → check_step → parse_math` 可达。`parse_math` 第 60 行直接默认 parse_expr；无 expected 的求导还有 `step_checker.py:101` 字符串 sp.diff。认证限制调用者，不能净化其数学文本；typed 开关关闭也不关闭该边路。官方文档明确说明 parse_expr 使用 eval，不应接收未清理输入：[SymPy Parsing](https://docs.sympy.org/latest/modules/parsing.html)。固定进程也不能使任意 eval 安全，必须先限制语法。

### R2 — “非 heuristic 且非 unknown”仍不足以成为学生学习证据，历史链也没有闭合

**P1，置信度高。**

- **原主张**：01 第 10、19–22 行诊断 G2；03 第 24 行提出 `eligible_learning_evidence`；04 第 31、34 行规定旧消息 legacy、heuristic/unknown/reference-help 不计分，不批量重算历史。
- **源码/复现**：`A/math_tools/step_checker.py:98–108` 在没有学生候选答案时，自行求导并返回 `verified=True,is_correct=True`。本轮在合成的上一轮“导数”概念背景下输入“帮我检查求导 x**2”，编译图得到 `expected=null,actual=2*x`，却调用 `upsert_mastery` 一次，默认参数下 delta=+0.415。正确“互斥和独立不是一回事，对吗”则触发 mistake、mastery 各一次，delta=-0.265。`A/tutor/fast_context.py:605–615` 的 mistake 写入独立于 verified；把返回值改 unknown 但保留 mistake，本轮仍观察到一次 mistake 写入。
- **历史证据**：`fast_context.py:269–273` 把历史消息裁成 role/content；原 `verification_kind`/scope 不进入历史上下文。`W/lib/message-status.ts:7–10` 对旧 verified 仍显示“已完成本步检查”。`A/memory/repository.py:596–660` 的 mistake 只有 session/concept/code/time，mastery 是聚合 score/attempts/correct_count，没有每次 checker 版本、证据引用及可逆 delta。
- **影响**：若只给 heuristic 降级，系统代算仍会被当作学生答对；若只修改新消息 UI，历史正文中的旧“通过”仍可在新轮次被当背景引用。仅靠这些历史表无法精确列出每条受影响更新并重算。这里确认的是通用 mastery/BKT 估计污染路径，**没有证据表明已污染独立 probe 成绩或具体真实学生数据**。
- **最小修改**：资格判据至少需要“确有学生提交的候选命题/步骤、输入绑定、checker 对该候选给出可判定结论、范围明确、非参考帮助”。确定性地算出答案不满足第一项。对 mistake 和 mastery 两个 sink 分别加资格门，非确定误区只保留待核对教学线索。未知结果保持 `is_correct=null`。旧消息读取时显示 legacy，并在送入新 prompt 时添加有限的来源/未核验提示；不改历史正文、不自动重放检查。对聚合旧掌握度只能做来源不明标记/候选影响范围，无法归因时不得声称精确修复；不要扩成全库迁移项目。
- **代价/取舍**：需要后端 eligibility、SSE/metadata、历史读取和状态展示联动；会减少自动可计分样本，但防止虚假学习判断。历史精确纠错仍延期，需独立授权和数据证据。优先使用现有字段加版本，不必先创建新证据服务。

保留已有保护：`fast_context.py:386,601–603` 跳过 LearningContext 的单步检查和学习写入；`orchestrator.py:558–565` 明确 reference_help；LLM review 发生在 collector 学习写入之后，不能由其 `verified` 字段推断它已经写入 BKT。根诊断及独立 probe 是另外的受控路径。

### R3 — S5 的指标还不能可靠区分“更正确”与“少回答/少核验”，部分 gold 需先消歧

**P1，置信度高（指标/数学定义）；实际模型影响待验证。**

- **原主张**：02 第 7、16–20、56–71、97–110、198–204 行要用 32/36/8 定位五类瓶颈，报告数学正确性、核验主张和失败干预；01 第 10 行建议扩大 unknown。
- **证据**：02 对 E1 已定义分母及零分母，但 E2 未明确“该指标适用却未回答”和“本来不适用”的区别。例如没给反例、没定位首错、所有题都答“无法核验”，可以降低 unsupported claim/verification overclaim，却未改善任务完成。`graph.py:809–822` 已有工具失败降级；S5.0 还会扩大不支持输入，因此这一混淆会直接影响比较。A–L 每家族仅 1 道 held-out，无法估计家族表现；同模板变式不是独立的错误家族证据。
- **数学消歧**：02 第 63 行的“Newton 导数非零便任意初值收敛”没有说明非零在迭代点还是全定义域。03 第 90 行的 x³−2x+2 只保证循环点 0、1 的导数非零；导数在 ±sqrt(2/3) 为零，不能反驳“全域 f′ 非零”版本。种子不是计算错，但必须锁定命题量词。其他种子复核见第 6 节。
- **对照证据**：历史 SHA 已解析为 `612e3a4e9175edf95041f4cada09b8e73850671a`。与当前相比 graph、prompt、Guard 都变化；旧 graph 还要求生成 Python 验算。旧新两侧关闭该功能是必要安全适配，但已不是未经修改的历史系统。S5.0 又只修 candidate 的 verifier，则差异同时含核验修复与 Runtime，不能归因到单一模块。原文第 133、139–142 行已经承认部分不可比较，这一点应保留。
- **最小修改**：每题同时报 task completion、正确性、恰当弃权、不恰当弃权、checker coverage；分母先固定适用任务，不能按模型实际产生的 claim 缩小主任务分母。claim-level 指标只作诊断；E1 的 tool 名称、参数合法性和参数数学正确性分开记录。对每个 dev 失败从同一初始快照分别干预 route/context/tool，记录干预是否泄露答案；不要把累计补料的成功归因给最后一项。先做同一安全 SHA 的单因素比较，历史整栈对照移为可选附录。
- **代价/取舍**：少量 manifest/评分表字段和更多人工判断；首版降低覆盖广度，换取结论可解释。逐题差异可以支持修哪类错误，不能支持“主瓶颈占比”或泛化准确率。held-out 若用于挑模块、调 prompt 或再次选模型，即转为 development；后续改善验证需要新的封存题，不能继续沿用原“未见”称号。

“至少 3 个失败”不是可靠阈值。02 第 204 行实际上还要求独立复核、正确 context/tool 后仍失败、清单干预改善和 held-out 趋势，不能只摘数字批评；但三道同模板题仍可能误触发。建议改成：至少两个不同来源/题型的同机制失败、便宜局部修复已比较、按额外调用与泄漏风险计算净收益；具体数量是试验起点，不是统计验收线。

### R4 — 完整评测冻结被设为过强的串行依赖，Evidence 优先也没有胜过局部修复/产品接入的证据

**P2，置信度高（依赖事实），中（产品排序建议）。**

- **原主张**：04 第 11–19、58–67、88、130–132 行将 gold 全冻结放在 smoke 之前，把 S5 报告作为 Evidence/linear 的共同前置；03 第 3 行称 VerificationEvidence 最值得优先验证；01 第 59–61 行给 linear/integration/reading 定性高收益。
- **源码/现状**：`evaluation/s5/` 和 `scripts/eval_tutor_quality.py` 尚不存在，root manifest 第 6–8 行仍为 developer fixtures/teacher pending/unseen not_run；没有已落实第二复核者。`A/agents/typed_tools.py:112–117`、`math_worker.py:38–41` 已有执行状态、scope、assumptions；`orchestrator.py:211–232` 已有消息 metadata。反之 `W/app/numerical-lab/page.tsx:111` 确实要求复制后跳聊天；`A/api/routes_numerical_lab.py:41–95` 已有 owner/hash/保存/核对可复用。
- **影响**：没有技术理由等全部 76 个任务/流程槽位双审后才验证供应商能否完成一个工具续轮；也没有理由让 linear 的可信只读引用等待开放证明 gold。题库、预算、历史适配可能消耗完两周，学生仍面对原有误计分和复制流程。原计划虽说 32/36/8 是上限，S5.2 和完整验收措辞又使其容易成为实际完成门槛。
- **最小修改**：把全题库数字改为后续覆盖目录；先冻结与当下决策有关的小包。供应商协议先验验证只依赖安全 harness/预算/profile，不依赖全课程 gold；数学质量运行仍要对应题的复核。S5.0 修复通过后，linear 只读引用可用现有 Newton 合同和两条新流程单独验收。先在现有 VerifyResult/metadata 中统一 scope/origin/eligibility；只有两个以上消费者确需绑定同一 claim 且现有字段无法消除误指，才提取 Evidence 模块。
- **代价/取舍**：短期没有完整 benchmark 和新抽象展示，但更早得到有效产品与供应商证据。linear 是否比教材选段更常用仍待用户观察；本报告不把定性选择包装为已测 ROI。

### R5 — 工期缺少跨层工作量拆解，51 次与费用上限还需要可执行的准入定义

**P2，置信度高；若跳过预算准入直接 live，则升级为 P1 运行控制问题。**

- **原主张**：04 第 37、52、67、130 行估计完整 S5 6–9 个开发日、人工 gold 10–14 小时；02 第 151–156 行给 51 次请求及 CNY 10 建议上限，并明确实际 HTTP 前 reservation、未知计费时停止。
- **源码/证据**：`A/llm/openai_compatible.py:48–51,187–191,262–264,306–308,440–442` 共享 HTTPX client，确实可由独立 harness 包装；`call_observation.py:76–82` 记录 dispatch，不是限额器。`graph.py:642–679,755–783,865–898` 分别可能发生 review、最多 3 次生成请求和 1 次 Guard 修复；routing 另算。embedding 第 420–442 行还可从进程环境获得其他 provider key；`graph.py:511` 起有后台 enrichment。`pricing.py:8–33` 是声明价格及已报告 token 的事后估算。现有代码没有 S5 HTTP 预算实现，这是计划工作，不能误写为已验收能力。
- **影响**：3+8×6=51 在“8 个单 run、无图片、无额外检索/后台调用、无自动重试”的限定下是合理保守请求上限，**不是任意 8 个多轮 episode 的上限**。先成功返回 usage 再扣钱不能保证首个或并发请求不超支；仅限输出 2048 也不能约束未知 reasoning/缓存/按次计费。价格和供应商未指定，当前不能验证 CNY 10 能覆盖 smoke。
- **最小修改**：把 51 写成 manifest 的 run/request 算式；每次重试、新 run、repair、routing 均先占额度，失败/取消不默认退款。transport 只准批准的 host/path/model，拒绝 embeddings、重定向和旁路；在独立进程禁后台任务、固定 retrieval。发送前按供应商确认的最大可计费输入/输出/额外费用预留，缺少任何计费上界就不运行“硬费用上限”模式。usage 缺失不释放已预留额度；单独列请求上限、估算费用、账单上限三种口径。未知能力的协议 probe 要有独立受限发送路径，不能为了调用 `tool_turn` 冒填 operator_verified/offline_fixture。
- **代价/取舍**：预算 transport、并发/取消/持久停止测试和真实 provider 适配需单列工作量；不必增加生产计费服务。10–14 小时若仅指第二人复核简单 gold，并非必然不可信；若还包含出题、盲评模型输出、分歧裁决和多轮流程，则明显遗漏工作，必须按复核数量重估。

## 4. G1–G5 逐项裁决与 S5.0 边界

| 原缺口 | 裁决、分类与置信度 | 限定影响和已有缓解 | 最小动作及取舍 |
|---|---|---|---|
| G1（01:9） | 保留；安全缺陷；高 | 普通 symbolic Chat 可达；不是所有 root/numerical 工具失效，也不是发生攻击的证据。线程取消不回收计算 | 立即封闭所有学生字符串解析入口；复用受控构造与 worker 所有权。多变量/复杂 CAS 延后；见 R1 |
| G2（01:10） | 保留并补全；数学 scope、错误诊断和学习记录缺陷；高 | 正确概念句已到写入接口。x/x 在共同定义域上确实等价，不能把返回 true 本身一概叫数学错误；错误在没有说明比较域。sqrt 未声明实数时也不能把泛域不成立说成 SymPy 算错 | origin/scope/三值结果/候选绑定和双 sink 资格门；历史只读兼容。新增 Evidence 类不是必要前提；见 R2 |
| G3（01:11） | 改名“开放推理质量证据缺口”；高置信度确认缺证，低置信度推断失败程度 | `prompt_builder.py:146–166` 已要求前提/首错检查并声明 LLM review 非证明；`message-status.ts:8` 显示“推理审查意见”。已有课程条件候选 `evidence_builder.py:28–43` 标 not_checked。没有数据证明多步依赖是主瓶颈 | 小 gold 和局部干预；不先上 ProofState。付出人工审阅成本，收益待验证 |
| G4（01:12） | 保留；评测/供应商证据缺口；高 | E0 和数值 oracle tests 有效但用途不同。没有 E1/E2/E3 不等于模型已经差，也不说明既有诊断无用 | 聚焦首版 + 对应 gold + 后续授权 smoke；不把全题库当串行硬门槛；见 R3–R5 |
| G5（01:13） | 保留；产品缺口；高（代码），中（影响） | Newton 同页保存会更新引用，不能说 Agent 完全不知道动作结果。linear/integration 本身已能独立实验；缺可信 Chat 交接 | 先 linear 只读 ref/选中行/追问，保留原编辑保存入口；减少新写动作复杂度。真实使用收益待验证 |

### 必须立即纳入 S5.0

- 所有旧可达 parser/string-SymPy 路径受控；不以 evaluate=False、字符黑名单或单纯移到子进程替代安全语法。
- 同时处理 350ms 外层 deadline、worker 取消和正常子集；至少保留已经指定的正常表达式等价、导数候选及常见输入表示，无法保留就明示降级并列出具体清单。
- heuristic 只生成待核对线索；mistake/mastery 都需要资格判断；代算、未提交候选、unknown、reference_help 不冒充学生独立作答。
- 洛必达的“未定式分类”与“定理适用”分开；无法验证导数比极限及其他前提时不确认适用。等价检查声明共同定义域/排除点，符号域缺失时说明默认或澄清。
- 运行成功、数学判定、学习资格分别表述；unknown 不能映射 False，也不能在 UI 显示为“没触发过检查”。区分 unsupported、timeout、失败和未请求。
- 旧消息读取、旧 metadata 和继续聊天的来源标记须验收；正式历史数据不自动重算。

### 可以延后

完整定义域求解、通用洛必达定理 checker、多变量/特殊函数支持、完整旧能力恢复、统一 Evidence artifact、历史学习估计精确纠错、全部操作的 UI 卡片。延后不是默默标错；应可见 unknown、保留用户输入并继续教学讨论。

SymPy 本身使用三值未知语义，不能把“没有证明相等”直接当作“不相等”：[SymPy Assumptions](https://docs.sympy.org/latest/guides/assumptions.html)。该官方依据只支持语义原则；本项目具体错误路径以上述源码与探针为证。

## 5. 更小且足以支持下一项决策的首版评测

### 5.1 首先缩小问题

首版只回答：**修复后普通单步检查是否诚实保留正常能力；数值讨论的失败主要来自输入/引用、工具结果，还是模型解释。** 不以它判定全本科数学能力或所有开放证明的主瓶颈。

| 内容 | 建议最小规模 | 选择理由与分母 |
|---|---|---|
| E0 增量合同 | 复用既有 38/92，加 S5.0 必要边界例 | 固定响应和错误注入归 E0，不反复冒充新增模型行为题；按合同版本列变化 |
| E1/E2 共用 dev case pool | 8 个 case，每题可有行为与数学两张评分表 | 2 个正常/等价表示、2 个 scope/unknown/误区、2 个 linear 残差与工具决策、2 个 Newton 条件/上下文；是缺口覆盖矩阵，不是抽样总体 |
| 封存确认集 | 4 个由第二复核者独立选取的 case | 覆盖正常保持、域/误判、条件反例、数值解释各一；不照抄公开种子，不宣称统计精度。复核者未到位时只交 dev，封存集 pending |
| E3 | 2 条开发流程；独立参数只在必要时补确认 | ①已有 Newton 引用→预览→显式保存→新引用；②普通数值 Chat→结果范围解释→用户修订/追问。owner/取消/过期攻击仍复用 E0。只有实施 linear bridge 时再增加其真实页面流程 |

8+4 是建议的投入上限，不是有统计效力的“最佳样本量”。E1/E2 共享 case_id 与 split，保留多个评分视图；同一 case 不因两个标签变成两个独立样本。完成这个包的意义是发现可复核的具体失败和支持小切片选择，任何“总体提升率”仍不成立。

首版无需 12 家族×3 题：矩阵计算、Rolle、数列证明、概率误区与数值分析主线跨度过大，评审标准和工具可用性都不同。原 E2 36 题可以保留为覆盖 backlog；原 E1 的 owner/hash/卡片/终态/帮助边界大量属于现成工程合同，live 只需补“真实模型是否正确使用/表述”的部分。原 E3 的 1–4 dev、5–8 held-out 又混入不同故障类型，不是同一流程的普通参数留出，需分别标 stress suite 与泛化确认。

### 5.2 gold、隔离和指标

每题先写输入、数学域/量词、允许帮助、必要结论、禁止结论、可接受等价答案、可选工具、独立解答和评分资格。作者与第二复核者是两个人的职责；模型自审或第二次生成不算独立复核。当前未确认人选、课时及教材授权，不能假定已可得。

公开已知的 Newton 循环、积分混叠、互斥误判及本报告探针都归 dev。封存题按数学结构/来源分组，不只换常数；避免把用于调 prompt 的同模板变式包装成独立 held-out。课程检索可以包含正常定理，但需记录是否包含同题完整解答；不能用被测 verifier 或 root_runner 单独产 gold。小矩阵代回、积分解析值、反例的每个前提应独立核验。

主表固定列：`case_id / applicable / task_completed / mathematically_correct / appropriate_abstention / inappropriate_abstention / checker_coverage / verification_overclaim / help_violation / not_run_reason`。未运行保留在 manifest，另报执行覆盖率；不与答错混为一个比率，也不能静默删除。首错定位只在 gold 存在可定位错误的题上计分；无错题误报单列。反例要求题未给出 witness 属未完成，不是 N/A。必要前提遗漏与定理误用允许同题多标签，但 primary failure 只计一个任务。

人工盲评匿名 arm、随机输出顺序；二元 count/n、逐题差异、wins/ties/losses 优先。12 个异质 held-out 的 Wilson 区间即使按独立同分布计算，也不能证明覆盖总体；每家族 n=1 更不能作稳定排名。保留区间可以提示不确定性，但不能代替样本设计。

### 5.3 定位瓶颈与公平比较

| 待区分因素 | 最小观测/干预 | 仍不能推出 |
|---|---|---|
| routing | 保存初始/最终 intent、verification_mode、实际 graph branch；从同一初始状态强制允许 route | route 名字对就一定讲得对 |
| context | 保存可公开的引用/截断说明、输入 hash；补入必要而非完整答案的相同 context | 多给 gold 解答后的成功等于检索改进 |
| tool selection/arguments | 分别记请求工具名、参数符合 schema、参数对应数学任务、结果是否真正被使用 | 工具未调用就错；简单导数可合法心算 |
| 数学推理 | 有正确 context 和正确局部结果后仍出现前提/逻辑/反例错误，人工定位 | 剩余失败全部由缺 ProofState 引起，可能仍是题意、rubric或随机性 |
| verification coverage | 人工 gold 正确但 checker 不支持/不确定；单独报可判定覆盖和误确认 | unknown 等于学生错或模型错 |

每个干预独立恢复同一 fixture 状态，防止多次跑图累积 mastery/history。以是否改变同一错误作定位线索，疑难题做少量同配置重复；不要为每个失败遍历所有消融。S5 的 fixed-model runner 是报告和状态合同验证，不是数学模型质量实验。

历史整栈对照可延期。若保留：分别记录真实历史源码 SHA、安全 adapter hash、prompt/Guard/verifier/retrieval hash。要研究 Runtime 本身，就给两侧相同的安全局部核验和教学规则并命名“受控 adapter 对照”；否则只报告 historical_stack_comparison。新增 capability coverage、tool on/off 消融和共有能力准确性必须分表，原方案对此的限制继续保留。

## 6. 数学种子与反例复核

| 种子位置 | 复核 | 需要锁定的边界 |
|---|---|---|
| 02:60 求导 x² | d/dx=2x，正确 | 是计算请求还是学生提交候选；不要因算对了就给学生加分 |
| 02:61 小线性系统 | (1/5,3/5) 代回两行得到 (1,2)，正确 | 每步合法性和最终解分别评分 |
| 02:62、65 Rolle/连续不必可导 | abs(x) 在 [-1,1] 连续、端点相等，0 不可导，正确 | 必须指定 0 在区间内部，不能说连续不成立 |
| 02:63、03:90 Newton | x³−2x+2 从 0→1→0；f′(0)=-2，f′(1)=1，正确 | 只能直接否定“迭代点导数非零足够收敛”。若命题是全域 f′ 非零，需更换 witness，不能偷换假设 |
| 02:64 互斥与独立 | P(A∩B)=0，P(A)P(B)=1/4，不独立，正确 | 不能推广成“互斥事件永不独立”，零概率事件是边界；本题概率各 1/2 已排除 |
| 02:66 自映射缺失 | g(x)=x/2+1 的导数 1/2，g([0,1])=[1,1.5]，不自映射，正确 | 它否定当前区间上的定理套用，不证明迭代发散；扩大至 [0,2] 可自映射并收敛至 2 |
| 02:67 数列证明 | epsilon>0，取整数 N>1/epsilon，n≥N 时 1/n<epsilon，正确 | N 属自然数、量词次序与严格不等式必须明确 |
| 02:68、03:91 可逆/对角化 | 可逆推出 kernel={0}；Jordan 块特征空间维数 1，正确 | 指定方阵及域；“按代数重数有 n 个特征值”不保证有 n 个独立特征向量 |
| 02:69 残差/充分条件 | 小残差不自动给小根误差；未对角占优不推出 Jacobi 必发散，正确 | 缺定量任务实例、范数、容差与独立 oracle，目前还是题目方向 |
| 02:69、117 积分混叠 | 在 [0,1]，sin²(16πx) 的真积分 1/2；指定均匀采样可全部命中零点 | 对应 `T/test_numerical_lab.py:79–87` 是现有公开 dev 反例，不得变 held-out；不能声称任意采样算法都失败 |
| 02:70 x/x、sqrt(x²) | 前者在 x≠0 等于 1；后者对实数等于 abs(x)，正确 | 域缺失是规格问题；与“所有实数处定义相同”区分 |
| 02:71 洛必达 | 原比值=(x/sin x)sin(1/x)，沿 sin(1/x)=±1 两列趋于 ±1；导数比 [sin(1/x)-cos(1/x)/x]/cos x 也无极限，正确 | 仅分子分母趋零不能确认适用；还须规定单侧/双侧及穿孔邻域条件 |

若需要“全实数 f′ 非零仍不能任意初值收敛”的独立 dev witness，可用 f(x)=arctan(x)、x0=2：f′=1/(1+x²)>0，Newton 更新 N(x)=x−(1+x²)arctan(x)。当 |x|≥2 时，arctan|x|>π/3>1，更新异号且 |N(x)|>|x|+(|x|−1)²，因此绝对值发散。它需要人工复核，而且 atan 不在现有 typed grammar 中；不应为此立刻扩大工具。这一新增公开例也只能算 dev。

## 7. 新抽象逐项决策

| 对象及原位置 | 决策 | 与现有结构的关系、具体收益条件 | 最小代价与取舍 |
|---|---|---|---|
| VerificationEvidence，03:24–58 | **最小语义保留，独立模块延期** | VerifyResult 已有 verdict，MathToolResult 已有执行/scope，worker 已有 assumptions，message metadata 能保存版本。缺的是候选绑定和消费一致性，不是类名。只有“一个 run 多个结果错指学生 claim”经复现、且 guard/UI/评测至少两处需要同一绑定时，抽取小类型才有可验证收益 | 先局部字段及单一构造函数；避免双份 source of truth。验收是误确认消失且正常可判定题保留，不是 artifact 数量 |
| ReasoningState/ProofState，03:66–83 | 延期，先公开 step list 实验 | AgentState 已承载单 run 数据；LearningContext 负责可信来源，AgentRun 负责执行回执，它们不是数学证明状态，但缺新状态也不证明质量问题 | 同配置干预确实减少前提丢失后，再加有限 reducer/version。要承担 stale、编辑、提示泄漏和历史兼容成本 |
| Counterexample，03:85–97 | 保留题型和教学模板；新模块条件启动 | Newton 循环和积分反例已有 oracle/test；优先复用。只有能识别明确原命题、核对 witness 全部假设才升级确定反驳 | 先一个模板，精确 witness 或独立数学论证；缺量词就澄清，数值近似只 supported/unknown |
| MathProblem IR，03:60–64 | 完整 IR 删除出当前实施范围；小字段按需 | givens/goal/变量可能有用，但不能把 LearningContext 的权威参数再抽取一份冲突对象 | 先复用可信 snapshot，必要的公开题意字段可放当前 state；没有真实抽取失败就不新建管线 |
| Reasoning Graph，03:11、83 | 延期 | Course Graph 是课程检索；证明依赖图是另一对象，但当前没有 list/refs 不足的失败证据 | 省去图一致性、迁移和 UI；将来需依赖失效时再评估 |
| Lean，03:105–113 | 延期，不把 feasibility 塞入四至六周承诺 | 形式证明可以检查形式命题，但题意翻译和教学效果另需验证；现在根/线性/积分主线没有对应必须形式化的失败 | 人工 3–5 题也需工具链、statement 复核和结果解释预算；当前收益待验证 |
| A8，03:120–121、04:114–126 | 延期 | AgentRun 能读回中断回执，LearningContext 能重建新 run；不等于 checkpoint，但已覆盖现有短任务恢复方式 | 只有实测丢失长状态阻碍任务时再做 owner/version/幂等恢复；不自动 replay |

原方案“暂不换框架、不加第二 Registry/tracing、不做多 Agent debate/MCTS/任意 Python”的取舍合理，明确保留。Evidence 中 verified 与 supported 的双正向状态、unsupported 与 unknown 的区别必须有各自的消费规则；若首版没有行为差别，应简化而不是让 UI 学生记五种近义标签。

## 8. 产品顺序与原方案对照

| 候选 | 已有收益证据 | 风险/剩余成本 | 本报告排序 |
|---|---|---|---|
| 局部核验与学习资格修复 | 正确句子被扣 mastery、代算被加 mastery 已复现 | parser、deadline、metadata、历史多处联动；必须保住正常子集 | 第一，当前两周唯一承诺 |
| linear 可信引用 | 明确存在复制→跳转；owner 记录、轨迹、hash、残差说明已具备 | selected iteration/向量尺寸/省略行、旧记录版本、移动端/刷新；收益大小尚无用户数据 | 安全修复后的默认产品切片；先只读讨论，用原实验台改参保存 |
| 独立 VerificationEvidence artifact | scope 问题真实，但局部字段是否不足未证实 | claim 提取、绑定、展示、旧卡片、误指及重复字段 | 排在局部修复之后；有多结果绑定失败时才优先于 linear |
| integration 引用 | 同 numerical 存储可复用，估计范围有教学价值 | 采样遗漏与误差保证的解释风险更高，选中对象不同 | linear 后按需求选；保留既有独立实验 |
| 教材选段接 Chat | `reading_explanation.py:8–26` 已有 owner/hash/section/offset，29–65 已有独立解释 | Chat 引用是增量便利而非从无到有；片段条件遗漏、资料指令、版权/版本 | 若观察到主要痛点是定理条件来源，可替代 linear；当前没有足够证据认定必然排第二 |

不声称上述排序由用户实验得出。可先用两到三个合成任务加少量真实观察，记录复制次数、是否引用正确选中行、能否说明残差与误差的差别；这是可用性证据，不能代替学习迁移试验。没有用户参与也可交付功能，但教学收益保持未知。

| 原方案 | 建议方案 | 原因 |
|---|---|---|
| S5.0 2–3 日，广泛 unknown 后恢复 | 一条核验可信闭环，指定保留子集、独立检查 deadline、双学习 sink 和旧消息语义 | 防止安全止血被误写为可用性完成 |
| S5.1 新 runner 后全 32/36/8 冻结，再 smoke | 8 dev + 4 封存候选 + 2 dev 流程；协议 smoke 准入独立 | 降低 gold/供应商串行等待，先验证决策所需证据 |
| 历史共有能力对照作为 S5.4 主任务 | 同一安全 SHA 的局部干预优先；历史 stack 附录可选 | 减少安全 adapter、旧 prompt/Guard 和修复混杂 |
| S5 后 Evidence 或完整 linear preview/save 分支 | 优先现有字段；linear 只读引用可先独立交付 | 直接减少学生复制负担，避免同时新建动作路径 |
| 至少 3 个失败 + 改善趋势启动状态 | 多来源同机制、便宜局部修复比较、独立确认、净收益判断 | 三道模板题不能自动证明需要状态架构 |
| 6–9 日完整 S5 + 10–14h gold | 分开安全切片、评测工程、出题/复核/输出盲评、等待 | 降低承诺歧义，不用扩大加班掩盖范围 |

## 9. 请求、费用和运行准入的核对结论

**保留原方案实际 HTTP 前限额的设计。它有可复用的注入点，但尚无实现和真实 provider 验收；本轮不执行 live。**

批准一个纯文本 run 的最坏请求路径可暂按 routing 1 + review 1 + generation/tool continuation 最多 3 + Guard repair 1 = 6 计算；部分路径互斥或提前结束，上限不等于实际数量。8 个单 run 加 3 个 transport probe 得 51。每个多轮 episode 要按实际 run 数重新计数，不能继续套 8×6；人工重试也不免单。用户取消后的在途请求仍可能计费。

建议 live preflight 必须打印：批准 case/run 数、各 run 模型请求上限、工具预算、固定模型/端点 hash、允许路径、请求总额度、币种、价目版本、输入/输出/额外计费项的最大值来源、费用是否有可证明上界。单元验证应在 mock transport 的发送点断言：第 52 次不发送、预算不足的并发请求不发送、失败不退请求数、unknown usage 不返还不明费用额度、错误端点/embedding/后台调用被拒绝、取消/恢复不重置已消耗预算。

费用预留可表达为 `reserved_i = max_billable_input_i × input_price + max_billable_output_i × output_price + max_extra_i`，只有三个上界都由已核实计费合同支持时才成立。128KiB JSON gate 或“字节当 token”是本地请求限制，不能无条件替代供应商的计费 token 上界。若 reasoning 计费、模型默认输出上限或 usage 行为未知，现有 CNY 10 只能叫建议预算，不是硬上限。不能因事后报告费用 null 就说没花钱。

未知能力 bootstrap 要单独设计：`capabilities.py:18–36` 只识别 operator_verified/offline_fixture，`openai_compatible.py:293–294` 会拒绝未知 native 能力。评测协议 probe 可以走独立、受预算保护的固定 HTTP 请求，验证后生成待确认能力记录；不能在生产配置中先虚构验证结果。若费用上界仍无法确定，只能保持 live pending，或未来由用户另行选择明确说明风险的请求次数限额模式；本轮没有这样的消费授权。

## 10. 两周范围、四至六周扩展与重新估算

以下是审阅者提出的排程区间，不是实测速度或保证。假设一人熟悉代码、集中开发日约 6 小时、每周约 3 日；复核者时间和供应商等待单列。缺少这些条件就重新估算。

### 两周只做一个切片

**选择：S5.0“诚实的本步检查与学习资格闭环”。不选择完整评测平台，也不选择新 Evidence 类型。**

交付范围：封闭旧解析边路；保留明确的一元正常子集及必要表示；worker 与 collector deadline 正确配合；unknown/域/洛必达 scope；学生候选与代算分离；mistake/mastery 资格门；旧消息 legacy 可读与新轮次来源提示；一小组正常/反例/降级/历史回归，走编译图、临时库及可见状态。

预计 **4–7 个集中开发日**（含跨层回归和必要界面核对），置信度中低。两周只有约 6 日时，承诺的是该切片，超出的 operation 恢复延期；不能在第 6 日以“所有东西 unknown”验收能力保持。独立的人工 gold 整理可并行，但不再把独立 runner、全题库、真实模型报告算进同一个两周必交。

停止条件：发现仍有绕过受控语法的真实入口；正常承诺子集被 350ms/取消吞掉；unknown 或代算仍进入学习写入；owner/帮助/原子交付回归失败；不能解释的历史来源被重新标确定。出现其中任何一项，停止宣称切片完成，不恢复旧 eval，不扩到新模块。

### 四至六周可选扩展

- 第 1–2 周：上述 S5.0；第二人如可用，复核首批小 gold。
- 第 3 周：8 dev 小 runner/评分表及最多 2 个流程；具备独立预算准入后，另经授权做协议 probe 和小 smoke。供应商等待期间不机械扩大题库。
- 第 4–6 周：根据实际失败在两个方向中选一个：局部 scope/候选绑定修复，或 linear 只读可信引用。用已冻结确认题复核，补真实页面/失败演示。若确需模型建议→preview→save，作为后续独立增量，不与只读 bridge 合并承诺。

四至六周按该投入假设只有 12–18 个开发日，**不同时承诺完整 S5、Evidence、linear 写动作、integration、reading、ProofState**。未取得第二复核者和 live 许可，可交付离线产品与 author-reviewed 报告，不能交付数学准确率结论。

### 完整原 S5 的工作量核算

| 工作包 | 审阅建议预留 | 原估算容易遗漏的内容 |
|---|---|---|
| 安全解析/固定 operation/deadline | 3–5 日 | 正常表示兼容、取消、输出/进程回收、worker 错误映射 |
| 学习资格/旧消息/新旧 UI | 1–2 日 | 两个写入 sink、代算、历史 prompt 来源、SSE 与持久 metadata 一致 |
| 小 runner/manifest/评分入口 | 2–3 日 | case 共享、N/A/弃权/not_run、真实图及临时库隔离 |
| live transport/能力与费用 preflight | 2–4 日 | 并发预留、取消、未知费用、bootstrap、外部调用封闭 |
| 结果整理/定向干预/最终集成回归 | 2–3 日 | 逐题盲评接口、复跑状态重置、可比性记录、UI/脚本结果一致 |
| 合计 | **10–17 开发日** | 历史 adapter 如保留另估；不是测得的工期 |

该区间含前述 4–7 日切片，不能相加重复计算。降低 runner/题库/历史比较范围可缩短；实际适配一轮后应重新估算，而不是把 17 日变成新刚性承诺。

人工成本应按职责报量：以 36 道数学题为例，作者解答每题 10–20 分钟约 6–12h，第二复核每题 8–15 分钟约 5–9h；行为/episode 状态核对与争议裁决另预留约 4–8h。**这是排预算的情景，非实测；原 10–14h 可以覆盖部分第二复核，不能默认覆盖整个流程。** live 输出盲评按“实际输出份数×每份审阅时间”另外计，两 arm、多轮和分歧都会增加，不能只按 36 题计一次。先计时审完 4 题再校准其余规模。

外部依赖：第二复核者、封存题来源/管理、具体 model/endpoint 的协议和价格、live 授权、必要浏览器验收时段。任何未落实项均不指定完成日期。没有执行 next build；未来涉及 UI 时依 AGENTS 先停 dev 再构建，保留 typecheck/lint/可见状态检查成本。

## 11. 简历价值与证据优先级

06 第 9–16、22–26、30–37 行大体克制，已有成果/未来成果已经分开，应保留。需要收紧的是脱离上下文后容易被误读的句子：

| 原表达 | 建议表述/限制 | 优先补的证据 |
|---|---|---|
| 06:23“实现受控原生数学工具链” | “实现两类固定数学工具及原生协议适配，完成离线固定响应/真实 worker 验证；实际供应商另验” | 一个绑定真实 model/endpoint 的授权 smoke、续轮和 usage 回执；不能只靠类存在 |
| 06:24“真实请求边界、provider usage” | “在 HTTP 调用边界记录请求尝试与 provider 报告的 usage，缺失保持未知；本地协议验证” | live usage 覆盖和账单口径；不能说已实现费用硬上限 |
| 06:22“区分参考帮助与独立学习记录” | 限定“Newton 可信引用/受控实验路径”；普通文字核验仍有 G2 | 修复代算/heuristic 双 sink，正常与历史回归证据 |
| 06:24“655/51、38/92” | 标日期/源码 SHA；38/92 是协议子集，655 不是数学题数 | 可公开小型失败→修复→确认报告，比继续增长测试数量更有价值 |
| 06:80 Evidence 优先于 ProofState | 改为“先修核验语义，再根据失败决定是否抽取 Evidence 或状态” | 现有字段不足的具体复现与净收益，不是架构图 |

当前最值得讲的是 Newton 引用→预览→显式保存、固定 worker 的取消/预算、失败不假成功的原子交付及 honest unknown。最值得补的是 G1/G2 闭合后的真实入口证据、一个真实供应商工具续轮、少量独立数学 gold 和逐题失败解释。协议全绿不能写成数学准确率、自动证明或教学提升；个人贡献仍须按本人实际完成部分陈述。

## 12. 最终保留/修改/删除/延期清单

| 处置 | 项目 | 依据 |
|---|---|---|
| 保留 | LangGraph、LearningContext/Actions、固定 worker 生命周期、Guard、AgentRun/RunTrace、默认离线测试 | 已有源码/回归和可复用边界，不需要为 v3 重新命名实现 |
| 保留 | G1 必修、G2 三值与 scope、E0/E1/E2/E3 不混成绩、未知费用不补零、合成数据、人工 gold | 本轮验证支持；原方案这些限制合理 |
| 修改 | S5.0 能力保留清单、独立 deadline、候选资格/双 sink、历史读路径 | R1、R2 |
| 修改 | E1/E2 分母、弃权/覆盖、同 case 标签、首版范围、干预状态重置、Newton 命题量词 | R3、第 5–6 节 |
| 修改 | 依赖图、预算 bootstrap、工期/人工/等待分别估计 | R4、R5 |
| 删除出当前必交 | 32/36/8 全量冻结门槛、历史 adapter 对照必做、Evidence 必须成为下一模块、linear bridge 必带新参数卡 | 没有当前决策收益证据，扩大串行范围 |
| 延期 | 独立 Evidence 模块、ReasoningState/ProofState、通用 Counterexample 引擎、完整 MathProblem IR/Reasoning Graph、Strategy Search、Lean、A8 | 保留明确失败触发条件，不凭“至少 3 题”自动开工 |
| 延期 | integration/reading 二选一之外的多工作区扩展、正式历史成绩重算、真人学习效果研究 | 需要额外使用需求、数据/人员及验收边界 |

## 13. 未验证事项与证据缺口

1. **真实影响规模未知**：本轮未读正式学生数据库，不能估算受影响人数、记录数量或历史误判率。mock 写入证明可达，不等于已在真实库发生。
2. **模型质量未知**：没有 live 输出；不能断言 routing、context、tool selection、推理哪一项占主要失败。G3 是证据缺口。
3. **S5.0 未实施**：worker 新 operation、域合同、输入规范化、资格门及历史兼容均未验证；本报告不签署安全修复完成。
4. **预算/供应商未知**：未读取私密配置，未确认真实价格、token 上界、usage、native tools 支持及账单。51 是受限运行形态的建议请求上限，不是现有强制器。
5. **gold/保留集未落实**：没有已确认的第二人、排期、独立题源及盲评结果；已公开模板不能变成 unseen。
6. **产品收益未知**：没有本轮用户访谈/交互录像/页面验收，不能给 linear、reading 或 Evidence 的使用收益百分比。没有真人学习迁移证据。
7. **历史精确修复不可直接承诺**：现有聚合 mastery 和 mistake 缺 checker/event 级可逆信息；能否从其他事件可靠补证，需要另审，不能靠“读历史清单”推断可重算。
8. **本轮验证范围有限**：复用历史全套/E0，只补 34 项定向回归与探针；没有重跑构建、远端 CI、并发负载、OS 强隔离或完整安全审计。175 文件哈希匹配不等于所有依赖环境不变。

## 14. 本轮可复查的验证记录

定向测试的实际入口：从 `apps/api` 在临时数据库、`LUOJIA_NO_DOTENV=1`、进程内供应商 key 清除和 HTTPX 外发禁止的包装中调用：

```text
pytest.main([
  '-q', '-p', 'no:cacheprovider',
  'tests/test_verifier.py',
  'tests/test_verifier_hard_gate.py',
  'tests/test_step_checker.py',
  'tests/test_fast_context.py',
  'tests/test_learning_context.py'
])
34 passed, 1 warning in 3.66s
```

其中 warning 为 FastAPI/Starlette TestClient 的既有弃用提示；未安装建议依赖。本轮没有写测试文件或覆盖旧 results 回执。图探针复用 `T/test_agent_graph.py:make_repository/make_state/make_config/install_fake_stream`，真实 `TutorWorkflow.workflow.ainvoke`，只将 `_collect_local_hits` 替为 `(None,0.0)` 并提供固定模型正文，防止外部检索和模型随机性干扰。

关键原始观测摘录（合成/mock 环境，非真实成绩）：

```json
{
  "correct_concept": {
    "input": "互斥和独立不是一回事，对吗",
    "intent": "check_student_step", "mode": "symbolic",
    "verified": true, "is_correct": false,
    "mistake_writes": 1, "mastery_writes": 1, "delta": -0.265
  },
  "computed_without_student_candidate": {
    "input": "帮我检查求导 x**2",
    "history_concepts": ["导数"],
    "verified": true, "is_correct": true,
    "expected": null, "actual": "2*x",
    "mastery_writes": 1, "delta": 0.415
  },
  "unknown_result_with_same_mistake": {
    "verified": false, "is_correct": null,
    "mistake_writes": 1, "mastery_writes": 0
  },
  "normal_integral_control": {
    "input": "我算 ∫2x dx = x^2 + C，对吗？",
    "verified": true, "is_correct": true,
    "mistake_writes": 0, "mastery_writes": 1
  },
  "fixed_worker_x_squared_ms": [1324.70, 1299.91],
  "prior_e0_report_source_hashes": {"checked": 175, "mismatch": 0}
}
```

`unknown_result_with_same_mistake` 是直接调用 `_finalize_learning_state` 的资格门隔离探针，不冒称整条图自然产生了这一组合。带“对吗”尾词的另一个求导输入出现普通解析失败并进入 verifier_teacher；它说明抽取也影响核验覆盖，本报告没有将此单例外推成失败率。

## 15. 五个直接回答

- **原方案最大的问题是什么？** 安全/学习语义修复与广泛评测被绑成一个前置大包，缺少正常能力保持和明确决策目标；有完成工程清单却未解决学生问题的风险。
- **S5.0→S5 的顺序是否仍成立？** 对 live 和部署成立；对离线 gold/runner 准备不必全串行。S5.0 必须补齐 deadline、候选资格和历史读语义，再以小评测推进。
- **VerificationEvidence 是否真的值得优先？** scope/origin/eligibility 值得立即修；独立 Evidence 模块目前不值得排在这些局部修复和有证据的产品接入之前。
- **如果只能完成一个切片，选什么？** S5.0 诚实的本步检查闭环：既安全，又不把正确陈述判错、不把系统代算记成学生掌握；正常一元任务仍能得到有范围的反馈。
- **哪些复杂设计应删掉或延期？** 删除当前必交中的全题库门槛、历史对照适配和 Evidence 必做；延期完整 IR/Reasoning Graph、ProofState、通用反例引擎、策略搜索、Lean、A8，以及同时接入多个工作区。
