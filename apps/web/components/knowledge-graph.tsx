"use client";

import React, { useCallback, useMemo } from 'react';
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
  BackgroundVariant
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CheckCircle2, Lock, Flame } from 'lucide-react';

const initialNodes = [
  // Branch A: Calculus (Blue/Cyan)
  { id: '1', position: { x: 400, y: 50 }, data: { label: '函数与极限', status: 'mastered' }, type: 'skillNode' },
  { id: '2', position: { x: 250, y: 150 }, data: { label: '连续性', status: 'mastered' }, type: 'skillNode' },
  { id: '3', position: { x: 550, y: 150 }, data: { label: '无穷小比较', status: 'mastered' }, type: 'skillNode' },
  { id: '4', position: { x: 400, y: 250 }, data: { label: '导数与微分', status: 'learning' }, type: 'skillNode' },
  { id: '5', position: { x: 200, y: 350 }, data: { label: '微分中值定理', status: 'locked' }, type: 'skillNode' },
  { id: '6', position: { x: 400, y: 350 }, data: { label: '洛必达法则', status: 'locked' }, type: 'skillNode' },
  { id: '7', position: { x: 600, y: 350 }, data: { label: '泰勒公式', status: 'locked' }, type: 'skillNode' },
  { id: '8', position: { x: 400, y: 450 }, data: { label: '不定积分', status: 'locked' }, type: 'skillNode' },
  { id: '9', position: { x: 400, y: 550 }, data: { label: '定积分与应用', status: 'locked' }, type: 'skillNode' },
  { id: '10', position: { x: 250, y: 650 }, data: { label: '多元函数微分学', status: 'locked' }, type: 'skillNode' },
  { id: '11', position: { x: 550, y: 650 }, data: { label: '重积分', status: 'locked' }, type: 'skillNode' },
  { id: '12', position: { x: 400, y: 750 }, data: { label: '无穷级数', status: 'locked' }, type: 'skillNode' },

  // Branch B: Linear Algebra (Emerald/Green)
  { id: '13', position: { x: 900, y: 50 }, data: { label: '行列式', status: 'learning' }, type: 'skillNode' },
  { id: '14', position: { x: 900, y: 150 }, data: { label: '矩阵及其运算', status: 'locked' }, type: 'skillNode' },
  { id: '15', position: { x: 900, y: 250 }, data: { label: '线性方程组', status: 'locked' }, type: 'skillNode' },
  { id: '16', position: { x: 900, y: 350 }, data: { label: '向量空间', status: 'locked' }, type: 'skillNode' },
  { id: '17', position: { x: 750, y: 450 }, data: { label: '特征值与特征向量', status: 'locked' }, type: 'skillNode' },
  { id: '18', position: { x: 1050, y: 450 }, data: { label: '二次型', status: 'locked' }, type: 'skillNode' },

  // Branch C: Probability (Amber/Orange)
  { id: '19', position: { x: -100, y: 50 }, data: { label: '随机事件与概率', status: 'locked' }, type: 'skillNode' },
  { id: '20', position: { x: -100, y: 150 }, data: { label: '一维随机变量', status: 'locked' }, type: 'skillNode' },
  { id: '21', position: { x: -100, y: 250 }, data: { label: '多维随机变量', status: 'locked' }, type: 'skillNode' },
  { id: '22', position: { x: -250, y: 350 }, data: { label: '大数定律', status: 'locked' }, type: 'skillNode' },
  { id: '23', position: { x: 50, y: 350 }, data: { label: '中心极限定理', status: 'locked' }, type: 'skillNode' },
];

const initialEdges = [
  // Calculus Edges
  { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#10b981', strokeWidth: 2 } },
  { id: 'e1-3', source: '1', target: '3', animated: true, style: { stroke: '#10b981', strokeWidth: 2 } },
  { id: 'e2-4', source: '2', target: '4', animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 } },
  { id: 'e3-4', source: '3', target: '4', animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 } },
  { id: 'e4-5', source: '4', target: '5', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e4-6', source: '4', target: '6', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e4-7', source: '4', target: '7', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e5-8', source: '5', target: '8', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e6-8', source: '6', target: '8', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e7-8', source: '7', target: '8', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e8-9', source: '8', target: '9', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e9-10', source: '9', target: '10', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e9-11', source: '9', target: '11', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e10-12', source: '10', target: '12', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e11-12', source: '11', target: '12', style: { stroke: '#4b5563', strokeWidth: 1 } },

  // Linear Algebra Edges
  { id: 'e13-14', source: '13', target: '14', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e14-15', source: '14', target: '15', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e15-16', source: '15', target: '16', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e16-17', source: '16', target: '17', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e16-18', source: '16', target: '18', style: { stroke: '#4b5563', strokeWidth: 1 } },

  // Probability Edges
  { id: 'e19-20', source: '19', target: '20', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e20-21', source: '20', target: '21', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e21-22', source: '21', target: '22', style: { stroke: '#4b5563', strokeWidth: 1 } },
  { id: 'e21-23', source: '21', target: '23', style: { stroke: '#4b5563', strokeWidth: 1 } },
];

function SkillNode({ data }: { data: any }) {
  const isMastered = data.status === 'mastered';
  const isLearning = data.status === 'learning';
  
  return (
    <div className={`px-4 py-2 shadow-lg rounded-full border-2 bg-white dark:bg-[#1e1e1b] flex items-center gap-2 transition-all duration-500
      ${isMastered ? 'border-emerald-500 shadow-emerald-500/20' : ''}
      ${isLearning ? 'border-blue-500 shadow-blue-500/20 ring-4 ring-blue-500/10' : ''}
      ${!isMastered && !isLearning ? 'border-gray-300 dark:border-gray-700 opacity-60 grayscale' : ''}
    `}>
      <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-[var(--border-subtle)]" />
      
      {isMastered && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
      {isLearning && <Flame className="w-4 h-4 text-blue-500 animate-pulse" />}
      {!isMastered && !isLearning && <Lock className="w-4 h-4 text-gray-400" />}
      
      <span className={`font-semibold text-sm ${isMastered ? 'text-emerald-700 dark:text-emerald-400' : isLearning ? 'text-blue-700 dark:text-blue-400' : 'text-gray-500'}`}>
        {data.label}
      </span>
      
      <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-[var(--border-subtle)]" />
    </div>
  );
}

export function KnowledgeGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  const nodeTypes = useMemo(() => ({ skillNode: SkillNode }), []);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className="w-full h-[600px] border border-[var(--border-subtle)] rounded-[2rem] overflow-hidden bg-[#faf9f6] dark:bg-[#1a1a18]">
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
            return '#4b5563';
          }}
          className="bg-white/50 dark:bg-black/50 border-[var(--border-subtle)]"
          maskColor="rgba(0,0,0,0.1)"
        />
        <Background variant={BackgroundVariant.Dots} gap={24} size={2} color="var(--border-primary)" />
      </ReactFlow>
    </div>
  );
}
