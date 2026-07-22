import assert from "node:assert/strict";
import test from "node:test";

import { sanitizeHtmlBlock } from "./html-sanitize.ts";

test("removes scripts, event handlers, and unsupported tags", () => {
  const html = `<div onclick="alert(1)">ok<img src=x onerror="alert(1)"><script>alert(1)</script></div>`;

  const sanitized = sanitizeHtmlBlock(html);

  assert.equal(sanitized, "<div>ok</div>");
});

test("preserves basic table structure and safe span attributes", () => {
  const html = `<table><tr><td colspan="2" style="color:red">A</td></tr></table>`;

  const sanitized = sanitizeHtmlBlock(html);

  assert.equal(sanitized, `<table><tr><td colspan="2">A</td></tr></table>`);
});
