"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";

export interface RadarDataPoint {
  label: string;
  value: number; // 0–1
}

interface RadarChartProps {
  data: RadarDataPoint[];
  size?: number;
  className?: string;
}

/** Compute N-gon vertex positions given center, radius, and count */
function polygonVertices(
  cx: number,
  cy: number,
  r: number,
  n: number,
  offset = 0,
): { x: number; y: number }[] {
  return Array.from({ length: n }, (_, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2 + offset;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  });
}

/** Convert vertices array to SVG polygon points string */
function pointsString(pts: { x: number; y: number }[]) {
  return pts.map((p) => `${p.x},${p.y}`).join(" ");
}

export function RadarChart({ data, size = 220, className }: RadarChartProps) {
  const n = Math.max(3, data.length);
  const cx = size / 2;
  const cy = size / 2;
  const radius = size * 0.38;
  const labelRadius = radius * 1.22;

  // Grid rings (20%, 40%, 60%, 80%, 100%)
  const rings = useMemo(
    () =>
      [0.2, 0.4, 0.6, 0.8, 1.0].map((level) =>
        polygonVertices(cx, cy, radius * level, n),
      ),
    [cx, cy, radius, n],
  );

  // Axis lines from center to each vertex
  const axes = useMemo(
    () => polygonVertices(cx, cy, radius, n),
    [cx, cy, radius, n],
  );

  // Data polygon (value-scaled vertices)
  const dataPts = useMemo(
    () =>
      data.length >= 3
        ? polygonVertices(cx, cy, radius, data.length).map((pt, i) => ({
            x: cx + (pt.x - cx) * data[i].value,
            y: cy + (pt.y - cy) * data[i].value,
          }))
        : [],
    [cx, cy, radius, data],
  );

  // Label positions
  const labels = useMemo(
    () =>
      polygonVertices(cx, cy, labelRadius, n).map((pt, i) => ({
        ...pt,
        label: data[i]?.label ?? "",
      })),
    [cx, cy, labelRadius, data, n],
  );

  if (data.length < 3) {
    return (
      <div
        className={`flex items-center justify-center text-[11px] italic text-[var(--text-muted)] ${className ?? ""}`}
        style={{ width: size, height: size }}
      >
        至少 3 个维度才能显示雷达图
      </div>
    );
  }

  const gridStroke = "var(--border-subtle)";
  const accentColor = "var(--accent, #617a55)";

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={className}
      style={{ overflow: "visible" }}
    >
      {/* Background grid rings */}
      {rings.map((pts, ri) => (
        <polygon
          key={`ring-${ri}`}
          points={pointsString(pts)}
          fill="none"
          stroke={gridStroke}
          strokeWidth={ri === rings.length - 1 ? 1.2 : 0.7}
          strokeOpacity={ri === rings.length - 1 ? 0.5 : 0.3}
        />
      ))}

      {/* Axis lines */}
      {axes.map((pt, i) => (
        <line
          key={`axis-${i}`}
          x1={cx}
          y1={cy}
          x2={pt.x}
          y2={pt.y}
          stroke={gridStroke}
          strokeWidth={0.6}
          strokeOpacity={0.25}
        />
      ))}

      {/* Data area fill */}
      {dataPts.length >= 3 && (
        <motion.polygon
          points={pointsString(dataPts)}
          fill={accentColor}
          fillOpacity={0.18}
          stroke={accentColor}
          strokeWidth={2}
          strokeLinejoin="round"
          initial={{ scale: 0, transformOrigin: `${cx}px ${cy}px` }}
          animate={{ scale: 1, transformOrigin: `${cx}px ${cy}px` }}
          transition={{ type: "spring", stiffness: 120, damping: 20, mass: 0.8 }}
        />
      )}

      {/* Data vertex dots with glow */}
      {dataPts.map((pt, i) => (
        <g key={`dot-${i}`}>
          <motion.circle
            cx={pt.x}
            cy={pt.y}
            r={3.5}
            fill={accentColor}
            initial={{ r: 0, opacity: 0 }}
            animate={{ r: 3.5, opacity: 1 }}
            transition={{ delay: 0.15 * i, type: "spring", stiffness: 200 }}
          />
          {/* Glow ring */}
          <circle
            cx={pt.x}
            cy={pt.y}
            r={7}
            fill="none"
            stroke={accentColor}
            strokeWidth={1.5}
            strokeOpacity={0.35}
            filter="url(#radar-glow)"
          />
        </g>
      ))}

      {/* Glow filter */}
      <defs>
        <filter id="radar-glow">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Labels */}
      {labels.map((pt, i) => (
        <text
          key={`label-${i}`}
          x={pt.x}
          y={pt.y}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="var(--text-secondary)"
          fontSize={10}
          fontWeight={500}
          style={{ pointerEvents: "none" }}
        >
          {pt.label.length > 6 ? pt.label.slice(0, 5) + "…" : pt.label}
        </text>
      ))}
    </svg>
  );
}