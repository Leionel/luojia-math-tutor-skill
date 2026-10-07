import type { TutorMeta } from "./api.ts";

/** Saved scoped evidence belongs to this response, never a later turn. */
export function verificationLabel(meta?: TutorMeta | null): string {
  if (!meta) return "尚无核验记录";
  if (meta.error) return "本轮未完成";
  if (meta.awaiting_confirmation) return "等待题目核对";
  if (meta.verification_kind === "root_oracle") return meta.verified ? "已完成求根核对" : "求根结果尚未确定";
  const review = meta.verification_kind === "llm_review" ? (meta.verified ? "推理审查意见" : "推理审查未完成") : "";
  const check = meta.step_check;
  if (!check || check.version !== "step-v1") return review || (meta.verified ? "历史检查（范围未记录）" : "历史回答（核验范围未记录）");
  let label: string;
  if (check.origin === "system_calculation" && check.execution_status === "succeeded") label = "参考计算（未核对学生答案）";
  else if (check.origin === "classification") label = "已检查未定式类型（未确认定理适用）";
  else if (check.execution_status === "timeout") label = "本步核验未确定（超时）";
  else if (check.execution_status === "rejected") label = "本步核验未确定（输入或范围不受支持）";
  else if (check.execution_status === "failed") label = "本步核验未确定（检查失败）";
  else if (check.execution_status === "not_requested") label = check.origin === "heuristic" ? "教学线索（尚未核验）" : "本轮未请求步骤检查";
  else if (meta.is_correct === null || !meta.verified) label = "本步核验未确定";
  else label = meta.is_correct ? "本步候选核对通过（限指定范围）" : "本步候选存在差异（限指定范围）";
  return review && check.execution_status !== "not_requested" ? `${label} · ${review}` : review || label;
}

export function messageStatus(meta?: TutorMeta | null): string | undefined {
  if (!meta) return undefined;
  const label = verificationLabel(meta);
  const mode = meta.teaching_mode ? { direct: "直接讲解", practice: "练习模式", socratic: "引导模式" }[meta.teaching_mode] : undefined;
  return mode ? `${label} · ${mode}` : label;
}
