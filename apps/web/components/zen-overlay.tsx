"use client";

import { useEffect, useRef, useState } from "react";
import { Play, Pause, RotateCcw, Target } from "lucide-react";
import { Button } from "./ui/button";

export function ZenOverlay({ isZenMode }: { isZenMode: boolean }) {
  const [timeLeft, setTimeLeft] = useState(25 * 60);
  const [isRunning, setIsRunning] = useState(false);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const noiseNodeRef = useRef<AudioBufferSourceNode | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);

  // Timer logic
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRunning && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      setIsRunning(false);
    }
    return () => clearInterval(interval);
  }, [isRunning, timeLeft]);

  // Audio synthesis (Pink Noise)
  useEffect(() => {
    if (!isZenMode) {
      // Clean up when exiting zen mode
      if (noiseNodeRef.current) {
        try { noiseNodeRef.current.stop(); } catch (e) {}
      }
      setIsRunning(false);
      return;
    }

    // Initialize AudioContext on first play
    if (!audioContextRef.current && typeof window !== "undefined") {
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioContext) {
        audioContextRef.current = new AudioContext();
      }
    }

    return () => {
      if (noiseNodeRef.current) {
        try { noiseNodeRef.current.stop(); } catch (e) {}
      }
    };
  }, [isZenMode]);

  const generatePinkNoise = (context: AudioContext) => {
    const bufferSize = 2 * context.sampleRate;
    const noiseBuffer = context.createBuffer(1, bufferSize, context.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    
    // Pink noise generation algorithm (Paul Kellet's method)
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
    
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.96900 * b2 + white * 0.1538520;
      b3 = 0.86650 * b3 + white * 0.3104856;
      b4 = 0.55000 * b4 + white * 0.5329522;
      b5 = -0.7616 * b5 - white * 0.0168980;
      output[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
      output[i] *= 0.11; // (roughly) compensate for gain
      b6 = white * 0.115926;
    }
    
    return noiseBuffer;
  };

  const toggleAudio = () => {
    if (!audioContextRef.current) return;
    
    if (isRunning) {
      // Pause
      if (noiseNodeRef.current) {
        try { noiseNodeRef.current.stop(); } catch(e) {}
        noiseNodeRef.current = null;
      }
    } else {
      // Play
      if (audioContextRef.current.state === "suspended") {
        audioContextRef.current.resume();
      }
      
      const buffer = generatePinkNoise(audioContextRef.current);
      noiseNodeRef.current = audioContextRef.current.createBufferSource();
      noiseNodeRef.current.buffer = buffer;
      noiseNodeRef.current.loop = true;
      
      gainNodeRef.current = audioContextRef.current.createGain();
      gainNodeRef.current.gain.value = 0.03; // Very soft volume
      
      noiseNodeRef.current.connect(gainNodeRef.current);
      gainNodeRef.current.connect(audioContextRef.current.destination);
      
      noiseNodeRef.current.start();
    }
  };

  const handlePlayPause = () => {
    toggleAudio();
    setIsRunning(!isRunning);
  };

  const resetTimer = () => {
    setTimeLeft(25 * 60);
    setIsRunning(false);
    if (noiseNodeRef.current) {
      try { noiseNodeRef.current.stop(); } catch(e) {}
      noiseNodeRef.current = null;
    }
  };

  if (!isZenMode) return null;

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;

  return (
    <div className="fixed top-6 right-6 z-50 flex flex-col items-end gap-2 animate-in fade-in slide-in-from-top-4 duration-500">
      <div className="bg-white/10 dark:bg-black/40 backdrop-blur-md border border-white/20 dark:border-white/10 rounded-2xl p-4 shadow-2xl flex flex-col items-center min-w-[140px] transition-all">
        <div className="flex items-center gap-2 text-white/70 mb-2 text-xs font-medium tracking-widest uppercase">
          <Target className="w-3.5 h-3.5" />
          <span>Flow State</span>
        </div>
        
        <div className="text-4xl font-mono font-light text-white tracking-tight mb-4 select-none">
          {minutes.toString().padStart(2, "0")}:{seconds.toString().padStart(2, "0")}
        </div>
        
        <div className="flex items-center gap-3">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={handlePlayPause}
            className="h-10 w-10 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
          >
            {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={resetTimer}
            className="h-10 w-10 rounded-full bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
