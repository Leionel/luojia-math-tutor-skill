"use client";

import React, { useCallback, useMemo, useEffect } from 'react';
import {
  ReactFlow,
  Controls,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  Node,
  Edge,
  ReactFlowInstance
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { layoutCourseNodes } from '@/lib/course-graph-layout';

export interface EvidencePackItem {
  id: string;
  concept_zh: string;
  prerequisite?: string[];
  status?: 'mastered' | 'learning' | 'locked' | 'unknown';
}

export interface KnowledgeGraphProps {
  items?: EvidencePackItem[];
  nodes?: Node[];
  edges?: Edge[];
  className?: string;
  courseId?: string;
  scopeFilter?: string;
  studentId?: string;
  onSelectNode?: (node: Node) => void;
  highlightNodeIds?: string[];
  selectedNodeId?: string;
}

const SCOPE_DOTS: Record<string, string> = {
  core: "bg-[var(--text-muted)]", prerequisite: "bg-dai-500", extension: "bg-ochre-500", unclassified: "bg-[var(--text-muted)]",
};

function SkillNode({ data }: { data: any }) {
  const active = data.isSelected || data.isHighlighted || data.isHovered;
  const size = Math.min(22, 10 + (data.degree || 0) * 2);
  return (
    <div className={`relative flex items-center justify-center w-12 h-12 cursor-pointer transition-opacity ${data.isDimmed ? "opacity-25" : "opacity-100"}`} title={data.label}>
      <Handle type="target" position={Position.Top} style={{ top: "50%", left: "50%", opacity: 0, border: 0 }} />
      <div style={{ width: size, height: size }} className={`rounded-full transition-colors ${active ? "bg-olive-500 ring-4 ring-olive-500/15" : SCOPE_DOTS[data.scope] || SCOPE_DOTS.unclassified}`} />
      <div className={`absolute top-10 left-1/2 -translate-x-1/2 w-36 text-center text-xs leading-4 ${active ? "text-[var(--text-primary)] font-medium" : "text-[var(--text-secondary)]"}`}>
        {String(data.label).replace(/\s*\([^)]*\)\s*$/, "")}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ top: "50%", left: "50%", opacity: 0, border: 0 }} />
    </div>
  );
}

export function KnowledgeGraph({
  items,
  nodes: propNodes,
  edges: propEdges,
  className,
  courseId = "numerical_analysis",
  scopeFilter,
  studentId,
  onSelectNode,
  highlightNodeIds = [],
  selectedNodeId
}: KnowledgeGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [loadError, setLoadError] = React.useState(false);
  const [hoveredId, setHoveredId] = React.useState<string | null>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const flowRef = React.useRef<ReactFlowInstance | null>(null);

  const layoutKey = nodes.map((node) => node.id).join("|");
  useEffect(() => {
    if (!layoutKey) return;
    const first = setTimeout(() => {
      flowRef.current?.fitView({ padding: 0.22, minZoom: 0.3, maxZoom: 1.2 });
    }, 200);
    const second = setTimeout(() => {
      flowRef.current?.fitView({ padding: 0.22, minZoom: 0.3, maxZoom: 1.2 });
    }, 900);
    return () => {
      clearTimeout(first);
      clearTimeout(second);
    };
  }, [layoutKey]);

  useEffect(() => {
    if (!containerRef.current) return;
    let timer: ReturnType<typeof setTimeout>;
    const observer = new ResizeObserver(() => {
      clearTimeout(timer);
      timer = setTimeout(() => flowRef.current?.fitView({ padding: 0.22, minZoom: 0.3, maxZoom: 1.2 }), 80);
    });
    observer.observe(containerRef.current);
    return () => { observer.disconnect(); clearTimeout(timer); };
  }, []);

  const highlightSet = useMemo(() => new Set(highlightNodeIds), [highlightNodeIds]);
  
  useEffect(() => {
    if (items && items.length > 0) {
      const layout = {
        nodes: items.map((item) => ({ id: item.id, type: "skillNode", position: { x: 0, y: 0 }, data: { label: item.concept_zh, status: item.status || "unknown" } })),
        edges: items.flatMap((item) => (item.prerequisite || []).map((source) => ({ id: `${source}-${item.id}`, source, target: item.id, label: "prerequisite_of" }))),
      };
      setNodes(layoutCourseNodes(layout.nodes, layout.edges));
      setEdges(layout.edges);
      return;
    }
    
    if (propNodes && propEdges) {
      setNodes(layoutCourseNodes(propNodes, propEdges));
      setEdges(propEdges);
      return;
    }

    // Canonical graph comes from the backend course pack; no local copy participates.
    if (courseId) {
      const controller = new AbortController();
      setIsLoading(true);
      setLoadError(false);
      const params = new URLSearchParams({ format: "react_flow" });
      if (scopeFilter) params.set("scope", scopeFilter);
      if (studentId) params.set("student_id", studentId);

      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      fetch(`${apiBase}/api/courses/${courseId}/graph?${params.toString()}`, { signal: controller.signal })
        .then((res) => {
          if (!res.ok) throw new Error("Graph fetch failed");
          return res.json();
        })
        .then((data) => {
          if (data.nodes) {
            if (controller.signal.aborted) return;
            setNodes(layoutCourseNodes(data.nodes, data.edges || []));
            setEdges(data.edges || []);
          }
        })
        .catch(() => {
          if (controller.signal.aborted) return;
          setLoadError(true);
          setNodes([]);
          setEdges([]);
        })
        .finally(() => {
          if (!controller.signal.aborted) setIsLoading(false);
        });
      return () => controller.abort();
    }
  }, [items, propNodes, propEdges, courseId, scopeFilter, studentId, setNodes, setEdges]);

  const nodeTypes = useMemo(() => ({ skillNode: SkillNode }), []);

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      onSelectNode?.(node);
    },
    [onSelectNode]
  );

  const focusId = hoveredId || selectedNodeId;
  const neighbors = new Set(focusId ? [focusId] : []);
  const degree = new Map<string, number>();
  edges.forEach((edge) => {
    degree.set(edge.source, (degree.get(edge.source) || 0) + 1);
    degree.set(edge.target, (degree.get(edge.target) || 0) + 1);
    if (edge.source === focusId) neighbors.add(edge.target);
    if (edge.target === focusId) neighbors.add(edge.source);
  });
  const displayNodes: Node[] = nodes.map((node) => ({ ...node, data: { ...node.data,
    degree: degree.get(node.id) || 0, isSelected: node.id === selectedNodeId,
    isHovered: node.id === hoveredId, isHighlighted: highlightSet.has(node.id),
    isDimmed: Boolean(focusId && !neighbors.has(node.id)),
  } }));
  const displayEdges: Edge[] = edges.map((edge) => {
    const active = edge.source === focusId || edge.target === focusId;
    return { ...edge, type: "straight", label: undefined, animated: false,
      style: { stroke: active ? "var(--accent)" : "var(--text-muted)", strokeWidth: active ? 1.5 : 0.8,
        opacity: focusId ? active ? 0.8 : 0.08 : 0.25 },
    };
  });

  return (
    <div ref={containerRef} className={`w-full h-full overflow-hidden bg-[var(--bg-primary)] relative ${className || ""}`}>
      {isLoading && <div className="absolute top-4 left-4 z-20 text-xs text-[var(--text-muted)]">正在载入课程关系…</div>}
      {loadError && <div className="absolute inset-0 z-20 grid place-items-center text-sm text-[var(--text-muted)]">课程图谱加载失败，请确认后端服务后刷新。</div>}
      {!isLoading && !loadError && !nodes.length && <div className="absolute inset-0 grid place-items-center text-sm text-[var(--text-muted)]">此范围暂无课程节点。</div>}
      <ReactFlow<Node, Edge>
        nodes={displayNodes} edges={displayEdges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        nodesConnectable={false} onNodeClick={handleNodeClick}
        onNodeMouseEnter={(_, node) => setHoveredId(node.id)}
        onNodeMouseLeave={() => setHoveredId(null)}
        nodeTypes={nodeTypes}
        onInit={(instance) => { flowRef.current = instance; instance.fitView({ padding: 0.22, minZoom: 0.3, maxZoom: 1.2 }); }}
        fitView fitViewOptions={{ padding: 0.22, minZoom: 0.3, maxZoom: 1.2 }}
        minZoom={0.3} maxZoom={2.5}
        proOptions={{ hideAttribution: true }}
      >
        <Controls showInteractive={false} className="!shadow-none !border !border-[var(--border-subtle)] !rounded-lg !overflow-hidden" />
      </ReactFlow>
      <div className="absolute bottom-5 right-5 pointer-events-none text-[11px] text-[var(--text-muted)]">关系数量决定圆点大小 · 拖动 / 缩放</div>
    </div>
  );
}
