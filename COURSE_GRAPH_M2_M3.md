# M2/M3 求根过程闭环与动态预览（2026-10-02）

本轮交付 M2/M3 的工程候选版：学生提交受控公式和轨迹 → 数值核对 → 生产 Case 匹配 → 错误定位与提示 → 修改后重验 → 显示回执 → 过程事件和 Overlay。教师逐题复核、未见题评测与真实学习效果仍待完成，不能把工程通过写成 G3 教师门槛或 M4 完成。

## 如何使用

打开 `/chat`，点击输入框上方“求根过程验证”。选择 Newton、二分法或不动点迭代，填写函数、JSON 轨迹、目标和容差。`x^2-2`、`[1,3]` 会定位第 1 步；点击“修改轨迹再验证”，提交自己重新计算的轨迹及 `[1,2]` 有根区间。根误差目标需要可用误差界；只想检查残差时显式选择“只要求残差”。

也可提交结构化消息：

````text
```root-attempt
{"method":"newton","function":"x^2-2","iterates":[1,3],"interval":[1,2],"goal":"root_error","tolerance":0.000001}
```
````

自由文字/截图不会自动被当作已计算的轨迹；任意 Python、JS 代码都不进入 Oracle。修订保留 episode_id 与任务函数、方法、目标、容差；每次新尝试用新的 attempt_id，同一尝试重试保留 attempt_id。界面生成 UUID，服务端检验冲突。

## 数学范围与版本

- `root-oracle-v1` / `root-tolerance-v1`：AST 长度 200、节点 80、嵌套 20，整数幂 ±16，轨迹/区间最多 101 条。只允许算术、x/pi/e、sin/cos/tan/exp/log/sqrt/abs；更新公式另外允许 f、df。没有 eval、动态导入、文件或网络能力。
- 分析导数用于 Newton 更新与导数核对。阻尼 Newton 和已声明重数的改进 Newton 不被当成普通公式错误。相邻值比较使用 relative=1e-8 / absolute=1e-10；这是轨迹记录精度契约，与用户的最终容差分别报告。
- 二分检查区间顺序、连续性可确认范围、端点零点/变号、半区间更新及误差上界。跨 `1/x` 极点的变号不支持根存在。
- 不动点检查更新式、区间映射与导数界。g 的不动点误差不被冒充 f 的根误差。区间计算未确认压缩条件时请求补充条件，不直接宣布发散。
- 根误差采用二分区间上界，或有根区间与导数下界下的 residual/lower_bound。残差目标仅确认残差；迭代上限、未知条件、工具异常均不冒充成功。
- 浮点区间运算采用向外扩张与保守拒绝。它是受限数值证据，不是经过形式化验证的通用区间库；超越函数和极端数值需 M4 独立审计。Decimal 高精度 sqrt(2) 是交叉参考之一。

| 错误家族 | 检查重点 |
| --- | --- |
| newton_formula | 导数、更新表达式、相邻值 |
| newton_derivative_zero | 零/近零导数、0/0 |
| newton_cycle | 0↔1 等两点循环 |
| newton_stop_step | 小步长仍有大残差 |
| residual_without_error_bound | 小残差不能替代根误差 |
| bisection_bracket | 初区间、变号、连续性 |
| bisection_update | 保根半区间与近似值位置 |
| bisection_stop | 停机误差界 |
| fixed_point_update | 实际 g(x) 更新 |
| fixed_point_conditions | 映射/压缩条件不足 |
| numeric_nonfinite | NaN/Inf、定义域、溢出 |
| iteration_limit | 上限停机仍未知 |

`supported` 可表示已提交步骤符合规则但未完成任务，不能仅看状态判成功。`complete` 必须与 supported 一起成立。其余状态为 contradicted/inconclusive/tool_error，保留定位、证据、下一步和版本。

## Case 与学习证据

Oracle 先定位数学家族，再使用正式课程 Case 标题/方法锚点调用现有生产 matcher。练习返回实际匹配和决策；探针公开 Case 固定为一般 Newton 教学锚点，避免通过错误家族 Case ID 泄露提示。这一路径不代表自由提问检索的泛化成绩，228 题开发 benchmark 与 244 题 retrieval eval 保持不变。

CourseStore 新增 `root_episodes` 表，沿用 process_events/unit_states/case_states。每次提交、事件与 Overlay 在同一个 SQLite IMMEDIATE 事务内写入；失败回滚，重试不留半个事件。持久化仍要求配置 `COURSE_STORE_PATH`，本地已配置 `data/course_store.db`；空配置只用于内存演示。

事件链为 attempt/probe/revision → verifier_evidence → diagnosis → hint_exposed → outcome；取消在可观察时附加 delivery_failed。上下文记录 user/course/session/episode/task/attempt、graph revision/generation、Case、Oracle/Tolerance/prompt/model、输入摘要和证据引用。课程库与会话库是两个库，未声称聊天消息与课程事件跨库原子提交。

成功和失败计数都在实际反馈卡显示并取得服务端 ACK 后归约。终端 done 未到、卡片不可见、页面隐藏、断流或取消时结果仍 pending/unknown；重试同一尝试重放同一反馈票据，ACK 重复不加分。ACK 是客户端可见性回执，不能证明学生阅读或理解，但学生不能提交 is_success/is_independent 代替服务器验证。

提示预算每 episode 为 3；普通诊断使用一级，直接讲解使用三级；未 ACK 的已生成提示也预留预算，避免并发绕过。已得到提示后的成功修订记 assisted。首个没有帮助的普通练习成功仅记 observed。

独立探针由服务器从不同函数生成，避开该学生已提交的同一服务器探针函数，并锁定初值、方法、区间、目标、容差和标准更新参数；必须提交至少两步且从规定初值开始。探针不返回私有误差步、轨迹、数值参考或下一步答案；首个成功并 ACK 才记一次独立证据。再次提交因已见过验证反馈保守记 assisted，不累加独立证据。单次独立证据仅标记 probe_observed，不称掌握或迁移已验证。开发探针池为 x²-n（3≤n≤50，排除平方数），耗尽后停止发新题，不无限重发同题记独立证据；这不保证该学生在其他渠道未见题。

鉴权后 Overlay 与 graph overlay 不允许跨用户读取；root ACK/probe/replay 要求会话和 episode 都归当前 principal。旧的自报 outcome 接口仅教师/管理员可写。学生 Case API 不返回 probe 正确答案、动作脚本及非 direct 推理签名；候选/审核修订读接口只供教师角色。生产试用需启用 AUTH_REQUIRED；本地 demo 的兼容权限不等于生产隔离。

## 动态 HTML 恢复

`teaching-v2.3` 加载 `visual-v2`，兼容旧 static visual-v1。完整回答中的闭合 html 围栏支持本地 DOM、按钮、滑块、Canvas 和动画；默认展示源码，用户点击“运行动态预览”才挂载。

独立 srcdoc iframe 仅 `sandbox=allow-scripts`，没有 allow-same-origin/popups/forms/top-navigation；CSP 禁网络、CDN、嵌套 iframe、对象、表单和 eval。静态 SVG/裸 HTML 保留无脚本沙箱；宿主 sanitizer 不放宽。60KB/1500节点上限，预览尺寸 180–800px，错误/拒绝时源码回退，停止卸载 iframe、重启生成新的通信票据，30 秒定时卸载。高度/错误消息同时核对 iframe 来源与通道。

30 秒是浏览器宿主定时器，**不是可以强杀同步死循环的 CPU/内存隔离**。任意生成 JS 仍可消耗浏览器资源，本轮未运行死循环/外传攻击或做正式渗透验收；需要不可信代码的硬资源保障时另设 worker/进程隔离验收。动态图示绝不进入数值 Oracle 或学习成功评分。

## 验收与下一步

- `npm test`：知识 JSON、API 415、Web 30 项通过；`npm run build:web`、web typecheck 通过；lint 0 错误/10 条既有警告。CI 前端清单补齐 artifact/SSE 用例；远端 CI 状态另核对。
- 10 条固定生产 LangGraph/SSE episode，含阻尼、重根改进与端点根三条合法替代路径；另有工具失败生产流程、取消事务、用户/会话隔离、伪造回执、重复/重启/回滚/并发预算回归。
- `python evaluation/evaluate_root_diagnostics.py`：13/13 错误→修订→合法控制三元组，覆盖 12 家族。报告 `results/root_diagnostics_eval.json`；fixture 和源码哈希见 `evaluation/root_diagnostic_manifest.json`。这些都是开发 fixture，不是独立 gold。
- 浏览器使用实际组件验证膜振动 Canvas、暂停/频率/停止/重启/脚本异常/生成门控/30 秒退出和父页面 DOM 隔离。390px 无横向溢出；主聊天求根表单可用、控制台无错误。截图 `results/m2-m3-{dynamic-desktop,dynamic-mobile,chat-mobile}.png`；临时验收路由已删除，没有改真实会话消息或调用真实模型。
- 原“只留开场白”问题补上 SSE error、EOF 和闲置超时处理；鉴权/超时/网络错误安全持久化。模型凭证没有改动，动态模型生成质量没有通过真实模型验证。

下一轮进入 M4：教师逐题核对上述 12 家族与错误/合法变体；先独立审计区间/容差和披露政策，再形成未见函数/措辞/跨表示的冻结集。M5 学生试用与 M6 无 AI/延迟保持实验继续按长期计划，不以工程提前完成跳过教师与研究门槛。新增产品功能规划与本轮候选实现分别保留状态。
