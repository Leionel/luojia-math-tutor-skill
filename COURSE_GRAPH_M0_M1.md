# M0 / M1 实施与验收（2026-10-01）

本轮完成 M0 工程基础与 M1 生产召回；教师 gold、实际 LLM 教学效果、M2 数值诊断和学习实验尚未完成。原 228 题及种子包未改标签，当前成绩属于已用于开发的离线集合，不能称独立泛化或学习效果。

## M0：正式图与审核事务

- SQLite 新增 `canonical_graphs`，保存完整课程快照、generation 和 seed checksum。服务重启优先读取正式快照；更新种子文件不会覆盖教师审核结果。完整保存单元、关系、Case、边界及来源字段。
- 审核先在私有副本校验，正式图、候选状态与完整 before/after revision 在同一 SQLite 事务提交；失败全部回滚，成功后才发布内存图。
- generation 与候选内容做 CAS，防止陈旧服务覆盖；重复终态审核返回已有回执，不重复增加实体或 revision。跨课程、无效目标、未知关系、非法范围和字段均拒绝。
- Case 替换清理旧索引，未知课程不再返回所有课程的 Case。别名审核后在同一 matcher 即时生效，重启仍可召回。
- 持久化仍由 `COURSE_STORE_PATH` 配置启用。未配置时为内存模式，不能声称重启保存；离线测试显式使用临时库或内存库。

修改前通过 SQLite backup API 备份两个已有数据库到 `results/m0-backups/20261001T122429Z/`，均 integrity=ok。实际 API 库 `apps/api/data/course_store.db` 为 pending 495 / superseded 283，approved/merged=0，因此本轮没有自动恢复或重审历史候选。根目录的同名库没有候选，两者不要混用。恢复演练在临时副本完成，未覆盖正式库。服务启动后已初始化 numerical_analysis 正式快照，候选计数保持原值。

维护工具不会覆盖目的文件：

```powershell
python scripts/course_store_maintenance.py audit apps/api/data/course_store.db
python scripts/course_store_maintenance.py backup apps/api/data/course_store.db --destination results/new-backup.db
python scripts/course_store_maintenance.py restore-copy results/new-backup.db --destination results/restored-copy.db
```

发现历史 approved 但实体缺失时，先审计 payload、完整 revision、来源，人工重建或核对；不要直接重新 approve，也不要用种子覆盖正式图。真正替换部署数据库另需停写、确认路径和恢复验收，本轮没有执行。

## M1：生产 Case / 单元召回

生产 matcher、课程匹配 API、EvidenceBuilder 与离线 evaluator 使用同一召回实现。利用已审核 Case / 单元的标题、问法、关键词、目标、概念锚点及中英任务特征做 BM25 和任务重排；独立召回单元后按课程边界与 verified 状态过滤。教师新审核的内容动态进入索引，不依赖固定 Case ID 分支。

未指定算法或缺少关键内容时追问；超范围或缺少对应教学 Case 时返回 NEW_CASE。上下文允许携带题目、步骤或代码文本，但不执行代码、不伪造历史。教学模式 guided/direct 与 Case task_type 分离。retrieval_trace 保存候选、原因、追问、generation 和排序版本，排序置信度明确为 heuristic_not_probability。

EvidencePack 将课程条件标记为 `not_checked`；兼容种子中写在 required_condition_ids 的文字条件，并标记 case_declared_condition，不假装已解析成正式节点或已经成立。图谱页面显示信息不足/未覆盖反馈，取消百分比“置信度”和直接展示探针答案，并防止旧请求覆盖新结果。公开 Case 数据接口仍包含原教学字段，本轮 UI 隐藏答案不等于建立评测答案权限隔离；M2 前应按角色与 disclosure policy 梳理接口。

## 冻结开发集结果

| 指标 | 修改前 | 当前 |
| --- | --- | --- |
| 228 题中的 Case Recall@1 | 11/208，5.3% | 162/208，77.9% |
| Case Recall@3 | 未报告 | 200/208，96.2% |
| 单 gold 决策准确率 | 34/222，15.3% | 200/222，90.1% |
| 可接受决策集合兼容 | 历史基线见 benchmark 文档 | 200/228 |
| 域外识别 | 10/11 | 11/11 |
| 域内新 Case 识别 | 7/7 | 7/7 |

仍有 61 题至少一项失败（Case 不匹配 46，决策不匹配 28，有重叠），工具异常 0。保留全部失败，不更改 gold 来掩盖错误。原 20 题 Case 16/16、可接受决策集合 20/20、域外 4/4，strict 退出 0；原多标签 gold 不能称严格决策全对。M1 已达到计划中的工程参考值 R@1≥70%、R@3≥90%，但 G1 的教师复核与未见任务验收尚未通过。

- 228 题 SHA256：`0c263dfc9c8646bcd43f0a77987439f8e97776e45d5efa94edf3e0903ab9e6a0`
- 种子包 SHA256：`7cc6d187788a27865e0ac46863340bfcc6cfa11787002b0dda7f5029bf05800e`
- matcher SHA256：`c8e79b44f677e3b2cef5093187d8bf8c08f8e15b5cfacd6735d5cd828f24e225`
- retrieval SHA256：`0d4299cef0735c70550ab01c408a215547e2c84e896e771a14f97cb6ec179a02`
- 结果：`results/case_benchmark_m1_final.json` 与 `results/case_benchmark_m1_legacy.json`（生成结果不提交）。

## 验收证据

`npm test`：知识 JSON、API **329 passed**、前端 **17 passed**，全程离线。新增回归覆盖审核失败回滚、重启保存、重复审核、陈旧 generation、非法关系、备份恢复、索引更新、双语召回、范围过滤、追问，以及 API / EvidenceBuilder / evaluator 排序一致。

生产构建与 typecheck 通过；lint 0 errors / 10 条已有 warnings。Next.js 16.3.8 / React 19.3.0；上一轮依赖审计 0 漏洞。升级后 localhost 开发访问补充精确 `allowedDevOrigins: ["127.0.0.1"]`，按官方配置说明处理开发 HMR 来源：[Next.js allowedDevOrigins](https://nextjs.org/docs/app/api-reference/config/next-config-js/allowedDevOrigins)。未运行远端 CI、真实 LLM 教学验收或部署。

浏览器真实调用确认二分法条件 Case、仅主题匹配说明、未知迭代算法追问。截图 `results/m0-m1/graph-match.png`；检查用临时页关闭，开发服务恢复 3000 / 8000。图谱种子已有二分法 LaTeX 的孤立 `\right.` 渲染问题，本轮保留种子哈希，列入教师材料整理而非声称所有图谱公式正常。

## 分批提交

1. `e23da77` — M0 完整正式图、事务审核、恢复工具与回归。
2. `1db7739` — M1 生产检索与 Prompt 整合，包含前轮教学规则、联网/全局搜索和模型适配重塑。
3. `27dd51a` — 冻结 228 题中英基准与生成说明。
4. `923ab3a` — 前轮移动抽屉、输入层与公式修复，以及本轮图谱匹配反馈。
5. `dee8c24` — Next.js / React / ESLint / CI 升级。
6. 本轮收尾 — 验收记录、长期计划状态和两处空白格式整理。

未 push。未提交数据库、密钥、生成结果、egg-info、public 下已有演示/样式原型。

## 下一阶段与长期计划

保留 §27 六个月 / 一年计划，按依赖推进，不因工程提前完成就跳过教师门槛。下个动作：教师抽查 61 条失败及歧义 gold，确定一组有来源、可验证的求根案例；并行准备 M2 的受控输入契约、停止/失败类型与数值 Oracle 测试，不开放任意代码执行。最小闭环仍是：学生错误求根过程 → 对应 Case → 验证定位 → 针对性提示 → 验证修改结果。M3 再将最小聊天事件链与修订证据接入，区分受帮助完成和独立完成。
