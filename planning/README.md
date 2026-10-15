# 项目规划总索引

## 当前状态（2026-10-15；唯一状态入口）

最新收尾：[Reading / Study 与教师入口修复、固定 worker 冷启动优化](r3-domain-worker-closeout-2026-10-15.md)。共享 Reading/Study 已接入真实领域数据；修复普通 Reading 引用 409、Study 完整操作丢失、引用竞争和刷新恢复。数学核验预算与质量边界保持；R3.2 与 Code 工作区仍是后续项。下面的旧交付为历史快照。

最新交付：用户要求开做并随后要求先交付，已完成 [R3.1＋3A UI-a 首版](r3-ui-a-and-r3-1-delivery-2026-10-14.md)：Chat＋Lab 共享会话与领域视图、OpenUI 1.0.0 目录、单调用证据驱动教学决策、真实参数预览与版本修订接续。根JSON/API971通过，最终Web88、API定向29、类型/构建通过，lint零错误；隔离Playwright覆盖桌面、390px、刷新、键盘、不中断生成与停止。固定回复只证明工程合同，供应商调用0，数学质量增益未评分。UI-b/c、R3.2与视觉重塑按下方既有规划接续；未commit/push/deploy。以下R2回执和规划决定记录此前状态，“尚未实施”不再描述本轮已交付的UI-a/R3.1。

最新复核：[T04真实ASGI/Chat工作流](r2-t04-application-recheck-2026-10-14.md)在修正采集器压缩转交问题后，routing→Teacher→Guard→保存完成；实际回答先询问指标、方法、函数与初值，verified=false/is_correct=null/mastery_delta=0。Guard无修复，不把结果归功于数学核验。首次harness错误与修正后共3次provider请求，usage部分未知。根JSON/API951/Web80通过，38条绑定check通过。该单次结果不支持以T04失败为由新增修复；复核实际回答和正确步骤负对照继续进行，不追加本轮模型消费。用户授权纳入的新能力/UI开发规划按下段推进，尚未实施。

最新规划决定：用户确认将intelligent UI与Chat/学习页面统一加入现有路线。[v4 §6](../luojia_roadmap_v4_2026-10-08.md)与[R3执行细化](r3-agent-capabilities-2026-10-14.md)采用“R2基线→R3有界开发→单因素复验”；UI-a共享Chat＋Lab、OpenUI自有组件目录与教学决策/实验建议一起形成近期核心，随后UI-b统一Reading/Study、UI-c统一Code。六大工作区的视觉提升与统一规范见补充文档[学习工作区视觉重塑与统一规范](r3-workspace-ui-design-and-unification-2026-10-14.md)。目标检索/策略优化接续；本次只改规划，功能/SDK均尚未实施，模型消费范围不自动扩大。

最新审核反馈：[三题判据的用户认可“通过”](../evaluation/r2/math-review-user-acceptance-2026-10-14.md)已按材料SHA登记，覆盖N01/N02/T04核对材料的整体认可。正式逐项签署、独立二审与模型评分仍待完成；T04直接smoke风险保留历史，当前应用单次回答见上方复核，不能混为同一次观察或评分。

| 状态 | 内容与依据 |
|---|---|
| **最新接续** | [两项推进与授权在线诊断](r2-two-tracks-and-live-smoke-2026-10-14.md)：[三题人工核对材料](../evaluation/r2/math-review-three-cases-2026-10-14.md)已就绪、逐题签署待确认；实际适配器的Mock预算准入已验证，live生产接线仍未启用。用户授权deepseek-flash在线诊断3题，完整返回、714 token；另有一次4-token连接检查。T04有待真人复核的条件/收敛概念风险。最终根JSON/API949/Web80通过。直接适配器smoke不是完整应用对照，正式质量评分仍0。R3有界开发已纳入近期计划，尚未实施。 |
| **本轮接续** | [回答采集v2与live准入审查](r2-capture-and-live-admission-2026-10-14.md)：补保存正文、SSE阶段、固定调用回执和外连拒绝记录；2对/4条离线采集通过，定向43/43、根JSON/API934/Web80通过。真实供应商传输/费用上界仍未实现，模型质量评分仍0。下一步少量数学签核与实际适配器的模拟预发送准入，再按具体预算授权真实试跑。 |
| **此前基线** | [R2接续回执](r2-evaluation-delivery-2026-10-14.md)：N01/N02真实ASGI/SSE离线应用采集2对/4条固定回复，全Teacher输入只差exact_check，质量分0、真人gold0；线性/讲回公平对照待建立。R2 E0追加后13/13合同、20/20实例，根JSON/API933/Web80通过。R2.4仍为2条局部桌面路径、真人0。[R4演示与源码材料](r4-demo-and-source-guide-2026-10-14.md)已准备，视频/真实模型段未录。当前本地提交未推送，远端CI待验；R1质量与R0上线Gate未过。 |
| **Now** | **UI-a＋R3.1工程首版已交付**，见[交付回执](r3-ui-a-and-r3-1-delivery-2026-10-14.md)，真实模型效果待复验。 |
| **Next** | **R3.2主动对照实验＋UI-b/c及现有视觉统一规划**：消息内模型组合交互卡，展开同一Lab预测/观察/修订，再回同会话；首个完整成果粗估9–14集中开发日。UI-b Reading/Study、UI-c Code随后统一，R3.3目标检索/R3.4策略优化接续，全部能力＋UI粗估17–27日，见[R3细化](r3-agent-capabilities-2026-10-14.md)。保留直接页面和历史版本，开发不等38条全签署；主链用应用对照验收，live另按具体预算授权。E2/R4随真实闭环推进。 |
| **Delivered** | [A0–A2](r1-a0-a2-delivery.md)、[A3 线性切片](r1-a3-delivery.md)、[A4–A5 本地工程](r1-a4-a5-delivery.md)、[B1–B2 本地首版](r1-b1-b2-delivery.md)、[B3–B4 本地开发切片](r1-b3-b4-delivery.md)、[B5 本地集成回归](r1-b5-delivery.md)与[隔离浏览器补验](r1-b5-browser-followup-2026-10-12.md)，以及 [9 次公开合成题真实模型观察与独立子 agent 审阅](r1-independent-quality-review-2026-10-12.md)。B3/B4 的 [CI #38194030159](https://github.com/Leionel/luojia-math-tutor-skill/actions/runs/38194030159)、B5 的 [CI #38224685431](https://github.com/Leionel/luojia-math-tutor-skill/actions/runs/38224685431)、审阅文档的 [CI #38227839910](https://github.com/Leionel/luojia-math-tutor-skill/actions/runs/38227839910) 已通过。此前 M1/U 系列仍按各自回执。 |
| **Blocked** | [v4 的 R0→R1 Gate](../luojia_roadmap_v4_2026-10-08.md)的正式库与授权链尚未独立验收；本地评测准备不解除上线门槛。R2 内容包38条无人签署；S5 8题离线基线执行0，E1应用模型对照与E2真人观察均0。2条局部桌面路径缺Chat/移动端/键盘/跨标签项。R1-A质量、B2/B3/B4内容与R0仍待证据。自检单题答案没有直连Chat可信引用；认证令牌持久存储另属R0风险。 |
| **Conditional** | R3.5任务记忆与一条长流程恢复按真实中断需求进入；F2精确PDF区域、F8代码沙箱、U18线性独立训练、长期Memory整理/Reasoning Graph/BKT重写按命名需求与证据决定。轻量Claim/Condition/Evidence绑定随R3.1推进，现有Course Graph目标检索进入R3.3；**F1/F2/F4/F8的最小增强已在R1-B交付**。 |

2026-10-14收到一次[用户整体审核反馈“通过”](../evaluation/r2/user-review-2026-10-14.md)，范围为N01/N02判据、页面流程与口径清单。没有逐项评分或操作记录，未升级真人gold、完整E2或模型质量Gate；上表的0仍指有完整记录的正式观察/评分数。

下面保留按日期形成的旧计划和交付索引；其中“下一步”及测试数只表示当时状态，以本表和链接回执核对现在进度。[独立评测](r2-independent-evaluation-2026-10-14.md)原“暂不启动R3”结论不改写；2026-10-14用户的新规划决定更新开发启动方式，历史报告不充作当前执行指令。

M1 Prompt B 的 Newton 参与式活动与实验台界面见 [本轮回执](m1-newton-delivery.md)；Prompt A 安全收口与待核实边界见 [G0 回执](m1-g0-delivery.md)；此前按日期叠加的简要状态见 [交付与规划快照](delivery-history-2026-10.md)。

最终检查：API899、Web最终71、生产构建通过；引用缓存缺失会话已加校验。U01–U06/U16首版、U08临时库已交付；接续重点是U07人工复核与U08正式备份/恢复gate，U09可另做合成名单简报；其余条件片不自动启用。下文保留原规划时顺序。

> 最新：[U08可撤销登录会话](complete-upgrade-2026-10/delivery-u08.md)与U16静态降级已接续实现。API899/Web70及增量11/19通过。**正式启动前先验收数据库备份/恢复；migration7会在Repository初始化时应用，旧v1需重新登录。** 当前网页仅隔离演示，不是正式库上线回执。

当前追加：[U16静态降级](complete-upgrade-2026-10/delivery-u16.md)已交付，任意模型脚本保持关闭；下一片先U08临时库开发。

> 接续交付：[U04–U06](complete-upgrade-2026-10/delivery-u04-u06.md)已完成积分引用、代码静态提示讨论与讲回证据定位首版，API880/Web65及增量14/33通过。正式经审判断与真实模型质量仍pending；原规划/回执保留历史状态。

当前交付：[U01–U03 首版](complete-upgrade-2026-10/delivery-u01-u03.md)已实现线性实验同页引用、教材选段 Chat、只读任务续接。API847/Web64、增量13合同28实例和原E0 38合同92实例通过；实际网页使用临时库与固定模型验收。接续候选 U04/U05/U16，真人质量与条件阶段仍 pending。下文保留规划时基线。

更新：2026-10-07（Asia/Hong_Kong）。**当前完整升级方案见[完整升级计划](complete-upgrade-2026-10/README.md)**：18个可单独验收的本地切片，保留F1–F8与Agent全部后续目标。本轮用户选择先计划，不实施功能。

## 当前交付与规划的关系

A0–A3、S1–S4、S5.0、S5.1/S5.2离线首版和S5.3Mock预算切片已有交付与5批本地提交。S5.2真人作者审核/二审/真实质量评分、封存确认与S5.3供应商准入/live仍pending。F1–F4/F5文字/F8静态首版可用，不等于全部扩展完成。

| 目录 | 职责 | 当前怎么用 |
|---|---|---|
| [learning-experience-2026-10](learning-experience-2026-10/README.md) | 六个月产品体验、F1–F8、内容与学习研究 | 保留原目标与功能首版回执，不重做已交付功能 |
| [agent-engineering-2026-10](agent-engineering-2026-10/plan.md) | Agent设计与A/S历史交付 | 保留runtime/trace/tool/上下文决策与历史证明 |
| [agent-v3-2026-10](agent-v3-2026-10/04-roadmap.md) | S5具体合同、材料与工程回执 | 已交付与真人/live未完成项的事实来源 |
| [complete-upgrade-2026-10](complete-upgrade-2026-10/README.md) | “还需要补什么”的共同实施规划 | 当前优先级、18个切片、依赖、验收/STOP与预算；不自动派发执行 |

## 现阶段状态与升级映射

| 任务 | 已有交付范围 | 补充升级 | 切片 |
|---|---|---|---|
| F1今日学习/复习 | 15/30分钟、恢复、反馈确认、Newton训练/probe | Chat任务续接、跨领域任务族；后续45分钟/章节组合 | U03/U18 |
| F2教材伴读 | 摘录/Markdown选段、来源/条件卡、笔记 | 可信选段Chat、实际PDF页/区域；不编造页码 | U02/U10 |
| F3数值实验 | 求根三方法、线性/积分实验、Newton可信Chat/预览保存 | linear/integration只读Chat；后续单域写动作、阻尼/工作量/误差说明 | U01/U04＋扩展清单 |
| F4章节自检 | 6道开发参考题、恢复/交卷/解析 | 版本化rubric与审核、新题组、独立研究材料另验收 | U07 |
| F5讲回 | 原句/条件对照/补充版本 | 逐项有来源反馈、真实评价；语音有条件扩展 | U06 |
| F6视频 | 普通推荐 | 真实字幕/时间点伴学；无字幕不伪造 | U11 |
| F7教师 | 仍为计划 | 授权名单简报、证据回查/脱敏导出；后续布置经审任务 | U09 |
| F8代码 | Newton静态审阅/版本/手动轨迹 | 静态规则版本/Chat、真正C0、限定C1；新库/Notebook另验收 | U05/U13/U14 |
| A4/A6跨工作区 | Newton已接，普通固定工具已交付 | 选实验/原文/任务/代码/讲回对象连续性；不重建Registry | U01–U06 |
| A5/S5质量 | 工程E0、公开材料、固定模型流程 | 真人复核/封存、明确批准的小smoke，状态与数学内容分开 | U07/U12及既有S5审核协议 |
| A7/S4计量 | call/span/usage、可选价格；S5.3Mock预留 | 实际费用上界、供应商准入与live transport | U12 |
| A8恢复 | 未启动；trace是回执 | 真实需求后单路径恢复，幂等/未知副作用/预算重验 | U15 |
| 账号与图示 | 登录界面和静/动态图已有 | 签发失败/真实退出、身份找回、同步JS不能安全运行时降级 | U08/U17/U16 |

状态依据：[F1–F4](learning-experience-2026-10/f1-f4-delivery.md)、[F5/F8首页](learning-experience-2026-10/home-f5-f8-delivery.md)、[流程加强](learning-experience-2026-10/xiaoluo-chat-lab-review.md)、[A0–A2](agent-engineering-2026-10/delivery-a0-a2.md)、[A3](agent-engineering-2026-10/delivery-a3-numerical.md)、[S1/S2](agent-engineering-2026-10/delivery-s1-s2.md)、[S3/S4](agent-engineering-2026-10/delivery-s3-s4.md)、[S5.0](agent-v3-2026-10/09-delivery-s5-0.md)、[S5.1](agent-v3-2026-10/10-delivery-s5-1.md)、[S5.2](agent-v3-2026-10/12-delivery-s5-2.md)、[S5.3与分批提交](agent-v3-2026-10/13-delivery-s5-3-offline-and-commits.md)。历史测试数量只证明各轮范围。

## 旧切片推荐顺序（实施前规划快照）

先U01线性引用，再U02教材选段/U03任务续接；U16图示降级按实际风险尽早安排。其余按完整计划的优先/接续/条件启动分组，**一次一个可验收结果**。真人/素材/授权/供应商/隔离缺失只停对应正式功能，不堵其它无硬依赖软件工作。

全部目标仍在六个月产品/研究主线，但全18项情景51–99开发日＋未计外部/C0成本，不能默认都在六个月交付；实际产能与需求决定条件项何时进入实施。不重复排已交付首版，不以AI生成速度代替验收。

## 文档维护

原目录、历史回执、07独立审阅与用户原runtime dirty保留；不搬迁或删除。现在做什么以完整升级计划/切片为准，工程与产品回执继续各自记录并链接。

业务代码尚未升级的条目不得改“已完成”；本地提交、推送、CI、部署、真实模型、教师gold和学习研究分别报告。实现偏离写complete-upgrade的implementation-notes，并同步三份项目交接记录。
