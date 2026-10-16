# 3A 统一实现复核与 R3.1 提交收尾

## 范围

复核另一个 agent 已提交的 `8edd92e` 多工作区画布，以及当前共享工作区样式；本轮提交剩余 R3.1 教学决策、OpenUI 合同、共享对话控制器和离线测试。保留无关 R2 材料、原文件删除及视觉探索产物，不推送、不部署。

## 结论

用户补充的另一 agent 完整执行记录已核对：六个独立页面的字体、标题和共用样式重塑，Lab 配置台/蓝图、Intelligent UI 卡片、可调宽度、桌面分栏和移动抽屉均已落地并存在对应提交；不是仍停留在规划。Lab 复用真实 `LabWorkspace`。以下缺口限定为画布的业务数据与来源统一：Reading / Study 目前是新增的静态示例，Code 尚未进入画布。独立 Reading / Study 原有真实功能仍存在。

### 待修问题

1. **P1：示例冒充教材原文。** `canvas-workspace.tsx` 的 `readingChapters` 是硬编码文本，却显示教材章节与“定理原文陈述”。没有真实 reading unit/document、source hash 或选段绑定；二分法“对初值完全鲁棒，不存在发散或奇异风险”的绝对陈述也超出已列条件。应复用真实 Reading 领域视图及已有数学渲染，移除未核对的原文标注。当前 `/reading` 识别 `unit`，画布却用 `chapter` 链接，不能定位所选内容。
2. **P1：跨工作区提问仍携带旧来源。** Reading/Study 的 `onAskTutor` 直接调用 Chat `submit`，请求沿用 `learningContext.ref`。此前选过 Lab 时，教材问题可能仍按旧 root_lab 解释，且用户看见的是另一个工作区。应先绑定真实领域引用，再提问；示例讨论应明确选择普通讨论并呈现来源变化，不能静默串用旧实验。
3. **P2：今日任务不是已有计划。** `studyTasks` 是固定三个例题，没有读取 `/study` 的真实任务、完成状态和版本；切换 tab 还会卸载 LabWorkspace。应抽取共享 Study View，并明确保存/恢复各工作区草稿和已选对象。

### 已修

打开 Reading/Study 时携带 root_lab 引用，会在异步引用检查后把 URL 强制写为 `workspace=lab`，刷新恢复错误工作区。现先写用户所选 tab，检查完成后保留最新可见 workspace；期间关闭面板不会重新写入 workspace。修改仅涉及工作区 URL 与现有引用检查，不扩大模型或工具权限。

## 验证

当前全量 `npm test` 通过（API 971 / Web 88、知识 JSON 与目录合同）；`tsc --noEmit` 通过，lint 0 错误 / 10 既有警告，暂存差异检查通过。首次 `next typegen` 遇到 tsconfig 文件读取 UNKNOWN 错误，未计为成功；直接 TypeScript 检查随后通过。源码复核及本轮离线验证日志保存在 `results/r3-commit-review/`。上轮生产构建与浏览器闭环证据见 [UI-a / R3.1 交付回执](r3-ui-a-and-r3-1-delivery-2026-10-14.md)；它们早于另一个 agent 的最新画布提交，不作为最新三 tab 全流程验收。
