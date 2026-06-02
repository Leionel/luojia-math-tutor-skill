"use client";

import { useEffect, useState } from "react";
import { testModel } from "@/lib/api";
import {
  getPreferredModel,
  getUserApiKey,
  setPreferredModel,
  setUserApiKey,
  type SupportModel
} from "@/lib/local-settings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Card, CardTitle } from "@/components/ui/card";

export function ModelSettings() {
  const [key, setKey] = useState("");
  const [model, setModel] = useState<SupportModel>("deepseek-v4-flash");
  const [status, setStatus] = useState("");

  useEffect(() => {
    setKey(getUserApiKey());
    setModel(getPreferredModel());
  }, []);

  async function saveAndTest() {
    setUserApiKey(key);
    setPreferredModel(model);
    setStatus("测试中...");
    const result = await testModel(key || null, model);
    setStatus(result.message);
  }

  return (
    <Card>
      <CardTitle>模型设置</CardTitle>
      <div className="mb-2 text-xs text-slate-500 dark:text-slate-400">系统已内置免费的 DeepSeek 兜底 Key，您可以直接使用！若额度耗尽，您也可以在此输入私人 Key 以接管服务。</div>
      <Select
        className="mb-2"
        value={model}
        onChange={(event) => setModel(event.target.value)}
      >
        <optgroup label="DeepSeek">
          <option value="deepseek-v4-flash">DeepSeek v4 Flash</option>
          <option value="deepseek-v4-pro">DeepSeek v4 Pro</option>
        </optgroup>
        <optgroup label="通义千问 (Qwen)">
          <option value="qwen-max-latest">Qwen Max Latest</option>
          <option value="qwen3.7-max">Qwen3.7-Max</option>
          <option value="qwen-plus-latest">Qwen Plus Latest</option>
        </optgroup>
        <optgroup label="Kimi (Moonshot)">
          <option value="kimi-k2.6">Kimi K2.6</option>
          <option value="kimi-k2.5">Kimi K2.5</option>
          <option value="moonshot-v1-auto">Moonshot v1 Auto</option>
        </optgroup>
        <optgroup label="智谱 (ZhipuAI)">
          <option value="glm-5">GLM-5</option>
          <option value="glm-5-turbo">GLM-5-Turbo</option>
          <option value="glm-4.7-flash">GLM-4.7-Flash</option>
        </optgroup>
        <optgroup label="OpenAI">
          <option value="gpt-5.5-instant">GPT-5.5 Instant</option>
          <option value="gpt-5.5">GPT-5.5</option>
          <option value="gpt-5.5-pro">GPT-5.5 Pro</option>
          <option value="gpt-5.3-codex">GPT-5.3 Codex</option>
        </optgroup>
        <optgroup label="Anthropic">
          <option value="claude-opus-4-8">Claude Opus 4.8</option>
          <option value="claude-sonnet-4-6">Claude Sonnet 4.6</option>
          <option value="claude-haiku-4-5">Claude Haiku 4.5</option>
        </optgroup>
        <optgroup label="Google">
          <option value="gemini-3.5-flash">Gemini 3.5 Flash</option>
          <option value="gemini-3.1-pro">Gemini 3.1 Pro</option>
        </optgroup>
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

