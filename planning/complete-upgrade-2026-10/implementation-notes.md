# 完整升级实施记录

## U08 可撤销登录会话（临时库）

注册签发预检、用户/session原子写入、Bearer v2 sid/撤销/当前角色、幂等服务端退出、跨标签页/首页身份保护已实现。知识JSON/API899/Web70、增量11合同19实例、构建通过，lint0错误10既有警告；实际合成账号登录/双标签退出，临时库1登录1撤销账号保留。migration7增表，在临时库backup/恢复/integrity与失败回滚验证。正式库未读未升级；下一次Repository初始化会应用7，正式启动前必须实际备份/恢复验收。v1不得HTTP授权，重新登录；不是JWT/OIDC。细节 planning/complete-upgrade-2026-10/delivery-u08.md。用户授权额度内继续，本轮已额外交付U16/U08，剩余条件阶段仍pending。

## U16 静态降级

用户授权 U06 完成后有额度继续，已完成 U16。模型 HTML 的脚本默认禁止且无运行入口，旧消息原源码/静态图保留；删除30秒计时器与脚本重启，教学 prompt teaching-v2.8 与 UI一致。Web65、prompt1、构建通过，lint0错误10既有警告。实际临时库网页确认 srcdoc 无script/on事件/外链、sandbox空、关闭草稿保留、390px无溢出；危险死循环未执行。回执 planning/complete-upgrade-2026-10/delivery-u16.md。下一先 U08 临时库会话，正式库备份/恢复另验。

## U04–U06 接续交付

用户授权接续与分步提交。积分同页固定引用、代码静态规则/行号来源讨论、讲回原句跨度/逐条件未核验意见/前后版本已实现。知识JSON/API880/Web65、增量14合同33实例和受影响85项回归通过，构建/类型检查通过、lint 0错误10既有警告；真实网页用临时库和固定模型，讲回为自我映射，模型结构化路径离线验证。没有真实模型消费、经审gold、学习收益或代码执行。细节 planning/complete-upgrade-2026-10/delivery-u04-u06.md。下一优先U16静态降级；用户授权有五小时额度时继续，不自动满足外部gate。

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
