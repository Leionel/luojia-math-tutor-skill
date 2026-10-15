# Reading / Study 统一后复核修复（2026-10-15）

后续状态见 [worker 与 CI 收尾](r3-domain-worker-closeout-2026-10-15.md)：原失败记录保留在本页，最新全量已通过。

基线 `93aa00d`。保留六页新样式与共享领域视图，修复本轮接线回归；没有修改正式数据、模型密钥或后端数学核验预算。其它工作轮次的 dirty 和删除保留。

## 已修

- **P1 普通 Reading 讨论总是 409**：新画布把 `condition_hash` 加入普通来源引用；后端将其判为条件卡对照，要求题目原话。现在共享 `readingSourceRef` 只生成来源定位，不授予条件对照语义；Unicode 字符跨度、课程/上传章节和 6000 字符上限明确校验。浏览器已实际绑定和发出 reading 请求。
- **P1 Study 完整流程被抽取丢失**：恢复原完整页面的计划创建、开始/续接任务、阅读留痕、提交轨迹、反馈确认与独立检验入口，恢复正确 `/study/plans` 接口、旧草稿/停机依据恢复、到期复习与此前任务。保留新的画布看板。移除会向独立作答注入预设答案的快捷填值。
- **P1 异步引用恢复与发送丢失**：清除引用也推进选择序号，阻止早先校验返回后恢复旧来源；绑定成功的显式快照发送不再被旧 render 的 contextLoading 挡住。生成 lease 占用时不更换来源；私有 Reading 讨论映射沿用 sessionStorage。Canvas 移除无法携带来源的裸 prompt 回退路径。
- **P2 教师审核入口缺失**：审核页面仍在 `/admin/knowledge`；Chat 顶栏/会话侧栏及六页学习导航补回入口。审核 API 权限不变。
- **P2 工作区与来源标注**：Chat 恢复已有会话后重新保留 workspace 参数；Reading 画布重新挂载时使用当前已绑定来源初始化。课程整理包不再标“教材原文”，移除无依据的学校出处；指纹一致不等于数学审核。Study 加载失败不再同时显示“今日无计划”。

## 验证与限制

- 最终前端 helper 测试 **94/94**，TypeScript 通过；lint **0 error / 10 既有 warning**。新增回归覆盖晚到校验不能覆盖清除、账号/会话失效、生成占用和真实 Reading 构造器，不仅手工构造示例对象。
- 隔离浏览器真实走通：创建今日计划、开始练习、提交轨迹、确认反馈、打开独立检验；有演示登录标志时草稿刷新恢复。Reading 成功向 Chat 发送经校验的来源；Study 普通讨论请求不携带先前 Reading 引用。刷新保留 Study 工作区；390px 页面 scrollWidth=390。教师导航链接已验证指向现存审核页面，未执行真实审核写入。
- 使用 `scripts/r3_ui_fixture.py`、独立双库、固定模型回复；为测试临时 3101 前端，浏览器转发本地 8102 响应时补 CORS 头。产品 CORS、正式服务与数据未改。本轮供应商模型调用 0。
- 全量根 `npm test`：知识 JSON/目录通过，API **969 passed / 2 failed**，因失败停在 API 阶段；前端最终独立运行 94/94。两项积分 SSE 核验测试单独复跑仍失败，进一步直接调用固定 worker 确认为 `execution_status=timeout`、`unknown_reason=tool_timeout`。保留 5 秒核验预算，没有将未知改成已核验，也没有宣称全套通过。
- 本轮未做生产构建，不将前轮证据算作新代码验收。账号变化沿用已有 AuthBoundary 的整页清理/跳转，未重复增加一套身份状态。

日志：`results/r3-domain-fixes/`。其中失败尝试保留，成功 Reading/Study 请求见 `browser-reading-fixed.log`、`browser-study-context.log`；最终前端见 `web-final.log`、`tsc-final.log`、`lint-final.log`。没有自动 commit/push；远端 PR 仍需之后明确更新。

收尾：本轮临时 3101/8102 服务均已停止，验收生成的 next-env 与 tsconfig 目录项已清理；原服务与工作区其它修改保留。
