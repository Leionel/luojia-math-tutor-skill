# R5：现状与原型取舍

基线：`accd40d`，`feature/course-graph-2.0`。上一轮数学修复、正式文档和其他 R2 工作均未提交。本轮在 `.local/r5/preexisting-sha256.json` 冻结 566 个既有文件的摘要，原型和评测另建目录。以下是源码走查，不将源码存在视作真人验收。

## 当前功能矩阵

| 能力 | 当前状态 | 源码证据与缺口 |
| --- | --- | --- |
| Chat、教学决策、局部核验 | 已接入，有离线回归，缺真实质量证据 | tutor/graph、teaching_decision、step_checker；step-v2 与 delivery-v3 修复已在当前工作区 |
| Study、Reading | 已有真实领域视图与共享引用，但入口割裂 | study-domain-view、reading-domain-view 同时服务独立页面与 Canvas；名称不一致 |
| Newton 学习活动 | 已有预测、观察、解释、保存、讨论与独立任务 | lab-workspace 与 Newton activity；完整机制应复用，原型只调整呈现 |
| 线性/积分实验 | 已有运行、保存、逐步讨论与引用恢复，交互深度不同 | numerical-lab/page；与求根分成两个页面，Canvas 目前只有 root_lab 实验槽 |
| Assessment、Teach-back、Code | 已实现，缺统一任务进程呈现与真人评价 | 独立页面、领域服务、版本/帮助锁；代码静态审阅不能称执行 |
| Notebook、Mistake Book | 有服务与页面，回到任务的路径较旧 | 笔记固定 320px 列；错题练习链接使用 sessionId，而 Chat 读取 session，属于待复现的路径风险 |
| Course Graph、教师审核 | 有正式图、审核与来源机制 | LearningShell 将教师审核与学生任务平级；图谱作为学生辅助地图仍有独立价值 |
| 统一学习记录 | 尚无统一入口 | 各领域记录存在，不能据此再造一套存储 |
| 跨会话总结 | 服务/API 已有，学生入口不足 | 沿用上一轮源码核对，不将规划视作完成体验 |
| 数学教学优势 | 尚未证明 | R2/S5 fixture 是工程证据，真人 gold、受控真实模型对照和学习收益不足 |

`api.ts` 会把旧调用中的 demo-user 参数解析为当前账号，不能仅凭页面里的字面量认定跨账号泄露。ReferenceTutor 已验证来源并复用 TutorConversation；“需要手动复制全部上下文”并非整个系统的现状。

## 设计简报

- 使用者：正在学习数值分析、能阅读公式但不清楚结论适用范围的学生。
- 工作：围绕一个问题完成预测、观察、修订和独立检查，之后从错误继续。
- 现状：后端与共享引用已承担连续性，页面名称、入口和任务进程呈现不一致。
- 结果：任务、选中步骤、原判断及帮助状态始终可见，不要求重新说明问题。
- 成功信号：学生可完成 Newton 路径，从实验指定步骤提问，从错因回到来源；此处只记录原型交互完成，不推断学习收益。
- 对象与后果：操作仅改变本浏览器 `luojia-r5-prototype-v1` 演示空间，可重置；不读取账号、不写真实记录。
- 权限：所有原型入口公开可见，独立检验限制只用于演示产品状态，正式权限继续由现有服务端实现。
- 待选择：实验主导 B 作为实验中心默认；Chat 主导 A 保留给开放推理。正式产品调整等待用户选择。

## 信息架构与布局

自由对话是一级入口；首页允许直接提问、带材料来聊或继续学习任务。学习工作区承接完整教学过程；实验中心承接探索；记录中心聚合来源。小珞在普通对话、材料伴读和实验讨论中复用同一聊天能力，正式实现沿用既有会话服务。教师工作台从学生主任务中分层呈现，保留独立入口。

| 决定 | 原因 | 规则 |
| --- | --- | --- |
| 首页强调继续一项任务 | 现有六个平级卡片尚需学生自己组合路径 | rule/one-primary-action |
| 保留不同数学领域与 A/B 布局 | 讨论与逐步观察的注意中心不同；同一运行与选中步骤不变 | rule/preserve-mental-model |
| 普通对话不自动携带活跃实验 | 学生可以只聊概念、推导或学习思路，材料与实验由本人添加 | rule/name-object-scope-consequence |
| 材料选段固定到消息引用 | 换材料、修订文本或移除引用后，旧消息仍可回看当时原文 | rule/preserve-mental-model、rule/preserve-user-input |
| 记录按知识点聚合，底层存储不合并 | 已有领域服务，先改善查找与回到来源 | rule/smallest-intervention |
| 预测、修订草稿跨页保留 | 不把路由切换当作重做任务 | rule/preserve-user-input |
| 帮助影响独立完成标签 | 先展示后果，再查看参考；刷新不能恢复为独立 | rule/name-object-scope-consequence |
| 原型使用真实浏览器计算和明确的规则反馈 | 演示学习过程，不伪装模型或数学审核 | rule/cover-reachable-states |
| 键盘、窄屏和空状态可完成主要流程 | 输入有标签，导航用链接，动作使用按钮 | rule/keyboard-complete-flow、rule/navigation-vs-action |

视觉沿用纸白 `#faf7f2`、橄榄 `#617a55`、黛青 `#3d5a66`、朱砂 `#b45143`、墨色 `#22231e`。宋体承担标题、微软雅黑承担正文、Consolas 承担数值。主视觉是实际迭代轨迹和持续存在的“判断账页”，不增加成绩仪表盘。横向实验表与紧邻反馈构成主工作区，移动端转为顺序阅读。

## 三条路径对照

| 路径 | 当前实现与依赖 | 原型变化 | 后续正式工程 |
| --- | --- | --- | --- |
| Newton 学习 | StudyTask、Reading 引用、NewtonActivity、root probe；领域流程已有 | 同页进程连接条件、预测、观察、判断、修订和新题 | 复用现有 task/ref/帮助回执，增加协调层和返回位置；不另做算法 |
| GS 探索 | numerical-lab 保存运行与 step 引用；ReferenceTutor 已能同页讨论 | 选择步骤即显示参数、版本和同一记录的反馈；A/B 可切换 | 扩展 Canvas 的领域适配，统一运行历史与对照入口 |
| 错误回到学习 | mistakes、notes、阅读笔记与领域历史分散；pendingQuiz/sessionId 风险待复现 | 知识点时间线展示错误来源，直接回到任务或历史运行 | 先做只读聚合和规范深链；独立检验继续采用专用回执 |

无需新增业务能力的改进：统一称呼、区分学生与教师导航、展示现有引用、为来源提供稳定返回。需要工程改造的部分：任务级协调、记录聚合、数值实验的共享适配。原型未替换正式页面。三条路径的实际浏览器操作与结果见 [验收记录](acceptance.md#实际浏览器走查)。

## 源码入口

- 导航与工作区：[LearningShell](../../../apps/web/components/learning/learning-shell.tsx)、[CanvasWorkspace](../../../apps/web/components/learning/canvas-workspace.tsx)。
- 教材与任务：[StudyDomainView](../../../apps/web/components/learning/study-domain-view.tsx)、[ReadingDomainView](../../../apps/web/components/learning/reading-domain-view.tsx)。
- 实验与来源：[LabWorkspace](../../../apps/web/components/learning/lab-workspace.tsx)、[Numerical Lab](../../../apps/web/app/numerical-lab/page.tsx)、[ReferenceTutor](../../../apps/web/components/learning/reference-tutor.tsx)。
- 记录：[Notebook](../../../apps/web/app/notebook/page.tsx)、[Mistake Book](../../../apps/web/app/mistake-book/page.tsx)。
- 判断与证据：[TeachingDecision](../../../apps/api/app/tutor/teaching_decision.py)、[StepChecker](../../../apps/api/app/math_tools/step_checker.py)、[ProofTutor](../../../apps/api/app/tutor/proof_tutor.py)、[PolicyComparison](../../../apps/api/app/tutor/policy_comparison.py)。
