"use client";
import { useEffect, useState } from "react";
import { learningRequest } from "@/lib/learning-api";
import { getCurrentUserId, getAuthHeaders } from "@/lib/demo-auth";
import { getUserApiKey, getPreferredModel } from "@/lib/local-settings";
import {
  draftTask,
  taskDraft,
  emptyTask,
  type Exploration,
  type PersonalGraph,
  type DraftTask,
} from "@/lib/explorations";
import type { LinearTask } from "@/lib/numerical-lab";
import {
  learningButton,
  learningButtonSecondary,
  learningInput,
} from "./learning-shell";

import type {
  NewtonTask,
  ExplorationTask,
  ExplorationAdvice,
} from "@/lib/explorations";

export function ExplorationExperiment({
  record,
  disabled,
  onSaved,
  onRun,
  onGraph,
  onReject,
}: {
  record: Exploration;
  disabled: boolean;
  onSaved: (r: Exploration) => void;
  onRun: (body: Record<string, unknown>) => void;
  onGraph: (g: PersonalGraph) => void;
  onReject: () => void;
}) {
  const [advice, setAdvice] = useState<ExplorationAdvice | null>(
      () => record.advice ?? null,
    ),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [kind, setKind] = useState<"gs" | "newton">("gs"),
    [tasks, setTasks] = useState<DraftTask[]>([
      { ...emptyTask },
      { ...emptyTask },
    ]);
  const [newton, setNewton] = useState(
    [0, -2].map((x) => ({
      function: "x^3-2*x+2",
      initial: String(x),
      limit: "20",
      tolerance: "0.000001",
    })),
  );
  const [compare, setCompare] = useState(true),
    [prediction, setPrediction] = useState(""),
    [confirmed, setConfirmed] = useState(false);
  const owner = getCurrentUserId(),
    credential = getAuthHeaders().Authorization;
  const key = `luojia_experiment_editor:${owner}:${record.id}`;
  useEffect(() => {
    const latest = [...record.history]
      .reverse()
      .find((h) => h.payload.runs?.length);
    const recent = latest?.payload.runs ?? [];
    setPrediction(latest?.payload.prediction ?? "");
    setCompare(recent.length === 2);
    if (recent.length) {
      const first = recent[0].task;
      if (first.domain === "root_finding") {
        setKind("newton");
        setNewton(
          recent
            .filter((r) => r.task.domain === "root_finding")
            .map((r) => {
              const t = r.task as NewtonTask;
              return {
                function: t.function,
                initial: String(t.initial_value),
                limit: String(t.limit),
                tolerance: String(t.tolerance),
              };
            }),
        );
        setCompare(recent.length === 2);
      } else
        setTasks([
          taskDraft(first),
          recent[1]?.task.domain === "linear_system"
            ? taskDraft(recent[1].task)
            : { ...emptyTask },
        ]);
    }
    try {
      const d = JSON.parse(localStorage.getItem(key) ?? "null");
      if (
        d &&
        ["gs", "newton"].includes(d.kind) &&
        Array.isArray(d.tasks) &&
        d.tasks.length === 2 &&
        d.tasks.every(
          (t: DraftTask) =>
            t &&
            [t.matrix, t.rhs, t.initial, t.tolerance, t.limit].every(
              (x) => typeof x === "string",
            ),
        ) &&
        Array.isArray(d.newton) &&
        d.newton.length >= 1 &&
        d.newton.length <= 2 &&
        d.newton.every(
          (t: {
            function: string;
            initial: string;
            limit: string;
            tolerance: string;
          }) =>
            t &&
            [t.function, t.initial, t.limit, t.tolerance].every(
              (x) => typeof x === "string",
            ),
        ) &&
        typeof d.compare === "boolean" &&
        typeof d.prediction === "string"
      ) {
        setKind(d.kind);
        setTasks(d.tasks);
        setNewton(d.newton);
        setCompare(d.compare);
        setPrediction(d.prediction);
      }
    } catch {}
    // One editor per saved exploration. A confirmation is never restored.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  function cache() {
    try {
      localStorage.setItem(
        key,
        JSON.stringify({ kind, tasks, newton, compare, prediction }),
      );
    } catch {
      setError("实验草稿无法保存在浏览器，刷新前请复制参数。");
    }
  }
  function edit() {
    setConfirmed(false);
  }
  async function suggest(template = false) {
    setBusy(true);
    setError("");
    try {
      if (template) {
        const p = await learningRequest<{ tasks: LinearTask[] }>(
          "/explorations/proposal",
        );
        if (
          owner !== getCurrentUserId() ||
          credential !== getAuthHeaders().Authorization
        )
          return;
        setTasks(p.tasks.map(taskDraft));
        setKind("gs");
        setCompare(true);
        setAdvice(null);
        edit();
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
      setError(e instanceof Error ? e.message : "建议暂不可用，请重试。");
    } finally {
      setBusy(false);
    }
  }
  const stale = !!advice && advice.based_on_revision !== record.revision - 1;
  function adopt() {
    const p = advice?.decision?.experiment_proposal;
    if (!p) return;
    const first = p.tasks[0];
    if (p.tasks.some((t) => t.domain !== first.domain)) {
      setError("请分别设计同类实验再作对照。");
      return;
    }
    if (first.domain === "root_finding") {
      setKind("newton");
      setNewton(
        p.tasks.map((x) => {
          const t = x as NewtonTask;
          return {
            function: t.function,
            initial: String(t.initial_value),
            limit: String(t.limit),
            tolerance: String(t.tolerance),
          };
        }),
      );
      setCompare(p.tasks.length === 2);
    } else {
      setKind("gs");
      setTasks([
        taskDraft(first),
        p.tasks[1] ? taskDraft(p.tasks[1] as LinearTask) : { ...emptyTask },
      ]);
      setCompare(p.tasks.length === 2);
    }
    edit();
  }
  function run() {
    try {
      const structured: ExplorationTask[] =
        kind === "gs"
          ? tasks.slice(0, compare ? 2 : 1).map(draftTask)
          : newton.slice(0, compare ? 2 : 1).map((t) => {
              const initial_value = Number(t.initial),
                limit = Number(t.limit),
                tolerance = Number(t.tolerance);
              if (
                !t.initial.trim() ||
                !Number.isFinite(initial_value) ||
                Math.abs(initial_value) > 1e6
              )
                throw Error("初值须为绝对值不超过1e6的有限数。");
              if (
                !Number.isInteger(limit) ||
                limit < 1 ||
                limit > 100 ||
                !Number.isFinite(tolerance) ||
                tolerance < 1e-12 ||
                tolerance > 0.01
              )
                throw Error("迭代预算为1–100，阈值为1e−12至0.01。");
              return {
                domain: "root_finding",
                method: "newton",
                function: t.function,
                initial_value,
                tolerance,
                limit,
              };
            });
      cache();
      onRun({
        tasks: structured,
        prediction,
        metrics:
          kind === "gs"
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
        请先保存主张与私人关联，再让助教结合已有计算设计下一步。
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
          {stale && advice.status !== "unavailable" && (
            <p>探索已更新，可重新分析后采用建议。</p>
          )}
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
          {!!advice.suggested_graph?.edges.length && <p>关系提议已保存，请在下方“候选关系与处理回执”中编辑、接受或拒绝。</p>}
        </div>
      )}
      <fieldset className="flex gap-4">
        <legend className="mb-2 text-sm">实验方法</legend>
        {(
          [
            ["gs", "GS 线性迭代"],
            ["newton", "Newton 求根"],
          ] as const
        ).map(([v, label]) => (
          <label key={v} className="flex min-h-11 items-center gap-2">
            <input
              type="radio"
              name={`method-${record.id}`}
              checked={kind === v}
              onChange={() => setKind(v)}
            />
            {label}
          </label>
        ))}
      </fieldset>
      <label className="flex min-h-11 items-center gap-2">
        <input
          name="compare"
          type="checkbox"
          checked={compare}
          onChange={(e) => {
            setCompare(e.target.checked);
            if (newton.length === 1) setNewton([...newton, { ...newton[0] }]);
          }}
        />
        增加第二组对照
      </label>
      {kind === "gs" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {tasks.slice(0, compare ? 2 : 1).map((t, i) => (
            <fieldset key={i} className="min-w-0 space-y-3">
              <legend>实验 {i === 0 ? "A" : "B"}</legend>
              {(
                [
                  ["matrix", "系数矩阵（每行一行）"],
                  ["rhs", "右端项"],
                  ["initial", "初始向量"],
                  ["tolerance", "残差阈值"],
                  ["limit", "迭代上限"],
                ] as const
              ).map(([f, label]) => (
                <label className="block text-sm" key={f}>
                  {label}
                  <textarea
                    name={f}
                    aria-label={`实验${i === 0 ? "A" : "B"} ${f}`}
                    rows={f === "matrix" ? 3 : 1}
                    className={`${learningInput} max-sm:text-base`}
                    value={t[f]}
                    onChange={(e) =>
                      setTasks(
                        tasks.map((x, j) =>
                          j === i ? { ...x, [f]: e.target.value } : x,
                        ),
                      )
                    }
                  />
                </label>
              ))}
            </fieldset>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {newton.slice(0, compare ? 2 : 1).map((t, i) => (
            <fieldset key={i} className="min-w-0 space-y-3">
              <legend>实验 {i === 0 ? "A" : "B"} · Newton</legend>
              {(
                [
                  ["function", "函数 f(x)"],
                  ["initial", "初值"],
                  ["tolerance", "残差阈值"],
                  ["limit", "迭代上限"],
                ] as const
              ).map(([f, label]) => (
                <label className="block text-sm" key={f}>
                  {label}
                  <input
                    name={f}
                    aria-label={`Newton${i === 0 ? "A" : "B"} ${label}`}
                    className={`${learningInput} max-sm:text-base`}
                    value={t[f]}
                    onChange={(e) =>
                      setNewton(
                        newton.map((x, j) =>
                          j === i ? { ...x, [f]: e.target.value } : x,
                        ),
                      )
                    }
                  />
                </label>
              ))}
            </fieldset>
          ))}
        </div>
      )}
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
