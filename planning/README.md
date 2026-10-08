# 项目规划总索引

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

## 当前推荐顺序

先U01线性引用，再U02教材选段/U03任务续接；U16图示降级按实际风险尽早安排。其余按完整计划的优先/接续/条件启动分组，**一次一个可验收结果**。真人/素材/授权/供应商/隔离缺失只停对应正式功能，不堵其它无硬依赖软件工作。

全部目标仍在六个月产品/研究主线，但全18项情景51–99开发日＋未计外部/C0成本，不能默认都在六个月交付；实际产能与需求决定条件项何时进入实施。不重复排已交付首版，不以AI生成速度代替验收。

## 文档维护

原目录、历史回执、07独立审阅与用户原runtime dirty保留；不搬迁或删除。现在做什么以完整升级计划/切片为准，工程与产品回执继续各自记录并链接。

业务代码尚未升级的条目不得改“已完成”；本地提交、推送、CI、部署、真实模型、教师gold和学习研究分别报告。实现偏离写complete-upgrade的implementation-notes，并同步三份项目交接记录。
