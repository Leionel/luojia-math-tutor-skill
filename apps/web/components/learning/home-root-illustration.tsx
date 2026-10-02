"use client";
import {motion, useReducedMotion} from "framer-motion";

// A mathematical illustration, never a fabricated student trajectory.
const curve=Array.from({length:81},(_,i)=>{
  const x=i/40;
  return `${i===0?"M":"L"}${50+145*x},${130-35*(x*x-2)}`;
}).join(" ");

export function HomeRootIllustration(){
  const reduced=useReducedMotion();
  return <figure className="mt-8 grid items-center gap-4 border-t border-[var(--border-primary)] pt-5 sm:grid-cols-[minmax(0,1fr)_320px] lg:grid-cols-[minmax(0,1fr)_390px]">
    <figcaption><p className="font-serif text-xl font-medium">一次更新，为什么更近？</p><p className="mt-3 max-w-[48ch] text-base sm:text-sm leading-7 text-[var(--text-secondary)]">切线给出下一步近似，收敛与停止还需要各自的条件。把观察和依据一起留下。</p><p className="mt-3 font-mono text-base sm:text-sm text-olive-700 dark:text-olive-300">f(x) = x² − 2</p><p className="mt-2 text-base sm:text-xs leading-6 text-[var(--text-muted)]">Newton 示意 · 1 → 1.5 → 1.4167…<br/>示意图不代表用户提交轨迹。</p></figcaption>
    <svg viewBox="0 0 390 225" role="img" aria-label="Newton 迭代示意：在 x0 等于 1 处作切线，得到 x1 等于 1.5；随后得到 x2 约为 1.4167。示意图不代表用户提交轨迹。" className="w-full text-olive-600 dark:text-olive-400">
      <path d="M35 130 H363 M50 212 V32" fill="none" stroke="var(--border-primary)"/>
      <path d="M50 200 H340" fill="none" stroke="var(--border-primary)" strokeDasharray="3 5"/>
      <motion.path d={curve} fill="none" stroke="currentColor" strokeWidth="2" initial={reduced?false:{pathLength:0}} animate={{pathLength:1}} transition={{duration:1.2,ease:"easeOut"}}/>
      <motion.path d="M195 165 L267.5 130 L267.5 121.25 L255.4167 130" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeDasharray="5 4" initial={reduced?false:{opacity:0}} animate={{opacity:1}} transition={{delay:reduced?0:0.5,duration:0.6}}/>
      <circle cx="195" cy="165" r="3.5" fill="currentColor"/><circle cx="267.5" cy="121.25" r="3.5" fill="currentColor"/>
      <circle cx={50+145*Math.sqrt(2)} cy="130" r="4" fill="var(--bg-primary)" stroke="currentColor" strokeWidth="2"/>
      <g fill="var(--text-muted)" fontSize="14" fontFamily="var(--font-mono, ui-monospace), monospace"><text x="183" y="185">x₀</text><text x="275" y="114">x₁</text><text x="237" y="153">√2</text><text x="352" y="148">x</text></g>
    </svg>
  </figure>;
}
