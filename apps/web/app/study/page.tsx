"use client";

import React from "react";
import { LearningShell } from "@/components/learning/learning-shell";
import { StudyDomainView } from "@/components/learning/study-domain-view";

export default function StudyPage() {
  return (
    <LearningShell
      title="学习任务 · 条件与过程"
      description="结合到期复习与前日推演，有序完成核心任务；亲手计算并提交迭代序列，验证局部收敛阶。"
    >
      <StudyDomainView mode="full" />
    </LearningShell>
  );
}
