"use client";

import React, { useCallback, useMemo, useEffect } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
  BackgroundVariant,
  Node,
  Edge
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CheckCircle2, Lock, Flame, Info } from 'lucide-react';
import { numericalAnalysisNodes, numericalAnalysisEdges } from '@/lib/numerical-analysis-graph';

const defaultNodes: Node[] = numericalAnalysisNodes;
const defaultEdges: Edge[] = numericalAnalysisEdges;

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
}

function generateGraphLayout(items: EvidencePackItem[]) {
  const levels = new Map<string, number>();
  
  items.forEach(item => levels.set(item.id, 0));
  
  for (let i = 0; i < items.length; i++) {
    let changed = false;
    items.forEach(item => {
      if (item.prerequisite && item.prerequisite.length > 0) {
        let maxPrereqLevel = -1;
        item.prerequisite.forEach(prereq => {
          if (levels.has(prereq)) {
            maxPrereqLevel = Math.max(maxPrereqLevel, levels.get(prereq)!);
          }
        });
        if (maxPrereqLevel !== -1 && levels.get(item.id)! <= maxPrereqLevel) {
          levels.set(item.id, maxPrereqLevel + 1);
          changed = true;
        }
      }
    });
    if (!changed) break;
  }

  const byLevel = new Map<number, EvidencePackItem[]>();
  items.forEach(item => {
    const lvl = levels.get(item.id) || 0;
    if (!byLevel.has(lvl)) {
      byLevel.set(lvl, []);
    }
    byLevel.get(lvl)!.push(item);
  });

  const newNodes: Node[] = [];
  const newEdges: Edge[] = [];

  const LEVEL_HEIGHT = 150;
  const NODE_WIDTH = 250;

  items.forEach(item => {
    const lvl = levels.get(item.id) || 0;
    const siblings = byLevel.get(lvl)!;
    const idx = siblings.findIndex(s => s.id === item.id);
    
    const totalWidth = siblings.length * NODE_WIDTH;
    const startX = -totalWidth / 2;
    
    newNodes.push({
      id: item.id,
      position: { x: startX + idx * NODE_WIDTH + NODE_WIDTH / 2, y: lvl * LEVEL_HEIGHT },
      data: { label: item.concept_zh, status: item.status || 'unknown' },
      type: 'skillNode'
    });

    if (item.prerequisite) {
      item.prerequisite.forEach(prereq => {
        newEdges.push({
          id: `e${prereq}-${item.id}`,
          source: prereq,
          target: item.id,
          animated: true,
          style: { stroke: '#9ca3af', strokeWidth: 2 }
        });
      });
    }
  });

  return { nodes: newNodes, edges: newEdges };
}

function SkillNode({ data }: { data: any }) {
  const isMastered = data.status === 'mastered';
  const isLearning = data.status === 'learning';
  const isLocked = data.status === 'locked';

  const scopeBadge = data.scope === 'core' ? '核心' :
                     data.scope === 'prerequisite' ? '前置' :
                     data.scope === 'extension' ? '拓展' : null;

  const typeBadge = data.unit_type === 'algorithm' ? '算法' :
                    data.unit_type === 'theorem' ? '定理' :
                    data.unit_type === 'definition' ? '定义' :
                    data.unit_type === 'counterexample' ? '反例' :
                    data.unit_type === 'misconception' ? '易错' : null;
  
  return (
    <div className={`px-4 py-2 shadow-lg rounded-2xl border-2 bg-white dark:bg-[#1e1e1b] flex flex-col gap-1 transition-all duration-300 min-w-[160px]
      ${isMastered ? 'border-emerald-500 shadow-emerald-500/20' : ''}
      ${isLearning ? 'border-blue-500 shadow-blue-500/20 ring-4 ring-blue-500/10' : ''}
      ${isLocked ? 'border-gray-300 dark:border-gray-700 opacity-60 grayscale' : ''}
      ${!isMastered && !isLearning && !isLocked ? 'border-purple-500 shadow-purple-500/20' : ''}
    `}>
      <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-[var(--border-subtle)]" />
      
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          {isMastered && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
          {isLearning && <Flame className="w-4 h-4 text-blue-500 animate-pulse" />}
          {isLocked && <Lock className="w-4 h-4 text-gray-400" />}
          {!isMastered && !isLearning && !isLocked && <Info className="w-4 h-4 text-purple-500" />}
          
          <span className={`font-semibold text-sm ${
            isMastered ? 'text-emerald-700 dark:text-emerald-400' : 
            isLearning ? 'text-blue-700 dark:text-blue-400' : 
            isLocked ? 'text-gray-500' : 
            'text-purple-700 dark:text-purple-400'
          }`}>
            {data.label}
          </span>
        </div>

        {scopeBadge && (
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${
            data.scope === 'core' ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300' :
            data.scope === 'prerequisite' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300' :
            'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300'
          }`}>
            {scopeBadge}
          </span>
        )}
      </div>

      {typeBadge && (
        <div className="flex items-center gap-1 text-[11px] text-gray-400">
          <span className="bg-gray-100 dark:bg-gray-800 px-1 rounded text-gray-500 dark:text-gray-400">
            {typeBadge}
          </span>
          {data.difficulty && (
            <span className="text-gray-400">难度★{data.difficulty}</span>
          )}
        </div>
      )}
      
      <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-[var(--border-subtle)]" />
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
  studentId
}: KnowledgeGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  
  useEffect(() => {
    if (items && items.length > 0) {
      const layout = generateGraphLayout(items);
      setNodes(layout.nodes);
      setEdges(layout.edges);
      return;
    }
    
    if (propNodes && propEdges) {
      setNodes(propNodes);
      setEdges(propEdges);
      return;
    }

    // Default to Numerical Analysis Root-Finding unit graph
    let baseNodes = [...defaultNodes];
    let baseEdges = [...defaultEdges];

    if (scopeFilter) {
      baseNodes = baseNodes.filter((n) => n.data?.scope === scopeFilter);
      const visibleIds = new Set(baseNodes.map((n) => n.id));
      baseEdges = baseEdges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target));
    }
    setNodes(baseNodes);
    setEdges(baseEdges);

    // Attempt live sync from backend API
    if (courseId) {
      setIsLoading(true);
      const params = new URLSearchParams({ format: "react_flow" });
      if (scopeFilter) params.set("scope", scopeFilter);
      if (studentId) params.set("student_id", studentId);

      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      fetch(`${apiBase}/api/courses/${courseId}/graph?${params.toString()}`)
        .then((res) => {
          if (!res.ok) throw new Error("Graph fetch failed");
          return res.json();
        })
        .then((data) => {
          if (data.nodes && data.nodes.length > 0) {
            setNodes(data.nodes);
            setEdges(data.edges || []);
          }
        })
        .catch(() => {
          // Gracefully keep the local numerical analysis graph
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [items, propNodes, propEdges, courseId, scopeFilter, studentId, setNodes, setEdges]);

  const nodeTypes = useMemo(() => ({ skillNode: SkillNode }), []);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className={`w-full h-[600px] border border-[var(--border-subtle)] rounded-[2rem] overflow-hidden bg-[#faf9f6] dark:bg-[#1a1a18] relative ${className || ''}`}>
      {isLoading && (
        <div className="absolute top-4 right-4 z-20 bg-white/80 dark:bg-black/80 px-3 py-1 rounded-full text-xs font-medium text-indigo-600 dark:text-indigo-400 shadow backdrop-blur">
          正在载入课程图谱...
        </div>
      )}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        className="dark:filter dark:invert-[.05]"
      >
        <Controls className="bg-white dark:bg-black border-[var(--border-subtle)] fill-[var(--text-primary)]" />
        <MiniMap 
          nodeColor={(n) => {
            if (n.data?.status === 'mastered') return '#10b981';
            if (n.data?.status === 'learning') return '#3b82f6';
            if (n.data?.status === 'locked') return '#4b5563';
            return '#a855f7'; // purple-500
          }}
          className="bg-white/50 dark:bg-black/50 border-[var(--border-subtle)]"
          maskColor="rgba(0,0,0,0.1)"
        />
        <Background variant={BackgroundVariant.Dots} gap={24} size={2} color="var(--border-primary)" />
      </ReactFlow>
    </div>
  );
}
