export type Segment =
  | { type: "text"; content: string }
  | { type: "inline-math"; content: string }
  | { type: "display-math"; content: string };

export function parseLatex(content: string): Segment[] {
  const segments: Segment[] = [];
  let remaining = content;

  while (remaining.length > 0) {
    const displayBlockRegex = /(?<!\\)\$\$([^\n]+?)\$\$|\\\[([^\n]+?)\\\]/;
    const inlineRegex = /\\\(([^\n]+?)\\\)|(?<![\\$])\$(?!\$)([^$\n]+?)(?<!\\)\$(?!\$)/;

    const codeMatch = remaining.match(/`+[^`\n]*`+/);
    const displayMatch = remaining.match(displayBlockRegex);
    const inlineMatch = remaining.match(inlineRegex);

    const displayIndex = displayMatch?.index ?? Infinity;
    const inlineIndex = inlineMatch?.index ?? Infinity;

    if (codeMatch && (codeMatch.index ?? Infinity) <= Math.min(displayIndex, inlineIndex)) {
      const end = codeMatch.index! + codeMatch[0].length;
      segments.push({ type: "text", content: remaining.slice(0, end) });
      remaining = remaining.slice(end);
      continue;
    }
    if (displayIndex === Infinity && inlineIndex === Infinity) {
      segments.push({ type: "text", content: remaining });
      remaining = "";
      continue;
    }

    if (displayIndex < inlineIndex) {
      const match = displayMatch!;
      const beforeText = remaining.slice(0, match.index);
      if (beforeText) {
        segments.push({ type: "text", content: beforeText });
      }

      const latex = match[1] ?? match[2] ?? "";
      segments.push({ type: "display-math", content: latex });
      remaining = remaining.slice(match.index! + match[0].length);
    } else {
      const match = inlineMatch!;
      const beforeText = remaining.slice(0, match.index);
      if (beforeText) {
        segments.push({ type: "text", content: beforeText });
      }

      const latex = match[1] ?? match[2] ?? "";
      segments.push({ type: "inline-math", content: latex });
      remaining = remaining.slice(match.index! + match[0].length);
    }
  }

  return segments;
}

export function splitTableRow(line: string): string[] {
  return line.trim().replace(/^\|/, "").replace(/(?<!\\)\|$/, "").split(/(?<!\\)\|/).map(cell => cell.trim().replace(/\\\|/g, "|"));
}

export type Block =
  | { type: "table"; headers: string[]; rows: string[][] }
  | { type: "h1"; content: string }
  | { type: "h2"; content: string }
  | { type: "h3"; content: string }
  | { type: "h4"; content: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "blockquote"; content: string }
  | { type: "hr" }
  | { type: "br" }
  | { type: "display-math"; content: string }
  | { type: "code-block"; language: string; content: string; closed: boolean }
  | { type: "plot"; function: string; domain?: string }
  | { type: "bilibili-search"; keyword: string }
  | { type: "html"; content: string; closed: boolean }
  | { type: "paragraph"; lines: string[] };

export function parseBlocks(lines: string[]): Block[] {
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.includes("|") && i + 1 < lines.length && splitTableRow(lines[i + 1]).every(cell => /^:?-{3,}:?$/.test(cell))) {
      const headers = splitTableRow(line);
      const rows: string[][] = [];
      i += 2;
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) rows.push(splitTableRow(lines[i++]));
      blocks.push({ type: "table", headers, rows });
    } else if (line.startsWith("#### ")) {
      blocks.push({ type: "h4", content: line.slice(5) });
      i++;
    } else if (line.startsWith("### ")) {
      blocks.push({ type: "h3", content: line.slice(4) });
      i++;
    } else if (line.startsWith("## ")) {
      blocks.push({ type: "h2", content: line.slice(3) });
      i++;
    } else if (line.startsWith("# ")) {
      blocks.push({ type: "h1", content: line.slice(2) });
      i++;
    } else if (line.startsWith("- ") || line.startsWith("* ")) {
      const items: string[] = [];
      while (i < lines.length && (lines[i].startsWith("- ") || lines[i].startsWith("* "))) {
        items.push(lines[i].slice(2));
        i++;
      }
      blocks.push({ type: "ul", items });
    } else if (/^\d+\.\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        const match = lines[i].match(/^(\d+)\.\s(.*)/);
        if (match) items.push(match[2]);
        i++;
      }
      blocks.push({ type: "ol", items });
    } else if (line.startsWith("> ")) {
      blocks.push({ type: "blockquote", content: line.slice(2) });
      i++;
    } else if (line.startsWith("---") || line.startsWith("***")) {
      blocks.push({ type: "hr" });
      i++;
    } else if (/^(\$\$|\\\[)/.test(line.trim())) {
      const trimmed = line.trim();
      const marker = trimmed.startsWith("$$") ? "$$" : "\\[";
      const endMarker = marker === "$$" ? "$$" : "\\]";
      const afterStart = trimmed.slice(marker.length);
      const sameLineEnd = afterStart.indexOf(endMarker);
      if (sameLineEnd >= 0) {
        blocks.push({ type: "display-math", content: afterStart.slice(0, sameLineEnd).trim() });
        const rest = afterStart.slice(sameLineEnd + endMarker.length).trim();
        if (rest) blocks.push({ type: "paragraph", lines: [rest] });
        i++;
      } else {
        const mathLines = [afterStart];
        let end = i + 1;
        let closed = false;
        // A missing delimiter must not consume the following Markdown/prose.
        while (end < lines.length && lines[end].trim() !== "" && !/^(#{1,6} |```|[-*] |> |\d+\. )/.test(lines[end].trim())) {
          const closing = lines[end].indexOf(endMarker);
          if (closing >= 0) {
            mathLines.push(lines[end].slice(0, closing));
            blocks.push({ type: "display-math", content: mathLines.join("\n").trim() });
            const rest = lines[end].slice(closing + endMarker.length).trim();
            if (rest) blocks.push({ type: "paragraph", lines: [rest] });
            i = end + 1;
            closed = true;
            break;
          }
          mathLines.push(lines[end++]);
        }
        if (!closed) {
          blocks.push({ type: "paragraph", lines: [line] });
          i++;
        }
      }
    } else if (/^ {0,3}```/.test(line)) {
      const language = line.trimStart().slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !/^ {0,3}```/.test(lines[i])) {
        codeLines.push(lines[i]);
        i++;
      }
      const closed = i < lines.length;
      if (closed) i++;
      blocks.push({ type: "code-block", language, content: codeLines.join("\n"), closed });
    } else if (line.trim() === "") {
      blocks.push({ type: "br" });
      i++;
    } else if (line.trim().startsWith("<plot ")) {
      const matchFn = line.match(/function="([^"]+)"/);
      const matchDomain = line.match(/domain="([^"]+)"/);
      if (matchFn) {
        blocks.push({ type: "plot", function: matchFn[1], domain: matchDomain?.[1] });
      }
      i++;
    } else if (line.trim().startsWith("<bilibili-search ")) {
      const matchKw = line.match(/keyword="([^"]+)"/);
      if (matchKw) {
        blocks.push({ type: "bilibili-search", keyword: matchKw[1] });
      }
      i++;
    } else if (/^<\/?(?:div|table|tbody|thead|tr|td|th|svg|ul|ol|li|h[1-6]|p|details|summary|section|article|nav|header|footer|main|aside|span)(?:>|\s)/i.test(line.trim())) {
      const htmlLines: string[] = [];
      const root = line.trim().match(/^<([a-z][a-z0-9]*)\b/i)?.[1];
      let depth = 0;
      let closed = false;
      while (i < lines.length) {
        if (htmlLines.length && /^(#{1,6} |```|<plot |<bilibili-search )/.test(lines[i].trim())) break;
        const current = lines[i++];
        htmlLines.push(current);
        if (root) {
          const tags = current.match(new RegExp(`<\\/?${root}\\b[^>]*>`, "gi")) || [];
          for (const tag of tags) depth += tag.startsWith("</") ? -1 : tag.endsWith("/>") ? 0 : 1;
          if (depth <= 0) { closed = true; break; }
        } else break;
      }
      blocks.push({ type: "html", content: htmlLines.join("\n"), closed });
    } else {
      const paragraphLines: string[] = [];
      while (
        i < lines.length &&
        !lines[i].startsWith("# ") &&
        !lines[i].startsWith("## ") &&
        !lines[i].startsWith("### ") &&
        !lines[i].startsWith("#### ") &&
        !lines[i].startsWith("- ") &&
        !lines[i].startsWith("* ") &&
        !/^\d+\.\s/.test(lines[i]) &&
        !lines[i].startsWith("> ") &&
        !lines[i].startsWith("---") &&
        !lines[i].startsWith("***") &&
        !/^\\\[/.test(lines[i].trim()) &&
        !/^\$\$/.test(lines[i].trim()) &&
        !/^ {0,3}```/.test(lines[i]) &&
        !/^<(?:plot|bilibili-search)\s/i.test(lines[i].trim()) &&
        !/^<\/?(?:div|table|tbody|thead|tr|td|th|svg|ul|ol|li|h[1-6]|p|details|summary|section|article|nav|header|footer|main|aside|span)(?:>|\s)/i.test(lines[i].trim()) &&
        lines[i].trim() !== ""
      ) {
        paragraphLines.push(lines[i]);
        i++;
      }
      if (paragraphLines.length > 0) {
        blocks.push({ type: "paragraph", lines: paragraphLines });
      }
    }
  }

  return blocks;
}
