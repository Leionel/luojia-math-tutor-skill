const ALLOWED_TAGS = new Set([
  "article",
  "aside",
  "div",
  "details",
  "footer",
  "header",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "li",
  "main",
  "nav",
  "ol",
  "p",
  "section",
  "span",
  "summary",
  "table",
  "tbody",
  "td",
  "th",
  "thead",
  "tr",
  "ul",
]);

const TABLE_CELL_ATTRS = new Set(["colspan", "rowspan"]);

function sanitizeAttributes(tagName: string, rawAttributes: string): string {
  if (tagName !== "td" && tagName !== "th") {
    return "";
  }

  const attrs: string[] = [];
  rawAttributes.replace(/\s+([a-zA-Z:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/g, (_match, name, dq, sq, bare) => {
    const attrName = String(name).toLowerCase();
    const attrValue = String(dq ?? sq ?? bare ?? "");
    if (TABLE_CELL_ATTRS.has(attrName) && /^\d{1,2}$/.test(attrValue)) {
      attrs.push(` ${attrName}="${attrValue}"`);
    }
    return "";
  });
  return attrs.join("");
}

export function sanitizeHtmlBlock(input: string): string {
  return input
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<\/?([a-zA-Z][a-zA-Z0-9-]*)([^>]*)>/g, (match, rawName, rawAttributes) => {
      const tagName = String(rawName).toLowerCase();
      if (!ALLOWED_TAGS.has(tagName)) {
        return "";
      }
      if (match.startsWith("</")) {
        return `</${tagName}>`;
      }
      const attrs = sanitizeAttributes(tagName, String(rawAttributes || ""));
      return `<${tagName}${attrs}>`;
    });
}
