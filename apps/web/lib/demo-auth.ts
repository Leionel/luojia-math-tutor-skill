const DEMO_ACCESS_KEY = "luojia_demo_access";
const LEGACY_ACCESS_KEY = "mock_auth_token";
const AUTH_TOKEN_KEY = "luojia_auth_token";
const AUTH_USER_KEY = "luojia_auth_user";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export function hasDemoAccess(): boolean {
  if (typeof window === "undefined") return false;
  return (
    window.localStorage.getItem(DEMO_ACCESS_KEY) === "true" ||
    Boolean(window.localStorage.getItem(AUTH_TOKEN_KEY)) ||
    window.localStorage.getItem(LEGACY_ACCESS_KEY) === "true"
  );
}

export function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function getCurrentUserId(): string {
  if (typeof window === "undefined") return "demo-user";
  return window.localStorage.getItem(AUTH_USER_KEY) || "demo-user";
}

export async function authenticate(
  action: "login" | "register",
  userId: string,
  password: string,
  displayName?: string,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/auth/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId.trim(),
      password,
      display_name: displayName?.trim() || undefined,
    }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(String(payload.detail || "身份验证失败"));
  }
  const payload = await response.json();
  window.localStorage.setItem(AUTH_TOKEN_KEY, String(payload.access_token));
  window.localStorage.setItem(AUTH_USER_KEY, String(payload.user_id));
  window.localStorage.removeItem(DEMO_ACCESS_KEY);
  window.localStorage.removeItem(LEGACY_ACCESS_KEY);
}

export function grantDemoAccess(): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(DEMO_ACCESS_KEY, "true");
  window.localStorage.removeItem(LEGACY_ACCESS_KEY);
}
