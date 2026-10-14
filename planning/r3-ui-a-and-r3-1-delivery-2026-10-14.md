# R3.1 与 3A 首个切片交付

2026-10-14，用户要求“开做3A和r3.1，可以专业一点”，随后要求“先交付”。本轮交付 **UI-a：Chat＋Lab 共享会话、OpenUI 自有目录，以及 R3.1 证据驱动教学决策的本地工程版本**。当前状态入口仍为 [规划索引](README.md)。

## 可以使用的功能

- `/chat` 顶部打开实验工作区；桌面对话与实验并列，手机使用单一抽屉。`/lab` 保留独立入口，两处复用 `LabWorkspace`，Chat 内不挂第二个聊天输入框。
- 在工作区保存预测、观察真实轨迹、保存解释与修订；选中的已保存版本回到同一会话讨论。参数卡仍通过已有服务器接口预览、填写观察、保存新实验。
- 模型在原 Teacher 调用内同时产出教学动作、局部主张判断、已知/缺失条件、证据引用和简短理由；没有新增规划模型调用。支持确认局部步骤、纠正主张、补齐条件、建议实验、讲解及提出针对性练习。
- OpenUI 目录首版包含来源摘录、条件核对、预测输入、参数对照与真实轨迹图。模型选择组件及引用，服务器验证后编译为 OpenUI Lang；数值和可执行操作来自服务器记录。
- 回答正文始终独立可读。无效决策或组件、来源不匹配、回答修复、未完成交付均降级；声明的输入预算不足时保留旧教学流程，不提高预算上限。

## 接线与维护入口

| 层 | 入口 | 责任 |
|---|---|---|
| 决策合同 | `apps/api/app/tutor/teaching_decision.py` | 严格模型字段、引用检查、来源哈希、动作/披露一致性、UI 选择与编译 |
| 工作流 | `graph.py` / `prompt_builder.py` / `orchestrator.py` | 同一次生成、Guard、持久化后交付独立 `intelligent_ui` SSE 事件及历史元数据 |
| 组件目录 | `protocol/intelligent-ui-catalog.json` / `intelligent-ui-prompt.txt` | 版本 `learning-ui-v1`，SDK `@openuidev/react-lang@1.0.0`；生成提示词及 SDK 格式检查 |
| 会话控制 | `apps/web/lib/tutor-conversation-controller.ts` | 主 Chat 和嵌入对话复用创建会话、历史、SSE 与交付租约；来源视图切换不取消发送 |
| 工作区 | `apps/web/components/learning/lab-workspace.tsx` | 同一领域视图在独立路由和 Chat 面板使用；保存后重新读取来源版本 |
| 渲染 | `apps/web/components/learning/intelligent-ui.tsx` / `lib/intelligent-ui.ts` | 自有 React 组件、严格语言匹配、消息与来源绑定、固定应用回调 |

`TEACHING_DECISION_ENABLED` 默认开启；设置为 `false` 可回退原 Teacher 流程。R2 固定应用采集器显式关闭它，保留旧对照的单因素范围。模型判断始终标为 `model_opinion`，不会据此提升 `verified`、正确性或掌握度。

本轮顺带修复了懒创建会话的父组件回传取消流、React Strict Mode 初始加载、引用选择异步竞争、带来源 URL 忽略已有会话 ID，以及旧参数卡匹配活动修订范围的问题。历史消息继续使用当时保存的来源快照。

## 已完成的验证

| 验证 | 结果 | 本地回执 |
|---|---|---|
| `npm test` | 知识 JSON、API **971** 项、当时 Web **86** 项通过 | `results/r3-implementation-20261014-195938/full-tests-final.log` |
| 最终 Web 测试 | **88/88**；增加目录一致性与来源显示合同 | `web-tests-final.log` |
| 最终 API 定向回归 | **29/29**；教学决策、ASGI 持久化及教学动作显示 | `api-final-targeted.log` |
| TypeScript | 通过 | `typecheck-final.log` |
| ESLint | 0 错误，10 条既有警告 | `lint-final.log` |
| 最终生产构建 | 通过；隔离 `.next-r3-check`，未在原 dev 的 `.next` 内构建 | `build-final.log` |
| Playwright 移动端 | 390px 无页面横溢；开关工作区不中断生成；Escape 关闭；停止生成显示未完成；两次请求属于同一会话 | `browser-checks-final.log` |
| Playwright 桌面 | Chat＋Lab 并列；连续刷新两次保留会话和工作区 | `desktop-checks.log` |

日志简称均位于上述 `results/r3-implementation-20261014-195938/`。另有真实浏览器操作：参数预览→保存新实验→刷新；预测→主动查看完整轨迹→保存解释→保存修订→同会话讨论。原预测、解释、修订分别保存；主动查看答案明确记录为帮助曝光。

截图：[桌面 Chat＋Lab](../output/playwright/r3-desktop-chat-lab.png)、[390px 修订抽屉与键盘焦点](../output/playwright/r3-mobile-workspace.png)。截图使用固定模型回复和真实受控计算轨迹，**不是数学质量评测或真人学习效果证据**。

## 交付范围和接续

- 已交付本地工程代码和验证。当前 3A 完成 UI-a，UI-b Reading/Study 与 UI-c Code 的面板整合尚未实施；R3.2 的目的驱动实验建议仍是下一片。
- 本轮实际供应商模型调用 0；模型格式遵循率、N01/N02/T04 等题的真实质量增益需另行预算化复验。原真人 gold、正式 E1/E2 与 R0 上线状态未升级。
- 未提交、推送或部署。原工作区已有修改、删除文件和并行新增规划保留；验收使用独立双库与 3100/8101 临时服务，不修改正式数据或 `.env`。
- 当前 8000 服务是原有进程；重启后端后才加载 R3.1。前端依赖已安装；正常开发入口仍为 `npm run dev:api`、`npm run dev:web`。

复现浏览器夹具：`python scripts/r3_ui_fixture.py --data-dir results/r3-ui-fixture --port 8101`。它只监听回环地址，使用独立数据库和固定回复；前端可用 `LUOJIA_NEXT_DIST_DIR=.next-r3-preview` 与 `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8101` 启动隔离实例。生成目录后运行 `npm run generate:ui-catalog`；CI 检查目录提示词是否过期。

SDK 接法参考 [OpenUI 自定义组件官方文档](https://www.openui.com/docs/openui-lang/defining-components)。

收尾：隔离验收服务已停止；原 `next-env.d.ts` dirty 字节已恢复，临时构建追加的 tsconfig 路径已清理。本轮涉及的 tracked 文件差异检查通过。另一个工作轮次正在修改 `learning-shell.tsx`，其尾随空格原样保留；未将全工作区差异检查报告为通过。
