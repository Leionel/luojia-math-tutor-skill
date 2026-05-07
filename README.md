# 珞珈数智助教 (Luojia Math Tutor) 🎓

[![Claude](https://img.shields.io/badge/Claude-Skill-blue)](https://claude.com/claude-code)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Leionel/luojia-math-tutor-skill?style=social)](https://github.com/Leionel/luojia-math-tutor-skill)

**通用化、启发式、硬核数学 AI 助教。**

本项目是一个高度结构化的 AI 指令集（Skill），旨在将任意主流 AI（Gemini, Claude, GPT）转化为一位硬核数学助教。基于 [Leionel/luojia-math-tutor](https://github.com/Leionel/luojia-math-tutor) 的核心算法与知识库进行全平台适配优化。

无需复杂的服务器配置，通过简单的文件引用即可在全平台适配。

---

## 🌟 核心特性

- **启发式引导**：拒绝直接给出答案，通过分步提问引导学生思考。
- **可视化解惑**：指导 AI 调用其内置 Python 环境绘制 3D 几何、概率分布图。
- **暗箱验算**：要求 AI 必须通过符号计算（SymPy）校验过程，确保数学逻辑无幻觉。
- **数学建模支援 (NEW!)**：支持国赛/美赛等开放性问题，指导假设构建与 Python 仿真（SciPy/NetworkX）。
- **考研特训模式 (NEW!)**：随机生成硬核综合题，并像真实阅卷老师一样给出红笔批改与降维解析。
- **本地权威库**：内置同济、武大、浙大等主流教材的结构化定义与定理。

---

## 🚀 全平台快速上手 (免 MCP 模式)

通过 `npx` 或手动配置，让你的 AI 自动学习本项目中的“助教大脑”。

### 1. 自动初始化 (推荐)
在你的数学学习项目根目录下运行：
```bash
# 自动将本项目指令注入到当前目录的 AI 配置文件中并拉取知识库
npx github:Leionel/luojia-math-tutor-skill
```

### 2. 手动配置方案

#### **方案 A：针对 Claude Code / Gemini CLI**
在项目根目录创建或编辑配置文件，添加以下核心指令：
- **Gemini CLI**: `gemini install luojia-math-tutor.skill` (直接安装打包好的包)
- **Claude Code**: 在对话开始前，直接将 `luojia-math-tutor/SKILL.md` 的内容粘贴为 System Prompt，或在项目说明中指定：
  > "请严格遵循 ./luojia-math-tutor/SKILL.md 中的助教工作流进行所有数学问题的解答。"

#### **方案 B：针对 Cursor / Windsurf / VSCode Copilot / Cline**
在项目根目录创建 `.cursorrules` (或 `.clinerules`)，内容如下：
```markdown
# 珞珈助教激活指令
1. 立即读取并内化 ./luojia-math-tutor/SKILL.md 中的人设与行为准则。
2. 解题时，必须优先检索 ./luojia-math-tutor/references/ 下 a JSON/PDF 知识库。
3. 严格执行“思路提示 -> 代码验算 -> 分步提问”的工作流。
```

---

## 🌌 技能生态矩阵 (Skill Ecosystem)

本项目不仅是一个数学助教，更是学术技能生态的枢纽。通过联动以下专业 Skill，提供全链路学术支持：

| 关联技能 | 核心能力 | 来源致谢 |
| :--- | :--- | :--- |
| **math-modeling** | 竞赛级模型构建与论文推导 | [XiaoMaColtAI/math-modeling-skill](https://github.com/XiaoMaColtAI/math-modeling-skill) |
| **Real Literature Trace** | 真实论文检索与溯源 | [LigphiDonk/academic-skills](https://github.com/LigphiDonk/academic-skills) |
| **Academic Figure Prompt** | 顶会级学术论文配图提示词 | [LigphiDonk/academic-skills](https://github.com/LigphiDonk/academic-skills) |

---

## 📂 项目结构 (大脑组成)
- `luojia-math-tutor/SKILL.md`: **核心大脑**。包含了所有的人设约束、工作流和输出模板。
- `luojia-math-tutor/references/`: 
  - `output/`: 结构化知识库 (GS/LA/Proba)。
  - `math-tools-guidelines.md`: 规范 AI 如何使用 Python 工具。
  - `interactive-tutoring.md`: 规范 AI 如何进行启发式提问。

---

## 🤝 贡献与反馈
本项目源自对硬核数学教育的热爱，欢迎在 GitHub 上提交 Issue 或 PR，一起完善助教的知识库！
关联主项目：[Leionel/luojia-math-tutor](https://github.com/Leionel/luojia-math-tutor)

---

## 💡 为什么这种模式更通用？
这种“指令+本地库”的模式不需要 AI 客户端支持特定协议（如 MCP），只要 AI 具备“文件读取”和“Python 执行”能力（目前主流 AI 均具备），就能完美复现助教能力。

---

**"咱们一步步捋，数学其实超容易懂～"** 💡
