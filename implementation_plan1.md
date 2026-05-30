# 智启助教：全面实现 Phase 2 前端闭环与多模型接入架构方案

## [Goal Description]

根据您“全部实现”的指示以及所要求的高端前沿设计（canvas-design / frontend-design），本次任务将对当前的 App 端（前端）进行一次彻底的升维改造，同时在后端扩充对更多主流 AI 模型厂商（如通义千问、Kimi、智谱、百川等）的支持。目标是打通整个 Phase 2 学习闭环，并赋予产品博物馆级别的顶级 UI 质感。

## 方案与架构详解

### 1. 前端（App 端）学习闭环模块补齐
- **真实掌握度数据面板 (Mastery Panel)**
  - 在 `learning-panel.tsx` 中接入 `GET /api/users/{user_id}/mastery` 接口。
  - 使用视觉极简、极具呼吸感的进度条（Progress Bars）渲染学生对各个知识点的实时掌握度。
- **分步验证模式开关 (Step Submit Mode)**
  - 改造 `tutor-input.tsx`，引入极致顺滑的 Toggle 动画，使用户可以无缝在“自然聊天”与“分步推导提交”模式间切换。
- **错题本与复盘卡片 (Mistake Book & Review Card)**
  - 新增 `components/review-card.tsx` 组件。在某一道题辅导结束后自动弹出优雅的卡片，总结错因、展示掌握度涨跌，并提供“生成类似题”入口。
  - 新增侧边栏入口，跳转到全局的 `mistake-book.tsx` 组件，使用时间轴或分类卡片回顾历史错因。
- **多模态与资源推荐气泡 (Visualizer & Video Recommendations)**
  - 升级 `math-message.tsx` 组件，使其能原生地解析后端传来的静态图片（如 Matplotlib 画的积分面积图）以及以极简信息流风格展示的 B 站推荐视频卡片（如 3Blue1Brown）。

### 2. 多模型大厂生态接入 (AI Providers Expansion)
- **后端模型网关扩展 (`openai_compatible.py`)**：
  - 目前仅支持 DeepSeek 系。将对接口网关进行扩展，原生内置对 **Qwen (阿里云通义千问)**、**Moonshot (Kimi)**、**ZhipuAI (智谱GLM)** 等国内第一梯队模型 API 的 BaseURL 与路由映射。
- **前端厂商选择器 (`settings-drawer.tsx` / `app-header.tsx`)**：
  - 在设置面板中引入一个高级的下拉菜单或图标网格，允许用户自由切换背后的驱动厂商，并在切换时保留优美的微动画过渡。

### 3. 前端先锋设计与视觉重构 (Canvas & Frontend Design)
根据 `frontend-design` 与 `canvas-design` 的理念，我们将完全摒弃“AI生成感”的普通排版：
- **美学运动定义：【Geometric Silence (几何静默)】**
  - **核心理念**：通过严密控制的网格体系与极简的色彩来传达复杂的数理逻辑。摒弃大面积的花哨渐变，采用深邃黑/纯净白为底色，以高饱和的单一强调色（如克莱因蓝或荧光青）作为点睛。
  - **视觉落地**：页面将拥有大量留白（Negative Space），使用高级非衬线字体（如 Inter 变体或单宽代码字体）展示数字和公式；卡片边缘锐利，微动效极度克制但丝滑。
  - **艺术级落地页 (Splash Canvas)**：我们将编写一个纯前端的展示型 Poster 页面（挂载于 `/splash` 或类似路由），通过 CSS 滤镜、数学几何图形的交错重叠，展现一份名为《The Architecture of Logic》的概念海报，作为对项目的艺术献礼。

---

## User Review Required

> [!IMPORTANT]  
> **视觉基调确认**：本次重构将应用极简、带有“Brutalist / 几何静默”风格的先锋设计，字体与留白将比原先更夸张和艺术化。您是否接受这种具有强烈辨识度、偏向高端极客审美的 UI 质感？

## Verification Plan

### Automated Tests
1. 重启 `npm run dev:web` 和 `dev:api`。
2. 调用 `/api/models/test` 测试新增的不同厂商模型通道（如配置有对应 Key 的情况下）。

### Manual Verification
1. 在网页侧边栏观察**真实掌握度进度条**的渲染和数据加载情况。
2. 试用底部的**分步检查模式**开关，观察 UI 状态切换。
3. 唤出**错题本**和**复盘卡片**，检查其渲染的艺术美感是否达到“几何静默”的设计标准。
4. 访问我们用代码绘制的前端海报概念页。
