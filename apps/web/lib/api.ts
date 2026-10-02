import { readTutorEvents } from "./tutor-stream";
import { getAuthHeaders, getCurrentUserId } from "./demo-auth";

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

export type WebSearchMode = "auto" | "on" | "off";
export type WebSearchReport = {
  status: "disabled" | "success" | "empty" | "error" | "timeout";
  reason?: string;
  result_count: number;
  sources: Array<{ id: string; title: string; url: string; provider: string }>;
};

export type TutorMeta = {
  teaching_mode?: TutorMode;
  root_diagnosis?: RootDiagnosis;
  error?: {code: string; message: string};
  web_search?: WebSearchReport;
  awaiting_confirmation?: boolean;
  vision_draft?: string;
  verification_kind?: "symbolic" | "llm_review" | "root_oracle" | "none";
  intent: string;
  subject: string;
  concepts: string[];
  concept_items?: ConceptTraceItem[];
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

export type ConceptPrerequisite = {
  id: string;
  label: string;
};

export type ConceptTraceItem = {
  id: string;
  label: string;
  subject?: string;
  chapter?: string;
  section?: string;
  path?: string[];
  description?: string;
  role: "primary" | "related";
  assessed: boolean;
  source?: "mistake" | "explicit" | "retrieval" | "conversation" | "rule";
  evidence?: string;
  prerequisites?: ConceptPrerequisite[];
};

export type KnowledgeCatalogItem = {
  id: string;
  subject: string;
  type: string;
  type_label: string;
  title: string;
  chapter: string;
  section: string;
  description: string;
  prerequisites: string[];
  difficulty: number;
};

export type MasteryItem = {
  concept: string;
  score: number;
  attempts_count: number;
  correct_count: number;
  updated_at: string;
};

import { API_BASE } from "./api-base";

function headers(json = false, userApiKey?: string | null): Record<string, string> {
  return {
    ...getAuthHeaders(),
    ...(json ? { "Content-Type": "application/json" } : {}),
    ...(userApiKey ? { "X-Luojia-LLM-Key": userApiKey } : {}),
  };
}

function activeUserId(_requested?: string): string {
  return getCurrentUserId();
}

export async function createSession(subject: Subject = "foundations") {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify({ user_id: activeUserId(), subject })
  });
  if (!res.ok) throw new Error("创建会话失败");
  return res.json() as Promise<{ session_id: string; title: string; subject: string }>;
}

export async function listSessions(userId: string = "demo-user", q?: string): Promise<Session[]> {
  userId = activeUserId(userId);
  const query = new URLSearchParams({ user_id: userId });
  if (q) query.append("q", q);
  const res = await fetch(`${API_BASE}/api/sessions?${query.toString()}`, { cache: "no-store", headers: headers() });
  if (!res.ok) throw new Error("获取会话失败");
  const data = await res.json();
  return data.items as Session[];
}

export async function fetchKnowledgeCatalog(): Promise<{
  items: KnowledgeCatalogItem[];
  facets: {
    subjects: Record<string, number>;
    types: Record<string, number>;
  };
  total: number;
}> {
  const res = await fetch(`${API_BASE}/api/knowledge/catalog`, {
    cache: "no-store",
    headers: headers(),
  });
  if (!res.ok) throw new Error("知识目录加载失败");
  return res.json();
}

export async function deleteSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: "DELETE", headers: headers() });
  if (!res.ok) throw new Error("删除会话失败");
  return res.json();
}

export async function generateTitle(message: string, userApiKey?: string | null, model?: string | null): Promise<{ title: string; label: string }> {
  const res = await fetch(`${API_BASE}/api/tutor/generate_title`, {
    method: "POST",
    headers: headers(true, userApiKey),
    body: JSON.stringify({ message, model: model || null })
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
    headers: headers(true),
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("重命名失败");
  return res.json();
}

export async function truncateSession(sessionId: string, messageId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages/after/${messageId}`, { method: "DELETE", headers: headers() });
  if (!res.ok) throw new Error("截断会话记录失败");
  return res.json();
}

export async function listMessages(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, { cache: "no-store", headers: headers() });
  if (!res.ok) throw new Error("获取消息失败");
  const data = await res.json();
  return data.items as Message[];
}


export async function listMistakes(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/mistakes`, { cache: "no-store", headers: headers() });
  if (!res.ok) throw new Error("获取错因失败");
  const data = await res.json();
  return data.items as Array<{ id?: string; mistake_code: string; concept: string; subject: string; created_at: string }>;
}

export async function listUserMistakes(userId: string) {
  userId = activeUserId(userId);
  const res = await fetch(`${API_BASE}/api/users/${userId}/mistakes`, { cache: "no-store", headers: headers() });
  if (!res.ok) throw new Error("获取全局错因失败");
  const data = await res.json();
  return data.items as Array<{ mistake_code: string; concept: string; subject: string; created_at: string }>;
}

export type MistakeCreate = { subject: string; concept?: string; mistake_code: string; session_id?: string; };
export async function addMistake(userId: string, data: MistakeCreate) {
  userId = activeUserId(userId);
  const res = await fetch(`${API_BASE}/api/users/${userId}/mistakes`, {
    method: "POST", headers: headers(true), body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("添加错因失败");
  return res.json();
}

export async function generateQuiz(userId: string, mistakeId: string) {
  userId = activeUserId(userId);
  const res = await fetch(`${API_BASE}/api/users/${userId}/mistakes/${mistakeId}/generate-quiz`, {
    method: "POST", headers: headers()
  });
  if (!res.ok) throw new Error("生成练习题失败");
  return res.json() as Promise<{ status: string; quiz_content: string; concept: string }>;
}

export async function fetchMastery(userId: string): Promise<MasteryItem[]> {
  userId = activeUserId(userId);
  const res = await fetch(`${API_BASE}/api/users/${userId}/mastery`, { cache: "no-store", headers: headers() });
  if (!res.ok) throw new Error("获取掌握度失败");
  const data = await res.json();
  return (Array.isArray(data) ? data : data.items) as MasteryItem[];
}

export async function testModel(userApiKey: string | null, model?: string) {
  const res = await fetch(`${API_BASE}/api/models/test`, {
    method: "POST",
    headers: headers(true, userApiKey),
    body: JSON.stringify({ model: model || null })
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => null);
    const detail = errorBody?.detail || errorBody?.message;
    throw new Error(detail ? `模型测试失败：${detail}` : `模型测试失败 (HTTP ${res.status})`);
  }
  return res.json() as Promise<{ ok: boolean; message: string }>;
}

export async function streamTutor(
  payload: {
    root_submission?: RootSubmission;
    session_id: string;
    message: string;
    subject: Subject;
    mode: TutorMode;
    user_api_key?: string | null;
    model?: string;
    requested_hint?: boolean;
    abortSignal?: AbortSignal;
    image_urls?: string[];
    web_search?: boolean;
    web_search_mode?: WebSearchMode;
    reasoning_effort?: "off" | "low" | "medium" | "high" | "max";
  },
  onMeta: (meta: TutorMeta) => void,
  onToken: (token: string) => void,
  onThinkingChain?: (chain: string) => void,
  onOpening?: (content: string) => void,
  onThinkingEnd?: (data: { summary: string; elapsedMs: number }) => void,
  onVisionConfirmation?: (draft: string) => void
) {
  const { abortSignal, user_api_key: userApiKey, ...restPayload } = payload;
  const res = await fetch(`${API_BASE}/api/tutor/stream`, {
    method: "POST",
    headers: headers(true, userApiKey),
    body: JSON.stringify({ user_id: activeUserId(), ...restPayload }),
    signal: abortSignal,
  });
  if (!res.ok || !res.body) throw new Error("助教连接中断，请稍后重试");

  let thinkingChain = "";
  await readTutorEvents(res.body.getReader(), (event, data) => {
    if (event === "meta" || event === "meta_update") onMeta(data as TutorMeta);
    if (event === "opening") {
      if (onOpening) onOpening(String(data.content || ""));
      else onToken(String(data.content || ""));
    }
    if (event === "token" || event === "message") onToken(String(data.content || data.text || ""));
    if (event === "thinking") {
      thinkingChain += String(data.content || data.text || "");
      onThinkingChain?.(thinkingChain);
    }
    if (event === "vision_confirmation") {
      const parsed = (data.parsed || {}) as {latex?: unknown[]; problem_text?: string};
      const formulas = Array.isArray(parsed.latex) ? parsed.latex.map(item => `$$${String(item)}$$`).join("\n") : "";
      const draft = [String(parsed.problem_text || ""), formulas].filter(Boolean).join("\n\n");
      if (data.requires_confirmation === true && draft) onVisionConfirmation?.(draft);
    }
    if (event === "thinking_end") {
      onThinkingChain?.(thinkingChain);
      onThinkingEnd?.({summary: String(data.summary || ""), elapsedMs: Number(data.elapsed_ms || 0)});
    }
  });
}

export async function generateSimilarExercises(concept: string, difficulty: number = 2, count: number = 1) {
  const res = await fetch(`${API_BASE}/api/exercises/similar`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify({ user_id: activeUserId(), concept, difficulty, count })
  });
  if (!res.ok) throw new Error("获取类似题失败");
  const data = await res.json();
  return data.exercises as Array<{ text: string; answer: string; concept: string; difficulty: number }>;
}

export async function generateNote(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/tutor/notes`, {
    method: "POST",
    headers: headers(true),
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
  userId = activeUserId(userId);
  const res = await fetch(`${API_BASE}/api/users/${userId}/notes`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("保存笔记失败");
  return res.json();
}

export async function listNotes(userId: string) {
  userId = activeUserId(userId);
  const res = await fetch(`${API_BASE}/api/users/${userId}/notes`, { headers: headers() });
  if (!res.ok) throw new Error("获取笔记失败");
  const data = await res.json();
  return data.notes as NoteEntry[];
}

export async function deleteNote(noteId: string) {
  const res = await fetch(`${API_BASE}/api/notes/${noteId}`, { method: "DELETE", headers: headers() });
  if (!res.ok) throw new Error("删除笔记失败");
  return res.json();
}

export type UploadResult = {
  url: string;
  markdown: string;
  document_id: string | null;
  /** Present when MinerU parsing failed for a non-document upload. */
  parse_error?: string | null;
};

export async function uploadTextbook(file: File): Promise<UploadResult> {
  const res = await fetch(`${API_BASE}/api/uploads`, {
    method: "POST",
    headers: headers(),
    body: file,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || "上传失败");
  }
  return res.json();
}

export async function generateDocumentNote(
  userId: string,
  documentId: string,
  withMistakes: boolean = false
): Promise<{ status: string; note_id: string; note: string }> {
  userId = activeUserId(userId);
  const res = await fetch(`${API_BASE}/api/users/${userId}/notes/from-document`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify({ document_id: documentId, with_mistakes: withMistakes }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || "笔记生成失败");
  }
  return res.json();
}

export type DocumentEntry = {
  id: string;
  filename: string;
  created_at: string;
};

export async function listUploadedDocuments(): Promise<DocumentEntry[]> {
  const res = await fetch(`${API_BASE}/api/uploads/documents`, { headers: headers() });
  if (!res.ok) throw new Error("获取文档列表失败");
  const data = await res.json();
  return data.documents as DocumentEntry[];
}

export async function generateCandidatesFromDocument(
  courseId: string,
  documentId: string
): Promise<{ status: string; total: number }> {
  const res = await fetch(`${API_BASE}/api/courses/${courseId}/candidates/from-document`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify({ document_id: documentId }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || "候选生成失败");
  }
  return res.json();
}

export type ModelInfo = {
  id: string;
  name: string;
  provider: string;
};

export type ProviderInfo = {
  id: string;
  label: string;
  base_url: string;
};

export type ModelCatalogResponse = {
  default_model: string;
  allowed_models: string[];
  models: ModelInfo[];
  providers?: ProviderInfo[];
};

export async function fetchModels(): Promise<ModelCatalogResponse> {
  const res = await fetch(`${API_BASE}/api/models`, { cache: "no-store", headers: headers() });
  if (!res.ok) throw new Error("获取模型列表失败");
  return res.json();
}

export async function fetchCourseGraph(
  courseId: string = "numerical_analysis",
  scope?: string,
  studentId?: string
) {
  const params = new URLSearchParams({ format: "react_flow" });
  if (scope) params.set("scope", scope);
  if (studentId) params.set("student_id", studentId);

  const res = await fetch(`${API_BASE}/api/courses/${courseId}/graph?${params.toString()}`, {
    headers: headers(),
  });
  if (!res.ok) throw new Error("获取课程图谱失败");
  return res.json();
}

export async function matchCourseCase(
  courseId: string = "numerical_analysis",
  query: string,
  context?: Record<string, any>
) {
  const res = await fetch(`${API_BASE}/api/courses/${courseId}/cases/match`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify({ query, context }),
  });
  if (!res.ok) throw new Error("案例匹配失败");
  return res.json();
}

export type CourseCase = {
  case_id: string;
  title: string;
  task_type: string;
  learning_objectives: string[];
  concept_ids: string[];
  accepted_variants: string[];
  diagnostic_probes: Array<{ question: string; correct_answer?: string }>;
};

export async function listCourseCases(
  courseId: string = "numerical_analysis",
  conceptId?: string
): Promise<CourseCase[]> {
  const params = new URLSearchParams();
  if (conceptId) params.set("concept_id", conceptId);
  const res = await fetch(`${API_BASE}/api/courses/${courseId}/cases?${params.toString()}`, {
    headers: headers(),
  });
  if (!res.ok) throw new Error("获取教学案例失败");
  const data = await res.json();
  return data.cases as CourseCase[];
}

export type GlobalSearchResultItem = {
  id: string;
  category: "curriculum" | "mistakes" | "notes";
  category_label: string;
  title: string;
  subtitle: string;
  content: string;
  formula?: string | null;
  metadata?: Record<string, any>;
};

export type GlobalSearchResponse = {
  query: string;
  category: string;
  total: number;
  items: GlobalSearchResultItem[];
};

export async function searchGlobal(
  query: string,
  category: string = "all",
  limit: number = 20
): Promise<GlobalSearchResponse> {
  const params = new URLSearchParams({
    q: query,
    category,
    limit: String(limit),
  });
  const res = await fetch(`${API_BASE}/api/search/global?${params.toString()}`, {
    headers: headers(),
  });
  if (!res.ok) throw new Error("全局检索失败");
  return res.json() as Promise<GlobalSearchResponse>;
}


export type RootAttemptInput = {
  initial_value?: number | null;
  method: "newton" | "bisection" | "fixed_point";
  function: string;
  iterates?: Array<number | "NaN" | "Inf" | "-Inf">;
  brackets?: number[][];
  interval?: number[] | null;
  phi?: string | null;
  derivative?: string | null;
  update?: string | null;
  variant?: "standard" | "damped" | "modified";
  damping?: number;
  multiplicity?: number;
  goal?: "root_error" | "residual";
  tolerance?: number;
  stop_reason?: "none" | "step" | "bracket" | "residual" | "exact" | "iteration_limit";
};
export type RootSubmission = {attempt: RootAttemptInput; attempt_id: string; episode_id?: string};
export type RootDiagnosis = {
  status: "supported" | "contradicted" | "inconclusive" | "tool_error";
  family: string; summary: string; next_probe: string; error_step: number | null;
  complete: boolean; oracle_version: string; case_id: string | null; case_decision: string;
  episode_id: string; attempt_id: string; feedback_id: string; kind: "practice" | "probe";
  help_level: number; remaining_help: number; input: RootAttemptInput;
  delivery: string; outcome: string;
  trace: Array<{k: number; x_k: number; f_x: number; step_size: number | null; bracket?: number[]}>;
};
export async function acknowledgeRootFeedback(sessionId: string, report: RootDiagnosis) {
  const response = await fetch(`${API_BASE}/api/root-diagnostics/ack`, {method: "POST", headers: headers(true), body: JSON.stringify({session_id:sessionId,episode_id:report.episode_id,attempt_id:report.attempt_id,feedback_id:report.feedback_id})});
  if (!response.ok) throw new Error("显示回执未保存，结果尚未计入。");
  return response.json() as Promise<{status:string;outcome:string}>;
}
export async function startRootProbe(sessionId: string, episodeId: string) {
  const response = await fetch(`${API_BASE}/api/root-diagnostics/probe`, {method:"POST",headers:headers(true),body:JSON.stringify({session_id:sessionId,episode_id:episodeId})});
  if (!response.ok) throw new Error("请先完成练习并保存显示回执，再开始独立探针。");
  return response.json() as Promise<{episode_id:string;challenge:RootAttemptInput;instruction:string}>;
}
