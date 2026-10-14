import assert from "node:assert/strict";
import test from "node:test";
import { TutorConversationController } from "./tutor-conversation-controller.ts";

test("lazy session is created once, parent adoption preserves the active stream", async () => {
  let resolve!: (value: {
    session_id: string;
    title: string;
    subject: string;
  }) => void;
  let creations = 0;
  let signal: AbortSignal | undefined;
  const created = new Promise<{
    session_id: string;
    title: string;
    subject: string;
  }>((done) => {
    resolve = done;
  });
  const controller = new TutorConversationController({
    create: async () => {
      creations++;
      return created;
    },
    history: async () => [],
    stream: async (input) => {
      signal = input.abortSignal;
    },
  });
  const lease = controller.begin("alice")!;
  const pending = controller.ensureSession(lease, () => "alice", "数值分析");
  assert.equal(controller.begin("alice"), null);
  resolve({ session_id: "session-a", title: "session", subject: "数值分析" });
  assert.equal(await pending, "session-a");
  controller.adoptSession("session-a");
  assert.ok(controller.current(lease, "alice"));
  await controller.stream(
    lease,
    {
      session_id: "session-a",
      message: "claim",
      subject: "auto",
      mode: "socratic",
      user_api_key: null,
    },
    () => {},
    () => {},
  );
  assert.equal(signal, lease.controller.signal);
  assert.equal(signal?.aborted, false);
  controller.finish(lease);
  const next = controller.begin("alice")!;
  assert.equal(
    await controller.ensureSession(next, () => "alice", "数值分析"),
    "session-a",
  );
  assert.equal(creations, 1);
  controller.cancel();
  assert.equal(next.controller.signal.aborted, true);
});
test("late creation cannot attach to a changed owner or replace a switched session", async () => {
  let owner = "alice";
  let resolve!: (value: {
    session_id: string;
    title: string;
    subject: string;
  }) => void;
  const pending = new Promise<{
    session_id: string;
    title: string;
    subject: string;
  }>((done) => {
    resolve = done;
  });
  const controller = new TutorConversationController({
    create: () => pending,
    history: async () => [],
    stream: async () => {
      throw Error("must not send");
    },
  });
  const old = controller.begin(owner)!;
  const create = controller.ensureSession(old, () => owner, "数值分析");
  owner = "bob";
  controller.invalidate();
  controller.adoptSession("bob-session");
  resolve({ session_id: "alice-session", title: "old", subject: "数值分析" });
  await assert.rejects(create, { name: "AbortError" });
  assert.equal(controller.sessionId, "bob-session");
  await assert.rejects(
    controller.stream(
      old,
      {
        session_id: "alice-session",
        message: "stale",
        subject: "auto",
        mode: "socratic",
        user_api_key: null,
      },
      () => {},
      () => {},
    ),
    { name: "AbortError" },
  );
});
