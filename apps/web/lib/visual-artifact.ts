export const ARTIFACT_CSP = "default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const TAGS = new Set("div span p h1 h2 h3 h4 h5 h6 section article header footer main aside ul ol li table thead tbody tr td th details summary b strong i em small br hr pre code style svg g path circle ellipse rect line polyline polygon text tspan defs marker title desc lineargradient radialgradient stop clippath".split(" "));
export function buildStaticArtifact(source: string, dark: boolean): string {
  if (source.length > 60000) throw new Error("预览超过 60 KB，请简化图示。");
  const template = document.createElement("template");
  template.innerHTML = source; // Template contents stay inert while filtering.
  const nodes = [...template.content.querySelectorAll("*")];
  if (nodes.length > 1500) throw new Error("预览节点过多，请简化图示。");
  for (const node of nodes) {
    if (!TAGS.has(node.tagName.toLowerCase())) { node.remove(); continue; }
    for (const attr of [...node.attributes]) {
      if (/^on/i.test(attr.name) || /^(href|xlink:href|src|srcset|action|formaction|nonce|http-equiv|autofocus|tabindex)$/i.test(attr.name)) node.removeAttribute(attr.name);
    }
  }
  return `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${ARTIFACT_CSP}"><meta name="viewport" content="width=device-width,initial-scale=1"><style>:root{color-scheme:${dark ? "dark" : "light"}}body{margin:12px;background:${dark ? "#1e1e1b" : "#faf7f2"};color:${dark ? "#e5e2d8" : "#292b24"};font:14px/1.6 system-ui;overflow-wrap:anywhere}svg{max-width:100%;height:auto}*{box-sizing:border-box;animation:none!important;transition:none!important}</style></head><body>${template.innerHTML}</body></html>`;
}

export function staticSvgHeight(source: string, width: number): number | null {
  if (!/^\s*<svg\b/i.test(source)) return null;
  const box = source.match(/^\s*<svg\b[^>]*\bviewBox=["']([^"']+)["']/i)?.[1].trim().split(/[\s,]+/).map(Number);
  if (!box || box.length !== 4 || !box.every(Number.isFinite) || box[2] <= 0 || box[3] <= 0) return null;
  return Math.max(180, Math.min(800, Math.ceil((width - 24) * box[3] / box[2] + 24)));
}
