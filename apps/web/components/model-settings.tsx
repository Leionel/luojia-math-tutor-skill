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
      <div className="mb-2 text-xs text-slate-500 dark:text-slate-400">系统已内置免费的 DeepSeek 兜底 Key，您可以直接使用！若额度耗尽，您也可以在此输入私人 Key 以接管服务。</div>
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
              <option value="deepseek-chat">DeepSeek Chat</option>
              <option value="deepseek-reasoner">DeepSeek Reasoner</option>
              <option value="deepseek-v4-flash">DeepSeek v4 Flash</option>
              <option value="deepseek-v4-pro">DeepSeek v4 Pro</option>
            </optgroup>
            <optgroup label="通义千问 (Qwen)">
              <option value="qwen-max">Qwen Max</option>
              <option value="qwen-plus">Qwen Plus</option>
              <option value="qwen-turbo">Qwen Turbo</option>
              <option value="qwen-math-plus">Qwen Math Plus</option>
            </optgroup>
            <optgroup label="Kimi (Moonshot)">
              <option value="moonshot-v1-8k">Moonshot v1 8K</option>
              <option value="moonshot-v1-32k">Moonshot v1 32K</option>
            </optgroup>
            <optgroup label="智谱 (ZhipuAI)">
              <option value="glm-4">GLM-4</option>
              <option value="glm-4-flash">GLM-4 Flash</option>
              <option value="glm-4v">GLM-4V</option>
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
