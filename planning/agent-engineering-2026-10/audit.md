# Agent 聊天与数学工具执行审查

2026-10-03；按 ax-audit 的聊天 / 工具执行两类 playbook 审查。源码基线：`12255a5a7adb76ddf5977b8481ed84a68cba346a`，下面区分修复前发现与本轮修复后的状态。

**限定范围的 AX 结论：READY，0 个 release-blocker，2 个 fix-this-sprint。** 这个结论只针对下面 18 项规则在本轮两类表面上的覆盖，不是整个产品、真实模型质量或安全隔离验收。完整数学语义 Guard、动态图示 CPU 强制隔离、学生代码 C0 和教师 / 真人评测仍未验收。

## 1. 剩余发现

| 规则 / layer / category | 功能与表面 | 结果 | 默认 → 分配 tier | 证据与原因 | 后续修复 |
| --- | --- | --- | --- | --- | --- |
| `trust-no-confidence-cues` / ax / trust | agent-chat；聊天回答 | warn | fix-this-sprint → fix-this-sprint | `apps/web/components/math-message.tsx:396` 有公开摘要；`apps/api/app/tutor/graph.py:798` 有工具执行范围提示，但工具步骤 / 来源与最后正文不能逐项关联。是部分覆盖，未判作完全缺失；采用聊天 surface override | A1 检查证据矛盾，A2 提供步骤与终态回执；不展示私有推理 |
| `context-memory-not-visible` / ax / context | agent-chat；学习状态上下文 | fail | fix-this-sprint → fix-this-sprint | `apps/api/app/tutor/prompt_builder.py:99` 注入估计；`apps/web/components/learning-panel.tsx:285` 显示部分掌握度 / 提示，但缺少完整来源与纠正 / 停用推断的路径。采用聊天 surface override | A4 可见来源、用户声明 / 推断区分与纠正；成绩和原始事件保持只读 |

两项均未 suppressed。更完整的跨功能上下文列为产品增强建议；普通聊天没有选定工作区对象，不把未载入全部 F1–F8 数据强行判作工具违规。

## 2. 本轮已修问题

| 问题 | 修复前证据 | 当前处理与回归 |
| --- | --- | --- |
| 提供方异常结束当成正常完成 | `openai_compatible.py` 原 stream 忽略 finish_reason，EOF 可正常 return，缺 Key 可 yield 提示文本 | 成功终止 + 非空正文；其他终止、无终止、坏 JSON、缺配置均 typed error。协议测试与 API 未配置模型回归 |
| 不确定任务已写学习事件 | 原 fast_context → policy_fallback，policy.uncertain 只计入 metrics | policy 在 context 前；未确认返回澄清且不进入评估；确认后重新选择核验模式。编译图与 API 端回归 |
| 工具结果由正文猜测 | 原 `"Error:" not in result` 和 `"no output" not in result` | 类型化状态与真实退出码；成功、无输出、warning、失败分别测试 |
| 取消请求可能留后台子进程 | 原同步 subprocess.run 包在 to_thread 中，任务取消无法结束它 | Popen 句柄由执行器管理；取消 / 超时 kill、通信回收和脚本清理。受控进程边界测试；不是 C0 资源隔离证明 |
| 内部阶段文本冒充回答 | 模型正文非空，但剥离 `[PLAN]` 后为空仍可完成 | 可见正文空则 typed error，正文不发送；纯协议候选回归 |
| 延迟口径不准确 | 原 teacher_first_token_ms 在全部缓冲后计算 | 改为 generation_buffer_ms；当前不宣称提供方真实首 token 延迟 |

前四项中的完成信号与取消曾影响工具执行可信度，已在此轮修复，不用下一阶段规划替代当前 bug 修复。A0 没有实现完整最终交付 Guard、trace / span、独立 Agent benchmark 或自动恢复。

## 3. 规则覆盖记录

pass 表示本项代码 / 契约已见满足，且注明验证边界；unknown 表示没有足够交互证据。观测型规则不会仅凭 grep 判通过或失败。

| # | Playbook | layer | Rule | 结果 | 证据 / 限制 |
| --- | --- | --- | --- | --- | --- |
| 1 | agent-chat | ax | comm-no-progress-signal | pass | Orchestrator PLAN、context / verification / output 进度；UI thinking；离线 SSE 测试。每次工具 round 的细节仍待 A2 |
| 2 | agent-chat | ax | control-no-escape-hatch | pass | tutor-chat.tsx AbortController / stop；Orchestrator 取消图任务；数学执行器取消回收测试 |
| 3 | agent-chat | arch | context-no-injection | pass | prompt_builder.py build_messages 有 history、EvidencePack、mastery，资料明确不可信 |
| 4 | agent-chat | ax | trust-no-confidence-cues | warn | 第 1 节的部分覆盖发现；公开摘要不等于答案正确性证明 |
| 5 | agent-chat | ax | trust-no-uncertainty-markers | unknown | 规则为观测型；未做本轮真实模型模糊题 / 缺条件多轮交互，确定性澄清不能代替整体模型语气验收 |
| 6 | agent-chat | ax | comm-no-intent-handshake | pass | 不确定任务先澄清，确认后 context；开场 / PLAN 说明任务；编译图与 API 回归。不是校准概率证明 |
| 7 | agent-chat | ax | control-over-conversational | unknown | 规则为观测型；已有六工作区和模式按钮，但未对本轮目标任务做真实交互 / 用户研究，不能据此证明按钮粒度合适 |
| 8 | agent-chat | ax | context-memory-not-visible | fail | 第 1 节；公开估计还缺来源与纠正路径 |
| 9 | agent-chat | ax | comm-no-generative-momentum | unknown | 规则为观测型；首页任务 / 建议存在，未实测新用户是否得到适用下一步，不能从静态入口判断有效性 |
| 10 | agent-tool-execution | ax | trust-no-escalation-path | pass | 范围是有限数学计算和只读检索，无高风险自主决策；失败返回未验证 / error，用户可修改重试。不用虚构人工升级后台补一个不适用条件 |
| 11 | agent-tool-execution | ax | control-no-approval-gate | pass | AST allowlist 的受控数学计算；本轮无删除 / 发送 / 付款等需要确认的动作。安全低风险调用适用 false-positive guard |
| 12 | agent-tool-execution | arch | comm-no-approval-gate | pass | 同上；owner / 独立 probe 帮助规则由服务端裁决，不新增反复审批 |
| 13 | agent-tool-execution | ax | control-no-escape-hatch | pass | 数学执行器持有 process，CancelledError 不吞掉；取消图和 kill / 回收契约均有离线测试。浏览器动态图示 CPU 问题不在本项范围 |
| 14 | agent-tool-execution | arch | comm-no-progress-visibility | pass | 执行前有核验 / 输出阶段进度，失败有明确提示；SSE on_progress 接到 UI。逐步骤持久 trace 是 A2 增强 |
| 15 | agent-tool-execution | arch | comm-no-completion-signal | pass | 提供方显式终止，工具真实退出码，图结束后 done；失败不会 done，不以停顿时间判完成 |
| 16 | agent-tool-execution | ax | comm-no-intent-handshake | pass | 数学核验目标与范围来自本轮任务 / 公开 PLAN；只读计算不涉及未经请求的外部操作 |
| 17 | agent-tool-execution | ax | context-under-contextual | pass | 当前数学工具获得任务消息、核验结果与检索上下文；普通聊天未绑定工作区，不把未来 snapshot 能力当缺失必需输入。A4 单路径增强另列 |
| 18 | agent-tool-execution | arch | granularity-static-api-mapping | unknown | 规则为观测型；当前仅有限数学工具，无真实工具扩展 / 动态发现使用证据，不强行加 MCP 或多工具 catalog |

### Audit self-check

- Surfaces planned / audited：2 / 2（聊天、服务端数学工具执行）；不覆盖系统提示词编辑器、管理 dashboard 和任意学生代码运行。
- Playbook checks planned / recorded：18 / 18；unique rule slugs：16；两个重复规则在不同表面独立检查。
- pass 12、warn 1、fail 1、unknown 4；unknown rate = 4/18 = 22.2%，低于 30% 完整性门槛。
- Suppressed：0；目标源码未找到 `ax-audit-ignore` 注释。
- 两项 finding 都有文件、行号、结果、默认 / 分配 tier 与理由；观测型 unknown 不变成发布阻断或通过证明。

## 4. AX Relationship Summary

- **evolutionStage：3，Personally Intelligent 的有限形态。** 保存历史与学习估计，并用其调整教学提示；工具动作以建议 / 反馈和显示确认边界为主。没有证据证明稳定个性化偏好、跨工作区连贯理解或自主维护任务。
- **trustSignal：moderate。** 已有取消、错误终态、来源 / 核验范围与独立帮助限制；最后正文与证据一致性及可纠正记忆仍有缺口。
- **keyGap：** 缺少把最终回答、实际工具结果和持久执行状态关联起来的交付协议。
- **trustQuestion：** 用户是否能用折叠步骤和“本次参考了什么”理解结论依据，而不会把计算成功误读为整段数学正确？需要在 A2 / A4 用原型交互验收。

## 5. 检查文件与证据范围

实际检查包括：`tutor/graph.py`、`orchestrator.py`、`fast_context.py`、`fast_path.py`、`intent_router.py`、`policy_router.py`、`prompt_builder.py`、`prompt_policy.py`、`proof_tutor.py`；`llm/openai_compatible.py`、`completion_protocol.py`；`agents/code_executor.py`、`tool_result.py`；`memory/repository.py`；`api/routes_tutor.py`；`web/components/tutor-chat.tsx`、`math-message.tsx`、`learning-panel.tsx`；`web/lib/api.ts`、`message-status.ts`、`tutor-stream.ts`；相关图、提示词、SSE、执行器与 API 回归。

验证详情见 [plan.md](plan.md) A0 回执与 `results/agent-reliability-tests.log`。本轮测试全离线；没有真实模型、学生试用、教师 gold、正式 sandbox、远端 CI 或生产部署证据。官方项目比较与后续切片见规划，不把参考文档描述冒充本项目已经实现。
