"use client";

import { ParticleField } from "./particle-field";

export function InkBackground({ withParticles = false }: { withParticles?: boolean }) {
  return (
    <>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes inkDrift {
          0% { transform: translate(0, 0) scale(1) rotate(0deg); }
          33% { transform: translate(30px, -50px) scale(1.05) rotate(2deg); }
          66% { transform: translate(-20px, 20px) scale(0.95) rotate(-1deg); }
          100% { transform: translate(0, 0) scale(1) rotate(0deg); }
        }
        @keyframes inkPulse {
          0% { opacity: 0.5; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.02); }
          100% { opacity: 0.5; transform: scale(1); }
        }
        .ink-drift { animation: inkDrift 20s ease-in-out infinite; }
        .ink-drift-reverse { animation: inkDrift 25s ease-in-out infinite reverse; }
        .ink-pulse { animation: inkPulse 15s ease-in-out infinite; }
      `}} />
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden bg-[#faf9f6] dark:bg-[#1a1a18] transition-colors duration-500">
        {/* Base rice paper texture with improved contrast */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noise%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%224%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noise)%22 opacity=%220.06%22/%3E%3C/svg%3E')] mix-blend-multiply dark:mix-blend-overlay opacity-60" />
        
        {/* Ink wash elements (animating slowly) */}
        <div className="ink-drift absolute top-[-20%] right-[-10%] w-[1000px] h-[1000px] bg-[radial-gradient(circle,_var(--tw-gradient-stops))] from-[#617a55]/20 via-[#617a55]/5 to-transparent rounded-full mix-blend-multiply dark:mix-blend-lighten blur-[100px]" />
        
        <div className="ink-drift-reverse absolute bottom-[-15%] left-[-15%] w-[800px] h-[800px] bg-[radial-gradient(circle,_var(--tw-gradient-stops))] from-[#c44a3d]/15 via-[#c44a3d]/5 to-transparent rounded-full mix-blend-multiply dark:mix-blend-lighten blur-[120px]" />
        
        <div className="ink-pulse absolute top-[20%] left-[20%] w-[1200px] h-[1200px] bg-[radial-gradient(circle,_var(--tw-gradient-stops))] from-[#d6d0ba]/30 via-[#d6d0ba]/10 to-transparent dark:from-[#3e3f36]/30 dark:via-[#3e3f36]/10 rounded-full mix-blend-multiply dark:mix-blend-lighten blur-[140px]" />
        
        {/* Interactive 3D Math Particle Field */}
        {withParticles && (
          <div className="absolute inset-0 opacity-50 mix-blend-overlay dark:mix-blend-screen">
            <ParticleField />
          </div>
        )}
      </div>
    </>
  );
}
