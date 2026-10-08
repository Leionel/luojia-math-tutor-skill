# CODEX 交接文档

## U08 可撤销登录会话（临时库）

注册签发预检、用户/session原子写入、Bearer v2 sid/撤销/当前角色、幂等服务端退出、跨标签页/首页身份保护已实现。知识JSON/API899/Web70、增量11合同19实例、构建通过，lint0错误10既有警告；实际合成账号登录/双标签退出，临时库1登录1撤销账号保留。migration7增表，在临时库backup/恢复/integrity与失败回滚验证。正式库未读未升级；下一次Repository初始化会应用7，正式启动前必须实际备份/恢复验收。v1不得HTTP授权，重新登录；不是JWT/OIDC。细节 planning/complete-upgrade-2026-10/delivery-u08.md。用户授权额度内继续，本轮已额外交付U16/U08，剩余条件阶段仍pending。

## U16 静态降级

用户授权 U06 完成后有额度继续，已完成 U16。模型 HTML 的脚本默认禁止且无运行入口，旧消息原源码/静态图保留；删除30秒计时器与脚本重启，教学 prompt teaching-v2.8 与 UI一致。Web65、prompt1、构建通过，lint0错误10既有警告。实际临时库网页确认 srcdoc 无script/on事件/外链、sandbox空、关闭草稿保留、390px无溢出；危险死循环未执行。回执 planning/complete-upgrade-2026-10/delivery-u16.md。下一先 U08 临时库会话，正式库备份/恢复另验。

## U04–U06 接续交付

用户授权接续与分步提交。积分同页固定引用、代码静态规则/行号来源讨论、讲回原句跨度/逐条件未核验意见/前后版本已实现。知识JSON/API880/Web65、增量14合同33实例和受影响85项回归通过，构建/类型检查通过、lint 0错误10既有警告；真实网页用临时库和固定模型，讲回为自我映射，模型结构化路径离线验证。没有真实模型消费、经审gold、学习收益或代码执行。细节 planning/complete-upgrade-2026-10/delivery-u04-u06.md。下一优先U16静态降级；用户授权有五小时额度时继续，不自动满足外部gate。

## U01–U03 首版交付与接续

用户授权实施并 commit。线性实验同页固定引用、课程/私有Markdown选段Chat、只读已有任务续接已实现；保持旧Newton动作与独立帮助边界。API847/Web最终64、原E0 38/92、新增13/28、生产构建通过；桌面/390px及选段/任务刷新用隔离临时库和固定模型验收，无真实模型消费或学习效果结论。具体边界和日志见 planning/complete-upgrade-2026-10/delivery-u01-u03.md。原runtime dirty、原型/egg-info、07审阅保护不动。用户随后授权接续U04–U06，逐片验证并提交。

## 2026-10-07 完整补充升级计划（只规划）

用户澄清为planning/README.md“还需要补什么”的升级，选择先完整计划、逐功能可验收切片/保留全部目标。本轮未做原先猜测的linear业务实现。新增planning/complete-upgrade-2026-10/README.md、18个独立切片草案、register与implementation-notes；重整总索引并链接旧目录。先U01真实linear引用，再U02选段/U03任务续接，U16图示安全降级尽早，其余接续/条件启动。F1–F8、Agent、六个月研究与原扩展目标保留，不许全并行或虚构六个月交付保证。

基线d9b9c849bf160a29f7d45efd330601b1083493b7。规划核实root context只Newton、numerical记录source_hash/schema但无统一graph revision、现有共享会话、阅读scope、代码静态无独立rule version、注册先写用户再签发、HMAC两段token v1非JWT、动态图30秒timer非CPU强杀。docker/wsl CLI存在不代表daemon/C0。真人gold、供应商/费用、PDF/字幕/真实授权、剩余开发产能待验证；条件阶段Feasibility4/5，未假签全5/5。

344个业务/测试/工具/评测文件hash本轮前后不变；只检查文档链接/覆盖/保护文件，不重跑业务测试，不消费模型，不派发外部任务。原runtime dirty/egg-info/public原型保留，07原文不改。后续用户选择切片才实施，不把此计划当功能完成回执。

## 2026-10-07 分步提交与S5.3离线预算

用户授权继续下一步并分步提交。已有4批：988e65c核验、f90cc2e界面、085b9e6评测、dd95458规划。原回执“未commit”是实施当时快照，不改旧HEAD证明。新S5.3离线预算预留组件/SQLite账本只允许MockTransport，固定纯文字endpoint/model/output，并发/费用/取消/失败/重启/重定向/变更profile/ledger损坏均受控，actual_cost未知，无真实供应商消费。仅synthetic价格合同，未验证真实token/额外费用，不称live硬预算已启用。生产client/协议probe/live继续pending。

根知识JSON/API819/Web56通过，新增预算39项；S5.3 E0 16合同39实例。源码/测试/manifest hash在results/s5-3-budget-proof.json；全日志s5-3-*。新预算切片另批提交，最终Git hash见log与本轮回执。细节planning/agent-v3-2026-10/13-delivery-s5-3-offline-and-commits.md。原runtime dirty、egg-info/public原型保留，07原文不改；无push/deploy/正式库更改，不重复UI构建。下一候选linear只读可信Chat；S5.2真人复核仍pending。

## 2026-10-07 S5.2材料与工程流程首版

用户授权开始5.2。新增8道公开dev独立解答/逐题rubric（agent_prepared_only，真人审核/二审pending）、严格内容/输入/rubric/版本绑定、未签署review worksheet、仅caller-supplied-unverified的录制回答导入与输出覆盖保护。新增2条固定模型实际ASGI/SSE完整流程，独立临时库与合成Principal：Newton引用/预览/显式save/重试/新引用/保护；普通数值Chat候选修订/输入保存/metadata恢复/两sink不写。共3run18阶段通过，不等于真实JWT、模型数学内容或真人学习效果。矩阵分支没有请求自动单步核验，输入绑定来自真实用户消息；不伪造step_hash。

根知识JSON/API780/Web56通过；S5.2新增31回归、targeted80，E0 v2 38/92与S5.2 11/31通过。无生产代码/表/接口/依赖/UI改动，不重复前端构建。详见planning/agent-v3-2026-10/12-delivery-s5-2.md、evaluation/s5/README.md和review-protocol.md；results/s5-2-*为ignored生成证据。16保护文件不变，HEAD仍52373b632013e0808f8939b1fd8876edbc5e2850；未commit/push/deploy/live消费。

下一步真实审核/二审与评分仍pending，4个确认register仅空名额无假hash，不称封存题；S5.3需独立供应商/预算/授权。linear可信引用、C0/C1及真人研究未由本轮升级。S5.2材料与工程首版交付不等于全质量验收。

## 2026-10-07 三份规划统一入口（仅文档）

用户询问learning-experience与agent-engineering后续。新增planning/README.md，保留产品六个月F1–F8、工程A/S历史与v3当前S5三种视角；同步旧入口/implementation-notes。不重复排已完成首版。下一S5.2内容/流程证据，产品候选linear只读Chat，S5.3 live/预算有条件；F6/F7/C0/C1/A8保留启动门槛。读源码确认可信LearningContext仍限定Newton，原回执用于交付范围、本轮不重做全功能验收。保留07和runtime原dirty，无业务改动/提交/推送。

## 2026-10-07 S5.1首版与弹出菜单实色修复

用户启动S5.1并要求深入审视其内容。已实现offline/dry-run/replay、4类固定模型真实compiled graph/worker采集、独立临时SQLite与写入/保存恢复观察、固定分母/hash/人工来源合同、Markdown解释报告。来源为fixture，不计入真实模型数学质量；8道公开dev输入/rubric仍pending，真人二审/4道封存/2流程/live预算未完成。核心目标及case取舍见planning/agent-v3-2026-10/11-s5-1-evaluation-rationale.md，交付回执10，接口evaluation/s5/README.md。

教学模式/工具和同根因思考弹出菜单改实色主题背景，去透明变量后缀与模糊，说明文字加深。HTTP/构建CSS验证实底；浏览器UI访问被工具URL策略拒绝，无新截图验收。3000端口保留生产预览。根测试知识JSON/API749/Web56通过（新增S5.1 49）；E0 v2 38/92、S5.0 10/45通过；Web类型/lint/build通过，lint10既有警告。16保护文件hash不变。

HEAD仍52373b632013e0808f8939b1fd8876edbc5e2850，保存原dirty；未commit/push/deploy/真实模型消费。下一步S5.2先作者解答/rubric审核，补实际观察adapter和完整流程；无已复核真实失败时不凭空扩Reasoner。不得把fixture合同通过写成模型准确率或教学增益。

## 2026-10-07 S5.0 与首页/文案交付（工作区）

用户授权开始S5.0，追加页面去AI味文案与fancy首页。已完成有界AST学生检查、固定私有worker/独立最多5秒预算、输入与候选重绑定、来源/范围/unknown、mistake/mastery双sink资格、帮助锁执行期监视与子进程回收、legacy历史prompt/展示；teaching-v2.6，无新表或模型权限扩张。首页加入深橄榄曲线区、光晕/脉冲、暂停/离屏/减少动态支持，操作提示改具体文字。实际手机焦点引起overflow内部滚动问题改为clip。

根npm test知识JSON/API700/Web56通过，E0 v2 38合同92实例，独立S5.0 addendum10合同45实例；Web typecheck/lint/build通过（lint10已有警告）。真实compiled graph/临时SQLite/SSE与真实worker回收均有测试；浏览器fixture为固定模型、隔离库、外部HTTP禁用，不是live质量/教学评测。16保护文件哈希一致。完整行为、降级范围和证据见planning/agent-v3-2026-10/09-delivery-s5-0.md；results/s5-0-*和s5-0-ui保存本机证据。

HEAD仍52373b632013e0808f8939b1fd8876edbc5e2850，保留此前dirty，未commit/push/deploy、正式库迁移或真实模型消费。下一批S5.1/S5.2聚焦runner/gold仍pending；linear只读引用与独立Evidence尚未实施。旧审计“G1/G2未修复”是历史快照，不能作为当前运行真相，也不能把公开E0通过当质量准确率。

## 2026-10-07 按独立审阅修订规划（仅文档）

用户“开始修改”承接方案审阅，本轮修改规划，未实施S5.0。先读planning/agent-v3-2026-10/08-s5-0-verifier-contract.md、04-roadmap.md、02-evaluation-s5.md；07-plan-review.md原样保留。源码HEAD仍52373b632013e0808f8939b1fd8876edbc5e2850；旧模型Python路线已退役，旧学生解析/学习资格问题仍未修复，不能把新文档当修复完成。

两周唯一承诺S5.0：正常一元等价/导数候选与有限表示、独立核验deadline（检索350ms不吞worker）、原输入/域/候选绑定、mistake/mastery双sink资格、无候选代算不计学生正确性、unknown/历史legacy与可见状态。初始核验最多5秒为待校准配置，4–7开发日为预算假设。安全止血若缺正常能力，只标部分完成；不恢复unsafe parser或任意Python。

gold与offline准备可并行，首版8 dev共用E1/E2池、4独立确认候选、2 dev流程；32/36/8全量目录与历史adapter降backlog。完成/正确/恰当弃权/coverage与固定分母一起报，各干预重置初始状态；确认题用于调优后需新封存题。协议probe不等全题库，但live需隔离预算/profile与另行消费授权；51只适用3 probe＋8单run×6，不能套多轮episode。费用上界未知则不运行硬预算live。

S5.0后默认linear只读引用，保留原实验台编辑/运行/保存，新参数卡后排。先现有meta/一处投影，只有具体多结果误指且多个消费者需要才抽Evidence；ProofState/IR/Lean/A8保持条件延期。完整原S5情景10–17日包含首片，人工出题/二审/输出盲评和等待另计，均非实测。

2026-10-04 API655/Web51/E0 38/92为历史完整回执；10月7日07记录定向验证，本轮文档改动不重跑业务测试/build/live。原用户runtime文档、07报告、原型/egg-info、175份源码哈希保持；改前17份文档快照在ignored results/agent-v3-plan-revision-20261007-before。未改密钥/数据库/能力开关、未commit/push/deploy，一次性自动化仍停用。实施偏离写implementation-notes.md，不能沿旧段落机械重排。

## 2026-10-04 预约推理审计与v3规划（仅文档）

按预约完整读取旧目录`docs/planning/Audit_on reasoning_20261003.md`，审计当前`D:\Projects\na-tutor\luojia-math-tutor-skill`，SHA `52373b632013e0808f8939b1fd8876edbc5e2850`。先读`planning/agent-v3-2026-10/00-current-baseline.md`、`02-evaluation-s5.md`、`04-roadmap.md`；七份主文档加drift/implementation notes已写。保留S3/S4与旧规划作为历史，不重复立项LearningContext/Actions/Typed Runtime/RunTrace。

本轮离线复验知识JSON/API655/Web51、E0 v2合同38/38实例92/92，生成证据`results/agent-v3-audit-*`。固定无副作用探针确认旧`verifier.parse_math`/字符串SymPy入口可绕过typed AST；正确“互斥≠独立”被关键词规则判错且可能进入mistake/BKT；定义域/unknown/洛必达范围也有问题。**这些仅被发现，未修复**。下一批S5.0先修旧检查安全与origin/scope/unknown/学习资格，再S5.1做8–12任务离线tracer，逐步冻结E1/E2/E3、gold、预算smoke和对照。VerificationEvidence优先候选，ProofState/Lean/A8有条件启动；linear/integration与reading选段是后续两条产品候选，不同时全接。

本轮仅更新规划/current README索引与三份项目记忆，无业务源码/测试/配置/数据迁移。未读写正式学生库、未调用真实模型、未重新build/UI验收、未commit/push/deploy。起始dirty `runtime-review-schedule.md`与egg-info/三个public原型目录保持原样；不扫入未来提交。S5 CLI/gold/预算/改善结果均为计划，当前不能写数学正确率或教学效果。本轮一次性自动化`agent`已由app工具设为`PAUSED`，回执确认停用。

## 2026-10-03 S3/S4 固定数学工具与调用计量

用户授权S3/S4。已新增固定math_differentiate/numerical_run、Chat Completions原生分片组装、两轮预算、实际worker取消/超时/64KiB输出回收、帮助前后重验与hint_exposed；模型生成Python调用点全部退役，旧executor仅历史内部实现/测试，无app调用方。Newton可信引用继续固定快照和服务器业务卡片，不把模型计算结果自动保存或算学生掌握。teaching-v2.5 / delivery-v2，默认typed关闭，精确selector+resolved_model+endpoint hash绑定能力和可选价格。

每次客户端调用记录安全span/call/parent、起止/状态/耗时、正文首delta（非reasoning、非缓冲等待）、provider usage及可选日期价格；工具span关联提出请求的模型span。缺失/冲突usage与不支持cache/reasoning计价保持未知，部分汇总标明覆盖。run-v1现有JSON兼容，无表/迁移/依赖。修复重复取消中SQLite已提交但内存序号未更新：持锁等待写入并同步再取消。重启过期run闭合span，不重放。

最终本地JSON/API655/Web51、v2合同38/38实例92/92、TypeScript/lint（0error/10既有warning）/生产build通过；隔离真实HTTP适配器/编译图/worker/Guard/SQLite网页验证3请求/2报告/1求导/1修复、刷新一致与390px无横向溢出，价格是合成测试值。实际现有两库SQLite backup integrity_check=ok后恢复正常API8000/Web3000，未改私密env。完整配置/证据/限制见planning/agent-engineering-2026-10/delivery-s3-s4.md。下一步S5/A5约4–6集中开发日含回归，人工gold另计；真实供应商能力、账单、教学收益、远端CI/部署未验收。下方S1/S2“下一步S3/S4”是历史状态。

## 2026-10-03 S1/S2 实验聊天闭环

用户授权S1/S2并要求更精致的界面。已实现Newton保存记录的LearningContextRef与服务端快照，owner/input_hash/runner_version/graph_revision/selected_step重验；最多11行/8KiB，参考讨论不写学生作答、mastery/BKT或独立成绩。桌面小珞侧栏、手机抽屉、指定步骤、刷新/会话映射恢复，以及参数编辑→预览→显式保存→同页更新已落地。卡片关联成功且可见的Guard通过消息/run，24小时过期，每卡3次预览，最多100次迭代；重验帮助边界、版本/哈希与最新预览，幂等保存。未保存的预览也记录help事件并从未见probe候选中排除。

卡片由服务器固定映射组装，默认参数沿用原实验；未实现模型自主工具选择。本引用路径关闭生成Python执行和联网，其他旧Python路径待S3/A6.2退役。笔记/实验共享完整会话控制，主聊天共享ChatLifetime与MathMessage；锁在创建前取得，切换/卸载/退出拒绝旧回调，取消/失败/EOF不能留下可执行卡片，草稿按owner保留。没有新表/迁移/依赖，不改学生成绩规则。新字段用现有JSON，缺少历史预算显式标为legacy_default。

完整离线JSON/API600/Web48、针对46项、A3契约19/19与实例40/40通过；TypeScript/build通过，lint0错误/10既有警告。隔离真实HTTP/编排/Guard/SQLite与固定模型响应验证桌面预览/脏参数锁定/保存回流/刷新/完整聊天步骤恢复、390px抽屉/草稿/取消/Escape与焦点恢复；真实模型与真人学习收益、远端CI/部署另验。截图与日志在ignored results/s1-s2-*。交付细节见planning/agent-engineering-2026-10/delivery-s1-s2.md。下一步S3/A6.2→S4/A7→S5/A5，余8–12个集中开发日含回归余量，人工gold另计；完整A4/F1/F2/F5/F8、跨领域可信引用、A8/C0另估。


> 历史交接：2026-10-03（S3/S4固定数学工具与调用计量；当前先读本文顶部10月7日修订）。先读 `planning/agent-engineering-2026-10/delivery-s3-s4.md` 与主规划§12，再读S1/S2回执。Runtime约束/a6-tool-runtime.md继续使用，下一步S5/A5；M0/M1见研究文档§27.8，研究主线见§27。下方历史状态仅表示当时进度。

## 2026-10-03 聊天衔接意见与局部修复

用户追加“让新功能长进聊天”意见，要求核对。主要缺口成立：stream没有统一学习引用，numerical-lab仍复制后跳/chat，工作区未共享当前任务。但聊天已有root submission/诊断卡/probe/run，notebook也有内嵌聊天，不能宣称只有Markdown。来稿Newton示意第一步-1.75错误，实际-2→-1.8→-1.769948187。审阅基线0340c49。

发现并复现帮助保护不一致，按此前“可以改的直接改”局部修复612e3a4：共享helper增加进行中章节自检；求根新运行在缓存复用前保护，历史两个GET经service保护，伴读选区改共享helper。6失败/1通过的新增检查复现后，针对72项通过；完整知识JSON/API589/Web45通过（results/chat-integration-review-tests.log）。无数据库迁移、分数/独立成功/掌握度规则变化，未重复前端build/lint或UI演示。入口检查不能收回已打开帮助、旧聊天、外部帮助或全部在途请求。

规划改为A4.1可信Newton实验引用→A6.1/A4.2最小业务动作/卡片/内嵌聊天→A6.2计算工具与旧Python退役→A7→A5。A4–A8未实现；保留既有线性/积分。首批一个实验讨论/参数预览/显式保存闭环，LearningAction共用A6合同，不建第二Registry；预览仍记帮助曝光并被probe选题读取，不计独立成绩。12–19个集中开发日含回归余量，单人每周约3日约4–7周、人工复核另计；全F1/F2/F5/F8接入与A8/C0另估。A5基线改为帮助修复后的612e3a4。A3离线契约19/19、实例40/40通过，报告源码SHA=612e3a4且文档修改期间tracked_worktree_dirty=true；75个本地链接/锚点与UTF-8检查通过。详见新审阅、主规划与Deviations，最终提交/推送以本轮回执为准，远端CI/部署未验证。

## 2026-10-03 Runtime 审阅与日程合并（仅文档）

用户要求此前开发完成后审阅所贴 Agent Runtime 意见并加入日程。审阅基线 `150553b`，来稿基于更早的 `ee373ae`。当前 A3 协议 CLI 和线性/积分实验已交付；无可信实验聊天快照、原生工具调用、真实 usage/span 或图 checkpoint。README“A3 尚未完成”旧句本轮修正。

推荐剩余顺序 A6 类型化工具 → A4 实验快照/预算/来源 → A7 span/usage/必要 capability → A5 E1/E2 与可选真实 E3。保持已有 A4/A5 编号；A8 仅在恢复需求成立后做单路径持久暂停 PoC，学生代码 C0/MCP/专门 dashboard 另行评估。计划 11–17 个集中开发日含回归余量，单人每周约3日为4–6周；人工复核另计，无固定截止日。A6 首批一条既有 numerical.run 垂直路径，再受限符号工具/旧模型 Python 路径退役；schema/timeout 不等于数学证明或 OS 强隔离。

本轮仅规划、README 与交接修订，未实施 A4–A8、调用真实模型或迁移数据库。详见上述两文档与 `implementation-notes.md` 的 Deviations。提交前完整 npm.cmd test：知识 JSON / API583 / Web45 通过，日志 results/runtime-planning-tests.log；65个本地文档链接/锚点、UTF-8与变更范围检查通过，diff check通过。前端源码未改，未重复build/lint；提交/推送以本轮最终回执为准，远端 CI/部署/教学效果无新增证据。保留现有无关原型/egg-info/ignored results、env 和数据库。

## 2026-10-03 新版海报接入与 v1 归档

用户自行生成并提供新版海报，明确要求原图改名为 `v1poster`。根目录 `LJ_Tutor_Poster.png` 已替换为附件原始 PNG，旧图原样归档为 `v1poster.png`。两图均为1055×1491，哈希分别与附件/替换前原图一致；未重绘、压缩或修改品牌素材。README 直接展示新版，第一版放在折叠历史区；交付哈希与提示词见 `planning/learning-experience-2026-10/poster-update-prompt.md`。

新版可见六项功能、Newton 示意轨迹和“代码未执行”；图中控件是静态示意。文件哈希、文档链接与 diff check 通过；业务源码、配置及冻结研究数据未改。本轮离线 npm test：知识 JSON、API469、Web40 全部通过，日志 results/poster-asset-update-tests.log；提交/推送回执单独报告。以下上一轮生图失败/未替换的记录保留为历史，不代表当前海报状态。

## 2026-10-03 README 与海报交接

README 已按当前 F1–F5/F8 六入口重写：Windows 快速开始、现有环境文件保留、模型配置、账号边界、可复现 Newton 循环例、受助/独立证据区分，以及静态代码审阅限制。修正 `.env.example` 关于课程库默认只在内存的旧注释；配置值与业务代码未改。历史 V8 20 条评测与当前求根功能、工程测试分开说明。

本轮 `npm test` 重跑通过：知识 JSON、API469、Web40；日志 `results/readme-update-tests.log`。文档相对链接检查无缺失，循环与收敛示例已离线核对，diff check 通过。未从干净环境重装依赖，未重复生产构建或真实模型/教师/学生评测。

海报提示词见 `planning/learning-experience-2026-10/poster-update-prompt.md`，完整及精简请求分别保存为相邻 txt。内置 imagegen 两次网络失败，第三次精简请求按用户“我来”停止；没有生成或替换海报。旧 `LJ_Tutor_Poster.png` 与原品牌素材保留，README 将旧图明确标注为历史设计。用户自行生成后再按提示词核对中文、Newton 轨迹与“代码未执行”，不能直接声称图片已验收。

此前四批提交 `047f134`、`f875b3e`、`381c0d6`、`65ece36` 已推送，本轮 fetch 核对 HEAD 与远端 `feature/course-graph-2.0` 一致。本文下方历史“未push”只说明当时状态。本轮文档提交与推送结果单独报告；不包含既有原型、egg-info、ignored results、数据库或 env。远端 CI 与部署未验证。


## 2026-10-03 小珞、教学流程审查与 F1–F4/F8 加强

用户授权加入数学学姐形象“小珞”、检查明显不符的流程/设定/提示并直接修复，随后授权在五小时额度耗尽前继续加强薄弱处。本轮原样接入小珞 PNG 到首页/聊天欢迎区，明确 AI 身份；统一独立 probe 的新帮助保护（普通聊天/笔记/相似题/求根提交），保存每条回答自身教学模式和检查状态，修正模式与任务意图冲突、相似题未持久保存、抽样教材笔记全书措辞及提示数据边界，新增根主题开发参考题。teaching-v2.4；计算执行与数学语义验证明确分开。

F1 反馈待确认时锁定输入和新提交，保留幂等重试；F2 原文段落追加笔记草稿且刷新恢复；F3 逐步/播放/暂停/同条件轨迹对照/历史回看与按实验保存的本地复盘；F4 未确认选项按 owner/测评恢复、题号导航与确认进度；F8 已保存行号定位、未提交修改提示、两版原文对照、tol/max_iter 使用与 solve 本体作用域静态检查。学生代码仍不执行，提示/手动轨迹不提升独立成功。无新增表/依赖。

本地最终 npm test：知识JSON/API469/Web39；生产build及TypeScript通过；lint0错误/10原有警告；diff check通过。浏览器在隔离演示库验证五类增强、首页与聊天形象，以及390px实验布局；未调用真实模型。日志 results/f1-f4-f8-strengthened-*.log。完整审查、修复与剩余弱项见 planning/learning-experience-2026-10/xiaoluo-chat-lab-review.md。真实模型/教师gold/真人学习收益/C0/C1/远端CI未验证。数学语义Answer Guard及动态HTML同步JS的CPU强制隔离仍未闭合；历史内容/外部帮助无法由当前应用保护排除；完整PDF标注、跨设备本地草稿与静态规则版本回执后续再做。未commit/push/deploy，保留原工作区成果与无关原型。额度读数91%时结束新功能扩展并收尾。

## 2026-10-02 首页与F5/F8（上一轮回执）

用户继续授权更新首页、加强F1–F4，并启动F5和F8首版。首页接入只读owner概览、六入口、真实任务恢复与参考测评；中文衬线排版、数学示意与减少动画适配。F1找回计划外/跨日未完成检验；F2笔记按原文章节过滤；F3参数/预测草稿及实验链接恢复；F4当前测评/结果链接恢复。详见 `planning/learning-experience-2026-10/home-f5-f8-delivery.md`。

新增learning_extensions：F5文字讲回、引用原句/来源哈希/补充版本，模型意见明确未核验；无模型可自我对照。F8限定Newton静态审阅、手动轨迹独立诊断与前后版本比较。没有C0隔离回执，因此不执行学生代码，旧code_executor未放宽。F5/F8帮助受首次独立probe保护，不更新独立成绩。复用learning_records，无新增数据库表或依赖。

本地npm test：API458/Web35/知识JSON通过；生产build与类型检查通过；lint0错误/10原有警告。浏览器使用隔离演示库；真实模型/教师核对/学生试用/C0/C1/远端CI未验证。预览 localhost:3000 首页、8000 API，仍用 results/f1-f4-ui*.db 和LUOJIA_NO_DOTENV=1。未commit/push/deploy，既有原型/egg-info等文件保留。

用户提供透明PNG Logo已原样接入首页、学习工作区、对话品牌区与浏览器图标，复用BrandLogo，原图SHA256一致。资产apps/web/public/brand/luojia-logo.png。

## 2026-10-02 F1–F4首版（上一轮回执）

用户授权先做F1–F4，并授权自检后升级。今日学习/教材伴读/求根实验/章节诊断已接入，聊天顶部“今日学习”进入；交付范围与后续门槛见 `planning/learning-experience-2026-10/f1-f4-delivery.md`。新增LearningWorkspace、受控root_runner、source-bound explanation与learning_records；runtime课程库默认随文件SQLite派生持久库，显式COURSE_STORE_PATH优先。旧段落“无配置即内存”只保留作历史基线。

本地npm test API445/Web34/JSON、typecheck/build通过；lint0错误/10既有警告。390px/1440px浏览器核心流程、恢复和弃测通过，results/f1-f4-*为隔离演示证据。参考题计分不是研究成绩，真实模型、教师gold和学生试用未验证；旧版本任务恢复/完整PDF标注/独立研究测验未完成。没有commit/push/deploy；保留既有原型/egg-info等无关工作区文件。

## 2026-10-02 功能规划入口（仅规划，优先读取）

用户要求在竞品建议基础上形成详细规划，选择融入现有六个月数值分析主线，并希望利用AI加速、不提前删除后续功能。已形成[总规划](planning/learning-experience-2026-10/README.md)：F1今日任务/间隔复习、F2教材伴读、F3数值实验优先，F4章节小测、F5讲回、F6视频伴学、F7教师简报、F8代码作业全部细化；七份文件含基线门槛、核心分计划、后续任务与实施记录模板。

下一步从B0核对现有求根WIP开始：本轮源码已存在root_expression/root_finding/root_diagnostics、前端输入/反馈卡及probe/ack/replay，不能重复实现，也不能仅凭文件存在宣称M2/M3已验收。核对过程含数学参考、10条episode、交付/幂等/权限/公开答案边界，以及根前端测试与CI清单差异。F2可在材料身份/授权/版本确认后先做，F1成绩与F3诊断依赖B0通过。

目标窗口2026/10–2027/03；沿用每周约3开发日的未确认估算，58–85开发日加返工余量。AI节省比例、教师档期、招募、字幕与隔离运行环境均未实测；按两周实际完成量校准。研究冻结版与候选功能隔离，独立学习结果不由受助成功/自动实验/模型讲回评价替代。

本轮仅写规划与项目记忆，未主动修改业务代码/正式数据/冻结题集，未运行应用测试或构建，未commit/push/deploy。后续偏离与验收写planning/learning-experience-2026-10/implementation-notes.md，并回写三份项目记忆。

## 1. 这是什么项目

**珞珈数智助教**（`luojia-math-tutor-skill`）：面向大学数学（当前主攻《数值分析》教材）的 AI Tutor，后端 FastAPI + LangGraph（`apps/api`），前端 Next.js 16.3.8 + React 19.3.0 + Tailwind（`apps/web`），教学规则与知识数据在 `luojia-math-tutor/`。当前工作分支 `feature/course-graph-2.0`（未合回主分支），远端同名。

构建/测试命令、代码风格、提交规范见 `AGENTS.md`，全部仍然有效。关键差异提醒：

- `pytest` **必须在 `apps/api` 目录下跑**（仓库根目录跑会收集到无关文件报 36 个 collection error）。
- 测试离线由 `LUOJIA_NO_DOTENV=1` 保证（`tests/conftest.py` 会清掉 LLM/MINERU key），别破坏这个机制。
- **不要在 dev server 运行时执行 `next build`**（会写坏 `.next`）。
- 提交时 CRLF 警告属正常（Windows 环境）。

## 2. 必读文档（按顺序）

1. `luojia_tutor2_branch_log.md` —— 本分支自 split 以来所有轮次的实测记录 + 「尚未处理的问题」清单（§6，部分已划掉表示已修）。
2. `luojia_tutor2_course_graph_research_refined.md` —— **先看 §27 最新推进计划**，再看 §26 接手缺陷、§25 历史检索基线、§24 改造方案。244 题 retrieval eval 与 228 题 Case eval 分开报告。
3. `results/retrieval_eval_results.json` —— 最新评测数字；`evaluation/retrieval_eval.json` 是评测集。

## 3. 当前状态（截至交接）

- 教材链路（上传 → MinerU 解析 → 结构感知切分 → 候选抽取 → 审核台）端到端可用；`apps/api/luojia_tutor.db` 存 1 本教材（`doc_656067dd6720`，32 万字，430 chunks，CJK bigram 索引）。
- 检索基线（`scripts/eval_retrieval.py`，244 条评测集）：chunk 级 BM25 **R@3 0.752 / R@5 0.798 / MRR 0.708**，vector（本地 LSA 降级臂）0.581/0.685/0.498，hybrid(RRF) 0.688/**0.805**/0.657；**图层 unit 级 dry-run R@3 0.725，hierarchy@1 = 0.867**（详见 research doc §25.3）。
- 前端已统一到「农场水墨」设计令牌（`apps/web/tailwind.config.ts` 重映射了 slate/indigo 等默认色名——**改 UI 时注意类名颜色≠视觉颜色**）；阅读字体（衬线/无衬线）与主题（light/dark，存储键 `luojia-theme`/`luojia-reading`）持久化已修好。
- 交互与思考链优化：消除白屏等待大卡片，采用极简折叠墨绿书卷徽标；输入台新增「🌐 联网探微」与「🧠 运思强度」（4档深度映射至 DeepSeek/OpenAI/Qwen/GLM/Anthropic）；新增藏书阁「Ctrl+K」全局跨域检索抽屉（教材定理/错题/笔记一键研讨）。
- 最新本地验收：API 329 项、前端 20 项与知识 JSON 通过；生产构建/typecheck 通过，lint 0 错误/10 条已有警告；前端依赖审计 0 漏洞。未运行远端 CI，离线隔离门控未变。

## M0 / M1 最新状态（2026-10-01，本段优先于下方历史记录）

M0 已实现完整 SQLite 正式图、事务审核、generation CAS、幂等回执、备份/恢复工具；M1 已接入生产 Case / 单元召回，API、EvidenceBuilder、离线 evaluator 排序一致。228 题开发集 R@1=162/208（77.9%）、R@3=200/208（96.2%）；原20题通过，61题仍需审查。教师 gold 与未见任务验收待完成，M2 尚未实施。

实际 API 库为 `apps/api/data/course_store.db`，初始化正式快照后仍 pending495 / superseded283，没有批量审核。数据库备份与完整验收见 `COURSE_GRAPH_M0_M1.md`；持久化须配置 COURSE_STORE_PATH，未配置为内存模式。先教师核对失败家族和少量求根材料，再推进受控数值诊断、提示与修订重验；不要继续盲目扩题或扩章。以下旧段落保留为基线证据，不是当前完成状态。

图谱 UI 最新方向：参考 Obsidian Graph View，采用圆点/细线的有界力导向布局，关联数量决定大小，悬停/选择突出邻域，公式/内容在侧栏。窗口尺寸变化自动适配，选择不重载图，拖动不强制回位；卡片网格方案未提交。新增3项布局回归，最新API329/Web20。完整记录与截图入口见 COURSE_GRAPH_M0_M1.md 追加段。

## 4. 明确的未完成项（按优先级）

> **2026-10-01 优先级：以研究文档 §27 为准，§26 保留缺陷证据。** 大批审核前先修正式图持久化与审核事务；随后接生产 Case/单元召回，再推进受控数值 Oracle、提示、修订重验和最小事件链。临时库已复现：approve 后单元存在，重建服务后候选仍 approved、单元消失。`hierarchy@1=0.867` 来自 pending 的独立排序 dry-run（13/15），审核入图不足以自动保证生产复现。种子包实际为27 units、21 relations、15 Cases；Overlay是证据计数层，聊天尚未自动写入该层。

> **228题v2 benchmark已交付：** AGY网络失败后，按用户要求由GPT-6 Luna实施、主代理复核。见 `evaluation/CASE_BENCHMARK_V2.md`：Case Recall **11/208 (5.3%)**、严格决策 **34/222 (15.3%)**、域外 **10/11**、域内新Case **7/7**；204题至少一项不匹配、工具异常0。原20题仍为Case16/16、可接受决策集合20/20、域外4/4；原gold是多标签，不能称严格决策全对。原题集/种子包/matcher哈希保持，正式库和审核状态未改。最终npm test：API265、前端12、知识JSON通过。新集尚需教师抽查，下一轮优先修审核持久化/事务，再改Case召回与生产图检索。

1. ~~vector/hybrid 评测两行空~~ **已补（2026-09-30）**：无 key 时用本地 TF-IDF+LSA(k=256) 降级臂出数；拿到 `DASHSCOPE_API_KEY`（写进 `apps/api/.env`）重跑 `scripts/eval_retrieval.py` 即得真神经向量水位——hybrid R@5 已是全场最高（0.805），换强向量臂后 R@3/MRR 大概率跟涨。
2. ~~hierarchy 要走图层~~ **已补（2026-09-30）**：评测加了图层 dry-run 臂（加权 IDF + 标题×3/关键词×2 + sqrt 归一），**hierarchy@1 = 0.867**。注意这是拿 495 条 pending 当 approved 代理测的；生产里 `CourseEvidenceBuilder` 只认已审核单元，所以**审核入图是把 0.867 变现的前提**。
3. **LLM 答题质量 baseline 缺失**：README 的 `90.0% (18/20)` 没有裸模型参照系（branch log §6.1）。
4. **候选审核仍待推进**（`data/course_store.db` 的 `graph_candidates`，495 条是 9 月 30 日快照）：先通过 G0 的持久化/事务验收，再少量试审求根材料。审核数量与历史 dry-run 分数不等于生产召回效果。
5. ~~无 CI~~ **已加（2026-09-30）**：`.github/workflows/ci.yml` 三 job（api pytest / knowledge JSON 校验 / web tsc+单测+build）。**部署仍无**。
6. 浏览器「上传」按钮的真实点击从未测过（链路其余环节都是 curl/API 实测的）。
7. ~~Desmos 正式 key~~ **已配置（2026-09-30）**：正式 key 在 gitignored 的 `apps/web/.env.local`（`NEXT_PUBLIC_DESMOS_API_KEY`），勿提交；缺 key 时模态框有空态兜底。

## 5. 关于最近两个提交的诚实声明

`ba55797`（glassmorphism 风格 UI）和 `0b035d8`（公式块复制交互、探索快捷问句）由另一个 AI 完成，**我没有审查过它们的正确性**。已知风险：glassmorphism 的新样式可能与 `tailwind.config.ts` 的农场水墨令牌重映射打架（类名写着别的颜色，渲染出来是令牌色），接手后如发现视觉不一致，先查这两处。

## 6. 安全红线

- `LLM_API_KEY` / `MINERU_API_KEY` 只存在于 gitignored 的 `apps/api/.env`；`NEXT_PUBLIC_DESMOS_API_KEY` 在 `apps/web/.env.local`。**永远不要把它们写进任何被跟踪的文件**；提交前 `git grep "sk-"` 检查。
- MinerU token 90 天过期，上传报 401/403 就是过期了。
- 教材模型输出、上传文件、候选 payload 都按不可信输入对待：走现有 sanitizer（`lib/html-sanitize.ts`）和表达式解析器，不要裸渲染 HTML。

## 7. 协作方式

- 提交信息沿用 `feat:/fix:/test:/docs:` 前缀 + 英文一句话，正文说清 why（看 `git log` 学样例）。
- 大改动先在本分支小步提交；UI 改动请附带 headless Chrome 截图佐证（`chrome --headless=new --screenshot=...`）。
- 文档（branch log / research doc）是本仓库的记忆，做完一轮必须回写，不许只留 commit message。

## 最新工作轮：Prompt重塑（2026-09-30，teaching-v2.1）

本节优先于上方历史测试数量与prompt状态。用户授权全部整改，详见 PROMPT_ARCHITECTURE_V2.md。统一系统规范与实际加载的三份指南；单一resolved_policy裁决；Case决策/条件/推理/来源传入；证明先审查；严格Verifier与评审schema；失败验算降级；图片真暂停、确认/编辑与草稿历史恢复；公开文案不虚称严格验证。当前验收：API294项、前端12项、知识JSON、tsc通过，lint退出0（现有警告）。测试进程设置SYMPY_GROUND_TYPES=python、MPMATH_NOGMPY=1绕开本机gmpy2本地扩展错误，离线门控不变。线上模型质量、真实上传点击、教师与学习效果验收仍未做；Case benchmark分数不可当本次prompt质量证明。已有服务需重启加载规范。未提交/推送/部署。


## 2026-10-01 — 响应式聊天 UI 与公式渲染修复

- 修复窄屏左右空白抽屉：Sidebar/LearningPanel 只渲染内容，由 MobileDrawer 统一控制显示、遮罩、关闭、焦点循环及跨断点恢复；桌面断点为 1024/1280px。
- 学习抽屉复用桌面状态/笔记内容，补齐移动端随堂笔记入口。顶部品牌/新会话避免换行，次要导航收进“更多”；输入区移动端取消常驻算子滚动条，简化工具文案，保持 16px 输入字体与底部安全区。中文 IME 确认不提交，粗指针设备 Enter 保留换行。
- 提取 message-parser.ts，修复同一行 $$…$$ 和 \[ … \] 的闭合处理，未闭合公式不吞后续空行/标题，保留代码与转义美元符号；加入 Markdown 表格渲染。原“膜振动方程”会话现已正常显示全部公式与后续标题，DOM 中 KaTeX 错误为 0。
- 学习面板取消未检查/无知识点时的默认 50% 展示，区分模型复核与本步检查；掌握度明确为估计。
- 验证：npm test（API 294、前端 17、知识 JSON 均通过）；tsc --noEmit 通过；lint 0 errors，原有 10 warnings。浏览器检查 320/390/768/1100/1440px、390x480 短视口，无整页横向溢出；Esc/关闭按钮/遮罩、Tab 焦点循环、跨断点关闭、移动端笔记切换与“更多”菜单通过。截图：results/ui-2026-10-01/mobile.jpg。
- 边界：未进行真实手机软键盘验证；开发服务器继续运行，因此未运行 next build；未提交/推送。框架仍为 Next.js 14.2.35。官方支持政策已将 14.x 列为不支持，建议后续独立迁移到 16.x 稳定补丁版，核对 React/API/lint 后再构建，不在本轮混入升级。

## 2026-10-01 — Next.js 16 升级

Next.js 14.2.35 → 16.3.8，React/React DOM 与类型依赖对齐 19.3.0，`eslint-config-next` 同步 16.3.8。lint 迁移为 ESLint flat config（ESLint 9.39.5；已有 effect/ref 用法保留兼容配置，React Compiler 未启用）。Next 16 自动调整 `tsconfig` 为 `react-jsx` 并加入 `.next/dev/types`；`next.config.mjs` 固定 Turbopack 根目录并关闭自动生成 agent 文件。新增 `npm run typecheck`（先 `next typegen`），CI 独立运行 lint，并纳入公式解析回归；README/AGENTS 同步 Node 与命令要求。

本轮先停 Web dev server 再构建，生产构建通过；完整离线 `npm test`：API294、前端17、知识JSON全部通过；typecheck 通过，lint 0 errors/10 条已有 warnings；`npm audit`（含开发依赖）与 `npm audit --omit=dev` 均为0漏洞。测试仅在进程内设 SYMPY_GROUND_TYPES=python、MPMATH_NOGMPY=1，conftest 门控不变。Next/React/ESLint 的最终安装树无 peer invalid。

服务已重启：Web `http://127.0.0.1:3000/chat`、API `http://127.0.0.1:8000/health` 均200；图谱页200。浏览器复核原会话48处公式、KaTeX错误0，390×844无页面横向溢出，左右抽屉有内容并可关闭；React Flow加载27节点/21关系，控制台error为0。截图 `results/ui-2026-10-01/next16-react19-mobile.png`。这不是手机软键盘或真实模型质量验收。未提交/推送/部署，未运行远端CI。

## 2026-10-01 — 长期推进计划（仅规划）

研究文档 §27 已保留用户引用的“可验证诊断闭环”判断全文，制定2026/10–2027/03详细时间线与2027/04–09条件性展望：G0恢复与审核事务 → G1生产召回 → G2 Newton错误/提示/修订重验与最小事件 → G3求根家族与Overlay → G4教师gold及冻结独立集 → G5试用 → G6协议 → G7学习效果 → G8复现与扩展决策。日期按约每周3个集中开发日估算，不是已确认产能；教师、招募及适用研究流程尚未落实。

228题已离线复跑：Recall@1 11/208、严格单标签决策34/222、可接受决策34/228、OOD10/11、域内新Case7/7、异常0；输出 `results/case_benchmark_2026-10-01_plan.json`，benchmark/种子/matcher哈希不变，执行退出0不表示基线通过。未实施计划中的业务改动。下一轮只先做M0：临时库重启恢复与审核失败原子性，正式库写入前备份与来源核对。

## 联网检索修复（2026-10-01）

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


## M2/M3 工程验收与动态 HTML（2026-10-02，本段更新已有求根 WIP 状态）

已完成求根受控 AST/导数/区间 Oracle、12 家族、Case→反馈→修订、事务事件与 Overlay、显示 ACK、提示预算、服务器独立探针、作用域重放。入口是聊天“求根过程验证”；实现与版本/范围见 COURSE_GRAPH_M2_M3.md，工程 fixture/manifest 见 evaluation/root_diagnostic_*.json。自由文字与任意代码不自动当作数值轨迹，教师逐题复核仍待完成，不宣布完整 G3/M4 或学习效果通过。

动态 HTML 已按用户要求恢复到 teaching-v2.3/visual-v2：完成态闭合 html 围栏、点击才运行、独立 allow-scripts iframe、无同源/网络/eval、Canvas/DOM/动画、错误/停止/重启/30秒定时卸载；宿主 sanitizer 未放宽。30秒不是同步死循环的 CPU 强杀保证，生成 JS 不进入 Oracle。原 SSE error 被忽略的问题也已修复，401/超时/EOF 明确失败，失败或取消不开放部分回答预览。没有改模型凭证或调用真实模型。

验收：npm test 知识 JSON/API415/Web30；production build/typecheck；lint 0错误/10既有警告；12家族13/13三元组；10条生产图/SSE固定episode及工具异常、取消、事务、权限、重启、重复回执回归。浏览器主聊天表单及动态图示390px无横向溢出，暂停/频率/错误/停止/重启/超时门控实测；临时验收路由已删除。日志与截图 results/m2-m3-*，正式论文 gold/真人/远端CI结果不由这些本地结果替代。

后续优先 M4 教师与数值/容差独立审计，再按长期计划做未见任务和无AI延迟保持；新增学习体验规划保留为独立文档工作，不在本轮业务提交中打包。服务恢复3000/8000；commit/push以最终回执为准。

## 2026-10-03 登录体验补查

用户指出登录系统未同步更新。当前Git历史显示真实Web鉴权接入于2026-09-08，后端后来有课程权限维护；本次没有重写鉴权协议。已修复聊天退出只跳转不清凭证：清除token/owner/演示键，完整跳转以卸载owner相关页面状态，保留学习草稿；桌面/手机均可退出。注册移除不保存的院校/专业，称呼/账号区分，账号格式与服务端一致，补齐label/自动填充。登录/注册成功进入今日学习。鉴权布局加入Logo/主题/首页返回，删除无依据的SECURE CONNECTION标语。

本轮前端40项通过（新增退出清理回归）、生产build/类型检查通过，lint0错误/10既有警告；后端未改，本轮未重复API suite，上一轮API469是之前的证据。截图results/auth-login-updated.jpg。没有实际注册/登录真实账号、密码重置或远端验证；当前isolated demo API没有配置token secret，不能以演示界面验证真实签发。剩余：密码找回、邮箱验证、服务端token撤销/刷新、过期引导与跨标签页状态；注册在签发配置缺失时先创建用户的非原子流程也需后续修复。未commit/push/deploy，五小时额度约94%时只做收尾。

## 2026-10-03 分批提交准备

用户明确授权分批提交并推送，按四个边界：后端学习与教学规则、学习工作区与品牌形象、登录体验、规划及交接记录。提交前重跑npm test：知识JSON/API469/Web40全部通过；最新auth-followup生产build与类型检查通过，lint0错误/10既有警告，diff check通过。git grep sk-检查仅发现说明文字/普通标识符/既有二进制匹配，新增源码/规划未检出匹配的凭证格式。既有egg-info、demo-jiuzhang-hybrid.html、style-explorer.html、ui-proposals、ignored results/数据库/env不纳入。

首版后端包含learning_records表、课程持久库派生路径和tzdata依赖；COURSE_STORE_PATH显式优先，离线测试门控保留。当前分支feature/course-graph-2.0。远端fetch首次因GitHub443连接失败，当前remote-tracking ref不是实时远端证据；推送将在提交后单独尝试并报告，本文不提前宣称已推送。


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

本轮代码提交：A1 `5197ddf`；A2 `f7c865a`。文档回执另批提交；远端分支以最终推送核对为准。

### 2026-10-03 A3 与多领域扩展

用户授权 A3 → 线性方程组 → 数值积分。A3 已新增版本化 manifest 和独立离线 CLI，19 个合同 / 40 个实例通过首跑；缺失、跳过、失败、重复实例不能绿色。CI 增加该命令及报告 artifact。复用实际图 / SQLite / 工具 fixture，结果限定为离线协议。多领域模块待实现，A4/A5 未实现。

A3 全量复验：知识 JSON、API 563 / Web 43 均通过（results/a3-full-tests.log）；报告解析器另覆盖缺失 / 重复 / 跳过 / 失败。无模型调用或部署。

### 2026-10-03 多领域数值实验首版

A3 已实现，终止门控 / Guard 两次临时破坏均被 CLI 检出，源码已恢复。线性方程组（Jacobi / Gauss–Seidel）及积分（梯形 / Simpson / 自适应 Simpson）共用 numerical-lab-v1 请求 / 结果与既有 owner 学习记录，入口 /numerical-lab。支持预测、步进 / 播放、方法对照、历史 / 参数复用、数值核对；source hash 与幂等请求 ID，自检 / probe 未完成时阻止参考读取、运行及核对。无新依赖 / 迁移 / 学生代码执行 / 独立成绩更新。积分估计不是严格界，sin(16*pi*x)^2 提供采样遗漏反例。聊天入口仍是复制用户上下文，A4 可信任务快照与 A5 真实模型评测未完成。交付细节见 planning/agent-engineering-2026-10/delivery-a3-numerical.md。

最终全量：知识 JSON、API 583 / Web 45；生产 build / typecheck 通过，lint 0 错误 / 10 既有警告。新实验计入首页实验记录总数，保留 owner 隔离；无数学掌握度写入。隔离浏览器完成迭代 / 积分 / 参数复用 / 刷新 / 390px 与反例分段对照；截图 results/numerical-lab-desktop.jpg 不提交，演示 DB 与服务均保持隔离。
