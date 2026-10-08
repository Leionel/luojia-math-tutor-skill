# R1-A A0–A2 本地工程回执（2026-10-08）

基线：`feature/course-graph-2.0` / `da67dd54abd910bca7219b9ed398807c3764cbf5`，本轮改动未提交。用户在规划冻结后明确要求启动 A0–A2；这是在 R0 目标 SHA 远端 CI 尚未验收时进行的**本地开发与离线验证**，不是 R0 Gate、R1-A A5 工程 Gate 或数学/教学质量 Gate 的通过回执。未访问正式学生库、未调用付费模型、未部署。原有未提交修改、删除及原型文件保留。

## A0：公开开发基线

新增 [`evaluation/r1/a0-development-cases.json`](../evaluation/r1/a0-development-cases.json)：Newton、Jacobi/GS、Teach-back、工作流/权限各 4 例，共 16 个公开开发案例。SHA256 `868005e021327e4690b027afb1096f7f624159db7ed46a27051f5fde25fde42b`。案例逐项列学生主张、独立算术/逻辑依据和应有边界；没有真人二审、封存确认集或真实模型答案。另有[评测边界说明](../evaluation/r1/README.md)。用 Python `Fraction` 独立复算了 `0→1→0`、`x₀=-2→-9/5`、Jacobi `[1/4,2/3]` 与 GS `[1/4,7/12]`；这只检查种子的确定性算术，不构成外部人工审核。

## A1：只读可信原话进入 Chat

在现有 `root_lab` 引用上加可选 `activity_claim`，定位学生**明确选择**的解释或某次修订。服务器按当前 principal 重读活动记录和 lab run，核对活动版本、request ID、修订计数、run/input hash、runner/graph 版本与帮助锁；浏览器不能提交原话或证据字段。普通“解释第 k 步”仍只带轨迹，不附历史学生主张。旧修订、跨 owner、错 hash 或被锁帮助在进入模型前拒绝。回复 metadata 中主张仍为 `unreviewed`，`verified=false`、`is_correct=null`、`mastery_delta=0`；本轮不发参数预览卡，也不写 mastery/mistake。

Newton 活动给已保存解释/修订增加“请小珞检查”入口，完整 Chat 显示被选中的原话，返回 `/lab#newton-activity` 回看原活动；独立的会话缓存键避免与普通轨迹问答混用。每次 Chat 请求及恢复均重新核对来源。A5 的曲线/切线、防剧透步进与 390px 浏览器验收**尚未实施**，不能由本轮链接和类型检查推定完成。

## A2：D1 暂行，质量对照待证

同一原话/轨迹在离线测试中形成 D0（无固定题精确代入）与 D1（附 M1 已有 `EXACT_CHECK`）两份 prompt，测试确认除了该有界数学证据之外，主张、轨迹和意图一致。生产路径暂用 D1：复用已保存 Root Runner 与本题 `x₀=0` 精确代入，经现有 Teacher/Guard 组织反馈，不新增 Agent、任意工具调用或自动评分。D2 不接生产路径；字段合同和质量优劣待审核与真实模型证据。对照边界见[工程比较](../evaluation/r1/a2-engineering-comparison.md)。16 例未执行真实模型，故没有数学准确率、误判率、端到端延迟分布或费用结论。

## 验证与未过 Gate

- `npm test`：知识 JSON 校验通过，API **907 passed**，Web **72 passed**；脚本从 `apps/api` 执行离线 pytest。
- `apps/web/npm run typecheck` 通过；lint 0 error、10 条既有 warning。定向 `test_learning_context.py`/`test_newton_activity.py` 共 10 passed。`git diff --check` 已检查本轮代码。
- 开发服务器仍监听 3000，遵守 `AGENTS.md`，本轮未执行 `next build`；未在正式库或现有页面进行账号操作。UI 浏览器 E2E、并发身份变更、移动端与实际模型回答质量仍 pending。
- [GitHub CI #24](https://github.com/Leionel/luojia-math-tutor-skill/actions/runs/37730488523) 是旧远端 SHA `50e5c16` 的失败记录；本地测试通过不替代目标 SHA 的远端 CI。R0 Gate 与正式库备份/恢复验收仍未完成。

下一步不自动启动 A3。应先审阅本回执和 R0 状态；若继续 A 阶段，按冻结规划处理 Jacobi/GS 的领域证据与共用回执。质量 Gate 需要独立数学审核和获准真实模型运行，D1 只是本地暂行工程选择。
