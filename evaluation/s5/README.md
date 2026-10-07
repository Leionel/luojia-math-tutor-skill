# S5.1：离线评测报告与草案入口

当前S5.2更新（2026-10-07）：8道development逐题材料已准备并绑定，状态仍agent_prepared_only/真人审核pending。两条ASGI/SSE完整流程的固定模型采集已实现；不代表真实模型数学质量。S5.1接口继续兼容，新增接口见下方。

这是 **offline replay / dry-run 首版**。默认模式只回放，不启动应用；显式capture模式在独立子进程跑编译图/固定worker。两种模式均不读正式学生库、不加载 `.env` 或真实模型凭证、不发网络请求；没有 `--live` 参数。S5.0 E0 回归继续单独运行，不能与这里的质量题目相加。

## 直接运行

在仓库根目录执行：

```powershell
# 8道development草案：全部保留not_run，不编造模型成绩
python scripts/eval_tutor_quality.py --offline --output results/s5-1-offline-plan.json

# 独立合成报告fixture：3条执行观察、1条budget_stop，故意含违规和未评分例
python scripts/eval_tutor_quality.py --manifest evaluation/s5/runner-fixture-manifest.json --offline --observations evaluation/s5/runner-fixture-observations.json --reviews evaluation/s5/runner-fixture-reviews.json --output results/s5-1-fixture-report.json

# 只显示任务数、run数和假设请求上限；不会启动真实调用
python scripts/eval_tutor_quality.py --dry-run --output results/s5-1-dry-run.json
```

退出0只表示报告成功生成且观察记录完整，不表示模型质量通过；1表示已写报告但观察ID缺失；2表示输入合同拒绝。fixture中的verification overclaim有意用于证明违规不会被均分吞掉，不能解释为当前产品发生该违规。实际quality只计`recorded_run`，`component_check`、`fixed_fixture`分别展示。

## 文件与审核状态

- `manifest.json`：8个development ID、固定指标适用性、输入/草案rubric摘要；gold均为`pending`。
- `development-drafts.json`：公开草案输入和共用初步检查项，不是已复核标准答案。输入/rubric摘要使用`json.dumps(value, ensure_ascii=False, sort_keys=True)`的UTF-8 SHA256；后续S5.2补齐逐题解答/rubric并重新冻结manifest和观察绑定。
- `runner-fixture-*`：与development分开，全部synthetic；只测试报告合同。没有伪造第二位真人复核者或封存题。
- 两条完整学习流程、4道独立确认候选、数学gold二审与应用图观察采集adapter仍待S5.2；确认split当前拒绝运行。

## 观察与人工评分

观察JSON固定版本`s5-observations-v1`，包含精确`manifest_sha256`和`records`。每条绑定`case_id`、`input_sha256`与`run_status`（completed / failed / not_run）；执行过的条目还要有`evidence_source`、`response_sha256`、安全的`run_ref`。not_run必须说明budget_stop、gold_pending、provider_unsupported、cancelled或fixture_not_supplied。ID重复或意外ID拒绝；缺ID不会悄悄缩短任务表。

评分JSON固定版本`s5-reviews-v1`，绑定同一manifest、case、response和rubric摘要；声明reviewer_id/role，所有指标值只能boolean或null。N/A不允许评分；未执行不允许评分；恰当与不当弃权不能同时为true。固定fixture只能synthetic评分。真实质量rubric仍pending时拒绝评分；author_reviewed_only保持作者审阅标签，不升级为独立确认。

`null`表示尚未评分，`applicable=false`表示该指标不适用，两者分开。每项报告numerator、固定执行分母、scored、unscored；只要有未评分项，rate为null；零分母也是null。failed执行仍在分母内。核验越界、帮助违规、无依据成功作为独立违规条目；不生成一个掩盖违规的综合分。

原始答复、隐藏推理、工具参数、endpoint、账号或密钥不会进入报告。评分者身份由文件声明，并没有认证；摘要绑定防止意外串题，不能独自证明观察或人工评价真实可信。S5.2必须补齐采集来源与真实复核。

## dry-run profile 的边界

可选`--profile`只接受`s5-plan-profile-v1`及model_label、endpoint_sha256、max_requests、currency、max_cost六个脱敏规划字段，拒绝endpoint URL/API key字段。model_label输出为摘要。每run最多6请求仅是现有规划假设，episode按planned_runs计算；协议probe没有纳入本次计划。

无论profile是否填写，`live_ready=false`。报告显示live未实施/未授权、价格与可计费token上界未核实等pending，不把费用提案当发送前硬预算。真正transport预留、取消/失败计费和provider准入属于S5.3。

## 复验

```powershell
cd apps/api
python -m pytest tests/test_s5_quality_eval.py -q
```

新增49项回归覆盖：缺失/重复/意外ID、scope来源分离、未评分/零分母、失败仍入分母、hash绑定、N/A、弃权冲突、违规、not_run、episode run计数、JSON重复字段/NaN、CLI两种模式和拒绝live/凭证profile。


## 实际链路采集与解释报告

```powershell
python scripts/eval_tutor_quality.py --manifest evaluation/s5/runtime-fixture-manifest.json --offline --capture-fixtures --output results/s5-1-runtime-report.json --markdown-output results/s5-1-runtime-report.md
python scripts/eval_tutor_quality.py --offline --output results/s5-1-offline-plan.json --markdown-output results/s5-1-offline-plan.md
```

capture只接受固定的4个公开合成case，不能执行任意development/confirmation输入；子进程移除凭证、禁dotenv和HTTP/socket连接，每case独立临时学生库与课程库，固定LLM响应、隔离检索，20秒case上限（内部核验仍最多5秒）。真实编译图结果经现有metadata投影由harness保存，再从临时库恢复；这不是HTTP/SSE验收。数据库连接在finally关闭，避免Windows临时目录被锁。

自动记录核验来源/范围/正误/资格、mastery/mistake写入次数、输入绑定和恢复一致性，不使用人工布尔评分替代实际状态。结果仍归fixed_fixture，不进入真实模型质量。报告拒绝任意原始配置/endpoint字段；runtime来源摘要单列，不把生成报告时的HEAD冒充历史运行版本。手工recorded_run来源仍是调用方声明，不存在自动认证。

Markdown解释报告区分执行覆盖、工程状态和内容评分；列出每题待补证据、未评分/零分母原因、真实失败簇和单因素复跑条件。合成违规不归因于产品；没有真实失败簇时不推荐凭空加ProofState或更多Agent。新增测试真实执行4类case，同时验证无资格写入单独阻断、来源字段脱敏和解释报告不编造质量提升。

四类runtime manifest包含独立工程期望。report会比较这些期望，防止所有题unknown也显示合同通过；它们不升级为真实模型数学gold。S5.1验证目标与后续启动条件见 `planning/agent-v3-2026-10/11-s5-1-evaluation-rationale.md`。


## S5.2 内容与流程

```powershell
# 内容报告、未签署人工审核worksheet和可阅读题解
python scripts/eval_tutor_quality.py --offline --output results/s5-2-content-report.json --markdown-output results/s5-2-content-report.md --review-packet-output results/s5-2-human-review-worksheet.json --content-markdown-output evaluation/s5/development-content-v1.md

# 独立临时库、固定模型、实际ASGI/SSE两流程
python scripts/eval_tutor_quality.py --manifest evaluation/s5/episode-fixture-manifest.json --offline --capture-episodes --output results/s5-2-episode-report.json --markdown-output results/s5-2-episode-report.md

# 回放调用方提供的公开dev回答，不启动模型；文件来源不自动认证
python scripts/eval_tutor_quality.py --offline --recorded-answers results/s5-recorded-answers.json --output results/s5-recorded-replay.json

python scripts/eval_agent_reliability.py --manifest evaluation/agent_reliability_s5_2.json --output results/s5-2-reliability-addendum.json
```

新`development-content-v1.json/md`包含每题独立解答、域/量词、必要/禁止项、合法替代路线与弃权规则。当前manifest输入哈希改为原始prompt UTF-8 SHA256；rubric仍为sort_keys/ensure_ascii=False JSON摘要，content按文件字节摘要；旧S5.1观察不能跨新manifest套用。原development-drafts.json保留历史，不是当前评分标准。

内容loader检查同目录文件/哈希、全case集合、输入/rubric/版本绑定和agent准备状态。输出不得覆盖manifest、内容、输入观察或彼此。没有真人记录不把agent准备升级gold；独立精确算术不调用被测checker/root runner，不是语义评分或形式证明。复核步骤见[review-protocol.md](review-protocol.md)。4个确认名额的register没有题目/答案或伪造hash，确认运行仍关闭。

Newton流程：fixture初始已保存实验→真实讨论/服务器卡片→预览→预览重试→合成用户显式save→save重试→新引用→失效hash/范围外owner/帮助锁拦截。预览/保存数量、参考轨迹和无学习写入实际检查。普通数值Chat流程：第一候选的残差讨论→用户改候选→第二答复→用户输入顺序/哈希、恢复metadata与SSE一致、两处学习记录均空。共2个episode、3个LLM run、18项阶段观察；401认证签发、真实页面、真实模型内容未验收。

ASGI在进程内由真实路由/编排运行；合成Principal代替JWT认证。仅允许TestClient的testserver传输，外部HTTP/socket拒绝；固定LLM、隔离检索与后台enrichment，每episode独立临时库。metadata比较排除流中终态更新的agent_run展示快照，run_refs单独保留；不把这个排除说成trace恢复验收。错误码409/404是预期阻止时算正确行为，不把所有非200一概失败。

`--recorded-answers`只接受`s5-recorded-answers-v1`、匹配manifest哈希及records；每record字段固定case_id/input_sha256/run_status/run_ref/response_text/not_run_reason，响应限32768字符。执行态completed/failed需要安全run_ref和非空响应，not_run不能带响应；重复/意外/错绑拒绝。报告只保留响应摘要、材料摘要和caller_supplied_unverified声明，不含原文/密钥/endpoint。缺case保留not_run并返回不完整；当前真人gold未审核，不会自动产生内容质量分。

S5.2新增31项回归：材料hash/ID/版本/假gold、未签署审核、独立算术、输入保护、真实2流程、阶段顺序/缺失/失败、重复run/伪内容审核和回答导入边界。默认npm test及CI API suite仍离线，未新增依赖或生产接口。
