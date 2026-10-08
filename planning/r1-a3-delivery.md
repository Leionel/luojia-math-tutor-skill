# R1-A A3：Jacobi / Gauss–Seidel 可信讨论切片（2026-10-08）

状态：用户在 A0–A2 后明确要求继续 A3；本片是本地工程实现与离线验证。R0 目标 SHA 的远端 CI、正式库备份/恢复、独立数学审核和真实模型质量仍分别待验。未调用付费模型、未部署、未写正式学生库。唯一当前状态以 [规划总索引](README.md) 为准。

## 行为与边界

- 沿用 U01 的 owner 范围 `linear_lab` 引用、同一 `TutorWorkflow`、Chat 消息与既有回执，不复制 Newton Agent，也不新增 Graph/Memory/IR。学生待评说法来自**本轮 Chat 用户消息**；运行前预测及保存轨迹仍是参考帮助，不能当独立作答。
- `resolve_learning_context` 对保存的线性任务重新运行现有 `linear_reference`，核对状态、充分条件、每步向量、残差、步差、理论误差界与成本字段；版本/轨迹不一致时在生成前拒绝。选中步骤的 `linear_check` 写明方法、复算向量、绝对残差、严格行对角占优是否成立、理论界是否存在及 unknown 原因。重新读取引用的现有流式检查继续覆盖权限或自检状态变化。
- Teacher 的既有 prompt 获得线性领域边界：Jacobi 与 GS 的分量更新顺序不同；正确的局部步骤不推出普遍收敛；小残差不等于同数值的小解误差；未证严格行对角占优是 unknown，不等于必然发散。Chat 引用卡向学生展示同样范围。固定计算是有限浮点证据，未把模型意见升为确定性判分，也未写 mastery。

## 验证与限制

- 定向 `tests/test_numerical_lab.py tests/test_learning_context.py`：33 passed，覆盖 Jacobi 第一步 `[1/4,2/3]`、GS `[1/4,7/12]`、残差与解误差反例、充分条件未知、跨 owner 与篡改/旧版本拒绝、prompt 原话隔离；这些是离线合同测试，不是模型数学准确率。
- 全量 `npm test`：知识 JSON、API **912 passed**、Web **72 passed**；`apps/web/npm run typecheck` 通过。开发服务器运行中，未执行 `next build`。
- 未做真人案例二审或真实模型对照；A0 的 L01–L04 仍是公开开发材料。UI 的 390px、键盘与真实聊天回复需 A5 集成验收。旧线性记录如不满足当前复算合同会提示重跑，避免把旧格式静默当作已核验。
- A0–A2 推送后的 [目标 SHA CI](https://github.com/Leionel/luojia-math-tutor-skill/actions/runs/37771507944) Web/知识通过、API 8 个 S5 哈希绑定测试失败：原 JSON 按 Windows CRLF 字节记 hash，而 Git checkout 为 LF。本轮附带最小跨平台修复：S5 JSON 固定 LF，并重绑内容/fixture 哈希；本地相关 80 项通过。修复版 CI 结果须以新 SHA 单独确认。

停止条件：若一个旧记录无法复算或学生消息缺矩阵/方法，保持引用不可用或追问，不把残差/模型推断升级为解误差或收敛证明。A4 Teach-back 与 A5 三域工程/质量 Gate 仍未完成。
