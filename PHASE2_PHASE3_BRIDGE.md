# Phase 2 与 Phase 3 衔接说明

## 1. 总体关系

当前项目路线可以理解为三层递进：

```text
Phase 1：MVP-0 可验收闭环
-> Phase 2：Tutor 产品化与学习闭环
-> Phase 3：STEM 可验证学习智能体平台
```

其中：

- Phase 1 解决“能不能跑通一个可靠的数学 Tutor”。
- Phase 2 解决“这个 Tutor 能不能持续陪学生练习并形成学习闭环”。
- Phase 3 解决“这套能力能不能复制到更多 STEM 课程，并服务教师和机构”。

因此，Phase 2 和 Phase 3 不是冲突关系。Phase 2 是产品化收敛，Phase 3 是平台化扩展。

## 2. Phase 2 的定位

Phase 2 的关键词是：

> Tutor 产品化、错因闭环、分层提示、复练路径、可视化辅助。

它仍然围绕大学数学这个主场景，不急着扩到所有学科。

Phase 2 应重点完成：

- mastery 轻量掌握度。
- hint_policy 分层提示策略。
- step_submit 分步提交。
- mistake_book 错题本。
- similar_exercises 类似题。
- review_card 复盘卡片。
- Matplotlib 静态可视化。
- 视频资源推荐。

Phase 2 的验收标准不是“覆盖很多学科”，而是：

> 学生做完一道题后，系统能知道他错在哪里、掌握度怎么变、下一步该提示什么、该练什么。

## 3. Phase 3 的定位

Phase 3 的关键词是：

> 课程级智能体模板、多课程复制、教师端分析、工具链平台化、B 端 API。

它不再只是把数学 Tutor 做得更强，而是把 Phase 2 中沉淀下来的模块抽象成可迁移平台能力。

Phase 3 应重点完成：

- Course Agent 模板。
- 多课程知识库接入。
- Tool Registry 工具注册与调度。
- 教师端学习分析面板。
- 多课程错因库与练习库。
- Tutor Agent API。
- Step Checker API。
- Learning Analytics API。
- Manim 或预渲染动画等高级可视化。

Phase 3 的验收标准是：

> 同一套架构不仅能服务大学数学，还能较低成本接入物理、统计、电路等强推理课程。

## 4. 从 Phase 2 到 Phase 3 的模块映射

| Phase 2 模块 | Phase 2 作用 | Phase 3 升级方向 |
|---|---|---|
| mastery | 记录单个学生在数学概念上的轻量掌握度 | 扩展为跨课程学习状态模型 |
| hint_policy | 根据错因和掌握度调整提示深度 | 抽象为通用 Adaptive Feedback Engine |
| mistake_book | 保存数学错因事件 | 扩展为课程级错因分析与教师端热力图 |
| similar_exercises | 针对当前数学概念生成类似题 | 抽象为 Exercise Generation Service |
| review_card | 每题结束后给出复盘 | 扩展为跨课程学习报告与复习任务 |
| visualizer | 生成函数、积分、概率图像 | 扩展为多课程 Visualization Tool Registry |
| video_recommend | 推荐概念相关视频 | 扩展为课程资源推荐系统 |
| step_checker | 检查学生单步推导 | 扩展为通用 Step Verification API |
| SymPy verifier | 验证数学符号计算 | 扩展为多工具验证层，如量纲检查、统计检验、电路求解 |

## 5. 关键衔接逻辑

### 5.1 mastery 的衔接

Phase 2 中，mastery 可以只服务数学概念，例如：

- 幂函数积分。
- 链式法则。
- 二阶行列式。
- 条件概率。

Phase 3 中，mastery 不应只是一个数学分数，而应抽象为：

```text
user_id + course_id + concept_id + score + evidence
```

其中 evidence 可以来自：

- 做题正确性。
- 错因次数。
- 提示使用情况。
- 复练表现。

### 5.2 hint_policy 的衔接

Phase 2 中，hint_policy 只需要控制数学 Tutor 的提示深度：

```text
INDEPENDENT -> LIGHT_HINT -> FORMULA_HINT -> NEAR_ANSWER
```

Phase 3 中，它可以升级为跨课程的自适应反馈引擎：

- 数学：给公式或下一步推导。
- 物理：提示受力分析或量纲检查。
- 电路：提示节点方程或等效电路。
- 统计：提示分布选择或检验条件。

### 5.3 mistake_book 的衔接

Phase 2 中，错题本服务个人复练。

Phase 3 中，错因数据可以服务教师端：

- 班级最高频错因。
- 知识点薄弱排名。
- 期末复习建议。
- 自动生成补充练习。

这也是从 C 端工具走向 B 端教学辅助的关键桥梁。

### 5.4 visualizer 的衔接

Phase 2 中，Matplotlib 静态图已经足够：

- 函数曲线。
- 积分面积。
- 概率密度。
- 矩阵变换示意。

Phase 3 中，才考虑更复杂的可视化：

- Manim 预渲染动画。
- 物理运动仿真。
- 电路频响图。
- 统计分布交互图。

因此，原 `implementation_plan.md` 中“Manim 留到 Phase 3”的判断是正确的。

### 5.5 video_recommend 的衔接

Phase 2 中，视频推荐是学习辅助，不是核心智能体能力。

Phase 3 中，可以扩展为课程资源推荐：

- 视频。
- 教材章节。
- 讲义。
- 练习集。
- 教师自定义资源。

但推荐逻辑应绑定错因和知识点，而不是只做静态链接列表。

## 6. Phase 2 的边界

Phase 2 不建议做：

- 多课程平台化。
- 教师端完整后台。
- 多租户权限系统。
- 自研模型训练。
- Manim 动画生成链路。
- OCR/PDF 全流程解析。
- 大规模向量库替换关键词检索。

Phase 2 应尽量把数学学习闭环打磨扎实。

## 7. Phase 3 的边界

Phase 3 可以做平台化，但也不建议无限扩张。

Phase 3 不建议一开始做：

- 全学科覆盖。
- 完整 LMS。
- 教务系统集成。
- 大模型训练平台。
- 商业化 SaaS 全套权限和计费。

Phase 3 更合理的目标是：

> 用 2-3 门 STEM 课程证明课程级智能体模板可复制。

推荐第二课程：

1. 大学物理。
2. 统计与数据分析。
3. 电路与信号系统。

## 8. 路线图建议

### 8.1 Phase 2 完成标志

当以下能力稳定后，可以宣布 Phase 2 完成：

- 学生答题后产生 review_card。
- 错因进入 mistake_book。
- mastery 能随答题结果更新。
- hint_policy 能根据连续错误调整提示。
- 类似题能基于当前概念生成。
- 至少 20-50 道验收题通过。
- 可视化能覆盖函数曲线、积分面积、概率密度。

### 8.2 Phase 3 启动标志

当 Phase 2 稳定后，Phase 3 可以从以下任务开始：

- 抽象 Course Agent 配置格式。
- 选择第二门课程做样板。
- 为第二课程建立知识库、错因库、工具链。
- 抽象 Tool Registry。
- 做一个最小教师端错因看板。

### 8.3 Phase 3 完成标志

可以用以下标准判断 Phase 3 原型完成：

- 至少支持数学 + 另一门 STEM 课程。
- 每门课程都有知识库、错因规则、工具调用和练习生成。
- 教师端能看到班级错因统计。
- API 能暴露 Tutor、Step Check、Mistake Diagnosis、Learning Analytics。
- 有一组跨课程 Demo 可以路演展示。

## 9. 在省赛材料中的表达方式

省赛 PPT 中建议这样表达：

```text
Phase 1：数学 Tutor MVP
验证对话、检索、验算、错因记录。

Phase 2：课程学习闭环
完善掌握度、提示层级、错题本、类似题、复盘卡片。

Phase 3：STEM 可验证学习智能体平台
将数学场景中验证过的框架迁移到物理、统计、电路等课程，
并提供教师端分析和教育机构 API。
```

计划书中建议这样写：

> 第二阶段聚焦大学数学场景下的学习闭环，完善错因追踪、掌握度评估、自适应提示与复练推荐。第三阶段将在此基础上抽象课程级智能体模板，将知识库、错因库、工具链和练习库配置化，逐步扩展到物理、统计、电路等 STEM 基础课程，并面向高校教师和教育机构提供学习分析与智能答疑 API。

## 10. 最终结论

Phase 2 和 Phase 3 的关系可以总结为：

> Phase 2 把“数学 Tutor”做成真正有学习闭环的产品；Phase 3 把 Phase 2 中沉淀出的知识库、工具链、错因库和教学策略抽象为平台能力，复制到更多 STEM 课程。

因此，Phase 2 是深挖，Phase 3 是复用；Phase 2 是产品闭环，Phase 3 是平台扩张。

