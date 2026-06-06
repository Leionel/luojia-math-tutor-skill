# 珞珈数智助教 (Luojia Math Tutor)

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**面向 STEM 教育的可验证学习智能体，以大学数学为首个落地场景。**

珞珈数智助教是一款基于大模型与数学物理符号运算的可验证学习智能体 Web 平台。系统将单纯的“AI 问答”重构为**具有持久化记忆、弱点洞察与教学步骤验证的自适应辅导系统**。项目采用双轨执行引擎，完美平衡了“大模型的启发式引导”与“符号引擎（SymPy）的确定性校验”。

---

## 🌾 核心设计美学：书院中国风 (Zen Academy Style)

平台摒弃了冷冰冰的科技蓝与千篇一律的暗黑风，首创**“书院中国风（Zen Academy Style）”**的教学设计理念，将学习比作知识的“沉淀”与“萌发”：

*   **自然色彩系统**：以宣纸白（`#faf7f2`）为背景底色，辅以茶绿（`#617a55`）作为主品牌色，点缀印章朱红（`#c44a3d`）和水墨黑（`#2a2b26`）。
*   **古典排版艺术**：引入 `Noto Serif SC` 与 `ZCOOL XiaoWei`（仿宋/小薇体）国风字体，配以竖排书法艺术字饰，实现温润儒雅的交互质感。
*   **国风学习意象**：
    *   **启发式萌发**：苏格拉底式提问引导，让知识的种子自行破土。
    *   **错题本沉淀**：收集学习漏洞，作为自适应巩固的养分。
    *   **动态水墨**：可视化图表与数学函数曲线，如水墨山水般呈现。

---

## 🚀 核心突破 (V4.0 功能矩阵)

项目已全面完成全场景学习闭环，包含以下核心模块：

### 1. 🎛️ 智能双栏工作台
*   **启发式苏格拉底对话**：引导式提问（Socratic Mode），只给思路，不漏答案，通过提问启发学生自主思考。
*   **智能随堂笔记 (Smart Notes)**：双栏布局，一键将冗长的问答记录提炼为排版极致优雅的 Markdown/LaTeX 笔记，支持直达笔记册 (`/notebook`)。
*   **A4 纸打印导出**：笔记册专为线下复习优化了 A4 排版格式，支持一键调用 `window.print()` 导出并自动隐藏非必要 UI。

### 2. 📊 错题沉淀与掌握度大盘 (Mistake Book & Mastery Dashboard)
*   **弱点自动侦测**：后台静默校验学生推导步骤，自动识别并分类错因（如符号错误、公式记错、边界条件遗漏等）。
*   **持久化错题本**：支持手动收藏与 AI 识别自动入库（SQLite 驱动），提供专属错题本视图 (`/mistake-book`)。
*   **自适应能力雷达图**：基于用户的做题与错题数据，在 `/dashboard` 中动态绘制多维度的“能力雷达图”，实时直观展示知识掌握度。
*   **举一反三 (Quiz Gen)**：针对错题一键生成概念相似、数值不同的复练题，真正打通学习闭环。

### 3. 🏷️ 无感化智能动态标签 (Dynamic AI Tagging)
*   **智能首问分类**：彻底抛弃繁琐的下拉框。大模型自动根据首条聊天内容分析并赋予精准的标签（如“微积分”、“矩阵变换”、“随机分布”）。
*   **侧边栏多维过滤**：历史对话栏支持根据动态标签一键聚合和筛选，支持会话的随时重命名与快速删除。

### 4. 🧮 状态机引擎与高阶交互
*   **LangGraph 推理闭环**：后端结合 `[PLAN] -> [VERIFY] -> [CORRECT] -> [OUTPUT]` 机制，使用 LangGraph 构建安全可靠的状态机调度流（State Graph）。使用 SymPy 拦截验证计算，彻底杜绝大模型数学幻觉。
*   **DeepSeek 专属隔离流**：针对 DeepSeek V4 深度推理模型，在底层设计了强类型的数据通道隔离机制，实时在前端展示模型原生的 `reasoning_content`（思考过程），并动态缓存处理历史回传防 400 报错，严防污染最终教学回答的正文。
*   **混合 RAG 检索引擎**：知识库不仅接入了大模型 Semantic Embedding 语义检索，更创新地引入了 BM25 纯本地关键字检索，并通过 RRF (Reciprocal Rank Fusion) 算法合并倒排。即使 API Token 耗尽或服务宕机，检索模块也能以 $\alpha=0$ 降级策略实现 100% 本地高可用。
*   **手写板与 OCR**：集成草稿板（Whiteboard），并接入 MinerU API 进行复杂的公式提取与图像拍照搜题识别。
*   **数学虚拟键盘**：内置定制的 LaTeX 数学键盘，降低用户输入复杂公式的门槛。
*   **语音播报 (TTS)**：支持将包含 LaTeX 公式的数学解题思路转化为自然的中文语音朗读。
*   **资源推荐**：自动联网检索并联想 Bilibili 相关考点的优质讲解视频。

---

## 📁 项目目录结构

```text
├── apps/web                     # Next.js 14 前端项目 (React, TypeScript, Tailwind)
│   ├── app/                     # App Router 路由 (chat, mistake-book, notebook, dashboard)
│   ├── components/              # 核心 UI 组件 (草稿板, 公式键盘, 消息泡, 雷达图等)
│   └── lib/                     # API 请求与前端封装
├── apps/api                     # FastAPI 后端项目 (Python, SymPy, SQLite)
│   ├── app/
│   │   ├── api/                 # API 路由接口 (会话, 错题, 掌握度, RAG, Bilibili)
│   │   ├── agents/              # 智能体组件 (Harness 质量评估器, Vision 识图)
│   │   ├── memory/              # SQLite 数据库模型与仓储 (repository.py)
│   │   └── tutor/               # 核心调度中枢 (orchestrator.py, prompt_builder.py)
│   └── pyproject.toml           # 依赖与打包配置
└── luojia-math-tutor/           # 珞珈数智助教核心 Skill 定义文件夹
    ├── SKILL.md                 # 助教的核心工作流提示词与平台联动指令
    └── references/              # 本地数学概念参考知识库与工具使用指南
```

---

## ⚙️ 本地快速部署

### 1. 前置准备
*   安装 [Node.js](https://nodejs.org/) (v18+)
*   安装 [Python](https://www.python.org/) (v3.10+)

### 2. 配置环境变量

**后端配置**：在 `apps/api/` 下创建 `.env`，参考 `apps/api/.env.example`：
```env
APP_ENV=local
DATABASE_URL=sqlite:///./luojia_tutor.db
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your_deepseek_api_key
LLM_MODEL=deepseek-chat
ALLOW_USER_API_KEY=true
```

**前端配置**：在 `apps/web/` 下创建 `.env.local`：
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. 安装与运行

在根目录下使用以下命令启动全栈服务：

```bash
# 1. 安装前端依赖并运行
cd apps/web
npm install
npm run dev

# 2. 安装后端依赖并运行 (新终端)
cd apps/api
pip install -e .
python -m uvicorn app.main:app --reload --port 8000
```

你也可以在根目录下直接使用脚本：
*   启动 API 端：`npm run dev:api`
*   启动 Web 端：`npm run dev:web`

启动成功后，打开浏览器访问 [http://localhost:3000](http://localhost:3000) 即可开启学习之旅。

---

## 🧪 自动化测试与质量校验

项目内置了完整的校验链条，可以通过根目录的测试指令验证系统正确性：

```bash
# 执行全部校验 (包含知识库 JSON 格式自检与 API 端 pytest)
npm test

# 仅执行数学知识库 JSON 校验
npm run test:knowledge

# 仅运行后端 API 测试
npm run test:api
```

---

## 💡 经典演示路径 (演示建议)

你可以使用以下数学典型问题来体验完整的“启发式引导 + 错题记录 + 掌握度分析”闭环：

1.  **初次试探（触发引导）**：输入 `“我算 ∫ x^2 dx = x^3，对吗？”`
    *   *AI 表现*：后台会静默通过 SymPy 验算得出错误，识别原因为“漏掉常数项或系数算错”，并在前端给出考点分析，以苏格拉底式提问引导你发现漏了什么（不直接说答案）。
2.  **查看面板**：右侧学习面板会展现被识别的考点（不定积分）和掌握度。
3.  **整理随堂笔记**：点击输入框上方的“生成随堂笔记”按钮，AI 会提炼本段对话并自动在 `/notebook` 视图生成漂亮的 LaTeX 整理文档。
4.  **错题本与雷达图**：点击该题的“加入错题本”按钮，然后访问 `/dashboard` 和 `/mistake-book`，可以看见错题记录和更新后的掌握度能力雷达图。
5.  **举一反三**：在错题本卡片上点击“举一反三”，系统将基于该错题考点自动生成一道相似计算，测试你是否真正掌握。

---

## 👥 许可证与说明

*   本项目核心代码、脚本及 Skill 配置遵循 [MIT License](LICENSE)。
*   `luojia-math-tutor/references/textbook/` 下的教材 PDF 仅供本地科研与学习参考，请在遵守法律的前提下合规使用。
