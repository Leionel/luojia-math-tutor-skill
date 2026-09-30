// MinerU-extracted textbook LaTeX frequently carries unbalanced braces or
// unmatched \left/\right pairs; KaTeX renders those as error text. Repair the
// expression instead of failing the whole block.
export function balancedLatex(expr: string): string {
  let out = "";
  let depth = 0;
  let left = 0;
  let right = 0;

  for (let i = 0; i < expr.length; i++) {
    const ch = expr[i];
    if (ch === "\\" && i + 1 < expr.length) {
      if (expr.startsWith("\\left", i) && !expr.startsWith("\\left.", i)) left += 1;
      if (expr.startsWith("\\right", i) && !expr.startsWith("\\right.", i)) right += 1;
      out += expr.slice(i, i + 2);
      i += 1;
      continue;
    }
    if (ch === "{") {
      depth += 1;
    } else if (ch === "}") {
      if (depth === 0) continue;
      depth -= 1;
    }
    out += ch;
  }

  out += "}".repeat(depth);
  if (left > right) out += " \\right.".repeat(left - right);
  if (right > left) out = " \\left.".repeat(right - left) + out;
  return out;
}
