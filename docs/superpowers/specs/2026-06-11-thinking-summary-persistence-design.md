# Tutor 思考状态与过程摘要持久化设计

## 1. 背景

低延迟架构会在模型生成前立即发送 `opening`，例如：

> 我们先确定题型和第一步可用的规则，再继续推进。

当前前端把收到的第一段文本视为正式回答，因此立即清除 `thinking` 状态，导致“思考中（已耗时 N 秒）”消失。与此同时，数据库只保存助手正文，没有保存可公开的过程信息，所以刷新或重新进入会话后无法恢复“查看思考过程”。

本次改造保留快速开场，同时让开场与正式回答之间继续显示思考状态，并持久化可公开、可解释的过程摘要。

## 2. 目标

- `opening` 到达后继续显示“思考中（已耗时 N 秒）”。
- 首个正式 `message` token 到达时停止实时思考计时，但保留本轮最终耗时。
- 生成可公开的阶段摘要，不保存模型原始 `reasoning_content`。
- 助手消息刷新后仍可展开“查看思考过程”。
- 已有数据库自动迁移，旧消息保持兼容。
- 不增加新的 LLM 调用，不影响首段响应速度。

## 3. 非目标

- 不持久化模型内部隐式推理或完整思维链。
- 不重构消息展示组件的整体视觉风格。
- 不为历史旧消息反向生成过程摘要。
- 不新增独立事件存储表或复杂审计系统。

## 4. 数据模型

在 `messages` 表新增两个可空字段：

- `thinking_summary text`：公开过程摘要，使用带阶段标签的纯文本格式。
- `thinking_elapsed_ms integer`：从请求进入后端到首个正式回答 token 的耗时；若无正式 token，则记录到请求结束或失败时的耗时。

`Repository.init_db()` 通过幂等 `ALTER TABLE` 为已有 SQLite 数据库补充字段。

`Repository.add_message()` 增加可选参数：

```python
def add_message(
    session_id: str,
    role: str,
    content: str,
    intent: str | None = None,
    thinking_summary: str | None = None,
    thinking_elapsed_ms: int | None = None,
) -> str:
```

用户消息继续使用默认空值。`list_messages()` 返回这两个字段，旧数据返回 `null`。

## 5. 公开过程摘要

过程摘要只描述系统执行阶段，不暴露模型内部推理。格式复用现有 `MathMessage` 的标签解析能力：

```text
[PLAN]
已识别为分步解题请求，目标是确定题型并给出下一步可执行提示。

[隐式 RAG]
已检索本地知识库、会话历史与当前掌握度。

[VERIFY]
本轮未触发符号校验。

[OUTPUT]
已开始组织启发式讲解。
```

摘要由后端根据已存在的路由、Fast Context 和验证结果确定性生成，不调用 LLM。

阶段规则：

- `[PLAN]`：来自 `intent`、`learning_objective` 与 `pedagogical_action`。
- `[隐式 RAG]`：说明本地知识、历史、BKT 或绑定文档是否参与，不展示完整用户数据。
- `[VERIFY]`：说明未触发、SymPy 已验证、SymPy 无法判断后升级、或 Verifier LLM 已参与。
- `[OUTPUT]`：说明进入 Teacher 或 Examiner 生成。

摘要不包含 API Key、完整 Prompt、模型原始推理、数据库内容或最终答案。

## 6. SSE 行为

事件语义调整如下：

1. `opening`
   - 立即追加到助手正文。
   - 不结束 `thinking` 状态。
   - 前端继续显示计时器。

2. `thinking`
   - 只用于可公开过程摘要的增量更新。
   - 不发送原始 `reasoning_content`。

3. `message`
   - 首个正式 token 到达时，前端将消息状态从 `thinking` 改为 `typing`。
   - 停止实时计时，保留最后的秒数。

4. `thinking_end`
   - 返回完整 `summary` 与 `elapsed_ms`。
   - 前端保存到当前助手消息。

5. `done`
   - 保持现有消息 ID 和性能指标。

后端在真正调用生成模型前发送一条公开的 `thinking` 摘要，使用户在 opening 后能看到系统仍在继续处理。

## 7. 前端状态

`LocalMessage` 扩展为：

```typescript
type LocalMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: "thinking" | "typing";
  thinkingSummary?: string;
  thinkingElapsedMs?: number;
};
```

行为：

- 新助手消息初始为 `thinking`。
- `opening` 只追加正文。
- `thinking` 更新 `thinkingSummary`。
- 首个 `message` 将状态改为 `typing`，停止计时。
- `thinking_end` 写入最终摘要与毫秒耗时。
- 请求结束后清除临时状态，但保留摘要和耗时。
- `selectSession()` 和编辑截断后的历史重载，从 API 字段恢复摘要与耗时。

`MathMessage` 在流式阶段显示实时秒数；历史消息显示“本轮思考约 N 秒”，并允许展开过程摘要。

## 8. 错误与取消

- 用户取消生成：保存已经产生的公开摘要；若没有助手消息入库，则不创建空历史消息。
- 模型调用失败：错误消息仍可带上已完成的过程摘要和耗时。
- 旧消息没有摘要：不显示“查看思考过程”，正文行为不变。
- SQLite 迁移失败：应用启动应记录错误并明确失败，不静默写入不一致数据。

## 9. 测试

### 后端

- 新数据库包含两个新增字段。
- 已有数据库可以幂等迁移。
- `add_message()` 与 `list_messages()` 往返保存摘要和耗时。
- `thinking_end` 包含公开摘要和耗时。
- 入库的助手消息包含摘要和耗时。
- 摘要不包含原始模型 reasoning token。

### 前端

- `opening` 后消息仍为 `thinking`。
- 首个 `message` 后状态变为 `typing`。
- `thinking_end` 保存摘要与耗时。
- 历史 API 消息能恢复摘要与耗时。
- 旧消息缺少新增字段时正常渲染。

### 集成验收

- 用户发送问题后先看到 opening，并继续看到思考计时。
- 正式回答开始后计时停止。
- 回答完成后可以展开公开过程摘要。
- 刷新页面后摘要和本轮耗时仍存在。
- 后端全量测试与前端生产构建通过。

## 10. 兼容性

- SSE 保留 `opening`、`thinking`、`message`、`thinking_end` 和 `done` 事件名称。
- 新字段均为可选字段，旧前端和旧数据库记录不会因此失效。
- 不改变普通请求的一次 LLM 调用预算。
- 不改变现有快速 opening 的延迟目标。
