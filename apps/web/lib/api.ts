export type TutorMode = "socratic" | "direct" | "practice";
export type Subject = string;

export type Session = {
  id: string;
  user_id: string;
  title: string;
  subject: string;
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  created_at: string;
  thinking_summary?: string;
  thinking_elapsed_ms?: number;
  learning_meta?: TutorMeta | null;
};

export type TutorMeta = {
  intent: string;
  subject: string;
  concepts: string[];
  verified: boolean;
  is_correct: boolean | null;
  mistake: string | null;
  verifier_summary: string;
  hint_level?: number;
  mastery_score?: number;
  mastery_label?: string;
  mastery_delta?: number;
  pedagogical_action?: string;
  learning_objective?: string;
  route?: string;
};

export type MasteryItem = {
  concept: string;
  score: number;
  attempts_count: number;
  correct_count: number;
  updated_at: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export async function createSession(subject: Subject = "foundations") {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: "demo-user", subject })
  });
  if (!res.ok) throw new Error("创建会话失败");
  return res.json() as Promise<{ session_id: string; title: string; subject: string }>;
}

export async function listSessions(userId: string = "demo-user", q?: string): Promise<Session[]> {
  const query = new URLSearchParams({ user_id: userId });
  if (q) query.append("q", q);
  const res = await fetch(`${API_BASE}/api/sessions?${query.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error("获取会话失败");
  const data = await res.json();
  return data.items as Session[];
}

export async function deleteSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("删除会话失败");
  return res.json();
}

export async function generateTitle(message: string, userApiKey?: string | null, model?: string | null): Promise<{ title: string; label: string }> {
  const res = await fetch(`${API_BASE}/api/tutor/generate_title`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, user_api_key: userApiKey || null, model: model || null })
  });
  if (!res.ok) return { title: message.slice(0, 10) + "...", label: "综合" };
  const data = await res.json();
  return { title: data.title, label: data.label || "综合" };
}

export async function renameSession(sessionId: string, title: string, subject?: string) {
  const payload: any = { title };
  if (subject) payload.subject = subject;
  
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("重命名失败");
  return res.json();
}

export async function truncateSession(sessionId: string, messageId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages/after/${messageId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("截断会话记录失败");
  return res.json();
}

export async function listMessages(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, { cache: "no-store" });
  if (!res.ok) throw new Error("获取消息失败");
  const data = await res.json();
  return data.items as Message[];
}


export async function listMistakes(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/mistakes`, { cache: "no-store" });
  if (!res.ok) throw new Error("获取错因失败");
  const data = await res.json();
  return data.items as Array<{ mistake_code: string; concept: string; subject: string; created_at: string }>;
}

export async function listUserMistakes(userId: string) {
  const res = await fetch(`${API_BASE}/api/users/${userId}/mistakes`, { cache: "no-store" });
  if (!res.ok) throw new Error("获取全局错因失败");
  const data = await res.json();
  return data.items as Array<{ mistake_code: string; concept: string; subject: string; created_at: string }>;
}

export type MistakeCreate = { subject: string; concept?: string; mistake_code: string; session_id?: string; };
export async function addMistake(userId: string, data: MistakeCreate) {
  const res = await fetch(`${API_BASE}/api/users/${userId}/mistakes`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to add mistake");
  return res.json();
}

export async function generateQuiz(userId: string, mistakeId: string) {
  const res = await fetch(`${API_BASE}/api/users/${userId}/mistakes/${mistakeId}/generate-quiz`, {
    method: "POST"
  });
  if (!res.ok) throw new Error("生成练习题失败");
  return res.json() as Promise<{ status: string; quiz_content: string; concept: string }>;
}

export async function fetchMastery(userId: string): Promise<MasteryItem[]> {
  const res = await fetch(`${API_BASE}/api/users/${userId}/mastery`, { cache: "no-store" });
  if (!res.ok) throw new Error("获取掌握度失败");
  const data = await res.json();
  return (Array.isArray(data) ? data : data.items) as MasteryItem[];
}

export async function testModel(userApiKey: string | null, model?: string) {
  const res = await fetch(`${API_BASE}/api/models/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_api_key: userApiKey || null, model: model || null })
  });
  if (!res.ok) throw new Error("模型测试失败");
  return res.json() as Promise<{ ok: boolean; message: string }>;
}

export async function streamTutor(
  payload: {
    session_id: string;
    message: string;
    subject: Subject;
    mode: TutorMode;
    user_api_key?: string | null;
    model?: string;
    requested_hint?: boolean;
    abortSignal?: AbortSignal;
    image_urls?: string[];
  },
  onMeta: (meta: TutorMeta) => void,
  onToken: (token: string) => void,
  onThinkingChain?: (chain: string) => void,
  onOpening?: (content: string) => void,
  onThinkingEnd?: (data: { summary: string; elapsedMs: number }) => void
) {
  const { abortSignal, ...restPayload } = payload;
  const res = await fetch(`${API_BASE}/api/tutor/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: "demo-user", ...restPayload }),
    signal: abortSignal,
  });
  if (!res.ok || !res.body) throw new Error("Tutor 流式接口失败");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let thinkingChain = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const raw of events) {
      const eventLine = raw.split("\n").find((line) => line.startsWith("event: "));
      const dataLine = raw.split("\n").find((line) => line.startsWith("data: "));
      if (!eventLine || !dataLine) continue;
      const event = eventLine.replace("event: ", "");
      const data = JSON.parse(dataLine.replace("data: ", ""));
      if (event === "meta") onMeta(data as TutorMeta);
      if (event === "opening") {
        if (onOpening) onOpening(String(data.content || ""));
        else onToken(String(data.content || ""));
      }
      if (event === "token" || event === "message") {
        onToken(String(data.content || data.text || ""));
      }
      if (event === "thinking") {
        thinkingChain += String(data.content || data.text || "");
        if (onThinkingChain) onThinkingChain(thinkingChain);
      }
      if (event === "thinking_end") {
        if (onThinkingChain) onThinkingChain(thinkingChain);
        if (onThinkingEnd) onThinkingEnd({
          summary: data.summary || "",
          elapsedMs: data.elapsed_ms || 0
        });
      }
    }
  }
}

export async function generateSimilarExercises(concept: string, difficulty: number = 2, count: number = 1) {
  const res = await fetch(`${API_BASE}/api/exercises/similar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: "demo-user", concept, difficulty, count })
  });
  if (!res.ok) throw new Error("获取类似题失败");
  const data = await res.json();
  return data.exercises as Array<{ text: string; answer: string; concept: string; difficulty: number }>;
}

export async function generateNote(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/tutor/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId })
  });
  if (!res.ok) throw new Error("生成笔记失败");
  const data = await res.json();
  return data as { note: string };
}

export interface NoteEntry {
  id: string;
  user_id: string;
  session_id: string;
  subject: string;
  content: string;
  created_at: string;
}

export async function saveNote(userId: string, data: { session_id: string; subject: string; content: string }) {
  const res = await fetch(`${API_BASE}/api/users/${userId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("保存笔记失败");
  return res.json();
}

export async function listNotes(userId: string) {
  const res = await fetch(`${API_BASE}/api/users/${userId}/notes`);
  if (!res.ok) throw new Error("获取笔记失败");
  const data = await res.json();
  return data.notes as NoteEntry[];
}

export async function deleteNote(noteId: string) {
  const res = await fetch(`${API_BASE}/api/notes/${noteId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("删除笔记失败");
  return res.json();
}
