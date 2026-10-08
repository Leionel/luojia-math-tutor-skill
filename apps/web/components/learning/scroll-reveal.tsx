"use client";
import {useEffect, useRef, useState, type ReactNode} from "react";

/** A single restrained entrance for below-fold results; content stays visible without JS. */
export function ScrollReveal({children,className=""}: {children:ReactNode;className?:string}) {
  const ref=useRef<HTMLDivElement>(null);
  const [enhanced,setEnhanced]=useState(false);
  const [seen,setSeen]=useState(false);
  useEffect(()=>{
    const node=ref.current;
    if(!node||typeof IntersectionObserver==="undefined"||window.matchMedia("(prefers-reduced-motion: reduce)").matches){setSeen(true);return;}
    if(node.getBoundingClientRect().top<window.innerHeight*.9){setSeen(true);return;}
    setEnhanced(true);
    const observer=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting)){setSeen(true);observer.disconnect();}},
      {rootMargin:"0px 0px -8% 0px",threshold:.08});
    observer.observe(node);
    return()=>observer.disconnect();
  },[]);
  return <div ref={ref} className={`${className} ${enhanced&&!seen?"opacity-0 translate-y-5":"opacity-100 translate-y-0"} motion-safe:transition-[opacity,transform] motion-safe:duration-700 motion-safe:ease-out`}>{children}</div>;
}
