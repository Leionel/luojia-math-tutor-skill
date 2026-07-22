"use client";

import { ParticleField } from "./particle-field";

export function InkBackground({ withParticles = false }: { withParticles?: boolean }) {
  return (
    <div className="fixed inset-0 z-0 opacity-40 pointer-events-none overflow-hidden">
      <div className="absolute top-[-10%] right-[-10%] w-[800px] h-[800px] bg-[#617a55] rounded-full mix-blend-multiply dark:mix-blend-lighten filter blur-[150px] opacity-20" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-[#c44a3d] rounded-full mix-blend-multiply dark:mix-blend-lighten filter blur-[150px] opacity-10" />
      <div className="absolute top-1/2 left-1/2 w-[1000px] h-[1000px] bg-[#d6d0ba] dark:bg-[#3e3f36] rounded-full filter blur-[120px] opacity-20 transform -translate-x-1/2 -translate-y-1/2" />
      
      {/* Subtle bamboo/rice paper texture */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noise%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.05%22 numOctaves=%222%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noise)%22 opacity=%220.05%22/%3E%3C/svg%3E')] opacity-30" />
      
      {/* Interactive 3D Math Particle Field */}
      {withParticles && <ParticleField />}
    </div>
  );
}
