# 珞珈数智助教 Web App 具体实现路径

本文档用于把当前 `luojia-math-tutor-skill` 从“可安装的数学助教 Skill”推进为“可用的大学数学 AI Tutor Web App”。目标是给开发直接落地的路线，而不是泛泛讨论产品愿景。

## 0. 产品决策

### 0.1 选择路线

采用 **B + C**：

* **B：苏格拉底式 Tutor**，决定交互方式：默认引导学生自己做，不直接剧透答案。
* **C：课程级 AI TA**，决定产品边界：先服务大学数学课程，尤其是高数、线代、概率论。

不做第一版：

* 不做万能搜题工具。
* 不做全学科问答。
* 不做一开始就支持 OCR、PDF 课程解析、班级后台、知识图谱。
* 不做多 Agent 炫技架构。

### 0.2 第一版定位

**珞珈数智助教：面向大学数学课程的 AI Tutor。**

第一版只主打：

> 高数文本题的分步引导、错因识别、关键计算验证和学习状态记录。

### 0.3 第一版验收目标

输入：

```txt
我算 ∫ x^2 dx = x^3，对吗？
```

系统必须完成：

1. 识别考点：幂函数积分。
2. 识别错误：漏除以 `n+1`。
3. 后台验证：对正确结果求导，确认导数回到 `$x^2$`。
4. 给分层提示：不直接骂错，也不直接只甩答案。
5. 更新学生状态：`幂函数积分` 掌握度下降或错因次数加一。

如果这个闭环跑通，项目就从“聊天机器人”变成“Tutor 产品”。

## 1. 推荐技术栈

### 1.1 前端

使用：

* Next.js App Router
* TypeScript
* Tailwind CSS
* shadcn/ui
* KaTeX
* Zustand 或 Jotai

理由：

* Next.js 适合快速做 AI Web App。
* Tailwind + shadcn/ui 能快速做出稳定、可维护的教学界面。
* KaTeX 渲染快，适合聊天中的公式。
* 状态管理只放前端临时状态，长期学习状态放后端。

### 1.2 后端

使用：

* Python FastAPI
* Pydantic
* SymPy
* SQLite 起步，后续迁移 PostgreSQL
* SQLAlchemy 或 SQLModel

理由：

* 数学验证天然适合 Python。
* 当前项目已经有 JSON 知识库和 Skill 文档，FastAPI 后端容易加载。
* SQLite 足够支撑本地 MVP，避免第一阶段被数据库部署拖住。

### 1.3 LLM 接入

第一版只抽象一个 `LLMClient` 接口，不在业务代码里绑定具体厂商。

```python
class LLMClient:
    async def stream(self, messages: list[dict], tools: list[dict] | None = None):
        ...
```

可选实现：

* OpenAI-compatible API
* 本地模型 API
* 其他云模型 API

要求：

* 支持流式输出。
* 支持系统提示词注入。
* 允许后端在响应前先做知识库检索和 SymPy 验证。

## 2. 目标目录结构

建议在当前仓库中演进为轻量 monorepo：

```txt
luojia-math-tutor-skill/
├─ apps/
│  ├─ web/
│  │  ├─ app/
│  │  │  ├─ page.tsx
│  │  │  ├─ layout.tsx
│  │  │  └─ tutor/[sessionId]/page.tsx
│  │  ├─ components/
│  │  │  ├─ tutor-chat.tsx
│  │  │  ├─ math-message.tsx
│  │  │  ├─ latex-input.tsx
│  │  │  ├─ mastery-panel.tsx
│  │  │  └─ hint-level-control.tsx
│  │  ├─ lib/
│  │  │  ├─ api.ts
│  │  │  ├─ stream.ts
│  │  │  └─ math-render.ts
│  │  └─ package.json
│  │
│  └─ api/
│     ├─ app/
│     │  ├─ main.py
│     │  ├─ config.py
│     │  ├─ api/
│     │  │  ├─ routes_tutor.py
│     │  │  ├─ routes_sessions.py
│     │  │  └─ routes_mastery.py
│     │  ├─ tutor/
│     │  │  ├─ orchestrator.py
│     │  │  ├─ intent_router.py
│     │  │  ├─ prompt_builder.py
│     │  │  ├─ hint_policy.py
│     │  │  └─ misconception.py
│     │  ├─ knowledge/
│     │  │  ├─ loader.py
│     │  │  ├─ search.py
│     │  │  └─ schema.py
│     │  ├─ math_tools/
│     │  │  ├─ verifier.py
│     │  │  ├─ step_checker.py
│     │  │  └─ graph.py
│     │  ├─ memory/
│     │  │  ├─ models.py
│     │  │  ├─ repository.py
│     │  │  └─ mastery.py
│     │  └─ llm/
│     │     ├─ client.py
│     │     └─ openai_compatible.py
│     ├─ tests/
│     │  ├─ test_knowledge_search.py
│     │  ├─ test_verifier.py
│     │  ├─ test_step_checker.py
│     │  └─ test_mastery.py
│     └─ pyproject.toml
│
├─ luojia-math-tutor/
│  ├─ SKILL.md
│  ├─ agents/openai.yaml
│  └─ references/
│
├─ scripts/
├─ README.md
└─ WEB_APP_IMPLEMENTATION_PATH.md
```

第一阶段不要移动现有 `luojia-math-tutor/`。后端通过相对路径读取它，保证 Skill 包仍然可单独使用。

## 3. 后端核心流程

### 3.1 Tutor Orchestrator

`apps/api/app/tutor/orchestrator.py`

职责：

1. 接收用户消息和会话状态。
2. 判断意图。
3. 检索知识库。
4. 调用数学验证器。
5. 构造 Tutor Prompt。
6. 流式返回教学回复。
7. 更新学生状态。

流程：

```txt
UserMessage
  ↓
IntentRouter
  ↓
KnowledgeSearch
  ↓
MathVerifier / StepChecker
  ↓
HintPolicy
  ↓
PromptBuilder
  ↓
LLM Stream
  ↓
Memory Update
```

### 3.2 意图分类

`intent_router.py`

第一版用规则 + LLM 轻分类，不要训练模型。

意图枚举：

```python
class Intent(str, Enum):
    CONCEPT = "concept"
    SOLVE_STEP_BY_STEP = "solve_step_by_step"
    CHECK_STUDENT_STEP = "check_student_step"
    FULL_SOLUTION = "full_solution"
    GENERATE_EXERCISE = "generate_exercise"
```

规则示例：

* 包含“完整解答”“标准答案”“直接给过程” -> `FULL_SOLUTION`
* 包含“我这样对吗”“这一步对吗”“为什么错” -> `CHECK_STUDENT_STEP`
* 包含“什么是”“怎么理解” -> `CONCEPT`
* 默认 -> `SOLVE_STEP_BY_STEP`

### 3.3 知识库检索

`knowledge/search.py`

第一版不做向量库，先做可解释的本地 JSON 检索：

1. 加载 `references/output/*.json`。
2. 标准化字段：
   * `id`
   * `subject`
   * `concept_zh`
   * `prerequisite`
   * `description`
   * `intuitive_explanation`
   * `solution`
3. 按关键词打分：
   * 概念名命中：+5
   * 前置知识命中：+3
   * 正文命中：+1
   * 学科匹配：+2
4. 返回 top 5。

接口：

```python
def search_knowledge(query: str, subject: str | None = None, limit: int = 5) -> list[KnowledgeHit]:
    ...
```

验收：

```txt
search_knowledge("二阶行列式") 必须命中 la.json 中的二阶行列式定义。
search_knowledge("幂函数积分") 必须命中高数或习题相关条目。
search_knowledge("泊松过程") 必须命中 Proba_example.json 或 proba.json。
```

## 4. 数学验证层

### 4.1 Verifier

`math_tools/verifier.py`

第一版支持 5 类验证：

```python
class VerifyType(str, Enum):
    EQUIVALENCE = "equivalence"
    DERIVATIVE = "derivative"
    INTEGRAL = "integral"
    MATRIX = "matrix"
    NUMERIC = "numeric"
```

核心函数：

```python
def verify_equivalent(lhs_latex: str, rhs_latex: str) -> VerifyResult:
    """
    判断两个表达式是否等价。
    第一版可先支持简单表达式字符串，不必完整支持 LaTeX AST。
    """
```

```python
def verify_derivative(expr: str, variable: str, expected: str) -> VerifyResult:
    """
    检查 d/dx expr 是否等于 expected。
    """
```

```python
def verify_integral(integrand: str, variable: str, candidate: str) -> VerifyResult:
    """
    检查 candidate 对 variable 求导后是否回到 integrand。
    """
```

### 4.2 Step Checker

`math_tools/step_checker.py`

目标：验证 `Step A -> Step B` 是否合理。

第一版只做表达式等价检查：

```python
def check_step(before: str, after: str) -> StepCheckResult:
    """
    返回：
    - is_valid: bool
    - reason: str
    - suspected_mistake: str | None
    """
```

示例：

```txt
before: ∫ x^2 dx
after: x^3

结果：
is_valid = false
suspected_mistake = "POWER_INTEGRAL_MISSING_DIVISOR"
reason = "对 x^3 求导得到 3x^2，不是 x^2。"
```

### 4.3 错因标签

`tutor/misconception.py`

先手写 20 个高频错因，不要一开始追求大而全。

高数第一批：

```python
POWER_INTEGRAL_MISSING_DIVISOR = "幂函数积分漏除以 n+1"
MISSING_INTEGRATION_CONSTANT = "不定积分漏写常数 C"
CHAIN_RULE_MISSING_INNER_DERIVATIVE = "链式法则漏乘内层导数"
LHOPITAL_WITHOUT_INDETERMINATE_FORM = "未确认未定式就使用洛必达"
EQUIVALENT_INFINITESIMAL_MISUSE = "等价无穷小使用条件错误"
SUBSTITUTION_BOUND_NOT_UPDATED = "定积分换元后上下限未同步变化"
SIGN_ERROR = "符号错误"
ALGEBRA_EXPANSION_ERROR = "代数展开错误"
```

线代第二批：

```python
DETERMINANT_ROW_OPERATION_ERROR = "行列式行变换倍数因子处理错误"
EIGENVECTOR_NOT_SUBSTITUTED = "特征向量未代回验证"
RANK_AND_DETERMINANT_CONFUSION = "混淆秩与行列式"
```

概率第三批：

```python
INDEPENDENCE_CONFUSION = "混淆独立与互斥"
PDF_NOT_NORMALIZED = "密度函数未归一化"
CONDITIONAL_PROBABILITY_DENOMINATOR_ERROR = "条件概率分母错误"
```

## 5. 学生状态层

### 5.1 数据库表

第一版 SQLite。

```sql
create table users (
  id text primary key,
  display_name text,
  created_at text not null
);

create table sessions (
  id text primary key,
  user_id text not null,
  title text,
  subject text,
  created_at text not null,
  updated_at text not null
);

create table messages (
  id text primary key,
  session_id text not null,
  role text not null,
  content text not null,
  intent text,
  created_at text not null
);

create table attempts (
  id text primary key,
  session_id text not null,
  user_id text not null,
  problem_text text not null,
  student_step text,
  is_correct integer,
  mistake_code text,
  verifier_summary text,
  created_at text not null
);

create table mastery (
  id text primary key,
  user_id text not null,
  concept text not null,
  score real not null,
  attempts_count integer not null default 0,
  correct_count integer not null default 0,
  updated_at text not null
);

create table mistake_events (
  id text primary key,
  user_id text not null,
  session_id text not null,
  mistake_code text not null,
  concept text,
  created_at text not null
);
```

### 5.2 掌握度更新

先用简单规则，不要上复杂知识追踪模型。

```python
def update_mastery(old_score: float, is_correct: bool, hint_level: int) -> float:
    if is_correct and hint_level == 0:
        return min(1.0, old_score + 0.08)
    if is_correct and hint_level > 0:
        return min(1.0, old_score + 0.03)
    return max(0.0, old_score - 0.06)
```

说明：

* `hint_level=0`：学生独立完成。
* `hint_level=1`：给过轻提示。
* `hint_level=2`：给过公式提示。
* `hint_level=3`：接近给出答案。

第一版先能记录和展示，不追求精确教育测量。

## 6. API 设计

### 6.1 创建会话

```http
POST /api/sessions
```

请求：

```json
{
  "user_id": "demo-user",
  "subject": "calculus",
  "title": "不定积分练习"
}
```

响应：

```json
{
  "session_id": "sess_123"
}
```

### 6.2 Tutor 流式回复

```http
POST /api/tutor/stream
```

请求：

```json
{
  "session_id": "sess_123",
  "user_id": "demo-user",
  "message": "我算 ∫ x^2 dx = x^3，对吗？",
  "mode": "socratic"
}
```

流式事件：

```txt
event: meta
data: {"intent":"check_student_step","concepts":["幂函数积分"],"verified":true}

event: token
data: {"text":"你的思路方向是对的：这是幂函数积分。"}

event: token
data: {"text":"不过这里少了一个关键系数..."}

event: done
data: {"message_id":"msg_456"}
```

### 6.3 获取掌握度

```http
GET /api/users/{user_id}/mastery
```

响应：

```json
{
  "items": [
    {
      "concept": "幂函数积分",
      "score": 0.52,
      "attempts_count": 4,
      "correct_count": 2
    }
  ]
}
```

### 6.4 生成类似题

```http
POST /api/exercises/similar
```

请求：

```json
{
  "user_id": "demo-user",
  "concept": "幂函数积分",
  "difficulty": 2,
  "count": 3
}
```

响应：

```json
{
  "exercises": [
    {
      "id": "ex_1",
      "text": "计算 $\\int x^5 dx$。",
      "answer": "$\\frac{x^6}{6}+C$",
      "concept": "幂函数积分"
    }
  ]
}
```

第一版可以先不暴露答案给前端，只用于后端批改。

## 7. 前端页面设计

### 7.1 首页

路径：`apps/web/app/page.tsx`

第一屏就是工作台，不做营销落地页。

布局：

```txt
左侧：课程与历史会话
中间：Tutor Chat
右侧：掌握度与错因面板
```

### 7.2 Tutor Chat

组件：`components/tutor-chat.tsx`

功能：

* 消息流式渲染。
* 支持 LaTeX。
* 支持“我想要提示 / 我想看完整解答”两个明确按钮。
* 学生可以提交“我的下一步”。
* 每条 AI 回复显示轻量状态：
  * 已检索知识库
  * 已后台验算
  * 未完成后台验算

### 7.3 LaTeX 输入

组件：`components/latex-input.tsx`

第一版不做复杂公式编辑器。支持：

* 普通文本输入。
* `$...$` 和 `$$...$$`。
* 常用公式快捷按钮：
  * 积分
  * 极限
  * 分式
  * 矩阵

### 7.4 掌握度面板

组件：`components/mastery-panel.tsx`

展示：

* 最近练习概念。
* 掌握度条。
* 高频错因。
* 推荐下一题。

不要做大仪表盘，第一版只做右侧窄栏。

## 8. Prompt 组织方式

不要把所有内容塞进一个巨型 prompt。按模块拼装。

`prompt_builder.py`：

```python
def build_tutor_prompt(
    skill_text: str,
    intent: Intent,
    knowledge_hits: list[KnowledgeHit],
    verifier_result: VerifyResult | None,
    student_state: StudentState,
) -> list[dict]:
    ...
```

系统提示组成：

1. `SKILL.md` 核心规则摘要。
2. 当前意图规则。
3. 命中的知识库条目。
4. 验证器结果。
5. 学生状态。
6. 输出约束。

关键约束：

```txt
默认不要一次性给完整答案。
如果用户明确要求完整解答，可以给完整过程。
如果 verifier_result 表示学生步骤错误，先肯定合理部分，再定位错误。
不要声称执行了未执行的验证。
```

## 9. 分阶段实施

### Phase 1：本地 Demo，预计 10 个工作日

目标：

> 文本题输入 -> 知识库检索 -> SymPy 验证 -> 流式 Tutor 回复。

任务拆分：

第 1 天：

* 建 `apps/web` Next.js 项目。
* 建 `apps/api` FastAPI 项目。
* 跑通前后端本地启动。

第 2 天：

* 前端完成三栏基础布局。
* 接入 KaTeX 渲染。
* 做静态假消息展示。

第 3 天：

* 后端实现 `/api/sessions`。
* 后端实现 SQLite 初始化。
* 前端能创建会话并进入 chat 页面。

第 4 天：

* 实现 `knowledge/loader.py`。
* 实现 `search_knowledge()`。
* 写 `test_knowledge_search.py`。

第 5 天：

* 实现 `math_tools/verifier.py`。
* 支持幂函数积分、简单求导、表达式等价。
* 写 `test_verifier.py`。

第 6 天：

* 实现 `intent_router.py`。
* 支持 5 类意图。
* 写规则测试。

第 7 天：

* 实现 `orchestrator.py`。
* 接入 LLM 流式输出。
* `/api/tutor/stream` 返回 SSE。

第 8 天：

* 前端接入 SSE。
* 消息逐字/逐块显示。
* 显示“已验证/未验证”状态。

第 9 天：

* 实现 `misconception.py` 第一批高数错因。
* 对 `∫x^n dx`、链式法则、漏常数做硬规则识别。

第 10 天：

* 实现 `mastery.py`。
* 右侧掌握度面板展示真实数据。
* 做 5 条端到端手工验收。

Phase 1 验收用例：

```txt
1. “什么是导数？”
   期望：命中概念讲解，给定义、直观解释、小问题。

2. “求 ∫ x^2 dx”
   期望：默认不直接完整剧透，先提示幂函数积分公式。

3. “我算 ∫ x^2 dx = x^3，对吗？”
   期望：识别错误，说明对 x^3 求导得到 3x^2。

4. “直接给完整过程”
   期望：允许完整解答。

5. “我的极限题能用洛必达吗？”
   期望：先检查是否未定式。
```

### Phase 2：Tutor 化，预计 4 周

目标：

> 系统能持续追踪学生状态，并根据错因给分层提示和类似题。

任务：

* 增加学生步骤提交模式。
* 完善 Step Checker。
* 建错因库 50 条。
* 支持类似题生成。
* 支持错题本。
* 支持会话标题自动生成。
* 加入练习完成后的复盘卡片。

验收：

* 同一个用户连续犯“漏积分常数”错误，系统能在后续不定积分题里主动提醒。
* 学生连续两次答错同一概念，系统降低提示难度，回溯前置知识。
* 学生完成一道题后，系统推荐 2 道同概念不同难度题。

### Phase 3：课程级 AI TA，预计 6-8 周

目标：

> 从单题 Tutor 变成课程学习系统。

任务：

* 增加课程空间：高数、线代、概率论。
* 增加章节视图。
* 增加知识点掌握地图。
* 支持上传讲义 PDF。
* 支持从讲义提取题目。
* 支持考前复习计划。
* 支持教师后台雏形。

验收：

* 用户能选择“高数-不定积分”进入练习。
* 系统能展示本章薄弱点。
* 系统能按错因推荐复习顺序。

## 10. 第一批开发 Ticket

### P0-1 初始化前端项目

交付：

* `apps/web` 可运行。
* 首页三栏布局。
* 本地命令：`npm run dev`。

完成标准：

* 打开浏览器能看到 Tutor 工作台。
* 有输入框、消息区、掌握度侧栏。

### P0-2 初始化后端项目

交付：

* `apps/api` 可运行。
* `/health` 返回 `{ "ok": true }`。
* 本地命令：`uvicorn app.main:app --reload`。

完成标准：

* 前端能请求 `/health`。

### P0-3 知识库加载器

交付：

* 加载 `luojia-math-tutor/references/output/*.json`。
* 标准化为统一 schema。
* 提供关键词检索。

完成标准：

* 测试覆盖 `二阶行列式`、`函数`、`泊松过程`。

### P0-4 SymPy 验证器

交付：

* 支持简单表达式等价。
* 支持候选积分结果验证。
* 支持简单导数验证。

完成标准：

* `x^3/3 + C` 对 `x^2` 判定正确。
* `x^3` 对 `x^2` 判定错误，并给出原因。

### P0-5 Tutor 流式接口

交付：

* `/api/tutor/stream`。
* SSE meta/token/done 三类事件。

完成标准：

* 前端能看到流式输出。
* meta 里包含 `intent`、`concepts`、`verified`。

### P0-6 错因识别

交付：

* 至少 8 个高数错因硬规则。
* 错因写入 `mistake_events`。

完成标准：

* 漏除以 `n+1`、漏 `+C`、链式法则漏内导都能识别。

### P0-7 学生状态面板

交付：

* `/api/users/{user_id}/mastery`。
* 前端右侧展示掌握度。

完成标准：

* 练习后刷新页面仍能看到掌握度变化。

## 11. 环境变量

后端：

```env
APP_ENV=local
DATABASE_URL=sqlite:///./luojia_tutor.db
KNOWLEDGE_ROOT=../../luojia-math-tutor/references
SKILL_FILE=../../luojia-math-tutor/SKILL.md
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

前端：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 12. 测试策略

### 12.1 后端单元测试

必须测：

* JSON 知识库加载。
* 关键词检索。
* SymPy 验证器。
* Step Checker。
* 错因识别。
* 掌握度更新。

### 12.2 前端最小测试

必须手工验收：

* LaTeX 正常渲染。
* 流式输出不卡死。
* 长公式不撑破布局。
* 移动端输入框可用。
* 掌握度侧栏在窄屏可折叠。

### 12.3 端到端测试题

第一批固定题：

```txt
1. 求 ∫ x^2 dx
2. 判断 ∫ x^2 dx = x^3 是否正确
3. 求 d/dx sin(x^2)
4. 判断 lim_{x->0} sin x / x
5. 解二阶行列式 |1 2; 3 4|
```

每次改 Orchestrator 或 Verifier 后都跑一遍。

## 13. 不要提前做的事

第一版不要做：

* OCR。
* PDF 解析。
* 向量数据库。
* Lean 证明。
* 班级管理。
* 复杂知识图谱。
* 多模型路由。
* 付费系统。

原因：

这些都不是第一版成败关键。第一版关键是：

> 学生给一步，系统能判断、引导、记录。

## 14. 成功标准

当以下 3 件事都成立，才进入 Phase 2：

1. 一个新用户能在 30 秒内开始问一道高数题。
2. 系统至少能稳定处理 20 道高数基础题。
3. 系统能记录并展示用户至少 5 类错因。

这三个没有完成前，不扩展 OCR、PDF、教师端。

## 15. 当前仓库与 Web App 的关系

当前仓库已有的资产：

* `luojia-math-tutor/SKILL.md`：Tutor 行为准则。
* `luojia-math-tutor/references/*.md`：知识库、交互、工具规范。
* `luojia-math-tutor/references/output/*.json`：结构化数学知识。
* `scripts/validate-json.js`：知识库合法性检查。

Web App 第一版要复用这些资产，而不是重写一套 prompt。

具体复用方式：

* 后端启动时加载 `SKILL.md`，提取核心教学约束。
* 检索模块读取 `references/output/*.json`。
* PromptBuilder 按意图读取对应 reference 摘要。
* Verifier 的行为边界遵守 `math-tools-guidelines.md`。
* Tutor 的交互节奏遵守 `interactive-tutoring.md`。

这样当前 Skill 项目会自然升级成 Web App 的教学内核。
