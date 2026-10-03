# S3/S4：固定数学工具与调用计量交付

日期：2026-10-03。范围：S3/A6.2 与 S4/A7 的本地工程验收；S1/S2 的 Newton 引用、参数预览和显式保存继续保留。

## 已交付的行为

普通聊天在服务端开启开关、且当前模型与端点有匹配的能力声明时，允许模型通过 Chat Completions 原生 `tool_calls` 选择两个固定函数：

| 线上函数名 | 实际处理器 | 证据范围 |
| --- | --- | --- |
| `math_differentiate` | 单变量 x 的 AST → 白名单 SymPy 构造器 → 求导 | 原表达式有定义且可微的区域；不自动求定义域、不证明整段回答 |
| `numerical_run` | 已有 `NumericalTask/run_numerical` | Jacobi/Gauss–Seidel 浮点残差；梯形/Simpson/自适应 Simpson 的采样误差估计 |

它们只返回参考计算，不保存实验、不代填学生预测、不提升掌握度或独立成绩。成功结果记录三级帮助曝光；请求开始、返回结果以及最终交付均检查进行中 probe/章节自检的帮助限制。S1/S2 的可信 Newton 引用路径继续只讨论固定快照，业务卡片仍由服务器组装，不宣称模型自行选择保存动作。线性/积分历史尚未接入可信聊天引用。

原生续轮由服务端固定表派发：完整工具请求 → 参数/帮助检查 → 固定 worker → 同 call_id 的 tool 消息 → 最终教学正文 → Answer Guard → 消息/run 原子落盘。工具失败仍是结构化结果，不能因为模型继续回答而算计算成功。

聊天的模型生成 Python 执行调用点已全部移除。旧验算标签被忽略，不转换为 DSL，不执行；只有标签且无正文仍交付失败。关闭新开关也不会恢复旧路径。`agents/code_executor.py` 仅保留内部历史实现和旧回归测试，没有 app 内调用方；学生代码作业仍只做静态审阅。提示版本为 `teaching-v2.5`，Guard 为 `delivery-v2`。

## 计算与协议预算

- 每个 run 最多两轮、每轮一个调用；参数修正占同一预算，第三次模型请求只允许正文。默认不自动重试；Guard 最多修复一次，并且修复不提供数学工具。
- call_id 格式受限，同 run 的同 ID/同参数 hash 复用结果，改参数复用 ID 拒绝。它不是 owner 或授权凭证。
- 参数 JSON 最多 8 KiB；严格模型拒绝额外字段、代码、owner/run 等参数。原生分片必须组装完成且 `finish_reason=tool_calls`，拒绝半途 EOF、截断、并行调用、重复 JSON key、未知函数、结束后的额外调用。
- 求导表达式最多 512 字符、64 AST 节点、深度 12；仅 x/pi/e、四则运算、整数幂 −8…8、sin/cos/tan/exp/log/sqrt。常量字面量最多 32 字符、绝对值 ≤10¹²。属性、索引、导入、lambda、列表和任意函数均拒绝。父进程与 worker 两次校验。
- 固定 worker 以 `python -I -u` 运行，参数只走 stdin；最长 10 秒，stdout+stderr 在采集中共同限制 64 KiB。取消、超时和输出超限均终止并回收实际拥有的进程。移除模型服务密钥等环境变量，不执行临时模型脚本。Windows 用户级已安装依赖路径仅作为固定依赖目录加入，不执行其 .pth。
- 模型请求整体 JSON 硬上限 128 KiB；若声明输入 token 上限，还把同一数值作为更保守的 UTF-8 字节上限，**不是 tokenizer 的实测 token 数**。已知输出上限发到提供方，最多 4096；未知不猜参数。流式响应总量 512 KiB、单行 128 KiB，在解析前约束；非流式正文读取后、解析前检查 512 KiB。

这里的进程管理和表达式白名单不等于 OS 强隔离，也没有内存/CPU 配额证书。HTML 动态图示、学生程序 C0、完整数学语义审查不在本切片。

## 调用回执与统计口径

每次实际 client 调用都有 span/call ID、parent ID、开始/结束时间、状态、耗时与安全错误码。工具 span 指向提出请求的模型 span，通过哈希后的原生 call_id 关联；公开记录不保存参数、stdout、prompt、原始端点、密钥或私有推理。

`model_attempts` 是进入客户端的尝试，`model_requests` 是进入 HTTP 请求边界的次数；未配置密钥的尝试不算发出请求。路由、审查、图片、检索向量、续轮和 Guard 修复在当前请求上下文中都计量。后台脱离聊天 run 的语义补全不混入该 run；这不是全账户账单。

`first_content_ms` 从请求边界到第一个非空正文 delta，排除 reasoning delta；没有正文 delta或非流式调用时保持未知。它是客户端观测的正文首片段时间，不是提供方内部计算时间，也不是用户收到最终正文的等待时间。最终正文仍经 Guard 缓冲交付。

usage 只接受提供方报告且输入+输出=总量的非负整数；缺失、非法、冲突都为未知。回执展示报告覆盖数、已知部分 token 合计；未报告的失败/修复请求不按零补齐。价格只有匹配模型/端点、币种和日期版本的运营配置时才估算；非零 cache/reasoning token 无对应计价模型时费用保持未知。部分费用明确标注“仅已知部分”，不是实际扣费。

回执继续使用 `run-v1` 和现有 steps JSON，新增 `usage-v1` 汇总；无新表、迁移或依赖。旧无 span 回执可读，usage 保持未知。刷新从同一 SQLite run 汇总，消息元数据和流终态一致。取消/过期重启关闭仍开着的 span，不伪造时间或用量。修复了检索超时的重复取消可能造成“SQLite 已提交、内存序号未推进”的问题：持有序号锁直到写入完成并同步，再传播取消。

网页“本轮过程”折叠区展示数学工具、模型阶段、真实耗时、正文首片段、请求数与用量覆盖。合并同一 span 的 started/dispatch/terminal 事件，保留不同调用；工具行加橄榄绿标识。桌面与 390px 页面使用同一回执组件。

## 如何开启

默认配置如下；本轮不修改现有私密 .env，不因为供应商名称猜测 tools/usage 能力。

```dotenv
TYPED_MATH_TOOLS_ENABLED=false
LLM_CAPABILITIES_JSON={}
LLM_PRICES_JSON={}
```

先在当前 API 目录计算绑定，不输出密钥：

```powershell
cd apps/api
python -c "import hashlib; from app.config import get_settings; s=get_settings(); b,m=s.resolve_request(None); print('selector='+s.llm_model); print('resolved_model='+m); print('base_url_sha256='+hashlib.sha256(b.rstrip('/').encode()).hexdigest())"
```

运营者针对实际端点与实际模型验证流式 function calling 和 usage 后，将以下 JSON **作为一行**写入 `LLM_CAPABILITIES_JSON`；替换 selector、wire model、hash、时间和实际上限。未验证的字段填 null；仅 `tool_calls=true` 且 `streaming=true` 时允许开启计算。能力记录是运营声明，不是应用自动测得的证明；任一绑定不匹配均回到 unknown。

```json
{"your-selector":{"resolved_model":"actual-wire-model","base_url_sha256":"endpoint-sha256","source":"operator_verified","checked_at":"2026-10-03T00:00:00+00:00","tool_calls":true,"streaming":true,"stream_usage":null,"input_token_limit":32000,"output_token_limit":4096}}
```

完成配置后设置 `TYPED_MATH_TOOLS_ENABLED=true` 并重启 API。测试使用 `source=offline_fixture` 和 HTTP 替身，与真实供应商验证严格分开。原生协议参考 [OpenAI function calling 文档](https://developers.openai.com/api/docs/guides/function-calling)，其他兼容端点的支持须分别核对。

可选 `LLM_PRICES_JSON` 同样按 selector + resolved_model + endpoint hash 绑定；字段是 `currency`（USD/CNY）、`version`（YYYY-MM-DD，可附 -vN）、`billing_mode=plain_input_output`、`input_per_million`、`output_per_million`。输入费率采用官方来源的运营维护值，不能沿用测试数字。估算公式为 `(input_tokens × input_rate + output_tokens × output_rate) / 1,000,000`；未填则费用未知。

## 验收与下一步

- 完整离线 `npm.cmd test`：知识 JSON、API 655 项、Web 51 项通过；日志 `results/s3-s4-full-tests.log`。
- `python scripts/eval_agent_reliability.py` 默认 v2：38/38 协议合同、92/92 参数化实例；日志与可追溯报告 `results/s3-s4-eval.log`、`results/s3-s4-reliability.json`。保留 v1 的历史19合同/40实例，可用 `--manifest evaluation/agent_reliability_v1.json` 显式运行旧合同。
- TypeScript、lint、生产构建通过；lint 0 error / 10 既有 warning。前端和进程取消检查分别使用真实页面、实际固定子进程。
- 网页隔离验收走真实 HTTP 适配器/编译图/worker/Guard/SQLite：一次求导、一次续轮、一次无工具修复，实际3请求、2次 usage 报告；刷新保持相同口径，费用为合成测试数据，页面明确标记离线验收。
- 攻击参数、ID 冲突、两轮预算、实际取消/超时/输出超限、中途启动自检、无输出/半途 EOF、修复不执行工具、私有信息投影、重启 span 闭合均有回归。积分反例 `sin(16*pi*x)^2` 仍可能采样出近零估计，Guard 拒绝显式“严格保证积分误差”的声明。

下一步 **S5/A5**：冻结任务级 E1、E2 对照（旧基线 vs 新 Runtime），安排人工 gold 复核；在明确的供应商/预算下做 E3 真实模型小规模烟测，再评估更广的数学语义与未标记答案泄漏。v2 是工程协议合同，不能把92/92叫模型准确率。未验收真实模型工具选择、真实账单、教学收益、远端 CI或部署。A8恢复、全部功能引用、C0强隔离继续条件启动。

剩余主线工作量按原规划重估为 S5/A5 及回归约 4–6 个集中开发日，人工 gold/真人学习实验另计；以实测校准，无固定交付日期。回滚只关闭 typed 开关，保留回执和受控实验 API，禁止恢复生成 Python 执行。
