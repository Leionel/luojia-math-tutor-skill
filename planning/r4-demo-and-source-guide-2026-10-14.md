# R4｜真实闭环演示与源码讲解材料

这是 v4 §7 的展示交付准备，不是新一套产品路线。当前状态以 [planning/README.md](README.md) 为准。脚本与源码核对基线为 `97c8869` 及本轮评测工具工作区；本轮没有录制视频、运行真实模型或签署数学质量。讲稿只能描述当前可达能力，不填准确率、学生增益或自动证明成绩。

## 一句话与演示主线

“珞珈数智助教把数学工具的局部事实、学生原话和教学反馈放进同一个可回查的学习过程。”

主线只用真实 `/lab` 内置 Newton 活动：错误预测 → 逐步观察 → 保存解释 → Chat核对原话 → 修订与恢复。线性和讲回作为能力迁移的技术问答补充，不把六个工作区全部塞入两分钟。

## 录制前准备

- 用隔离账号与独立学生库/课程库；原活动不能覆盖，应换新隔离账号排练。记录录制时的SHA、源码dirty摘要、模型配置与来源版本，正式库不作录制素材。
- 先执行 `python scripts/r2_review_packet.py --check`；本轮 E1采集排练可运行 `python scripts/r2_application_capture.py --offline`。后者是固定模型的真实ASGI/SSE工程采集，无JWT、网页录像或模型质量成绩。
- 页面排练可以无模型；Chat反馈段必须来自实际获准运行，保留原始回答。缺模型时只录确定性观察和保存部分，明确“Agent反馈段待录”；不得用静态文案或配音替代一条未发生的模型回复。
- 浏览器不显示密钥、真实学生资料或完整环境文件。视频剪辑保持预测、点击、结果、修订的实际先后关系；不能把修订后的正确回答拼回原预测时间。

## 120秒屏幕与讲稿

| 时间 | 实际操作 | 建议口播与画面依据 |
|---|---|---|
| 0–15秒 | 打开 `/lab` 的Newton活动，展示 `f(x)=x³−2x+2, x₀=0`。 | “这次要判断的是这个初值的迭代行为。导数非零，够不够保证收敛？” |
| 15–30秒 | “我的预测”填“我猜会收敛”，理由填“迭代点处导数非零”，点击“保存预测”。 | “先保留学生的判断；此时界面只公开起点。” |
| 30–55秒 | “开始观察真实迭代”，逐次“揭示下一步切线与落点”，看到0→1→0。 | “服务端计算的每一步按观察进度揭示。这里f(0)=2、f′(0)=−2，所以到1；f(1)=1、f′(1)=1，又回到0。” 后续剩余步可加速剪辑，不能跳过操作后假称逐步看完。 |
| 55–75秒 | 观察完整后保存解释：“x₁=1是对的，所以任意初值都收敛。” 点击检查已保存解释的Chat链接。 | “这句话同时包含正确计算和错误推广。Chat引用的是保存版本，并携带固定题的精确代入证据。” |
| 75–95秒 | 展示实际Agent回答，引用卡、原run回链与“未核验/参考帮助”状态。 | 仅依据实际回答讲解；理想判据是承认一步更新、反驳任意初值保证、限定证据范围。若输出遗漏或误判，标为本次开发观察并保留，不能口播成已经通过。 |
| 95–115秒 | 回到原活动，保存修订：“这个函数与标准Newton更新从0出发往复；这一观察不能推广到任意初值。” 刷新。 | “修订另存一版，原预测保留。刷新后仍能回到同一个学习对象。” |
| 115–120秒 | 原预测、修订与状态同屏。 | “这里证明的是计算、来源和过程衔接；开放数学教学质量正在用独立审核与应用同题对照验证。” |

**可现在展示**：服务端参考计算、已揭示切线、预测/解释/修订保存、来源回链、参考帮助与独立学习证据的区别。**待真实运行后展示**：具体模型回答质量及D0/D1结果。**不在片中宣称**：通用自动证明、Agent自主实验设计、掌握度准确、教育收益。

## 三条源码链与面试追问

### 1. 学生原话、计算和披露是怎么分开的？

入口为 [newton-activity.tsx](../apps/web/components/learning/newton-activity.tsx)，经已有学习API调用 [NewtonActivity](../apps/api/app/tutor/newton_activity.py) 的 `predict → reveal → step → explain → revise`。`reveal` 复用 [run_reference](../apps/api/app/math_tools/root_runner.py)，服务端保存完整run；返回活动时只公开已揭示前缀。学生修改自己的解释时增加修订，不覆盖最初预测。

应能回答：为什么存完整run但只返回前缀？如何在刷新后保留revealed_step？同题通用Lab或历史引用暴露后，为什么只记帮助而不强制拦截一切探索？答案应限内置入口与规范化表达式，不能声称阻止手算或所有代数等价写法。

### 2. Agent的判断与确定数学事实谁负责？

[TutorOrchestrator.stream_reply](../apps/api/app/tutor/orchestrator.py) 调 [resolve_learning_context / _saved_newton_claim](../apps/api/app/tutor/learning_context.py)，按owner、run/hash、课程/runner版本、学生选中的request与revision重读。已保存原话作为 `student_claim`；`exact_check` 只支持固定题与初值。随后 [build_messages](../apps/api/app/tutor/prompt_builder.py) 把范围装入runtime context，现有编译工作流的 [teacher_node](../apps/api/app/tutor/graph.py) 生成教学表达，经Guard交付并保存metadata。

应能回答：精确0→1→0如何支持“这个初值往复”，为什么不能支持整段解释或“任意初值”？为什么引用反馈的 `verified=False/is_correct=None/mastery_delta=0`？Guard约束交付协议和明显越界，不能代替数学语义评分。Teach-back的原句跨度绑定也不等于其数学内容已证。

本轮 [`r2_application_capture.py`](../scripts/r2_application_capture.py) 在真实ASGI/SSE与工作流入口的实验harness中，仅在D0移除 `exact_check`；其他prompt、原话、轨迹一致，每臂重新建临时库。四个固定回复证明采集合同，没有真实模型质量分；不能把这种有轨迹的D0称为“裸LLM”。

### 3. Chat动作卡怎样避免把模型建议当已执行？

普通Newton参考讨论可由 [root_proposal](../apps/api/app/tutor/learning_actions.py) 提供服务器操作卡；学生填写参数，经 `LearningActions.preview` 复用固定 `run_reference` 预览，再由 `save` 显式保存与重新绑定。已选学生解释的讨论不提供这张参数卡，演示主线不强求出现。参考预览后填的观察保存为 `prediction_timing=after_preview`，不能包装成运行前独立预测。

应能回答：如何绑定owner/session/message/artifact/source，为什么旧preview不能覆盖新preview，如何幂等保存？当前卡片复制原参数并由学生调整；让Agent基于缺口选择对照实验是R3候选，尚未交付。线性与Teach-back复用工作流、保留领域检查，未新建场景专用Agent。

## 展示完成与下一步

材料已准备；实际视频、真实模型段和真人数学审核仍待完成。先亲自排练并能解释上面三条链，再录90–150秒视频、整理一份GitHub技术附录。R2结果如无增益应照实展示；R3只选一个可复现失败簇改进，当前不加新的Memory/Graph/证明框架。
