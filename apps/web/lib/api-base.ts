export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
export function resolveAnswerImage(source: string, base = API_BASE): string | null {
  try {
    const url = new URL(source.startsWith("/api/") ? `${base.replace(/\/$/, "")}${source}` : source);
    return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}
