# 珞珈数智助教（Luojia Math Tutor）

[![Claude](https://img.shields.io/badge/Claude-Skill-blue)](https://claude.com/claude-code)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**面向 STEM 教育的可验证学习智能体，以大学数学为首个落地场景。**

珞珈数智助教最初是一个数学 AI Tutor Skill，现在已经扩展为本地可运行的 Web App。项目通过大模型完成自然语言理解、教学规划和表达生成，通过本地知识库提供课程依据，通过 SymPy/Python 工具验证关键推导步骤，并结合错因记录、掌握度和类似题训练形成学习闭环。

当前版本聚焦高数、线代、概率论三类大学数学基础内容，可用于演示“生成式 AI + 符号验证 + 错因记忆 + 自适应练习”的可验证 Tutor Agent。

## 项目定位

本项目不只是一个“会讲题”的聊天机器人，而是一个可验证学习智能体：

- **Planning**：识别学科、题型、用户意图和教学模式。
- **Knowledge Grounding**：检索本地结构化数学知识库。
- **Tool Use**：调用 SymPy/Python 对关键步骤进行确定性验算。
- **Memory**：记录会话、消息、尝试、错因事件和轻量掌握度。
- **Adaptive Feedback**：根据错因、掌握度和用户模式调整提示层级。
- **Practice Loop**：基于当前考点生成类似题，支持复练闭环。

面向比赛或路演时，推荐表述为：

> 珞珈数智助教是面向 STEM 教育的可验证学习智能体，以大学数学为首个落地场景，构建“生成式 AI + 符号验证 + 错因记忆 + 自适应练习”的学习闭环。

## 当前能力

### 🖥️ Tutor 工作台 (App 端详细介绍)

基于 Next.js App Router + TypeScript + TailwindCSS 构建，采用了**“几何静默 (Geometric Silence)”**的东方极简融合 Cyberpunk 专属设计美学（深色毛玻璃、青/墨绿/赤红强调色、呼吸动效）。

1. **四大学习模式**
   - **引导模式 (Socratic)**：采用苏格拉底式提问，一步步引导自行推导，培养数学直觉。
   - **直接讲解 (Direct)**：直接给出详尽、严谨的数学推导过程和最终答案。
   - **练习模式 (Practice)**：智能生成难度递进的相似练习题，辅助巩固概念。
   - **整理笔记 (Notes)**：化身知识萃取机，将凌乱草稿提炼为极致排版的 Markdown/LaTeX 笔记。

2. **三大场景分类**
   - **基础概念**：侧重于对定义、定理来源的通俗化解释，帮助扫盲并建立直觉基石。
   - **深度推导**：侧重于严谨的数学推演、证明步骤与逻辑链条，适合冲刺高分的拔高训练。
   - **实战解题**：侧重于解题技巧、套路总结和错题分析，直接面向应试拿分。

3. **沉浸式画板与识图 (Whiteboard & OCR)**
   - 内置全屏级沉浸式草稿板，支持手写绘图推演。
   - 接入 **MinerU API** 进行多模态深度公式识别提取。
   - 配备了优雅的全局网络代理防呆拦截弹窗，防止上传超时。

4. **全局错题本与 A4 打印导出**
   - SQLite 自动记忆错因与考点，生成专属错题本。
   - 专为线下复习优化的 **A4 纸打印排版格式**，自动留出笔记书写空间并隐藏非必要 UI。

### 🧮 可验证数学推理 (后端能力)

- 后端使用 FastAPI + Pydantic + SymPy + SQLite。
- 支持积分候选验证、求导验证、矩阵计算、二阶行列式、洛必达条件判断等基础能力。
- **StepChecker** 可识别学生步骤中的常见错误。
- **Misconception** 规则库记录高数、线代、概率论常见错因。
- SSE 返回稳定的 `meta/token/done` 事件，前端可实时展示验证状态和错因。

### 🔄 学习闭环

- SQLite 保存会话、消息、尝试、错因事件和轻量掌握度。
- 错题本 API 支持按用户聚合错因。
- **Mastery** 记录概念掌握度变化。
- **Hint Policy** 根据掌握度、连续错误和用户请求调整提示深度。
- **复盘卡片** 用于总结本题考点、判断、错因和下一步建议。
- **类似题 API** 支持围绕当前概念生成复练题。

### 🌐 多模态与视频资源

- 首页采用 Bento Grid（便当盒）布局一览系统核心特色。
- 可视化接口支持生成函数曲线、积分面积、概率密度等基础图像。
- 视频推荐接口可搜索 Bilibili 视频，并提供本地兜底结果辅助学习。

### 🧠 最强多模型接入基座

内置统一 OpenAI-compatible LLM Client，已配置 2026 年最新地表最强模型矩阵：
- **海外旗舰**：OpenAI (GPT-5.5 / GPT-5.5 Pro / GPT-5.3 Codex / o1), Anthropic (Claude Opus 4.8 / Sonnet 4.6), Google (Gemini 3.5 Flash / 3.1 Pro)。
- **国产巅峰**：DeepSeek (v4 Flash / v4 Pro), 通义千问 (Qwen3.7-Max), Kimi (K2.6 / K2.5), 智谱 (GLM-5 / GLM-5-Turbo)。
- 支持平台统一 Key 或 用户自定义前端 Key，保障数据安全与灵活性。

## 技术架构

```text
用户输入/图片上传
  -> Intent Router
  -> Knowledge Search
  -> Step Checker / Verifier
  -> Misconception Detector
  -> Hint Policy
  -> Prompt Builder
  -> OpenAI-compatible LLM Stream
  -> Memory Update
  -> Review / Similar Exercise / Learning Panel
```

核心目录：

```text
apps/web                       Next.js Tutor 工作台
apps/api                       FastAPI 后端
luojia-math-tutor/SKILL.md     数学助教核心工作流与提示约束
luojia-math-tutor/references   本地知识库、工具规范与参考资料
scripts/validate-json.js       知识库 JSON 校验脚本
```

## 本地启动

### 1. 环境变量

后端参考 `apps/api/.env.example`：

```env
APP_ENV=local
DATABASE_URL=sqlite:///./luojia_tutor.db
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=
LLM_MODEL=deepseek-chat
ALLOW_USER_API_KEY=true
```

前端参考 `apps/web/.env.local.example`：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 2. 安装依赖

前端：

```bash
cd apps/web
npm install
```

后端建议在 Python 3.10+ 环境中安装：

```bash
cd apps/api
python -m pip install -e .
```

如果当前环境不支持 editable install，也可以安装主要依赖：

```bash
python -m pip install fastapi uvicorn pydantic sympy httpx pytest
```

### 3. 启动后端

```bash
cd apps/api
python -m uvicorn app.main:app --reload --port 8000
```

健康检查：

```bash
curl http://localhost:8000/health
```

预期返回：

```json
{"ok": true}
```

### 4. 启动前端

```bash
cd apps/web
npm run dev
```

打开：

```text
http://localhost:3000
```

也可以在根目录使用脚本：

```bash
npm run dev:api
npm run dev:web
```

## API 概览

主要 API：

- `GET /health`
- `POST /api/sessions`
- `GET /api/sessions`
- `GET /api/sessions/{session_id}/messages`
- `GET /api/sessions/{session_id}/mistakes`
- `POST /api/tutor/stream`
- `POST /api/models/test`
- `GET /api/users/{user_id}/mastery`
- `GET /api/users/{user_id}/mastery/summary`
- `GET /api/users/{user_id}/mistakes`
- `POST /api/exercises/similar`
- `POST /api/viz/plot`
- `POST /api/uploads`
- `GET /api/resources/bilibili/search`

`POST /api/tutor/stream` 支持请求级模型覆盖：

```json
{
  "session_id": "sess_xxx",
  "user_id": "demo-user",
  "message": "我算 ∫ x^2 dx = x^3，对吗？",
  "subject": "calculus",
  "mode": "socratic",
  "model": "deepseek-v4-flash",
  "user_api_key": null
}
```

SSE 事件包含：

```text
event: meta
event: token
event: done
```

部分版本还会发送：

```text
event: thinking_start
event: thinking
event: thinking_end
event: review
event: video_recommend
```

## 质量检查

根目录：

```bash
# 知识库校验 + 后端测试
npm test

# 仅校验知识库 JSON
npm run test:knowledge

# 仅后端测试
npm run test:api

# 前端生产构建
npm run build:web
```

前端目录：

```bash
cd apps/web
npm.cmd run build
```

注意：后端测试依赖当前 Python 环境中已安装 `fastapi/sympy/httpx/pytest` 等依赖。如果根目录 `npm test` 报 `ModuleNotFoundError`，请先按“安装依赖”部分配置后端环境。

## 演示验收题

建议用以下问题验证核心闭环：

```text
1. 我算 ∫ x^2 dx = x^3，对吗？
2. 求 d/dx sin(x^2)
3. 这个极限能直接用洛必达吗：lim x->0 sinx/x
4. 计算二阶行列式 |1 2; 3 4|
5. A、B 互斥是不是就独立？
```

预期效果：

- 对话区流式输出 Tutor 式回复。
- 公式正常渲染。
- 后端可识别考点、验证状态和错因。
- 右侧学习面板展示当前考点、错因、掌握度和下一步建议。
- 错因进入本地记录，刷新后会话历史仍可恢复。

## 参赛叙事与路线图

本项目可包装为生成式 AI 智能体赛道作品：

> 面向 STEM 教育的可验证学习智能体。

阶段路线：

```text
Phase 1：数学 Tutor MVP
对话、检索、验算、错因记录。

Phase 2：课程学习闭环
掌握度、提示层级、错题本、类似题、复盘卡片、可视化辅助。

Phase 3：STEM 可验证学习智能体平台
扩展到物理、统计、电路等强推理课程，并提供教师端分析和教育机构 API。
```

相关文档：

- [MVP0_INIT_GUIDE.md](./MVP0_INIT_GUIDE.md)
- [CRAIC_AGENT_TRACK_EXTENSION.md](./CRAIC_AGENT_TRACK_EXTENSION.md)
- [PHASE2_PHASE3_BRIDGE.md](./PHASE2_PHASE3_BRIDGE.md)
- [PHASE3_STEM_AGENT_PLATFORM.md](./PHASE3_STEM_AGENT_PLATFORM.md)
- [WEB_APP_IMPLEMENTATION_PATH.md](./WEB_APP_IMPLEMENTATION_PATH.md)

## Skill 模式

本仓库仍保留原始 Skill 使用方式。你可以通过 `npx` 或手动配置，让其他 AI 工具读取 `luojia-math-tutor/SKILL.md` 和本地知识库。

自动初始化：

```bash
npx github:Leionel/luojia-math-tutor-skill
```

手动配置：

- Gemini CLI：在项目指令中引用 `luojia-math-tutor/SKILL.md`。
- Claude Code：将 `SKILL.md` 作为 System Prompt 或项目说明。
- Cursor / Windsurf / VSCode Copilot / Cline：在规则文件中引用 `SKILL.md` 与 `references/`。

## 许可与资源说明

本仓库中的代码、脚本与 Skill 指令文本采用 MIT License。

`luojia-math-tutor/references/textbook/` 下的教材 PDF 仅作为本地学习参考资源，请在拥有合法使用权的前提下使用；如需再分发或公开发布，请自行确认对应教材、出版社或作者授权。

## 贡献

欢迎提交 Issue 或 PR，一起完善可验证学习智能体、数学知识库、错因规则和 STEM 课程扩展能力。

关联主项目：[Leionel/luojia-math-tutor](https://github.com/Leionel/luojia-math-tutor)

