import test from "node:test";
import assert from "node:assert/strict";
import { resolveAnswerImage } from "./api-base.ts";
import { ARTIFACT_CSP, DYNAMIC_ARTIFACT_CSP, buildDynamicArtifact, staticSvgHeight } from "./visual-artifact.ts";
test("answer images use configured backend and reject active or credential URLs", () => {
  assert.equal(resolveAnswerImage("/api/assets/a.png", "https://tutor.example"), "https://tutor.example/api/assets/a.png");
  for (const url of ["javascript:alert(1)", "data:text/html,test", "https://user:pass@example.com/a"]) assert.equal(resolveAnswerImage(url), null);
});
test("static artifact policy denies execution, networking and embedded browsing", () => {
  for (const directive of ["script-src 'none'", "default-src 'none'", "connect-src 'none'", "frame-src 'none'", "form-action 'none'"]) assert.ok(ARTIFACT_CSP.includes(directive));
});

test("SVG viewBox sizing is bounded and HTML keeps manual sizing", () => {
  assert.equal(staticSvgHeight('<svg viewBox="0 0 320 100"></svg>', 344), 180);
  assert.equal(staticSvgHeight('<svg viewBox="0 0 10 99999"></svg>', 344), 800);
  assert.equal(staticSvgHeight('<svg viewBox="0 0 0 10"></svg>', 344), null);
  assert.equal(staticSvgHeight('<div>card</div>', 344), null);
});

test("untrusted dynamic execution fails closed before parsing or running scripts", () => {
  assert.equal(DYNAMIC_ARTIFACT_CSP,ARTIFACT_CSP);
  assert.throws(()=>buildDynamicArtifact('<script>while(true){}</script>',false,"test"),/静态预览/);
  assert.ok(DYNAMIC_ARTIFACT_CSP.includes("script-src 'none'"));
  for (const directive of ["default-src 'none'", "connect-src 'none'", "frame-src 'none'", "object-src 'none'"]) assert.ok(DYNAMIC_ARTIFACT_CSP.includes(directive));
  assert.ok(!DYNAMIC_ARTIFACT_CSP.includes("unsafe-eval"));
});
