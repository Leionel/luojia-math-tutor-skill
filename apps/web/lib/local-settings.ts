export function getUserApiKey() {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem("luojia_user_api_key") || "";
}

export type SupportModel = string;

export function getPreferredModel(): SupportModel {
  if (typeof window === "undefined") return "deepseek-v4-flash";
  const value = window.localStorage.getItem("luojia_model");
  if (value) {
    return value;
  }
  return "deepseek-v4-flash";
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
