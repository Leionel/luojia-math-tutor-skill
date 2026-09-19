"use client";

import { useEffect, useState } from "react";
import { fetchModels, testModel, type ProviderInfo } from "@/lib/api";
import {
  getPreferredModel,
  getUserApiKey,
  setPreferredModel,
  setUserApiKey,
} from "@/lib/local-settings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Card, CardTitle } from "@/components/ui/card";

const FALLBACK_PROVIDERS: ProviderInfo[] = [
  { id: "deepseek", label: "DeepSeek", base_url: "https://api.deepseek.com/v1" },
  { id: "kimi", label: "Kimi (Moonshot)", base_url: "https://api.moonshot.cn/v1" },
  { id: "qwen", label: "通义千问 (Qwen)", base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1" },
  { id: "glm", label: "智谱 (GLM)", base_url: "https://open.bigmodel.cn/api/paas/v4" },
  { id: "openai", label: "OpenAI", base_url: "https://api.openai.com/v1" },
  { id: "anthropic", label: "Anthropic", base_url: "https://api.anthropic.com/v1" },
  { id: "gemini", label: "Gemini", base_url: "https://generativelanguage.googleapis.com/v1beta/openai" },
  { id: "grok", label: "Grok (xAI)", base_url: "https://api.x.ai/v1" },
  { id: "custom", label: "自定义", base_url: "" },
];

// Stored preferred-model ids look like "provider:model" (or
// "custom:https://host/v1|model"); bare ids are legacy curated picks.
function splitModelId(id: string): { provider: string; modelName: string; base: string } {
  if (id.startsWith("custom:")) {
    const rest = id.slice("custom:".length);
    const sep = rest.indexOf("|");
    if (sep > 0) {
      return { provider: "custom", base: rest.slice(0, sep), modelName: rest.slice(sep + 1) };
    }
    return { provider: "custom", base: "", modelName: "" };
  }
  const sep = id.indexOf(":");
  if (sep > 0) {
    return { provider: id.slice(0, sep), base: "", modelName: id.slice(sep + 1) };
  }
  return { provider: "deepseek", base: "", modelName: id };
}

export function ModelSettings() {
  const [key, setKey] = useState("");
  const [provider, setProvider] = useState("deepseek");
  const [modelName, setModelName] = useState("");
  const [customBase, setCustomBase] = useState("");
  const [status, setStatus] = useState("");
  const [providers, setProviders] = useState<ProviderInfo[]>(FALLBACK_PROVIDERS);

  useEffect(() => {
    setKey(getUserApiKey());
    const saved = splitModelId(getPreferredModel());
    setProvider(saved.provider);
    setModelName(saved.modelName);
    setCustomBase(saved.base);

    fetchModels()
      .then((data) => {
        if (data.providers && data.providers.length > 0) {
          setProviders(data.providers);
        }
      })
      .catch(() => {
        // Keep the static provider list when the backend is unreachable.
      });
  }, []);

  function composeModelId(): string {
    const name = modelName.trim();
    if (provider === "custom") {
      const base = customBase.trim().replace(/\/+$/, "");
      return base && name ? `custom:${base}|${name}` : "";
    }
    return name ? `${provider}:${name}` : "";
  }

  async function saveAndTest() {
    const id = composeModelId();
    if (!id) {
      setStatus(provider === "custom" ? "请填写接口地址与模型名称。" : "请填写模型名称。");
      return;
    }
    setUserApiKey(key);
    setPreferredModel(id);
    setStatus("测试中...");
    const result = await testModel(key || null, id);
    setStatus(result.message);
  }

  return (
    <Card>
      <CardTitle>模型设置</CardTitle>
      <div className="mb-2 text-xs text-slate-500 dark:text-slate-400">选择供应商并填写模型名称；模型凭证默认由服务端管理，仅当管理员开启用户 Key 转发时，此处的临时 Key 才会生效。</div>
      <Select
        className="mb-2"
        value={provider}
        onChange={(event) => setProvider(event.target.value)}
      >
        {providers.map((p) => (
          <option key={p.id} value={p.id}>
            {p.label}
          </option>
        ))}
      </Select>
      {provider === "custom" ? (
        <Input
          className="mb-2"
          placeholder="接口地址（https://…/v1）"
          value={customBase}
          onChange={(event) => setCustomBase(event.target.value)}
        />
      ) : null}
      <Input
        className="mb-2"
        placeholder="模型名称，例如 gpt-4o-mini、deepseek-chat"
        value={modelName}
        onChange={(event) => setModelName(event.target.value)}
      />
      <Input
        className="mb-2"
        placeholder="该供应商的 API Key（可选）"
        type="password"
        value={key}
        onChange={(event) => setKey(event.target.value)}
      />
      <Button variant="outline" size="sm" onClick={saveAndTest}>
        保存并测试
      </Button>
      {status ? <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">{status}</div> : null}
    </Card>
  );
}
