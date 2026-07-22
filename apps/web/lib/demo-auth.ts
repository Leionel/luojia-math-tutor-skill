const DEMO_ACCESS_KEY = "luojia_demo_access";
const LEGACY_ACCESS_KEY = "mock_auth_token";

export function hasDemoAccess(): boolean {
  if (typeof window === "undefined") return false;
  return (
    window.localStorage.getItem(DEMO_ACCESS_KEY) === "true" ||
    window.localStorage.getItem(LEGACY_ACCESS_KEY) === "true"
  );
}

export function grantDemoAccess(): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(DEMO_ACCESS_KEY, "true");
  window.localStorage.removeItem(LEGACY_ACCESS_KEY);
}
