import type {LabRun} from "@/lib/learning-api";

const f=(x:number)=>x*x*x-2*x+2;
const derivative=(x:number)=>3*x*x-2;
const px=(x:number)=>48+(x+1.25)/3*544;
const py=(y:number)=>228-(y+2)/5.5*200;

/** This fixed activity plots only the transition whose landing row is already visible. */
export function NewtonTangentView({rows}:{rows:LabRun["rows"]}){
  const landing=rows.at(-1),start=rows.length>1?rows.at(-2):null;
  const samples=Array.from({length:91},(_,i)=>-1.25+i*3/90);
  const curve=samples.map((x,i)=>`${i?"L":"M"}${px(x).toFixed(2)} ${py(f(x)).toFixed(2)}`).join(" ");
  const tangent=start&&landing?{x:start.x,y:start.fx,landing:landing.x,slope:derivative(start.x)}:null;
  const left=tangent?Math.max(-1.25,Math.min(tangent.x,tangent.landing)-0.15):0;
  const right=tangent?Math.min(1.75,Math.max(tangent.x,tangent.landing)+0.15):0;
  const line=tangent?`M${px(left)} ${py(tangent.y+tangent.slope*(left-tangent.x))} L${px(right)} ${py(tangent.y+tangent.slope*(right-tangent.x))}`:"";
  return <figure className="mt-5 rounded-xl border border-olive-500/20 bg-[var(--bg-tertiary)] p-4">
    <svg viewBox="0 0 640 250" role="img" aria-label={tangent?`已揭示第 ${landing!.k} 步：在 x=${start!.x} 处的切线与横轴交于 x=${landing!.x}`:"当前仅显示初值；尚未揭示切线"} className="w-full">
      <path d={`M${px(-1.25)} ${py(0)} H${px(1.75)} M${px(0)} ${py(-2)} V${py(3.5)}`} fill="none" stroke="currentColor" opacity=".35"/>
      <path d={curve} fill="none" stroke="currentColor" strokeWidth="2.5" className="text-olive-700 dark:text-olive-300"/>
      {tangent&&<><path d={line} fill="none" stroke="currentColor" strokeWidth="2.5" className="text-cinnabar-600 dark:text-cinnabar-300"/>
        <circle cx={px(tangent.x)} cy={py(tangent.y)} r="5" fill="currentColor" className="text-cinnabar-600 dark:text-cinnabar-300"/>
        <circle cx={px(tangent.landing)} cy={py(0)} r="5" fill="currentColor" className="text-cinnabar-600 dark:text-cinnabar-300"/>
        <text x={px(tangent.landing)+8} y={py(0)-8} fill="currentColor" fontSize="13">x{landing!.k} = {landing!.x}</text></>}
      {!tangent&&landing&&<circle cx={px(landing.x)} cy={py(landing.fx)} r="5" fill="currentColor" className="text-cinnabar-600 dark:text-cinnabar-300"/>}
    </svg>
    <figcaption className="text-sm leading-6 text-[var(--text-secondary)]">{tangent?`曲线 f(x)、x${start!.k} 处切点及已揭示的落点 x${landing!.k}。这张图只解释本次更新，不证明收敛。`:"曲线与起点已知。下一条切线将在你主动揭示一步后显示。"}</figcaption>
  </figure>;
}
