"use client";

import { Suspense } from "react";
import { LearningShell } from "@/components/learning/learning-shell";
import { CodeDomainView } from "@/components/learning/code-domain-view";
import { useRouter } from "next/navigation";
import type { CodeContextRef } from "@/lib/learning-context";

export default function CodeWorkshopPage() {
  const router = useRouter();

  const handleDiscussFinding = (ref: CodeContextRef) => {
    const encoded = encodeURIComponent(JSON.stringify(ref));
    // The saved reference selects the exact finding; never put student text in URLs.
    router.push(`/chat?ref=${encoded}&workspace=code`);
  };

  return (
    <LearningShell
      title="代码静态审阅 · 过程与依据"
      description="Newton 法等经典作业的代码规范核对与数值轨迹诊断。学生代码安全隔离不予执行，呈现严密数学依据。"
    >
      <Suspense fallback={<div className="p-12 text-center text-xs text-[var(--text-muted)]">正在加载算法工坊…</div>}>
        <CodeDomainView mode="full" onDiscussFinding={handleDiscussFinding} />
      </Suspense>
    </LearningShell>
  );
}
