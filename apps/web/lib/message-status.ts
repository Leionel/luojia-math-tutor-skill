import type {TutorMeta} from "./api.ts";

/** Status belongs to the saved response, never the latest turn or current selector. */
export function messageStatus(meta?: TutorMeta | null): string | undefined {
  if (!meta) return undefined;
  if (meta.error) return "本轮未完成";
  const verification = meta.awaiting_confirmation ? "等待题目核对"
    : meta.verification_kind === "llm_review" ? (meta.verified ? "推理审查意见" : "推理审查未完成")
    : meta.verification_kind === "root_oracle" ? (meta.verified ? "已完成求根核对" : "求根结果尚未确定")
    : meta.verified ? "已完成本步检查" : "本轮未进行步骤检查";
  const mode = meta.teaching_mode ? {direct:"直接讲解",practice:"练习模式",socratic:"引导模式"}[meta.teaching_mode] : undefined;
  return mode ? `${verification} · ${mode}` : verification;
}
