# 评测与证据边界

项目将工程合同、数学与教学质量、任务可用性和学习收益分开评价。以下脚本默认离线；没有模型调用或真人记录的报告，不产生真实模型或学生效果成绩。

## 评价层次

| 层次 | 材料与工具 | 当前证据 |
| --- | --- | --- |
| E0 工程合同 | [Agent 合同 v3](../evaluation/agent_reliability_v3.json)、API/Web 回归 | 固定实例验证状态、来源、权限、范围和失败处理 |
| E1 数学与教学质量 | [R2 协议](../evaluation/r2/e1-protocol-v1.md)、[审核协议](../evaluation/s5/review-protocol.md)、[开发内容](../evaluation/s5/development-content-v1.md) | 有未签署材料、采集与报告工具；尚无完整独立 gold 和受控真实模型结果 |
| E2 任务可用性 | [任务方案](../evaluation/r2/e2-task-plan-v1.md) | 已定义任务与失败记录，局部自动化观察不能代替真人完成情况 |
| E3 学习收益 | 独立迁移任务与延迟测验 | 尚无足够学生实验数据 |

## 可复现离线验证

先按[运行说明](setup.md)安装依赖。Windows 在根目录执行：

```powershell
npm.cmd test
python scripts/check_docs.py
python scripts/eval_agent_reliability.py --output results/agent-reliability.json
python scripts/r2_review_packet.py --check
```

Agent 默认运行 v3 合同；旧 v1/v2 manifest 保留，可用 `--manifest` 指定历史集合。分母按实际参数化实例固定，缺失、重复、跳过或失败都不能作为通过。v3 增加精确十进制与数学反馈冲突反例，见[失败分析](../evaluation/math-feedback-boundaries.md)。

`r2_review_packet.py --check` 检查已冻结材料与源码摘要。38 个内容条目是审核准备材料，状态为待人工审核；条目数量不代表质量试验次数。修改被绑定内容时需版本化，不将旧评价沿用到新内容。

## 应用流程与报告工具

```powershell
# 真实编译图与固定模型回复，隔离数据库和网络
python scripts/eval_tutor_quality.py --manifest evaluation/s5/runtime-fixture-manifest.json --offline --capture-fixtures --output results/s5-runtime.json --markdown-output results/s5-runtime.md

# 两个 ASGI/SSE 学习流程，使用合成身份与固定模型回复
python scripts/eval_tutor_quality.py --manifest evaluation/s5/episode-fixture-manifest.json --offline --capture-episodes --output results/s5-episodes.json --markdown-output results/s5-episodes.md

# 数学开发材料的未运行状态、独立算术见证及审核准备
python scripts/eval_tutor_quality.py --offline --output results/s5-content.json --markdown-output results/s5-content.md
```

固定回复流程能检查真实编排、引用、学习写入和恢复；它们不评价真实模型回答。默认内容报告可能 `report_complete=true` 且实际执行为零：前者只说明未运行记录完整。未评分项与不适用项分别记录，不能把空分母当满分。

[S5 说明](../evaluation/s5/README.md) 保留输入协议、合成违规、失败分母、来源及内容哈希的细节。[R2 说明](../evaluation/r2/README.md) 提供配对采集入口与人工审核要求。

## 检索评价

```powershell
python scripts/eval_retrieval.py
```

该脚本比较 BM25、向量、混合与课程图 dry-run。向量分支配置 `DASHSCOPE_API_KEY` 时可能访问供应商；无凭证时使用本地 TF-IDF/LSA。重新生成检索题集会改变评价输入，不应在比较前无声覆盖。

## 真实模型与学生评价的准入

真实模型运行需先有明确授权、供应商与模型版本、请求和费用约束、固定输入以及失败记录。数学审核应覆盖定理条件、合法替代步骤、局部正确与整题结论、恰当 unknown、帮助泄露和错误反馈。

由真实作者与独立审核者完成签署后，再安排受控真实模型对照；没有签署时保留 `agent_prepared_only`。学生评价应记录任务初态、帮助程度、完成与恢复失败，再独立检查迁移表现。参考实验跑通或掌握度上升都不足以证明学习收益。

R6 继续使用 R5 的原始三组与开发题；输入冻结、G03 的具体矩阵改进和未完成的保留题门禁见 [R6 针对性分析](../evaluation/r5/r6-gs-analysis.md)。
