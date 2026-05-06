# 珞珈数智助教 (Luojia Math Tutor) - Gemini CLI Skill

[![Main Repo](https://img.shields.io/badge/Main-Repository-blue)](https://github.com/Leionel/luojia-math-tutor)

**珞珈数智助教**是专为大学生（高等数学、线性代数、概率论与数理统计）及考研学生设计的数学 AI 助教技能包，适用于 [Gemini CLI](https://github.com/google/gemini-cli)。

## 🌟 核心功能

- **零计算幻觉**：内置 Python 执行引擎（SymPy/NumPy），所有数学推导与计算均由代码实时验证。
- **启发式引导**：遵循 Step-by-Step CoT 阻断机制，通过提问引导学生思考，而非直接给出完整答案。
- **动态可视化**：实时生成函数曲线、概率分布图及 3D 几何图形（Matplotlib/Seaborn），实现抽象概念的直观理解。
- **本地权威库**：融合了结构化 JSON 概念库与多本权威数学教材（PDF），确保解答的准确性与权威性。

## 🔗 相关项目
本项目是 **[珞珈数智助教主仓库](https://github.com/Leionel/luojia-math-tutor)** 的技能实现版本。

## 🚀 安装与使用

### 1. 安装
确保已安装 `gemini-cli`，然后下载本项目中的 `luojia-math-tutor.skill` 文件：

```bash
gemini skills install luojia-math-tutor.skill --scope user
```

### 2. 启用
在交互式会话中运行：
```bash
/skills reload
```

### 3. 触发
使用以下关键词即可唤醒助教：
> **高数、线代、概率论、解题、辅导、可视化、讲题**

## 📂 目录结构

- `luojia-math-tutor/`：技能核心逻辑与说明文档。
  - `SKILL.md`：技能元数据与主控流程。
  - `references/`：教学规范、计算准则及本地知识库指南。
    - `output/`：结构化 JSON 数学概念题库。
    - `textbook/`：权威数学教材 PDF 库。
- `luojia-math-tutor.skill`：打包好的技能分发包。

## 📄 许可证
本项目遵循 MIT 协议。
