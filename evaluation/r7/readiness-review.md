# R7 readiness review 与 R7.0 质量攻坚

日期：2026-10-18（America/Los_Angeles）。主判定 **HOLD-QUALITY**；允许 **GO-R7.2-PREP**，不启动 R7.1 新领域开发。工程验收、确定性数学修复、真实模型质量和学习收益分开判断。

## 1. 版本与范围

起始分支 `feature/course-graph-2.0`，HEAD `15def45bf4a718b1bab5d3a95e10133ab0aea274`。相对本地 `origin/feature/course-graph-2.0` 引用领先九次；初始审查未fetch；后续经用户追加commit后push授权，ls-remote核对目标分支远端为`47d60bc1d1971e76f6337404fbb1f83b9345b9bf`。推送与远程CI以最终交付回执为准。用户列出的 `4c3bf80`、`db5c01f`、`268d9a1` 均在本地历史；其后已有 R6.5 的 `36ef451`、`15def45`，这是摘要之外的漂移。

起始工作树有既有 R2 脚本／协议／测试、Explore、materials、records、notebook、numerical-lab、侧栏和共享工作区等前端改动，另有 next-env、tsconfig、三份文档删除及未跟踪的 R2 工具／UI 提案。未 reset、stash、清理或纳入本轮提交。本轮仅修改 root oracle 和必要回归，新增 R7 审核材料／脚本及评价文档入口。报告针对真实工作树，不以干净 HEAD 冒充验证对象。

已读取 AGENTS；R64 README、acceptance、协议／题集／rubric／freeze 及原始 artifacts；R5 README／failure-analysis／冻结采集器与适配器；R2 当前工作树的 R2.3 E1 协议、review packet、live smoke 与预算代码；docs/evaluation、architecture、learning-design；CI；相关数学、教学决策、上下文、私人召回与测试。R2 的 live smoke 是旧有限授权适配器实验，不能当本轮授权或完整应用评价入口。

实际生产入口包括 [graph.root_diagnostic_node](../../apps/api/app/tutor/graph.py)、[root_diagnostics](../../apps/api/app/tutor/root_diagnostics.py)、[root_finding](../../apps/api/app/math_tools/root_finding.py)、[step_checker](../../apps/api/app/math_tools/step_checker.py)、[verifier](../../apps/api/app/math_tools/verifier.py)、[TeachingDecision](../../apps/api/app/tutor/teaching_decision.py)、[answer_guard](../../apps/api/app/tutor/answer_guard.py)、[fast_context](../../apps/api/app/tutor/fast_context.py)、[learning_context](../../apps/api/app/tutor/learning_context.py)、[explorations](../../apps/api/app/tutor/explorations.py)、[exploration_advice](../../apps/api/app/tutor/exploration_advice.py) 和 [personal_recall](../../apps/api/app/tutor/personal_recall.py)。未重建工作流、数据库或 Agent。

## 2. R6.4 证据矩阵

原始快照：[acceptance-2026-10-17.json](../r64/acceptance-2026-10-17.json)。本机审核输出 `results/r7/evidence-audit.json`，用原 R5/R64 校验器重读 72+33 份 artifacts；8 份验证日志摘要、浏览器任务的 10 个日志／截图引用均匹配。不是仅转述 README。

| 记录／判定 | 实际对象、入口与模型 | 能证明 | 不能证明 |
|---|---|---|---|
| 已证明：105/105 E0 | `results/r64/final-v3.json`：旧 R5 72、探索15、私人18；`r64_r5_capture.py`、`eval_r64.py`；固定回复，真实 ASGI／编译图／数值 runner | 有界输入、协议、计算、保存及来源串联可完成 | 不是105道独立数学题，更不是105次真实模型答对；quality、usage、费用 null |
| 已证明：9/9 输入控制 | 同报告 `levels.E0.pair_input_control` 和 `final-v3-artifacts/private/*`；三个领域×相关／无关／失效，P0/P1 | 同历史、问题、模型配置与非个人提示投影；相关P1各选1条，其余0；选择理由、ID、版本进入真实 Chat 输入 | 回复是相同中性 fixture；没有追问改善、记忆污染率、质量差异或区间 |
| 已证明：5/5 E2 自动化 | `results/r64/browser-receipt-v1.json`、`browser-restore.log`、绑定截图；Playwright+合成身份+固定模型+真实计算 | Chat到探索、Newton／积分返回、私人图恢复、材料引用保存的当时功能链路 | 非5名用户、非真人成功率、非当前源码浏览器复测 |
| 已证明：1128 API／116 Web | `results/r64/npm-test-release.log`；npm test：离线 pytest 与 Node 工具测试；其余8份绑定日志可重读 | 当时真实脏工作树的工程回归；身份／来源／版本等合同 | 不认证供应商、JWT真实用户、开放数学答复或学习收益 |
| 已证明：R6.5 漂移 | `evaluation/r65/acceptance-2026-10-18.json`、`results/r65/npm-test-final.log`；1128 API／117 Web、浏览器7/7 | 后续导航／恢复改进与当时功能验收；因此116和5不是最新前端历史数 | 七项仍为自动化与固定模型；本轮未重跑浏览器 |
| 可推测但未证明 | 有限核验、受限工具、条件检索和私人上下文可为反馈提供额外证据 | 有潜在差异机制，值得与普通 LLM 对照 | 不能由工具正确或关系被选中推断教学收益；相关性筛选仍是词法启发式 |
| 未执行／被阻塞：E1 | R64计划105，真实执行0，人工评分0；本轮另建45条精简回放计划，执行0 | 未运行状态与失败分母完整 | 当前模型版本、数学质量、私人增益及置信区间均未知；等待授权、独立审核和原生 live 采集 |
| 未执行：真人E2／E3 | 参与者0；E3 12个计划测量名额没有独立题／人 | 研究设计可以准备 | 当场实验成功不是迁移；学习收益 null |

快照与底层报告的 E0、E1、E3 完全一致。E2 的快照用 `persisted_record` 压缩底层 `saved_record`，两个 JSON 整体不相等；已按任务状态、原始回执及摘要分别核对，没有把结构差异报成任务失败。R64 源码摘要与现在相比，后端本轮 root oracle 变化，前端18个既有／R6.5文件漂移；旧快照未改写为“当前通过”。39个公开槽位只有32个不同 prompt；所有题仍为 agent_prepared_only，独立保留六个名额为空。

### N03/Q03 与删测审核

`evaluation/r5/r6-freeze-v1.json` 与 R64 freeze 的题集、arms、`scripts/eval_r5.py` 摘要仍匹配。原始 `results/r64/r5-original-recheck.json` 是只选择两题的6/72完成、0/24匹配，不能把其余未选题说成失败；原 R5 全量72次中22/24可比较。原 collector 将 reviewer JSON 返回给 PolicyRouter，协议混用使两题停在追问。

[r64_r5_capture.routing_fixture](../../scripts/r64_r5_capture.py)只返回原 fallback intent 的类型化 PolicyDecision，不读取题号或 gold；72/72、24/24是修复离线采集协议后的匹配。**原生真实路由未获验证。** 原失败 JSON、R64 首轮15个 Windows TestClient 网络门禁失败和 `npm-test.log` 的1127通过／1个 SOURCE_DRIFT失败均仍在，未移出分母或覆盖。

核对 `git show 4c3bf80`：建议编辑全流程 GS/Newton 双实例减1；仅让 fixture 预先返回“不实验”的三个实例删除；三领域 schema 解析减2。前端另删固定标签及原样回传字段断言。三领域真实API运行、积分混叠反例、非法计划／原子性，以及 personal_recall 的 owner、pending/edit/accept/reject、revision、失效来源和不可替换旧运行仍有独立测试。本轮没有恢复镜像断言；新增四个实例针对首错／后续非法值／重开反馈，两个实例针对新回放入口的授权输入绑定和截断预算行为。

## 3. 数学与教学失败簇

### C1：证据范围越界（高影响，当前模型行为尚未实测）

数学反例已由真实 runner 支持：Simpson 对 `sin(8*pi*x)^2`、[0,1]、n=4→8 得到近零结果和0误差估计，但解析积分为1/2；n=6→12可得到约1/2。二者不能让估计自动成为严格界。另有 N04：残差10^-12而根误差1；G03：不严格占优却 rho=1/5，充分条件未满足不是发散证明。

证据：`results/r64/final-v3-artifacts/explorations/Q-design.json`、`evaluation/r64/acceptance-2026-10-17.json.real_local_computation_examples`、`test_shared_exploration.py::test_aliasing_counterexample_estimate_does_not_bound_true_error`；本轮 `results/r7/current-private-v2.json` 重新执行同类受控计算。**这些是反例和风险假设，不是当前模型已犯错的成绩。** 风险位于受控工具／引用到最终正文的解释：工具标签与 TeachingDecision 能限制来源，answer_guard 只能拦部分显式措辞，无法证明所有语义均未越界。普通 LLM也可能犯错；Agent 的额外计算只有被正确解释时才可能带来差异。

### C2：较晚非法观察遮住首个错误更新（当前真实可复现，已修）

对 f(x)=sqrt(x)-2，Newton 更新为 T(x)=4sqrt(x)-x。学生轨迹 `[1,3,4,-1]` 中 T(1)=3 正确，T(3)=4sqrt(3)-3≈3.9282032303，不是4，因此最早更新错误在 x2；末尾 x3=-1 另有定义域错误。旧 oracle 先遍历全部函数值，直接报告 k=3，反馈未保留正确前缀。换 NaN 尾部也一样。不动点 g(x)=(x+4)/2 的 `[0,2,4,-1]` 同样首错k=2，旧实现只报k=3。

这是输入／工具过程诊断失败，进入 `RootEpisodeService.submit → graph.root_diagnostic_node → feedback_text`，不依赖模型臆测。详见 [保存的 before/after](first-error-before-after.json) 与 `results/r7/before-first-error.json`、`after-first-error-v3.json`。本地计算、真实持久化与重开反馈均复现；不是供应商质量试验。适用范围仅为受控 Newton／不动点轨迹，未声称能定位任意自然语言证明首错。

### C3：缺条件时补造语义／计划协议不一致（历史真实观察，当前风险待重测）

`results/r61/real-model-attempt2.json` 的 missing 案例：学生只说“第三步比第二步小”，真实 `deepseek-v4-flash` 回复却在 known_conditions 写“第三步残差小于第二步”。这属于问题理解错误：不能推定比较量。GS案例正确解释充分非必要，却仍只追问矩阵，未主动设计所求全称判断的反例；Newton结合旧关系，但 action／proposal、候选端点不一致导致建议不可用。第一批三个回复均长度截断；这是六次旧授权调用的历史失败，非R64或本轮真实成绩。

现有 exploration_advice 已补比较量未知、动作与计划一致、图端点完整等规则，且可舍弃坏候选图保留可用建议；未真实重测，不能声称已修复模型质量。发生位置包括理解→结构化决策→建议可用性。与普通 LLM相比，结构化校验能阻止非法计划执行，也可能丢弃有用解释；需同时评价拒绝是否恰当与用户能否继续任务。私人召回的9对 fixture 只证明输入控制，尚不能确认真实追问更针对或不会污染记忆。

## 4. R7.0 本轮改动

最小修复在 [root_finding.py](../../apps/api/app/math_tools/root_finding.py)：保存可计算前缀，先按声明规则核对其相邻更新，再报告后续非法观察。初值不一致同样优先于更晚错误；此前合法更新被明确保留，追问定位到 `k=1→2`。有正确前缀而后续确实非法的控制仍返回该非法观察，不会因修复而误判完成。原 Newton 阻尼／重根、二分、残差／根误差语义继续回归。

oracle 改为 `root-oracle-v2`，旧持久化回执不被重写；无数据库迁移。提交／重开沿用原 owner、版本、帮助与 ACK 逻辑，无成功或掌握升级。`root_runner` 的有限参考轨迹算法未改。

另以合成身份运行真实编译 `TutorOrchestrator.stream_reply`：`root_submission`进入原诊断节点，流完成，最终正文和保存的`learning_meta.root_diagnosis`均定位k=2、保留0→1并追问1→2。`results/r7/compiled-root.json`保存SSE与原消息；模型入口被设为调用即失败，实测供应商请求0。该证据覆盖修复在实际Chat编排中的可达性，仍不属于开放自然语言模型质量。

| 输入 | 修复前 | 修复后 | 控制条件 |
|---|---|---|---|
| Newton `[1,3,4,-1]` | numeric_nonfinite，k=3 | newton_formula，k=2；承认0→1，重算1→2 | 同函数、初值、goal和容差，无模型调用 |
| Newton `[1,3,4,"NaN"]` | numeric_nonfinite，k=3 | newton_formula，k=2 | 仅替换末尾观察，错误仍更早 |
| 不动点 `[0,2,4,-1]` | numeric_nonfinite，k=3 | fixed_point_update，k=2，g(2)=3 | 同函数与phi；不复制Newton专用答案 |
| Newton 正确x2后接非法值 | 原来指末尾 | 仍指末尾k=3，不完成 | 防止把后续错误吞掉 |

新增 [r7_math_probe.py](../../scripts/r7_math_probe.py)可在独立临时CourseStore中重算并重开；没有按题ID修改 Agent 决策。回归在 `test_root_oracle.py`、`test_root_episodes.py`，期望值由独立更新公式计算。新回放入口复用 R5/R64 输入采集、S5 严格读入／原子预算，不增加教学节点。

值得保留 R6.2 的有限、版本绑定、解释可见的已确认关系召回，以及 R6.3 的 typed plan→学生确认→原 runner→规范引用。当前词法主题／概念匹配只覆盖三领域；固定Newton活动的精确检查只适用于该活动，不能外推为通用数学能力。已有确定性活动与通用探索保持边界；没有证据支持新增 Agent、加长全图提示或扩展自治记忆。当前不为了整洁重构已有三领域薄适配。

## 5. E1 准备与外部依赖

[versioned protocol](protocol-v1.json)、[逐题审核指南](review-guide.md)、[空授权模板](approval-template.json)与 `results/r7/e1-review-packet-final.json` 已落盘。九个冻结公开开发题覆盖局部正确、首错、缺前提、充分／必要性、合法替代、残差与误差、积分估计边界；私人九对继续沿用相同合成历史。没有把生成题改称独立保留题，也没有修改旧gold。

本轮当前采集：R5选择9题共27/72完成、9/24匹配；完整未选分母保留，进程退出1是有意的部分计划状态。R64采集15探索＋18私人，旧消融72留not_run；没有声称新跑105次。两者均固定模型且外连拒绝。审核包45条全部not_run、quality／usage／实际费用null、供应商请求0。

Live入口可以在获得新授权与数学复核后执行**最终Teacher输入回放**；严格限制为27+18次，预发送原子预算、已审核输入token上界、输出上限、45秒总超时、无重试、首败停止，失败保留正文／usage／分母。批准文件摘要绑定同一预算账本，换输出文件不能重置额度。该功能只经MockTransport验证。原生实时路由、上游审核、工具选择、输出修复和保存仍未做真实对照；这也是后续采集要补的工程范围，不能把component回放命名为完整D2收益。

目前供应商、模型版本、token测量、价格和授权全部未定。45×1536=69,120只是建议输出token计划上限；输入成本和所有计费项需要目标供应商合同，无法诚实报价。建议按27与18分别授权／冻结小批。实际需一位数学作者加一位独立数值分析审核者，每人约2–4小时用于题目、等价解和45份回答复核；该时间为工作量估计，不是已开展审核。费用需报价后确定。

评分沿用十一维、逐句证据与摘要绑定，不合成固定回复质量分；私人对照报告原始P1−P0、退化、未评分分母和宽区间。尚未取得任何可评分真实回答，差异与置信区间均null。真人E2可先准备4–6名成年参与者、每人30–45分钟的探索任务与恢复日志作为形成性研究，须另行同意和招募；E3由独立作者准备迁移／7日延迟题，未执行。

## 6. R7 决策卡

**主判定 HOLD-QUALITY；允许 GO-R7.2-PREP；不允许启动 R7.1 新领域开发。**

三条依据：工程与数学工具证据可复核，但不等于开放反馈质量；当前发现且修复了会误导学生的确定性首错缺陷；当前模型／独立数学评分／真人及迁移仍没有准入证据。不能选GO；也不是仅等待外部签字，原生live采集和当前风险重测仍有技术工作。

最多三个关键阻塞：

1. 条件、量词、局部正确和证据界限尚无当前版本独立数学审核及真实模型对照。
2. 旧真实建议的语义补造／协议失败未真实重测，私人增益未评分；新回放也不覆盖原生实时路由／工具／交付。
3. 没有独立保留题作者、真实参与者与迁移／延迟数据，不能宣称学习有效。

下一轮优先：先独立审九题及首错反例，补原生live采集范围；在明确预算授权下做可比小批并保留退化，然后根据评分回修C1/C3。R7.2仅进行任务脚本、同意、盲化审核和独立题准备。避免代码沙箱、通用证明器、大型多Agent、全局图实体平台或再加一层提示框架。

| R7.1候选 | 新的高价值数学机制 | 启动代价／条件 | 当前选择 |
|---|---|---|---|
| 数值线性代数：病态与误差 | 小残差与前向误差的差异、条件数／扰动、稳定性；能深化现有GS边界 | 在旧域关键题有独立可复核质量基础后，审核有界条件数／扰动计算与合法反例；局部扩展适配和任务 | 优先候选，但本轮不开工 |
| 无约束优化：步长与收敛条件 | 下降、停机与驻点的区别，步长／线搜索及正则条件 | 需要新runner、目标函数与步长对照、独立数学题；新增机制是否优于现有域深化须先论证 | 保留为后选，不双线开发 |

只有当前旧领域关键严重错误被独立复核解决、真实对照结果和失败都可追溯、拟扩领域提供上述新增机制，才重新判断GO-R7.1。工程全绿或选取9/9历史不单独满足该条件。

## 7. 文档与验证

本轮验证结果与日志见 [机器判定摘要](decision-summary.json)。全量 npm test 为 API **1134通过**、Web **117通过**，API有5条依赖／布局警告；定向数学及原有边界126通过，新回放2通过。类型检查、生产构建（20路由）、lint（0 error、8条已有warning）、可靠性47/47合同与128/128实例通过。完整本机结果在 `results/r7/`，未纳入数据库、密钥或用户材料。核心命令：

```powershell
python scripts/r7_evidence_audit.py --output results/r7/new-audit.json
python scripts/r7_math_probe.py --output results/r7/new-math.json
cd apps/api
python -m pytest -q tests/test_root_oracle.py tests/test_root_episodes.py tests/test_math_feedback_boundaries.py tests/test_shared_exploration.py tests/test_personal_recall.py tests/test_explorations.py tests/test_r7_quality.py
cd ../..
npm.cmd test
python scripts/eval_agent_reliability.py
python scripts/check_docs.py
cd apps/web
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

未执行真实模型、独立人工评分、真人／迁移或生产部署。用户在审查末尾追加授权commit后push；仅推送已提交历史，工作树改动保留，远程CI结果另见交付回执。本轮无UI修改，未新增浏览器成绩。前端构建前确认3000／3161没有开发服务；自动生成的next-env恢复既有工作树内容。

13个有既存字节摘要的用户改动文件与R6.5结束时一致，见`results/r7/protected-worktree.json`。tsconfig未手工编辑，当前git diff为空；没有起始字节摘要，不能额外认证它的字节级一致性。next-env只在确认内容差异为Next自动生成路径后恢复原备份，未用git覆盖用户文件。

执行中的非质量失败也保留：首版数学probe因Windows SQLite连接未关闭导致临时目录回收失败，已显式关闭CourseStore后重跑；不是模型失败。首版after使用旧oracle标签，中间回执保留，最终以`after-first-error-v3.json`及绑定源码为准；diff复核补正停止原因只标原轨迹末尾，随后重新全量验证和采集。原R64失败和冻结输入均不覆盖。
