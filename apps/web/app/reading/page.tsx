"use client";

import React from "react";
import { LearningShell } from "@/components/learning/learning-shell";
import { ReadingDomainView } from "@/components/learning/reading-domain-view";

export default function ReadingPage() {
  return (
    <LearningShell
      title="材料伴读 · 原文与理解"
      description="阅读课程整理材料或自己的文档，带着原文讨论条件、推导与疑问，保留来源和笔记。"
    >
      <ReadingDomainView mode="full" />
    </LearningShell>
  );
}
