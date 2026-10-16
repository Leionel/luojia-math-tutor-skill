"use client";
import Link from "next/link";
import {useEffect, useId, useRef, useState} from "react";
import {useReducedMotion} from "framer-motion";
import {ArrowUpRight, Pause, Play} from "lucide-react";
import styles from "./home-root-illustration.module.css";

// Real Newton geometry; this illustration is independent of student records.
const curve=Array.from({length:81},(_,i)=>{
  const x=i/40;
  return `${i===0?"M":"L"}${50+145*x},${130-35*(x*x-2)}`;
}).join(" ");

export function HomeRootIllustration(){
  const reduced=useReducedMotion();
  const [paused,setPaused]=useState(false);
  const [active,setActive]=useState(false);
  const ref=useRef<HTMLElement>(null);
  const id=useId().replace(/:/g, "");
  useEffect(()=>{
    const element=ref.current;
    if(!element)return;
    let visible=false;
    const sync=()=>setActive(visible && document.visibilityState==="visible");
    const observer=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;sync();});
    observer.observe(element);
    document.addEventListener("visibilitychange",sync);
    return()=>{observer.disconnect();document.removeEventListener("visibilitychange",sync);};
  },[]);
  const running=active && !paused && reduced===false;
  return <figure ref={ref} className={styles.stage} data-running={running} aria-label="Newton 迭代示意">
    <div aria-hidden="true" className={styles.aurora}/>
    <div aria-hidden="true" className={styles.halo}/>
    <div className={styles.content}>
    <div className={styles.caption}>
      <p className={styles.eyebrow}><span aria-hidden="true"/> THE SHAPE OF A SOLUTION</p>
      <h2>让每一次迭代，<br/><span>都有迹可循。</span></h2>
      <p className={styles.description}>改一个初值，看看下一步会落在哪里。再对照收敛条件，解释曲线里的变化。</p>
      <Link href="/lab" className={styles.link}>打开数值实验台 <ArrowUpRight size={18} aria-hidden="true"/></Link>
      <p className={styles.note}>Newton 示意 · f(x) = x² − 2<br/>1 → 1.5 → 1.4167… · 非用户提交轨迹</p>
    </div>
    <div className={styles.chart}>
      <div className={styles.chartHeader}><span>一次更新，为什么更近？</span><span className={styles.formula}>xₖ₊₁ = xₖ − f(xₖ) / f′(xₖ)</span></div>
      <svg viewBox="0 0 390 225" role="img" aria-label="Newton 迭代示意：在 x0 等于 1 处作切线，得到 x1 等于 1.5；随后得到 x2 约为 1.4167。示意图不代表用户提交轨迹。">
        <defs><linearGradient id={`${id}-curve`} x1="0" y1="1" x2="1" y2="0"><stop stopColor="#a8ba90"/><stop offset="1" stopColor="#faf7f2"/></linearGradient></defs>
        <g stroke="#faf7f2" strokeOpacity=".08" fill="none"><path d="M50 45H340 M50 87.5H340 M50 172.5H340 M50 215H340 M122.5 32V212 M195 32V212 M267.5 32V212 M340 32V212"/></g>
        <path d="M35 130 H363 M50 212 V32" fill="none" stroke="#faf7f2" strokeOpacity=".35"/>
        <path d={curve} fill="none" stroke="#a8ba90" strokeWidth="14" opacity=".12" className={styles.glow}/>
        <path d={curve} fill="none" stroke={`url(#${id}-curve)`} strokeWidth="2.5"/>
        <path d="M195 165 L267.5 130 L267.5 121.25 L255.4167 130" fill="none" stroke="#dd8b80" strokeWidth="1.5" strokeDasharray="5 4"/>
        <circle cx="195" cy="165" r="4" fill="#dd8b80"/><circle cx="267.5" cy="121.25" r="4" fill="#dd8b80"/>
        <g className={styles.pulse}><circle cx={50+145*Math.sqrt(2)} cy="130" r="12" fill="none" stroke="#a8ba90" strokeOpacity=".5"/></g>
        <circle cx={50+145*Math.sqrt(2)} cy="130" r="4" fill="#161d13" stroke="#faf7f2" strokeWidth="2"/>
        <g fill="#f2efe9" fontSize="12" fontFamily="ui-monospace, monospace"><text x="183" y="185">x₀ = 1</text><text x="276" y="110">x₁ = 1.5</text><text x="236" y="153">√2</text><text x="352" y="148">x</text></g>
      </svg>
      <div className={styles.chartFooter}><span><i aria-hidden="true"/>函数曲线</span><span><i aria-hidden="true"/>切线与下一步</span></div>
    </div>
    </div>
    {!reduced && <button type="button" className={styles.pause} onClick={()=>setPaused(value=>!value)} aria-pressed={paused} aria-label={paused?"播放背景动画":"暂停背景动画"}>{paused?<Play size={14} aria-hidden="true"/>:<Pause size={14} aria-hidden="true"/>}<span>{paused?"播放动画":"暂停动画"}</span></button>}
  </figure>;
}
