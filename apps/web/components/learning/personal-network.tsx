"use client";
import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import {
  ReactFlow,
  Background,
  Controls,
  MarkerType,
  type Node,
  type Edge,
  type ReactFlowInstance,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { Exploration } from "@/lib/explorations";
import { chatReferenceHref } from "@/lib/learning-context";
import { learningRequest } from "@/lib/learning-api";
import {
  getCurrentUserId,
  getAuthHeaders,
  isAuthStorageKey,
} from "@/lib/demo-auth";
import { learningInput, learningButtonSecondary } from "./learning-shell";

const labels = {
  implies: "我猜可推出",
  supports: "我认为支持",
  challenges: "我认为质疑",
  related: "有关联",
  unknown: "待确认",
};
export function PersonalNetwork({
  record,
  spacious = false,
}: {
  record: Exploration;
  spacious?: boolean;
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = record.graph.nodes.find((n) => n.id === selectedId) ?? null;
  const flow = useRef<ReactFlowInstance | null>(null),
    canvas = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!canvas.current) return;
    const observer = new ResizeObserver(() =>
      flow.current?.fitView({ padding: 0.18, maxZoom: 1.15 }),
    );
    observer.observe(canvas.current);
    return () => observer.disconnect();
  }, [record.graph.nodes.length]);
  const nodes: Node[] = record.graph.nodes.map((n, i) => ({
    id: n.id,
    data: { label: n.label },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    position: { x: 80 + (i % 4) * 220, y: 50 + Math.floor(i / 4) * 160 },
    style: {
      background: "var(--bg-card)",
      color: "var(--text-primary)",
      border: "1px solid var(--border-primary)",
      width: 170,
      overflowWrap: "anywhere",
    },
  }));
  const edges:Edge[] = record.graph.edges.map((e) => ({
    ...e,
    label: labels[e.relation],
    type: "smoothstep",
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: "var(--text-secondary)" },
    labelStyle: { fill: "var(--text-primary)" },
    labelBgStyle: { fill: "var(--bg-card)" },
  }));
  const binding = selected ? record.source_bindings[selected.id] : null;
  const stale = record.reference_health.some((h) => h.node_id === selected?.id);
  return (
    <div className="min-w-0 space-y-3">
      <p className="text-xs leading-6">
        学生私人判断 ·
        每次探索独立保存。课程来源保留审核状态；计算证据只支持指定参数。
      </p>
      <div
        className={
          spacious && selected
            ? "grid min-w-0 gap-5 lg:grid-cols-[minmax(0,1fr)_320px]"
            : "min-w-0 space-y-3"
        }
      >
        {!nodes.length ? (
          <p className="py-5 text-sm">
            这次探索还没有私人节点。
            <Link
              href={`/explore?id=${encodeURIComponent(record.id)}`}
              className="underline"
            >
              添加自己的概念与关联
            </Link>
          </p>
        ) : (
          <div
            ref={canvas}
            aria-label="私人知识节点关系图"
            className={`${spacious ? "h-[62dvh] min-h-[380px] lg:min-h-[520px]" : "h-[360px]"} min-w-0 overflow-hidden rounded-xl border border-[var(--border-primary)]`}
          >
            <ReactFlow
              onInit={(instance) => {
                flow.current = instance;
              }}
              key={record.id + record.revision}
              nodes={nodes}
              edges={edges}
              fitView
              fitViewOptions={{ padding: 0.18, maxZoom: 1.15 }}
              nodesConnectable={false}
              nodesDraggable={false}
              onNodeClick={(_, n) => setSelectedId(n.id)}
            >
              <Background />
              <Controls showInteractive={false} />
            </ReactFlow>
          </div>
        )}
        {selected && (
          <aside
            aria-label="私人节点详情"
            className="space-y-2 rounded-lg border border-dai-600/30 p-4 text-sm leading-7"
          >
            <h3 className="font-semibold">{selected.label}</h3>
            <p>{selected.description || "尚未填写节点说明"}</p>
            <p>当前主张：{record.claim}</p>
            {record.graph.edges
              .filter(
                (e) => e.source === selected.id || e.target === selected.id,
              )
              .map((e) => (
                <p key={e.id}>
                  {record.graph.nodes.find((n) => n.id === e.source)?.label} →{" "}
                  {record.graph.nodes.find((n) => n.id === e.target)?.label} ·{" "}
                  {labels[e.relation]}：{e.reason}
                </p>
              ))}
            <p>
              绑定来源：
              {binding
                ? `${binding.title} · ${binding.review_state}`
                : "个人想法，尚未绑定来源"}
              {stale ? "（来源已变化，请回探索核对）" : ""}
            </p>
            {binding?.ref.kind === "reading" && (
              <Link
                className="mr-4 underline"
                href={`/reading?${binding.ref.section_id === null ? `unit=${encodeURIComponent(binding.ref.source_id)}` : `document=${encodeURIComponent(binding.ref.source_id)}&section=${encodeURIComponent(binding.ref.section_id)}`}`}
              >
                查看绑定原文
              </Link>
            )}
            {binding?.ref.kind === "course" && (
              <Link
                className="mr-4 underline"
                href={`/graph?view=course&unit=${encodeURIComponent(binding.ref.unit_id)}`}
              >
                查看课程来源
              </Link>
            )}
            {binding?.ref.kind === "note" && (
              <Link
                className="mr-4 underline"
                href={`/notebook?note=${encodeURIComponent(binding.ref.note_id)}`}
              >
                查看绑定笔记
              </Link>
            )}
            <Link
              className="mr-4 underline"
              href={`/explore?id=${encodeURIComponent(record.id)}`}
            >
              回探索编辑与查看计算
            </Link>
            <Link
              className="underline"
              href={chatReferenceHref({
                kind: "exploration",
                record_id: record.id,
                revision: record.revision,
              })}
            >
              结合这次探索讨论
            </Link>
          </aside>
        )}
      </div>
    </div>
  );
}

export function PersonalNetworkBrowser() {
  const [items, setItems] = useState<{ id: string; title: string }[]>([]),
    [id, setId] = useState(""),
    [record, setRecord] = useState<Exploration | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [epoch, setEpoch] = useState(0);
  useEffect(() => {
    const change = () => {
      setRecord(null);
      setItems([]);
      setId("");
      setEpoch((n) => n + 1);
    };
    const storage = (e: StorageEvent) => {
      if (isAuthStorageKey(e.key)) change();
    };
    window.addEventListener("luojia-auth-change", change);
    window.addEventListener("storage", storage);
    return () => {
      window.removeEventListener("luojia-auth-change", change);
      window.removeEventListener("storage", storage);
    };
  }, []);
  useEffect(() => {
    let live = true;
    const owner = getCurrentUserId(),
      credential = getAuthHeaders().Authorization;
    setLoading(true);
    setError("");
    learningRequest<{ items: typeof items }>("/explorations")
      .then((r) => {
        if (
          live &&
          owner === getCurrentUserId() &&
          credential === getAuthHeaders().Authorization
        ) {
          setItems(r.items);
          const requested = new URLSearchParams(window.location.search).get(
            "exploration",
          );
          setId(
            r.items.find((i) => i.id === requested)?.id ?? r.items[0]?.id ?? "",
          );
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [epoch]);
  useEffect(() => {
    if (!id) return;
    let live = true;
    setRecord(null);
    setLoading(true);
    setError("");
    learningRequest<Exploration>(`/explorations/${encodeURIComponent(id)}`)
      .then((r) => {
        if (live) setRecord(r);
      })
      .catch((e) => {
        if (live) setError(e.message);
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [id, epoch]);
  return (
    <section className="mx-auto w-full max-w-[1540px] min-w-0 space-y-5 px-4 py-6 sm:px-8 lg:px-10">
      <h1 className="font-serif text-3xl">我的知识网络</h1>
      <p className="text-sm leading-7">
        按探索回看自己的主张、关系与依据；不同探索中的同名概念不会自动合并。
      </p>
      <div className="flex flex-wrap gap-4">
        <Link href="/explore" className={learningButtonSecondary}>
          开始新的数学探索
        </Link>
        <Link className="min-h-11 py-3 underline" href="/records">
          学习记录
        </Link>
      </div>
      {!!items.length && (
        <label className="block text-sm">
          选择数学探索
          <select
            aria-label="选择数学探索"
            className={learningInput}
            value={id}
            onChange={(e) => {
              setId(e.target.value);
              window.history.replaceState(
                null,
                "",
                `/graph?view=personal&exploration=${encodeURIComponent(e.target.value)}`,
              );
            }}
          >
            {items.map((i) => (
              <option key={i.id} value={i.id}>
                {i.title}
              </option>
            ))}
          </select>
        </label>
      )}
      {loading && <p role="status">正在读取私人知识网络…</p>}
      {error && (
        <div role="alert">
          <p>{error}</p>
          <button
            className="min-h-11 underline"
            onClick={() => setEpoch((n) => n + 1)}
          >
            重新读取
          </button>
        </div>
      )}
      {!loading && !error && !items.length && (
        <p>还没有保存的探索。开始一个问题，逐步积累你的知识关系。</p>
      )}
      {record && <div className="flex min-w-0 flex-wrap items-center gap-4 rounded-xl border border-[var(--border-primary)] p-4 text-sm">
        <p className="w-full break-words">当前探索：{record.title} · 版本 {record.revision} · 私人判断，未经数学审核</p>
        <Link className="inline-flex min-h-11 items-center underline" href={`/explore?id=${encodeURIComponent(record.id)}&revision=${record.revision}`}>回到这次探索与历史</Link>
        <Link className="inline-flex min-h-11 items-center underline" href="/graph?view=course">查看课程知识网络（保留来源审核状态）</Link>
      </div>}
      {record && <PersonalNetwork key={record.id} record={record} spacious />}
    </section>
  );
}
