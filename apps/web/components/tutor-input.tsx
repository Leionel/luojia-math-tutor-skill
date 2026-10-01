"use client";

import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Paperclip, X, Loader2, PenTool, Eraser, Check, AlertCircle, Undo2, Redo2, Keyboard, LineChart, Globe, BrainCircuit, Plus, Sparkles, BookOpen, Target } from "lucide-react";
import { DesmosModal } from "./desmos-modal";
import { getAuthHeaders } from "@/lib/demo-auth";
import { useTheme } from "@/lib/theme-context";
import { ModeSwitcher } from "./mode-switcher";
import type { TutorMode } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const EFFORT_OPTIONS = [
  { value: "off", label: "直答 (Off)", desc: "极速响应，不展开思考链" },
  { value: "low", label: "轻敏 (Low)", desc: "轻量梳理，快速切入" },
  { value: "medium", label: "深思 (Medium)", desc: "严谨推演，循循善诱 (默认)" },
  { value: "max", label: "格物 (Max)", desc: "极限思维深度，定理全盘剖析" },
] as const;

export type ReasoningEffortLevel = "off" | "low" | "medium" | "high" | "max";

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
  webSearch = false,
  onWebSearchChange,
  reasoningEffort = "medium",
  onReasoningEffortChange,
}: {
  value: string;
  onChange: (val: string) => void;
  disabled: boolean;
  onSubmit: (value: string, forcedMode?: "socratic" | "practice" | "direct", imageUrls?: string[]) => void;
  onDirect?: () => void;
  onHint?: () => void;
  onSimilar?: () => void;
  placeholder?: string;
  mode: TutorMode;
  onModeChange: (mode: TutorMode) => void;
  webSearch?: boolean;
  onWebSearchChange?: (val: boolean) => void;
  reasoningEffort?: ReasoningEffortLevel;
  onReasoningEffortChange?: (val: ReasoningEffortLevel) => void;
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
  const [showToolsMenu, setShowToolsMenu] = useState(false);
  const [showEffortMenu, setShowEffortMenu] = useState(false);
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
    let imageUrls: string[] | undefined;

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
        if (selectedFile.type.startsWith("image/") && typeof data.url === "string") imageUrls = [data.url];
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

    onSubmit(finalMessage, undefined, imageUrls);
    onChange("");
  }

  return (
    <div className="bg-transparent p-2 sm:p-4 pb-2 transition-colors duration-300">
      <div className="mx-auto max-w-4xl rounded-xl border border-[#d8cfb4] dark:border-[#3e3f36] bg-[#fbf9f4]/95 dark:bg-[#1f201c]/95 backdrop-blur-xl shadow-input transition-all duration-300 relative group focus-within:border-olive-600/70 focus-within:ring-2 focus-within:ring-olive-600/15">
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

        {/* 顶部常用算子快选带与模式切换 */}
        <div className="flex items-center justify-between gap-2 px-3 sm:px-4 py-1.5 border-b border-[#ece5cf]/60 dark:border-[#33352b]/60">
          <div className="hidden sm:flex items-center gap-1.5 overflow-x-auto min-w-0 text-[11px] font-mono pr-1">
            <span className="text-[var(--text-muted)] font-serif mr-0.5 select-none shrink-0">算子:</span>
            {[
              { s: "\\int ", d: "∫" },
              { s: "\\mathrm{d}x", d: "dx" },
              { s: "\\partial", d: "∂" },
              { s: "\\sum_{i=1}^{n}", d: "∑" },
              { s: "\\lambda", d: "λ" },
              { s: "\\infty", d: "∞" },
              { s: "e^{x}", d: "eˣ" },
              { s: "\\lim_{x \\to 0}", d: "lim" },
              { s: "P(A|B)", d: "P(A|B)" },
            ].map((op) => (
              <button
                key={op.d}
                type="button"
                onClick={() => insert(`$${op.s}$`)}
                className="px-2 py-0.5 rounded bg-[#f0eae0] dark:bg-[#282a24] hover:bg-olive-500/15 hover:text-olive-700 dark:hover:text-olive-300 border border-[#dfd7c2] dark:border-[#383a30] transition-colors font-serif font-semibold shrink-0"
              >
                {op.d}
              </button>
            ))}
          </div>

          <span className="text-xs text-[var(--text-muted)] sm:hidden">提问与推导</span>
          <div className="shrink-0">
            <ModeSwitcher value={mode} onChange={onModeChange} />
          </div>
        </div>

        <Textarea
          className={`min-h-[4rem] sm:min-h-[4.8rem] resize-none overflow-y-auto rounded-none border-0 bg-transparent px-4 sm:px-5 py-3 text-base text-[var(--text-primary)] placeholder:text-[var(--text-muted)]/70 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-0 leading-relaxed ${reading === "sans" ? "font-ui-sans" : "font-serif"}`}
          placeholder={placeholder || "写下问题或推导步骤，也可以上传草稿…"}
          value={value}
          onChange={(event) => {
            onChange(event.target.value);
            const el = event.target;
            el.style.height = 'auto';
            el.style.height = `${Math.min(el.scrollHeight, 240)}px`;
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing && !window.matchMedia("(pointer: coarse)").matches) {
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
                    <button onClick={() => setStrokeWidth(2)} className={`w-10 h-10 sm:w-8 sm:h-8 rounded-full flex items-center justify-center transition-colors ${strokeWidth===2 ? "bg-white dark:bg-[#3e3f36] shadow-sm text-[var(--text-primary)]" : "hover:bg-black/5 dark:hover:bg-white/5"}`} title="细笔"><div className="w-4 h-[2px] bg-current rounded-full" /></button>
                    <button onClick={() => setStrokeWidth(4)} className={`w-10 h-10 sm:w-8 sm:h-8 rounded-full flex items-center justify-center transition-colors ${strokeWidth===4 ? "bg-white dark:bg-[#3e3f36] shadow-sm text-[var(--text-primary)]" : "hover:bg-black/5 dark:hover:bg-white/5"}`} title="中笔"><div className="w-4 h-[4px] bg-current rounded-full" /></button>
                    <button onClick={() => setStrokeWidth(8)} className={`w-10 h-10 sm:w-8 sm:h-8 rounded-full flex items-center justify-center transition-colors ${strokeWidth===8 ? "bg-white dark:bg-[#3e3f36] shadow-sm text-[var(--text-primary)]" : "hover:bg-black/5 dark:hover:bg-white/5"}`} title="粗笔"><div className="w-4 h-[8px] bg-current rounded-full" /></button>
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

        <div className="flex items-center justify-between gap-2 sm:gap-3 border-t border-[var(--border-subtle)] bg-[var(--bg-card)]/50 p-2 sm:p-2.5 px-3 sm:px-4 relative z-10 rounded-b-2xl">
          {/* 左侧：+号扩展工具、联网探微、运思推演 */}
          <div className="flex items-center gap-1 sm:gap-2 whitespace-nowrap text-xs">
            <input type="file" accept="image/*,application/pdf,.doc,.docx" className="hidden" ref={fileInputRef} onChange={handleFileSelect} />

            {/* + 号扩展工具箱 */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowToolsMenu(!showToolsMenu)}
                className={`inline-flex items-center justify-center w-10 h-10 sm:w-8 sm:h-8 rounded-full transition-all border ${
                  showToolsMenu || showKeyboard
                    ? "bg-olive-600/15 text-olive-700 dark:text-olive-300 border-olive-500/40 shadow-xs"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/60"
                }`}
                title="扩展工具箱 (公式键盘、文件解析、草稿板、图形引擎)"
              >
                <Plus className={`w-4 h-4 transition-transform duration-200 ${showToolsMenu ? "rotate-45" : ""}`} />
              </button>

              {showToolsMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowToolsMenu(false)} />
                  <div className="absolute bottom-full left-0 mb-2 w-52 bg-[var(--bg-card)]/95 backdrop-blur-xl border border-[var(--border-subtle)] shadow-xl rounded-2xl p-1.5 z-50 flex flex-col gap-0.5 animate-in fade-in slide-in-from-bottom-2 duration-200">
                    <div className="px-2.5 py-1 text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-wider font-mono">
                      输入与推演工具
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        setShowKeyboard(!showKeyboard);
                        setShowToolsMenu(false);
                      }}
                      className={`text-left px-2.5 py-1.5 hover:bg-sky-500/10 text-sky-800 dark:text-sky-300 text-xs rounded-xl transition-colors font-medium flex items-center gap-2.5 ${showKeyboard ? "bg-sky-500/10" : ""}`}
                    >
                      <Keyboard className="w-4 h-4 text-sky-600 dark:text-sky-400 shrink-0" />
                      <div className="flex flex-col">
                        <span className="font-semibold text-xs">公式键盘</span>
                        <span className="text-[10px] text-[var(--text-muted)]">数学符号快速输入板</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setShowToolsMenu(false);
                        requestAction("image");
                      }}
                      className="text-left px-2.5 py-1.5 hover:bg-indigo-500/10 text-indigo-800 dark:text-indigo-300 text-xs rounded-xl transition-colors font-medium flex items-center gap-2.5"
                    >
                      <Paperclip className="w-4 h-4 text-indigo-500 shrink-0" />
                      <div className="flex flex-col">
                        <span className="font-semibold text-xs">文件解析</span>
                        <span className="text-[10px] text-[var(--text-muted)]">文档与草稿图片 OCR</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setShowToolsMenu(false);
                        requestAction("canvas");
                      }}
                      className="text-left px-2.5 py-1.5 hover:bg-teal-500/10 text-teal-800 dark:text-teal-300 text-xs rounded-xl transition-colors font-medium flex items-center gap-2.5"
                    >
                      <PenTool className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
                      <div className="flex flex-col">
                        <span className="font-semibold text-xs">智能草稿板</span>
                        <span className="text-[10px] text-[var(--text-muted)]">手绘推导演草白板</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setShowToolsMenu(false);
                        setIsDesmosOpen(true);
                      }}
                      className="text-left px-2.5 py-1.5 hover:bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 text-xs rounded-xl transition-colors font-medium flex items-center gap-2.5"
                    >
                      <LineChart className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                      <div className="flex flex-col">
                        <span className="font-semibold text-xs">图形引擎</span>
                        <span className="text-[10px] text-[var(--text-muted)]">Desmos 函数交互几何</span>
                      </div>
                    </button>

                    {onDirect && onHint && onSimilar && (
                      <div className="pt-1.5 mt-1 border-t border-[var(--border-subtle)] flex flex-col gap-0.5">
                        <div className="px-2.5 py-0.5 text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-wider font-mono">
                          解题锦囊快捷指令
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setShowToolsMenu(false);
                            onHint();
                          }}
                          className="text-left px-2.5 py-1.5 hover:bg-amber-500/10 text-amber-800 dark:text-amber-300 text-xs rounded-xl transition-colors font-medium flex items-center gap-2"
                        >
                          <Sparkles className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                          <span>求取下一步提示</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setShowToolsMenu(false);
                            onDirect();
                          }}
                          className="text-left px-2.5 py-1.5 hover:bg-sky-500/10 text-sky-800 dark:text-sky-300 text-xs rounded-xl transition-colors font-medium flex items-center gap-2"
                        >
                          <BookOpen className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                          <span>查看完整证明</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setShowToolsMenu(false);
                            onSimilar();
                          }}
                          className="text-left px-2.5 py-1.5 hover:bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 text-xs rounded-xl transition-colors font-medium flex items-center gap-2"
                        >
                          <Target className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          <span>生成同类练习</span>
                        </button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>

            <div className="w-px h-3.5 bg-[var(--border-subtle)] mx-0.5" />

            {/* 联网检索开关 */}
            <button
              type="button"
              onClick={() => onWebSearchChange?.(!webSearch)}
              className={`inline-flex items-center gap-1 h-10 sm:h-8 px-2 sm:px-3 rounded-full text-xs font-semibold transition-all border ${
                webSearch
                  ? "bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border-emerald-500/40 shadow-xs ring-1 ring-emerald-500/20"
                  : "text-[var(--text-secondary)] hover:text-emerald-700 dark:hover:text-emerald-300 hover:bg-emerald-500/10 border-transparent"
              }`}
              title={webSearch ? "已开启联网探微 (结合网络题库与最新学术推导)" : "点击开启联网检索"}
            >
              <Globe className={`w-3.5 h-3.5 ${webSearch ? "text-emerald-600 dark:text-emerald-400 animate-pulse" : "text-[var(--text-tertiary)]"}`} />
              <span className="sm:hidden">联网</span><span className="hidden sm:inline">联网探微</span>
              {webSearch && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>}
            </button>

            {/* 运思推演深度开关 */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowEffortMenu(!showEffortMenu)}
                className={`inline-flex items-center gap-1 h-10 sm:h-8 px-2 sm:px-3 rounded-full text-xs font-semibold transition-all border ${
                  reasoningEffort !== "off"
                    ? "bg-purple-500/15 text-purple-800 dark:text-purple-300 border-purple-500/30"
                    : "text-[var(--text-secondary)] hover:text-purple-700 dark:hover:text-purple-300 hover:bg-purple-500/10 border-transparent"
                }`}
                title="调整模型运思强度与深度"
              >
                <BrainCircuit className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
                <span><span className="hidden sm:inline">运思:</span>{reasoningEffort === "off" ? "直答" : reasoningEffort === "low" ? "轻敏" : reasoningEffort === "max" ? "格物" : "深思"}</span>
                <svg className={`w-3 h-3 ml-0.5 transition-transform duration-200 ${showEffortMenu ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showEffortMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowEffortMenu(false)} />
                  <div className="absolute bottom-full left-0 mb-2 w-52 bg-[var(--bg-card)]/95 backdrop-blur-xl border border-[var(--border-subtle)] shadow-xl rounded-2xl p-1.5 z-50 flex flex-col gap-1 animate-in fade-in slide-in-from-bottom-2 duration-200">
                    <div className="px-2.5 py-1 text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-wider">
                      运思推演深度 (Reasoning)
                    </div>
                    {EFFORT_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => {
                          onReasoningEffortChange?.(opt.value);
                          setShowEffortMenu(false);
                        }}
                        className={`text-left px-2.5 py-1.5 text-xs rounded-xl transition-all flex items-center justify-between ${
                          reasoningEffort === opt.value
                            ? "bg-purple-500/15 text-purple-700 dark:text-purple-300 font-bold"
                            : "text-[var(--text-primary)] hover:bg-[var(--bg-hover)] font-normal"
                        }`}
                      >
                        <div className="flex flex-col">
                          <span className="font-medium text-xs">{opt.label}</span>
                          <span className="text-[10px] text-[var(--text-secondary)]">{opt.desc}</span>
                        </div>
                        {reasoningEffort === opt.value && <Check className="w-3.5 h-3.5 text-purple-600 shrink-0 ml-1" />}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 右侧：纯净发送按钮 */}
          <div className="flex items-center justify-end shrink-0 ml-auto">
            <Button
              disabled={disabled || isUploading}
              onClick={submit}
              className="h-10 sm:h-9 rounded-full bg-olive-600 hover:bg-olive-700 dark:bg-olive-500 dark:hover:bg-olive-400 text-[#faf7f2] shadow-sm px-4 sm:px-6 font-bold tracking-wider text-xs active:scale-95 transition-all"
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
