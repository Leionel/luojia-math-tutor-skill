# MVP-0 初始化说明（珞珈数智助教 Web App）

## 1. 目标与范围

本项目当前按 MVP-0 目标推进：本地开发版、多学科（高数/线代/概率论）、轻状态 AI Tutor。
核心闭环为：用户提问/提交步骤 -> 识别意图与学科 -> 检索本地知识库 -> SymPy 验证 -> LLM 生成回复 -> 落库会话与错因事件。

## 2. 当前实现对照（结论）

整体结论：**主干结构和核心能力已按方案落地，后端测试通过，前端生产构建通过。**

已对齐项（已实现）：
- Monorepo：`apps/web`、`apps/api` 已存在。
- 后端核心模块：`routes_sessions.py`、`routes_tutor.py`、`routes_models.py`、`knowledge/*`、`math_tools/*`、`tutor/*`、`llm/openai_compatible.py`、`memory/*` 已存在。
- API 路由：`GET /health`、`POST /api/sessions`、`GET /api/sessions`、`GET /api/sessions/{session_id}/messages`、`POST /api/tutor/stream`、`GET /api/sessions/{session_id}/mistakes`、`POST /api/models/test` 已实现。
- SQLite 轻状态表：`users/sessions/messages/attempts/mistake_events` 已初始化创建。
- 前端主页面：`/` 直接是 Tutor 工作台（非 landing page），核心组件已存在。
- 模型接入：OpenAI-compatible 抽象已实现，支持平台 Key 与用户 Key（用户 Key 从前端传入）。
- 知识库来源：读取 `luojia-math-tutor/SKILL.md` 与 `references/output/*.json`。
- 测试：`pytest apps/api/tests -q` 通过。

## 3. 目录说明

- 前端：`apps/web`
- 后端：`apps/api`
- 知识库与技能：`luojia-math-tutor`

## 4. 环境变量

### 后端（`apps/api/.env`）

```env
APP_ENV=local
DATABASE_URL=sqlite:///./luojia_tutor.db
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=
LLM_MODEL=deepseek-chat
ALLOW_USER_API_KEY=true
```

说明：
- 若请求传 `user_api_key` 且 `ALLOW_USER_API_KEY=true`，优先使用用户 Key。
- 否则使用平台 `LLM_API_KEY`。
- 请求级 `model` 支持 `deepseek-v4-flash`、`deepseek-v4-pro`、`deepseek-chat`；非法模型回退到环境变量 `LLM_MODEL` 或 `deepseek-chat`。

### 前端（`apps/web/.env.local`）

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 5. 本地启动

1. 启动后端（FastAPI）：
   - 工作目录：`apps/api`
   - 启动命令：`uvicorn app.main:app --reload --port 8000`

2. 启动前端（Next.js）：
   - 工作目录：`apps/web`
   - 启动命令：`npm run dev`
   - 默认访问：`http://localhost:3000`

## 6. 快速验收清单

- 健康检查：`GET /health` 返回 `{ "ok": true }`。
- 创建会话：`POST /api/sessions` 返回 `session_id`。
- Tutor 流式：`POST /api/tutor/stream` 能收到 `meta -> token -> done`。
- 模型连通：`POST /api/models/test` 可验证平台 Key 或用户 Key。
- 前端输入 `$\int x^2 dx = x^3$` 后：
  - 对话区公式渲染正常；
  - 右侧能看到验证状态与错因；
  - 会话刷新后可恢复历史。

## 7. 端到端验收题（MVP-0）

| 题目 | 期望验证行为 |
|------|-------------|
| `我算 ∫ x^2 dx = x^3，对吗？` | 识别幂函数积分，验证不通过，错因：漏除以 n+1 |
| `求 d/dx sin(x^2)` | 识别链式法则求导，给出求导结果 |
| `这个极限能直接用洛必达吗：lim x->0 sinx/x` | 识别 0/0 未定式，确认可用洛必达 |
| `计算二阶行列式 \|1 2; 3 4\|` | 识别二阶行列式，计算值为 -2 |
| `A、B 互斥是不是就独立？` | 识别互斥与独立混淆，给出概念区分 |

## 8. 根脚本

```bash
# 运行全部测试（知识库校验 + 后端 pytest）
npm test

# 仅知识库校验
npm run test:knowledge

# 仅后端测试
npm run test:api

# 启动后端开发服务
npm run dev:api

# 启动前端开发服务
npm run dev:web

# 前端生产构建验证（在 apps/web 目录）
npm.cmd run build
```
