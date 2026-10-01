# CODEX 交接文档

> 最新交接：2026-10-01。写给要接手本仓库的 Codex。M0/M1 最新实测见研究文档 §27.8 与 `COURSE_GRAPH_M0_M1.md`；长期推进继续以 §27 为准；本文下方按日期保留历史工作记录。

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
