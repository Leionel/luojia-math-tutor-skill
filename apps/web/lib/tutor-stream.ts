export class TutorStreamError extends Error {
  code: string;
  constructor(message: string, code = "stream_failed") { super(message); this.name = "TutorStreamError"; this.code = code; }
}

/** Require a terminal done event: socket EOF is not a completed answer. */
export async function readTutorEvents(reader: ReadableStreamDefaultReader<Uint8Array>, onEvent: (event: string, data: Record<string, unknown>) => void, idleMs = 90000) {
  let buffer = "";
  const decoder = new TextDecoder();
  function dispatch(raw: string): boolean {
    const lines = raw.split("\n");
    const event = lines.find(line => line.startsWith("event:"))?.slice(6).trim();
    const json = lines.filter(line => line.startsWith("data:")).map(line => line.slice(5).trimStart()).join("\n");
    if (!event || !json) return false;
    let data: Record<string, unknown>;
    try { data = JSON.parse(json); } catch { throw new TutorStreamError("响应格式异常，本轮未完成。", "invalid_event"); }
    if (!data || typeof data !== "object" || Array.isArray(data)) throw new TutorStreamError("响应格式异常，本轮未完成。", "invalid_event");
    if (event === "error") throw new TutorStreamError(typeof data.message === "string" ? data.message.slice(0, 500) : "本轮生成失败，请重试。", typeof data.code === "string" ? data.code : "generation_failed");
    onEvent(event, data);
    return event === "done";
  }
  try {
    while (true) {
      let timer: ReturnType<typeof setTimeout> | undefined;
      const timeout = new Promise<never>((_, reject) => { timer = setTimeout(() => reject(new TutorStreamError("响应等待超时，本轮未完成；请稍后重试。", "stream_timeout")), idleMs); });
      let chunk: ReadableStreamReadResult<Uint8Array>;
      try { chunk = await Promise.race([reader.read(), timeout]); }
      finally { clearTimeout(timer); }
      buffer += decoder.decode(chunk.value, { stream: !chunk.done });
      buffer = buffer.replace(/\r\n/g, "\n");
      let end: number;
      while ((end = buffer.indexOf("\n\n")) >= 0) {
        const raw = buffer.slice(0, end); buffer = buffer.slice(end + 2);
        if (dispatch(raw)) return;
      }
      if (chunk.done) {
        if (buffer.trim() && dispatch(buffer)) return;
        throw new TutorStreamError("连接提前结束，尚未收到完成回执；已生成内容仅为部分回答。", "incomplete_stream");
      }
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
