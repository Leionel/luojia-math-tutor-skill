# M1 Prompt A：G0 收口回执（2026-10-08）

本回执只记录本轮修复与待核实边界。基线为 `feature/course-graph-2.0`、`50e5c1651476a7aca21a2c8dc1afcf7d5ae21665`。原有未提交的 runtime 日程、三份根目录删除、原型、egg-info 与其他交互规划均未纳入本轮。

## 已处理

- 修改前隔离探针：在临时上传目录放入 UUID `.png`，匿名 `GET /api/uploads/{filename}` 返回 `200` 及原始字节。现上传要求登录会话；新增 migration 8 的 `uploaded_files` owner 记录，GET 在当前有效会话和 owner 一致时返回，匿名 `401`，跨用户、未知及旧无记录文件 `404`。上传图像供视觉解析使用时也检查 owner。
- Chat 中的本地上传图改为携带 Bearer 的受控 fetch，成功后只用临时 blob URL 显示；身份变化取消请求并释放旧 URL。原上传 URL 不作为无需授权的图片链接。
- `uv.lock` 补齐 `python-dotenv`、`tzdata`；README 修正 U08/U16 的旧说法。README 顶部历史快照移至[交付与规划快照](delivery-history-2026-10.md)。

旧上传文件若缺少可核实 owner 记录，会保持不可访问。需要恢复时，应先由项目负责人核对来源与归属，再制定单独的一次性数据迁移；本轮没有猜测 owner、没有扫描或改写正式学生文件。新增 migration 8 与之前的 migration 7 一样，只在隔离测试库验收；正式库仍须先完成真实备份、恢复与迁移验收。

## 只审计的边界

- `data/course_packs/numerical_analysis_root_finding.json` 中 27 个 unit、21 条 relation、15 个 teaching case 均未写 `review_status`。`knowledge/schema.py`、`case_schema.py`、`graph_repository.py` 和 `loader.py` 存在缺失时默认为 `verified` 的路径。若现在直接改为默认 draft，会使该旧课程种子大面积失去可检索资格。后续最小切片应先为版本固定、来源可追溯的旧可信种子显式标记并核对数量，再将未知来源输入默认改为 draft；同时用正常课程检索与候选审核回归证明未丢内容。本轮未修改审核语义。
- `git lfs ls-files` 显示 `luojia-math-tutor/references/textbook/` 下 17 份 PDF 由 LFS 跟踪，其中有公开出版教材及名称含 `Z-Library` 的文件。README 的 MIT 声明明确不覆盖教材；仓库内未见逐份授权证明或公开分发许可清单。公开范围与每份使用/再分发授权待负责人核实；本轮不认定违法，不删除文件、不改 Git 历史。
- 未调用付费模型、未部署、未 push，未访问或迁移正式学生数据库。

## 验证

`npm test` 通过：知识 JSON、API 901 项、Web 71 项；API pytest 由根脚本切换到 `apps/api` 执行，默认离线。`apps/web` 的 `npm run typecheck`、`npm run lint` 与根目录 `npm run build:web` 通过；lint 为 0 error、10 项既有 warning。`uv lock --check` 最终通过；在全新临时虚拟环境执行 `uv sync --locked --no-dev` 并成功导入 `python-dotenv`/FastAPI。浏览器以隔离测试账号打开真实 Chat 消息，授权图片显示为 `blob:` URL，解码完成且 `naturalWidth=1`、`naturalHeight=1`；同一资源匿名 HTTP 请求为 401。未把编译通过代替显示验收。
