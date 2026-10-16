import { ChatLifetime, type ChatLease } from "./chat-lifetime.ts";
import type { createSession, listMessages, streamTutor } from "./api";

type Port = {
  create: typeof createSession;
  history: typeof listMessages;
  stream: typeof streamTutor;
};
/** Session/owner changes cancel delivery; selecting a workspace does not. */
export class TutorConversationController extends ChatLifetime {
  private session?: string;
  private readonly port: Port;
  constructor(port: Port) {
    super();
    this.port = port;
  }
  adoptSession(id?: string) {
    this.session = id;
  }
  get sessionId() {
    return this.session;
  }
  async ensureSession(
    lease: ChatLease,
    owner: () => string,
    subject: Parameters<typeof createSession>[0],
  ) {
    if (!this.current(lease, owner()) || lease.controller.signal.aborted)
      throw new DOMException("Conversation changed", "AbortError");
    if (!this.session) {
      const created = await this.port.create(subject, lease.controller.signal);
      if (!this.current(lease, owner()) || lease.controller.signal.aborted)
        throw new DOMException("Conversation changed", "AbortError");
      this.session = created.session_id;
    }
    return this.session;
  }
  async history(id: string, signal?: AbortSignal) {
    return this.port.history(id, signal);
  }
  async stream(lease: ChatLease, ...args: Parameters<typeof streamTutor>) {
    if (!this.current(lease, lease.owner) || lease.controller.signal.aborted)
      throw new DOMException("Conversation changed", "AbortError");
    return this.port.stream(
      { ...args[0], abortSignal: lease.controller.signal },
      ...(args.slice(1) as Tail<Parameters<typeof streamTutor>>),
    );
  }
}
type Tail<T extends unknown[]> = T extends [unknown, ...infer Rest]
  ? Rest
  : never;
