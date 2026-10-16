# 开发与文档维护

## 公开资料的分工

- [README](../README.md)：项目定位、学习入口、快速启动与证据摘要。
- [架构](architecture.md)和[学习设计](learning-design.md)：当前数据流、教学机制、源码和完成边界。
- [评测](evaluation.md)与 `evaluation/`：可复现协议、审核材料、反例和失败分析。
- [限制](limitations.md)与 [AGENTS.md](../AGENTS.md)：尚未验证的能力、安全约束与开发命令。

新增能力先更新实现和回归，再改公开说明。开发交接、阶段计划和交付记录保存在本地笔记与归档中。

## 2026-10-16 文档归档

在基线 `accd40d3401a9775bf8653c744af15bc003fc0c7` 上，已为 113 个文件保存工作副本和 HEAD 原文：92 个 `planning/` 文件、4 个历史 `docs/superpowers/` 文件、15 个根目录过程材料，以及合并前的 README 和 AGENTS。

本机归档位置：`.local/maintenance/2026-10-16-accd40d/`。

| 文件 | 用途 |
| --- | --- |
| `development-materials.zip` | `working/` 保存迁移前字节，`head/` 保存基线原文，内含 manifest |
| `archive-manifest.json` | 逐文件路径、操作、分类原因、两个版本的 SHA256 与归档摘要 |
| `protected-worktree.json`、`protected-changes.patch` | 本轮开始时 7 个未提交修改的校验值与补丁 |
| `document-inventory.json` | 文档清单、标题与迁移前大小和摘要 |

3 份项目日志和交接材料迁至忽略目录 `.local/notes/`。4 份包含其他未提交修改的过程文档仅从 Git 索引移出，原路径与字节保留。其余已归档过程材料从公开工作树移除。评测协议、开发题、内容审核材料和失败证据保留在 `evaluation/`。

旧 `diff.patch` 是包含乱码的历史补丁，没有运行或脚本依赖，已随原文归档。演示 HTML 与旧规划一并保留在归档。海报素材本轮未移动；其他未跟踪草稿和已有删除也未纳入本轮删除操作。

## 恢复方式

先读取 manifest 确认 SHA256，再将所需版本解压到新目录，避免覆盖当前文件：

```powershell
python -m zipfile -t .local/maintenance/2026-10-16-accd40d/development-materials.zip
python -m zipfile -e .local/maintenance/2026-10-16-accd40d/development-materials.zip .local/recovered-2026-10-16
```

从 `working/` 取回当时的本地内容，从 `head/` 取回基线版本。归档未上传；新克隆可通过 Git 历史查询已提交版本，例如：

```powershell
git show accd40d3401a9775bf8653c744af15bc003fc0c7:planning/README.md
```

Git 历史保留原提交。未提交的本地资料仅能从本机归档恢复。

## 验证文档

```powershell
python scripts/check_docs.py
```

检查范围为 README、AGENTS、公开 `docs/` 和评测入口中的相对文件链接及 Markdown 锚点；忽略代码块与外部 URL，不发网络请求。引用开发草稿时，应改为稳定的公开说明，避免让新克隆依赖本机笔记。
