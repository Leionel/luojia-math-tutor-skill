# CODEX 交接文档

> 最新交接：2026-10-03（用户新版海报接入、v1 归档）。写给要接手本仓库的 Codex。M0/M1 最新实测见研究文档 §27.8 与 `COURSE_GRAPH_M0_M1.md`；诊断/研究主线见 §27，新增功能规划见 §28 与下方入口；本文下方按日期保留历史工作记录。

## 2026-10-03 新版海报接入与 v1 归档

用户自行生成并提供新版海报，明确要求原图改名为 `v1poster`。根目录 `LJ_Tutor_Poster.png` 已替换为附件原始 PNG，旧图原样归档为 `v1poster.png`。两图均为1055×1491，哈希分别与附件/替换前原图一致；未重绘、压缩或修改品牌素材。README 直接展示新版，第一版放在折叠历史区；交付哈希与提示词见 `planning/learning-experience-2026-10/poster-update-prompt.md`。

新版可见六项功能、Newton 示意轨迹和“代码未执行”；图中控件是静态示意。文件哈希、文档链接与 diff check 通过；业务源码、配置及冻结研究数据未改。本轮离线 npm test：知识 JSON、API469、Web40 全部通过，日志 results/poster-asset-update-tests.log；提交/推送回执单独报告。以下上一轮生图失败/未替换的记录保留为历史，不代表当前海报状态。

## 2026-10-03 README 与海报交接

README 已按当前 F1–F5/F8 六入口重写：Windows 快速开始、现有环境文件保留、模型配置、账号边界、可复现 Newton 循环例、受助/独立证据区分，以及静态代码审阅限制。修正 `.env.example` 关于课程库默认只在内存的旧注释；配置值与业务代码未改。历史 V8 20 条评测与当前求根功能、工程测试分开说明。

本轮 `npm test` 重跑通过：知识 JSON、API469、Web40；日志 `results/readme-update-tests.log`。文档相对链接检查无缺失，循环与收敛示例已离线核对，diff check 通过。未从干净环境重装依赖，未重复生产构建或真实模型/教师/学生评测。

海报提示词见 `planning/learning-experience-2026-10/poster-update-prompt.md`，完整及精简请求分别保存为相邻 txt。内置 imagegen 两次网络失败，第三次精简请求按用户“我来”停止；没有生成或替换海报。旧 `LJ_Tutor_Poster.png` 与原品牌素材保留，README 将旧图明确标注为历史设计。用户自行生成后再按提示词核对中文、Newton 轨迹与“代码未执行”，不能直接声称图片已验收。

此前四批提交 `047f134`、`f875b3e`、`381c0d6`、`65ece36` 已推送，本轮 fetch 核对 HEAD 与远端 `feature/course-graph-2.0` 一致。本文下方历史“未push”只说明当时状态。本轮文档提交与推送结果单独报告；不包含既有原型、egg-info、ignored results、数据库或 env。远端 CI 与部署未验证。


## 2026-10-03 小珞、教学流程审查与 F1–F4/F8 加强

用户授权加入数学学姐形象“小珞”、检查明显不符的流程/设定/提示并直接修复，随后授权在五小时额度耗尽前继续加强薄弱处。本轮原样接入小珞 PNG 到首页/聊天欢迎区，明确 AI 身份；统一独立 probe 的新帮助保护（普通聊天/笔记/相似题/求根提交），保存每条回答自身教学模式和检查状态，修正模式与任务意图冲突、相似题未持久保存、抽样教材笔记全书措辞及提示数据边界，新增根主题开发参考题。teaching-v2.4；计算执行与数学语义验证明确分开。

F1 反馈待确认时锁定输入和新提交，保留幂等重试；F2 原文段落追加笔记草稿且刷新恢复；F3 逐步/播放/暂停/同条件轨迹对照/历史回看与按实验保存的本地复盘；F4 未确认选项按 owner/测评恢复、题号导航与确认进度；F8 已保存行号定位、未提交修改提示、两版原文对照、tol/max_iter 使用与 solve 本体作用域静态检查。学生代码仍不执行，提示/手动轨迹不提升独立成功。无新增表/依赖。

本地最终 npm test：知识JSON/API469/Web39；生产build及TypeScript通过；lint0错误/10原有警告；diff check通过。浏览器在隔离演示库验证五类增强、首页与聊天形象，以及390px实验布局；未调用真实模型。日志 results/f1-f4-f8-strengthened-*.log。完整审查、修复与剩余弱项见 planning/learning-experience-2026-10/xiaoluo-chat-lab-review.md。真实模型/教师gold/真人学习收益/C0/C1/远端CI未验证。数学语义Answer Guard及动态HTML同步JS的CPU强制隔离仍未闭合；历史内容/外部帮助无法由当前应用保护排除；完整PDF标注、跨设备本地草稿与静态规则版本回执后续再做。未commit/push/deploy，保留原工作区成果与无关原型。额度读数91%时结束新功能扩展并收尾。

## 2026-10-02 首页与F5/F8（上一轮回执）

用户继续授权更新首页、加强F1–F4，并启动F5和F8首版。首页接入只读owner概览、六入口、真实任务恢复与参考测评；中文衬线排版、数学示意与减少动画适配。F1找回计划外/跨日未完成检验；F2笔记按原文章节过滤；F3参数/预测草稿及实验链接恢复；F4当前测评/结果链接恢复。详见 `planning/learning-experience-2026-10/home-f5-f8-delivery.md`。

新增learning_extensions：F5文字讲回、引用原句/来源哈希/补充版本，模型意见明确未核验；无模型可自我对照。F8限定Newton静态审阅、手动轨迹独立诊断与前后版本比较。没有C0隔离回执，因此不执行学生代码，旧code_executor未放宽。F5/F8帮助受首次独立probe保护，不更新独立成绩。复用learning_records，无新增数据库表或依赖。

本地npm test：API458/Web35/知识JSON通过；生产build与类型检查通过；lint0错误/10原有警告。浏览器使用隔离演示库；真实模型/教师核对/学生试用/C0/C1/远端CI未验证。预览 localhost:3000 首页、8000 API，仍用 results/f1-f4-ui*.db 和LUOJIA_NO_DOTENV=1。未commit/push/deploy，既有原型/egg-info等文件保留。

用户提供透明PNG Logo已原样接入首页、学习工作区、对话品牌区与浏览器图标，复用BrandLogo，原图SHA256一致。资产apps/web/public/brand/luojia-logo.png。

## 2026-10-02 F1–F4首版（上一轮回执）

用户授权先做F1–F4，并授权自检后升级。今日学习/教材伴读/求根实验/章节诊断已接入，聊天顶部“今日学习”进入；交付范围与后续门槛见 `planning/learning-experience-2026-10/f1-f4-delivery.md`。新增LearningWorkspace、受控root_runner、source-bound explanation与learning_records；runtime课程库默认随文件SQLite派生持久库，显式COURSE_STORE_PATH优先。旧段落“无配置即内存”只保留作历史基线。

本地npm test API445/Web34/JSON、typecheck/build通过；lint0错误/10既有警告。390px/1440px浏览器核心流程、恢复和弃测通过，results/f1-f4-*为隔离演示证据。参考题计分不是研究成绩，真实模型、教师gold和学生试用未验证；旧版本任务恢复/完整PDF标注/独立研究测验未完成。没有commit/push/deploy；保留既有原型/egg-info等无关工作区文件。

## 2026-10-02 功能规划入口（仅规划，优先读取）

用户要求在竞品建议基础上形成详细规划，选择融入现有六个月数值分析主线，并希望利用AI加速、不提前删除后续功能。已形成[总规划](planning/learning-experience-2026-10/README.md)：F1今日任务/间隔复习、F2教材伴读、F3数值实验优先，F4章节小测、F5讲回、F6视频伴学、F7教师简报、F8代码作业全部细化；七份文件含基线门槛、核心分计划、后续任务与实施记录模板。

下一步从B0核对现有求根WIP开始：本轮源码已存在root_expression/root_finding/root_diagnostics、前端输入/反馈卡及probe/ack/replay，不能重复实现，也不能仅凭文件存在宣称M2/M3已验收。核对过程含数学参考、10条episode、交付/幂等/权限/公开答案边界，以及根前端测试与CI清单差异。F2可在材料身份/授权/版本确认后先做，F1成绩与F3诊断依赖B0通过。

目标窗口2026/10–2027/03；沿用每周约3开发日的未确认估算，58–85开发日加返工余量。AI节省比例、教师档期、招募、字幕与隔离运行环境均未实测；按两周实际完成量校准。研究冻结版与候选功能隔离，独立学习结果不由受助成功/自动实验/模型讲回评价替代。

本轮仅写规划与项目记忆，未主动修改业务代码/正式数据/冻结题集，未运行应用测试或构建，未commit/push/deploy。后续偏离与验收写planning/learning-experience-2026-10/implementation-notes.md，并回写三份项目记忆。

## 1. 这是什么项目

**珞珈数智助教**（`luojia-math-tutor-skill`）：面向大学数学（当前主攻《数值分析》教材）的 AI Tutor，后端 FastAPI + LangGraph（`apps/api`），前端 Next.js 16.3.8 + React 19.3.0 + Tailwind（`apps/web`），教学规则与知识数据在 `luojia-math-tutor/`。当前工作分支 `feature/course-graph-2.0`（未合回主分支），远端同名。

构建/测试命令、代码风格、提交规范见 `AGENTS.md`，全部仍然有效。关键差异提醒：

- `pytest` **必须在 `apps/api` 目录下跑**（仓库根目录跑会收集到无关文件报 36 个 collection error）。
- 测试离线由 `LUOJIA_NO_DOTENV=1` 保证（`tests/conftest.py` 会清掉 LLM/MINERU key），别破坏这个机制。
- **不要在 dev server 运行时执行 `next build`**（会写坏 `.next`）。
- 提交时 CRLF 警告属正常（Windows 环境）。

## 2. 必读文档（按顺序）

1. `luojia_tutor2_branch_log.md` —— 本分支自 split 以来所有轮次的实测记录 + 「尚未处理的问题」清单（§6，部分已划掉表示已修）。
2. `luojia_tutor2_course_graph_research_refined.md` —— **先看 §27 最新推进计划**，再看 §26 接手缺陷、§25 历史检索基线、§24 改造方案。244 题 retrieval eval 与 228 题 Case eval 分开报告。
3. `results/retrieval_eval_results.json` —— 最新评测数字；`evaluation/retrieval_eval.json` 是评测集。

## 3. 当前状态（截至交接）

- 教材链路（上传 → MinerU 解析 → 结构感知切分 → 候选抽取 → 审核台）端到端可用；`apps/api/luojia_tutor.db` 存 1 本教材（`doc_656067dd6720`，32 万字，430 chunks，CJK bigram 索引）。
- 检索基线（`scripts/eval_retrieval.py`，244 条评测集）：chunk 级 BM25 **R@3 0.752 / R@5 0.798 / MRR 0.708**，vector（本地 LSA 降级臂）0.581/0.685/0.498，hybrid(RRF) 0.688/**0.805**/0.657；**图层 unit 级 dry-run R@3 0.725，hierarchy@1 = 0.867**（详见 research doc §25.3）。
- 前端已统一到「农场水墨」设计令牌（`apps/web/tailwind.config.ts` 重映射了 slate/indigo 等默认色名——**改 UI 时注意类名颜色≠视觉颜色**）；阅读字体（衬线/无衬线）与主题（light/dark，存储键 `luojia-theme`/`luojia-reading`）持久化已修好。
- 交互与思考链优化：消除白屏等待大卡片，采用极简折叠墨绿书卷徽标；输入台新增「🌐 联网探微」与「🧠 运思强度」（4档深度映射至 DeepSeek/OpenAI/Qwen/GLM/Anthropic）；新增藏书阁「Ctrl+K」全局跨域检索抽屉（教材定理/错题/笔记一键研讨）。
- 最新本地验收：API 329 项、前端 20 项与知识 JSON 通过；生产构建/typecheck 通过，lint 0 错误/10 条已有警告；前端依赖审计 0 漏洞。未运行远端 CI，离线隔离门控未变。

## M0 / M1 最新状态（2026-10-01，本段优先于下方历史记录）

M0 已实现完整 SQLite 正式图、事务审核、generation CAS、幂等回执、备份/恢复工具；M1 已接入生产 Case / 单元召回，API、EvidenceBuilder、离线 evaluator 排序一致。228 题开发集 R@1=162/208（77.9%）、R@3=200/208（96.2%）；原20题通过，61题仍需审查。教师 gold 与未见任务验收待完成，M2 尚未实施。

实际 API 库为 `apps/api/data/course_store.db`，初始化正式快照后仍 pending495 / superseded283，没有批量审核。数据库备份与完整验收见 `COURSE_GRAPH_M0_M1.md`；持久化须配置 COURSE_STORE_PATH，未配置为内存模式。先教师核对失败家族和少量求根材料，再推进受控数值诊断、提示与修订重验；不要继续盲目扩题或扩章。以下旧段落保留为基线证据，不是当前完成状态。

图谱 UI 最新方向：参考 Obsidian Graph View，采用圆点/细线的有界力导向布局，关联数量决定大小，悬停/选择突出邻域，公式/内容在侧栏。窗口尺寸变化自动适配，选择不重载图，拖动不强制回位；卡片网格方案未提交。新增3项布局回归，最新API329/Web20。完整记录与截图入口见 COURSE_GRAPH_M0_M1.md 追加段。

## 4. 明确的未完成项（按优先级）

> **2026-10-01 优先级：以研究文档 §27 为准，§26 保留缺陷证据。** 大批审核前先修正式图持久化与审核事务；随后接生产 Case/单元召回，再推进受控数值 Oracle、提示、修订重验和最小事件链。临时库已复现：approve 后单元存在，重建服务后候选仍 approved、单元消失。`hierarchy@1=0.867` 来自 pending 的独立排序 dry-run（13/15），审核入图不足以自动保证生产复现。种子包实际为27 units、21 relations、15 Cases；Overlay是证据计数层，聊天尚未自动写入该层。

> **228题v2 benchmark已交付：** AGY网络失败后，按用户要求由GPT-6 Luna实施、主代理复核。见 `evaluation/CASE_BENCHMARK_V2.md`：Case Recall **11/208 (5.3%)**、严格决策 **34/222 (15.3%)**、域外 **10/11**、域内新Case **7/7**；204题至少一项不匹配、工具异常0。原20题仍为Case16/16、可接受决策集合20/20、域外4/4；原gold是多标签，不能称严格决策全对。原题集/种子包/matcher哈希保持，正式库和审核状态未改。最终npm test：API265、前端12、知识JSON通过。新集尚需教师抽查，下一轮优先修审核持久化/事务，再改Case召回与生产图检索。

1. ~~vector/hybrid 评测两行空~~ **已补（2026-09-30）**：无 key 时用本地 TF-IDF+LSA(k=256) 降级臂出数；拿到 `DASHSCOPE_API_KEY`（写进 `apps/api/.env`）重跑 `scripts/eval_retrieval.py` 即得真神经向量水位——hybrid R@5 已是全场最高（0.805），换强向量臂后 R@3/MRR 大概率跟涨。
2. ~~hierarchy 要走图层~~ **已补（2026-09-30）**：评测加了图层 dry-run 臂（加权 IDF + 标题×3/关键词×2 + sqrt 归一），**hierarchy@1 = 0.867**。注意这是拿 495 条 pending 当 approved 代理测的；生产里 `CourseEvidenceBuilder` 只认已审核单元，所以**审核入图是把 0.867 变现的前提**。
3. **LLM 答题质量 baseline 缺失**：README 的 `90.0% (18/20)` 没有裸模型参照系（branch log §6.1）。
4. **候选审核仍待推进**（`data/course_store.db` 的 `graph_candidates`，495 条是 9 月 30 日快照）：先通过 G0 的持久化/事务验收，再少量试审求根材料。审核数量与历史 dry-run 分数不等于生产召回效果。
5. ~~无 CI~~ **已加（2026-09-30）**：`.github/workflows/ci.yml` 三 job（api pytest / knowledge JSON 校验 / web tsc+单测+build）。**部署仍无**。
6. 浏览器「上传」按钮的真实点击从未测过（链路其余环节都是 curl/API 实测的）。
7. ~~Desmos 正式 key~~ **已配置（2026-09-30）**：正式 key 在 gitignored 的 `apps/web/.env.local`（`NEXT_PUBLIC_DESMOS_API_KEY`），勿提交；缺 key 时模态框有空态兜底。

## 5. 关于最近两个提交的诚实声明

`ba55797`（glassmorphism 风格 UI）和 `0b035d8`（公式块复制交互、探索快捷问句）由另一个 AI 完成，**我没有审查过它们的正确性**。已知风险：glassmorphism 的新样式可能与 `tailwind.config.ts` 的农场水墨令牌重映射打架（类名写着别的颜色，渲染出来是令牌色），接手后如发现视觉不一致，先查这两处。

## 6. 安全红线

- `LLM_API_KEY` / `MINERU_API_KEY` 只存在于 gitignored 的 `apps/api/.env`；`NEXT_PUBLIC_DESMOS_API_KEY` 在 `apps/web/.env.local`。**永远不要把它们写进任何被跟踪的文件**；提交前 `git grep "sk-"` 检查。
- MinerU token 90 天过期，上传报 401/403 就是过期了。
- 教材模型输出、上传文件、候选 payload 都按不可信输入对待：走现有 sanitizer（`lib/html-sanitize.ts`）和表达式解析器，不要裸渲染 HTML。

## 7. 协作方式

- 提交信息沿用 `feat:/fix:/test:/docs:` 前缀 + 英文一句话，正文说清 why（看 `git log` 学样例）。
- 大改动先在本分支小步提交；UI 改动请附带 headless Chrome 截图佐证（`chrome --headless=new --screenshot=...`）。
- 文档（branch log / research doc）是本仓库的记忆，做完一轮必须回写，不许只留 commit message。

## 最新工作轮：Prompt重塑（2026-09-30，teaching-v2.1）

本节优先于上方历史测试数量与prompt状态。用户授权全部整改，详见 PROMPT_ARCHITECTURE_V2.md。统一系统规范与实际加载的三份指南；单一resolved_policy裁决；Case决策/条件/推理/来源传入；证明先审查；严格Verifier与评审schema；失败验算降级；图片真暂停、确认/编辑与草稿历史恢复；公开文案不虚称严格验证。当前验收：API294项、前端12项、知识JSON、tsc通过，lint退出0（现有警告）。测试进程设置SYMPY_GROUND_TYPES=python、MPMATH_NOGMPY=1绕开本机gmpy2本地扩展错误，离线门控不变。线上模型质量、真实上传点击、教师与学习效果验收仍未做；Case benchmark分数不可当本次prompt质量证明。已有服务需重启加载规范。未提交/推送/部署。


## 2026-10-01 — 响应式聊天 UI 与公式渲染修复

- 修复窄屏左右空白抽屉：Sidebar/LearningPanel 只渲染内容，由 MobileDrawer 统一控制显示、遮罩、关闭、焦点循环及跨断点恢复；桌面断点为 1024/1280px。
- 学习抽屉复用桌面状态/笔记内容，补齐移动端随堂笔记入口。顶部品牌/新会话避免换行，次要导航收进“更多”；输入区移动端取消常驻算子滚动条，简化工具文案，保持 16px 输入字体与底部安全区。中文 IME 确认不提交，粗指针设备 Enter 保留换行。
- 提取 message-parser.ts，修复同一行 $$…$$ 和 \[ … \] 的闭合处理，未闭合公式不吞后续空行/标题，保留代码与转义美元符号；加入 Markdown 表格渲染。原“膜振动方程”会话现已正常显示全部公式与后续标题，DOM 中 KaTeX 错误为 0。
- 学习面板取消未检查/无知识点时的默认 50% 展示，区分模型复核与本步检查；掌握度明确为估计。
- 验证：npm test（API 294、前端 17、知识 JSON 均通过）；tsc --noEmit 通过；lint 0 errors，原有 10 warnings。浏览器检查 320/390/768/1100/1440px、390x480 短视口，无整页横向溢出；Esc/关闭按钮/遮罩、Tab 焦点循环、跨断点关闭、移动端笔记切换与“更多”菜单通过。截图：results/ui-2026-10-01/mobile.jpg。
- 边界：未进行真实手机软键盘验证；开发服务器继续运行，因此未运行 next build；未提交/推送。框架仍为 Next.js 14.2.35。官方支持政策已将 14.x 列为不支持，建议后续独立迁移到 16.x 稳定补丁版，核对 React/API/lint 后再构建，不在本轮混入升级。

## 2026-10-01 — Next.js 16 升级

Next.js 14.2.35 → 16.3.8，React/React DOM 与类型依赖对齐 19.3.0，`eslint-config-next` 同步 16.3.8。lint 迁移为 ESLint flat config（ESLint 9.39.5；已有 effect/ref 用法保留兼容配置，React Compiler 未启用）。Next 16 自动调整 `tsconfig` 为 `react-jsx` 并加入 `.next/dev/types`；`next.config.mjs` 固定 Turbopack 根目录并关闭自动生成 agent 文件。新增 `npm run typecheck`（先 `next typegen`），CI 独立运行 lint，并纳入公式解析回归；README/AGENTS 同步 Node 与命令要求。

本轮先停 Web dev server 再构建，生产构建通过；完整离线 `npm test`：API294、前端17、知识JSON全部通过；typecheck 通过，lint 0 errors/10 条已有 warnings；`npm audit`（含开发依赖）与 `npm audit --omit=dev` 均为0漏洞。测试仅在进程内设 SYMPY_GROUND_TYPES=python、MPMATH_NOGMPY=1，conftest 门控不变。Next/React/ESLint 的最终安装树无 peer invalid。

服务已重启：Web `http://127.0.0.1:3000/chat`、API `http://127.0.0.1:8000/health` 均200；图谱页200。浏览器复核原会话48处公式、KaTeX错误0，390×844无页面横向溢出，左右抽屉有内容并可关闭；React Flow加载27节点/21关系，控制台error为0。截图 `results/ui-2026-10-01/next16-react19-mobile.png`。这不是手机软键盘或真实模型质量验收。未提交/推送/部署，未运行远端CI。

## 2026-10-01 — 长期推进计划（仅规划）

研究文档 §27 已保留用户引用的“可验证诊断闭环”判断全文，制定2026/10–2027/03详细时间线与2027/04–09条件性展望：G0恢复与审核事务 → G1生产召回 → G2 Newton错误/提示/修订重验与最小事件 → G3求根家族与Overlay → G4教师gold及冻结独立集 → G5试用 → G6协议 → G7学习效果 → G8复现与扩展决策。日期按约每周3个集中开发日估算，不是已确认产能；教师、招募及适用研究流程尚未落实。

228题已离线复跑：Recall@1 11/208、严格单标签决策34/222、可接受决策34/228、OOD10/11、域内新Case7/7、异常0；输出 `results/case_benchmark_2026-10-01_plan.json`，benchmark/种子/matcher哈希不变，执行退出0不表示基线通过。未实施计划中的业务改动。下一轮只先做M0：临时库重启恢复与审核失败原子性，正式库写入前备份与来源核对。

## 联网检索修复（2026-10-01）

用户实测“OpenAI证明Navier–Stokes的思路”没有联网资料，且新闻提问错误进入证明审查。旧实现默认手动关闭，DDG非200/解析空/超时统一丢成空列表，1.8秒HTTP预算与2秒上下文窗口不足，逐轮无搜索状态。

本轮加入auto/on/off（显式关闭优先，设置本机保存）、时效/明确搜索/机构证明声称及猜想状态路由、常见Navier拼写归一化；新闻解释不进证明审查或无关课程检索/异步embedding。应用统一负责检索，不依赖未实现工具执行循环的模型原生搜索。Tavily可选优先，DDG失败或空结果转Bing RSS；公共通道仅尽力而为。总预算10秒，本地0.35秒窗口独立；取消请求清理全部检索任务。

success/empty/error/timeout/disabled、提供方尝试、来源与耗时沿提示词→SSE→learning_meta.web_search持久化。成功仅表示拿到摘要，不核验全文、日期、证明或用户前提；失败不得转成“已查证不存在”。来源文本视为不可信资料，过滤非http(s)/带凭据链接。回答框显示状态与来源链接，旧历史不补造搜索记录，无数据库schema变化。

验证：npm test API345/Web20/知识JSON通过；build/typecheck通过；lint0错误/10原有警告。离线回归覆盖DDG202转RSS、Tavily空转备用、超时/取消、链接过滤、失败敏感信息隔离、显式off、普通证明保留审查、新闻不进审查、提示词/SSE/数据库状态一致。独立联网烟测同主题返回3条摘要（含OpenAI链接）；这不等于已核验网页内容或证明。未调用真实模型做本轮答复验收。浏览器验证三档、刷新保存、390px无横向溢出/控件48px；截图results/search-repair-{desktop,mobile}.png；日志results/search-repair-*.log。前端服务http://127.0.0.1:3000/chat，API8000已恢复。分批本地提交，未push/部署。

界面使用ui-design Build模式，读取SKILL、aesthetic-direction、design-guidelines、colors、form-controls、surfaces、responsive-design。下一任务：只读审查代码生成图标/HTML/图表嵌入回答框的触发、隔离、移动端及失败状态；M2受控数值诊断计划不变。

## 回答框图标、图表与HTML审查（2026-10-01）

联网修复已分三批本地提交：c566913后端/回归、8bfffa0前端模式/来源、64188a4交接。随后按用户要求只读审查嵌入链路，详细逐文件9项见ANSWER_EMBED_AUDIT.md。P1是默认HTML脚本执行无网络/资源策略、未闭合流式预览、1/x跨间断点连成假零点、模型缺前端可视化能力协议；P2是SVG被清空、块边界吞内容、固定400px函数图、iframe高度/主题/失败反馈、图片API写死localhost。现有表达式Parser/HTML白名单/iframe非同源隔离必须保留，不夸大成已证明的主站XSS。辅助函数复现证据results/answer-embed-audit-repro.json，MDN支持sandbox/CSP边界。审查没有修改渲染代码或执行攻击样例；下一轮若实施，先静态安全与完成态渲染、再artifact协议/提示词/移动端/分段曲线。

## 回答图示安全与展示修复（2026-10-01）

用户授权修复 ANSWER_EMBED_AUDIT.md 的9项并分批 commit/push。新增 visual-v1：静态 HTML/SVG 主动预览、闭合与生成完成双门控、空 iframe sandbox、CSP 禁脚本/外联、惰性 template 白名单（60KB/1500节点）；不扩大原宿主 sanitizer。SVG viewBox 自适应高度，HTML 手动有界高度、深浅主题、失败/源码回退；XML仅源码。图片复用统一 API 基址，协议/凭据过滤、来源/失败提示，外部图片点击后才加载。裸 HTML 根边界及 plot/bilibili 段落边界修复。

函数图保存 segments 并探测采样间隔，奇异点不跨段连线；响应式 SVG，范围内才画零轴，异常数值范围拒绝。间断检测仍为启发式，图示不能作为连续性/根存在性/证明证据。teaching-v2.2 加载 references/visual-artifacts.md，前端声明图形与后端 math/SymPy 验证能力分清。

离线 npm test：API346/Web26/知识JSON通过；build/typecheck通过；lint0错误/10已有警告。日志 results/embed-repair-*.log；浏览器临时独立预览验证静态清洗、无脚本沙箱、生成中0 iframe、XML源码、主题、390px无横向溢出，截图 results/embed-repair-{desktop,mobile}.png。临时路由已删除，未改真实会话、未调用真实模型、未做正式渗透验收。完整关闭项与限制见 ANSWER_EMBED_AUDIT.md 实施回执。

服务已恢复 Web3000/API8000。M2求根过程诊断闭环、独立教师gold与学习事件评估仍为后续主线，任意生成JavaScript不作为诊断Oracle。提交分为静态渲染安全、函数图语义/响应式、提示词协议、实施回执四批；推送结果以当前回合最终输出为准。

本轮实现提交：dfd8792 静态预览与生成门控；25ca8fb 分段函数图与响应式；e646c16 visual-v1 提示词协议。文档回执另批提交，用户已明确要求 push 当前分支。


## M2/M3 工程验收与动态 HTML（2026-10-02，本段更新已有求根 WIP 状态）

已完成求根受控 AST/导数/区间 Oracle、12 家族、Case→反馈→修订、事务事件与 Overlay、显示 ACK、提示预算、服务器独立探针、作用域重放。入口是聊天“求根过程验证”；实现与版本/范围见 COURSE_GRAPH_M2_M3.md，工程 fixture/manifest 见 evaluation/root_diagnostic_*.json。自由文字与任意代码不自动当作数值轨迹，教师逐题复核仍待完成，不宣布完整 G3/M4 或学习效果通过。

动态 HTML 已按用户要求恢复到 teaching-v2.3/visual-v2：完成态闭合 html 围栏、点击才运行、独立 allow-scripts iframe、无同源/网络/eval、Canvas/DOM/动画、错误/停止/重启/30秒定时卸载；宿主 sanitizer 未放宽。30秒不是同步死循环的 CPU 强杀保证，生成 JS 不进入 Oracle。原 SSE error 被忽略的问题也已修复，401/超时/EOF 明确失败，失败或取消不开放部分回答预览。没有改模型凭证或调用真实模型。

验收：npm test 知识 JSON/API415/Web30；production build/typecheck；lint 0错误/10既有警告；12家族13/13三元组；10条生产图/SSE固定episode及工具异常、取消、事务、权限、重启、重复回执回归。浏览器主聊天表单及动态图示390px无横向溢出，暂停/频率/错误/停止/重启/超时门控实测；临时验收路由已删除。日志与截图 results/m2-m3-*，正式论文 gold/真人/远端CI结果不由这些本地结果替代。

后续优先 M4 教师与数值/容差独立审计，再按长期计划做未见任务和无AI延迟保持；新增学习体验规划保留为独立文档工作，不在本轮业务提交中打包。服务恢复3000/8000；commit/push以最终回执为准。

## 2026-10-03 登录体验补查

用户指出登录系统未同步更新。当前Git历史显示真实Web鉴权接入于2026-09-08，后端后来有课程权限维护；本次没有重写鉴权协议。已修复聊天退出只跳转不清凭证：清除token/owner/演示键，完整跳转以卸载owner相关页面状态，保留学习草稿；桌面/手机均可退出。注册移除不保存的院校/专业，称呼/账号区分，账号格式与服务端一致，补齐label/自动填充。登录/注册成功进入今日学习。鉴权布局加入Logo/主题/首页返回，删除无依据的SECURE CONNECTION标语。

本轮前端40项通过（新增退出清理回归）、生产build/类型检查通过，lint0错误/10既有警告；后端未改，本轮未重复API suite，上一轮API469是之前的证据。截图results/auth-login-updated.jpg。没有实际注册/登录真实账号、密码重置或远端验证；当前isolated demo API没有配置token secret，不能以演示界面验证真实签发。剩余：密码找回、邮箱验证、服务端token撤销/刷新、过期引导与跨标签页状态；注册在签发配置缺失时先创建用户的非原子流程也需后续修复。未commit/push/deploy，五小时额度约94%时只做收尾。

## 2026-10-03 分批提交准备

用户明确授权分批提交并推送，按四个边界：后端学习与教学规则、学习工作区与品牌形象、登录体验、规划及交接记录。提交前重跑npm test：知识JSON/API469/Web40全部通过；最新auth-followup生产build与类型检查通过，lint0错误/10既有警告，diff check通过。git grep sk-检查仅发现说明文字/普通标识符/既有二进制匹配，新增源码/规划未检出匹配的凭证格式。既有egg-info、demo-jiuzhang-hybrid.html、style-explorer.html、ui-proposals、ignored results/数据库/env不纳入。

首版后端包含learning_records表、课程持久库派生路径和tzdata依赖；COURSE_STORE_PATH显式优先，离线测试门控保留。当前分支feature/course-graph-2.0。远端fetch首次因GitHub443连接失败，当前remote-tracking ref不是实时远端证据；推送将在提交后单独尝试并报告，本文不提前宣称已推送。


## 2026-10-03 Agent 可靠性修复与实习方向规划

用户要求参考成熟 Agent 项目提升工程能力，目标岗位为 AI 应用 / Agent 工程；随后要求修完后先交规划，已确认可靠性与评测优先。本轮只实施 A0：模型 finish_reason / EOF / 空正文 / 缺配置等 typed failure，不发送假 done；不确定意图在 context 学习写入前确认，仍未确定先澄清；最终 intent 重新选择核验模式；数学工具用类型化结果和退出码判断成功，取消 / 超时 kill、通信回收并清理脚本；缓冲时间改名 generation_buffer_ms。未增加依赖、数据库表或放宽 AST / F8 学生代码执行边界。

最终完整 npm.cmd test 退出 0：知识JSON/API501/Web40全部通过（API较上轮新增32项）；5条既有弃用/绘图警告。首轮两个旧API用例依赖缺配置文案当正常回复，已换显式离线成功fixture并补缺配置/无上下文澄清回归，生产未加fake。日志 results/agent-reliability-tests.log。diff check、规划链接及新增源码凭证格式扫描通过；前端源码未改，未重复build/lint。

规划入口 planning/agent-engineering-2026-10/plan.md，配套 audit.md / implementation-notes.md：A1有界交付Guard → A2本地持久执行回执 → A3离线失败评测为首个里程碑；A4任务快照与可纠正记忆、A5真实模型评测及求职展示随后。参考 LangGraph、OpenAI Agents SDK、Dify、Letta 官方文档，不迁移框架。后续A1–A5尚未实施，先供用户评审；完整数学语义Guard、学生代码C0、教师gold/真人学习收益、远端CI/部署未验证，已有回归通过不代替独立benchmark或真实模型质量。

限定聊天/服务端数学工具两surface的AX审查记录18检查、16唯一规则；12pass/1warn/1fail/4unknown，观测型缺真实交互保持unknown，未夸大整体发布验收。剩余缺口是正文/实际执行证据关联和记忆来源/纠正。六个月求根主线、独立probe帮助保护及原始事件/成绩权限不变。

实现025ec54已推送feature/course-graph-2.0并核对远端SHA；规划与交接另批，最终推送以本轮回执为准。之前12255a5是新版海报/v1归档已推送状态。仅提交清单内内容，保留无关egg-info、三个Web原型目录/文件以及ignored结果、数据库和env。

### 2026-10-03 A1 交付守卫

A0 45 项针对回归再次通过。A1 默认交付检查、一次文字修复、未通过候选拦截和 UI 证据边界已实现；全量 API537/Web41/知识 JSON、typecheck 通过，lint 无错误。检查通过不表示数学正确，规则首版是显式高精度模式，语义覆盖待 A5。用户已授权继续 A2 持久执行回执；构建/界面及推送将在集成验收后完成。

### 2026-10-03 A0–A2 Agent 工程实施结束

用户授权顺序实施；A0 已完成并复验，A1 5197ddf 交付检查 / 一次文字修复后继续 A2。A2 新 schema6 / run-v1 持久回执、原子消息终态、64事件上限、owner与seq条件更新、取消 / 重启过期、重试关联、折叠过程与刷新历史。ASGI断连有主动监听，取消会等待图 / 子进程和数据库写入清理；租约30s续租/120s过期，启动或读历史恢复过期记录，不自动重放。回滚保留新表，正式库启动前SQLite backup；本轮仅临时/隔离演示库迁移。

离线API559/Web43/知识JSON、typecheck、lint0错误10现存警告、生产构建通过；浏览器桌面/390px、修复/拦截/取消/刷新/键盘检查通过。所有run仅执行范围，交付守卫不证明数学正确；F8仍不执行学生代码，usage和未审定自定义模型别名为null。A3独立失败评测CLI未做，A4记忆/A5真实模型待实施。完整回执：planning/agent-engineering-2026-10/delivery-a0-a2.md。远端CI/部署/教师与真人学习效果未验收。

本轮代码提交：A1 `5197ddf`；A2 `f7c865a`。文档回执另批提交；远端分支以最终推送核对为准。

### 2026-10-03 A3 与多领域扩展

用户授权 A3 → 线性方程组 → 数值积分。A3 已新增版本化 manifest 和独立离线 CLI，19 个合同 / 40 个实例通过首跑；缺失、跳过、失败、重复实例不能绿色。CI 增加该命令及报告 artifact。复用实际图 / SQLite / 工具 fixture，结果限定为离线协议。多领域模块待实现，A4/A5 未实现。

A3 全量复验：知识 JSON、API 563 / Web 43 均通过（results/a3-full-tests.log）；报告解析器另覆盖缺失 / 重复 / 跳过 / 失败。无模型调用或部署。
