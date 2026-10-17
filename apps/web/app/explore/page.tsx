"use client";
import Link from "next/link";
import {readChatEntry} from "@/lib/chat-entry";
import { useEffect, useRef, useState } from "react";
import {
  LearningShell,
  learningButton,
  learningButtonSecondary,
  learningInput,
} from "@/components/learning/learning-shell";
import {
  learningRequest,
  LearningRequestError,
  type ReadingDocument,
} from "@/lib/learning-api";
import {
  getCurrentUserId,
  getAuthHeaders,
  isAuthStorageKey,
} from "@/lib/demo-auth";
import { chatReferenceHref, readingSourceRef } from "@/lib/learning-context";
import {
  gsStatus,
  type Exploration,
  type PersonalGraph,
  type Source,
  type Run,
} from "@/lib/explorations";
import {ExplorationExperiment} from "@/components/learning/exploration-experiment";
import {RelationCandidates} from "@/components/learning/relation-candidates";
import {PersonalNetwork} from "@/components/learning/personal-network";

type Catalog = {
  course: { title: string; ref: Source }[];
  notes: { title: string; ref: Source }[];
  documents: { id: string; filename: string }[];
};
type Pending = { path: string; body: Record<string, unknown> };
type Draft = {
  title: string;
  claim: string;
  reason: string;
  graph: PersonalGraph;
  base: number;
};
const fresh = (): Draft => ({
  title: "我的数学探索",
  claim: "",
  reason: "",
  graph: { nodes: [], edges: [] },
  base: 0,
});
function savedDraft(saved: Exploration): Draft {
  const revision = [...saved.history]
    .reverse()
    .find((h) => h.action === "revise");
  return {
    ...fresh(),
    title: saved.title,
    claim: saved.claim,
    graph: saved.graph,
    base: saved.revision,
    reason: revision?.payload.reason || "",
  };
}
const relations = {
  implies: "我猜可推出",
  supports: "我认为支持",
  challenges: "我认为质疑",
  related: "有关联",
  unknown: "关系未知",
};
export default function ExplorePage() {
  const [identity, setIdentity] = useState(0);
  useEffect(() => {
    const changed = () => setIdentity((n) => n + 1);
    const storage = (e: StorageEvent) => {
      if (isAuthStorageKey(e.key)) changed();
    };
    window.addEventListener("luojia-auth-change", changed);
    window.addEventListener("storage", storage);
    return () => {
      window.removeEventListener("luojia-auth-change", changed);
      window.removeEventListener("storage", storage);
    };
  }, []);
  return <Explore key={identity} />;
}
function Explore() {
  const owner = getCurrentUserId(),
    credential = getAuthHeaders().Authorization;
  const [originSession,setOriginSession]=useState("");
  const [id, setId] = useState(""),
    [record, setRecord] = useState<Exploration | null>(null),
    [draft, setDraft] = useState<Draft>(fresh);
  const [items, setItems] = useState<
      { id: string; title: string; revision: number }[]
    >([]),
    [catalog, setCatalog] = useState<Catalog>({
      course: [],
      notes: [],
      documents: [],
    });
  const [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [storageError, setStorageError] = useState("");
  const [pending, setPending] = useState<Pending | null>(null),
    [ready, setReady] = useState(false);
  const [nodeLabel, setNodeLabel] = useState(""),
    [sourceChoice, setSourceChoice] = useState(""),
    [edgeSource, setEdgeSource] = useState(""),
    [edgeTarget, setEdgeTarget] = useState(""),
    [edgeReason, setEdgeReason] = useState(""),
    [edgeType, setEdgeType] = useState<keyof typeof relations>("unknown");
  const alive = useRef(true),
    epoch = useRef(0);
  const valid = () =>
    alive.current &&
    owner === getCurrentUserId() &&
    credential === getAuthHeaders().Authorization;
  const newScope=()=>{if(typeof window==="undefined")return "standalone";const params=new URLSearchParams(window.location.search);return params.get("draft")||params.get("session")||"standalone";};
  const key = (value: string) =>
    `luojia_exploration_draft_v1:${owner}:${value || `new:${newScope()}`}`;
  const draftStorageKey=key(id);
  function stored(value: string) {
    try {
      const cached = JSON.parse(localStorage.getItem(key(value)) || "null");
      const d = cached?.draft;
      const text = (v: unknown) => typeof v === "string";
      if (
        !d ||
        ![d.title, d.claim, d.reason].every(text) ||
        !Number.isInteger(d.base) ||
        d.base < 0
      ) return null;
      if (
        !Array.isArray(d.graph?.nodes) ||
        !Array.isArray(d.graph?.edges) ||
        !d.graph.nodes.every(
          (n: PersonalGraph["nodes"][number]) =>
            n && [n.id, n.label, n.description].every(text),
        ) ||
        !d.graph.edges.every(
          (e: PersonalGraph["edges"][number]) =>
            e &&
            [e.id, e.source, e.target, e.reason].every(text) &&
            e.relation in relations,
        )
      )
        return null;
      const p = cached.pending;
      const allowed = value
        ? new RegExp(
            `^/explorations/${value}/(claim|graph|restore-graph|runs|reject-relation)$`,
          )
        : /^\/explorations$/;
      return {
        draft: d as Draft,
        pending:
          p &&
          typeof p.path === "string" &&
          allowed.test(p.path) &&
          p.body &&
          typeof p.body === "object"
            ? (p as Pending)
            : null,
      };
    } catch {
      return null;
    }
  }
  function saveLocal(value: string, data: Draft, operation: Pending | null) {
    try {
      localStorage.setItem(
        key(value),
        JSON.stringify({ draft: data, pending: operation }),
      );
      setStorageError("");
    } catch {
      setStorageError(
        "浏览器无法保存草稿，刷新前请复制未提交的文字；服务端已保存记录不受影响。",
      );
    }
  }
  async function list() {
    const value = await learningRequest<{ items: typeof items }>(
      "/explorations",
    );
    if (valid()) setItems(value.items);
  }
  async function open(value: string) {
    const token = ++epoch.current;
    setReady(false);
    setLoading(true);
    setError("");
    setRecord(null);
    setPending(null);
    setId(value);
    try {
      const cached = stored(value);
      if (value) {
        const saved = await learningRequest<Exploration>(
          `/explorations/${encodeURIComponent(value)}`,
        );
        if (!valid() || token !== epoch.current) return;
        setRecord(saved);
        setDraft(cached?.draft ?? savedDraft(saved));
      } else {
        const entryId=new URLSearchParams(window.location.search).get("draft");
        const entry=entryId?readChatEntry(sessionStorage,owner,entryId):null;
        if(entryId&&!entry)throw Error("转交的问题草稿已过期或不属于当前账号，请回对话重新选择。");
        const session=new URLSearchParams(window.location.search).get("session");
        if(session){
          const seed=await learningRequest<{title:string;claim:string;origin_session_id:string}>(`/explorations/from-chat/${encodeURIComponent(session)}`);
          if(!valid()||token!==epoch.current)return;
          setOriginSession(seed.origin_session_id);setDraft(cached?.draft??{...fresh(),title:seed.title,claim:entry?.slice(0,2000)??seed.claim});
        }else {setOriginSession("");setDraft(cached?.draft??{...fresh(),claim:entry?.slice(0,2000)??""});}
      }
      if (valid() && token === epoch.current) {
        setPending(cached?.pending ?? null);
        setReady(true);
      }
    } catch (e) {
      if (valid() && token === epoch.current)
        setError(e instanceof Error ? e.message : "探索读取失败。");
    } finally {
      if (valid() && token === epoch.current) setLoading(false);
    }
  }
  useEffect(() => {
    alive.current = true;
    void open(new URLSearchParams(window.location.search).get("id") || "");
    void list().catch(() => {
      if (valid()) setError("探索目录暂不可读取；请重试，不代表没有保存记录。");
    });
    void learningRequest<Catalog>("/explorations/sources")
      .then((value) => {
        if (valid()) setCatalog(value);
      })
      .catch(() => {
        if (valid()) setError("来源目录暂不可读取；已有绑定保留，请稍后重试。");
      });
    return () => {
      alive.current = false;
    };
    // The owner wrapper remounts all state on authentication changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => {
    if (
      !ready ||
      !alive.current ||
      owner !== getCurrentUserId() ||
      credential !== getAuthHeaders().Authorization
    )
      return;
    try {
      localStorage.setItem(
        draftStorageKey,
        JSON.stringify({ draft, pending }),
      );
      setStorageError("");
    } catch {
      setStorageError(
        "浏览器无法保存草稿，刷新前请复制未提交的文字；服务端已保存记录不受影响。",
      );
    }
  }, [draft, pending, draftStorageKey, ready, owner, credential]);
  function change(value: Partial<Draft>) {
    setDraft((old) => ({ ...old, ...value }));
  }
  const conflict = !!record && draft.base !== record.revision;
  async function send(operation: Pending) {
    if (busy) return;
    setBusy(true);
    setError("");
    setPending(operation);
    saveLocal(id, draft, operation);
    try {
      const saved = await learningRequest<Exploration>(
        operation.path,
        operation.body,
      );
      if (!valid()) return;
      setRecord(saved);
      setId(saved.id);
      setDraft((old) => ({
        ...old,
        base: saved.revision,
        title: saved.title,
        ...(operation.path.endsWith("/restore-graph")
          ? { graph: saved.graph }
          : {}),
      }));
      setPending(null);
        saveLocal(
        saved.id,
        {
          ...draft,
          base: saved.revision,
          title: saved.title,
          ...(operation.path.endsWith("/restore-graph")
            ? { graph: saved.graph }
            : {}),
        },
        null,
      );
      if (operation.path === "/explorations")
        try {
          localStorage.removeItem(key(""));
        } catch {}
      window.history.replaceState(
        null,
        "",
        `/explore?id=${encodeURIComponent(saved.id)}`,
      );
      void list().catch(() => {});
    } catch (e) {
      if (valid()) {
        setError(e instanceof Error ? e.message : "请求未确认，草稿保留。");
        if (
          e instanceof LearningRequestError &&
          e.status >= 400 &&
          e.status < 500
        ) {
          setPending(null);
          saveLocal(id, draft, null);
        }
      }
    } finally {
      if (valid()) setBusy(false);
    }
  }
  function mutate(action: string, body: Record<string, unknown>) {
    if (!record || conflict || pending) return;
    void send({
      path: `/explorations/${encodeURIComponent(record.id)}/${action}`,
      body: {
        ...body,
        expected_revision: record.revision,
        request_id: crypto.randomUUID(),
      },
    });
  }
  async function addNode() {
    if (!nodeLabel.trim() || draft.graph.nodes.length >= 20) return;
    setError("");
    try {
      let ref: Source | null = null;
      if (sourceChoice.startsWith("course:"))
        ref = catalog.course[Number(sourceChoice.slice(7))].ref;
      if (sourceChoice.startsWith("note:"))
        ref = catalog.notes[Number(sourceChoice.slice(5))].ref;
      if (sourceChoice.startsWith("doc:")) {
        setBusy(true);
        const doc = await learningRequest<ReadingDocument>(
          `/reading/documents/${encodeURIComponent(sourceChoice.slice(4))}`,
        );
        if (!valid()) return;
        const section = doc.sections[0];
        if (!section) throw Error("原文不可读。");
        ref = readingSourceRef(doc, section.quote, section.id);
      }
      if (!valid()) return;
      change({
        graph: {
          ...draft.graph,
          nodes: [
            ...draft.graph.nodes,
            {
              id: crypto.randomUUID(),
              label: nodeLabel.trim(),
              description: "",
              source_ref: ref,
            },
          ],
        },
      });
      setNodeLabel("");
      setSourceChoice("");
    } catch (e) {
      if (valid())
        setError(e instanceof Error ? e.message : "来源核对失败，未添加节点。");
    } finally {
      if (valid()) setBusy(false);
    }
  }
  const disabled = busy || !!pending || conflict;
  const runs = record?.history.flatMap((h) => h.payload.runs || []) || [];
  return (
    <LearningShell
      title="数学探索"
      description="保存你的主张，编辑私人知识关联，用受控实验检查想法，再修订。私人关系与计算结果不会自动进入官方图谱或计为独立掌握。"
      wide
    >
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <Link href="/graph?view=personal" className="min-h-11 py-3 text-sm underline">我的知识网络</Link>
        <Link href="/records" className="min-h-11 py-3 text-sm underline">
          学习记录
        </Link>
        <label className="min-w-0 flex-1 text-sm">
          继续已保存探索
          <select
            aria-label="继续已保存探索"
            value={id}
            onChange={(e) => {
              const next = e.target.value;
              window.history.replaceState(
                null,
                "",
                next ? `/explore?id=${encodeURIComponent(next)}` : "/explore",
              );
              void open(next);
            }}
            className={`${learningInput} mt-1`}
            disabled={busy}
          >
            <option value="">新建探索</option>
            {items.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title} · 版本 {item.revision}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={() => void open(id)}
          disabled={busy}
          className={learningButtonSecondary}
        >
          重新读取已保存版本
        </button>
      </div>
      {error && (
        <p
          role="alert"
          className="mb-4 rounded-xl border border-cinnabar-600/30 p-4 text-sm leading-7"
        >
          {error}
        </p>
      )}
      {storageError && (
        <p role="status" className="mb-4 text-sm text-ochre-700">
          {storageError}
        </p>
      )}
      {pending && (
        <div
          role="status"
          className="mb-4 rounded-xl border border-ochre-600/30 p-4 text-sm leading-7"
        >
          <p>
            上次请求尚未确认，当前草稿保留。先重试原请求，或重新读取核对后再放弃。
          </p>
          <button
            type="button"
            className={`${learningButtonSecondary} mr-3`}
            disabled={busy}
            onClick={() => void send(pending)}
          >
            重试同一请求
          </button>
          <button
            type="button"
            className="min-h-11 underline"
            disabled={busy}
            onClick={() => setPending(null)}
          >
            已核对，放弃待确认请求
          </button>
        </div>
      )}
      {conflict && (
        <div className="mb-4 rounded-xl border border-ochre-600/30 p-4 text-sm leading-7">
          <p>
            草稿基于版本 {draft.base}，服务端当前为版本 {record?.revision}
            。请先对照下方过程记录；不会自动覆盖。
          </p>
          <button
            type="button"
            className="min-h-11 underline"
            onClick={() => change({ base: record!.revision })}
          >
            已核对，保留此草稿并以当前版本继续
          </button>
        </div>
      )}
      {loading ? (
        <p role="status">正在读取探索…</p>
      ) : (
        ready && (
          <>
            <section className="space-y-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-5">
              <h2 className="font-serif text-xl">
                {record ? "我的主张与修订" : "从你的主张开始"}
              </h2>
              {!record && (
                <label className="block text-sm">
                  探索名称
                  <input
                    aria-label="探索名称"
                    maxLength={160}
                    value={draft.title}
                    onChange={(e) => change({ title: e.target.value })}
                    className={`${learningInput} mt-1`}
                  />
                </label>
              )}
              <label className="block text-sm">
                我的数学主张
                <textarea
                  aria-label="我的数学主张"
                  value={draft.claim}
                  maxLength={2000}
                  onChange={(e) => change({ claim: e.target.value })}
                  rows={3}
                  placeholder="例如：第一行不严格对角占优，GS 就一定发散吗？请写下自己的判断与依据。"
                  className={`${learningInput} mt-1`}
                />
              </label>
              {record ? (
                <>
                  <label className="block text-sm">
                    修订理由
                    <textarea
                      aria-label="修订理由"
                      maxLength={2000}
                      value={draft.reason}
                      onChange={(e) => change({ reason: e.target.value })}
                      rows={2}
                      className={`${learningInput} mt-1`}
                      placeholder="指出哪次实验或哪条条件改变了你的想法。"
                    />
                  </label>
                  <button
                    type="button"
                    disabled={
                      disabled || !draft.claim.trim() || !draft.reason.trim()
                    }
                    className={learningButton}
                    onClick={() =>
                      mutate("claim", {
                        claim: draft.claim,
                        reason: draft.reason,
                      })
                    }
                  >
                    保存主张修订
                  </button>
                  <p className="text-xs text-[var(--text-muted)]">
                    当前版本 {record.revision} · 学生主张尚未数学审核 ·{" "}
                    {record.help_exposure
                      ? "已使用参考计算"
                      : "尚未运行参考计算"}
                  </p>
                </>
              ) : (
                <button
                  type="button"
                  disabled={
                    busy ||
                    !!pending ||
                    !draft.claim.trim() ||
                    !draft.title.trim()
                  }
                  className={learningButton}
                  onClick={() =>
                    void send({
                      path: "/explorations",
                      body: {
                        request_id: crypto.randomUUID(),
                        title: draft.title,
                        claim: draft.claim,
                        origin_session_id: originSession || null,
                      },
                    })
                  }
                >
                  保存并开始探索
                </button>
              )}
            </section>
            {record && (
              <>
                {!!record.reference_health.length && (
                  <p
                    role="status"
                    className="mt-5 rounded-xl border border-ochre-600/30 p-4 text-sm"
                  >
                    部分已绑定来源已删除或版本发生变化。历史定位保留；后续实验不会静默换用新版。请移除或重新选择相关引用后保存私人关系。
                  </p>
                )}
                <ExplorationExperiment key={record.id} record={record} disabled={disabled}
                  onSaved={saved=>{setRecord(saved);change({base:saved.revision});}}
                  onRun={body=>mutate("runs",body)}
                  onReject={()=>mutate("reject-relation",{reason:"学生拒绝本次候选关联"})}
                  onGraph={g=>{const ids=new Map(g.nodes.map(n=>[n.id,crypto.randomUUID()]));change({graph:{nodes:[...draft.graph.nodes,...g.nodes.map(n=>({...n,id:ids.get(n.id)!}))],edges:[...draft.graph.edges,...g.edges.map(e=>({...e,id:crypto.randomUUID(),source:ids.get(e.source)!,target:ids.get(e.target)!}))]}});}}/>
                <RelationCandidates record={record} disabled={disabled} onDecide={body=>mutate("relations/decision",body)}/>
                {!!runs.length && (
                <section aria-label="探索实验结果" className="mt-6 space-y-4">
                    <h2 className="font-serif text-xl">已保存的实验与证据</h2>
                    {runs.map((run, index) => (
                      <RunView
                        key={run.ref.record_id}
                        run={run}
                        record={record}
                        index={index}
                      />
                    ))}
                  </section>
                )}
                  <section className="mt-6 space-y-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-5">
                  <h2 className="font-serif text-xl">私人知识关联</h2>
                  <PersonalNetwork record={record}/>
                  <details><summary className="min-h-11 cursor-pointer py-3 text-sm font-semibold">编辑节点、来源与私人关系</summary>
                  <p className="text-xs leading-6 text-[var(--text-secondary)]">
                    节点与关系由你编辑；这里的“支持、质疑、推出”表示你的想法，均未经数学审核。可引用课程节点、个人笔记或资料首个章节。
                  </p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <label className="text-sm">
                      新节点名称
                      <input
                        aria-label="新节点名称"
                        maxLength={200}
                        value={nodeLabel}
                        onChange={(e) => setNodeLabel(e.target.value)}
                        className={`${learningInput} mt-1`}
                      />
                    </label>
                    <label className="text-sm">
                      新节点来源（可选）
                      <select
                        aria-label="新节点来源"
                        value={sourceChoice}
                        onChange={(e) => setSourceChoice(e.target.value)}
                        className={`${learningInput} mt-1`}
                      >
                        <option value="">我的个人想法，无已绑定来源</option>
                        <optgroup label="课程节点（保留审核状态）">
                          {catalog.course.map((c, i) => (
                            <option key={i} value={`course:${i}`}>
                              {c.title}
                            </option>
                          ))}
                        </optgroup>
                        <optgroup label="个人笔记">
                          {catalog.notes.map((n, i) => (
                            <option key={i} value={`note:${i}`}>
                              {n.title}
                            </option>
                          ))}
                        </optgroup>
                        <optgroup label="个人资料首章">
                          {catalog.documents.map((d) => (
                            <option key={d.id} value={`doc:${d.id}`}>
                              {d.filename}
                            </option>
                          ))}
                        </optgroup>
                      </select>
                    </label>
                  </div>
                  <button
                    type="button"
                    disabled={disabled || !nodeLabel.trim()}
                    className={learningButtonSecondary}
                    onClick={() => void addNode()}
                  >
                    添加私人节点
                  </button>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {draft.graph.nodes.map((node) => (
                      <article
                        key={node.id}
                        className="min-w-0 space-y-2 rounded-lg border border-[var(--border-primary)] p-3"
                      >
                        <input
                          aria-label={`节点名称 ${node.label}`}
                          maxLength={200}
                          value={node.label}
                          onChange={(e) =>
                            change({
                              graph: {
                                ...draft.graph,
                                nodes: draft.graph.nodes.map((n) =>
                                  n.id === node.id
                                    ? { ...n, label: e.target.value }
                                    : n,
                                ),
                              },
                            })
                          }
                          className={learningInput}
                        />
                        <textarea
                          aria-label={`节点说明 ${node.label}`}
                          maxLength={1000}
                          rows={2}
                          value={node.description}
                          placeholder="写下你对这个概念的理解"
                          onChange={(e) =>
                            change({
                              graph: {
                                ...draft.graph,
                                nodes: draft.graph.nodes.map((n) =>
                                  n.id === node.id
                                    ? { ...n, description: e.target.value }
                                    : n,
                                ),
                              },
                            })
                          }
                          className={learningInput}
                        />
                        <p className="text-xs">
                          {node.source_ref
                            ? `来源：${record.source_bindings[node.id]?.title || "待保存核对"} · 保存与运行时核对版本`
                            : "私人想法 · 未核验"}
                        </p>
                        <div className="flex gap-3 text-xs">
                          {node.source_ref && (
                            <button
                              type="button"
                              className="min-h-11 underline"
                              disabled={disabled}
                              onClick={() =>
                                change({
                                  graph: {
                                    ...draft.graph,
                                    nodes: draft.graph.nodes.map((n) =>
                                      n.id === node.id
                                        ? { ...n, source_ref: null }
                                        : n,
                                    ),
                                  },
                                })
                              }
                            >
                              移除来源绑定
                            </button>
                          )}
                          <button
                            type="button"
                            className="min-h-11 underline"
                            disabled={disabled}
                            onClick={() =>
                              change({
                                graph: {
                                  nodes: draft.graph.nodes.filter(
                                    (n) => n.id !== node.id,
                                  ),
                                  edges: draft.graph.edges.filter(
                                    (e) =>
                                      e.source !== node.id &&
                                      e.target !== node.id,
                                  ),
                                },
                              })
                            }
                          >
                            删除私人节点
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                  {draft.graph.nodes.length >= 2 && (
                    <div className="space-y-3 border-t border-[var(--border-primary)] pt-4">
                      <div className="grid gap-3 sm:grid-cols-3">
                        <label className="text-sm">
                          关系起点
                          <select
                            aria-label="关系起点"
                            value={edgeSource}
                            onChange={(e) => setEdgeSource(e.target.value)}
                            className={`${learningInput} mt-1`}
                          >
                            <option value="">选择节点</option>
                            {draft.graph.nodes.map((n) => (
                              <option key={n.id} value={n.id}>
                                {n.label}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="text-sm">
                          我的关系判断
                          <select
                            aria-label="我的关系判断"
                            value={edgeType}
                            onChange={(e) =>
                              setEdgeType(
                                e.target.value as keyof typeof relations,
                              )
                            }
                            className={`${learningInput} mt-1`}
                          >
                            {Object.entries(relations).map(([key, label]) => (
                              <option key={key} value={key}>
                                {label}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="text-sm">
                          关系终点
                          <select
                            aria-label="关系终点"
                            value={edgeTarget}
                            onChange={(e) => setEdgeTarget(e.target.value)}
                            className={`${learningInput} mt-1`}
                          >
                            <option value="">选择节点</option>
                            {draft.graph.nodes.map((n) => (
                              <option key={n.id} value={n.id}>
                                {n.label}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                      <label className="block text-sm">
                        这条关联的理由
                        <input
                          aria-label="关联理由"
                          maxLength={1000}
                          value={edgeReason}
                          onChange={(e) => setEdgeReason(e.target.value)}
                          className={`${learningInput} mt-1`}
                        />
                      </label>
                      <button
                        type="button"
                        disabled={
                          disabled ||
                          !edgeSource ||
                          !edgeTarget ||
                          edgeSource === edgeTarget ||
                          !edgeReason.trim() ||
                          draft.graph.edges.length >= 30
                        }
                        className={learningButtonSecondary}
                        onClick={() => {
                          change({
                            graph: {
                              ...draft.graph,
                              edges: [
                                ...draft.graph.edges,
                                {
                                  id: crypto.randomUUID(),
                                  source: edgeSource,
                                  target: edgeTarget,
                                  relation: edgeType,
                                  reason: edgeReason,
                                },
                              ],
                            },
                          });
                          setEdgeReason("");
                        }}
                      >
                        添加私人关系
                      </button>
                    </div>
                  )}
                  <ul className="space-y-2">
                    {draft.graph.edges.map((edge) => (
                      <li
                        key={edge.id}
                        className="rounded-lg border-l-2 border-olive-600 bg-olive-600/5 p-3 text-sm leading-7"
                      >
                        <p>
                          {
                            draft.graph.nodes.find((n) => n.id === edge.source)
                              ?.label
                          }{" "}
                          → {relations[edge.relation]} →{" "}
                          {
                            draft.graph.nodes.find((n) => n.id === edge.target)
                              ?.label
                          }
                        </p>
                        <select
                          aria-label="修改关系类型"
                          value={edge.relation}
                          onChange={(e) =>
                            change({
                              graph: {
                                ...draft.graph,
                                edges: draft.graph.edges.map((x) =>
                                  x.id === edge.id
                                    ? {
                                        ...x,
                                        relation: e.target
                                          .value as keyof typeof relations,
                                      }
                                    : x,
                                ),
                              },
                            })
                          }
                          className={`${learningInput} mt-2`}
                        >
                          {Object.entries(relations).map(([key, label]) => (
                            <option key={key} value={key}>
                              {label}
                            </option>
                          ))}
                        </select>
                        <input
                          aria-label="修改关系理由"
                          maxLength={1000}
                          value={edge.reason}
                          onChange={(e) =>
                            change({
                              graph: {
                                ...draft.graph,
                                edges: draft.graph.edges.map((x) =>
                                  x.id === edge.id
                                    ? { ...x, reason: e.target.value }
                                    : x,
                                ),
                              },
                            })
                          }
                          className={`${learningInput} mt-2`}
                        />
                        <button
                          type="button"
                          className="min-h-11 text-xs underline"
                          disabled={disabled}
                          onClick={() =>
                            change({
                              graph: {
                                ...draft.graph,
                                edges: draft.graph.edges.filter(
                                  (x) => x.id !== edge.id,
                                ),
                              },
                            })
                          }
                        >
                          撤销这条私人关系
                        </button>
                      </li>
                    ))}
                  </ul>
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => mutate("graph", { graph: draft.graph })}
                    className={learningButton}
                  >
                    保存私人关联
                  </button>
                  </details>
                </section>
                <section className="mt-6 space-y-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-5">
                  <h2 className="font-serif text-xl">
                    探索过程 · 版本 {record.revision}
                  </h2>
                  <p className="text-xs leading-6 text-[var(--text-secondary)]">
                    主张、私人图和实验按版本保存。恢复私人图只恢复节点关系，不撤销主张与实验历史。
                  </p>
                  {record.linked_chats.map((chat) => (
                    <Link
                      key={chat.id}
                      href={`/chat?session=${encodeURIComponent(chat.id)}`}
                      className="block min-h-11 py-3 text-sm underline"
                    >
                      继续关联对话：{chat.title}
                    </Link>
                  ))}
                  {[...record.history].reverse().map((h) => (
                    <details
                      key={h.revision}
                      className="rounded-lg border border-[var(--border-primary)] p-3"
                    >
                      <summary className="min-h-11 cursor-pointer py-3 text-sm">
                        版本 {h.revision} ·{" "}
                        {(
                          {
                            created: "创建探索",
                            graph: "保存私人关系",
                            restore_graph: "恢复私人图",
                            revise: "修订主张",
                            run: "确认参考实验",
                            advice: "保存助教建议（尚未执行）",
                            reject_relation: "拒绝候选关联",
                          } as Record<string, string>
                        )[h.action] || "保存记录"}{" "}
                        · {new Date(h.at).toLocaleString("zh-CN")}
                      </summary>
                      <p className="whitespace-pre-wrap text-sm leading-7">
                        当时的主张：{h.claim}
                      </p>
                      {h.payload.reason && (
                        <p className="mt-2 text-sm">
                          修订理由：{h.payload.reason}
                        </p>
                      )}
                      {h.payload.prediction && (
                        <p className="mt-2 text-sm">
                          运行前预测：{h.payload.prediction}
                        </p>
                      )}
                      <p className="mt-2 text-xs">
                        私人节点 {h.graph.nodes.length} · 关系{" "}
                        {h.graph.edges.length} · 未审核
                      </p>
                      <button
                        type="button"
                        disabled={disabled}
                        className="mt-2 min-h-11 text-xs underline"
                        onClick={() =>
                          mutate("restore-graph", {
                            target_revision: h.revision,
                          })
                        }
                      >
                        恢复此版本的私人图
                      </button>
                    </details>
                  ))}
                </section>
              </>
            )}
          </>
        )
      )}
    </LearningShell>
  );
}
function RunView({ run, index,record }: { run: Run; index: number;record:Exploration }) {
  const evidence = run.matrix_evidence;
  return (
    <article className="min-w-0 space-y-3 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-5">
      <h3 className="font-serif text-lg">
        实验 {index + 1} · {(run.task.domain==="root_finding"?run.stop_detail:gsStatus(run.status))}
      </h3>
      <p className="text-xs leading-6">
        受控浮点计算 · 观察当前参数与初值的有限轨迹；不计独立掌握。
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr>
              <th className="p-2">步数</th>
              <th className="p-2">{run.task.domain==="root_finding"?"迭代值 x":"向量"}</th>
              <th className="p-2">残差</th>
              <th className="p-2">相邻步变化</th>
            </tr>
          </thead>
          <tbody>
            {run.rows.slice(-8).map((row) => (
              <tr
                key={row.k}
                className="border-t border-[var(--border-primary)]"
              >
                <td className="p-2">{row.k}</td>
                <td className="p-2 font-mono">
                  {row.x!==undefined?row.x.toPrecision(6):row.vector?.map((x) => x.toPrecision(5)).join(", ")}
                </td>
                <td className="p-2">{(row.fx??row.residual)?.toExponential(3)}</td>
                <td className="p-2">{row.step?.toExponential(3) ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {evidence?.status === "deterministic_calculation" ? (
        <div className="space-y-2 border-l-2 border-dai-600 pl-3 text-sm leading-7">
          <h4 className="font-semibold">针对这个矩阵的有理数计算</h4>
          <p>
            严格行对角占优：{evidence.strict_row_dominant ? "是" : "否"}
            ；误差迭代矩阵谱半径：{evidence.spectral_radius_exact}，
            {evidence.rho_less_than_one ? "小于 1" : "不小于 1"}。
          </p>
          {evidence.is_counterexample_to_necessity && (
            <p>
              这个矩阵不满足严格行对角占优，但其 GS 误差迭代矩阵谱半径小于
              1。它可用于反驳“非严格行对角占优就必定发散”；不能据此推广为所有这类矩阵都收敛。
            </p>
          )}
          <p className="text-xs">{evidence.statement_scope}</p>
        </div>
      ) : (
        <p className="text-sm">{run.next_question??evidence?.reason}</p>
      )}
      <details className="text-xs">
        <summary className="min-h-11 cursor-pointer py-3">
          参数与来源详情
        </summary>
        <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-all">
          {JSON.stringify(
            {
              task: run.task,
              source: run.ref,
              iteration_matrix: evidence?.iteration_matrix,
            },
            null,
            2,
          )}
        </pre>
      </details>
      <div className="flex flex-wrap gap-4 text-sm">
        <Link
          className="min-h-11 py-3 text-olive-700 dark:text-olive-300 underline"
          href={`${chatReferenceHref({kind:"exploration",record_id:record.id,revision:record.revision,selected_run_id:run.ref.record_id})}${record.origin_session_id?`&session=${encodeURIComponent(record.origin_session_id)}`:""}`}
        >
          围绕这次已保存计算讨论
        </Link>
        <Link
          className="min-h-11 py-3 underline"
          href={`/${run.ref.kind==="root_lab"?"lab":"numerical-lab"}?id=${encodeURIComponent(run.ref.record_id)}`}
        >
          查看原始数值记录
        </Link>
      </div>
    </article>
  );
}
