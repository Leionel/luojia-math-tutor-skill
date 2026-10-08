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
  if(payload.auth_version!==2||payload.token_type!=="bearer"||typeof payload.access_token!=="string"||!payload.access_token||payload.user_id!==userId.trim())throw new Error("登录响应无法确认，请重试；原登录信息未改动。");
  window.localStorage.setItem(AUTH_TOKEN_KEY, String(payload.access_token));
  window.localStorage.setItem(AUTH_USER_KEY, String(payload.user_id));
  window.localStorage.removeItem(DEMO_ACCESS_KEY);
  window.localStorage.removeItem(LEGACY_ACCESS_KEY);
  window.dispatchEvent?.(new Event("luojia-auth-change"));
}

export function grantDemoAccess(): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(DEMO_ACCESS_KEY, "true");
  window.localStorage.removeItem(LEGACY_ACCESS_KEY);
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USER_KEY);
  window.dispatchEvent?.(new Event("luojia-auth-change"));
}

export function isAuthStorageKey(key:string|null):boolean{
  return key===null||[AUTH_TOKEN_KEY,AUTH_USER_KEY,DEMO_ACCESS_KEY,LEGACY_ACCESS_KEY].includes(key);
}

export async function signOutCurrentSession():Promise<"demo"|"server">{
  const headers=getAuthHeaders();
  if(!headers.Authorization){clearAuthSession();return "demo";}
  let response:Response;
  try{response=await fetch(`${API_BASE}/api/auth/logout`,{method:"POST",headers,signal:AbortSignal.timeout(15000)});}
  catch{throw new Error("连接失败，服务端撤销未确认。可以重试，或仅清除此设备登录。");}
  if(!response.ok)throw new Error("未能确认服务端会话已撤销。可以重试，或仅清除此设备登录。");
  const receipt=await response.json();
  if(receipt.revoked!==true||receipt.scope!=="current_session")throw new Error("退出结果无法确认，请重试。");
  if(getAuthHeaders().Authorization!==headers.Authorization)throw new Error("登录身份已变化，请刷新后继续。");
  clearAuthSession();return "server";
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") return;
  for (const key of [AUTH_TOKEN_KEY, AUTH_USER_KEY, DEMO_ACCESS_KEY, LEGACY_ACCESS_KEY]) {
    window.localStorage.removeItem(key);
  }
  window.dispatchEvent?.(new Event("luojia-auth-change"));
}
