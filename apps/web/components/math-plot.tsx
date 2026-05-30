"use client";

import React, { useMemo } from "react";

interface MathPlotProps {
  function: string;
  domain?: string; // "-10,10"
}

export function MathPlot({ function: fn, domain = "-10,10" }: MathPlotProps) {
  const [minX, maxX] = domain.split(",").map(Number);
  
  const width = 400;
  const height = 300;
  const padding = 40;
  
  // Calculate points
  const points = useMemo(() => {
    try {
      const step = (maxX - minX) / 100;
      const pts: { x: number; y: number }[] = [];
      
      // Simple sanitize and map math functions
      const safeFn = fn
        .replace(/sin/g, 'Math.sin')
        .replace(/cos/g, 'Math.cos')
        .replace(/tan/g, 'Math.tan')
        .replace(/exp/g, 'Math.exp')
        .replace(/log/g, 'Math.log')
        .replace(/sqrt/g, 'Math.sqrt')
        .replace(/abs/g, 'Math.abs')
        .replace(/pi/g, 'Math.PI')
        .replace(/\^/g, '**');

      // Evaluator
      const evaluator = new Function("x", `return ${safeFn};`);
      
      let minY = Infinity;
      let maxY = -Infinity;

      for (let x = minX; x <= maxX; x += step) {
        const y = evaluator(x);
        if (Number.isFinite(y)) {
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
          pts.push({ x, y });
        }
      }

      // Add padding to Y range to avoid clipping
      const yRange = maxY === minY ? 1 : maxY - minY;
      minY -= yRange * 0.1;
      maxY += yRange * 0.1;

      return { pts, minY, maxY };
    } catch (e) {
      console.error("Failed to parse plot function:", fn, e);
      return null;
    }
  }, [fn, minX, maxX]);

  if (!points) return <div className="p-4 bg-red-50 text-red-500 rounded border border-red-200">无法渲染函数图像: {fn}</div>;

  const { pts, minY, maxY } = points;
  
  // Transform domain to SVG coordinates
  const scaleX = (x: number) => padding + ((x - minX) / (maxX - minX)) * (width - 2 * padding);
  const scaleY = (y: number) => height - padding - ((y - minY) / (maxY - minY)) * (height - 2 * padding);

  const originX = minX <= 0 && maxX >= 0 ? scaleX(0) : scaleX(minX);
  const originY = minY <= 0 && maxY >= 0 ? scaleY(0) : scaleY(minY);

  const pathD = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(p.x)} ${scaleY(p.y)}`).join(" ");

  return (
    <div className="my-4 rounded-xl overflow-hidden border border-[#d6d0ba] dark:border-[#3e3f36] bg-[#faf7f2]/80 dark:bg-[#1e1e1b]/80 shadow-md p-4 w-fit flex flex-col items-center">
      <div className="mb-2 text-sm font-title text-[#617a55] border-b border-[#d6d0ba] dark:border-[#3e3f36] pb-2 w-full text-center">
        函数图像: f(x) = {fn}
      </div>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="font-body text-xs text-[#757a6b]">
        {/* Grid X */}
        {Array.from({ length: 11 }).map((_, i) => {
          const x = minX + (maxX - minX) * (i / 10);
          return (
            <g key={`gx-${i}`}>
              <line x1={scaleX(x)} y1={padding} x2={scaleX(x)} y2={height - padding} stroke="currentColor" strokeOpacity={0.1} />
              <text x={scaleX(x)} y={height - padding + 15} textAnchor="middle" fill="currentColor">{Math.round(x * 10) / 10}</text>
            </g>
          );
        })}
        
        {/* Grid Y */}
        {Array.from({ length: 5 }).map((_, i) => {
          const y = minY + (maxY - minY) * (i / 4);
          return (
            <g key={`gy-${i}`}>
              <line x1={padding} y1={scaleY(y)} x2={width - padding} y2={scaleY(y)} stroke="currentColor" strokeOpacity={0.1} />
              <text x={padding - 10} y={scaleY(y) + 4} textAnchor="end" fill="currentColor">{Math.round(y * 10) / 10}</text>
            </g>
          );
        })}

        {/* Axes */}
        <line x1={padding} y1={originY} x2={width - padding} y2={originY} stroke="currentColor" strokeWidth={1} />
        <line x1={originX} y1={padding} x2={originX} y2={height - padding} stroke="currentColor" strokeWidth={1} />

        {/* Function Curve */}
        <path d={pathD} fill="none" stroke="#617a55" strokeWidth={2} className="drop-shadow-sm" />
      </svg>
    </div>
  );
}
