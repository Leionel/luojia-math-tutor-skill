# S5.2 首版交付：逐题内容、复核材料与两条ASGI流程

日期：2026-10-07。承接用户“开始5.2”。HEAD仍 `52373b632013e0808f8939b1fd8876edbc5e2850`，成果位于工作区；未提交、推送、部署或调用真实模型。当前交付是内容准备与工程流程，**真人作者审核、独立二审、真实模型质量与封存确认尚未完成**。

## 8道development内容

[evaluation/s5/development-content-v1.md](../../evaluation/s5/development-content-v1.md)与JSON补齐了独立于被测checker的解答、域/量词、必要/禁止项、合法替代路径、任务完成与弃权规则、工具范围及学习资格。原草案保留历史，不冒充新rubric。

- 等价与平方导数：支持正常表示，只确认本行。
- 全实数x/x：保留排除点；正数sqrt(x²)：命题成立与checker不支持前提同时说明，不能拿负数反驳题设。
- 线性残差：独立代回；奇异系统用非零零空间向量/两个合法解说明不唯一。
- Newton循环：精确0→1→0与导数非零，反例不偷换“全实数处处非零”量词。
- 旧实验引用：旧参数/版本保持旧来源，不捏造新初值结果或自动保存。

7项stdlib Fraction精确见证检查通过，未调用应用checker/root runner作内容oracle。它们支撑算术，不构成语义评分或形式证明。材料状态均为`agent_prepared_only`，human_author_review和independent_human_review为pending；没有伪造教师或第二位真人。

manifest绑定内容文件、case全集、输入/rubric/版本。当前input改原始prompt UTF-8摘要，旧S5.1观察不可跨manifest套用。checker_coverage仅适用于前两题，额外条件/全域命题不能被硬记为正常支持子集。E1/E2共用8个case，不变成16样本。

## 可复核的操作入口

- `--review-packet-output`：生成未签署worksheet，输入/rubric摘要绑定，response_sha256与review者为空，必要项/禁止项待定位证据；不兼容已评分reviews，防止空模板变成绩。
- `--content-markdown-output`：生成可读题解/rubric材料。
- `--recorded-answers`：导入调用方提供的公开dev录制回答，严格检查ID、manifest/input摘要、执行状态、来源字段与32768字符上限；只输出回答摘要和caller_supplied_unverified声明。没有发起模型调用，也不认证录制或review者身份，运行版本缺失保持未知。缺case仍保留not_run/不完整，不缩分母。
- 输出不得覆盖manifest、内容、观察/录制、评分、profile或彼此。

真人审核流程见[review-protocol](../../evaluation/s5/review-protocol.md)。4个确认register只是空名额，无题目/答案/真实hash或冻结状态；确认运行仍关闭。真实审核完成须保存真实来源并版本化升级，当前材料不能自动自升gold。

## 两条完整流程的工程证据

运行命令：

```powershell
python scripts/eval_tutor_quality.py --manifest evaluation/s5/episode-fixture-manifest.json --offline --capture-episodes --output results/s5-2-episode-report.json --markdown-output results/s5-2-episode-report.md
```

使用真实FastAPI路由、ASGI/SSE、TutorOrchestrator/compiled graph、临时SQLite；固定模型与合成Principal、隔离检索和后台enrichment，只有进程内testserver传输被允许，外部HTTP/socket被拒绝。每episode独立初始库，连接finally关闭。

| episode | 实际run | 阶段 | 当前结果 |
|---|---:|---:|---|
| Newton参考实验 | 1 | 11 | 引用→讨论/服务器卡片→预览/重试→合成用户显式save/重试→新引用；错hash409、范围外owner404、帮助锁409均按预期拦截；参考结果不记学习成绩 |
| 普通数值Chat修订 | 2 | 7 | 初始候选→修改候选→用户输入顺序/哈希→两答复不同→metadata与SSE/恢复一致→mastery与mistake均无不合格写入 |

总2个episode、3个LLM run、18项观察通过，状态`passed_content_pending`。保存由真实编排完成，区别于S5.1 harness投影保存。metadata比较排除会在流终态更新的agent_run展示快照，run_refs单列；不以此宣称trace恢复完整验收。

采集中最初把矩阵分支的step_check.input_hash视为必须有值，实际该分支未请求单步核验，应为N/A。现按保存的原用户输入绑定每turn，并明确没有checker确认矩阵候选；不增加假hash或修改生产行为来通过测试。错误码不是统一失败：409/404是保护期望时正确拦截。

合成Principal不验收JWT签发，固定数学回复不证明真实模型回答质量，HTTP确认不等于真人完成或真实浏览器点击。所有fixture仍单列，真实模型数学质量比例保持null。

## 验证

- 根 `npm.cmd test`：知识JSON、API **780 passed**（5条警告）、前端 **56 passed**；新增S5.2 **31项**，S5.1＋S5.2 targeted **80 passed**。
- E0 v2：38合同/92实例通过；新增独立S5.2 E0 manifest：11合同/31实例通过。公开工程回归不是封存数学质量集。
- 内容绑定报告、精确算术、未签署worksheet、offline/dry-run及两流程JSON/Markdown均可复跑。
- 16个原保护文件hash不变；没有新增生产接口/表/依赖、没有修改默认离线门控。仅工具/数据/文档/测试改动，本轮不重复UI构建或浏览器验收。

生成证据位于ignored results：`s5-2-full-tests.log`、`s5-2-content-report.json/md`、`s5-2-human-review-worksheet.json`、`s5-2-episode-report.json/md`、`s5-2-reliability-{v2,addendum}.json/log`、`s5-2-dry-run.json`。真实答案原文不会进入公共报告。

## 尚需完成

S5.2真人审核/二审、真实回答评分、4道新确认题的独立准备与封存仍pending。本轮已交付可审核材料、来源/状态与工程流程，不宣称S5.2全部质量验收结束。S5.3可在明确授权后准备能力/计费上界/发送前预算和小规模live；没有因offline通过自动消费。产品linear只读引用继续按共同索引为候选，不把本轮固定矩阵聊天冒充可信实验引用已实现。C0/C1、研究测验与真人学习收益不受本轮自动升级。
