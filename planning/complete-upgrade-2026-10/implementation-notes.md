# 完整升级实施记录

## U01–U03 实施决策

用户授权先实施三片并 commit。保留 root ref 具体类与旧动作 schema，新增固定 linear/reading union；只读任务走限定命令和独立服务，不经模型规划或生成标题。共有会话生命周期继续复用，没有新 Registry/Planner/数据库。

偏离与保守取舍：窄屏采用原生 dialog，具备焦点约束与 Escape；教材 offset 采用 Unicode codepoint，与 Python source_excerpt 一致。确认选段定位按 owner/hash/section/revision 在本地恢复，原文正文仍服务端读取。linear 没有历史 graph_revision，不补当前值伪装来源。source JSON 8KiB 超限整段拒绝，长轨迹最多首尾与所选附近11行，必要输入/条件完整保留。任务读取无今日计划时兼容以前未完成任务；三项上限及遗漏数量明确，独立待答隐藏数学内容，失效会话不重建。

teaching-v2.7 说明跨来源数据与帮助边界；质量报告脚本从 policy 的 AST 读取版本，不导入配置或使用旧硬编码。新增前端测试已接根命令与CI。

回执见 [delivery-u01-u03.md](delivery-u01-u03.md)：API847、Web最终64、E0增量13/28及原38/92、生产构建通过。真实模型/真人gold/全部浏览器故障矩阵没有验收；不将只读来源/任务升级说成恢复执行或独立学习效果。

## Decisions

2026-10-07：用户选择先写完整升级计划，并选择逐功能可验收切片/保留全部目标。本轮只做规划，不改业务代码、不发布外部任务或实施任何切片。

## Deviations

待实施后逐项记录“计划原意→实际代码/条件→采取的保守选择→影响与回执”。旧功能首版不重做；U01等只增当前缺口。

## Receipts

规划基线HEAD d9b9c849bf160a29f7d45efd330601b1083493b7；344个业务/测试/工具/评测文件的规划前hash保存于ignored results/complete-upgrade-plan-baseline.json。本轮不重新跑业务验收。实际源码验证、数据/真人/供应商条件见母计划。
