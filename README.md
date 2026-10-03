# 珞珈数智助教 · Luojia Math Tutor

<img src="apps/web/public/brand/luojia-logo.png" width="64" alt="珞珈数智 Logo" align="left" />

**把条件讲清，把过程算明。**

陪你读教材、做数值实验的 AI 数学助教。当前学习工作区聚焦**非线性方程求根：二分法、不动点迭代与 Newton 法**；对话同时保留高等数学、线性代数与概率统计的辅导入口。

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Next.js%2016-40513b)](apps/web/package.json)

[功能与学习路径](#功能与学习路径) · [快速开始](#快速开始) · [验证与评测](#验证与评测) · [当前边界](#当前边界) · [规划与交接](#规划与交接)

## 快速开始

以下命令适用于 **Windows / PowerShell**，从仓库根目录执行。CI 使用 Node.js 24、Python 3.12；前端声明 Node.js ≥20.9，后端声明 Python ≥3.10。建议使用项目虚拟环境安装 Python 依赖。

### 1. 安装依赖

```powershell
npm.cmd ci
npm.cmd --prefix apps/web ci
python -m pip install -e ./apps/api
```

### 2. 配置本地环境

仅在文件不存在时复制示例，保留你已有的配置：

```powershell
if (!(Test-Path apps/api/.env)) {
    Copy-Item apps/api/.env.example apps/api/.env
}
if (!(Test-Path apps/web/.env.local)) {
    Set-Content apps/web/.env.local 'NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000'
}
```

编辑 `apps/api/.env`，让 `LLM_PROVIDER`、`LLM_BASE_URL`、`LLM_MODEL` 和 `LLM_API_KEY` 对应你的模型服务。完整设置见 [.env.example](apps/api/.env.example)。密钥与数据库均不应提交。

没有模型密钥时，受控求根实验、过程诊断、章节参考自检和静态代码审阅仍可使用；模型聊天、模型伴读解释等能力需要有效配置，不能把无模型的来源对照当作模型生成。

### 3. 分别启动两个终端

终端 A：

```powershell
npm.cmd run dev:api
```

终端 B：

```powershell
npm.cmd run dev:web
```

打开 [本地首页](http://localhost:3000)，API 文档位于 [本地 Swagger](http://127.0.0.1:8000/docs)。根目录的 `dev:*` 与 `npm test` 脚本使用 `npm.cmd`；其他系统请在 `apps/api` 手动启动 uvicorn，在 `apps/web` 使用 npm 启动前端。

### 4. 选择账号或本地演示

本地示例为 `APP_ENV=local`、`AUTH_REQUIRED=false`，未登录请求使用演示身份。注册账号为 3–64 位字母、数字或 `_.@-`，首字符为字母或数字；密码至少 10 个字符。登录或注册成功后进入今日学习。

账号凭证保存在当前浏览器。退出清除本地凭证并卸载当前页面，保留本地学习草稿；**尚未提供密码找回、邮箱验证、令牌刷新或服务端会话撤销**。

## 功能与学习路径

<img src="apps/web/public/brand/xiaoluo.png" width="160" alt="小珞：手持教材与笔的 AI 数学学姐形象" align="right" />

**小珞**是珞珈数智的 AI 助教形象：数学学姐的交流风格，陪你辨清公式条件、观察迭代过程、解释自己的理解。首页使用全身立绘，聊天欢迎区使用缩小布局。

从一项任务开始：**读材料 → 做实验 → 提交自己的过程 → 确认反馈 → 换题检验 → 到期复习**。系统生成的实验轨迹是参考帮助；你自己的提交和独立检验分别记录。

| 功能 | 页面 | 当前可以做什么 |
| --- | --- | --- |
| F1 今日学习 | `/study` | 安排 15/30 分钟任务，继续跨日未完成记录，提交求根轨迹、确认反馈、换题检验与间隔复习。反馈待确认时防止覆盖提交。 |
| F2 教材伴读 | `/reading` | 阅读课程摘录或自己的已上传材料，核对适用条件、选择原文段落提问，把摘录和问题保存为带来源的笔记。 |
| F3 求根实验 | `/lab` | 先预测再运行三类受控参考算法；逐步查看、播放/暂停轨迹，对照历史实验，记录本地复盘。 |
| F4 章节自检 | `/assessment` | 六道开发参考题；草稿恢复、题号导航、首次作答确认，交卷后查看参考解析和复习入口。 |
| F5 讲给助教听 | `/teach-back` | 用自己的话解释条件，将原句对应到条件，保存补充版本；模型可用时提供明确标注的审阅意见。 |
| F8 数值代码作业 | `/code-workshop` | 限定 Newton 作业的 Python AST 静态审阅、代码行定位、保存版本对照；手动轨迹单独诊断。**学生代码不执行。** |

F6 视频伴学与 F7 教师简报仍在规划，见[扩展功能与启动条件](planning/learning-experience-2026-10/04-extensions.md)。

已有的对话助教 `/chat`、错题本 `/mistake-book`、随堂笔记 `/notebook` 和课程图谱 `/graph` 继续保留。默认给予适量提示；直接讲解或明确请求完整解答时可给完整过程。练习出题与答案披露分别处理。

## 一个可复现的体验例子

1. 打开求根实验，选择“牛顿法：0 → 1 → 0 循环”。写下对 `f(x)=x³−2x+2`、`x₀=0` 的预测，再运行参考实验。
2. 用滑块、前后步按钮或播放观察循环。把初值改为 `−2`，写下新预测，保持函数、目标和阈值一致后运行，再对照两次记录。
3. 在教材伴读选择牛顿法，核对“初值足够接近根”等条件，将所选原文加入笔记。也可以到讲回页面解释这些条件。
4. 在今日学习提交**自己计算**的指定轨迹和停止依据，读完反馈后确认结果。练习成功可以换题检验；独立检验期间，已接入保护的聊天、伴读解释、参考实验等入口阻止新的帮助请求。
5. 用章节自检复习条件与误差判断，或进入代码作业修订模板。章节参考分、静态提示和手动轨迹都不等于已证明掌握。

小残差、相邻差小与根误差小是不同判断；一次数值实验也不能证明一般收敛。

## 实现与证据边界

```mermaid
flowchart LR
    Student[学生] --> Chat[对话请求]
    Student --> Workspace[学习工作区]
    Chat --> Policy[意图与答案披露策略]
    Policy --> Context[课程检索与历史上下文]
    Context --> Check[按需符号检查或模型审阅]
    Check --> Answer[流式回答与逐消息检查状态]
    Workspace --> Root[受控求根轨迹与规则诊断]
    Workspace --> Source[原文范围与来源哈希]
    Workspace --> Code[代码静态解析与版本记录]
    Root --> Feedback[反馈确认与练习结果]
    Feedback --> Probe[新题独立检验与复习安排]
    Answer --> Store[持久记录]
    Source --> Store
    Code --> Store
    Probe --> Store
```

- **对话**：LangGraph 按请求调用教学策略、课程检索、受限 math/SymPy 工具或模型审阅。工具执行成功只说明计算代码运行成功；模型审阅仍是意见，不能把整段解释标成数学证明。
- **求根过程**：受控表达式解析、轨迹诊断与 RootEpisodeService 分开处理更新、停止依据和反馈确认。系统参考实验不计为独立完成；未知结果不计成功。
- **材料**：课程知识包与个人上传原文分别呈现。选段保留字符范围与来源哈希；抽样生成的教材笔记明确标注覆盖限制。
- **学习记录**：SQLite 保存会话、课程与学习任务。BKT 后验是基于观测和参数的估计，复习阶段是调度规则；二者都不替代无 AI 的迁移测验或延迟保持证据。
- **帮助保护**：未完成的独立检验阻止应用中新请求的讲解、参考实验等帮助；历史内容和外部工具不能据此排除。

### 存储与配置

| 配置 | 作用 |
| --- | --- |
| `DATABASE_URL` | 主应用数据库，默认使用 SQLite。 |
| `COURSE_STORE_PATH` | 显式指定课程与学习工作区持久库；路径相对 API 工作目录。文件 SQLite 未指定时派生 `<数据库路径>.course.db`；内存库不保证重启恢复。 |
| `AUTH_REQUIRED` / `AUTH_TOKEN_SECRET` | 控制鉴权及令牌签名。生产环境要求鉴权与独立配置的签名密钥。 |
| `LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` | 服务端模型配置。 |
| `ALLOW_USER_API_KEY` | 是否接受当前请求转发的用户模型密钥，示例默认关闭。 |
| `MINERU_API_KEY` | PDF/Word 上传解析配置；课程摘录与已有 Markdown 伴读不要求重新上传。 |
| `NEXT_PUBLIC_API_BASE_URL` | 前端访问后端的地址，构建时注入。 |

任务、答案和保存版本由服务端控制；未确认选项、实验复盘及部分编辑草稿保存在当前浏览器，不能承诺跨设备同步。生产部署需要同时配置 `APP_ENV=production`、`AUTH_REQUIRED=true`、独立随机签名密钥和明确的 `CORS_ORIGINS`；本地演示配置不能直接作为线上配置。

### 搜索与图示

聊天联网检索支持自动、开启和关闭。搜索摘要是来源线索，不等于全文核实或证明验证。逐轮检索状态与来源保存在消息元数据中；旧回答不补造检索记录。

公式与静态图示用于辅助理解。完成的动态 HTML 可主动运行于独立 iframe，并可停止/重启；禁止外联和父页面 DOM 访问，30 秒定时卸载。**该定时器不能保证强制终止同步 JavaScript 死循环**；动态预览不进入数学验证或学习计分。

## Agent 工程可靠性

聊天请求先确认任务，候选回答通过交付检查后再发送。可疑表述最多进行一次纯文字修复；仍不通过、模型截断或流异常时给出安全失败回执，不能标成完整答案。交付 Guard 检查显式协议 / 执行声明和练习答案标签；**检查通过不代表数学正确**，间接语义仍待评测。

每轮生成 UUID 执行记录，保存有限公共步骤和终态，回答与终态在同一 SQLite 事务中提交。聊天旁可折叠回看过程；浏览器停止生成会触发服务端图任务与工具清理，刷新可恢复取消 / 中断记录。过期运行只标记 interrupted，不自动重放。缺少 provider usage 时保存 null，不推算成本。

新增 schema migration 6，已有部署启用前应使用 SQLite backup API 备份实际数据库；代码回滚保留新表。设计、回归和限制见 [A0–A2 交付回执](planning/agent-engineering-2026-10/delivery-a0-a2.md)，后续见 [Agent 工程规划](planning/agent-engineering-2026-10/plan.md)。独立评测 CLI（A3）和真实模型质量对照（A5）尚未完成。

## 验证与评测

截至 **2026-10-03**，本地代码交付验证为：知识 JSON 通过，**API 559 项、前端工具测试 43 项通过**；生产构建和类型检查通过，lint **0 错误、10 条原有警告**。隔离演示库完成学习任务、草稿/版本恢复、实验交互和手机布局检查。详细回执见[学习体验审查](planning/learning-experience-2026-10/xiaoluo-chat-lab-review.md)与[实施记录](planning/learning-experience-2026-10/implementation-notes.md)。这是工程验证，不是教师验收或真人学习效果评测。

Windows 根目录：

```powershell
npm.cmd test
npm.cmd run test:knowledge
npm.cmd run test:api
npm.cmd run test:web:ui
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
npm.cmd run build:web
```

构建前先停止正在服务的 Web 开发/预览进程，避免 `.next` 被同时写入。`pytest` 必须从 `apps/api` 运行；离线测试门控会禁用 dotenv 和真实模型密钥，不应移除。

仓库保留[LuojiaMathBench V8 样本](data/LuojiaMathBench_v8.jsonl)及[旧评测归档](evaluation/report_v5_archive.md)。旧 README 报告过 20 条 V8 样本的教学合规率 90% 和直接答案泄露率 5%；这些是**历史运行结果**，本轮未重新运行模型评测，不能作为当前求根工作区的效果或泛化结论。逐样本结果生成在忽略的 `results/`，干净克隆不包含这些运行文件。

## 当前边界

- 交付 Answer Guard 已覆盖显式规则及一次修复，数学语义尚未形成覆盖全部回答的闭环；不能承诺“绝对正确”或“零幻觉”。
- F8 的学生代码隔离执行环境（C0）尚未验收，首版仅作静态审阅；支持的手动轨迹不能证明程序运行正确。
- F4 为开发版章节参考练习；F5 原句对应与模型意见都不直接增加独立成功。
- F1 仍以受控 Newton 任务为主，F2 仍是课程摘录与 Markdown 原文伴读；完整 PDF 标注、跨设备草稿、完整教师后台仍待实现。
- 密码找回、邮箱验证、服务端会话撤销、真实模型质量、教师核对及真人学习效果仍需后续验证。

## 项目结构

```text
apps/api/app/api/                # FastAPI 路由与鉴权入口
apps/api/app/tutor/              # 教学编排、求根任务、伴读及代码静态审阅
apps/api/app/knowledge/          # 课程图谱、持久记录与复习策略
apps/api/app/math_tools/         # 表达式解析、求根诊断与参考轨迹
apps/api/tests/                  # 离线后端回归测试
apps/web/app/                    # 首页、对话、六类学习入口与账号页面
apps/web/components/learning/    # 共享学习界面与轨迹回放
apps/web/lib/                    # 请求、输入校验与前端工具测试
apps/web/public/brand/           # 用户提供的 Logo 与小珞立绘
luojia-math-tutor/               # 助教 Skill 与课程参考资料
planning/learning-experience-2026-10/ # 六个月功能规划与实施回执
scripts/                        # 评测、数据校验与维护脚本
results/                        # 本地生成证据，不跟踪
```

## 规划与交接

- [六个月功能规划](planning/learning-experience-2026-10/README.md)：F1–F8 的范围、启动条件与主线衔接。
- [F1–F4 首版](planning/learning-experience-2026-10/f1-f4-delivery.md)、[首页及 F5/F8](planning/learning-experience-2026-10/home-f5-f8-delivery.md)、[小珞与流程加强](planning/learning-experience-2026-10/xiaoluo-chat-lab-review.md)：实现与验收边界。
- [M0/M1 课程图谱](COURSE_GRAPH_M0_M1.md)、[M2/M3 求根过程](COURSE_GRAPH_M2_M3.md)：课程与研究主线。
- [分支日志](luojia_tutor2_branch_log.md)、[研究规划](luojia_tutor2_course_graph_research_refined.md)、[交接文档](CODEX_HANDOFF.md)、[贡献约定](AGENTS.md)。
- [海报更新提示词](planning/learning-experience-2026-10/poster-update-prompt.md)：现有视觉材料的更新说明。

## 项目海报

![珞珈数智助教新版海报：小珞、Newton 迭代示意与六项学习功能](LJ_Tutor_Poster.png)

新版海报展示小珞、求根实验与六项学习入口；实验面板为静态示意，功能范围与验证证据以上文为准。

<details>
<summary>查看第一版海报</summary>

![第一版珞珈数智助教海报，保留历史视觉设计](v1poster.png)

第一版保留为历史归档。图中的性能数字、绝对验证措辞和旧功能排列不作为当前能力说明。

</details>

## 许可证

核心代码、脚本及 Skill 配置采用 [MIT License](LICENSE)。教材文件和引用材料遵循各自的授权范围；仓库代码许可证不自动授予教材内容的使用权限。

### 离线 Agent 可靠性评测

运行 `python scripts/eval_agent_reliability.py`，结果保存为 `results/agent-reliability.json`（不跟踪）。版本化 19 个协议合同、40 个参数化实例覆盖生成异常、工具清理、交付 Guard、数据库原子性和 owner 隔离。报告保留分子 / 分母、Git SHA、案例与源码哈希；这是离线 fixture 协议评测，不是模型准确率。CI 同步执行并上传报告。
