# Agent v3：当前基线与阅读入口

> 2026-10-07 S5.3 offline预算切片已交付并分批提交，见[13回执](13-delivery-s5-3-offline-and-commits.md)。发送前预留、并发/取消/恢复/重定向等39实例通过；只允许MockTransport，供应商probe/计费上界/live未验收。API819/Web56通过；旧“未commit”段落为历史工作区快照。

> 2026-10-07 S5.2首版更新：[12交付回执](12-delivery-s5-2.md)。8道公开dev逐题解答/rubric已准备并绑定（agent_prepared_only），2条固定模型ASGI流程/3个run/18项阶段通过；真人审核、独立二审、真实模型内容与4道确认题仍pending。工程/API780/Web56与E0合同通过，不能转写成数学准确率或teacher gold。

> 2026-10-07 S5.1首版更新：offline/dry-run/replay、四类真实图固定fixture采集及解释报告已实现，见[10交付回执](10-delivery-s5-1.md)和[11验证目标](11-s5-1-evaluation-rationale.md)。8道development输入/rubric仍是待复核草案；S5.2内容质量与真人二审、S5.3 live/预算未完成。旧“CLI不存在”或“仅规划”描述以下方日期为历史快照，不代表当前入口。

> 当前交付更新（2026-10-07）：S5.0 已在工作区实现并完成离线工程验收，见[09交付回执](09-delivery-s5-0.md)：API700/Web56，E0 v2 38合同/92实例，S5.0增量10合同/45实例；前端typecheck/lint/build通过。S5.1–S5.2质量runner/gold及live、linear接入仍待实施。下方原审计/规划描述保留日期，不代表当前源码状态。

原审计时间：2026-10-04（Asia/Hong_Kong）；预约任务开始于04:00。下方SHA、起始dirty与验证表保留原审计快照。

> 当前规划修订（2026-10-07）：用户授权按[07独立审阅](07-plan-review.md)修改方案。两周只承诺S5.0安全、正常能力与学习资格闭环，见[08执行合同](08-s5-0-verifier-contract.md)；gold/runner可并行准备，首版8 dev＋4独立确认候选＋2流程，linear先只读引用，Evidence按失败条件提取。**仅修改文档，漏洞及新评测未实施**；当前依赖/工期看02/04，旧6–9日和全32/36/8不再是当前必交。

## 先看结论

下一阶段先完成S5.0的诚实核验闭环，再用聚焦S5支持局部改进。继续复用LangGraph、LearningContext/Actions、Typed Runtime与RunTrace；不先重建Reasoner，也不等待完整题库才减少linear复制流程。

| 文档 | 用途 |
|---|---|
| [01-gap-analysis.md](01-gap-analysis.md) | 五个主要缺口、源码/测试证据、工作区接入取舍、AX 子审计 |
| [02-evaluation-s5.md](02-evaluation-s5.md) | 最高优先级：数据、gold、指标、对照、预算和报告合同 |
| [03-math-reasoning-design.md](03-math-reasoning-design.md) | 四种架构比较；VerificationEvidence、推理状态、反例与 Lean 的启动条件 |
| [04-roadmap.md](04-roadmap.md) | 可执行切片、依赖、验收、回滚，以及两周/四至六周安排 |
| [05-decision-log.md](05-decision-log.md) | 关键决策和 prompt 要求的十二个判断 |
| [06-internship-story.md](06-internship-story.md) | 可写进简历的当前事实、演示与未来成果边界 |
| [07-plan-review.md](07-plan-review.md) | 原样保留的独立审阅；原方案行号来自修订前版本 |
| [08-s5-0-verifier-contract.md](08-s5-0-verifier-contract.md) | 第一实施切片：正常矩阵、调度、学习资格、历史与验收 |
| [documentation-drift.md](documentation-drift.md) | 当前状态与历史设计的差异；没有删除历史回执 |
| [implementation-notes.md](implementation-notes.md) | 后续执行记录位置；本轮没有实施上述切片 |

## 审计身份与工作区（2026-10-04快照）

- 仓库：`D:\Projects\na-tutor\luojia-math-tutor-skill`。
- 分支：`feature/course-graph-2.0`。
- Audited SHA：`52373b632013e0808f8939b1fd8876edbc5e2850`。
- 指定 prompt 来自另一目录：`D:\Projects\luojia-math-tutor-skill\docs\planning\Audit_on reasoning_20261003.md`，已完整读取；不是切换到该旧目录审计。
- Prompt SHA-256：`3ea06f1fff86b3b31a4fdd4458fae2ccb86df21f2c24745d876a0113ccf2b9d2`，用于区分本轮审计指令版本。
- 起始 tracked dirty：`planning/agent-engineering-2026-10/runtime-review-schedule.md`。该用户修改文件不编辑。
- 起始 untracked：`apps/api/luojia_math_tutor_api.egg-info/`、`apps/web/public/demo-jiuzhang-hybrid.html`、`apps/web/public/style-explorer.html`、`apps/web/public/ui-proposals/`。均保留。
- ignored `results/` 是生成证据，不计为已发布成果。本轮新增的规划与状态索引会令结束时的工作区进一步变脏，不能把这个状态反写成起始基线。

## 已交付能力：审质量，不重复立项

| 阶段 | 当前事实 | 主要证据与限制 |
|---|---|---|
| A0 | 模型完成/失败协议、意图澄清、工具执行证据边界 | `completion_protocol.py`、`policy_router.py`、`test_completion_protocol.py`；不是数学正确性证书 |
| A1 | Answer Guard，至多一次无工具修复；未通过不交付候选正文 | `answer_guard.py`、`graph.py:_guard_answer`、`test_answer_guard.py`；显式规则仍不能覆盖所有语义 |
| A2 | owner/session-scoped AgentRun；消息与终态原子保存；取消、过期中断回执 | `run_trace.py`、`memory/agent_runs.py`、`test_agent_runs.py`；没有 graph checkpoint 或自动 replay |
| A3 | 版本化、离线协议评测 CLI | `scripts/eval_agent_reliability.py`；v1 的 19 合同/40 实例是历史版本，默认已是 v2 |
| S1 | 已保存 Newton 实验的可信 LearningContext，实验内提问和完整聊天恢复 | `learning_context.py`、`lab-tutor.tsx`、`test_learning_context.py`；不是所有领域引用 |
| S2 | 参数卡→编辑→确定性预览→显式保存→同页新实验 | `learning_actions.py`、`root-action-card.tsx`、`test_learning_actions.py`；卡片是服务端固定映射，不是模型选动作 |
| S3 | 原生 `math_differentiate` / `numerical_run`，严格 schema、固定 worker、两轮预算 | `typed_tools.py`、`math_worker.py`、`test_typed_math_runtime.py`；默认关闭，必须匹配端点/实际模型能力声明 |
| S4 | 模型/tool span、因果 parent、请求边界、usage 覆盖、可选版本计价 | `call_observation.py`、`pricing.py`、`agent-run-receipt.tsx`、`test_call_observation.py`；缺失保持未知，不是全账户账单 |

`numerical_run` 当前支持 `LinearTask | IntegrationTask`，并不覆盖任意数学运算或 Newton 题目。Newton 参考讨论故意禁用原生工具和联网，使用保存轨迹及业务预览。旧 `[VERIFY] Python` 模型执行调用点已退役；但**这不等于所有学生表达式路径都已安全**，见 G1。

## 本轮重新验证

| 命令/证据 | 本轮结果 | 能证明什么 |
|---|---|---|
| 根目录 `npm.cmd test` | 知识 JSON 通过；API **655 passed / 5 warnings**；Web **51 passed** | 既有离线回归通过；日志 `results/agent-v3-audit-tests.log` |
| `python scripts/eval_agent_reliability.py --output results/agent-v3-audit-reliability.json` | **38/38 协议合同、92/92 参数化实例** | E0 工程合同；报告含 SHA、源文件哈希与 dirty 标记 |
| 固定无副作用审计探针 | 复现旧解析入口、关键词误判、定义域遗漏与洛必达过度结论 | `results/agent-v3-audit-probes.py` / `.json`；不是新冻结 benchmark 或模型结果 |
| 文档目录、引用与`git diff --check` | 9份文档、12个本地Markdown链接、87处当前源码引用存在性、7个milestone必备字段检查通过；diff check通过 | 只校验文档完整性与引用存在性；不代替源码语义或生产验证。回执`results/agent-v3-audit-docs-check.json` |

本轮未重复运行生产构建或浏览器验收：没有改应用代码/UI，也没有停用现有服务。`delivery-s3-s4.md` 在同一源码基线记录了此前 typecheck/build、lint 0 error / 10 既有 warning 与隔离页面验收；它们是历史回执，不冒充本轮新跑的结果。

## 数学能力的三层边界

1. **确定性领域诊断**：求根更新/导数/停止依据，线性迭代残差与充分条件，积分有限采样估计，受控求导。已具备实际工程覆盖；浮点与采样结果不是一般数学证明。
2. **局部符号核验**：表达式等价、导数、不定积分候选、二阶行列式、未定式类型。已有实现及测试，但安全入口、定义域、unknown 和 theorem scope 有本轮确认的问题，尚不能称为可靠的全题验证层。
3. **开放推理**：证明、定理适用、多步逻辑、反例生成仍主要是 LLM 审查→LLM 教学。Course Graph 提供课程/条件候选，不检查本题是否满足这些条件。

## 当前未知与未验收

- 未运行真实供应商模型；原生协议支持、真实 tool selection、usage 可用性及账单均未被本轮证实。能力配置是声明，不能拿来替代 smoke。
- 没有冻结并独立复核的 E1/E2/E3 质量对照；92/92 不能写成 Agent 准确率或数学正确率。
- 既有求根 10 组工程 episode 不是教师 gold，也不是 held-out 学习测验；manifest 自身写了 `teacher_review=pending`。
- 开放证明没有形式化核验；LLM reviewer 的 `verified` 表示已完成审查，不是严格证明。
- C0 学生代码执行、动态 HTML 同步 JS 的强终止、远端 CI/部署/并发负载、真人学习收益均未在此轮验收。
- 本轮未调用真实模型、未访问学生生产数据库、未更改密钥/能力开关、未 commit/push/deploy。
