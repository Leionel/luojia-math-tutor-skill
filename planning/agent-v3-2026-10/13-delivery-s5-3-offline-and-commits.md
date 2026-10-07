# S5.3 离线预算切片与分批提交回执

日期：2026-10-07。用户授权“继续下一步，并分步提交”。本轮实现发送前预算的offline合同，**没有供应商协议probe、真实价格核实或付费模型运行**，没有接入生产LLM客户端。

## 已分批提交的已有成果

| commit | 内容 |
|---|---|
| `988e65c` | S5.0有界检查、输入/候选绑定、两处学习证据资格 |
| `f90cc2e` | 核验展示、文案、实色菜单和首页效果 |
| `085b9e6` | S5.1/S5.2离线评测、内容/rubric与ASGI流程 |
| `dd95458` | 产品/工程共同索引、审阅与交付文档 |

四批源码与此前通过回执的源文件hash一致后提交。旧回执中的HEAD和“工作区未提交”保留实施当时快照；不能据此说当前仍未提交。以下预算切片在本轮验收后另成一批，最终hash见Git log/本轮最终回复与ignored提交回执。尚未推送。

## 离线预算合同

新增 `scripts/s5_budget.py`，与生产模型client隔离。`OfflineBudgetPolicy`只接受synthetic_fixture价格合同及全部计费项已有上界的明确标志；`OfflineBudgetTransport`底层只允许精确的httpx.MockTransport，真实HTTPTransport拒绝。不能把operator_verified、未知费用或一个手填金额转换成live许可。

固定POST目标/model，限制纯文字、64KiB请求、明确且有界的max_tokens或max_completion_tokens。拒绝图片、动态tool字段、embedding/不同endpoint/查询/重定向、不合法输出上限和重复JSON。字节上限是内存边界，**不是计费token上界**。本切片没有验证真实供应商tokenizer、cache/reasoning/按次费或真实per-request上界。

SQLite在传输前用BEGIN IMMEDIATE预留请求和合成最坏费用，Decimal处理，币种不转换。计数与保留成本原子更新，profile指纹绑定；并发不能超额。失败、取消、重试、未知usage均不退还预留；重启保留已占额度和未闭合reservation，不能靠重新创建client或改profile恢复预算。ledger计数/成本与reservation不一致时拒绝继续发送。

返回HTTP响应只标`response_received`，不表示模型完整回答。拒绝重定向后不跟随、不退额度；终态不会被后续异常改回失败。报告只含政策/endpoint摘要、计数、保留费用和状态，不存正文、密钥或原始endpoint；actual_cost保持null。事务为短同步本地操作，工具只用于隔离offline harness，不宣称生产异步性能/强OS隔离。

## 验证

- 新增 **39项**回归：第52请求不发送；40并发竞争在0.07合成预算下只允许7次；失败/重试/未知usage不退款；取消与恢复；profile改动/ledger损坏；endpoint/payload/重定向/真实transport拒绝；数额精度与费用覆盖边界、终态/隐私。
- 根`npm.cmd test`：知识JSON、API **819 passed**（5条警告）、前端 **56 passed**。
- 独立S5.3 E0：**16/16合同、39/39实例**，`evaluation/agent_reliability_s5_3.json`。原E0 v2与S5.2 manifest未变，旧题仍在全量suite。
- 合成示例：2次预留，第三次发送前被阻止；真实供应商请求0。helper源码/测试/manifest hash另存`results/s5-3-budget-proof.json`，因为旧E0报告源范围主要是app/tests。
- 没有UI源码变化，不重复前端build/浏览器验收；保留3000本地预览。此前已通过界面构建随第二批提交。

证据：`results/s5-3-full-tests.log`、`s5-3-reliability-addendum.json/log`、`s5-3-budget-proof.json`。源码与测试提交，生成账本/日志/实际profile不提交。

## 未完成的S5.3内容

此处仅offline预算切片，不是S5.3全部验收：实际供应商协议能力bootstrap、真实计费与token上界、最多3个协议请求、批准的最多8单run smoke、真实usage/费用核对与生产client可选注入均未做。真实profile/许可缺失时live保持关闭，不自动读`.env`消费，不将synthetic合同写成provider_verified。

S5.2真人作者审核/二审、真实回答评分和新封存确认继续pending；不因提交或预算fixture通过被自动升级。最近可独立推进的产品候选仍为linear只读可信Chat引用。

## 保留的工作区内容

原`runtime-review-schedule.md`修改、egg-info与已有public原型未提交，当前字节与本轮之前一致。07独立审阅原文保留并作为文档提交，不修改内容。正式学生库、上传件、密钥和results未进入这些提交。尚无远端CI、推送或部署回执。
