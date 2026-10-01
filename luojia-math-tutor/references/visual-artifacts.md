# 回答内可视化协议 visual-v1

需要图示帮助理解时才生成，先给出文字说明、定义域与适用条件。

- 函数图：独占一行 `<plot function="x^2-1" domain="-2,2" />`。表达式仅支持变量 x、常数 pi/e、加减乘除乘方及 abs/cos/exp/log/sin/sqrt/tan。定义域是两个有限数且左端小于右端。禁止 Python、赋值、属性调用、任意代码。
- 静态结构图或图标：使用闭合的 svg 围栏，包含 viewBox、可读标签、title；不用外部字体、图片、事件处理器、foreignObject 或脚本。用 currentColor 或与纸张/墨色协调的颜色。
- 静态排版：使用闭合的 html 围栏，可包含内联 CSS 和上述静态 SVG。正文置于容器内；不使用链接、表单、iframe、外部资源或 JavaScript。xml 围栏只展示源码。
- 流式生成时仅显示源码；回答完成且代码块闭合后，用户可打开静态预览、复制源码并调整高度。预览禁用脚本和网络，无法执行按钮逻辑。需要交互时使用应用受控函数图，而非生成任意脚本。
- 函数图是数值采样，间断点检测有遗漏可能；不能据此宣称连续、收敛、有根或证明完成。没有工具结果时不声称已运行代码或验证结果。

例子：
```svg
<svg viewBox="0 0 320 100" xmlns="http://www.w3.org/2000/svg">
<title>求根诊断流程</title>
<rect x="10" y="20" width="100" height="50" fill="none" stroke="currentColor"/>
<text x="20" y="50" fill="currentColor">检查条件</text>
<path d="M110 45 L200 45" stroke="currentColor"/>
<text x="210" y="50" fill="currentColor">验证迭代</text>
</svg>
```
