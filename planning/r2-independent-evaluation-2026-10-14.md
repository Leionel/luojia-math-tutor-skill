# R2 / R4 独立评测归档与 R3 决策（2026-10-14）

独立任务：**R2 独立评测与 R3 启动判断**，任务ID `01a13991-415a-7343-a7e3-4bd3cfe83832`。任务为新建上下文的只读评测，未参与本轮实现；审阅基线 `23aace8fb0e6756a1273a40dc9cc923828d4fda4`。以下归档独立任务的原始结论；它是第二份 AI 审阅，不能代替真人数学签署。主任务只增加本归档与状态索引，不实施 R3 或修改业务代码。当前状态以 [规划总索引](README.md) 为准。

---

# R2 / R4 独立只读评测

**结论：R2 已完成可信评测的工程准备，尚未完成数学与教学质量评价；R3 暂不启动。** 当前没有经过真人审核、在应用路径中可复现的模型失败簇。R4 的讲稿与源码讲解路径基本可信，但真实模型反馈段、完整页面录像和学生收益均未验收。

仓库为 `feature/course-graph-2.0`，HEAD `23aace8fb0e6756a1273a40dc9cc923828d4fda4`，本地领先远端 3 提交。派发时列出的修改、删除和未跟踪文件均仍在；我未修改业务、规划或配置文件。

## 核查结果

- **应用采集可达，但范围有限。** 我离线复跑 [采集脚本](D:/Projects/na-tutor/luojia-math-tutor-skill/scripts/r2_application_capture.py:91)，得到 N01/N02 各 D0/D1 一臂，共 2 对、4 次固定 Teacher 调用。每臂新建临时学生库、课程库和会话，请求经过进程内 ASGI `/api/tutor/stream`、SSE、编译工作流及消息保存；报告显示 HTTP 200、`done`、每臂一条用户消息、mastery/mistake 各 0。外连阻断覆盖该请求执行窗口。它使用合成 Principal、固定模型，并跳过本地检索；未验证 JWT、真实 provider、费用或完整网页路径。[路由](D:/Projects/na-tutor/luojia-math-tutor-skill/apps/api/app/api/routes_tutor.py:45)、[采集设置](D:/Projects/na-tutor/luojia-math-tutor-skill/scripts/r2_application_capture.py:103)。
- **Teacher 输入的单因素差分成立。** 产物中的两对完整消息经 [差分检查](D:/Projects/na-tutor/luojia-math-tutor-skill/scripts/r2_application_capture.py:33) 比较，均仅在 `learning_task.exact_check` 不同。不过 D0 仍有相同的数值轨迹、残差和“循环、尚未收敛”的诊断摘要；D1 增加的是固定题精确证据，并未触发模型工具调用。因此它只能作为“加入这段精确证据”的消融输入，不能代表裸 LLM 对整套 Tutor，也尚不能证明任何质量增益。[上下文装配](D:/Projects/na-tutor/luojia-math-tutor-skill/apps/api/app/tutor/learning_context.py:94)、[工具路径](D:/Projects/na-tutor/luojia-math-tutor-skill/apps/api/app/tutor/graph.py:763)。
- **材料绑定与分母陈述基本诚实。** `r2_review_packet.py --check` 通过：38 条是待审内容条目，不是独立试验；逐项材料及源文件 hash 有绑定。[审核包生成器](D:/Projects/na-tutor/luojia-math-tutor-skill/scripts/r2_review_packet.py:44)。既有 E0 产物记载 13/13 合同、20/20 实例；S5 离线产物为 **0/8 执行**，其 `report_complete=true` 只表示未运行报告完整。我读取了这些既有产物，没有重跑全量 JSON/API933/Web80，也没有验证远端 CI。
- **数学复算未发现 N01/N02 判据错误。** 对 \(f(x)=x^3-2x+2\)，\(f(0)=2,\ f'(0)=-2\)，故 \(x_1=1\)；\(f(1)=1,\ f'(1)=1\)，故 \(x_2=0\)。两点导数非零且都不是根，标准更新会重复 \(0\leftrightarrow1\)。这支持接受 N01 的**一步计算**、否定 N02 的**任意初值收敛**推广，却不支持“所有初值失败”或独立掌握度。[逐题判据](D:/Projects/na-tutor/luojia-math-tutor-skill/evaluation/r2/newton-pair-rubric-v1.json:1)。B2 的连续性、残差与根误差等条件卡，B3 六题参考答案，以及 S5 八道公开开发题的列示算术，未见新的明显数学反例；它们仍缺真人内容审核。B4-V01/V02 的残差停止只在 `fx=f(x)`、实际停止点位于 `[1,2]` 等前提下有 \(|x-\sqrt2|\leq |fx|/2\)；达到迭代上限不由此保证正确。V03 更新符号错，V04 的 `fx` 不是题设函数值。[变体笔记](D:/Projects/na-tutor/luojia-math-tutor-skill/evaluation/r2/b4-math-notes-v1.md:1)。

## 需要收紧的陈述

| 严重性 / 置信度 | 证据、影响与最小建议 |
|---|---|
| **P2 / 高** | [采集脚本](D:/Projects/na-tutor/luojia-math-tutor-skill/scripts/r2_application_capture.py:132)替换检索与模型，并用合成身份。复跑只证明该受控路径的输入、交付及持久化合同；不能据此称生产配置或真实模型端到端通过。保留现有快速离线合同，后续另采真实模型原始回答、阶段状态、请求/重试及 usage；代价是需先完成供应商与预算准入。 |
| **P2 / 高** | [E1 协议](D:/Projects/na-tutor/luojia-math-tutor-skill/evaluation/r2/e1-protocol-v1.md:9)要求逐阶段和成本记录，而当前 [采集产物构造](D:/Projects/na-tutor/luojia-math-tutor-skill/scripts/r2_application_capture.py:166)主要保存 Teacher 输入、固定回复摘要和边界布尔值；`provider_http_requests: 0` 是固定路径的设定值，尚非真实调用计量。它可做工程基线，不能直接升级为可评分的 live E1 运行器。最小做法是在获准运行前补实际响应、阶段、失败、请求和费用字段，并保留未评分状态；这会增加少量采集复杂度。 |
| **P3 / 高** | 文档中的“0学习写入”需限定为“**0 mastery/mistake 写入、0 独立成绩**”。采集为构造题目实际保存了预测、参考 run、揭示进度和解释；[NewtonActivity](D:/Projects/na-tutor/luojia-math-tutor-skill/apps/api/app/tutor/newton_activity.py:104)确实写 `learning_records`。这些写入只在每臂临时库内，不构成污染正式数据。修正文案即可。 |
| **P2 / 中高** | [R4 讲稿](D:/Projects/na-tutor/luojia-math-tutor-skill/planning/r4-demo-and-source-guide-2026-10-14.md:18)安排解释保存后进入 Chat；此时活动页面已可能显示固定题 [精确核对卡](D:/Projects/na-tutor/luojia-math-tutor-skill/apps/api/app/tutor/newton_activity.py:100)。录像可以证明学生看到证据、保存并修订，不能仅凭修订归因于 Agent 反馈。录制时明确卡片与 Agent 各提供了什么，保留真实先后操作及模型原答；要主张 Agent 的额外教学价值，须另做经审对照。 |

旧 [独立审阅](D:/Projects/na-tutor/luojia-math-tutor-skill/planning/r1-independent-quality-review-2026-10-12.md:24)中的 T04 过早判错和 B4 合法残差停止误导，仍是值得追查的**历史开发观察**。随后 [局部修正](D:/Projects/na-tutor/luojia-math-tutor-skill/planning/r1-quality-fixes-2026-10-12.md:10)已改提示和静态文案；旧 9 次直连公开合成题没有经过当前应用路径，不能倒推修正已生效，也不能当作当前 R3 失败簇。

## R4 与下一步决策

R4 三条源码链与当前实现相符：页面活动经 `predict → reveal → step → explain → revise` 保存过程；引用由 owner、run/hash 和版本重读后进入 Teacher；普通参考讨论的操作卡需学生填参数、预览并显式保存。[页面](D:/Projects/na-tutor/luojia-math-tutor-skill/apps/web/components/learning/newton-activity.tsx:101)、[引用解析](D:/Projects/na-tutor/luojia-math-tutor-skill/apps/api/app/tutor/learning_context.py:74)、[操作卡](D:/Projects/na-tutor/luojia-math-tutor-skill/apps/api/app/tutor/learning_actions.py:35)。第三条是面试补充链，**不是**这段“检查已保存解释”演示必然出现的按钮。当前可展示过程与来源衔接；视频、真实模型反馈和非开发者体验仍待实做。

按 [v4 的 R2→R3 Gate](D:/Projects/na-tutor/luojia-math-tutor-skill/luojia_roadmap_v4_2026-10-08.md:291)，**暂不启动 R3**。提示策略、错误归因应先看经审应用回答；“Agent 建议下一次对照实验”目前只有学生填写参数的卡片，缺它能解决的失败证据；Graph、Memory、BKT 或额外 Agent 角色均没有启动依据。若未来只允许一个 R3 切片，我选“**缺条件时先澄清、避免过早判错**”：触发条件是在当前应用路径中，经真人审核的 T04 及至少一个同类线性/讲回题反复出现确定性误判；验收用同组题改前/改后及一小组未参与调参题，分别核对 `unknown`、追问所缺字段、N01 正确步骤不误判、帮助披露和请求成本。没有该触发就不实施。

**现在最值得做的具体工作**是请真实数学审核者先签核 N01/N02 与 T04 等少量判据，同时用隔离账号排练并录下 R4 的确定性 Newton 页面段，记录实际按钮、刷新和回链断点；模型段等消费授权和采集字段齐备后再录。这样同时推进可评分的 E1 基准与可见的学生闭环，不把固定回复或 AI 复核冒充真人 gold。
