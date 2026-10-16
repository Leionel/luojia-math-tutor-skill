export type DeliveryGuard = {
  version: "delivery-v1" | "delivery-v2" | "delivery-v3";
  scope: "delivery_rules_only";
  status: "passed" | "repaired" | "withheld" | "unavailable";
  rule_ids: string[];
  repair_count: number;
  enabled: boolean;
};

export function deliveryGuardLabel(value: unknown): string | null {
  if (!value || typeof value !== "object") return null;
  const guard = value as Partial<DeliveryGuard>;
  if (!guard.version || !["delivery-v1", "delivery-v2", "delivery-v3"].includes(guard.version) || guard.scope !== "delivery_rules_only") return null;
  if (guard.enabled === false) return "本轮未启用额外交付检查";
  return ({passed: "交付规则检查通过；数学核验状态另见回答标注", repaired: "已修复回答表述并通过交付检查；不代表数学结论已验证",
    withheld: "本轮未交付：回答未通过交付检查", unavailable: "本轮未交付：交付检查暂不可用"} as const)[guard.status as DeliveryGuard["status"]] ?? null;
}
