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

1. **baseline 两行仍无数据。** GPT-4o / DeepSeek 裸模型同批 20 条、同 rubric 的结果不存在，所以 README 的 `90.0% (18/20)` **没有参照系**。约两小时 + API 费用，是含金量最高的一块。
2. **交付面为零。** 无 `.github/`、无 CI、无 Dockerfile / docker-compose。服务能起（`app/main.py`，`/health`），但没有任何东西把它推出去，§2 那 12 条约定也没有任何机制强制。
3. **`MathMarkdown` 与 `LatexRenderer` 定界符不一致。** 前者（审核台、对话页）只认 `$$…$$` 和 `$…$`；后者（笔记本）认四种，含 `\[…\]` 和 `\(…\)`。目前不发作（MinerU 输出用 `$$`，模型生成的笔记走 `LatexRenderer`），但任何产出 `\[ \]` 的来源进审核台就会显示裸源码。
4. **浏览器「上传」按钮点击未实测。** 上传→解析→落库→笔记→渲染→候选→审核台整条链已验证，但上传那一步是用 curl 直传 API 走的，UI 的文件提交动作没点过。
5. **495 条候选待审，审核量是真成本。** 需要按小节批量审 + `proof`/`example` 这类逐字来自教材、非模型生成的原子走低风险快速通道，人工只审 `definition`/`theorem`/`lemma` 与跨节关系。
6. **`prerequisite` 拓扑排序的语义未决。** `KnowledgeRelation` 带类型化前置边，对其做拓扑排序就会生成强制学习路径，与本分支反对的「越俎代庖」相冲。对照仓库的明确判断是「不通过拓扑排序生成强制顺序、不因环删真实关系」。
7. **21/150 个单元的 LaTeX 括号本身不配平**，来自 MinerU 输出（全文 `{` 12,974 vs `}` 12,923，而 `\begin{array}`/`\end{array}` 是 312/312 配平的）。渲染层已有 `throwOnError: false` + try/catch 兜底不会崩，但内容质量受损，需要在抽取或审核阶段标记出来。
8. **前端测试面薄**：`apps/web` 只有 12 个 Node 测试，无 e2e、无视觉回归。
9. **`apps/api/test_mineru.py` 是孤儿脚本**：import 一个不存在的 `mineru` 包，不被 pytest 收集（`testpaths=["tests"]`）、无任何引用。建议删除。
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
