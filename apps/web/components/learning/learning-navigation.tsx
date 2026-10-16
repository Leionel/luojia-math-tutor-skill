"use client";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {Home,MessageCircle,BookOpen,FlaskConical,NotebookPen} from "lucide-react";

export function LearningNavigation(){
  const path=usePathname();
  const items=[{href:"/",label:"学习中心",icon:Home},{href:"/chat",label:"自由对话",icon:MessageCircle},
    {href:"/reading",label:"材料伴读",icon:BookOpen},{href:"/lab",label:"数学实验",icon:FlaskConical},
    {href:"/records",label:"学习记录",icon:NotebookPen}];
  return <nav aria-label="主要学习导航" className="grid min-w-0 gap-1">
    {items.map(({href,label,icon:Icon})=>{const active=path===href||href==="/lab"&&path==="/numerical-lab";return <Link key={href} href={href} aria-current={active?"page":undefined} className={`inline-flex min-h-11 items-center gap-2 rounded-lg px-3 text-xs sm:text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-olive-600 ${active?"bg-olive-600/10 text-olive-800 dark:text-olive-200":"text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"}`}><Icon aria-hidden="true" className="size-4"/>{label}</Link>;})}
  </nav>;
}
