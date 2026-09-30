"use client";

import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Paperclip, X, Loader2, PenTool, Eraser, Check, AlertCircle, Undo2, Redo2, Keyboard, LineChart } from "lucide-react";
import { DesmosModal } from "./desmos-modal";
import { getAuthHeaders } from "@/lib/demo-auth";
import { useTheme } from "@/lib/theme-context";
import { ModeSwitcher } from "./mode-switcher";
import type { TutorMode } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function TutorInput({
  value,
  onChange,
  disabled,
  onSubmit,
  onDirect,
  onHint,
  onSimilar,
  placeholder,
  mode,
  onModeChange,
}: {
  value: string;
  onChange: (val: string) => void;
  disabled: boolean;
  onSubmit: (value: string, forcedMode?: "socratic" | "practice" | "direct") => void;
  onDirect?: () => void;
  onHint?: () => void;
  onSimilar?: () => void;
  placeholder?: string;
  mode: TutorMode;
  onModeChange: (mode: TutorMode) => void;
}) {
  function insert(text: string) {
    onChange(`${value}${text}`);
  }

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDrawing, setIsDrawing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isDrawingRef = useRef(false);
  const [eraseMode, setEraseMode] = useState(false);
  const [showKeyboard, setShowKeyboard] = useState(false);
  const [keyboardTab, setKeyboardTab] = useState<"common" | "calculus" | "greek" | "relations">("common");
  const [strokeColor, setStrokeColor] = useState("#242421");
  const [strokeWidth, setStrokeWidth] = useState(3);
  const historyRef = useRef<ImageData[]>([]);
  const historyIndexRef = useRef(-1);
  const [showProxyWarning, setShowProxyWarning] = useState(false);
  const [pendingAction, setPendingAction] = useState<"image" | "canvas" | null>(null);
  const [isDesmosOpen, setIsDesmosOpen] = useState(false);
  const [showAIAsst, setShowAIAsst] = useState(false);
  const { reading } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  function saveHistoryState() {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height);
    historyRef.current = historyRef.current.slice(0, historyIndexRef.current + 1);
    historyRef.current.push(data);
    historyIndexRef.current++;
  }

  function undo() {
    if (historyIndexRef.current > 0) {
      historyIndexRef.current--;
      const data = historyRef.current[historyIndexRef.current];
      const ctx = canvasRef.current?.getContext("2d");
      if (ctx && data) ctx.putImageData(data, 0, 0);
    } else if (historyIndexRef.current === 0) {
      historyIndexRef.current--;
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext("2d");
      if (ctx && canvas) ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  function redo() {
    if (historyIndexRef.current < historyRef.current.length - 1) {
      historyIndexRef.current++;
      const data = historyRef.current[historyIndexRef.current];
      const ctx = canvasRef.current?.getContext("2d");
      if (ctx && data) ctx.putImageData(data, 0, 0);
    }
  }

  function handleProxyConfirm() {
    setShowProxyWarning(false);
    if (pendingAction === "image") {
      fileInputRef.current?.click();
    } else if (pendingAction === "canvas") {
      historyRef.current = [];
      historyIndexRef.current = -1;
      setIsDrawing(true);
    }
    setPendingAction(null);
  }

  function requestAction(action: "image" | "canvas") {
    // Only show warning if they haven't seen it recently, or just show it every time for safety.
    // We'll show it every time as requested.
    setPendingAction(action);
    setShowProxyWarning(true);
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  }

  function removeFile() {
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function handleDesmosImage(base64: string) {
    // Convert base64 to File object
    fetch(base64)
      .then(res => res.blob())
      .then(blob => {
        const file = new File([blob], "desmos_graph.png", { type: "image/png" });
        setSelectedFile(file);
        setPreviewUrl(base64);
      });
  }

  async function submit() {
    const trimmed = value.trim();
    if ((!trimmed && !selectedFile) || disabled || isUploading) return;
    
    let finalMessage = trimmed;
    
    if (selectedFile) {
      setIsUploading(true);
      try {
        const formData = new FormData();
        formData.append("file", selectedFile);
        const res = await fetch(`${API_BASE}/api/uploads`, {
          method: "POST",
          headers: getAuthHeaders(),
          body: formData,
        });
        if (!res.ok) throw new Error("Upload failed");
        const data = await res.json();
        const md = data.markdown ? `\n\n> **文档识别解析**：\n${data.markdown}\n` : "";
        finalMessage = `![上传的文件](${data.url})${md}\n${trimmed}`;
      } catch (e) {
        console.error(e);
        finalMessage = `![文件上传失败]\n\n${trimmed}`;
      } finally {
        setIsUploading(false);
        removeFile();
      }
    }

    onSubmit(finalMessage);
    onChange("");
  }

  return (
    <div className="bg-transparent p-3 sm:p-5 pb-2 sm:pb-3 transition-colors duration-300">
      <div className="mx-auto max-w-4xl rounded-2xl border border-[var(--border-primary)] bg-[var(--bg-card)]/90 backdrop-blur-xl shadow-input transition-all duration-300 relative group focus-within:border-olive-500/60 focus-within:ring-2 focus-within:ring-olive-500/15">
        {previewUrl && (
          <div className="relative p-4 pb-0 bg-transparent">
            <div className="relative inline-block border border-[var(--border-subtle)] rounded-xl overflow-hidden bg-white/60 dark:bg-black/40 shadow-xs">
              <img src={previewUrl} alt="Preview" className="h-20 w-auto object-cover opacity-95" />
              <button
                onClick={removeFile}
                className="absolute top-1.5 right-1.5 bg-black/60 hover:bg-black/80 text-white rounded-full p-1 transition-colors"
                title="移除附加文件"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
        <Textarea
          className={`min-h-[5.5rem] resize-none overflow-y-auto rounded-none rounded-t-2xl border-0 bg-transparent px-4 sm:px-5 py-3.5 text-[15px] sm:text-base text-[var(--text-primary)] placeholder:text-[var(--text-muted)]/70 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-0 leading-relaxed ${reading === "sans" ? "font-ui-sans" : "font-body"}`}
          placeholder={placeholder || "输入数学推导、上传草稿图片或试卷文档 (PDF/Word)...（Enter 发送，Shift+Enter 换行）"}
          value={value}
          onChange={(event) => {
            onChange(event.target.value);
            const el = event.target;
            el.style.height = 'auto';
            el.style.height = `${Math.min(el.scrollHeight, 240)}px`;
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
              requestAnimationFrame(() => {
                const el = event.target as HTMLTextAreaElement;
                el.style.height = 'auto';
              });
            }
          }}
          style={{ height: 'auto' }}
        />

        {/* MATH KEYBOARD */}
        {showKeyboard && (
          <div className="border-t border-[var(--border-subtle)] bg-[#faf9f6] dark:bg-[#1a1a18] p-3 animate-in fade-in slide-in-from-bottom-2 duration-200">
            <div className="flex items-center gap-2 mb-2 border-b border-[var(--border-subtle)] pb-2">
              <button onClick={() => setKeyboardTab("common")} className={`text-xs font-bold px-3 py-1 rounded-full transition-colors ${keyboardTab === "common" ? "bg-[var(--bg-card)] shadow-sm text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>常用符号</button>
              <button onClick={() => setKeyboardTab("calculus")} className={`text-xs font-bold px-3 py-1 rounded-full transition-colors ${keyboardTab === "calculus" ? "bg-[var(--bg-card)] shadow-sm text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>微积分</button>
              <button onClick={() => setKeyboardTab("relations")} className={`text-xs font-bold px-3 py-1 rounded-full transition-colors ${keyboardTab === "relations" ? "bg-[var(--bg-card)] shadow-sm text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>关系运算</button>
              <button onClick={() => setKeyboardTab("greek")} className={`text-xs font-bold px-3 py-1 rounded-full transition-colors ${keyboardTab === "greek" ? "bg-[var(--bg-card)] shadow-sm text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>希腊字母</button>
            </div>
            
            <div className="flex flex-wrap gap-1.5">
              {keyboardTab === "common" && [
                { l: "+", d: "+" }, { l: "-", d: "-" }, { l: "\\times ", d: "×" }, { l: "\\div ", d: "÷" }, { l: "\\pm ", d: "±" }, 
                { l: "\\frac{ }{ }", d: "a/b" }, { l: "^2", d: "x²" }, { l: "^{ }", d: "xⁿ" }, { l: "_n", d: "xₙ" }, 
                { l: "\\sqrt{ }", d: "√" }, { l: "\\sin()", d: "sin" }, { l: "\\cos()", d: "cos" }, { l: "\\tan()", d: "tan" }, 
                { l: "\\log_{ }", d: "log" }, { l: "\\ln()", d: "ln" }, { l: "\\begin{pmatrix} \\\\ \\end{pmatrix}", d: "[ ]" }
              ].map(sym => (
                <button key={sym.l} onClick={() => insert(`$${sym.l}$`)} className="px-3 py-1.5 bg-white dark:bg-[#242421] border border-[var(--border-subtle)] rounded shadow-sm hover:border-cyan-500 hover:text-cyan-600 transition-colors font-mono text-sm sm:text-base font-bold min-w-[2.5rem]">
                  {sym.d}
                </button>
              ))}

              {keyboardTab === "calculus" && [
                { l: "\\int ", d: "∫" }, { l: "\\iint ", d: "∬" }, { l: "\\oint ", d: "∮" }, { l: "\\lim_{x \\to }", d: "lim" }, 
                { l: "\\infty", d: "∞" }, { l: "\\partial", d: "∂" }, { l: "\\nabla", d: "∇" }, { l: "\\mathrm{d}x", d: "dx" }, 
                { l: "\\sum_{i=1}^{n}", d: "∑" }, { l: "\\prod", d: "∏" }, { l: "\\prime", d: "′" }
              ].map(sym => (
                <button key={sym.l} onClick={() => insert(`$${sym.l}$`)} className="px-3 py-1.5 bg-white dark:bg-[#242421] border border-[var(--border-subtle)] rounded shadow-sm hover:border-rose-500 hover:text-rose-600 transition-colors font-mono text-sm sm:text-base font-bold min-w-[2.5rem]">
                  {sym.d}
                </button>
              ))}

              {keyboardTab === "relations" && [
                { l: "=", d: "=" }, { l: "\\neq ", d: "≠" }, { l: "\\approx ", d: "≈" }, { l: ">", d: ">" }, { l: "<", d: "<" }, 
                { l: "\\geq ", d: "≥" }, { l: "\\leq ", d: "≤" }, { l: "\\equiv ", d: "≡" }, { l: "\\propto ", d: "∝" }, 
                { l: "\\to ", d: "→" }, { l: "\\Rightarrow ", d: "⇒" }, { l: "\\Leftrightarrow ", d: "⇔" }, { l: "\\in ", d: "∈" }, 
                { l: "\\notin ", d: "∉" }, { l: "\\subset ", d: "⊂" }, { l: "\\cup ", d: "∪" }, { l: "\\cap ", d: "∩" }
              ].map(sym => (
                <button key={sym.l} onClick={() => insert(`$${sym.l}$`)} className="px-3 py-1.5 bg-white dark:bg-[#242421] border border-[var(--border-subtle)] rounded shadow-sm hover:border-amber-500 hover:text-amber-600 transition-colors font-mono text-sm sm:text-base font-bold min-w-[2.5rem]">
                  {sym.d}
                </button>
              ))}

              {keyboardTab === "greek" && [
                { l: "\\alpha", d: "α" }, { l: "\\beta", d: "β" }, { l: "\\gamma", d: "γ" }, { l: "\\delta", d: "δ" }, 
                { l: "\\epsilon", d: "ε" }, { l: "\\zeta", d: "ζ" }, { l: "\\eta", d: "η" }, { l: "\\theta", d: "θ" }, 
                { l: "\\lambda", d: "λ" }, { l: "\\mu", d: "μ" }, { l: "\\nu", d: "ν" }, { l: "\\xi", d: "ξ" }, 
                { l: "\\pi", d: "π" }, { l: "\\rho", d: "ρ" }, { l: "\\sigma", d: "σ" }, { l: "\\tau", d: "τ" }, 
                { l: "\\phi", d: "φ" }, { l: "\\omega", d: "ω" }, { l: "\\Delta", d: "Δ" }, { l: "\\Sigma", d: "Σ" }, { l: "\\Omega", d: "Ω" }
              ].map(sym => (
                <button key={sym.l} onClick={() => insert(`$${sym.l}$`)} className="px-3 py-1.5 bg-white dark:bg-[#242421] border border-[var(--border-subtle)] rounded shadow-sm hover:border-emerald-500 hover:text-emerald-600 transition-colors font-serif text-sm sm:text-base font-bold min-w-[2.5rem]">
                  {sym.d}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* PROXY WARNING OVERLAY */}
        {mounted && showProxyWarning && createPortal((
          <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-white/95 dark:bg-[#1e1e1b]/95 backdrop-blur-md rounded-[2rem] p-8 animate-in fade-in duration-300">
            <div className="flex items-start max-w-lg w-full mb-6">
              <div className="p-3 bg-amber-500/10 rounded-full text-amber-500 shrink-0 shadow-sm border border-amber-500/20 mr-5">
                <AlertCircle className="w-8 h-8" />
              </div>
              <div className="text-left flex-1 mt-1">
                <h3 className="font-bold text-lg text-[var(--text-primary)] mb-2">网络环境配置提醒</h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  多模态解析（识图、草稿板）需直连本地计算引擎。请确认您当前<strong>未开启全局代理</strong>或已将 <strong>localhost 绕过代理</strong>，以免上传受阻。
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <Button variant="outline" className="px-6 rounded-full border-[var(--border-primary)] hover:bg-[var(--bg-hover)] transition-all" onClick={() => setShowProxyWarning(false)}>
                取消
              </Button>
              <Button className="px-6 rounded-full bg-amber-500 hover:bg-amber-600 shadow-md shadow-amber-500/20 text-white transition-all" onClick={handleProxyConfirm}>
                已知悉，继续
              </Button>
            </div>
          </div>
        ), document.body)}

        {/* WHITEBOARD OVERLAY */}
        {mounted && isDrawing && createPortal((
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-white dark:bg-[#1e1e1b] w-full max-w-5xl h-[85vh] rounded-[2rem] flex flex-col shadow-2xl overflow-hidden border border-[#d6d0ba] dark:border-[#3e3f36]">
              {/* Toolbar */}
              <div className="flex flex-wrap items-center justify-between p-3 px-5 border-b border-[var(--border-subtle)] bg-[#f2efe9] dark:bg-[#242421]">
                <div className="flex items-center gap-4">
                  <h3 className="font-title font-bold text-lg text-[var(--text-primary)] mr-2 hidden sm:block">智能草稿板</h3>
                  
                  {/* Colors */}
                  <div className="flex items-center gap-1.5 bg-white/50 dark:bg-black/20 p-1.5 rounded-full border border-[var(--border-subtle)]">
                    <button onClick={() => {setEraseMode(false); setStrokeColor("#242421");}} className={`w-6 h-6 rounded-full bg-[#242421] border-2 transition-transform ${!eraseMode && strokeColor==="#242421" ? "border-amber-500 scale-110 shadow-sm" : "border-transparent"}`} title="墨黑" />
                    <button onClick={() => {setEraseMode(false); setStrokeColor("#e11d48");}} className={`w-6 h-6 rounded-full bg-rose-600 border-2 transition-transform ${!eraseMode && strokeColor==="#e11d48" ? "border-amber-500 scale-110 shadow-sm" : "border-transparent"}`} title="赤红" />
                    <button onClick={() => {setEraseMode(false); setStrokeColor("#2563eb");}} className={`w-6 h-6 rounded-full bg-blue-600 border-2 transition-transform ${!eraseMode && strokeColor==="#2563eb" ? "border-amber-500 scale-110 shadow-sm" : "border-transparent"}`} title="湛蓝" />
                    <button onClick={() => {setEraseMode(false); setStrokeColor("#16a34a");}} className={`w-6 h-6 rounded-full bg-green-600 border-2 transition-transform ${!eraseMode && strokeColor==="#16a34a" ? "border-amber-500 scale-110 shadow-sm" : "border-transparent"}`} title="翠绿" />
                  </div>

                  {/* Thickness */}
                  <div className="flex items-center gap-1 bg-white/50 dark:bg-black/20 p-1 rounded-full border border-[var(--border-subtle)] text-[var(--text-secondary)]">
                    <button onClick={() => setStrokeWidth(2)} className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${strokeWidth===2 ? "bg-white dark:bg-[#3e3f36] shadow-sm text-[var(--text-primary)]" : "hover:bg-black/5 dark:hover:bg-white/5"}`} title="细笔"><div className="w-4 h-[2px] bg-current rounded-full" /></button>
                    <button onClick={() => setStrokeWidth(4)} className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${strokeWidth===4 ? "bg-white dark:bg-[#3e3f36] shadow-sm text-[var(--text-primary)]" : "hover:bg-black/5 dark:hover:bg-white/5"}`} title="中笔"><div className="w-4 h-[4px] bg-current rounded-full" /></button>
                    <button onClick={() => setStrokeWidth(8)} className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${strokeWidth===8 ? "bg-white dark:bg-[#3e3f36] shadow-sm text-[var(--text-primary)]" : "hover:bg-black/5 dark:hover:bg-white/5"}`} title="粗笔"><div className="w-4 h-[8px] bg-current rounded-full" /></button>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 bg-white/50 dark:bg-black/20 p-1 rounded-full border border-[var(--border-subtle)] mr-2">
                    <Button variant="ghost" size="icon" onClick={undo} className="h-8 w-8 rounded-full text-[var(--text-secondary)] hover:text-[var(--text-primary)]" disabled={historyIndexRef.current < 0} title="撤销">
                      <Undo2 className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={redo} className="h-8 w-8 rounded-full text-[var(--text-secondary)] hover:text-[var(--text-primary)]" disabled={historyIndexRef.current >= historyRef.current.length - 1} title="重做">
                      <Redo2 className="w-4 h-4" />
                    </Button>
                  </div>

                  <Button variant="ghost" size="sm" onClick={() => setEraseMode(!eraseMode)} className={`rounded-full h-9 px-4 transition-colors ${eraseMode ? "bg-rose-500/10 text-rose-600 dark:text-rose-400" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-black/5 dark:hover:bg-white/5"}`}>
                    <Eraser className="w-4 h-4 mr-1.5" /> 橡皮擦
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => {
                    const ctx = canvasRef.current?.getContext("2d");
                    if (ctx && canvasRef.current) {
                      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
                      saveHistoryState();
                    }
                  }} className="rounded-full h-9 px-4 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-black/5 dark:hover:bg-white/5">清空</Button>
                  <Button size="sm" onClick={() => {
                    if (canvasRef.current) {
                      canvasRef.current.toBlob((blob) => {
                        if (blob) {
                          const file = new File([blob], "drawing.png", { type: "image/png" });
                          setSelectedFile(file);
                          setPreviewUrl(URL.createObjectURL(file));
                          setIsDrawing(false);
                        }
                      });
                    }
                  }} className="rounded-full h-9 px-5 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white shadow-sm transition-colors">
                    <Check className="w-4 h-4 mr-1.5" /> 完成
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setIsDrawing(false)} className="h-9 w-9 rounded-full text-[var(--text-secondary)] hover:text-rose-500 hover:bg-rose-500/10 transition-colors ml-1">
                    <X className="w-5 h-5" />
                  </Button>
                </div>
              </div>
              
              {/* Canvas Area with Dot Grid */}
              <div className="flex-1 relative bg-[#faf9f6] dark:bg-[#1a1a18] bg-[radial-gradient(#d6d0ba_1px,transparent_1px)] dark:bg-[radial-gradient(#3e3f36_1px,transparent_1px)] [background-size:24px_24px]" style={{ cursor: eraseMode ? 'crosshair' : 'crosshair' }}>
                <canvas
                  ref={canvasRef}
                  width={1600}
                  height={1200}
                  className="w-full h-full object-contain touch-none"
                  onPointerDown={(e) => {
                    isDrawingRef.current = true;
                    const ctx = canvasRef.current?.getContext("2d");
                    const rect = canvasRef.current?.getBoundingClientRect();
                    if (ctx && rect) {
                      const scaleX = canvasRef.current!.width / rect.width;
                      const scaleY = canvasRef.current!.height / rect.height;
                      ctx.beginPath();
                      ctx.moveTo((e.clientX - rect.left) * scaleX, (e.clientY - rect.top) * scaleY);
                    }
                  }}
                  onPointerMove={(e) => {
                    if (!isDrawingRef.current) return;
                    const ctx = canvasRef.current?.getContext("2d");
                    const rect = canvasRef.current?.getBoundingClientRect();
                    if (ctx && rect) {
                      const scaleX = canvasRef.current!.width / rect.width;
                      const scaleY = canvasRef.current!.height / rect.height;
                      ctx.lineTo((e.clientX - rect.left) * scaleX, (e.clientY - rect.top) * scaleY);
                      ctx.strokeStyle = eraseMode ? "rgba(255,255,255,1)" : strokeColor;
                      ctx.globalCompositeOperation = eraseMode ? "destination-out" : "source-over";
                      ctx.lineWidth = eraseMode ? 30 : strokeWidth;
                      ctx.lineCap = "round";
                      ctx.lineJoin = "round";
                      ctx.stroke();
                    }
                  }}
                  onPointerUp={() => {
                    if (isDrawingRef.current) {
                      isDrawingRef.current = false;
                      saveHistoryState();
                    }
                  }}
                  onPointerOut={() => {
                    if (isDrawingRef.current) {
                      isDrawingRef.current = false;
                      saveHistoryState();
                    }
                  }}
                />
              </div>
            </div>
          </div>
        ), document.body)}

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border-subtle)] bg-[var(--bg-card)]/50 p-2.5 sm:p-3 relative z-10 rounded-b-2xl">
          {/* Tool actions on the left */}
          <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 text-xs">
            <button
              type="button"
              onClick={() => setShowKeyboard(!showKeyboard)}
              className={`inline-flex items-center gap-1.5 h-8 px-3 rounded-full text-xs font-semibold transition-all ${
                showKeyboard 
                  ? "bg-sky-500/15 text-sky-700 dark:text-sky-300 border border-sky-500/30 shadow-xs" 
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border border-transparent"
              }`}
              title="切换数学符号输入键盘"
            >
              <Keyboard className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />
              <span>公式键盘</span>
            </button>
            
            <input type="file" accept="image/*,application/pdf,.doc,.docx" className="hidden" ref={fileInputRef} onChange={handleFileSelect} />
            <button
              type="button"
              onClick={() => requestAction("image")}
              className="inline-flex items-center gap-1.5 h-8 px-3 rounded-full text-xs font-semibold text-[var(--text-secondary)] hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-500/10 transition-all border border-transparent"
              title="上传文档/草稿照片多模态识别"
            >
              <Paperclip className="w-3.5 h-3.5 text-indigo-500" />
              <span>文件解析</span>
            </button>

            <button
              type="button"
              onClick={() => requestAction("canvas")}
              className="inline-flex items-center gap-1.5 h-8 px-3 rounded-full text-xs font-semibold text-[var(--text-secondary)] hover:text-teal-600 dark:hover:text-teal-400 hover:bg-teal-500/10 transition-all border border-transparent"
              title="打开全屏手写草稿白板"
            >
              <PenTool className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
              <span>智能草稿板</span>
            </button>

            <button
              type="button"
              onClick={() => setIsDesmosOpen(true)}
              className="inline-flex items-center gap-1.5 h-8 px-3 rounded-full text-xs font-semibold text-[var(--text-secondary)] hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-500/10 transition-all border border-transparent"
              title="打开 Desmos 动态数学画板"
            >
              <LineChart className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>图形引擎</span>
            </button>

            {onDirect && onHint && onSimilar && (
              <>
                <div className="w-px h-3.5 bg-[var(--border-subtle)] mx-0.5" />

                {/* AI 辅助二级菜单 */}
                <div className="relative">
                  <button 
                    type="button"
                    onClick={() => setShowAIAsst(!showAIAsst)} 
                    className={`inline-flex items-center gap-1 h-8 px-3 rounded-full text-xs font-semibold transition-all ${
                      showAIAsst 
                        ? "bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30" 
                        : "text-[var(--text-secondary)] hover:text-amber-700 dark:hover:text-amber-400 hover:bg-amber-500/10 border border-transparent"
                    }`}
                  >
                    <span>解题锦囊</span>
                    <svg className={`w-3.5 h-3.5 ml-0.5 transition-transform duration-200 ${showAIAsst ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {showAIAsst && (
                    <>
                      <div className="fixed inset-0 z-40" onClick={() => setShowAIAsst(false)} />
                      <div className="absolute bottom-full left-0 mb-2 w-44 bg-[var(--bg-card)]/95 backdrop-blur-xl border border-[var(--border-subtle)] shadow-xl rounded-2xl p-1.5 z-50 flex flex-col gap-0.5 animate-in fade-in slide-in-from-bottom-2 duration-200">
                        <button 
                          className="text-left px-3 py-2 hover:bg-amber-500/10 text-amber-700 dark:text-amber-300 text-xs rounded-xl transition-colors font-medium flex items-center gap-2" 
                          onClick={() => { onHint && onHint(); setShowAIAsst(false); }}
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
                          <span>求取下一步提示</span>
                        </button>
                        <button 
                          className="text-left px-3 py-2 hover:bg-sky-500/10 text-sky-700 dark:text-sky-300 text-xs rounded-xl transition-colors font-medium flex items-center gap-2" 
                          onClick={() => { onDirect && onDirect(); setShowAIAsst(false); }}
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9a2 2 0 0 1-2 2H6l-4 4V4c0-1.1.9-2 2-2h8a2 2 0 0 1 2 2z"/><path d="M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1"/></svg>
                          <span>查看完整证明</span>
                        </button>
                        <button 
                          className="text-left px-3 py-2 hover:bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 text-xs rounded-xl transition-colors font-medium flex items-center gap-2" 
                          onClick={() => { onSimilar && onSimilar(); setShowAIAsst(false); }}
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
                          <span>生成同类迁移练习</span>
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Mode & Submit on the right */}
          <div className="flex items-center justify-end gap-2.5 shrink-0 ml-auto w-full sm:w-auto">
            <ModeSwitcher value={mode} onChange={onModeChange} />
            <Button 
              disabled={disabled || isUploading} 
              onClick={submit} 
              className="h-9 rounded-full bg-olive-600 hover:bg-olive-700 dark:bg-olive-500 dark:hover:bg-olive-400 text-[#faf7f2] shadow-sm px-6 font-bold tracking-wider text-xs active:scale-95 transition-all"
            >
              {isUploading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : null}
              <span>{isUploading ? "解析中..." : "发送"}</span>
            </Button>
          </div>
        </div>
      </div>
      {mounted && createPortal(
        <DesmosModal isOpen={isDesmosOpen} onClose={() => setIsDesmosOpen(false)} onSendImage={handleDesmosImage} />,
        document.body
      )}
    </div>
  );
}
