"use client";
import Link from "next/link";
import { getCurrentUserId } from "@/lib/demo-auth";
import { useEffect, useRef, useState } from "react";
import {
  LearningShell,
  Notice,
  learningButton,
  learningButtonSecondary,
  learningInput,
  learningPanel,
  AtelierFolioCard,
} from "@/components/learning/learning-shell";
import {
  finiteNumber,
  learningRequest,
  stableRequestId,
  type LabRun,
  type RootParameters,
} from "@/lib/learning-api";
import { LabReflection } from "@/components/learning/lab-reflection";
import { ExperimentNavigation } from "@/components/learning/experiment-navigation";
import { LabTutor } from "@/components/learning/lab-tutor";
import { MobileDrawer } from "@/components/mobile-drawer";
import {
  MessageCircle,
  FlaskConical,
  Sparkles,
  Play,
  Compass,
  Gauge,
  Layers,
  ArrowRight,
} from "lucide-react";
import { rootContextRef, type RootContextRef } from "@/lib/learning-context";
import { LabPlayback } from "@/components/learning/lab-playback";
import { NewtonActivity } from "@/components/learning/newton-activity";

type LabWorkspaceProps = {
  embedded?: boolean;
  initialRef?: RootContextRef;
  draftPrediction?: string;
  sessionId?: string;
  onDiscuss?: (ref: RootContextRef) => void;
  onSaved?: (run: LabRun) => void;
};
export function LabWorkspace({
  embedded = false,
  initialRef,
  draftPrediction,
  sessionId,
  onDiscuss,
  onSaved,
}: LabWorkspaceProps) {
  const [tab, setTab] = useState<"activity" | "experiment">(
    initialRef?.activity_claim ? "activity" : "experiment",
  );
  const locate = (url: string) => {
    if (!embedded) window.history.replaceState(null, "", url);
  };
  const discuss = (selected: LabRun, step: number) => {
    if (embedded) {
      onDiscuss?.(rootContextRef(selected, step));
      return;
    }
    setTutorRun(selected);
    setSelectedStep(step);
    setTutorOpen(true);
  };
  useEffect(() => {
    const tabParam = new URLSearchParams(window.location.search).get("tab");
    if (tabParam === "activity" || tabParam === "experiment") {
      setTab(tabParam);
    } else if (initialRef) {
      setTab(initialRef.activity_claim ? "activity" : "experiment");
    }
  }, [initialRef]);
  const [desktop, setDesktop] = useState(false);
  const [tutorOpen, setTutorOpen] = useState(false);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const operation = useRef<AbortController | null>(null);
  const mounted = useRef(false);
  const locked = useRef(false);
  const [method, setMethod] = useState<RootParameters["method"]>("newton");
  const [expression, setExpression] = useState("x^3-2*x+2");
  const [initial, setInitial] = useState("0");
  const [left, setLeft] = useState("-2");
  const [right, setRight] = useState("0");
  const [phi, setPhi] = useState("cos(x)");
  const [tolerance, setTolerance] = useState("0.0001");
  const [goal, setGoal] = useState<"root_error" | "residual">("residual");
  const [limit, setLimit] = useState("20");
  const [prediction, setPrediction] = useState("");
  const [run, setRun] = useState<LabRun | null>(null);
  const [tutorRun, setTutorRun] = useState<LabRun | null>(null);
  const [history, setHistory] = useState<LabRun[]>([]);
  const [comparison, setComparison] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [presetValue, setPresetValue] = useState("cycle");
  useEffect(() => {
    mounted.current = true;
    const media = window.matchMedia("(min-width: 1280px)");
    const update = () => {
      setDesktop(media.matches);
      if (media.matches) setTutorOpen(false);
    };
    update();
    media.addEventListener("change", update);
    const cancel = () => {
      mounted.current = false;
      operation.current?.abort();
      setRun(null);
      setTutorRun(null);
      setHistory([]);
      setSelectedStep(null);
      setComparison("");
      setPrediction("");
      setMethod("newton");
      setExpression("x^3-2*x+2");
      setInitial("0");
      setLeft("-2");
      setRight("0");
      setPhi("cos(x)");
      setTolerance("0.0001");
      setGoal("residual");
      setLimit("20");
      setPresetValue("cycle");
      setError("身份已变化，请刷新后继续。");
    };
    window.addEventListener("luojia-auth-change", cancel);
    return () => {
      mounted.current = false;
      operation.current?.abort();
      media.removeEventListener("change", update);
      window.removeEventListener("luojia-auth-change", cancel);
    };
  }, []);
  useEffect(() => {
    try {
      const d = JSON.parse(
        localStorage.getItem(`lab-draft:${getCurrentUserId()}`) ?? "null",
      );
      if (d && typeof d === "object") {
        if (["newton", "bisection", "fixed_point"].includes(d.method))
          setMethod(d.method);
        if (["root_error", "residual"].includes(d.goal)) setGoal(d.goal);
        if (
          ["cycle", "root", "bisect", "fixed", "custom"].includes(d.presetValue)
        )
          setPresetValue(d.presetValue);
        if (typeof d.expression === "string") setExpression(d.expression);
        if (typeof d.initial === "string") setInitial(d.initial);
        if (typeof d.left === "string") setLeft(d.left);
        if (typeof d.right === "string") setRight(d.right);
        if (typeof d.phi === "string") setPhi(d.phi);
        if (typeof d.tolerance === "string") setTolerance(d.tolerance);
        if (typeof d.limit === "string") setLimit(d.limit);
        if (typeof d.prediction === "string") setPrediction(d.prediction);
      }
    } catch {
      /* A corrupt browser draft does not alter server history. */
    }
    setHydrated(true);
    const owner = getCurrentUserId(),
      controller = new AbortController();
    operation.current = controller;
    learningRequest<{ runs: LabRun[] }>(
      "/root-lab/runs",
      undefined,
      controller.signal,
    )
      .then(async (a) => {
        if (!mounted.current || owner !== getCurrentUserId()) return;
        const openRuns = a.runs.filter(
          (item) => !item.id.startsWith("newton-"),
        );
        setHistory(openRuns);
        const id =
          initialRef?.record_id ??
          new URLSearchParams(window.location.search).get("id");
        const loaded =
          id && !id.startsWith("newton-")
            ? await learningRequest<LabRun>(
                `/root-lab/runs/${encodeURIComponent(id)}`,
                undefined,
                controller.signal,
              )
            : (openRuns.at(-1) ?? null);
        if (mounted.current && owner === getCurrentUserId()) {
          setRun(loaded);
          const step = new URLSearchParams(window.location.search).get("step");
          if (
            step !== null &&
            loaded &&
            Number.isInteger(Number(step)) &&
            Number(step) >= 0 &&
            Number(step) < loaded.rows.length
          )
            setSelectedStep(Number(step));
        }
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [initialRef?.record_id]);
  useEffect(() => {
    if (hydrated)
      localStorage.setItem(
        `lab-draft:${getCurrentUserId()}`,
        JSON.stringify({
          method,
          expression,
          initial,
          left,
          right,
          phi,
          tolerance,
          goal,
          limit,
          prediction,
          presetValue,
        }),
      );
  }, [
    hydrated,
    method,
    expression,
    initial,
    left,
    right,
    phi,
    tolerance,
    goal,
    limit,
    prediction,
    presetValue,
  ]);
  useEffect(() => {
    if (hydrated && draftPrediction) setPrediction(draftPrediction);
  }, [draftPrediction, hydrated]);
  const compare = history.find((r) => r.id === comparison);
  const comparable =
    compare &&
    run &&
    compare.parameters.function === run.parameters.function &&
    compare.parameters.goal === run.parameters.goal &&
    compare.parameters.tolerance === run.parameters.tolerance;
  const submit = async () => {
    if (locked.current || !mounted.current) return;
    locked.current = true;
    const owner = getCurrentUserId(),
      controller = new AbortController();
    operation.current?.abort();
    operation.current = controller;
    setBusy(true);
    setError("");
    try {
      const params: RootParameters = {
        method,
        function: expression,
        tolerance: finiteNumber(tolerance, "容差"),
        goal,
        interval: [finiteNumber(left, "左端点"), finiteNumber(right, "右端点")],
        ...(method === "bisection"
          ? {}
          : { initial_value: finiteNumber(initial, "初值") }),
        ...(method === "fixed_point" ? { phi } : {}),
      };
      const result = await learningRequest<LabRun>(
        "/root-lab/runs",
        {
          attempt: params,
          max_iterations: finiteNumber(limit, "迭代上限"),
          prediction,
          request_id: stableRequestId(
            localStorage,
            `lab-request:${getCurrentUserId()}`,
            { params, limit, prediction },
            () => crypto.randomUUID(),
          ),
        },
        controller.signal,
      );
      if (!mounted.current || owner !== getCurrentUserId()) return;
      setSelectedStep(null);
      setTutorRun(null);
      setRun(result);
      locate(`/lab?id=${encodeURIComponent(result.id)}`);
      onSaved?.(result);
      setHistory((previous) =>
        [...previous.filter((r) => r.id !== result.id), result].slice(-20),
      );
    } catch (e) {
      if (!controller.signal.aborted)
        setError(e instanceof Error ? e.message : "实验失败");
    } finally {
      locked.current = false;
      if (mounted.current) setBusy(false);
    }
  };
  const preset = (value: string, updatePrediction = false) => {
    setPresetValue(value);
    setComparison("");
    if (value === "cycle") {
      setMethod("newton");
      setExpression("x^3-2*x+2");
      setInitial("0");
      setLeft("-2");
      setRight("0");
      setGoal("residual");
      if (updatePrediction || !prediction.trim()) {
        setPrediction(
          "我预计在拐点附近会产生周期振荡或向外逃逸；依据是该点导数未能引导切线向根收缩。",
        );
      }
    }
    if (value === "root") {
      setMethod("newton");
      setExpression("x^2-2");
      setInitial("1");
      setLeft("1");
      setRight("2");
      setGoal("root_error");
      if (updatePrediction || !prediction.trim()) {
        setPrediction(
          "我预计从 x₀=1 出发将快速二次收敛到 √2 附近；依据是局部邻域内 f'(x)≠0 且满足单调凸性。",
        );
      }
    }
    if (value === "bisect") {
      setMethod("bisection");
      setExpression("x^2-2");
      setLeft("1");
      setRight("2");
      setGoal("root_error");
      if (updatePrediction || !prediction.trim()) {
        setPrediction(
          "我预计每步区间对半缩小，约需 14 次迭代达到 10⁻⁴ 精度；依据是 (b-a)/2^k 理论误差界。",
        );
      }
    }
    if (value === "fixed") {
      setMethod("fixed_point");
      setExpression("cos(x)-x");
      setPhi("cos(x)");
      setInitial("0.5");
      setLeft("0");
      setRight("1");
      setGoal("root_error");
      if (updatePrediction || !prediction.trim()) {
        setPrediction(
          "我预计将在根附近交替收敛；依据是 |phi'(x)| = |sin(x)| < 1 满足压缩映射原理。",
        );
      }
    }
  };
  const saved = (next: LabRun) => {
    setTutorRun(null);
    setRun(next);
    setSelectedStep(null);
    setComparison("");
    setHistory((previous) =>
      [...previous.filter((r) => r.id !== next.id), next].slice(-20),
    );
    locate(`/lab?id=${encodeURIComponent(next.id)}`);
    onSaved?.(next);
  };
  const activeTutorRun = tutorRun ?? run;
  const content = (
    <>
      <nav
        aria-label="实验视图"
        className="mb-8 flex flex-wrap gap-2 border-b border-paper-200 dark:border-paper-800 pb-3"
      >
        <button
          type="button"
          aria-pressed={tab === "activity"}
          onClick={() => {
            setTab("activity");
            locate("/lab?tab=activity");
          }}
          className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs sm:text-sm font-semibold transition-all duration-200 ${
            tab === "activity"
              ? "bg-olive-600/15 text-olive-800 dark:text-olive-200 border border-olive-600/30 shadow-xs"
              : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]/70 hover:text-[var(--text-primary)]"
          }`}
        >
          <Sparkles className="w-4 h-4 text-olive-600" />
          <span>参与式探究活动（牛顿法收敛与发散）</span>
        </button>
        <button
          type="button"
          aria-pressed={tab === "experiment"}
          onClick={() => {
            setTab("experiment");
            locate("/lab?tab=experiment");
          }}
          className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs sm:text-sm font-semibold transition-all duration-200 ${
            tab === "experiment"
              ? "bg-olive-600/15 text-olive-800 dark:text-olive-200 border border-olive-600/30 shadow-xs"
              : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]/70 hover:text-[var(--text-primary)]"
          }`}
        >
          <FlaskConical className="w-4 h-4 text-dai-600" />
          <span>自由数值实验台（多算法横向对比）</span>
        </button>
      </nav>

      <div hidden={tab !== "activity"}>
        <NewtonActivity
          selectedRef={initialRef}
          onReview={embedded ? onDiscuss : undefined}
          onDiscuss={discuss}
        />
      </div>
      <div hidden={tab !== "experiment"}>
        <div className="mb-5 border-t border-[var(--border-subtle)] pt-8">
          <p className="font-mono text-xs tracking-[.2em] text-olive-700 dark:text-olive-300">
            OPEN LAB / 自由实验
          </p>
          <h2 className="mt-2 font-title text-2xl font-semibold">
            换一个条件，再做一次实验
          </h2>
          <p className="mt-2 text-base sm:text-sm leading-7 text-[var(--text-secondary)]">
            每次保存新的轨迹与版本引用。
            {embedded
              ? "选中实验或修订后，在左侧同一会话继续讨论。"
              : "每次实验都要重新核对条件。"}
          </p>
        </div>
        <Notice error={error} />
        <div
          className={
            !embedded && activeTutorRun?.parameters.method === "newton"
              ? "grid items-start gap-8 xl:grid-cols-[minmax(0,1fr)_400px]"
              : ""
          }
        >
          <div
            className={`grid gap-8 ${embedded ? "" : "lg:grid-cols-[minmax(240px,.75fr)_minmax(0,1.4fr)]"}`}
          >
            {" "}
            <AtelierFolioCard
              title={
                <div className="flex items-center gap-2">
                  <FlaskConical className="w-5 h-5 text-olive-600 shrink-0" />
                  <span>实验参数配置台</span>
                </div>
              }
              badge="受控单变量探究"
              badgeVariant="olive"
              className="self-start"
            >
              {/* 预设探索起点选择器 (Preset Quick Pills) */}
              <div className="mb-5">
                <div className="flex items-center justify-between mb-2">
                  <label htmlFor="preset" className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5 text-olive-600" />
                    <span>选择探究案题起点</span>
                  </label>
                  <span className="text-[11px] text-[var(--text-muted)] font-mono">
                    {presetValue === "custom" ? "自定义配置" : "经典收敛探针"}
                  </span>
                </div>

                {/* 隐藏的原生 select 保证测试与无障碍兼容 */}
                <select
                  id="preset"
                  name="preset"
                  value={presetValue}
                  className="sr-only"
                  onChange={(e) => preset(e.target.value)}
                >
                  <option value="custom">自定义参数</option>
                  <option value="cycle">牛顿法：给定函数与初值</option>
                  <option value="root">牛顿法：逼近 √2</option>
                  <option value="bisect">二分法：缩小有根区间</option>
                  <option value="fixed">不动点：cos(x) 迭代</option>
                </select>

                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: "root", label: "逼近 √2", icon: "⚡", desc: "牛顿二次收敛" },
                    { id: "cycle", label: "拐点震荡", icon: "🔄", desc: "周期死循环反例" },
                    { id: "bisect", label: "二分收缩", icon: "✂️", desc: "区间对半压缩" },
                    { id: "fixed", label: "不动点迭代", icon: "🎯", desc: "cos(x) 吸引子" },
                  ].map((item) => {
                    const active = presetValue === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => preset(item.id, true)}
                        className={`group relative flex flex-col items-start p-2.5 rounded-xl border text-left transition-all duration-200 cursor-pointer ${
                          active
                            ? "bg-olive-500/10 border-olive-500/50 shadow-xs"
                            : "bg-[var(--bg-card)] border-paper-300/80 dark:border-paper-700/80 hover:border-olive-500/30 hover:bg-olive-500/[0.03]"
                        }`}
                      >
                        <div className="flex items-center gap-1.5 font-medium text-xs text-[var(--text-primary)]">
                          <span className="text-sm">{item.icon}</span>
                          <span>{item.label}</span>
                        </div>
                        <span className="text-[10px] text-[var(--text-muted)] mt-0.5 truncate w-full">
                          {item.desc}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <form
                className="space-y-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  submit();
                }}
              >
                {/* 求解算法选择 (Method Segmented Control) */}
                <div>
                  <label htmlFor="method" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono">
                    求解算法
                  </label>
                  <select
                    id="method"
                    name="method"
                    className="sr-only"
                    value={method}
                    onChange={(e) => {
                      setPresetValue("custom");
                      setMethod(e.target.value as RootParameters["method"]);
                    }}
                  >
                    <option value="newton">标准牛顿法</option>
                    <option value="bisection">二分法</option>
                    <option value="fixed_point">不动点迭代</option>
                  </select>

                  <div className="grid grid-cols-3 gap-1.5 p-1 rounded-xl bg-[var(--bg-input)] border border-paper-300 dark:border-paper-700">
                    {[
                      { key: "newton", label: "牛顿切线法" },
                      { key: "bisection", label: "区间二分法" },
                      { key: "fixed_point", label: "不动点迭代" },
                    ].map((item) => {
                      const active = method === item.key;
                      return (
                        <button
                          key={item.key}
                          type="button"
                          onClick={() => {
                            setPresetValue("custom");
                            setMethod(item.key as RootParameters["method"]);
                          }}
                          className={`py-1.5 px-2 rounded-lg text-xs font-medium transition-all text-center cursor-pointer ${
                            active
                              ? "bg-[var(--bg-card)] text-olive-800 dark:text-olive-200 shadow-2xs font-semibold border border-olive-500/30"
                              : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                          }`}
                        >
                          {item.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* 待解函数 f(x) */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label htmlFor="function" className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono flex items-center gap-1">
                      <span>目标方程 f(x) = 0</span>
                    </label>
                    <span className="font-mono text-[10px] text-olive-700 dark:text-olive-300 bg-olive-500/10 px-1.5 py-0.2 rounded border border-olive-500/20">
                      f(x)
                    </span>
                  </div>
                  <input
                    id="function"
                    name="function"
                    required
                    maxLength={200}
                    className={`${learningInput} font-mono`}
                    value={expression}
                    onChange={(e) => {
                      setPresetValue("custom");
                      setExpression(e.target.value);
                    }}
                    placeholder="例如：x^2 - 2"
                  />
                </div>

                {/* 不动点迭代辅助映射 phi(x) */}
                {method === "fixed_point" && (
                  <div className="animate-fade-in">
                    <div className="flex items-center justify-between mb-1.5">
                      <label htmlFor="phi" className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono">
                        等价映射格式 phi(x)
                      </label>
                      <span className="font-mono text-[10px] text-dai-700 dark:text-dai-300 bg-dai-500/10 px-1.5 py-0.2 rounded border border-dai-500/20">
                        x = φ(x)
                      </span>
                    </div>
                    <input
                      id="phi"
                      name="phi"
                      required
                      maxLength={200}
                      className={`${learningInput} font-mono`}
                      value={phi}
                      onChange={(e) => {
                        setPresetValue("custom");
                        setPhi(e.target.value);
                      }}
                      placeholder="例如：cos(x)"
                    />
                  </div>
                )}

                {/* 初始探针初值 x0 (二分法不需要) */}
                {method !== "bisection" && (
                  <div className="animate-fade-in">
                    <div className="flex items-center justify-between mb-1.5">
                      <label htmlFor="initial" className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono">
                        初始迭代探针 x₀
                      </label>
                      <span className="text-[10px] text-[var(--text-muted)]">
                        初值邻域决定局部收敛
                      </span>
                    </div>
                    <input
                      id="initial"
                      name="initial"
                      required
                      className={`${learningInput} font-mono`}
                      value={initial}
                      onChange={(e) => {
                        setPresetValue("custom");
                        setInitial(e.target.value);
                      }}
                      placeholder="例如：1.0"
                    />
                  </div>
                )}

                {/* 探究区间 [a, b] */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono">
                      闭区间 [ a , b ] 约束
                    </label>
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">
                      有根/隔根邻域
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 p-2 rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-input)]/50">
                    <div>
                      <span className="block text-[10px] text-[var(--text-muted)] font-mono mb-1">下界 a</span>
                      <input
                        id="left"
                        name="left"
                        required
                        className={`${learningInput} font-mono py-1.5 text-xs`}
                        value={left}
                        onChange={(e) => {
                          setPresetValue("custom");
                          setLeft(e.target.value);
                        }}
                      />
                    </div>
                    <div>
                      <span className="block text-[10px] text-[var(--text-muted)] font-mono mb-1">上界 b</span>
                      <input
                        id="right"
                        name="right"
                        required
                        className={`${learningInput} font-mono py-1.5 text-xs`}
                        value={right}
                        onChange={(e) => {
                          setPresetValue("custom");
                          setRight(e.target.value);
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* 观察目标与收敛准则 */}
                <div>
                  <label htmlFor="goal" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono">
                    收敛观察准则
                  </label>
                  <select
                    id="goal"
                    name="goal"
                    className={learningInput}
                    value={goal}
                    onChange={(e) => {
                      setPresetValue("custom");
                      setGoal(e.target.value as "root_error" | "residual");
                    }}
                  >
                    <option value="residual">残差准则：|f(xₖ)| &lt; ε</option>
                    <option value="root_error">根误差准则：|xₖ - x*| &lt; ε（须有可核对的界）</option>
                  </select>
                </div>

                {/* 容差阈值与上限步数 */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="tolerance" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono">
                      容差阈值 ε
                    </label>
                    <input
                      id="tolerance"
                      name="tolerance"
                      required
                      className={`${learningInput} font-mono`}
                      value={tolerance}
                      onChange={(e) => {
                        setPresetValue("custom");
                        setTolerance(e.target.value);
                      }}
                      placeholder="0.0001"
                    />
                  </div>
                  <div>
                    <label htmlFor="limit" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono">
                      迭代上限 N_max
                    </label>
                    <input
                      id="limit"
                      name="limit"
                      type="number"
                      min={1}
                      max={100}
                      required
                      className={`${learningInput} font-mono`}
                      value={limit}
                      onChange={(e) => {
                        setPresetValue("custom");
                        setLimit(e.target.value);
                      }}
                    />
                  </div>
                </div>

                {/* 科学假说预测 */}
                <div className="rounded-xl border border-ochre-500/30 bg-ochre-500/[0.04] p-3.5 space-y-2">
                  <div className="flex items-center justify-between">
                    <label htmlFor="prediction" className="text-xs font-semibold text-ochre-800 dark:text-ochre-200 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-ochre-600" />
                      <span>先写下科学假说 / 预测行为</span>
                    </label>
                    <span className="font-mono text-[10px] text-ochre-700 dark:text-ochre-300 bg-ochre-500/10 px-1.5 py-0.2 rounded">
                      先验推演
                    </span>
                  </div>
                  <textarea
                    id="prediction"
                    name="prediction"
                    required
                    maxLength={1000}
                    rows={3}
                    className={`${learningInput} text-xs leading-relaxed`}
                    value={prediction}
                    onChange={(e) => setPrediction(e.target.value)}
                    placeholder="我预计接下来会……；依据是……"
                  />
                  {/* 快捷灵感芯片 */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <span className="text-[10px] text-[var(--text-muted)]">灵感填入：</span>
                    {[
                      { label: "二次收敛", text: "预计 4~5 步二次收敛；依据是初值靠近根且导数非零。" },
                      { label: "死循环震荡", text: "预计在拐点附近死循环震荡；依据是局部切线反弹。" },
                      { label: "对半收缩", text: "预计稳步对半收缩，约 14 步达到 10⁻⁴ 精度。" },
                    ].map((item) => (
                      <button
                        key={item.label}
                        type="button"
                        onClick={() => setPrediction(item.text)}
                        className="text-[10px] px-2 py-0.5 rounded-md border border-ochre-500/20 bg-ochre-500/10 text-ochre-800 dark:text-ochre-200 hover:bg-ochre-500/20 transition-colors cursor-pointer"
                      >
                        + {item.label}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={busy || !prediction.trim()}
                  className={`w-full ${learningButton} py-3 shadow-md hover:shadow-lg`}
                >
                  {busy ? (
                    <span className="flex items-center gap-2">
                      <span className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                      <span>正在求解并追踪轨迹…</span>
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Play className="w-4 h-4 fill-current" />
                      <span>启动受控数值推演</span>
                    </span>
                  )}
                </button>
              </form>
            </AtelierFolioCard>
            <section className="min-w-0">
              {!run ? (
                <AtelierFolioCard
                  title="即时算式蓝图 · 动态预演"
                  badge={
                    method === "newton"
                      ? "Newton-Raphson 局部二次切线逼近"
                      : method === "bisection"
                        ? "Bolzano 介值区间对半收缩"
                        : "Banach 压缩映射单调/交替迭代"
                  }
                  badgeVariant="olive"
                  className="h-full flex flex-col justify-between"
                >
                  <div className="space-y-6">
                    {/* 数学黑板蓝图卡 (Mathematical Blueprint Blackboard) */}
                    <div className="relative rounded-2xl border border-paper-300/80 dark:border-paper-700/80 bg-gradient-to-br from-paper-100/90 via-paper-50/50 to-paper-100/60 dark:from-paper-900/40 dark:via-paper-800/30 dark:to-paper-900/40 p-5 sm:p-6 shadow-inner">
                      <div className="flex items-center justify-between mb-3 text-xs font-mono text-[var(--text-muted)]">
                        <span className="flex items-center gap-1.5 text-olive-700 dark:text-olive-300 font-semibold">
                          <Gauge className="w-3.5 h-3.5" />
                          <span>BLUEPRINT / 动态算式蓝图</span>
                        </span>
                        <span>{goal === "residual" ? "准则: |f(x)| < ε" : "准则: |x - x*| < ε"}</span>
                      </div>

                      {/* 方程大字排版 */}
                      <div className="text-center py-4">
                        <div className="font-mono text-xl sm:text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                          f(x) = {expression || "x^2 - 2"} = 0
                        </div>
                        {method === "fixed_point" && (
                          <div className="mt-2 font-mono text-sm sm:text-base text-dai-700 dark:text-dai-300">
                            映射方程：x = φ(x) = {phi || "cos(x)"}
                          </div>
                        )}
                        <div className="mt-3 text-xs text-[var(--text-secondary)] font-mono">
                          {method === "newton" && "迭代格式: x_{k+1} = x_k - f(x_k) / f'(x_k)"}
                          {method === "bisection" && "迭代格式: c_k = (a_k + b_k) / 2"}
                          {method === "fixed_point" && "迭代格式: x_{k+1} = φ(x_k)"}
                        </div>
                      </div>

                      {/* 核心几何与参数快照 Pills */}
                      <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2 pt-4 border-t border-paper-200/60 dark:border-paper-800/60 font-mono text-xs">
                        <div className="p-2 rounded-lg bg-[var(--bg-card)] border border-paper-200 dark:border-paper-800 text-center">
                          <span className="block text-[10px] text-[var(--text-muted)]">探究闭区间</span>
                          <span className="font-semibold text-olive-800 dark:text-olive-200">[{left}, {right}]</span>
                        </div>
                        {method !== "bisection" && (
                          <div className="p-2 rounded-lg bg-[var(--bg-card)] border border-paper-200 dark:border-paper-800 text-center">
                            <span className="block text-[10px] text-[var(--text-muted)]">初始探针 x₀</span>
                            <span className="font-semibold text-olive-800 dark:text-olive-200">{initial}</span>
                          </div>
                        )}
                        <div className="p-2 rounded-lg bg-[var(--bg-card)] border border-paper-200 dark:border-paper-800 text-center">
                          <span className="block text-[10px] text-[var(--text-muted)]">容差阈值 ε</span>
                          <span className="font-semibold text-[var(--text-primary)]">{tolerance}</span>
                        </div>
                        <div className="p-2 rounded-lg bg-[var(--bg-card)] border border-paper-200 dark:border-paper-800 text-center">
                          <span className="block text-[10px] text-[var(--text-muted)]">步数上限</span>
                          <span className="font-semibold text-[var(--text-primary)]">{limit} 步</span>
                        </div>
                      </div>
                    </div>

                    {/* 科学探究三步法向导 */}
                    <div className="rounded-2xl border border-paper-300/80 dark:border-paper-700/80 bg-[var(--bg-card)] p-5">
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono mb-4 flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-olive-600" />
                        <span>苏格拉底探究三步法</span>
                      </h3>
                      <div className="grid sm:grid-cols-3 gap-3">
                        <div className="p-3.5 rounded-xl border border-paper-200/80 dark:border-paper-800/80 bg-[var(--bg-input)]/40">
                          <div className="font-mono text-xs font-bold text-olive-700 dark:text-olive-300 mb-1">
                            01 · 假说确立
                          </div>
                          <p className="text-xs leading-relaxed text-[var(--text-secondary)]">
                            在左侧选定初值与区间，写下对算法收敛或振荡的直觉判断。
                          </p>
                        </div>
                        <div className="p-3.5 rounded-xl border border-paper-200/80 dark:border-paper-800/80 bg-[var(--bg-input)]/40">
                          <div className="font-mono text-xs font-bold text-olive-700 dark:text-olive-300 mb-1">
                            02 · 轨迹回放
                          </div>
                          <p className="text-xs leading-relaxed text-[var(--text-secondary)]">
                            启动实验后，逐帧审视几何切线与误差衰减，验证局部收敛阶。
                          </p>
                        </div>
                        <div className="p-3.5 rounded-xl border border-paper-200/80 dark:border-paper-800/80 bg-[var(--bg-input)]/40">
                          <div className="font-mono text-xs font-bold text-olive-700 dark:text-olive-300 mb-1">
                            03 · 证伪对照
                          </div>
                          <p className="text-xs leading-relaxed text-[var(--text-secondary)]">
                            单变量更换初值或容差，同台叠图对照收敛轨迹与停止依据。
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* 一键起跑经典探针 */}
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono mb-3 flex items-center justify-between">
                        <span className="flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-ochre-600" />
                          <span>一键载入典型案题探针</span>
                        </span>
                        <span className="text-[10px] text-[var(--text-muted)]">点击载入参数与假说</span>
                      </div>
                      <div className="grid sm:grid-cols-3 gap-2.5">
                        <button
                          type="button"
                          onClick={() => preset("root", true)}
                          className="flex flex-col text-left p-3 rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-card)] hover:border-olive-500/50 hover:bg-olive-500/[0.04] transition-all cursor-pointer group"
                        >
                          <span className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-olive-700 dark:group-hover:text-olive-300 flex items-center justify-between">
                            <span>⚡ 逼近 √2</span>
                            <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                          </span>
                          <span className="text-[10px] text-[var(--text-muted)] mt-1">
                            感受牛顿法 4 步二次收敛神速
                          </span>
                        </button>
                        <button
                          type="button"
                          onClick={() => preset("cycle", true)}
                          className="flex flex-col text-left p-3 rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-card)] hover:border-cinnabar-500/50 hover:bg-cinnabar-500/[0.04] transition-all cursor-pointer group"
                        >
                          <span className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-cinnabar-700 dark:group-hover:text-cinnabar-300 flex items-center justify-between">
                            <span>🔄 拐点死循环</span>
                            <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                          </span>
                          <span className="text-[10px] text-[var(--text-muted)] mt-1">
                            体验在 0 与 1 之间的周期震荡
                          </span>
                        </button>
                        <button
                          type="button"
                          onClick={() => preset("bisect", true)}
                          className="flex flex-col text-left p-3 rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-card)] hover:border-dai-500/50 hover:bg-dai-500/[0.04] transition-all cursor-pointer group"
                        >
                          <span className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-dai-700 dark:group-hover:text-dai-300 flex items-center justify-between">
                            <span>✂️ 稳健二分</span>
                            <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                          </span>
                          <span className="text-[10px] text-[var(--text-muted)] mt-1">
                            介值定理保证下的单调收敛
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                </AtelierFolioCard>
              ) : (
                <AtelierFolioCard
                  title={
                    <div className="flex items-center gap-2">
                      <span className="font-title text-base sm:text-xl font-semibold">本次观察与数值推演</span>
                      <span className="font-mono text-xs px-2 py-0.5 rounded-md bg-olive-500/10 text-olive-800 dark:text-olive-200 border border-olive-500/25">
                        {run.parameters.method} · {run.rows.length} 步
                      </span>
                    </div>
                  }
                  badge={
                    run.diagnosis.complete
                      ? "收敛完成"
                      : run.diagnosis.status === "stalled"
                        ? "停滞/震荡"
                        : "达到上限步数"
                  }
                  badgeVariant={
                    run.diagnosis.complete
                      ? "olive"
                      : run.diagnosis.status === "stalled"
                        ? "cinnabar"
                        : "ochre"
                  }
                >
                  <div className="space-y-6">
                    {/* 算式与停止依据横幅 */}
                    <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-input)]/50 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-paper-200/60 dark:border-paper-800/60 pb-2 mb-3">
                        <span className="font-mono font-bold text-sm text-[var(--text-primary)]">
                          {run.parameters.method} · f(x) = {run.parameters.function}
                        </span>
                        <span className="font-mono text-xs text-[var(--text-secondary)]">
                          目标: {run.parameters.goal} · 容差: {run.parameters.tolerance}
                        </span>
                      </div>
                      <div className="grid sm:grid-cols-2 gap-3 text-xs">
                        <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-paper-200 dark:border-paper-800">
                          <span className="block text-[10px] text-[var(--text-muted)] font-semibold mb-0.5">
                            {run.prediction_timing === "after_preview" ? "预览后的观察" : "我的科学预测"}
                          </span>
                          <span className="text-[var(--text-primary)] leading-relaxed">{run.prediction}</span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-paper-200 dark:border-paper-800">
                          <span className="block text-[10px] text-[var(--text-muted)] font-semibold mb-0.5">
                            停止判据与诊断
                          </span>
                          <span className="text-[var(--text-primary)] leading-relaxed font-mono">
                            {run.stop_detail}
                          </span>
                          <p className="mt-1 text-[11px] text-[var(--text-secondary)]">
                            {run.diagnosis.summary}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* 几何切线播放器 */}
                    <LabPlayback
                      key={run.id}
                      run={run}
                      comparison={comparable ? compare : undefined}
                      onDiscussStep={
                        run.parameters.method === "newton"
                          ? (step) => {
                              discuss(run, step);
                              locate(`/lab?id=${encodeURIComponent(run.id)}&step=${step}`);
                            }
                          : undefined
                      }
                    />

                    {/* 实验反思卡 */}
                    <LabReflection key={`reflection-${run.id}`} runId={run.id} />

                    {/* 历史对照实验控制台 */}
                    <div className="rounded-xl border border-paper-200 dark:border-paper-800 bg-[var(--bg-card)] p-4">
                      <div className="flex items-center justify-between mb-2">
                        <label htmlFor="compare" className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] font-mono flex items-center gap-1.5">
                          <Compass className="w-3.5 h-3.5 text-olive-600" />
                          <span>选择历史实验横向对照</span>
                        </label>
                        <span className="text-[10px] text-[var(--text-muted)]">同题单变量验证</span>
                      </div>
                      <select
                        id="compare"
                        name="compare"
                        className={learningInput}
                        value={comparison}
                        onChange={(e) => setComparison(e.target.value)}
                      >
                        <option value="">不对照（单轨迹观察）</option>
                        {history
                          .filter((h) => h.id !== run.id)
                          .map((h) => (
                            <option key={h.id} value={h.id}>
                              {h.parameters.method} · {h.parameters.function} · x₀={h.parameters.initial_value ?? "中点"} · ({h.rows.length} 步)
                            </option>
                          ))}
                      </select>
                      {compare && (
                        <div className="mt-3 flex items-center justify-between">
                          <button
                            type="button"
                            className="text-xs text-olive-700 dark:text-olive-300 hover:underline font-medium cursor-pointer"
                            onClick={() => {
                              setRun(compare);
                              setSelectedStep(null);
                              setComparison("");
                              locate(`/lab?id=${encodeURIComponent(compare.id)}`);
                            }}
                          >
                            ← 回看这次历史实验 ({compare.rows.length} 步)
                          </button>
                          {comparable ? (
                            <span className="text-xs text-olive-700 dark:text-olive-300 font-medium">
                              ✓ 参数一致，已成功叠图对照
                            </span>
                          ) : (
                            <span className="text-xs text-ochre-700 dark:text-ochre-300">
                              函数、目标或阈值不同，暂不合并轨迹
                            </span>
                          )}
                        </div>
                      )}
                      {comparable && compare && (
                        <p className="mt-2 text-xs text-[var(--text-secondary)] leading-relaxed bg-olive-500/5 p-2 rounded-lg border border-olive-500/20">
                          对照结果：{compare.stop_detail}；历史记录 {compare.rows.length} 步，本次记录 {run.rows.length} 步。
                        </p>
                      )}
                    </div>

                    {/* 迭代轨迹数据表 (High Quality Atelier Table) */}
                    <div className="overflow-hidden rounded-xl border border-paper-300/80 dark:border-paper-700/80 shadow-2xs">
                      <div className="bg-[var(--bg-input)] px-4 py-2.5 border-b border-paper-200 dark:border-paper-800 flex items-center justify-between">
                        <span className="text-xs font-semibold text-[var(--text-primary)] font-mono">
                          ITERATION TRACE / 本次迭代数值轨迹
                        </span>
                        <span className="text-[10px] text-[var(--text-muted)] font-mono">
                          共 {run.rows.length} 步记录
                        </span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-right text-xs">
                          <thead className="bg-paper-100/70 dark:bg-paper-800/50 text-[var(--text-secondary)] border-b border-paper-200 dark:border-paper-800">
                            <tr>
                              {["k 步数", "xₖ 近似值", "f(xₖ) 残差", "相邻差 |xₖ - xₖ₋₁|", "搜索区间 [a, b]"].map((s) => (
                                <th
                                  key={s}
                                  scope="col"
                                  className="whitespace-nowrap px-3.5 py-2.5 font-medium"
                                >
                                  {s}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-paper-200/60 dark:divide-paper-800/60 font-mono">
                            {run.rows.map((row, idx) => (
                              <tr
                                key={row.k}
                                className={`transition-colors hover:bg-olive-500/5 ${
                                  idx % 2 === 1 ? "bg-paper-50/40 dark:bg-paper-900/20" : ""
                                }`}
                              >
                                <td className="p-3 text-[var(--text-muted)] font-bold">{row.k}</td>
                                <td className="p-3 text-[var(--text-primary)] font-semibold">
                                  {row.x.toPrecision(7)}
                                </td>
                                <td className="p-3 text-olive-700 dark:text-olive-300">
                                  {row.fx.toExponential(3)}
                                </td>
                                <td className="p-3 text-[var(--text-secondary)]">
                                  {row.step?.toExponential(3) ?? "—"}
                                </td>
                                <td className="whitespace-nowrap p-3 text-[var(--text-muted)]">
                                  {row.bracket
                                    ?.map((x) => x.toPrecision(5))
                                    .join(" ~ ") ?? "—"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* 底部导航提示与链接 */}
                    <div className="pt-2 flex flex-wrap items-center justify-between gap-3 text-xs border-t border-paper-200/60 dark:border-paper-800/60">
                      <p className="text-[var(--text-secondary)]">
                        这是系统生成的参考轨迹，会记录为研学帮助；不计为独立考核。
                      </p>
                      <div className="flex items-center gap-3">
                        {run.parameters.method === "newton" && !embedded && (
                          <Link
                            href={`/chat?lab=${encodeURIComponent(run.id)}`}
                            className="inline-flex items-center gap-1.5 text-olive-700 dark:text-olive-300 hover:underline font-semibold"
                          >
                            <Sparkles className="w-3.5 h-3.5" />
                            <span>带着这次实验问小珞 →</span>
                          </Link>
                        )}
                        <Link
                          href="/study"
                          className="text-[var(--text-secondary)] hover:text-olive-700 dark:hover:text-olive-300 hover:underline"
                        >
                          回到求根日课练习 →
                        </Link>
                      </div>
                    </div>
                  </div>
                </AtelierFolioCard>
              )}
            </section>
          </div>
          {!embedded &&
            activeTutorRun?.parameters.method === "newton" &&
            desktop && (
              <div className="sticky top-6 h-[min(760px,calc(100dvh-360px))] min-h-[480px]">
                <LabTutor
                  run={activeTutorRun}
                  selectedStep={selectedStep}
                  onSaved={saved}
                  onResetStep={() => setSelectedStep(null)}
                />
              </div>
            )}
        </div>
        {!embedded &&
          activeTutorRun?.parameters.method === "newton" &&
          !desktop && (
            <>
              <button
                type="button"
                onClick={() => setTutorOpen(true)}
                className="fixed bottom-5 right-5 z-40 flex min-h-14 items-center gap-2 rounded-full border border-olive-500/25 bg-olive-700 px-5 font-medium text-paper-50 shadow-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-olive-600"
              >
                <MessageCircle aria-hidden="true" className="size-5" />
                问小珞
              </button>
              {tutorOpen && (
                <MobileDrawer
                  title="小珞 · 实验伴学"
                  side="right"
                  breakpoint={1280}
                  onClose={() => setTutorOpen(false)}
                >
                  <LabTutor
                    run={activeTutorRun}
                    selectedStep={selectedStep}
                    onSaved={saved}
                    onResetStep={() => setSelectedStep(null)}
                  />
                </MobileDrawer>
              )}
            </>
          )}
      </div>
    </>
  );
  return embedded ? (
    <div className="min-w-0 p-4 sm:p-6" data-session-id={sessionId}>
      {content}
    </div>
  ) : (
    <LearningShell
      wide
      title="数值实验 · 动态探究"
      description="先留下猜想判断，再让迭代回答。更换初值或算法时，实时追踪步长衰减并核对收敛适用范围。"
    >
      <ExperimentNavigation active="root" />
      {content}
    </LearningShell>
  );
}
