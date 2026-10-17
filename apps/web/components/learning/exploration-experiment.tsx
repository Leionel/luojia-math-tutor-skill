"use client";
import { useEffect, useState } from "react";
import { learningRequest } from "@/lib/learning-api";
import { getCurrentUserId, getAuthHeaders } from "@/lib/demo-auth";
import { getUserApiKey, getPreferredModel } from "@/lib/local-settings";
import type {
  Exploration,
  ExplorationAdvice,
  ExperimentPlan,
  ExplorationTask,
} from "@/lib/explorations";
import {
  experimentDomains,
  experimentTaskDraft,
  parseExperimentTask,
  planForTasks,
  type Domain,
  type TaskDraft,
} from "@/lib/experiment-plans";
import {
  learningButton,
  learningButtonSecondary,
  learningInput,
} from "./learning-shell";

type PlanDraft = {
  question_to_test: string;
  known_conditions: string;
  varying_factors: string;
  fixed_factors: string;
  observable: string;
  mathematical_reason: string;
  tool_limitations: string;
};
function details(p: ExperimentPlan): PlanDraft {
  return {
    ...p,
    known_conditions: p.known_conditions.join("\n"),
    varying_factors: p.varying_factors.join(", "),
    fixed_factors: p.fixed_factors.join(", "),
    tool_limitations: p.tool_limitations.join("\n"),
  };
}
const blankPlan: PlanDraft = {
  question_to_test: "",
  known_conditions: "",
  varying_factors: "",
  fixed_factors: "",
  observable: "",
  mathematical_reason: "",
  tool_limitations: "",
};
export function ExplorationExperiment({
  record,
  disabled,
  onSaved,
  onRun,
}: {
  record: Exploration;
  disabled: boolean;
  onSaved: (r: Exploration) => void;
  onRun: (body: Record<string, unknown>) => void;
}) {
  const [advice, setAdvice] = useState<ExplorationAdvice | null>(
      record.advice ?? null,
    ),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [domain, setDomain] = useState<Domain>("linear_system"),
    [drafts, setDrafts] = useState<TaskDraft[]>([
      { ...experimentDomains.linear_system.empty },
      { ...experimentDomains.linear_system.empty },
    ]);
  const [plan, setPlan] = useState<PlanDraft>(blankPlan),
    [compare, setCompare] = useState(true),
    [prediction, setPrediction] = useState(""),
    [confirmed, setConfirmed] = useState(false),
    [origin, setOrigin] = useState("student_design");
  const owner = getCurrentUserId(),
    credential = getAuthHeaders().Authorization,
    key = `luojia_experiment_editor:${owner}:${record.id}`;
  function loadTasks(tasks: ExplorationTask[], p?: ExperimentPlan | null) {
    setDomain(tasks[0].domain);
    setDrafts([
      experimentTaskDraft(tasks[0]),
      tasks[1]
        ? experimentTaskDraft(tasks[1])
        : { ...experimentTaskDraft(tasks[0]) },
    ]);
    setCompare(tasks.length === 2);
    setPlan(
      details(
        p?.schema_version === "experiment-plan-v1"
          ? p
          : planForTasks(record.claim, tasks),
      ),
    );
    setConfirmed(false);
  }
  useEffect(() => {
    const latest = [...record.history]
      .reverse()
      .find((h) => h.payload.runs?.length);
    if (latest?.payload.runs?.length) {
      loadTasks(
        latest.payload.runs.map((r) => r.task),
        latest.payload.plan,
      );
      setPrediction(latest.payload.prediction ?? "");
      setOrigin(latest.payload.plan_origin ?? "student_design");
    }
    try {
      const d = JSON.parse(localStorage.getItem(key) ?? "null");
      if (
        d &&
        d.domain in experimentDomains &&
        Array.isArray(d.drafts) &&
        d.drafts.length === 2 &&
        d.drafts.every(
          (t: TaskDraft) =>
            t &&
            experimentDomains[d.domain as Domain].fields.every(
              (f) => typeof t[f.name] === "string",
            ),
        ) &&
        typeof d.prediction === "string" &&
        typeof d.compare === "boolean"
      ) {
        setDomain(d.domain);
        setDrafts(d.drafts);
        setPrediction(d.prediction);
        setCompare(d.compare);
        if (
          [
            "student_design",
            "deterministic_template",
            "model_proposal_edited_by_student",
          ].includes(d.origin)
        )
          setOrigin(d.origin);
        if (
          d.plan &&
          Object.keys(blankPlan).every((k) => typeof d.plan[k] === "string")
        )
          setPlan(d.plan);
      }
    } catch {}
    // Saved history restores the workflow without local browser drafts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  function cache() {
    try {
      localStorage.setItem(
        key,
        JSON.stringify({ domain, drafts, plan, compare, prediction, origin }),
      );
    } catch {
      setError("草稿未能写入浏览器，请先保存实验或复制参数。");
    }
  }
  function edit() {
    setConfirmed(false);
  }
  async function suggest(template = false) {
    setBusy(true);
    setError("");
    setConfirmed(false);
    try {
      if (template) {
        const p = await learningRequest<{ tasks: ExplorationTask[] }>(
          "/explorations/proposal",
        );
        if (
          owner !== getCurrentUserId() ||
          credential !== getAuthHeaders().Authorization
        )
          return;
        loadTasks(p.tasks);
        setOrigin("deterministic_template");
        setAdvice(null);
      } else {
        const apiKey = getUserApiKey();
        const a = await learningRequest<ExplorationAdvice>(
          `/explorations/${record.id}/advice`,
          { expected_revision: record.revision, model: getPreferredModel() },
          AbortSignal.timeout(55000),
          apiKey ? { "X-Luojia-LLM-Key": apiKey } : undefined,
        );
        if (
          owner !== getCurrentUserId() ||
          credential !== getAuthHeaders().Authorization
        )
          return;
        setAdvice(a);
        if (a.exploration) onSaved(a.exploration);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "建议暂不可用。");
    } finally {
      setBusy(false);
    }
  }
  const stale = !!advice && advice.based_on_revision !== record.revision - 1;
  function adopt() {
    const p = advice?.decision?.experiment_proposal;
    if (p) {
      loadTasks(p.tasks, p);
      setOrigin("model_proposal_edited_by_student");
    }
  }
  function run() {
    try {
      const tasks = drafts
        .slice(0, compare ? 2 : 1)
        .map((t) => parseExperimentTask(domain, t));
      const split = (s: string) =>
        s
          .split(/[,，\n]/)
          .map((t) => t.trim())
          .filter(Boolean);
      const p = planForTasks(record.claim, tasks, {
        ...(plan.question_to_test.trim()
          ? { question_to_test: plan.question_to_test }
          : {}),
        known_conditions: plan.known_conditions.split("\n").filter(Boolean),
        ...(plan.varying_factors.trim()
          ? { varying_factors: split(plan.varying_factors) }
          : {}),
        ...(plan.fixed_factors.trim()
          ? { fixed_factors: split(plan.fixed_factors) }
          : {}),
        ...(plan.observable.trim() ? { observable: plan.observable } : {}),
        ...(plan.mathematical_reason.trim()
          ? { mathematical_reason: plan.mathematical_reason }
          : {}),
        ...(plan.tool_limitations.trim()
          ? {
              tool_limitations: plan.tool_limitations
                .split("\n")
                .filter(Boolean),
            }
          : {}),
      });
      cache();
      onRun({
        tasks,
        plan: p,
        plan_origin: origin,
        prediction,
        metrics:
          domain === "integration"
            ? ["value", "error_estimate", "work"]
            : domain === "linear_system"
              ? ["residual", "step", "spectral_radius"]
              : ["residual", "step"],
        confirmed: true,
      });
      setConfirmed(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "参数不可用。");
    }
  }
  return (
    <section
      className="mt-6 space-y-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-5"
      onBlur={cache}
      onChange={edit}
    >
      <h2 className="font-serif text-xl">设计受控对照实验</h2>
      <p className="text-sm leading-7">
        主张 → 可编辑计划 → 我的预测 → 确认计算 → 比较证据 →
        修订。助教提议不会自动运行。
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className={learningButton}
          disabled={disabled || busy}
          onClick={() => void suggest()}
        >
          让助教分析并建议实验
        </button>
        <button
          type="button"
          className={learningButtonSecondary}
          disabled={disabled || busy}
          onClick={() => void suggest(true)}
        >
          采用 GS 默认示例
        </button>
      </div>
      {busy && <p role="status">正在分析已保存的主张、关系和实验…</p>}
      {error && <p role="alert">{error}</p>}
      {advice && (
        <div className="space-y-2 border-l-2 border-dai-600 pl-4 text-sm leading-7">
          <p className="font-semibold">
            {advice.status === "unavailable"
              ? advice.reason
              : stale
                ? "历史助教建议 · 模型意见"
                : "助教建议 · 模型意见，尚未执行"}
          </p>
          <p>{advice.decision?.reason}</p>
          {!!advice.decision?.known_conditions.length && (
            <p>已知条件：{advice.decision.known_conditions.join("；")}</p>
          )}
          {!!advice.decision?.missing_conditions.length && (
            <p>待补条件：{advice.decision.missing_conditions.join("；")}</p>
          )}
          {advice.decision?.experiment_proposal && (
            <>
              <p>
                检验问题：{advice.decision.experiment_proposal.question_to_test}
              </p>
              <p>观察量：{advice.decision.experiment_proposal.observable}</p>
              <p>
                数学理由：
                {advice.decision.experiment_proposal.mathematical_reason}
              </p>
              <p>
                工具限制：
                {advice.decision.experiment_proposal.tool_limitations?.join(
                  "；",
                )}
              </p>
              <button
                type="button"
                className={learningButtonSecondary}
                disabled={disabled || stale}
                onClick={adopt}
              >
                采用建议参数并编辑
              </button>
            </>
          )}
          <p>{advice.follow_up}</p>
          {advice.candidate_warning && <p>{advice.candidate_warning}</p>}
          {!!advice.suggested_graph?.edges.length && (
            <p>关系提议已保存，请在下方“候选关系与处理回执”中决定。</p>
          )}
        </div>
      )}
      <fieldset className="flex flex-wrap gap-4">
        <legend className="mb-2 text-sm">实验方法</legend>
        {(Object.keys(experimentDomains) as Domain[]).map((d) => (
          <label key={d} className="flex min-h-11 items-center gap-2">
            <input
              type="radio"
              name={`method-${record.id}`}
              checked={domain === d}
              onChange={() => {
                setDomain(d);
                setDrafts([
                  { ...experimentDomains[d].empty },
                  { ...experimentDomains[d].empty },
                ]);
                setPlan(blankPlan);
                setOrigin("student_design");
              }}
            />
            {experimentDomains[d].label}
          </label>
        ))}
      </fieldset>
      <label className="flex min-h-11 items-center gap-2">
        <input
          name="compare"
          type="checkbox"
          checked={compare}
          onChange={(e) => setCompare(e.target.checked)}
        />
        增加第二组对照
      </label>
      <div className="grid gap-4 lg:grid-cols-2">
        {drafts.slice(0, compare ? 2 : 1).map((t, i) => (
          <fieldset key={`${domain}-${i}`} className="min-w-0 space-y-3">
            <legend>
              实验 {i === 0 ? "A" : "B"} · {experimentDomains[domain].label}
            </legend>
            {experimentDomains[domain].fields.map((f) => (
              <label key={f.name} className="block text-sm">
                {f.label}
                {f.options ? (
                  <select
                    className={learningInput}
                    aria-label={`实验${i === 0 ? "A" : "B"} ${f.name}`}
                    value={t[f.name]}
                    onChange={(e) =>
                      setDrafts(
                        drafts.map((x, j) =>
                          i === j ? { ...x, [f.name]: e.target.value } : x,
                        ),
                      )
                    }
                  >
                    {f.options.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </select>
                ) : (
                  <textarea
                    rows={f.rows ?? 1}
                    aria-label={`实验${i === 0 ? "A" : "B"} ${f.name}`}
                    className={`${learningInput} max-sm:text-base`}
                    value={t[f.name]}
                    onChange={(e) =>
                      setDrafts(
                        drafts.map((x, j) =>
                          i === j ? { ...x, [f.name]: e.target.value } : x,
                        ),
                      )
                    }
                  />
                )}
              </label>
            ))}
          </fieldset>
        ))}
      </div>
      <details>
        <summary className="min-h-11 cursor-pointer py-3 text-sm font-semibold">
          核对并编辑计划的理由、因素与限制
        </summary>
        <p className="text-xs leading-6">
          因素使用参数字段名；空白因素在确认时按两组实际差异填写。编辑后须重新确认。
        </p>
        {(
          [
            ["question_to_test", "待检验的局部问题"],
            ["known_conditions", "已知条件（每行一条）"],
            ["varying_factors", "变化因素（字段名，用逗号分隔）"],
            ["fixed_factors", "保持因素（字段名，用逗号分隔）"],
            ["observable", "观测量"],
            ["mathematical_reason", "建议背后的数学理由"],
            ["tool_limitations", "工具限制（每行一条）"],
          ] as const
        ).map(([k, label]) => (
          <label key={k} className="mt-3 block text-sm">
            {label}
            <textarea
              className={learningInput}
              value={plan[k]}
              maxLength={k === "mathematical_reason" ? 600 : 500}
              onChange={(e) => setPlan({ ...plan, [k]: e.target.value })}
            />
          </label>
        ))}
      </details>
      <p className="text-sm leading-7">
        工具范围：{experimentDomains[domain].limitations}
      </p>
      <label className="block text-sm">
        运行前，我的预测
        <textarea
          name="prediction"
          aria-label="运行前我的预测"
          className={`${learningInput} max-sm:text-base`}
          rows={3}
          maxLength={1000}
          value={prediction}
          onChange={(e) => setPrediction(e.target.value)}
        />
      </label>
      <label className="flex min-h-11 items-center gap-2 text-sm">
        <input
          name="confirmed"
          type="checkbox"
          checked={confirmed}
          onChange={(e) => {
            e.stopPropagation();
            setConfirmed(e.target.checked);
          }}
        />
        我已核对参数，确认运行参考计算
      </label>
      <button
        type="button"
        className={learningButton}
        disabled={disabled || busy || !confirmed || !prediction.trim()}
        onClick={run}
      >
        确认执行受控实验
      </button>
    </section>
  );
}
