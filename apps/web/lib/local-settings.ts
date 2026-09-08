export function getUserApiKey() {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem("luojia_user_api_key") || "";
}

export type SupportModel = string;

export const DEFAULT_MODEL = "deepseek-v4-flash";
const SUPPORTED_MODELS = new Set([
  "deepseek-v4-flash",
  "deepseek-v4-pro",
  "qwen-plus",
  "qwen3.5-plus",
  "qwen3.6-plus",
  "kimi-k3",
  "kimi-k2.6",
  "glm-4.7",
  "glm-4.7-flash",
  "glm-4.6v-flash",
]);

export function getPreferredModel(): SupportModel {
  if (typeof window === "undefined") return DEFAULT_MODEL;
  const value = window.localStorage.getItem("luojia_model");
  if (value && SUPPORTED_MODELS.has(value)) {
    return value;
  }
  return DEFAULT_MODEL;
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
