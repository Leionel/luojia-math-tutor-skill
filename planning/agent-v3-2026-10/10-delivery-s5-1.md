# S5.1首版交付：实际链路采集、离线评分与解释报告

日期：2026-10-07。基线HEAD仍为 `52373b632013e0808f8939b1fd8876edbc5e2850`，本轮在已有S5.0工作区继续修改，没有提交、推送或部署。用户要求修复两个透明弹出面板，并开始S5.1；后续明确要求深入审视S5.1内容。

## 交付的内容

S5.1现在围绕“输入→核验→回答→学习写入→保存”一致性建立证据，而非只生成JSON。验证目标与8道草案的取舍详见[11设计说明](11-s5-1-evaluation-rationale.md)，运行接口与schema见 `evaluation/s5/README.md`。

1. `scripts/eval_tutor_quality.py`：offline replay、dry-run、明确opt-in的固定图fixture采集、JSON/Markdown报告。没有live执行参数，不读取真实学生会话、模型密钥或供应商配置。
2. `scripts/s5_quality.py`：固定ID/适用性分母、执行与评分状态、input/response/rubric/manifest摘要、人工来源声明、违规则单列、fixture/component/recorded_run分层。
3. `scripts/s5_runtime_capture.py`：拥有的独立子进程、禁dotenv/网络、每case临时SQLite、固定LLM与隔离检索，执行现有compiled graph和真实固定数学worker；记录实际写入与恢复状态，未复用测试模块作为业务实现。
4. `evaluation/s5/`：8道development草案；4个报告合同示例；4类真实图fixture及独立工程期望。未造独立封存题或真人二审。
5. 解释报告：明确证据能支持的结论、执行覆盖与任务完成差别、逐题待补评分、零分母/未评分、真实失败簇与单因素复跑条件；不合成一个准确率总分。

### 实际状态证据

| 固定图fixture | 本步结果 | 学习资格 | mastery / mistake 写入 |
|---|---|---|---|
| 正确平方导数候选 | student_claim / 正确 | 有 | 1 / 0 |
| 漏内导数候选 | student_claim / 错误 | 有 | 1 / 1 |
| 系统参考求导 | system_calculation / 学生正误为空 | 无 | 0 / 0 |
| 额外前提超出受控解析 | rejected / 未确定 | 无 | 0 / 0 |

四条均输入绑定、初始库独立、保存恢复一致；正常能力期望独立存在manifest，“全部unknown”不能显示合同通过。harness保存的是现有图状态metadata投影，不等于新增HTTP/SSE验收。固定响应不证明模型数学解释或教学能力；这些观察不进入真实模型质量分母。

mastery写入是普通估计更新，错误候选也可能写入，不能解读成答错加分。未知/系统参考不写；一个无资格写入或错绑单独标runtime失败，不能均分抵消。

### 报告的判断边界

- 缺题保留not_run并标不完整；重复/意外ID、输入/评分哈希错绑拒绝。
- applicable来自manifest；failed执行保持分母，未评分保持null；零分母和不齐评分的比例为空。
- 合成fixture违规只属于报告工具测试，不归因当前产品；未复核真实失败时不建议凭空加ProofState。
- capture源码摘要与生成报告时源码快照分开；手工recorded_run未提供运行源码时保持未知。review身份只是文件声明，未认证。
- 目前8道数学/数值草案gold均pending；没有真实模型成绩、匿名盲评、独立确认或跨题型收益结论。

## 面板修复

`mode-switcher.tsx`与`tutor-input.tsx`的弹出菜单由 `bg-[var(--bg-card)]/95` 改为实色 `bg-[var(--bg-card)]`，去掉背景模糊；说明文字用secondary色增加对比。同根因的思考菜单一起修复，模式/按钮值和功能不改。

构建后 `/chat` HTTP200；实际CSS规则为 `background-color:var(--bg-card)`，两组件popup源码均无透明后缀。浅色token为白色、深色为深色实底。浏览器自动UI访问被工具URL策略拒绝，本轮没有新截图验收，不把样式检查当视觉验收。保留本地3000端口预览供用户刷新检查。构建前停止拥有的dev，构建后启用production preview。

## 验证

- 根npm.cmd test：知识JSON、API749项（5条警告）、Web56项通过，含新增49项S5.1回归。
- E0 v2 38合同/92实例和S5.0增量10合同/45实例均通过，未改变原manifest。
- Web typecheck、lint（0错误、10已有警告）和production build通过。
- 四类真实图fixture及offline/dry-run/合成报告回放分别有可重跑JSON；Markdown解释报告单列质量pending。

本机证据（ignored）：`results/s5-1-full-tests.log`、`s5-1-web-build.log`、`s5-1-web-lint.log`、`s5-1-popup-style-check.json`、`s5-1-runtime-report.json/md`、`s5-1-offline-plan.json/md`、`s5-1-dry-run.json`和E0报告。16个保护文件保持原始hash，含07独立审阅、用户原有runtime dirty与已有原型。

## 剩余工作

S5.1首版离线工具已交付；内容质量仍pending。S5.2补独立解答、逐题rubric、两条完整流程与真实回答观察来源，真实复核后再建4道封存确认候选。S5.3单独处理供应商能力/发送前请求和费用预算、授权小规模live；当前profile只打印脱敏规划，并不构成消费准入。未修改生产数学核验行为、数据库结构、模型权限或默认离线测试门控。
