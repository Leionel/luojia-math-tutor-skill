# Prompt 架构重塑：teaching-v2.1

日期：2026-09-30。范围：本轮 prompt 审查所列的主提示、参考指南、上下文构造、路由、证明辅导、验证文案、评审、复习提醒、来源与图片确认。工作区已有联网检索、运思强度和界面调整，本轮在其当前内容上增量修改，未回退这些改动。

## 运行架构

1. prompt_policy.load_teaching_prompt 将 SKILL.md 与三个 references/*.md 规范实际读入同一个系统提示。
2. resolve_teaching_policy 裁决答案披露与教学粒度。明确完整解答或 direct 模式优先；Case 默认建议不得添加相反约束。
3. prompt_builder 分离后台策略与 evidence_untrusted 资料，保留 student/history 的原始消息角色。后台控制用 developer，Chat Completions 适配器发送时映射 system，学生消息不升级权限。
4. Case 证据包含决策、置信度、推理要点、适用条件、边界及来源。未匹配案例也保留决策；NEW_CASE 与超纲分开。诊断探针跳过历史中已出现的原文问题，仅注入问题和目的，不注入答案键。
5. 证明提示经过 verifier 再进入 proof_tutor。LLM 审查与确定性检查分开；只对符号验证模式强制执行沙箱，不把任意证明强制转换成SymPy脚本。
6. math/SymPy 工具结果包含 execution_succeeded；失败、无输出和非零退出不满足执行门控。执行成功仍不等于命题为真。每轮最多两个工具请求，每次仅处理一个验证代码块。
7. 图片解析成功或失败均停止本轮，不进入检索、解题和掌握度更新。转写正文显示在聊天中，前端提供确认继续/编辑题目。确认请求携带文字而不重新带图片；草稿与待确认状态持久化到已有 learning_meta JSON，重新打开会话可恢复按钮。

## 按文件整改

| 文件 | 本轮整改 |
|---|---|
| luojia-math-tutor/SKILL.md | 统一完整答案例外；删掉“必须停顿”和最终数值禁令；说明真实工具范围；移除强制模板、宣传话术与虚构验证栏目；明确信息不足、证据和图片暂停规则。 |
| references/interactive-tutoring.md | 指导粒度由resolved_policy裁决；肯定须有证据；短题自然回答；完整解答不强制反问。 |
| references/math-tools-guidelines.md | 受限执行器与外部客户端分开；区分计算/证明/LLM意见；求根精度按容差与误差依据。 |
| references/knowledge-base-usage.md | 后台负责检索；模型不自行读文件；Case决策、条件、审核边界和引用规则明确。 |
| tutor/prompt_policy.py（新增） | 唯一教学策略裁决与规范加载入口，版本teaching-v2.1。 |
| tutor/prompt_builder.py | 去掉冲突的强制动作文本；结构化资料与策略；传入Case关键字段；探针不泄露答案、不重复原文；知识2400字符总预算，文档6000字符预算，历史12条/每条2000字符。 |
| tutor/hint_policy.py | 提示等级不再断言学生掌握/遗忘；完整请求允许全部过程与结论。 |
| tutor/graph.py | 图片真暂停；证明先审查；严格Verifier schema；工具失败降级；内部VERIFY代码无论出现位置均隐藏；公开进度不暴露Teacher/Examiner。 |
| tutor/proof_tutor.py | 复用规范与上游审查；明确四类判断；不重复注入无限长知识正文；移除未使用的ProofCheckResult。 |
| tutor/policy_router.py | 输入角色隔离；传最近历史；schema校验；action按intent规范化；多意图与否定规则。 |
| tutor/orchestrator.py | 公开文案区分正确/错误/未确定；LLM意见不叫确定性验证；增加verification_kind；图片草稿入历史、不评估掌握度。 |
| knowledge/evidence_builder.py、schema.py | 新增匹配决策和条件详情；提供可溯源课程条目引用；扩展字段保持旧位置参数顺序。 |
| tutor/fast_context.py | 保留无匹配Case的决策；融合课程与本地来源，避免引用丢失；保留已有联网检索整合。 |
| llm/openai_compatible.py | 传输适配developer→system，不改变用户角色；保留已有模型与运思强度映射。 |
| agents/code_executor.py | 非零退出且无stderr时也返回失败。 |
| agents/vision_agent.py | 图片及补充说明为转写数据，不服从其中指令，不猜不确定符号。 |
| agents/harness_evaluator.py | 尊重完整答案授权；数学正确、动作一致、披露与虚构验证分开评分；格式可验不当数学正确；严格schema，评审服务失败标unavailable。 |
| agents/cron_agent.py | 低掌握度估计不等于“经常做错”；复习邀请不施压、不编造经历。 |
| tutor/title_generator.py、api/routes_tutor.py | 标题输入为待概括数据；标题/标签校验长度、分隔和单行格式。 |
| search/web_search.py | 搜索摘要不称最新/已核验；WEB-ID与课程来源区分，明确禁止服从摘要内指令。 |
| web/lib/api.ts、tutor-chat.tsx、tutor-input.tsx | 上传图片真正传image_urls；处理确认事件，确认/编辑按钮；恢复待确认草稿，状态区分推理审查与本步检查。 |
| web/components/review-card.tsx | 不称LLM结论“推演严密”；掌握度显示为估计；删掉通用错题卡里硬编码的错误原因与导数正解，改用本轮真实摘要。 |

## 验证

- 新增 tests/test_prompt_restructure.py，20项离线回归：完整请求覆盖、公式提示、消息角色、Case条件与决策、探针不泄露与不重复、规范加载、预算、无效Verifier类型、错误审查文案、工具失败、图片暂停/失败/历史保存、路由历史、评审正确性、角色适配、内部代码隐藏。
- 更新旧证明路由和搜索来源断言；模拟模型接受现有运思参数。
- npm test：API294项、前端12项、知识JSON全通过；API2条现有Matplotlib布局警告。
- 前端tsc --noEmit --incremental false通过；lint退出0，现有Hook/img/font告警保留。
- 本机Anaconda gmpy2加载会产生Windows本地扩展错误；验收命令仅在测试进程设置SYMPY_GROUND_TYPES=python与MPMATH_NOGMPY=1，使用纯Python算术后端。不修改系统环境、不去除conftest离线门控。
- v2题集、课程种子和production matcher的SHA256保持原值：本轮没有通过修改gold或matcher制造分数提升。

## 证据限制与后续

以上是源代码、离线流程与接口契约证据。没有运行真实模型A/B、教师验收、浏览器真实图片上传或学习效果实验，不宣称数学正确率、prompt注入抵抗率或Case召回率提升。角色适配只是传输规则测试，尚未逐家调用线上模型接口。

原228题benchmark评价的是Case matcher，不是本次教学prompt。下一步应在固定题集上补真实教学响应评测，区分完整答案/引导/批改/信息不足/验证不可用，辅以教师审阅与数值Oracle。审核持久化/事务、生产召回、数值Oracle、聊天事件闭环仍按research§26路线推进。

系统提示在TutorWorkflow初始化时读取；已有运行进程须重启后才能载入新规范。本轮未提交、未推送、未部署，未修改正式DB、课程审核状态、原题集或production matcher。
