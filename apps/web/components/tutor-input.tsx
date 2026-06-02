"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ImageIcon, X, Loader2, PenTool, Eraser, Check, AlertCircle, Undo2, Redo2, Keyboard, LineChart } from "lucide-react";
import { DesmosModal } from "./desmos-modal";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function TutorInput({
  value,
  onChange,
  disabled,
  onSubmit,
  onDirect,
  onHint,
  onSimilar,
}: {
  value: string;
  onChange: (val: string) => void;
  disabled: boolean;
  onSubmit: (value: string, forcedMode?: "socratic" | "practice" | "direct") => void;
  onDirect: () => void;
  onHint: () => void;
  onSimilar: () => void;
}) {
  function insert(text: string) {
    onChange(`${value}${text}`);
  }

  const [isStepMode, setIsStepMode] = useState(false);
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

    onSubmit(finalMessage, isStepMode ? "practice" : "socratic");
    onChange("");
  }

  return (
    <div className="bg-transparent p-4 sm:p-6 pb-6 sm:pb-10 transition-colors duration-300">
      <div className="mx-auto max-w-4xl rounded-[2rem] border border-[var(--border-primary)] bg-white dark:bg-[var(--bg-input)] shadow-input transition-all duration-300 relative group">
        {previewUrl && (
          <div className="relative p-4 pb-0 bg-transparent">
            <div className="relative inline-block border border-[var(--border-subtle)] rounded-md overflow-hidden bg-white/50 dark:bg-black/50">
              <img src={previewUrl} alt="Preview" className="h-20 w-auto object-cover opacity-90" />
              <button
                onClick={removeFile}
                className="absolute top-1 right-1 bg-black/60 hover:bg-black/80 text-white rounded-full p-0.5 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
        <Textarea
          className="min-h-24 rounded-none rounded-t-xl border-0 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-0"
          placeholder="上传问题照片或试卷文档 (PDF/Word)，或直接输入...（Enter 发送，Shift+Enter 换行）"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }}
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
        {showProxyWarning && (
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
        )}

        {/* WHITEBOARD OVERLAY */}
        {isDrawing && (
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
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border-subtle)] bg-transparent p-3 relative z-10">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Button variant="ghost" size="sm" onClick={() => setShowKeyboard(!showKeyboard)} className={`h-8 rounded-full font-medium transition-all ${showKeyboard ? "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"}`}>
              <Keyboard className="w-4 h-4 mr-1" />
              公式键盘
            </Button>
            
            <div className="w-px h-4 bg-[var(--border-primary)] my-auto mx-1" />
            <input type="file" accept="image/*,application/pdf,.doc,.docx" className="hidden" ref={fileInputRef} onChange={handleFileSelect} />
            <Button variant="ghost" size="sm" onClick={() => requestAction("image")} className="h-8 rounded-full text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/10 font-medium transition-all" title="上传文档/图片识别">
              <ImageIcon className="w-4 h-4 mr-1" />
              文件解析
            </Button>
            <Button variant="ghost" size="sm" onClick={() => requestAction("canvas")} className="h-8 rounded-full text-teal-600 dark:text-teal-400 hover:bg-teal-500/10 font-medium transition-all" title="打开草稿板">
              <PenTool className="w-4 h-4 mr-1" />
              草稿板
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setIsDesmosOpen(true)} className="h-8 rounded-full text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10 font-medium transition-all" title="打开动态图形引擎">
              <LineChart className="w-4 h-4 mr-1" />
              图形引擎
            </Button>

            <div className="w-px h-4 bg-[var(--border-primary)] my-auto mx-1" />

            {/* AI 辅助二级菜单 */}
            <div className="relative">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowAIAsst(!showAIAsst)} 
                className={`h-8 rounded-full font-medium transition-all ${showAIAsst ? "bg-amber-500/10 text-amber-600 dark:text-amber-400" : "text-[var(--text-secondary)] hover:text-amber-600 dark:hover:text-amber-400 hover:bg-[var(--bg-hover)]"}`}
              >
                解题锦囊
                <svg className={`w-3.5 h-3.5 ml-1 transition-transform ${showAIAsst ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </Button>
              {showAIAsst && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowAIAsst(false)} />
                  <div className="absolute bottom-full left-0 mb-2 w-36 bg-white dark:bg-[#1a1a18] border border-[var(--border-subtle)] shadow-xl rounded-xl p-1.5 z-50 flex flex-col gap-0.5 animate-in fade-in slide-in-from-bottom-2 duration-200">
                    <button className="text-left px-3 py-2 hover:bg-amber-500/10 text-amber-600 dark:text-amber-400 text-xs rounded-md transition-colors font-medium flex items-center gap-2" onClick={() => { onHint(); setShowAIAsst(false); }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>获取提示
                    </button>
                    <button className="text-left px-3 py-2 hover:bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs rounded-md transition-colors font-medium flex items-center gap-2" onClick={() => { onDirect(); setShowAIAsst(false); }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9a2 2 0 0 1-2 2H6l-4 4V4c0-1.1.9-2 2-2h8a2 2 0 0 1 2 2z"/><path d="M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1"/></svg>看完整解答
                    </button>
                    <button className="text-left px-3 py-2 hover:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs rounded-md transition-colors font-medium flex items-center gap-2" onClick={() => { onSimilar(); setShowAIAsst(false); }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>生成类似题
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 shrink-0 ml-auto w-full sm:w-auto">
            <div className="group relative flex items-center">
              <button
                onClick={() => setIsStepMode(!isStepMode)}
                className="flex items-center gap-2 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all cursor-help"
              >
                <div className="relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center justify-center rounded-full outline-none">
                  <div className={`absolute inset-0 rounded-full transition-colors duration-300 ${isStepMode ? "bg-[var(--accent)]" : "bg-[var(--bg-hover)]"}`} />
                  <div className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-transform duration-300 ${isStepMode ? "translate-x-4" : "translate-x-0"}`} />
                </div>
                分步引导
              </button>
              
              {/* Hover Tooltip for Step Mode */}
              <div className="absolute top-full right-0 mt-2.5 w-56 opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 z-[100] -translate-y-1 group-hover:translate-y-0">
                <div className="bg-white dark:bg-[#1e1e1b] border border-[var(--border-subtle)] shadow-xl rounded-lg p-3 text-[11px] text-[var(--text-secondary)] leading-relaxed relative text-left">
                  <div className="absolute -top-1.5 right-5 w-3 h-3 bg-white dark:bg-[#1e1e1b] border-l border-t border-[var(--border-subtle)] rotate-45"></div>
                  开启后，AI 将不会直接给出完整解答，而是带您一步步拆解运算过程。
                </div>
              </div>
            </div>
            
            <Button disabled={disabled || isUploading} onClick={submit} className="h-9 rounded-full bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white shadow-md shadow-[var(--accent-light)] px-6 font-semibold transition-all">
              {isUploading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              {isUploading ? "提取中..." : "发送"}
            </Button>
          </div>
        </div>
      </div>
      <DesmosModal isOpen={isDesmosOpen} onClose={() => setIsDesmosOpen(false)} onSendImage={handleDesmosImage} />
    </div>
  );
}
