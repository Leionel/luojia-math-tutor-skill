# MVP-0 完善计划：珞珈数智助教 Web App

## Summary

当前 MVP 主体已搭好：`apps/web`、`apps/api`、核心 API、SQLite 轻状态、SSE、知识库检索、基础 SymPy 验证、DeepSeek/OpenAI-compatible 接入都已存在。后端测试通过，前端生产构建通过。

本轮完善目标限定为：**把用户给出的 MVP-0 方案补齐到可本地验收状态**，不进入 OCR、PDF、向量库、登录、长期画像、教师后台等 Phase 2/3 能力。

## Key Changes

- 后端补齐 MVP 题型闭环：
  - 扩展 `Verifier/StepChecker`，覆盖 5 个端到端验收题：幂函数积分、链式法则求导、洛必达条件判断、二阶行列式、互斥与独立区分。
  - 保持轻量规则实现，不引入向量库或复杂 CAS 流程。
  - `meta` 中稳定返回 `intent/subject/concepts/verified/is_correct/mistake/verifier_summary`，右侧栏可直接消费。

- 模型设置补齐：
  - 前端设置区明确区分“平台默认 Key”和“用户自带 Key”。
  - 模型下拉固定支持 `deepseek-v4-flash`、`deepseek-v4-pro`、`deepseek-chat`。
  - `/api/models/test` 和 `/api/tutor/stream` 都支持请求级 `model` 覆盖；后端加 allowlist，非法模型回退到环境变量 `LLM_MODEL`。
  - 用户 Key 与模型选择只存浏览器本地，不入库。

- 前端工作台补齐：
  - 输入区完善三个动作按钮：`要提示`、`看完整解答`、`生成类似题`。
  - 保留 `Enter` 发送、`Shift+Enter` 换行。
  - 移动端增加左侧会话/课程抽屉和右侧学习状态抽屉，桌面端仍保持三栏。
  - 统一中文 UI 文案，避免 PowerShell 显示编码问题影响判断；文件继续保存为 UTF-8。

- UI 组件整理：
  - 新增本地 `components/ui` 基础组件（Button/Input/Textarea/Select/Sheet/Card 风格），按 shadcn/ui 的使用方式组织，但不依赖网络安装。
  - 将现有按钮、选择框、输入框迁移到这些组件，减少散落样式。
  - 保持当前简洁工具型界面，不做 landing page。

- 文档与工程化：
  - 更新 `MVP0_INIT_GUIDE.md` 和 `README.md`，写清本地启动、环境变量、模型切换、验收题。
  - 新增 `.env.example`：后端 LLM/SQLite 配置，前端 `NEXT_PUBLIC_API_BASE_URL`。
  - 根脚本补齐：`test` 继续跑知识库校验和后端测试；新增/确认前端 build 验证脚本。
  - 不改动 `luojia-math-tutor/` 既有 skill 目录结构。

## Public Interfaces

- `POST /api/tutor/stream` 请求体保持兼容，新增可选字段：
  - `model?: "deepseek-v4-flash" | "deepseek-v4-pro" | "deepseek-chat"`
- `POST /api/models/test` 请求体保持兼容，新增可选字段：
  - `model?: "deepseek-v4-flash" | "deepseek-v4-pro" | "deepseek-chat"`
- SQLite 表结构不新增，不加 mastery，不保存用户 API Key。

## Test Plan

- 后端自动测试：
  - 知识库 5 个 JSON 全加载。
  - 检索命中：`二阶行列式`、`幂函数积分`、`条件概率`。
  - Verifier：积分正确/错误、链式法则、矩阵乘法、二阶行列式。
  - StepChecker：漏除以 `n+1`、漏 `+C`、条件概率分母错误、互斥/独立混淆、洛必达条件误用。
  - API：会话创建、消息读取、mistakes 读取、model test、SSE `meta/token/done` 基本格式。

- 前端验证：
  - `npm.cmd run build` 在 `apps/web` 通过。
  - 输入 `$\\int x^2 dx = x^3$` 后公式正常渲染，右侧显示验证状态与错因。
  - `Enter` 发送，`Shift+Enter` 换行。
  - 三个动作按钮分别触发提示、完整解答、类似题。
  - 模型切换到 v4-flash/v4-pro 后，请求体携带对应模型。
  - 刷新页面后本机会话历史仍可恢复。
  - 移动端可打开会话抽屉和学习状态抽屉。

- 端到端验收题：
  - `我算 ∫ x^2 dx = x^3，对吗？`
  - `求 d/dx sin(x^2)`
  - `这个极限能直接用洛必达吗：lim x->0 sinx/x`
  - `计算二阶行列式 |1 2; 3 4|`
  - `A、B 互斥是不是就独立？`

## Assumptions

- 本轮只完善 MVP-0，不扩展到登录、长期 mastery、OCR/PDF、向量库、知识图谱或公网部署。
- DeepSeek 模型名按用户指定落地为 `deepseek-v4-flash` 与 `deepseek-v4-pro`，并保留 `deepseek-chat` 作为默认兼容项。
- shadcn/ui 以本地组件结构和样式约定补齐，不依赖联网执行 shadcn CLI。
- 当前 PowerShell 输出乱码是终端编码显示问题；代码文件按 UTF-8 读取时中文正常。
