# R2.0–R2.4 可信评价首轮回执（2026-10-14）

唯一当前状态入口是 [`planning/README.md`](README.md)。本轮起点 `feature/course-graph-2.0` / `cc420724b0d35580796ed10bb2c4dbe8f6b62f9e`，按用户确认把 v4 的 R2/E0–E2 拆为 R2.0–R2.4；原 v4 文件没有这些细编号。本轮只扩评测材料、离线检查与 CI 测试入口，不改业务代码、模型配置、正式数据库或学生记录，也没有付费模型请求和部署。原有 `runtime-review-schedule.md` 修改、根目录三份文件删除及未跟踪原型均保留，未纳入本轮文件。

## 本轮完成与尚未完成

| 切片 | 本轮可核对的交付 | 当前不能宣称 |
|---|---|---|
| R2.0 证据基线 | [`evaluation/r2/README.md`](../evaluation/r2/README.md) 固定 E0/E1/E2、历史证据和分母边界；原 S5 离线运行结果 `results/r2-s5-offline-baseline.json` 显示 8道 dev **0/8执行**，独立 Fraction 只核对7项特定算术见证。 | `report_complete=true` 不是模型质量通过；7项算术检查不是8题开放回答正确率。 |
| R2.1 内容审核准备 | [`scripts/r2_review_packet.py`](../scripts/r2_review_packet.py) 从 R1/S5 内容和 B2/B3 源码字面量生成 [`38条未签署审核包`](../evaluation/r2/review-packet-v1.json)，源文件与逐项材料摘要绑定。B4 新增4个只读正反代码变体及[数学讨论笔记](../evaluation/r2/b4-math-notes-v1.md)；代码仅语法解析、不执行。源码或包被改动时 `--check` 拒绝。 | 无真人作者审核、独立二审、teacher gold 或盲测结果；公开变体数不能算误报率。B2 卡片还须连当前 Graph 原文人工核对。 |
| R2.2 E0 聚焦复验 | [`e0-contracts-v1.json`](../evaluation/r2/e0-contracts-v1.json) 使用既有运行器选 12个合同、固定19个实例，覆盖 D0/D1 输入绑定、Newton/线性、讲回、来源版本、B3/B4/B5 和包版本。本地 **12/12、19/19**，结果 `results/r2-e0-contracts.json`。CI Web 测试改调用根 `npm run test:web:ui`，与本地相同，补上此前 CI 漏列的 `learning-browser-storage.test.ts`。 | 这不是数学/教学质量或远端 CI 已通过；目标提交的 CI 尚待验收。 |
| R2.3 E1 Agent 对照 | [`e1-protocol-v1.md`](../evaluation/r2/e1-protocol-v1.md) 限定6道公开开发题、D0/D1 配对初态、逐阶段记录、人工评分项、unknown 与失败分母。 | 真人 gold 0、应用路径真实模型对照 0；计划的12个观察单元不是实际成绩。D2 未启动。 |
| R2.4 E2 任务体验 | [`e2-task-plan-v1.md`](../evaluation/r2/e2-task-plan-v1.md) 列5条 Chat↔Lab/教材/自检/代码任务及完成、剧透、来源、恢复、移动端和身份清理失败信号。 | 本轮真人0、新浏览器任务0；R1 历史局部浏览器证据不能换名成为这轮 E2。 |

## 为什么先做这些

R1-A/B 的工程回执已经有较多通过数，但内容仍未经真人审核，直连模型9条公开提示也没有经过本应用的路由、工具、引用和 UI。先把“待审核的是什么、跑过的是什么、分母是多少”固定住，才可能在后续对照中知道改进来自数学工具、来源上下文还是教学决策。R2.1 复用 S5 审核协议，R2.2 复用现有 `eval_agent_reliability.py`，没有引入另一个评分框架或新 Agent。CI 漏跑存储测试是实际发现的覆盖差异，统一命令后可由同一测试清单复验。

## 验证、依赖与停止条件

本轮已运行 `python scripts/r2_review_packet.py --check`、R2 E0 运行器和 S5 离线报告；审核包绑定的新增 `apps/api/tests/test_r2_review_packet.py` 定向 **2/2** 通过。根目录完整 `npm test`：知识 JSON、**API 930/930、Web 80/80**；Web typecheck 与生产构建通过，lint **0 错/10 个既有警告**。启动构建前检查 3000 端口无开发服务器监听；没有边运行 dev 边构建。`git diff --check` 退出0；远端 CI 仍需目标提交后验收。所有 pytest 均从 `apps/api`（或由根脚本切入）执行，离线门保持。若源文件内容改变，审核包必须版本化重建，旧评分不得移植。

R2.3 只有在真实数学作者审核与第二复核、应用路径采集器、供应商/usage/价格/重试预算预检及明确模型消费授权到位后启动。若无法保持同题同初态单因素对照，就报告“对照不成立”，不能把12计划单元硬凑为样本。R2.4 可先用隔离库和固定模型查交互，随后真人独立做任务；任何 owner 越界、帮助锁失效或私题串号会先重开 R1/R0 修复。R0 正式库备份/恢复、迁移和授权 Gate 未完成前仍不部署。
