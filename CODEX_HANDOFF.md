# CODEX 交接文档

> 交接时间：2026-09-30。写给要接手本仓库的 Codex。先读完这份，再看两份权威长文档。

## 1. 这是什么项目

**珞珈数智助教**（`luojia-math-tutor-skill`）：面向大学数学（当前主攻《数值分析》教材）的 AI Tutor，后端 FastAPI + LangGraph（`apps/api`），前端 Next.js 14 + Tailwind（`apps/web`），教学规则与知识数据在 `luojia-math-tutor/`。当前工作分支 `feature/course-graph-2.0`（未合回主分支），远端同名。

构建/测试命令、代码风格、提交规范见 `AGENTS.md`，全部仍然有效。关键差异提醒：

- `pytest` **必须在 `apps/api` 目录下跑**（仓库根目录跑会收集到无关文件报 36 个 collection error）。
- 测试离线由 `LUOJIA_NO_DOTENV=1` 保证（`tests/conftest.py` 会清掉 LLM/MINERU key），别破坏这个机制。
- **不要在 dev server 运行时执行 `next build`**（会写坏 `.next`）。
- 提交时 CRLF 警告属正常（Windows 环境）。

## 2. 必读文档（按顺序）

1. `luojia_tutor2_branch_log.md` —— 本分支自 split 以来所有轮次的实测记录 + 「尚未处理的问题」清单（§6，部分已划掉表示已修）。
2. `luojia_tutor2_course_graph_research_refined.md` —— 切分/检索/课程图调研，§24 是 A–D 改造方案与实测，**§25 是检索评测基线（最新）**。
3. `results/retrieval_eval_results.json` —— 最新评测数字；`evaluation/retrieval_eval.json` 是评测集。

## 3. 当前状态（截至交接）

- 教材链路（上传 → MinerU 解析 → 结构感知切分 → 候选抽取 → 审核台）端到端可用；`apps/api/luojia_tutor.db` 存 1 本教材（`doc_656067dd6720`，32 万字，430 chunks，CJK bigram 索引）。
- 检索基线（BM25 bigram FTS，生产同路径）：**Recall@3 0.752 / Recall@5 0.798 / MRR@10 0.708**，244 条评测集（`scripts/build_retrieval_eval.py` 生成，`scripts/eval_retrieval.py` 跑）。
- 前端已统一到「农场水墨」设计令牌（`apps/web/tailwind.config.ts` 重映射了 slate/indigo 等默认色名——**改 UI 时注意类名颜色≠视觉颜色**）；阅读字体（衬线/无衬线）与主题（light/dark，存储键 `luojia-theme`/`luojia-reading`）持久化已修好。
- API 256 项 pytest 全绿；前端 `npm test` 通过。

## 4. 明确的未完成项（按优先级）

1. **vector / hybrid 评测两行是空的**：现在的 `LLM_API_KEY` 是 DeepSeek 的，没有 embedding 端点。需要一个 DashScope key（`text-embedding-v3` 已验证可连通），填进 `apps/api/.env` 后重跑 `scripts/eval_retrieval.py` 即可补齐（向量缓存机制已就绪）。
2. **hierarchy 问法 R@3 只有 0.133**：`X 属于哪一节` 需要图层作答（part_of 边），不是 chunk 检索能解决的——要把 `fast_context` 的课程图 evidence pack 纳入评测口径。
3. **LLM 答题质量 baseline 缺失**：README 的 `90.0% (18/20)` 没有裸模型参照系（branch log §6.1）。
4. **495 条候选待人工审核**（`data/course_store.db` 的 `graph_candidates`）；建议批量审 + 低风险快速通道。
5. **无 CI / 无部署**：服务只在本机跑过，没有任何东西把它推出去。
6. 浏览器「上传」按钮的真实点击从未测过（链路其余环节都是 curl/API 实测的）。
7. Desmos 用的还是 trial key（现从 `NEXT_PUBLIC_DESMOS_API_KEY` 注入，缺 key 时模态框有空态提示）；正式 key 需自己去 desmos.com/api 申请。

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
