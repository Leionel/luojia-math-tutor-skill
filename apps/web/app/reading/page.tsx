"use client";

import React from "react";
import { LearningShell } from "@/components/learning/learning-shell";
import { ReadingDomainView } from "@/components/learning/reading-domain-view";

export default function ReadingPage() {
  return (
    <LearningShell
      title="定理研读 · 前提与边界"
      description="精读教材经典选段与公式推导，严密辨析定理适用的前置约束条件，留下学者思考与证据锚点。"
    >
      <ReadingDomainView mode="full" />
    </LearningShell>
  );
}
