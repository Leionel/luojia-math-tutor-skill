"use client";

import { useEffect, useRef } from "react";

export function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = window.innerWidth;
    let height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;

    const handleResize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };
    window.addEventListener("resize", handleResize);

    // Torus points
    const points: { x: number, y: number, z: number, origX: number, origY: number, origZ: number }[] = [];
    const R = 200; // outer radius
    const r = 80;  // inner radius
    const segments = 40;
    const tubes = 20;

    for (let i = 0; i < segments; i++) {
      const theta = (i / segments) * 2 * Math.PI;
      for (let j = 0; j < tubes; j++) {
        const phi = (j / tubes) * 2 * Math.PI;
        
        const x = (R + r * Math.cos(phi)) * Math.cos(theta);
        const y = (R + r * Math.cos(phi)) * Math.sin(theta);
        const z = r * Math.sin(phi);
        
        points.push({ x, y, z, origX: x, origY: y, origZ: z });
      }
    }

    let mouseX = 0;
    let mouseY = 0;
    let isMouseOver = false;

    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX - width / 2;
      mouseY = e.clientY - height / 2;
    };
    const handleMouseEnter = () => isMouseOver = true;
    const handleMouseLeave = () => isMouseOver = false;

    window.addEventListener("mousemove", handleMouseMove);
    document.body.addEventListener("mouseenter", handleMouseEnter);
    document.body.addEventListener("mouseleave", handleMouseLeave);

    let angleX = 0;
    let angleY = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Base rotation
      angleX += 0.002;
      angleY += 0.003;

      // Add mouse interaction
      const targetAngleX = angleX + (isMouseOver ? mouseY * 0.005 : 0);
      const targetAngleY = angleY + (isMouseOver ? mouseX * 0.005 : 0);

      const cx = Math.cos(targetAngleX);
      const sx = Math.sin(targetAngleX);
      const cy = Math.cos(targetAngleY);
      const sy = Math.sin(targetAngleY);

      // Check dark mode for color
      const isDark = document.documentElement.classList.contains('dark');
      ctx.fillStyle = isDark ? "rgba(97, 122, 85, 0.4)" : "rgba(97, 122, 85, 0.2)";

      for (let i = 0; i < points.length; i++) {
        const p = points[i];
        
        // Rotate Y
        let x1 = p.origX * cy - p.origZ * sy;
        let z1 = p.origZ * cy + p.origX * sy;
        
        // Rotate X
        let y2 = p.origY * cx - z1 * sx;
        let z2 = z1 * cx + p.origY * sx;
        
        // Project
        const fov = 800;
        const scale = fov / (fov + z2 + 400); // offset Z
        
        const projX = x1 * scale + width / 2;
        const projY = y2 * scale + height / 2;

        const size = Math.max(0.5, 2.5 * scale);
        
        ctx.beginPath();
        ctx.arc(projX, projY, size, 0, Math.PI * 2);
        ctx.fill();
      }

      requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      document.body.removeEventListener("mouseenter", handleMouseEnter);
      document.body.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  return (
    <canvas 
      ref={canvasRef} 
      className="fixed inset-0 z-0 pointer-events-none opacity-40 mix-blend-multiply dark:mix-blend-lighten"
    />
  );
}
