import test from "node:test";
import assert from "node:assert/strict";
import { readTutorEvents, TutorStreamError } from "./tutor-stream.ts";

function reader(chunks: string[]) {
  return new ReadableStream<Uint8Array>({start(controller) { chunks.forEach(chunk => controller.enqueue(new TextEncoder().encode(chunk))); controller.close(); }}).getReader();
}
test("stream supports fragmented CRLF, terminal done and partial output", async () => {
  const events: string[] = [];
  await readTutorEvents(reader(['event: token\r\ndata: {"content":"中"}\r', '\n\r\nevent: done\ndata: {}']), event => events.push(event));
  assert.deepEqual(events, ["token", "done"]);
});
test("upstream auth error is propagated instead of successful EOF", async () => {
  await assert.rejects(readTutorEvents(reader(['event: opening\ndata: {"content":"hello"}\n\nevent: error\ndata: {"code":"model_auth_failed","message":"鉴权失败"}\n\n']), () => {}), error => error instanceof TutorStreamError && error.code === "model_auth_failed");
});
test("truncated or idle streams cannot count as completed responses", async () => {
  await assert.rejects(readTutorEvents(reader(['event: token\ndata: {"content":"partial"}\n\n']), () => {}), /连接提前结束/);
  let cancelled = false;
  const pending = new ReadableStream<Uint8Array>({cancel() { cancelled = true; }}).getReader();
  await assert.rejects(readTutorEvents(pending, () => {}, 5), /等待超时/);
  assert.ok(cancelled);
});
