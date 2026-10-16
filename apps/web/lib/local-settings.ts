export function getUserApiKey() {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem("luojia_user_api_key") || "";
}

export type SupportModel = string;

export const DEFAULT_MODEL = "deepseek-v4-flash";

// The stored id is either a curated catalog id ("deepseek-v4-flash") or a
// provider-prefixed free-form id ("openai:gpt-4o-mini",
// "custom:https://.../v1|model-name") resolved server-side.
export function getPreferredModel(): SupportModel {
  if (typeof window === "undefined") return DEFAULT_MODEL;
  return window.localStorage.getItem("luojia_model") || DEFAULT_MODEL;
}

export function setPreferredModel(model: SupportModel) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem("luojia_model", model);
}

export function setUserApiKey(key: string) {
  if (typeof window === "undefined") return;
  if (key.trim())
    window.localStorage.setItem("luojia_user_api_key", key.trim());
  else window.localStorage.removeItem("luojia_user_api_key");
}
