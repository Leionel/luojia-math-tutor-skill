# 回答框可视化与 HTML 嵌入审查

日期：2026-10-01。范围：代码生成的 SVG 图标、函数图表、HTML 预览与回答框。下述问题保留审查时的代码状态；用户随后授权修复，实施回执见文末。网络搜索修复另批已提交。

## 当前链路

模型正文 → SSE 内容追加 → `MathMessage` → `LatexRenderer` → `parseBlocks`。

| 输出格式 | 当前行为 |
| --- | --- |
| `<plot function="x^2" domain="-1,1" />` 独立块 | `MathPlot` 受控表达式采样 → 应用生成 SVG |
| 裸 `<div>`、`<svg>` | `sanitizeHtmlBlock` 严格白名单 → 主页面插入 HTML |
| `html` / `xml` fenced code | 默认 iframe 预览，原内容进入 `srcDoc`，允许脚本 |
| `svg` fenced code | 源码展示，不预览 |
| Markdown 图片 | 普通 `<img>`，外部地址直接使用；`/api` 地址写死 localhost:8000 |

这不是完整的图形生成工具协议：后台没有通用绘图库或 HTML 执行器，只有前端的几条格式分支。后台提示词只声明 math/SymPy，未告诉模型可声明函数图或静态可视化。

## 逐文件问题

### `apps/web/components/latex-renderer.tsx`

1. **P1：生成的 HTML 默认执行脚本，缺少网络与资源限制。** 第15行默认preview，第47–48行使用 `sandbox="allow-scripts"` + 原始srcDoc。iframe没有内容CSP，也没有执行停止、资源预算或错误反馈。生成代码能运行脚本、请求外部资源，坏代码可能使预览卡顿。需要静态HTML/SVG默认禁止脚本；确需交互时由受控组件处理，或单独设计有限能力的运行环境。

   安全边界必须准确：没有 `allow-same-origin`，因此不能直接据此宣称代码可读主站Cookie/LocalStorage或访问父页面；已存在同源隔离。sandbox不是网络阻断策略。脚本权限及同源边界见 [MDN iframe](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe)；网络连接限制见 [MDN connect-src](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/connect-src)。本审查没有运行外传、死循环或沙箱逃逸样例。

2. **P1：流式 HTML 尚未完整就能预览。** 第48行srcDoc直接依赖content；解析器没有closed字段，缺结束围栏也会返回code-block。流式正文更新可重复初始化iframe和脚本；同一HTML在思考展开区/笔记区也使用相同renderer。建议闭合围栏且本轮生成结束后才形成稳定artifact，流式阶段只显示“生成中”或源码。

3. **P2：HTML预览没有高度适配、主题协同或错误回执。** 第46行固定最小300px白底iframe，没有加载/脚本错误/尺寸协议，长内容内外双滚动，短SVG留下大空白，深色页面仍白底。第22行把XML也当HTML，`svg`语言却不预览。统一明确的artifact类型，静态与交互走各自一致的路径；不要依赖围栏语言猜测执行能力。

4. **P2：生成图片的API地址写死本机。** 第160行将 `/api...` 改为 `http://127.0.0.1:8000...`。手机或部署环境的127.0.0.1是浏览器所在设备，不能加载服务器图片；应沿用统一API基址/受控资产地址。外部图片也缺少与artifact对应的来源和加载失败状态。

### `apps/web/lib/html-sanitize.ts`

5. **P2：SVG分支识别了但必然被删空，样式也全部移除。** 第1–28行白名单没有svg/path/circle等；第33–49行除表格colspan/rowspan外删除所有属性；第54行删除style。安全清洗是有效边界，但跟“生成图标/带样式图表”的能力不匹配。直接复现圆形SVG清洗结果为空字符串。不要为显示图形直接放宽主页面HTML权限，应采用受控SVG节点/属性协议或禁止脚本、禁止外联的静态预览。

### `apps/web/lib/message-parser.ts`

6. **P2：块边界不完整，会吞掉图形标记和后续正文。** 第161–170行不区分未闭合代码；第195–214行普通段落的停止条件缺plot/bilibili标记，“说明文字\n<plot .../>”整体变成paragraph，无法画图。第187–193行裸HTML读到空行为止，“<div>...</div>\n## 下一步”把标题吞进HTML块。建议使用明确artifact边界、闭合状态和独立解析规则，而非只靠空行。

### `apps/web/lib/math-expression.ts` 与 `apps/web/components/math-plot.tsx`

7. **P1：函数图跨越间断点连线，产生数学误导。** math-expression第225行删除奇异采样点；math-plot第34行将剩余点全部用L连接。`1/x`在0处丢点后，x≈-0.02、y≈-50与x≈0.02、y≈50被连成穿过原点的线，错误表现为有零点。现有测试只检查数值有限，没有检查连通段。应保留分段/缺失点信息，在间断处重新M起笔；对未采到的渐近线增加跳跃检测，并注明图像是数值采样、不能代替证明。

8. **P2：函数图固定宽度，手机内容区装不下。** math-plot第14、37、41行固定400px SVG，加32px容器padding及边框，比390px屏幕内实际聊天列更宽。应保留viewBox但使用响应式宽度，并检查坐标文字的可读性。第31–32行当0不在范围内时将“坐标轴”画到最小值边缘，也应明确为边界刻度而非原点轴。

### `luojia-math-tutor/SKILL.md` 与 `apps/api/app/tutor/prompt_policy.py`

9. **P1：能力协议断裂。** SKILL第28行说没有绘图工具，prompt_policy第6行加载的参考规范也没有 `<plot>` / 静态SVG / HTML可视化协议。模型因此常用“环境未启用绘图工具”降级，而前端本来能声明式绘图。需要区分“后台执行绘图程序”和“前端渲染声明式图形”，明确允许类型、输入条件、返回格式和失败说明；不能只把“不能画图”改成泛泛“可以画图”。

## 证据与限制

已读取生产提示词、解析器、渲染组件、清洗器和表达式解析器，并直接调用生产辅助函数复现SVG被清空、未闭合HTML可解析、plot被段落吞掉、HTML吞标题及间断点被省略。可复核输出：`results/answer-embed-audit-repro.json`。间断点连线及移动端宽度由生产路径代码确定；本轮没有修改UI制造演示，也未以恶意样例做真实浏览器攻击测试。

已有正确边界应保留：表达式使用受控Parser，不使用eval/Function；长度上限200；点数默认100；裸HTML保留极小标签/属性白名单；iframe未开放同源权限。此次不能称为“完全没有安全措施”。

## 建议实施顺序

1. 修默认脚本执行和流式预览：静态输出禁止脚本及外联，完成后才渲染；交互以应用预置组件优先。
2. 定义一个可版本化的可视化artifact协议：函数图、静态SVG、静态HTML、受控交互；分清示意图、采样图与数值验证。正文/思考摘要/笔记不要各自猜执行方式。
3. 接通提示词能力与renderer协议，修块解析、移动端宽度、尺寸和失败反馈、API资产基址。
4. 修间断点与轴标语义，加入图形语义验收，再考虑扩展图表类型或任意HTML交互。

以上为初次审查时的状态；实施记录如下。M2诊断闭环应优先使用受控函数图和明确数值证据；任意生成JS不作为诊断Oracle。

## 实施回执（2026-10-01）

| 原编号 | 实施结果 |
| --- | --- |
| 1 | 静态 HTML/SVG 需主动打开；空 sandbox、CSP 禁止脚本/外联/嵌套浏览/表单；惰性 template 中白名单清洗，删除事件/链接/foreignObject，限制 60 KB/1500 节点。保留原主页面严格 sanitizer，不扩大主站执行权限。 |
| 2 | 围栏及裸 HTML 标记 closed；本轮正文生成结束后才可挂载 iframe。思考过程仅源码，已结束摘要可预览；笔记/历史统一 renderer。旧消息不因新消息生成而卸载预览。 |
| 3 | visual-v1 静态类型统一；SVG viewBox 响应式高度 180–800px，HTML 手动有界调高；主题变化同步、失败提示/源码回退；XML 仅源码。没有开放任意 JS 或承诺跨源自动测高。 |
| 4 | 图片复用 NEXT_PUBLIC_API_BASE_URL；过滤协议和 URL 凭据，失败状态与来源链接；外部图片需主动点击加载，禁止默认外联图片请求。 |
| 5 | 裸/围栏 SVG 进入独立静态沙箱；保留绘图节点和静态样式，不放宽宿主 sanitizer。 |
| 6 | 段落遇 plot/bilibili 标记停止；裸 HTML 按根标签闭合停止，保护后续标题；支持 0–3 空格围栏和未闭合状态。 |
| 7 | 保存曲线 segments；无效点断开，对采样间隔增加内部探测；曲线每段重新 M 起笔。极点、连续陡线和极大范围有回归。间断探测仍是启发式，无法证明所有函数的连续性。 |
| 8 | 函数图 SVG 响应式 viewBox；0 不在范围时不画伪原点轴；390px 检查没有横向溢出。 |
| 9 | teaching-v2.2 加载 visual-artifacts.md，明确 visual-v1 语法、函数范围、静态限制与采样/验证边界；生产提示词加载回归通过。 |

验证：离线 npm test（知识 JSON、API346、Web26）通过；生产 build/typecheck 通过；lint 0 errors/10 existing warnings。日志 results/embed-repair-{full-test,build,lint}.log。浏览器独立临时页面调用真实 renderer，验证 SVG/HTML 白名单、空沙箱、CSP、生成中零 iframe、XML 源码、主题切换及 390px 无横向溢出；SVG180px/HTML320px，测试样例显示两段曲线。截图 results/embed-repair-{desktop,mobile}.png。临时路由已删除，没有写入真实会话，没有调用真实模型或运行恶意外传/死循环样例；未执行正式渗透或全平台安全验收。iframe onError 只作加载失败兜底，不声称可完整获知跨源内容错误。

服务已恢复 localhost:3000/chat 与 API8000；用户授权分批提交并 push。M2 过程诊断仍按原时间线推进，图示不替代受控数值 Oracle。
