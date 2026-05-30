"use client";

import { useState } from "react";
import { LatexRenderer } from "./latex-renderer";

const DEFAULT_LATEX = `\\[
  f(x) = \\int_{-\\infty}^\\infty \\hat{f}(\\xi)\\,e^{2 \\pi i \\xi x} \\,d\\xi
\\]
这里是你的**体验舱**。你可以尝试修改公式，或者输入普通文本与 LaTeX 的混合内容。

求和公式示例：
$\\sum_{i=1}^{n} i^2 = \\frac{n(n+1)(2n+1)}{6}$
`;

export function LiveSandbox() {
  const [content, setContent] = useState(DEFAULT_LATEX);

  return (
    <div className="w-full max-w-4xl mx-auto mt-12 mb-8 bg-white/40 dark:bg-[#242421]/60 border border-[#d6d0ba] dark:border-[#3e3f36] rounded-xl overflow-hidden shadow-lg backdrop-blur-md flex flex-col md:flex-row">
      <div className="w-full md:w-1/2 p-0 border-b md:border-b-0 md:border-r border-[#d6d0ba]/50 dark:border-[#3e3f36]/50">
        <div className="bg-[#f2efe9] dark:bg-[#1e1e1b] px-4 py-2 text-xs font-title tracking-widest text-[#757a6b] dark:text-[#8d8a7d] border-b border-[#d6d0ba]/50 dark:border-[#3e3f36]/50">
          编辑区 (Input)
        </div>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full h-[250px] p-6 bg-transparent resize-none outline-none font-mono text-sm text-[#4a4d44] dark:text-[#c5c2b6] leading-relaxed"
          placeholder="在此输入 Markdown 或 LaTeX..."
          spellCheck={false}
        />
      </div>
      <div className="w-full md:w-1/2 p-0 bg-white/60 dark:bg-[#242421]/80">
        <div className="bg-[#f2efe9] dark:bg-[#1e1e1b] px-4 py-2 text-xs font-title tracking-widest text-[#757a6b] dark:text-[#8d8a7d] border-b border-[#d6d0ba]/50 dark:border-[#3e3f36]/50">
          渲染区 (Preview)
        </div>
        <div className="p-6 h-[250px] overflow-y-auto">
          <LatexRenderer content={content} />
        </div>
      </div>
    </div>
  );
}
