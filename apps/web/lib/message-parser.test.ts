import assert from "node:assert/strict";
import test from "node:test";
import { parseBlocks, parseLatex, splitTableRow } from "./message-parser.ts";

test("same-line formulas never consume later prose or headings", () => {
  const blocks = parseBlocks(["$$u=X(x)Y(y)T(t)$$", "", "的乘积解。", "", '## 常数从哪来', "$$\\frac{T''}{c^2T}=\\frac{X''}{X}$$", "后文"]);
  assert.deepEqual(blocks.filter(b => b.type === "display-math").map(b => b.content), ["u=X(x)Y(y)T(t)", "\\frac{T''}{c^2T}=\\frac{X''}{X}"]);
  assert.ok(blocks.some(b => b.type === "h2" && b.content === "常数从哪来"));
  assert.ok(blocks.some(b => b.type === "paragraph" && b.lines.includes("后文")));
});

test("bracket and multiline math preserve following text", () => {
  assert.deepEqual(parseBlocks(["\\[x^2\\] 后文", "$$", "\\begin{aligned}", "x&=1\\\\", "y&=2", "\\end{aligned}", "$$"]), [
    {type:"display-math",content:"x^2"}, {type:"paragraph",lines:["后文"]},
    {type:"display-math",content:"\\begin{aligned}\nx&=1\\\\\ny&=2\n\\end{aligned}"},
  ]);
});

test("incomplete streaming delimiters retain prose and recover later formulas", () => {
  const blocks = parseBlocks(["$$x=1", "", "## 后续标题", "解释", "$$y=2$$"]);
  assert.ok(blocks.some(b => b.type === "h2"));
  assert.deepEqual(blocks.filter(b => b.type === "display-math"), [{type:"display-math",content:"y=2"}]);
  assert.deepEqual(parseBlocks(["$$x=1", "## 后续标题"])[0], {type:"paragraph",lines:["$$x=1"]});
});

test("inline code, escaped dollars and incomplete delimiters remain literal", () => {
  assert.deepEqual(parseLatex('`$x$` and \\$5 then $y$'), [{type:"text",content:'`$x$`'}, {type:"text",content:' and \\$5 then '}, {type:"inline-math",content:'y'}]);
  assert.deepEqual(parseLatex('$$x'), [{type:"text",content:'$$x'}]);
  assert.deepEqual(parseLatex('\\(x\\) and $$y$$'), [{type:"inline-math",content:'x'}, {type:"text",content:' and '}, {type:"display-math",content:'y'}]);
  assert.equal(parseBlocks(['```latex', '$$x$$', '```'])[0].type, 'code-block');
});

test("Markdown tables support math and escaped cell separators", () => {
  assert.deepEqual(splitTableRow('| $x$ | a\\|b |'), ['$x$', 'a|b']);
  assert.deepEqual(parseBlocks(['| 变量 | 意义 |', '| :--- | ---: |', '| $x$ | 坐标 |']), [{type:'table',headers:['变量','意义'],rows:[['$x$','坐标']]}]);
});
