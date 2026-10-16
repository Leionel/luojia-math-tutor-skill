# F1：今日任务与持续复习

> 状态：待实施；目标窗口2026/10/15–11/11；估算5–7开发日。
> 入口：[总规划](README.md)。完成归因依赖B0；不写成绩的任务原型可先做。

## 1. 学生体验与最小范围

学生进入“今日学习”，选择15或30分钟，看到最多3项任务：一项到期复习、一项当前错因修订、一项独立检验或前置条件任务。每项说明推荐原因、预计时间、教材来源和当前进度。点击继续回到原任务，刷新不丢输入与完成状态。

示例15分钟：3分钟辨析Newton适用条件 → 8分钟修正一段迭代过程 → 4分钟独立题。时间为任务标签估计，超时不惩罚、不强制结束作答。

首版仅求根；人工审题模板与已有episode复用。无历史记录时给一个经审入门任务，不显示虚构薄弱点。没有合格题时明确暂不可用，不返回“请练习一道某概念题”充当可核验题目。

## 2. 选择与复习规则

选择器用确定性规则，不为生成任务额外调用LLM：

1. 仅选择学生有权限、版本明确、内容已审、估算时间能放进预算的任务。
2. 优先到期复习，再未结束修订，再当前单元的独立检验；材料不足则前置条件任务。尚不支持的单元不进入计划。
3. 同一计划最多3项；可替换未开始任务，已开始的任务保留。旧计划保留进度，新计划不把旧输入丢掉。
4. 推荐理由从事实生成，例如“上次在提示后修正了停止条件，今天安排独立检查”；没有时间/结果证据时只说“求根入门任务”。
5. 完成只是任务行为；阅读完成、实验运行和讲回评价都不自动提升独立数学表现。

首版间隔采用可版本化的简单基线`[1,3,7,14]天`，这是待评估策略，不宣称最优：

初始化stage=-1（尚无独立复习成功）；首次成功到stage=0、间隔1天；后续不同review session的独立成功逐档前进，最高stage=3。失败回到stage=-1并排1天修订；受助成功不升级，排1天独立复核。

| 核对结果 | 任务状态 | 对复习的影响 |
| --- | --- | --- |
| 首次有效、无系统帮助的独立题正确 | verified_complete；保留独立证据 | 依stage定义推进一档，按对应间隔设due；最高档保留14天 |
| 独立题错误且有可确认错因 | needs_revision | 回到短间隔；下一次优先错因修订与独立复核 |
| 提示后正确、看过答案或自动实验结果 | assisted_complete | 记录受助，不向独立梯级升级；排短间隔独立复核 |
| inconclusive/tool_error/取消/没提交 | unknown或进行中 | 不修改成功与复习梯级；解释并允许补条件/继续 |
| 手动标记阅读完成 | read_complete | 仅记录阅读进度，可推荐条件题，不计解题成功 |

每次升级必须对应不同review session的有效结果；同次反复重交不会连续升级。逾期不直接判遗忘或降掌握度；展示到期事实，重新安排即可。首版不把知识图谱上的前置关系当作已练习证据自动向下传播。

## 3. 状态与交互

任务：`planned → in_progress → awaiting_check → verified_complete / assisted_complete / needs_revision / unknown`。阅读任务另用read_complete。未知状态不进“已学会”统计。

| 状态 | 界面与恢复 |
| --- | --- |
| 无历史/任务为空 | 经审入门任务；若无内容，链接到现有教材与聊天入口 |
| 创建/加载中 | 保留原列表；按钮busy，防重复创建 |
| 断网/创建失败 | 保留分钟选择与作答；可重试同一幂等键 |
| 部分任务不可用 | 保留可用项并说明缺材料，不凑满3项 |
| 来源/graph版本改变 | 标注旧版本；不静默改题；未开始任务可重新选择，已开始任务按原快照恢复 |
| 多标签同时提交 | 服务端冲突反馈与状态重载；不覆盖较新的已核对结果 |
| 紧凑屏幕/键盘 | 单列任务；15/30选择可见；主动作“开始/继续任务”；替换为次操作 |

## 4. 数据、拟定接口与修改位置

新增状态归CourseStore，与课程过程事件处于同一库；SQLite schema增量按现有CourseStore机制实施。API只接受任务输入与幂等键，不接受前端声明的成功/独立分数。

建议最小持久化对象：

- `StudyPlan`：plan_id、student_id、course_id、local_date、timezone、minutes、graph_revision、policy_version、generation、task_ids。
- `StudyTask`：task_id、plan_id、type、unit/case/exercise_id、source_ref、estimated_minutes、state、episode_id、outcome_event_id、content_version；必要题干快照保留。
- `ReviewState`：student/course/unit、schedule_version、stage、due_at、last_effective_event_id、last_review_session_id；采用UTC存储，按Asia/Hong_Kong或已验证用户时区解释日期。
- `applied_review_events`：用于幂等消费的event_id与派生目标；唯一约束与状态更新同事务提交。

既有last_practiced_at可能为无时区字符串；实施时先审计，未知时区记录保持未知，不擅自当UTC。新字段统一有时区；不批量猜测改写旧数据。

| 拟定接口 | 语义 |
| --- | --- |
| GET `/api/study/today?course_id=...` | 读今日已存计划/到期项；GET不创建或完成任务 |
| POST `/api/study/plans` | 根据分钟预算生成计划；服务端principal为owner；请求幂等 |
| POST `/api/study/tasks/{task_id}/start` | 创建或恢复相应会话/episode；打开不算完成 |
| POST `/api/study/tasks/{task_id}/refresh-outcome` | 校验关联episode，读取server outcome后刷新派生状态；不能上传is_success |
| POST `/api/study/tasks/{task_id}/replace` | 仅替换未开始任务，校验generation；保留旧任务审计 |

优先复用：`knowledge/course_store.py`、`student_overlay.py`、`tutor/root_diagnostics.py`、`api/routes_mistakes.py`、`tutor/exercise_generator.py`、`apps/web/lib/api.ts`。
拟新增：`tutor/study_planner.py`、`knowledge/review_schedule.py`、`api/routes_study.py`、`apps/web/app/study/page.tsx`与少量任务组件。现有错题本和LearningPanel只增加“加入/继续今日任务”链接，不重做全站导航。

跨Repository创建会话与CourseStore绑定任务不作双库事务：先按稳定任务身份校验/恢复会话，再绑定；绑定失败重试不得新建重复会话。源事件提交和派生状态可采用重放恢复，不要求新消息队列；读取/写入入口执行增量补齐即可。

## 5. 三个可独立验收任务

| 任务 | 交付与依赖 | 验收 |
| --- | --- | --- |
| D1，1–2日 | 今日页的一项已审任务→开始→刷新恢复；依赖课程快照，暂不写独立成绩 | 同日同幂等请求不重复计划；空数据有真实入门任务；两用户任务隔离 |
| D2，2日 | 关联已有episode并消费核对结果；依赖D1+B0 | 正确/受助/错误/unknown分开；重复outcome不重复完成；创建会话失败可恢复 |
| D3，2–3日 | 持续复习、到期选择和推荐理由；依赖D2 | 冻结时钟下各间隔正确；跨午夜/时区/逾期/课程更新可解释；同一次重交只推进一次 |

## 6. 验收、回滚与停止条件

新增回归应覆盖至少：无历史、无经审题、到期排序、预算不足、重复创建、辅助成功、首次独立成功、同次重交、多标签冲突、事件先提交派生失败再重放、跨用户和课程隔离、版本过期、未知时区。

未来定向测试建议文件：`apps/api/tests/test_study_planner.py`、`test_review_schedule.py`及前端必要的日期/状态归约测试；名称在实施时建立。完整命令见总规划§8.2。真实浏览器走“选15分钟→作答→断线恢复→重验→出现下次日期”，记录可用性；不把调度测试通过当学习收益。

新增入口关闭后旧错题/聊天仍可用；保留新表与原始事件。策略改版不静默重排已开始任务，派生复习状态可按版本重建。若B0独立证据不可确认，停D2/D3成绩升级，D1仍可交付。

后续观察：计划开始/完成、真实输入失败、同类错误复发、到期独立题表现；每个分母区分独立、受助、未知。正式学习结果仍按冻结对照与无AI测验评估。
