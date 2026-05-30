# Phase 2 细化实施计划：Tutor 化 + 可视化（融合版）

## 两份方案的关系

| 文档 | 定位 | 范围边界 |
|:---|:---|:---|
| [PLAN.md](file:///d:/Projects/luojia-math-tutor-skill/PLAN.md) (Gemini MVP-0) | Phase 1 收尾 | 补齐 5 题验收闭环、模型 allowlist、shadcn/ui 本地组件、移动端抽屉、文档。**明确不做 mastery/OCR/PDF/向量库。** |
| 本文档 (Phase 2) | Phase 1 → Tutor 产品升级 | mastery 闭环、hint_policy、步骤提交、错因扩展、错题本、类似题、可视化、视频推荐 |

> [!NOTE]
> **它们是上下游关系，不冲突。** PLAN.md 交付的是 Phase 1 的"可验收状态"，Phase 2 在此基础上做 Tutor 化。

### 从 PLAN.md 继承到 Phase 2 的基础设施

Phase 2 开始时默认这些已就绪：

- ✅ 模型 allowlist（`deepseek-v4-flash`/`deepseek-v4-pro`/`deepseek-chat`）+ 请求级 `model` 覆盖
- ✅ `components/ui` 本地 shadcn 组件（Button/Input/Textarea/Select/Sheet/Card）
- ✅ 移动端会话抽屉 + 学习状态抽屉
- ✅ 5 条端到端验收题全部通过
- ✅ `meta` 事件稳定返回 `intent/subject/concepts/verified/is_correct/mistake/verifier_summary`

### Phase 2 新增 vs PLAN.md 不做的

| PLAN.md 明确不做 | Phase 2 做 | 说明 |
|:---|:---|:---|
| mastery 表 | ✅ W1 完成 | Tutor 产品核心 |
| 长期画像 | ✅ 错题本 + 掌握度追踪 | 基于 SQLite，不上用户系统 |
| OCR/PDF | ❌ 继续不做 | Phase 3 |
| 向量库 | ❌ 继续不做 | 保持关键词检索 |
| 知识图谱 | ❌ 继续不做 | Phase 3 |

---

## 已确认决策

1. **Manim → Phase 3**：Phase 2 不接 Manim，Phase 3 "课程级 AI TA" 中以预渲染缓存方式引入
2. **视频源扩展**：除 3Blue1Brown 外，收录「妈咪说」「遇见数学」等优质 UP 主视频
3. **mastery 在 W1 首先完成**：作为 Phase 2 的第一优先任务

---

## 现状分析

Phase 1 已完成：

| 模块 | 状态 | 关键文件 |
|:---|:---|:---|
| 前端三栏布局 | ✅ | `tutor-chat.tsx`, `sidebar.tsx`, `learning-panel.tsx` |
| KaTeX 渲染 | ✅ | `latex-renderer.tsx`, `math-message.tsx` |
| SSE 流式对话 | ✅ | `api.ts` → `streamTutor()` |
| Orchestrator | ✅ | `orchestrator.py` |
| 意图路由 (5类) | ✅ | `intent_router.py` |
| 知识库检索 | ✅ | `knowledge/search.py` |
| SymPy 验证器 | ✅ | `verifier.py` |
| Step Checker | ✅ | `step_checker.py` |
| 错因识别 (12条) | ✅ | `misconception.py` |
| 数据库 | ✅ | `repository.py` (users/sessions/messages/attempts/mistake_events) |
| LLM 客户端 | ✅ | `openai_compatible.py` (含 fallback) |

> [!WARNING]
> Phase 1 遗留缺口（Phase 2 W1 必须补齐）：
> - `mastery` 表未建、`mastery.py` 模块不存在
> - `hint_policy.py` 模块不存在
> - `/api/users/{user_id}/mastery` 路由不存在
> - 掌握度面板只展示错因，无真实掌握度数据
> - 可视化能力空白（SKILL.md 分支A "可视化概念讲解" 无后端实现）

---

## 可视化方案

**Matplotlib 静态绘图为主 + 多源视频链接为辅，Manim 留到 Phase 3。**

| 层级 | 方案 | 范围 | Phase |
|:---|:---|:---|:---|
| 基础 | Matplotlib + sympy.plotting → PNG | 函数曲线、积分面积、概率密度、矩阵变换 | **Phase 2** |
| 辅助 | Bilibili 视频链接库（3B1B + 妈咪说 + 遇见数学等） | 核心概念配套推荐 | **Phase 2** |
| 高级 | Manim 预渲染动画缓存 | 复杂几何动画、变换过程 | Phase 3 |

---

## Phase 2 目标

> 系统能持续追踪学生状态，根据错因给分层提示和类似题，并对核心概念提供可视化辅助。

### 验收标准

1. 同一用户连续犯"漏积分常数"错误 → 系统在后续不定积分题里主动提醒
2. 学生连续两次答错同一概念 → 系统降低提示难度，回溯前置知识
3. 学生完成一道题后 → 系统推荐 2 道同概念不同难度题
4. 用户问"什么是定积分" → 返回文字讲解 + 函数面积示意图
5. 用户问概念题 → 自动推荐匹配的视频链接

---

## 任务拆分（4 周）

### 第 1 周：补齐掌握度闭环 + hint_policy

#### W1-1 mastery 表与模块

- `repository.py`：`init_db()` 增加 `mastery` 表
- 新建 `app/memory/mastery.py`：`update_mastery(old_score, is_correct, hint_level) -> float`
- 新建 `tests/test_mastery.py`

#### W1-2 掌握度 API + Orchestrator 集成

- 新建 `app/api/routes_mastery.py`：`GET /api/users/{user_id}/mastery`
- `orchestrator.py` 末尾调用 `update_mastery()`

#### W1-3 hint_policy 模块

- 新建 `app/tutor/hint_policy.py`：4 级提示策略（INDEPENDENT / LIGHT / FORMULA / NEAR_ANSWER）
- 集成到 `orchestrator.py` 和 `prompt_builder.py`
- 新建 `tests/test_hint_policy.py`

#### W1-4 前端掌握度面板升级

- `learning-panel.tsx`：调用真实 mastery API，展示进度条 + 错因 TOP 5
- `api.ts`：新增 mastery 相关 API 函数

**W1 完成标准：** 练习后掌握度实时变化；连续错 2 次自动降级提示

---

### 第 2 周：步骤提交 + 错因库扩展 + 错题本

#### W2-1 学生步骤提交模式

- 新建 `components/step-submit.tsx`
- `TutorStreamRequest` 增加 `step_mode` + `step_index`
- `orchestrator.py` step_mode 时先验证再反馈

#### W2-2 错因库扩展到 50 条

- `misconception.py` 新增 ~38 条错因：
  - 高数 +15：换元上下限、分部积分符号、泰勒余项、级数收敛、反常积分、微分方程常数、偏导固定变量...
  - 线代 +10：秩与行列式混淆、伴随矩阵、线性无关判定、克莱姆法则...
  - 概率 +10：贝叶斯先验后验、期望线性性、方差独立条件、分布函数连续性...
- 改进 `detect_mistake()` 匹配逻辑

#### W2-3 错题本

- `repository.py` 增加 `list_user_mistakes()` + `get_mistake_stats()`
- 新建 `app/api/routes_mistakes.py`
- 新建 `components/mistake-book.tsx`（从 Sidebar 进入，按学科/概念分类）

**W2 完成标准：** 分步提交得到针对性反馈；错题本可按概念筛选

---

### 第 3 周：类似题 + 复盘卡片 + 会话标题

#### W3-1 类似题生成

- 新建 `app/tutor/exercise_generator.py`
- 新建 `app/api/routes_exercises.py`：`POST /api/exercises/similar`
- 有 LLM 时调模型生成，无 LLM 时从知识库 JSON 抽题 fallback

#### W3-2 复盘卡片

- 新建 `components/review-card.tsx`（考点/正确性/错因/掌握度变化/快捷入口）
- SSE 新增 `event: review`，orchestrator 在 `done` 前发送

#### W3-3 会话标题自动生成

- 新建 `app/tutor/title_generator.py`
- 有 LLM：前 2 条消息生成 ≤15 字标题
- 无 LLM：规则 `"{学科}-{概念}-{日期}"`

**W3 完成标准：** 做完题弹复盘卡片；Sidebar 显示有意义标题

---

### 第 4 周：可视化 + 视频链接 + 集成测试

#### W4-1 Matplotlib 可视化服务

- 新建 `app/math_tools/visualizer.py`：
  - `FUNCTION_CURVE`（y=f(x)）、`INTEGRAL_AREA`（定积分面积）、`PROBABILITY_DENSITY`（PDF 曲线）、`MATRIX_TRANSFORM`（矩阵变换）
  - 返回 PNG bytes，遵循 `math-tools-guidelines.md` 第6节规范
- 新建 `app/api/routes_viz.py`：`POST /api/viz/plot` → base64 PNG
- `orchestrator.py`：`intent == CONCEPT` + 可视化关键词时自动生成图

#### W4-2 多源视频链接库

- 新建 `luojia-math-tutor/references/video-links.json`（40+ 条）：
  - **3Blue1Brown**：微积分的本质、线性代数的本质系列
  - **妈咪说MomTalk**：概率论直观系列
  - **遇见数学**：线代几何意义系列
  - 其他优质 UP 主
- `knowledge/search.py` 扩展：搜索时同时匹配视频库
- SSE 新增 `event: video_recommend`
- 新建 `components/video-recommend.tsx`（Bilibili 跳转卡片）

#### W4-3 集成测试（10 条端到端）

```
 1. "什么是导数？"          → 概念讲解 + 切线图 + 3B1B视频
 2. "求 ∫ x^2 dx"          → 苏格拉底引导
 3. "我算 ∫ x^2 dx = x^3"  → 错误识别 + 掌握度↓
 4. 再犯同样错误              → 主动提醒 + FORMULA_HINT
 5. "直接给完整过程"        → 完整解答 + 复盘卡片
 6. 点击"生成类似题"        → 同概念不同参数
 7. "画出 x^2 的图像"      → 带标注抛物线 PNG
 8. "定积分的几何意义？"    → 面积图 + 视频链接
 9. 查看错题本               → 历次错因按概念聚合
10. 查看掌握度面板           → 各概念进度条
```

---

## 文件变更清单

### 后端新增 (12)

| 文件 | 说明 |
|:---|:---|
| `app/memory/mastery.py` | 掌握度算法 |
| `app/tutor/hint_policy.py` | 提示层级决策 |
| `app/tutor/exercise_generator.py` | 类似题生成 |
| `app/tutor/title_generator.py` | 会话标题生成 |
| `app/math_tools/visualizer.py` | Matplotlib 可视化 |
| `app/api/routes_mastery.py` | 掌握度 API |
| `app/api/routes_mistakes.py` | 错题本 API |
| `app/api/routes_exercises.py` | 类似题 API |
| `app/api/routes_viz.py` | 可视化 API |
| `tests/test_mastery.py` | 掌握度测试 |
| `tests/test_hint_policy.py` | 提示策略测试 |
| `tests/test_visualizer.py` | 可视化测试 |

### 后端修改 (6)

| 文件 | 改动 |
|:---|:---|
| `repository.py` | +mastery 表 + 错题聚合查询 |
| `orchestrator.py` | +mastery 更新 +hint_policy +review 事件 +可视化触发 |
| `prompt_builder.py` | +hint_level +mastery_score +视频推荐 |
| `misconception.py` | 12→50 条错因 |
| `main.py` | 注册新路由 |
| `knowledge/search.py` | +视频链接库搜索 |

### 前端新增 (4)

| 文件 | 说明 |
|:---|:---|
| `components/step-submit.tsx` | 步骤提交 |
| `components/review-card.tsx` | 复盘卡片 |
| `components/mistake-book.tsx` | 错题本 |
| `components/video-recommend.tsx` | 视频推荐卡片 |

### 前端修改 (5)

| 文件 | 改动 |
|:---|:---|
| `learning-panel.tsx` | 真实掌握度进度条 |
| `tutor-chat.tsx` | +review/video_recommend 事件 |
| `tutor-input.tsx` | +步骤提交切换 |
| `math-message.tsx` | +嵌入图片 +视频卡片 |
| `lib/api.ts` | +mastery/mistakes/exercises/viz API |

### 数据文件 (1)

| 文件 | 说明 |
|:---|:---|
| `references/video-links.json` | 多源视频链接库 (40+ 条) |
