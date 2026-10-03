# 分支工作日志：`feature/course-graph-2.0` 相对 `main` 做了什么

> 面向后续接手本分支的人（人或 AI）。读完这份再动 `app/knowledge/**`、`app/tutor/graph.py`、`app/api/routes_notes.py` 或 `results/**`。
> 文中所有数字都由 `git log` / `pytest` / 真实教材实跑得出，不是从提交信息里抄的。
> 最近更新：2026-09-29。

## 0. 分支坐标

| 项 | 值 |
| --- | --- |
| 分叉点 | `251c680`（`git merge-base origin/main HEAD`） |
| 分支提交数 | 33 |
| 变更规模 | 80 files, **+15126 / −607** |
| HEAD | `73ea8ae`，与 `origin/feature/course-graph-2.0` 一致 |
| 时间跨度 | 2026-09-17 14:39 → 2026-09-29 22:53 |
| 测试现状 | `apps/api`：`pytest -q` → **256 passed, 0 failed**（离线，约 8s） |

一句话概括：把「数值分析课程知识图谱」从一份 2000 行调研文档落成可运行系统，然后**用一本真实的 150 页教材把整条链路跑穿**，把跑穿过程中暴露的缺陷逐个修掉。

## 1. 五个阶段

### 阶段 1 · 09-17 下午：Course Graph 2.0 落地（`baa95e1`→`eab71b1`，5 commits，≈ +10100 行）

把调研结论实现成代码：`case_schema`/`case_matcher`（Teaching Case 层）、`boundary`（判界）、`candidate_graph`（候选演化）、`student_overlay`（学生叠加层）、`course_store`/`graph_repository`/`graph_review`/`evidence_builder`；首套课程数据集 `data/course_packs/numerical_analysis_root_finding.json`（793 行）；前端 `/graph` + KaTeX（`math-view.tsx`）+ 暗色对比修正；`/admin/knowledge` 审核台。

**这一阶段产物量大但状态是"能跑"，不是"可信"**——后面四个阶段全是它的账单。

### 阶段 2 · 09-18 14:55：第一轮可靠性收口（`3990686`，24 files，+898/−296）

双真源 → 单一 SQLite `CourseStore`；删掉 `student_overlay` 里的第二套 mastery；`boundary` 改 fail-closed 并引入 `UNCLASSIFIED`；`auth` 加 `role` claim；`/api/courses` 改 typed 事件 + 幂等；审核写 `graph_revisions`；删伪 seed；前端统一走后端。

### 阶段 3 · 09-18 15:00–15:33：评测证据链 + verifier 硬关卡（`80171fc`、`f94c8b9`、`830b65a`、`4a2103d`）

- `evaluate_benchmark.py` 原来 `open(..., "a")` 追加写，导致 `results/v8_eval_results.jsonl` 120 行 = 同一批 20 个 id 叠了 6 次；且异常被 `print` 吞掉后仍把**空响应**送进评分器写成 `passed:false`。改为覆盖写、失败样本带 `error` 且**不进分母**、归档旧文件。
  - 注意：README 的 `90% (18/20)` **一直是对的**。任何人打开那个 jsonl 数一遍会得到 18/120 = 15%，从而误判成造假——这个坑踩过一次，别再踩。现在 `python apps/api/scripts/summarize_eval.py` 一条命令自证：20 行、90.0%、5.0%。
- README 三处零证据 claim 处理：G01–G04 表整表删除；两行 baseline 改「未评测 + 🚧 规划中」（`v7_baseline.jsonl` 是 0 字节）；举一反三文案改为如实描述静态题库并删掉零调用者的 `generate_exercise_prompt`；`report.md`（V5 代中途快照）改名 `report_v5_archive.md` 并加 superseded-by 头。
- 符号验证从软标注改硬关卡：`verify_lhopital_conditions` 原来三个分支全部 `verified=True`、`is_correct` 由文本含不含 `"0/0"` 子串决定；现在真用 SymPy 求分子/分母极限判型，解析不出则 `verified=False, is_correct=None`。`[VERIFY]` 原靠模型自愿输出（不打标 = 整轮零验证），现在缺标记触发**强制验算轮**。失败不再静默：输出加 `⚠️ 本轮未能完成符号验算` / `❗ 验证服务暂不可用` 前缀。
  - 图拓扑仍是 `add_edge("verifier", "teacher")`——关卡做在**输出变异 + 强制二轮**上，不在路由分支上。别误以为漏改。

### 阶段 4 · 09-19 上午：教材链路（`cacf765`、`5969486`、`9357acd`、`a19b392`、`0e732a0`）

MinerU v4 token 流程；模型配置改**供应商制**（`provider:model` / `custom:base|model` 前缀编码，8 个调用点零改动）；修掉 `repo.insert_document` **根本不存在**导致所有 PDF 上传静默失败、RAG 一直是空的；上传上限 10MB→200MB、超 200 页返回 413；笔记本与错题本各加「教材整理」入口；教材 → 图谱候选三段式流水线（`candidate_pipeline.py`）。

### 阶段 5 · 09-29：用真教材跑穿全链路并修掉暴露的缺陷（17 commits）

测试载体：吕锡亮《数值分析》讲义 PDF，**150 页 / 7.2 MB**，MinerU 解析得 **320,900 字符** markdown，121 秒。

**5.1 环境与可复现性**（`6d47ddc`、`29c0ede`、`4cced5a`、`ea93e8d`）

- 沙箱用 `subprocess [python, "-I", tmp]`，而 `-I` 隐含 `-s`，**排除 user site-packages**。依赖装在用户目录时 `import sympy` 必失败，所有 `[VERIFY]` 验算 100% 挂掉。改为 `-E -P`（保留隔离、去掉 `-s`）；缺失依赖改判为**环境故障**而非"学生代码错了"。
- **`apps/api/.env` 从来没被服务加载过**：`Settings` 的默认值在类定义时就用 `os.getenv` 绑定，`mineru_client` 同样裸读环境变量，而全 app 没有任何 `load_dotenv`（只有 `scripts/evaluate_benchmark.py` 自己调），`npm run dev:api` 也没有 `--env-file`。实测 `MINERU_API_KEY set? False`——阶段 4 填进去的 key 服务根本看不见，教材上传必然失败。改为在 `class Settings` 之前加载，`override=False`；`python-dotenv` 补进 pyproject（此前被 import 却从未声明）。
- 上一条的副作用：测试开始继承开发者真实 key 并**打真网络**，套件从 7s 变 84s 且并发下变红。用 `LUOJIA_NO_DOTENV` 门控，`tests/conftest.py` 里设置并清空两个 key，另有测试断言测试进程内它们必为空。
- `COURSE_STORE_PATH` 默认为空 = **纯内存**，重启即丢候选与审核记录，且此前无文档。已写进 `.env.example` 并在本机 `.env` 配上。

**5.2 教材链路从"完全不可用"到可用**（`17290ee`、`69de7a8`、`9feebfa`）

- **MinerU 端点拼错**：`file-urls/bear` 应为 `file-urls/batch`。MinerU 对未知路径返回纯文本 `404 page not found`（19 字节），`Response.json()` 把开头的 `404` 当数字解析完再报 `Extra data: line 1 column 5 (char 4)`——一个拼写错误伪装成了响应格式 bug，**整条教材上传链路自诞生起就没通过**。新增 `_parse_json`：HTTP 状态 + content-type + 正文片段，401/403 明确指向 90 天 token 过期。
- **候选抽取在用重叠分块重建原文**：`routes_courses` 用 `"\n".join(chunks)`，而 `chunk_markdown` 是 500 字窗口 + 50 字重叠。真实教材上重建文本比原文长 **11.3%**（357,263 vs 320,900），导致 70 个提案只有 66 个唯一 id；`add_candidate` 遇同 id 会 `support_count += 1`，于是**只上传一本书**就有 4 个单元的支持度显示为 2。改为 `documents` 持久化 markdown（migration 004）并从中读取；无原文时 **409 fail-closed**，不再退回有损重建。
- 同批修掉两个邻近缺陷：候选 id 只哈希 `(document_id, title)`，同名标题（两个「证明」块）会塌成一个候选并丢弃第二段内容 → 改为把正文也纳入哈希；MinerU 失败被写成 `extracted_md = "⚠️ [MinerU 网络解析失败: …]"` 当内容返回 → 文档类上传改 **502 且不入库**，图片上传保持 200 + 空 markdown + `parse_error` 字段（`tutor-input.tsx:151` 的 `data.markdown ? … : ""` 用法不受影响）。
- **定长窗口分块换成结构感知分块**（`document_chunking.py`）：复用 `segment_document`，一块绝不跨两个教学单元；长小节按段落边界切，单段超限退到 `text_preview.safe_cut` 的 LaTeX 安全边界。每块前缀 `[章 › 节 › 小节] 标题`。实测 714 → **430 块**，正文重拼**无丢失无重复**，**158/158 标题完整且仅出现一次**，429/430 带上下文头。块被明确定义为**有损派生物**，原文重建只走 `documents.markdown`。

**5.3 切分粒度与检索接线（调研文档 §24 的 A–D）**（`f83c52e`、`5b563cc`、`41d0a62`、`97f3674`、`1e7d9fb`）

- **A 切细教学原子 + 产出关系**：`证明`/`例`/`推论`/`注` 不再附着进上一单元，各自成节点；类型词表补 `引理`/`推论`/`注`/`例`/`证明`；产出 `NEW_RELATION` 候选（`supports_proof`/`example_of`/`derives_from`/`part_of`）。`graph_review.py:115-124` 早已能审 `new_relation`、`TASK_TYPE_RELATIONS` 也早含这些类型——缺的只是流水线去产出。
- **去掉写入期 600 字截断**：`_MAX_CONTENT_CHARS` 是给 UI 卡片设的预算，却被用来截断知识本体。实测丢弃全书 **75%** 正文、截断 46 个定理中的 44 个，且切在 LaTeX 中间（`定理 2.4` 存成 `… + \frac { f ( x ^ { * } ) -`，未闭合），被丢掉的正是结论 `|x_{k+1} - x*| ≤ (L/d)|x* - x_k|²`。截断下移到展示层 `app/text_preview.truncate_text`（会避开未闭合的 `$`/`$$`/花括号/尾部命令）。保留率 25% → **99.9%**。
- **MinerU 把标记渲染成标题**：`## 定义 1.1` 既是标题又是标记，而 `if heading` 分支排在 `elif unit_type` 前面，标题分支先赢 → 类型全丢。改顺序后类型从 `{definition 2, theorem 2}` 变成 `{definition 19, theorem 46}`。
- **B 融合两套检索**：原来 `_collect_local_hits` 是**互斥二选一**——课程图谱命中就完全绕过 BM25+向量+RRF 的混合检索，未命中才兜底调用；且图命中恒为 `score=85`、`direct_hits` 恒为 `[]`、`fast_context:103` 纯拼接不重排，`_hits_text` 取 `hits[:3] × 240 字` ≈ 720 字。**课程图谱命中时等价于没有检索**：注入的是子图前 3 个节点，与学生提问无关。改为并发 + **RRF 排名融合**（按排名而非原始分数，因为两者量纲差三个数量级），混合检索带 **200ms 子预算**（否则慢速 embedding 调用会连课程图谱结果一起被 350ms 窗口取消）；图命中改「锚点 1.0 / 一跳 0.6」× case 置信度并预排序；注入改 **2400 字按排名填充**，省略显式报告。
- **C 章节路径与溯源**：**MinerU 把 158 个标题全部输出成 `##`**，markdown 层级完全不携带层次信息 → 改从章节编号推深度（`第 N 章`→1，`N.M`→2，`N.M.K`→3），深度分布从「239/240 都是 1」变成 `{1:10, 2:135, 3:94}`。另外 `graph_review` 批准候选时未映射 `chapter_path`/`source_document_id`/`page_start`/`page_end`，入图后的规范单元答不出"我来自哪一节" → 已补。`KnowledgeItem` 本就有 `chapter`/`section` 字段，现由 `chapter_path` 填充并在 prompt 里渲染成 `来源 · 章 › 节`。

**5.4 抽取质量与审核可用性**（`4680c6a`、`7012cf2`、`9bc21ff`、`8bcd446`、`73ea8ae`）

- **前置/后置内容不再成为知识单元**：用结构性规则（不在编号大纲内）而非词表，`引言`/`前言`/`目录`/扉页/`参考文献` 全部落网，而「第 1 章 基础知识」这类章引言保留。两个陷阱：`参考文献` 在第 6 章之后会**继承章路径**，所以后置标题要重置大纲栈；`K第 1 章 练习 k` 是 OCR 装饰的合法练习节，所以章号匹配用 `search` 而非 `^` 锚定，否则会被误杀。
- **标题收敛**：`例题 1.1 (1) 多项式计算通常较为简单，我们可以设计一个算法：` → `例题 1.1`。规则「标记 + 编号 +（短名称）」，编号后残余若短且不含句读则保留为名称（`算法 2.1 二分法` 不丢"二分法"），纯数字括注是枚举不是名称。长句标题 72 → 3 条。
- **`命题` 此前根本不是标记**：全书 7 个（`命题 3.1`–`5.1`）被当成普通标题、类型 `concept`，**还会重置 anchor**，导致其后的证明连不到任何东西。现归入 theorem 类（标题保留"命题"字样），theorem 46 → 53。
- **关系端点改按 section order 索引而非 title**：标题收敛后全书有 56 个都叫「证明」，用 title 做键会让所有 `supports_proof` 指向同一个错误单元。
- **`support_count` 原来数的是"跑了几次"而不是"几个来源支持"**：同 id 命中就无条件 `+1`，同一文档重跑即虚增。改为仅在 `evidence_ref` 新出现时递增。同时 pending 候选的 payload 原本**永远刷不动**（同 id 直接丢弃新 payload），导致 C 阶段新增的 `chapter_path` 无法回填 → 改为「仅 pending 状态下刷新」，教师一旦 approve/merge/reject/defer 就永不被覆盖。
- **新增 `SUPERSEDED` 状态**：候选 id 哈希了 title 和 text，管道一改进 id 就变，旧候选**永远不会被取代，只会堆积**。实测抽取改进后 DB 里有 778 条 pending = 495 条当前 + **283 条孤儿**（含已不再抽取的前置内容、长句标题、无端点标题的旧关系）。`from-document` 现在会撤走「同一文档、仍 pending、本轮未产出」的候选；只动 pending，教师决定过的记录原样不动；撤下的行保留不删，早期管道提议过什么仍可审计。
- **审核台此前无法审关系**：260 条关系候选只有一个笼统的「拓扑关系」徽章，DOM 里搜不到任何具体类型，卡片正文还落到「无补充描述」（关系本来没有 content）。现在徽章点名具体类型（支撑证明 / 例题佐证 / 推论来源 / 从属小节），卡片渲染 `source —关系→ target`，详情面板附两端 unit id、原始 `relation_type` 与置信度，单元卡片与详情显示章节出处。
- **笔记生成两处缺陷**：端点同样在用 `"\n".join(chunks)` 重建原文（已改读 `documents.markdown`，无原文 409）；`_sample_chunks` 是 `chunk[:keep]` **按比例切每块前缀**，24k 预算摊到 32 万字 = **每块只留 56 字**，其中 53% 还是上下文头部行，正文与 LaTeX 被切在词中间（`…重要作`、`!['`、`[Numerical Anal`）；`_MAX_HEADINGS = 80` 而全书 158 个标题，截断点正好在第 3 章之后，**第 4/5/6 章标题模型根本看不见**。改为整块等距抽样（含首尾端点）+ 标题上限 400 + 正文预算 48k。

## 2. 本分支确立的硬约定（新增代码必须遵守）

1. **不确定就 fail-closed，不给乐观默认值。** 解析不出、判不了、没数据 → 显式 `UNCLASSIFIED` / `verified=False` / 「未评估」/ 409，绝不默认 `core`、默认 `True`、默认 0.5。
2. **失败必须显式到达用户，不得伪装成内容。** `insert_document` 缺失、空 `ai_response`、MinerU 报错写成 `⚠️ …` 塞进正文、抽样把正文切成碎片——这四个 bug 是同一个病。生成失败要报错并排除出统计分母。
3. **README 里每个百分数都要能指到一个文件和一个分母**，且 `summarize_eval.py` 能重算出来。
4. **只有单一真源。** 图状态归 `CourseStore`(SQLite)，掌握度归 `memory/mastery.py` 的 BKT，**文档正文归 `documents.markdown`**。FTS 分块是派生检索产物，永不用于重建原文。
5. **流水线只投喂，不直接写正式图。** 自动抽取一律进 `CandidateManager` 的 pending 态，approve 权在教师，approve 必须产生 `graph_revisions`。
6. **候选 id 用内容哈希（含正文）**，同一文档重传走去重而不是刷屏。
7. **provenance 必须可追到 `document + 章节 + 页码`，并且要活过审核入图**——只在候选上带 `evidence_ref` 不够，`KnowledgeUnit` 也得有。
8. **一次评测/抽取只留一次运行的证据。** 覆盖写或归档，失败样本带 `error` 且不进分母。
9. **重新抽取必须取代同一来源的旧 pending 候选**（`SUPERSEDED`），且绝不动教师已审的记录。
10. **抽样与截断只能整块进行，不能按比例切前缀**；截断只能发生在展示/prompt 层，且必须避开未闭合的 `$`/`$$`/花括号/尾部 LaTeX 命令。
11. **位置推断出来的关系 `confidence < 1.0`**，因为它来自文档顺序而不是文本语义。
12. **测试必须离线。** 任何需要开发者 `.env` 或外网的测试都会在别人机器上变红或变慢 10 倍。

## 3. 怎么验证当前状态

```powershell
# 唯一聚合入口：校验知识 JSON + 后端 pytest + 前端 12 个 Node 测试
npm test

# 后端（预期 256 passed，离线约 8s）
npm run test:api
cd apps/api; python -m pytest -q

# 评测指标自证（预期 20 行、90.0%、5.0%）
python apps/api/scripts/summarize_eval.py

# 课程图数据与契约
python apps/api/scripts/verify_course_graph.py
node scripts/validate-json.js

# 前端：必须先停掉 next dev，否则 build 会共写并损坏 .next
# 只想类型检查而不动 .next，用 npx tsc --noEmit
cd apps/web; npm run build
```

本地跑服务：`npm run dev:api`（uvicorn :8000）+ `npm run dev:web`（next :3000）。改了后端代码必须**重启 uvicorn**——`dev:api` 没带 `--reload`，改文件不生效，这个坑踩过。

## 4. 与另一仓库的分工

同一课程组还有 `jmdonbaba/numerical-analysis-ai-tutor`（纯前端 Demo + 多人 AI 协作治理）。两者**只有"知识图谱"这个词重合**：那边做「提问归一化成标准节点 → 图生长 → 教师看热力」，服务课程运营；本分支做「不泄露答案 → 逐步符号验证 → BKT → 错题复练」，服务单个学生的一次解题会话。不要为了对齐两边而把本分支的教学法改成内容生产流水线。

那边值得抄的：CI + 机器校验 claim 一致性、Playwright + pixelmatch 视觉回归、以及「不通过拓扑排序生成强制学习顺序、不因环删真实关系」这条产品判断（见 §6）。

## 5. 安全说明

`MINERU_API_KEY` 与 `LLM_API_KEY` 只存在于 `apps/api/.env`（`.gitignore:10` 覆盖，`git ls-files` 确认未跟踪，`git status` 无泄漏），**未进入任何提交**；`git grep` 全树无 `sk-` 命中。MinerU token 有 **90 天有效期**，上传报 401/403 即为过期，`_parse_json` 会直接提示去 `mineru.net/apiManage` 重新生成。

## 6. 尚未处理的问题

> **2026-09-30 接手复核补充（研究文档 §26）：** 新的最高优先级是正式图跨重启恢复：临时SQLite验证 approve 后有单元，重建CourseService后候选保持approved但单元丢失。另需补生产教材单元召回；eval里的加权图检索并非EvidenceBuilder路径，不能把pending dry-run的13/15 hierarchy@1当成生产验收。实际种子包27 units / 21 relations / 15 Cases。Overlay为过程证据计数，不是已验收的掌握度/遗忘模型；聊天工作流尚未自动写入课程events。

> 本轮只核查并更新记录：`npm test`知识JSON通过、API256通过（5 warnings）、前端12通过；旧Case benchmark16/16域内、20/20决策、4/4域外，未跑build/浏览器验收/在线模型评测。用户随后授权AGY Staff（Gemini 3.8 Flash High）更新约200题离线v2 benchmark，保留原20题与生产matcher。文档§26记录推荐四轮顺序；未修改真实教材库或审核决定。

> AGY实施最终未交付：直连Google端点超时；为AGY进程沿用本地HTTP代理后仍出现`stream reading error: unexpected EOF`（job `implement-muo1j7ha-6625291f`，error）。没有benchmark变更。扩充200题为已授权但未完成事项，已请用户选择Codex接手或AGY网络恢复后继续；系统代理配置保持原样。

> 用户随后指定Luna：已启动GPT-6 Luna子代理实施相同范围，主代理复核；交付前不登记200题为完成。

> **本轮最终交付：** Luna新增228题独立v2（原20题保留）、13条静态代码片段、15条任务上下文、11条域外、7条域内新Case、2条不可确定路由。主代理发现并要求修复`[None]`域外计分和宽松决策口径，随后按研究§4.5纠正两条未改变Case前提的标签；gold不是从matcher预测生成。最终Case11/208、严格决策34/222、可接受集合34/228、域外10/11、新Case7/7；204题至少一项不匹配、异常0。题集hash `0c263dfc9c8646bcd43f0a77987439f8e97776e45d5efa94edf3e0903ab9e6a0`；原题集/种子包/matcher hash保持。生成器逐字节复现，npm test知识JSON通过、API265通过（含9项评分回归）、前端12通过。协议在 `evaluation/CASE_BENCHMARK_V2.md`，结果在gitignored的`results/case_benchmark_v2.json`。尚无教师标注审核/LLM对照/学生学习效果证据；生产代码、正式教材库与审核状态未改，未commit/push。

1. **baseline 两行仍无数据。** GPT-4o / DeepSeek 裸模型同批 20 条、同 rubric 的结果不存在，所以 README 的 `90.0% (18/20)` **没有参照系**。约两小时 + API 费用，是含金量最高的一块。
2. **交付面为零。** 无 `.github/`、无 CI、无 Dockerfile / docker-compose。服务能起（`app/main.py`，`/health`），但没有任何东西把它推出去，§2 那 12 条约定也没有任何机制强制。
3. ~~`MathMarkdown` 与 `LatexRenderer` 定界符不一致。~~ **已修（2026-09-30）**：`MathMarkdown` 改为 `LatexRenderer` 的薄封装，审核台/对话页与笔记本共用一条解析路径，四种定界符全支持。
4. **浏览器「上传」按钮点击未实测。** 上传→解析→落库→笔记→渲染→候选→审核台整条链已验证，但上传那一步是用 curl 直传 API 走的，UI 的文件提交动作没点过。
5. **495 条候选待审，审核量是真成本。** 需要按小节批量审 + `proof`/`example` 这类逐字来自教材、非模型生成的原子走低风险快速通道，人工只审 `definition`/`theorem`/`lemma` 与跨节关系。
6. **`prerequisite` 拓扑排序的语义未决。** `KnowledgeRelation` 带类型化前置边，对其做拓扑排序就会生成强制学习路径，与本分支反对的「越俎代庖」相冲。对照仓库的明确判断是「不通过拓扑排序生成强制顺序、不因环删真实关系」。
7. ~~21/150 个单元的 LaTeX 括号本身不配平~~ **渲染层已修（2026-09-30）**：新增 `lib/latex-balance.ts` 的 `balancedLatex`（丢弃多余 `}`、补齐缺失 `}`、配平 `\left/\right`），`LatexRenderer` 与 `MathView` 渲染前统一修复；抽取层数据保持原样，待审核流程标记。
8. **前端测试面薄**：`apps/web` 只有 12 个 Node 测试，无 e2e、无视觉回归。
9. ~~`apps/api/test_mineru.py` 是孤儿脚本~~ **已删除（2026-09-30）**。
10. **`opening < 150ms` 只是测试断言**，运行时没有任何 deadline（对比 `fast_context` 的 350ms 是真的，`fast_context.py:51` 硬编码 `asyncio.wait` + 取消）。

## 7. 阶段 5 的实测终态（同一本 150 页教材）

| 项 | 起点 | 终态 |
| --- | --- | --- |
| 教材上传 | 端点拼错，**100% 失败** | 200，121s，320,900 字符 markdown |
| 原文落库 | 不存在该列 | 逐字节一致，`documents.markdown` |
| 分块 | 714 块，重拼 **+11.3% 注水**，标题被切断 | **430 块，无丢失无重复，158/158 标题完整**，429/430 带上下文头 |
| 正文保留率 | **25%**（600 字上限） | **99.8%** |
| 候选 | 150 单元 / **0 关系** | **235 单元 / 260 关系**（495 pending，283 superseded） |
| 单元类型 | concept 146, definition 2, theorem 2 | concept 66, proof 55, theorem 53, definition 19, example 16, corollary 11, lemma 8, algorithm 4, remark 3 |
| 关系类型 | — | part_of 169, supports_proof 67, example_of 13, derives_from 11；**悬空端点 0** |
| 单元长度中位数 | 1,437（且被截到 600） | **774，全文不截断** |
| 章节路径深度 | 239/240 只有 1 级 | `{1:10, 2:135, 3:94}` |
| `support_count` | 单次上传即虚增到 2 | **全部 1** |
| 检索 | 二选一、图命中恒 `score=85`、注入 ~720 字 | 并发 + RRF 融合、位置相关度、**2400 字按排名注入** |
| 学习笔记 | 12,183 字，**120 处「原文未覆盖」**，4-6 章靠猜 | **18,595 字，3 处未覆盖**，六章章名全对，115 个 `\[…\]` + 110 个 `\(…\)` |
| 笔记渲染 | — | 页面 **225 个 KaTeX 节点，裸定界符 0** |
| 审核台 | 关系候选不可审 | 类型 + 两端标题 + 端点 id + 置信度全部可见 |
| 测试 | 167 passed / **1 failed** | **256 passed / 0 failed**，离线 |

## 附：检索评测基线（2026-09-30）

- 评测集 244 条（`scripts/build_retrieval_eval.py` 从教材图谱确定性生成），gold 244/244 解析成功。
- 顺带修了三个真缺陷：`search_document_chunks` 方法缺失（chunk 检索运行时从未生效）、SQLite 默认分词器切不动中文（新增 CJK bigram 索引，migration 005）、问句脚手架毒化 AND 查询（`cjk_query_groups` 剥离问句框架）。
- BM25（生产同路径）Recall@3 **0.752** / Recall@5 **0.798** / MRR@10 **0.708**；vector/hybrid 两行待 embedding key（DeepSeek 无 embedding 端点）。详见研究文档 §25。

## 8. 界面与交互体验演进（2026-09-30）

- **九章草堂混合体上线**：落地方案 A「宣纸手稿演算台」作为主脊柱，融合方案 C「双栏对照错因复盘卡」与方案 B「按需调阅数理仪器」，彻底区分学子立论与珞珈师说身份印章。
- **模型设置鉴权与容错**：在 `apps/api/.env` 启用 `ALLOW_USER_API_KEY=true`，前端 `ModelSettings` 补充 `try...catch` 与状态透传，杜绝红屏崩溃。
- **推导等待体验重构**：消除原本强行全屏铺开的 4 个空旷大白方框，重塑为极简收拢的手稿墨绿徽标（高度仅 28px，可按需展开细腻时间轴），并在开场白后加入墨润呼吸光标，极大改善等待节奏。

## 9. 联网检索与多厂商运思强度切换（2026-09-30）

- **多厂商运思强度映射适配**：
  - 在 `apps/api/app/llm/openai_compatible.py` 实现 `build_request_payload`，支持 4 档推演深度（`off` 直答 / `low` 轻敏 / `medium` 深思 / `max` 格物）。
  - 精准映射主流模型：DeepSeek 官方 API（`reasoning_effort: low/high/max` 及 `thinking.type: enabled/disabled`）、OpenAI（`reasoning_effort`）、Anthropic（`output_config.effort` 与 `thinking_budget`）、Qwen 通义千问（`enable_thinking`, `thinking_budget`）、智谱 GLM（`reasoning_effort`）。
- **双轨全域网络检索系统**：
  - 针对原生支持联网的模型（Qwen `enable_search: true`、GLM `web_search`、Kimi `$web_search`）开启 Native 参数；
  - 针对纯推理模型（DeepSeek 等）研发高可用外部检索适配器 `apps/api/app/search/web_search.py`（Tavily + DuckDuckGo 双引擎，1.8s 严格超时与降级容错），在 Agent Fast Context 层自动化注入 `[WEB-N]` 不可信提示摘要防模型幻觉。
- **藏书阁全局站内检索（Ctrl+K）**：
  - 新增后端接口 `GET /api/search/global`，跨教材定理（知识图谱 200+ 单元）、学子错题本与随堂笔记三维并行检索。
  - 前端开发 `GlobalSearchModal` 弹窗（支持 KaTeX 实时公式预览与「带入草堂研讨」一键装载），并在落笔台底部提供 `[🌐 联网探微]` 微光按钮与 `[🧠 运思强度]` 浮动切换器。
- **质量与回归**：新增 `test_web_search.py`、`test_reasoning_effort.py`、`test_tutor_search_integration.py`、`test_global_search.py` 全部 9 个离线用例绿灯通过；前端 `npm run lint` 0 错误。



## 2026-09-30 Prompt全面重塑（teaching-v2.1）

用户授权将prompt审查所列问题全部实施。主规范与三份参考指南已统一并真正加载，新增prompt_policy唯一策略入口，明确完整答案/direct优先。后台策略与不可信资料分开，Case条件/推理要点/匹配决策/来源进入prompt，探针不注入答案键。证明先审查，Verifier严格schema；工具执行成功与数学命题成立分开，失败降级。图片识别后真暂停，前端确认/编辑，草稿通过learning_meta持久化恢复。公开文案区分LLM意见与本步检查，错题卡不再使用硬编码的错误原因或正解。

详见 PROMPT_ARCHITECTURE_V2.md（按文件整改与证据范围）。最终离线npm test：API294、前端12、知识JSON通过；tsc通过；lint退出0、保留现有告警。测试进程使用SYMPY_GROUND_TYPES=python、MPMATH_NOGMPY=1绕开本机gmpy2本地扩展错误，conftest离线门控未变。新增20项prompt/流程回归。没有真实模型A/B、教师验收、真实浏览器上传或学习效果实验；v2题集/课程包/matcher哈希未变。已有服务需重启加载新prompt。未commit/push/deploy。


## 2026-10-01 — 响应式聊天 UI 与公式渲染修复

- 修复窄屏左右空白抽屉：Sidebar/LearningPanel 只渲染内容，由 MobileDrawer 统一控制显示、遮罩、关闭、焦点循环及跨断点恢复；桌面断点为 1024/1280px。
- 学习抽屉复用桌面状态/笔记内容，补齐移动端随堂笔记入口。顶部品牌/新会话避免换行，次要导航收进“更多”；输入区移动端取消常驻算子滚动条，简化工具文案，保持 16px 输入字体与底部安全区。中文 IME 确认不提交，粗指针设备 Enter 保留换行。
- 提取 message-parser.ts，修复同一行 $$…$$ 和 \[ … \] 的闭合处理，未闭合公式不吞后续空行/标题，保留代码与转义美元符号；加入 Markdown 表格渲染。原“膜振动方程”会话现已正常显示全部公式与后续标题，DOM 中 KaTeX 错误为 0。
- 学习面板取消未检查/无知识点时的默认 50% 展示，区分模型复核与本步检查；掌握度明确为估计。
- 验证：npm test（API 294、前端 17、知识 JSON 均通过）；tsc --noEmit 通过；lint 0 errors，原有 10 warnings。浏览器检查 320/390/768/1100/1440px、390x480 短视口，无整页横向溢出；Esc/关闭按钮/遮罩、Tab 焦点循环、跨断点关闭、移动端笔记切换与“更多”菜单通过。截图：results/ui-2026-10-01/mobile.jpg。
- 边界：未进行真实手机软键盘验证；开发服务器继续运行，因此未运行 next build；未提交/推送。框架仍为 Next.js 14.2.35。官方支持政策已将 14.x 列为不支持，建议后续独立迁移到 16.x 稳定补丁版，核对 React/API/lint 后再构建，不在本轮混入升级。

## 2026-10-01 Next.js 16 升级

Next.js 14.2.35 → 16.3.8，React/React DOM 与类型依赖同步19.3.0，`eslint-config-next` 同步16.3.8；`next lint` 改为 ESLint flat config，使用 ESLint9.39.5，保留既有 effect/ref 用法兼容规则。Next自动更新 `jsx=react-jsx` 与 `.next/dev/types`；固定Turbopack根目录，关闭自动生成AGENTS/CLAUDE。新增typecheck先生成路由类型；CI独立lint并加入message-parser测试，README/AGENTS同步。

停Web dev后生产构建通过；完整离线npm test（API294、前端17、知识JSON）通过；typecheck通过，lint 0 errors/10已有warnings。定向更新browserslist/baseline-browser-mapping/postcss-selector-parser；含开发依赖的npm audit与生产依赖audit均0漏洞，最终安装树无peer invalid。开发服务恢复于127.0.0.1:3000；API8000健康、chat/graph页面均200。浏览器原会话48处公式、0 KaTeX错误；390×844无横向溢出，左右抽屉可用；图谱27节点/21关系，控制台0 error。截图：results/ui-2026-10-01/next16-react19-mobile.png。未真实手机软键盘/线上模型验收，未远端CI/commit/push/deploy。

## 2026-10-01 — 六个月详细计划与一年展望

按用户要求仅规划后续业务，写入研究文档§27，保留“可验证诊断闭环”的原判断全文。2026/10–2027/03按G0–G8推进：正式图持久化/审核原子性 → 生产Case召回 → Newton错误定位/提示/修订再验/最小事件 → 完整求根家族/Overlay → 教师gold/独立集 → 小规模试用 → 协议冻结 → 有对照的无AI跨表示迁移与延迟保持 → 复现/扩展决策；2027/04–09只作条件性滚动展望。每周约3开发日为估算，教师合作、招募与研究流程未确认。

本日离线复跑228题，Case Recall@1仍11/208，严格单标签34/222，可接受决策34/228，域外10/11，新Case7/7，matcher异常0；输出results/case_benchmark_2026-10-01_plan.json，三项冻结哈希不变。执行成功不等于检索能力通过。下一轮从M0开始，先用临时库验证重启恢复和故障原子性；本轮未修改正式图数据/审核状态、matcher或Gold。

## 2026-10-01：M0 / M1 实施与分批提交

详细实现、哈希、恢复命令与边界见 `COURSE_GRAPH_M0_M1.md`，研究时间线更新 §27.8，交接文档新增最新状态优先段。

- M0：完整 canonical_graphs 快照、种子首次初始化、正式数据优先、SQLite原子审核与完整revision、CAS、幂等回执、恢复工具。修改前两个库各自 backup/integrity=ok，真实API库pending495/superseded283；无历史approved/merged，无自动重审。测试仅临时库，浏览器启动时初始化正式快照，未批量审核。
- M1：生产与离线同一Case/单元召回，双语BM25+任务重排、仅verified与允许范围、缺信息追问，EvidencePack保留not_checked条件及retrieval_trace。图谱页不将排序分数展示成正确率，不展示探针答案，补充未知/信息不足反馈与异步旧响应保护。
- 冻结228题开发集：R@1=162/208（77.9%），R@3=200/208（96.2%）；单gold决策200/222，可接受决策200/228，域外11/11，新Case7/7。61题至少一项失败（Case46/决策28，有交集），0工具异常；原20题strict通过（Case16/16/集合20/20/域外4/4）。题集/种子哈希保持，不修改gold。教师审核与独立泛化尚未验证。
- 验收：npm test API329 / Web17 / 知识JSON通过；Next16.3.8构建、typecheck通过；lint0错误/10已有警告。真实浏览器核验匹配与追问，截图results/m0-m1/graph-match.png。日志results/m0-m1-full-test.log、m0-m1-web-check.log。开发服务3000/8000恢复，未远端CI或部署。
- 提交：e23da77 M0；1db7739 M1+前轮Prompt/搜索；27dd51a 228题基准；923ab3a 移动/公式与匹配UI；dee8c24 Next/React工具链；最终文档与格式收尾另批。未push；密钥、DB、results、egg-info与public原型不提交。
- 尚未完成：教师抽查61失败与歧义gold、材料少量审核、M2受控诊断Oracle/修订重验、事件链。图谱种子二分法公式已有孤立right定界符；本轮保持种子哈希，不能称全部图谱公式已修复。公开Case接口答案字段权限需M2前梳理，UI隐藏不等于接口隔离。

### 同轮追加：Obsidian 风格课程关系图

用户对原长带图谱与随后卡片网格均不满意，最终改为圆点/细线、确定性有界力导向布局、关联数量映射大小、悬停/选中突出邻域；不改课程数据与语义，不伪装学习路径或掌握度。去掉网格背景/缩略图/编辑连线，将内容与公式收进侧栏，问题定位默认折叠。修复高亮/选中重载图与拖动回位，取消旧范围请求，尺寸变化自动适配。官方参考 https://obsidian.md/help/plugins/graph；执行UI Design技能的Build模式。

最新npm test API329/Web20/知识JSON通过；新增3项验证节点有限且分离、顺序稳定、环路/缺失端点容错。构建/typecheck通过，lint0错误/10已有警告。桌面/390px移动端与节点详情/问题定位浏览器验收见results/m0-m1/graph-obsidian-*.png，测试日志results/graph-ui-*.log。此UI另批提交，未push；公开Case答案接口隔离、教师gold与M2仍待推进。

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

## 2026-10-02 — 竞品启发的详细功能规划（仅文档）

用户要求将竞品建议形成详细规划，选择融入现有六个月数值分析主线，并强调AI可加速、不提前删去后续功能。交付[总规划](planning/learning-experience-2026-10/README.md)及六份配套文档：B0现有实现核对；F1今日任务与间隔复习；F2教材伴读与条件卡；F3交互求根实验；F4–F8章节小测/讲回/视频伴学/教师简报/代码作业；实施记录模板。保留原§27诊断闭环与无AI跨表示/延迟保持主线，研究文档新增§28作为功能扩展入口。

功能均拆为本地待办和真实阻塞，未创建外部issue或派发聊天/代理。每项包含体验、状态、拟定数据/API、复用/新增位置、验收、恢复和停止条件。预算58–85开发日加约10日余量，按现有每周约3日估算滚动校准，不把AI产能或外部合作写成已确认。文字讲回与自动实验均不直接增加独立数值成绩；课程库与会话/文档库的跨库写入不冒充原子事务。

源码核对发现求根Oracle/episode/ack/probe/replay和前端输入/反馈已在工作区出现，旧文档“M2尚未实施”需由B0运行回执统一，而非本轮直接改成已完成。CI前端工具测试清单与根命令有差异，作为B0核对项。材料授权/来源、教师gold、招募、字幕与代码隔离仍是条件性依赖。

本轮仅规划与文档检查；没有应用回归/构建/真实模型或学生试用，没有主动修改业务代码、真实库、gold或seed，没有commit/push/deploy。下一项是B0基线核对与一条求根错误→修订→独立题验收；已授权教材fixture的伴读可独立推进。


## 2026-10-02 — M2/M3 工程闭环与动态 HTML 恢复

用户授权继续 M2/M3、恢复动态 HTML，并沿用分批commit/push。实现详见 COURSE_GRAPH_M2_M3.md。受控 RootAttempt 表单/JSON进入生产 LangGraph 独立路径，不调用LLM、不执行学生代码；Newton/二分/不动点12家族，状态 supported/contradicted/inconclusive/tool_error，输出步骤与数值证据，Case仍经过生产matcher。修改轨迹重验；缺条件和工具异常保持未知。

SQLite新增root_episodes，事件/状态同事务，先验证后写入；显示ACK后计帮助/结果，未交付未知，重试及重启幂等。预算3、首试服务器探针有固定初值/参数与至少两步，发题即预留且避开该学生已发函数；私有探针证据与正确答案不经学生API披露。受助修订计assisted，普通正确计observed，首次独立probe仅probe_observed。学生不能自报成功；Overlay/episode/session跨用户隔离，候选/修订读取教师权限。demo兼容不称生产权限。课程库/会话库非跨库原子事务。

visual-v2/teaching-v2.3恢复闭合完成态html内联JS，主动运行的无同源iframe，CSP禁外联/eval/嵌套，60KB/1500节点，错误/停止/重启/30秒定时卸载。同步JS死循环没有硬CPU隔离，图示绝不记数值验证成功。SSE新增鉴权/超时/连接错误、终端done与EOF检查；失败部分回答保持预览禁用，保留错误状态，凭证未改。

验收npm test/API415/Web30/知识JSON、build/typecheck通过；lint0错误/10原有警告；12家族13/13开发三元组；10生产SSE固定episode含3合法替代，另工具异常/取消/并发/重启/回滚/回执/权限回归。截图results/m2-m3-{dynamic-desktop,dynamic-mobile,chat-mobile}.png，日志m2-m3-*；临时验收路由删除，未写真实会话、未调用真实模型。教师逐题gold和独立测试未验收，G3教师项/M4不能标完成。新增规划文档的并行修改不纳入本轮提交。


## 2026-10-02 — F1–F4首版实施与本地验收

用户授权“先开干f1-f4”，并补充自检通过后可升级。实现今日任务/间隔复习、课程摘录/私有教材选段伴读、三种受控求根参考实验、六题章节诊断；自检后开放参考计分、薄弱知识点和复习入口。页面 /study /reading /lab /assessment，共用LearningWorkspace与CourseStore.learning_records，复用RootEpisodeService/Oracle；数学状态、显示ACK、owner和重复请求均由服务器决定。每日study session限制复习升级；实验曝光从probe池排除，进行中的首次独立probe不允许新参考实验或伴读解释；未知不计成功。

原规划及回执：`planning/learning-experience-2026-10/f1-f4-delivery.md`。runtime课程库优先COURSE_STORE_PATH，文件SQLite缺配置则派生 `.course.db` 持久库；测试临时库/离线门控保留并在结束时关闭连接。原文从markdown按实际字符范围读取，哈希变化拒绝旧请求；模型输出仍未数学验证。F4是章节练习参考计分，不是研究gold/独立测验。

最终本地npm test：知识JSON/API445/Web34；typecheck/build通过；lint0错误/10既有警告。隔离演示库浏览器完成练习→确认→probe→复习、伴读/笔记刷新、原文引用/无模型降级、参考轨迹对照、六题83分/复习入口、弃测与390px/1440px布局。证据results/f1-f4-*；没有真实模型、真人学习收益、教师gold或远端CI证据，未修改冻结seed/gold，未commit/push/deploy。

首版取舍：四张开发条件卡、固定Newton练习及开发probe池；旧版本已开始任务不自动替换；未完成完整PDF标注、研究测验隔离/监考、人工评分和F5–F8。保持原六个月求根诊断/迁移/延迟保持主线，不用工程验收替代学习效果。

## 2026-10-02 — 首页升级、F1–F4加强及F5/F8首版

用户授权继续推进、更新首页字体/排版/效果，启动F5/F8并加强F1–F4；随后提供透明PNG Logo并要求接入。首页改为只读owner学习概览、真实进度/待续任务/参考自检与六入口，中文衬线标题、纸色留白和Newton切线示意。Logo原文件按SHA256一致复制到public/brand，首页、学习工作区、对话页共用BrandLogo，兼顾深浅主题，浏览器图标同步接入。

F1列出计划外和跨日未完成任务并恢复待确认/独立检验；F2私有原文章节笔记隔离；F3方法/参数/预测草稿恢复、预设标记与实验链接；F4当前测评/参考结果链接恢复。F5文字讲回以来源哈希、学生原句对应条件和不可变补充版本保存，模型意见未核验；无模型仍可自我对照。F8只做限定Newton代码AST静态提示、手动轨迹诊断和版本比较，不执行学生代码。C0隔离未验收，原code_executor未放宽。讲回/代码审阅不增加独立成功，未完成独立probe继续阻止参考帮助。

本地离线npm test：API458/Web35/知识JSON通过；生产build和类型检查通过；lint0错误/10原有警告。浏览器隔离演示库验证保存/补充/草稿/版本、首页独立任务优先续接、独立probe帮助保护与确认、实验参数恢复、指定参考结果刷新、390px与1440px布局。合成轨迹/文字只是工程验收数据。真实模型质量、教师核对、学生试用、C0/C1和远端CI尚未验证。详见planning/learning-experience-2026-10/home-f5-f8-delivery.md，日志与截图results/home-*、teach-back-*、code-workshop-*。未commit/push/deploy；既有工作区成果和无关原型保留。


## 2026-10-03 小珞、教学流程审查与 F1–F4/F8 加强

用户授权加入数学学姐形象“小珞”、检查明显不符的流程/设定/提示并直接修复，随后授权在五小时额度耗尽前继续加强薄弱处。本轮原样接入小珞 PNG 到首页/聊天欢迎区，明确 AI 身份；统一独立 probe 的新帮助保护（普通聊天/笔记/相似题/求根提交），保存每条回答自身教学模式和检查状态，修正模式与任务意图冲突、相似题未持久保存、抽样教材笔记全书措辞及提示数据边界，新增根主题开发参考题。teaching-v2.4；计算执行与数学语义验证明确分开。

F1 反馈待确认时锁定输入和新提交，保留幂等重试；F2 原文段落追加笔记草稿且刷新恢复；F3 逐步/播放/暂停/同条件轨迹对照/历史回看与按实验保存的本地复盘；F4 未确认选项按 owner/测评恢复、题号导航与确认进度；F8 已保存行号定位、未提交修改提示、两版原文对照、tol/max_iter 使用与 solve 本体作用域静态检查。学生代码仍不执行，提示/手动轨迹不提升独立成功。无新增表/依赖。

本地最终 npm test：知识JSON/API469/Web39；生产build及TypeScript通过；lint0错误/10原有警告；diff check通过。浏览器在隔离演示库验证五类增强、首页与聊天形象，以及390px实验布局；未调用真实模型。日志 results/f1-f4-f8-strengthened-*.log。完整审查、修复与剩余弱项见 planning/learning-experience-2026-10/xiaoluo-chat-lab-review.md。真实模型/教师gold/真人学习收益/C0/C1/远端CI未验证。数学语义Answer Guard及动态HTML同步JS的CPU强制隔离仍未闭合；历史内容/外部帮助无法由当前应用保护排除；完整PDF标注、跨设备本地草稿与静态规则版本回执后续再做。未commit/push/deploy，保留原工作区成果与无关原型。额度读数91%时结束新功能扩展并收尾。

## 2026-10-03 登录体验补查

用户指出登录系统未同步更新。当前Git历史显示真实Web鉴权接入于2026-09-08，后端后来有课程权限维护；本次没有重写鉴权协议。已修复聊天退出只跳转不清凭证：清除token/owner/演示键，完整跳转以卸载owner相关页面状态，保留学习草稿；桌面/手机均可退出。注册移除不保存的院校/专业，称呼/账号区分，账号格式与服务端一致，补齐label/自动填充。登录/注册成功进入今日学习。鉴权布局加入Logo/主题/首页返回，删除无依据的SECURE CONNECTION标语。

本轮前端40项通过（新增退出清理回归）、生产build/类型检查通过，lint0错误/10既有警告；后端未改，本轮未重复API suite，上一轮API469是之前的证据。截图results/auth-login-updated.jpg。没有实际注册/登录真实账号、密码重置或远端验证；当前isolated demo API没有配置token secret，不能以演示界面验证真实签发。剩余：密码找回、邮箱验证、服务端token撤销/刷新、过期引导与跨标签页状态；注册在签发配置缺失时先创建用户的非原子流程也需后续修复。未commit/push/deploy，五小时额度约94%时只做收尾。

## 2026-10-03 分批提交准备

用户明确授权分批提交并推送，按四个边界：后端学习与教学规则、学习工作区与品牌形象、登录体验、规划及交接记录。提交前重跑npm test：知识JSON/API469/Web40全部通过；最新auth-followup生产build与类型检查通过，lint0错误/10既有警告，diff check通过。git grep sk-检查仅发现说明文字/普通标识符/既有二进制匹配，新增源码/规划未检出匹配的凭证格式。既有egg-info、demo-jiuzhang-hybrid.html、style-explorer.html、ui-proposals、ignored results/数据库/env不纳入。

首版后端包含learning_records表、课程持久库派生路径和tzdata依赖；COURSE_STORE_PATH显式优先，离线测试门控保留。当前分支feature/course-graph-2.0。远端fetch首次因GitHub443连接失败，当前remote-tracking ref不是实时远端证据；推送将在提交后单独尝试并报告，本文不提前宣称已推送。


## 2026-10-03 README 更新与海报提示词交接

用户要求更新 README 与海报提示词，后要求直接生图，再明确表示海报由自己生成。README 改为当前六入口 F1–F5/F8、快速开始、Newton 循环/收敛体验例与能力边界；历史 V8 样本结果不冒充当前求根效果。`.env.example` 只更正课程库派生持久路径的旧注释，没有修改配置值、业务源码或冻结数据。完整/精简生图请求保存于 planning/learning-experience-2026-10，入口 poster-update-prompt.md。

本轮 npm test：知识JSON/API469/Web40通过；本地文档链接无缺失、Newton 示例离线核对与diff check通过。日志 results/readme-update-tests.log。未从干净环境重装依赖，未重复build/真实模型/教师gold/真人评测。内置imagegen两次网络错误，第三次请求按用户指示停止；没有新图，旧海报/原Logo/原小珞保留。交付PNG与视觉核验由后续生成结果决定，不承诺提示词分辨率、可编辑文字层或效果。

此前四批047f134/f875b3e/381c0d6/65ece36已推送，fetch核对本轮开始时本地与远端feature/course-graph-2.0一致。当前文档及提示词按明确清单提交，提交/推送回执在最终交付分别报告；无关原型/egg-info、ignored results、数据库/env不纳入。研究主线、教师/独立与延迟测验门槛不变；没有远端CI或部署证据。


## 2026-10-03 用户新版海报接入与 v1 归档

用户自行提供新版 PNG，并明确要求原海报改名为 v1poster。新附件原样接入根目录 LJ_Tutor_Poster.png；原图归档为 v1poster.png。两图实际1055×1491，SHA256分别为3803c9ed3683cc6dc3c03b0aa85c2c5371ef910531c55095c57e8ee1ceb3a8e4、5935f08d8171c0c8f1042dd0e1c481506ff2db955d42b8bdbabf8edc711e115b，均与各自原文件一致。README 展示新版、折叠保留第一版，poster-update-prompt.md 更新实际交付记录；未重新生图或修改 Logo/小珞素材。

已核对六项功能、代码未执行标注、Newton 四个近似值与先越过再趋近的示意。海报为静态展示，不是生产运行或学习效果验收。文件哈希、文档链接和 diff check 通过；业务源码/配置/冻结数据未改。本轮离线 npm test：知识JSON/API469/Web40全部通过，日志 results/poster-asset-update-tests.log；提交/推送回执单独报告；只提交本轮图片及相关文档，保留既有无关原型/egg-info，未部署或重跑真实模型/教师/真人评测。上一节“未替换海报”是当时历史状态。


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

### 2026-10-03 多领域数值实验首版

A3 已实现，终止门控 / Guard 两次临时破坏均被 CLI 检出，源码已恢复。线性方程组（Jacobi / Gauss–Seidel）及积分（梯形 / Simpson / 自适应 Simpson）共用 numerical-lab-v1 请求 / 结果与既有 owner 学习记录，入口 /numerical-lab。支持预测、步进 / 播放、方法对照、历史 / 参数复用、数值核对；source hash 与幂等请求 ID，自检 / probe 未完成时阻止参考读取、运行及核对。无新依赖 / 迁移 / 学生代码执行 / 独立成绩更新。积分估计不是严格界，sin(16*pi*x)^2 提供采样遗漏反例。聊天入口仍是复制用户上下文，A4 可信任务快照与 A5 真实模型评测未完成。交付细节见 planning/agent-engineering-2026-10/delivery-a3-numerical.md。

最终全量：知识 JSON、API 583 / Web 45；生产 build / typecheck 通过，lint 0 错误 / 10 既有警告。新实验计入首页实验记录总数，保留 owner 隔离；无数学掌握度写入。隔离浏览器完成迭代 / 积分 / 参数复用 / 刷新 / 390px 与反例分段对照；截图 results/numerical-lab-desktop.jpg 不提交，演示 DB 与服务均保持隔离。
