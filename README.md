# 珞珈数智助教 · Luojia Math Tutor

围绕数学推理过程开展教学的 Agent：理解学生主张，结合受控计算与课程证据选择反馈，让学生通过实验、修订和独立任务检查理解。

当前以数值分析为主要学习场景，提供 Chat、数学探索、私人知识网络、教材伴读、学习任务、数值实验、讲回、自检与代码工坊。项目已实现这些路径之间的引用和状态续接；开放数学推理质量与学习收益仍待独立评价。

[快速启动](#快速启动) · [架构](docs/architecture.md) · [学习设计](docs/learning-design.md) · [评测](docs/evaluation.md) · [已知限制](docs/limitations.md)

第一次使用可按[完成一次数学探索](docs/exploration-guide.md)操作：从 Chat 转交主张，编辑预测与实验，确认计算，再修订并回到原会话。没有模型服务时也可手工实验或使用标注的 GS 示例。

## 可以怎样学

| 学习活动 | 当前实现 |
| --- | --- |
| 讨论一道题或一个步骤 | 有限语法内进行确定性步骤检查；其余推理交给模型审查，并标明核验来源、范围与 unknown |
| 围绕一个判断持续探索 | 从 Chat 发起 GS / Newton / 积分探索，编辑同一实验计划、确认计算并修订；[使用说明](docs/r6.3-shared-experiments.md) |
| 用旧判断检查新问题 | 私人候选关系由学生接受/拒绝，相关历史进入原教学决策，显示选择理由与原来源；[数据流](docs/r6.2-personal-decisions.md) |
| 先预测，再做实验 | Newton、线性迭代和数值积分实验；讨论保存的运行，预览受限修改后再保存 |
| 对照教材中的条件 | 读取课程图谱中的来源选段，绑定教材版本和内容摘要；核对条件后回到同一对话 |
| 修改后独立检验 | 分层自检、讲回与限定代码任务；参考运行、获得帮助和独立作答分别记录 |

例如，在实验台保存 Newton 运行后进入讨论，说明你对收敛的预测。助教可以引用这次运行解释轨迹、提出更换初值的对照实验；学生仍需在独立任务中展示掌握。

## 技术实现

- **教学编排**：FastAPI + LangGraph，先收集题目、历史与课程证据，再生成教学决策、回复和交付校验。
- **受控计算**：固定子进程执行有限 SymPy 语法与数值算法；学生候选、系统参考计算和模型意见分别标记。
- **课程证据**：本地检索与 Course Graph 提供知识关系、教材条件、版本和审核发布状态。
- **共享学习工作区**：Next.js + React，以 owner、引用类型、版本、内容摘要和帮助状态校验跨页面引用及操作。
- **可追溯评测**：离线协议合同、固定回复应用流程和待审核数学材料分开统计，不以测试数量代替教学成绩。

数据流、源码入口和信任边界见[架构说明](docs/architecture.md)。

## 快速启动

以下适用于 Windows PowerShell。CI 使用 Python 3.12、Node.js 24；其他系统的命令及配置见[运行说明](docs/setup.md)。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ./apps/api
npm.cmd ci
npm.cmd --prefix apps/web ci
if (!(Test-Path apps/api/.env)) { Copy-Item apps/api/.env.example apps/api/.env }
```

在 `apps/api/.env` 配置模型服务的 `LLM_PROVIDER`、`LLM_BASE_URL`、`LLM_MODEL` 和 `LLM_API_KEY`。没有模型密钥时可使用本地数值实验和静态任务；聊天生成需要有效模型配置。

在两个终端分别启动：

```powershell
# 终端一，仓库根目录
npm.cmd run dev:api
```

```powershell
# 终端二，仓库根目录
npm.cmd run dev:web
```

打开 [本地 Web](http://127.0.0.1:3000)；API 位于 [本地接口文档](http://127.0.0.1:8000/docs)。默认接口地址和 CORS 对应这两个端口，修改端口时需同步配置。

## 如何理解验证结果

```powershell
npm.cmd test
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
npm.cmd run build:web
python scripts/check_docs.py
python scripts/eval_agent_reliability.py
python scripts/r2_review_packet.py --check
```

运行构建前停止使用同一构建目录的开发服务。测试与默认评测保持离线，不需要付费模型。

| 证据 | 能回答的问题 | 当前边界 |
| --- | --- | --- |
| E0 工程合同 | 引用、状态、核验范围及失败处理是否满足已定义约束 | 固定用例通过不代表真实模型数学正确率 |
| E1 数学与教学质量 | 推理、条件、正确步骤误判、unknown 与反馈是否恰当 | 已有开发材料和采集工具，缺完整独立审核与受控真实模型数据 |
| E2 任务可用性 | 学生能否完成跨工作区任务并恢复状态 | 已有任务方案和局部工程观察，缺系统真人验收 |
| E3 学习收益 | 学生能否在独立迁移任务中掌握方法 | 尚无足够学生实验数据 |

可复现命令、材料来源与失败分析见[评测说明](docs/evaluation.md)。

[R6.4 探索评测](evaluation/r64/README.md)已完成 105 次离线采集和 5 项浏览器功能任务；真实模型、独立数学评分、真人与迁移测验未运行，不据此宣称教学收益。

[R6.5 体验收束](evaluation/r65/README.md)修复入口发现性、资料加载时输入清空、历史定位与手机长公式溢出，并减少重复目录请求和自动标题模型调用。验收是本地生产构建的自动化功能检查；没有生产部署或真人完成率结论。

## 仓库导航

```text
apps/api/              API、教学编排、受控核验与测试
apps/web/              Chat、共享工作区与交互组件
luojia-math-tutor/      Tutor Skill、知识说明与整理后的参考数据
evaluation/            协议、开发题、审核材料与评测合同
scripts/               评测与维护工具
docs/                  架构、学习设计、运行、评测与维护说明
```

开发约定见 [AGENTS.md](AGENTS.md)，文档归档与恢复见[维护说明](docs/maintenance.md)。历史提交保留，开发过程材料已从公开工作树收口。

## 已知限制

GS/Newton/积分共用探索计划、真实本地计算与历史恢复，私人历史可选择性进入新问题；见[R6.2/R6.3实施报告](evaluation/r62-r63-execution-report.md)。模型域选择与策略差异目前是fixture编排验收，此前真实模型小样本的问题仍未通过新一轮真实验收，见[R6.1报告](evaluation/r61-execution-report.md)。有限步骤检查不证明整道题；证明辅导依赖模型。课程资料的发布标记不等于独立数学审校。掌握度是教学策略输入，参考实验成功不能证明学生独立掌握。生产鉴权、数据库备份恢复与部署配置需要在目标环境验收，详见[限制与安全边界](docs/limitations.md)。

## License

项目代码采用 [MIT License](LICENSE)。外部教材和上传资料的使用仍须遵守各自授权。
