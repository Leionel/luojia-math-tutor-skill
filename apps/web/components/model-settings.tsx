"use client";

import { useEffect, useState } from "react";
import { fetchModels, testModel, type ModelInfo } from "@/lib/api";
import {
  getPreferredModel,
  getUserApiKey,
  setPreferredModel,
  setUserApiKey,
  DEFAULT_MODEL,
  type SupportModel
} from "@/lib/local-settings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Card, CardTitle } from "@/components/ui/card";

export function ModelSettings() {
  const [key, setKey] = useState("");
  const [model, setModel] = useState<SupportModel>(DEFAULT_MODEL);
  const [status, setStatus] = useState("");
  const [modelCatalog, setModelCatalog] = useState<Record<string, ModelInfo[]>>({});

  useEffect(() => {
    setKey(getUserApiKey());
    setModel(getPreferredModel());

    fetchModels()
      .then((data) => {
        const groups: Record<string, ModelInfo[]> = {};
        for (const item of data.models) {
          if (!groups[item.provider]) {
            groups[item.provider] = [];
          }
          groups[item.provider].push(item);
        }
        setModelCatalog(groups);
      })
      .catch(() => {
        // Fallback to empty catalog (will use static markup below)
      });
  }, []);

  async function saveAndTest() {
    setUserApiKey(key);
    setPreferredModel(model);
    setStatus("测试中...");
    const result = await testModel(key || null, model);
    setStatus(result.message);
  }

  const hasDynamicModels = Object.keys(modelCatalog).length > 0;

  return (
    <Card>
      <CardTitle>模型设置</CardTitle>
      <div className="mb-2 text-xs text-slate-500 dark:text-slate-400">模型凭证默认由服务端管理。仅当管理员显式开启用户 Key 转发时，此处的临时 Key 才会生效。</div>
      <Select
        className="mb-2"
        value={model}
        onChange={(event) => setModel(event.target.value)}
      >
        {hasDynamicModels ? (
          Object.entries(modelCatalog).map(([provider, items]) => (
            <optgroup key={provider} label={provider}>
              {items.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </optgroup>
          ))
        ) : (
          <>
            <optgroup label="DeepSeek">
              <option value="deepseek-v4-flash">DeepSeek v4 Flash</option>
              <option value="deepseek-v4-pro">DeepSeek v4 Pro</option>
            </optgroup>
            <optgroup label="通义千问 (Qwen)">
              <option value="qwen-plus">Qwen Plus</option>
              <option value="qwen3.5-plus">Qwen 3.5 Plus</option>
              <option value="qwen3.6-plus">Qwen 3.6 Plus</option>
            </optgroup>
            <optgroup label="Kimi (Moonshot)">
              <option value="kimi-k3">Kimi K3</option>
              <option value="kimi-k2.6">Kimi K2.6</option>
            </optgroup>
            <optgroup label="智谱 (ZhipuAI)">
              <option value="glm-4.7">GLM-4.7</option>
              <option value="glm-4.7-flash">GLM-4.7 Flash</option>
              <option value="glm-4.6v-flash">GLM-4.6V Flash</option>
            </optgroup>
          </>
        )}
      </Select>
      <Input
        className="mb-2"
        placeholder="用户自带 API Key（可选）"
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
