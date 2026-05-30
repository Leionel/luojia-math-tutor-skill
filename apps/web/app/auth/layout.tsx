import { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-black text-white selection:bg-cyan-500/30">
      {/* GEOMETRIC SILENCE BACKGROUND */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 h-[1000px] w-[1px] -translate-x-1/2 -translate-y-1/2 bg-gradient-to-b from-transparent via-cyan-500/50 to-transparent rotate-90" />
        <div className="absolute top-1/2 left-1/2 h-[1000px] w-[1px] -translate-x-1/2 -translate-y-1/2 bg-gradient-to-b from-transparent via-cyan-500/50 to-transparent" />
        
        <div className="absolute top-1/2 left-1/2 h-[400px] w-[400px] -translate-x-1/2 -translate-y-1/2 border-[1px] border-cyan-500/20 rounded-full mix-blend-screen" />
        <div className="absolute top-1/2 left-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 border-[1px] border-cyan-500/10 rounded-full mix-blend-screen" />
        
        {/* Math Grid */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_20%,transparent_100%)]" />
      </div>

      <div className="relative z-10 w-full max-w-md px-6">
        {children}
      </div>

      <div className="absolute top-8 left-8 text-xs font-mono text-slate-600">
        SYSTEM.AUTH
      </div>
      <div className="absolute top-8 right-8 text-xs font-mono text-slate-600 text-right">
        SECURE CONNECTION
      </div>
    </div>
  );
}
