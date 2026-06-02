"use client";

import { useEffect, useRef, useState } from "react";
import { X, Send } from "lucide-react";
import { Button } from "./ui/button";

// Extend window object to include Desmos
declare global {
  interface Window {
    Desmos: any;
  }
}

export function DesmosModal({
  isOpen,
  onClose,
  onSendImage,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSendImage: (base64Image: string) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const calculatorRef = useRef<any>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (!isOpen || !containerRef.current) return;

    let checkInterval: NodeJS.Timeout;

    const initDesmos = () => {
      if (window.Desmos) {
        if (!calculatorRef.current) {
          calculatorRef.current = window.Desmos.GraphingCalculator(containerRef.current, {
            expressions: true,
            settingsMenu: true,
            zoomButtons: true,
          });
        }
        setIsReady(true);
      } else {
        checkInterval = setTimeout(initDesmos, 500);
      }
    };

    initDesmos();

    return () => {
      if (checkInterval) clearTimeout(checkInterval);
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSend = () => {
    if (calculatorRef.current) {
      // Use Desmos native screenshot API
      calculatorRef.current.asyncScreenshot({
        width: 800,
        height: 600,
        targetPixelRatio: 2
      }, (dataUrl: string) => {
        onSendImage(dataUrl);
        onClose();
      });
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 sm:p-8 animate-in fade-in duration-200">
      <div className="relative w-full max-w-5xl h-[85vh] bg-white dark:bg-[#1a1a18] rounded-[2rem] shadow-2xl overflow-hidden flex flex-col border border-[var(--border-primary)]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-card)]">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-600">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            </div>
            <div>
              <h2 className="font-bold text-[var(--text-primary)]">动态图形计算引擎</h2>
              <p className="text-xs text-[var(--text-secondary)]">Powered by Desmos</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button 
              onClick={handleSend} 
              disabled={!isReady}
              className="rounded-full bg-emerald-600 hover:bg-emerald-700 text-white shadow-md transition-colors font-medium px-5"
            >
              <Send className="w-4 h-4 mr-2" />
              发送图形给助教
            </Button>
            <button 
              onClick={onClose}
              className="p-2 rounded-full text-[var(--text-secondary)] hover:text-rose-500 hover:bg-rose-500/10 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Desmos Container */}
        <div className="flex-1 w-full bg-white relative">
          {!isReady && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-[var(--text-secondary)] bg-[var(--bg-card)] z-10">
              <div className="w-8 h-8 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mb-4" />
              <p className="text-sm font-medium">引擎初始化中...</p>
            </div>
          )}
          <div ref={containerRef} className="w-full h-full" style={{ position: 'absolute', top: 0, left: 0, bottom: 0, right: 0 }} />
        </div>
      </div>
    </div>
  );
}
