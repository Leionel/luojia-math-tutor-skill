# B0：先核对现有求根实现，再接新功能

> 状态：待执行；预计2–3开发日，计入主规划B0/M2/M3工作包。本轮没有执行这些验收。

## 目标

把当前工作区已有代码与旧文档的“M2尚未实施”对齐，确认F1成绩归因、F3数值实验和F4独立测评可以复用哪些能力。先核对已有实现，不重新开发同名模块。

## 输入与边界

- 查看当前git diff与未跟踪文件；保留其他工作。关键文件：`apps/api/app/{math_tools/root_expression.py,math_tools/root_finding.py,tutor/root_diagnostics.py,api/routes_root_diagnostics.py}`、CourseStore/StudentOverlay、TutorWorkflow及前端求根卡。
- 阅读`apps/api/tests/test_root_oracle.py`，确认测试被实际收集；新测试文件存在不等于已跑过。
- 读取真实库前先确认配置和路径；回归/故障注入只使用临时数据库。涉及正式库迁移须单独执行backup与integrity_check。
- 固定求根小材料包：方法、错误家族、教师确认来源、合法路径、容差和Oracle版本。pending材料不进入正式教学。

## 必须完成的核对

| 项目 | 验收动作 | 通过条件 |
| --- | --- | --- |
| 数值与数学参考 | 对Newton公式错误、0↔1循环、近零导数、残差/误差区分、二分更新、不动点条件核对独立参考 | 不依赖同一实现自证；合法路径与不充分条件均覆盖 |
| 首个完整episode | 错误轨迹→诊断→真实反馈展示→ack→修订→重验→独立probe | 对每一步有对应证据；提示后成功不会记独立 |
| 幂等/故障 | 重复attempt/ack、相同ID不同内容、取消/断线、服务重启、事务失败 | 无重复完成或成绩；失败输入仍可恢复 |
| 权限与答案 | 学生A尝试访问B的session/episode；检查课程Case接口与probe反馈 | 资源隔离；受保护答案/测试键不通过其他API绕过测评策略 |
| 硬coded probe | 检查现有几个二次函数题的匹配/重复/帮助归因 | 如需独立题只称独立证据；扩任务前有教师gold，不称迁移已验证 |
| UI与流式交付 | 桌面/390px、JSON错误、帮助预算、unknown与inconclusive；断流后恢复 | 信息可理解、键盘可完成、没有生成成功但成绩未核对的假完成 |
| 测试注册 | 比较根`test:web:ui`与`.github/workflows/ci.yml`的前端测试清单 | 实施回归同时进入本地与CI；缺项列为待修，不顺手改无关流水线 |

旧文档中的Oracle“没有”与代码存在是状态漂移，不凭此判定实现正确。发现缺陷先归类数学/权限/交付/展示，再形成最小修复任务并记录实际范围。

## 执行命令与回执

```powershell
# 工作目录apps/api；保留conftest离线门控
python -m pytest tests/test_root_oracle.py -q
# 工作目录仓库根目录
npm.cmd test
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
# 停止Web dev后运行，并恢复服务
npm.cmd run build:web
```

解释器按当前已配置的项目环境选择。若本机gmpy2扩展出现既有兼容问题，只在测试进程使用已记录的`SYMPY_GROUND_TYPES=python`与`MPMATH_NOGMPY=1`，不修改应用默认配置，不删除离线门控。

回执保存：`results/learning-experience/b0/`；含git版本/差异范围、命令原输出、参考用例、10条端到端episode（至少3条合法/替代路径）、真实UI截图与未验证事项。更新根目录branch log、research refined和handoff。

## 退出门槛与恢复

B0通过后，F1可依据episode推进完成状态，F3可用Oracle诊断学生轨迹。F2在材料权限和版本确认后可以独立开展；没有B0也可做不写成绩的今日任务原型。

任一关键数学误诊、跨用户读取、答案绕过或事件重复成功未解决，则停止受影响的成绩/诊断入口，继续fixture与原文阅读。不要回滚其他工作区内容来获得绿色测试。应用失败时保留旧聊天功能与原始事件，按版本修复派生状态。
