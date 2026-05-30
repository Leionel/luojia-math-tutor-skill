"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ImageIcon, X, Loader2, PenTool, Eraser, Check, AlertCircle } from "lucide-react";

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
  const [showProxyWarning, setShowProxyWarning] = useState(false);
  const [pendingAction, setPendingAction] = useState<"image" | "canvas" | null>(null);

  function handleProxyConfirm() {
    setShowProxyWarning(false);
    if (pendingAction === "image") {
      fileInputRef.current?.click();
    } else if (pendingAction === "canvas") {
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
        const md = data.markdown ? `\n\n> **MinerU 识别解析**：\n${data.markdown}\n` : "";
        finalMessage = `![上传的图片](${data.url})${md}\n${trimmed}`;
      } catch (e) {
        console.error(e);
        finalMessage = `![图片上传失败]\n\n${trimmed}`;
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
      <div className="mx-auto max-w-4xl rounded-[2rem] border border-[var(--border-primary)] bg-white dark:bg-[var(--bg-input)] shadow-input overflow-hidden transition-all duration-300 relative group">
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
          placeholder="上传数学题照片，或输入问题...（Enter 发送，Shift+Enter 换行）"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }}
        />

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
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-white dark:bg-[#242421] w-full max-w-5xl h-[80vh] rounded-2xl flex flex-col shadow-2xl overflow-hidden border border-[#d6d0ba] dark:border-[#3e3f36]">
              <div className="flex items-center justify-between p-4 border-b border-[#d6d0ba] dark:border-[#3e3f36] bg-[#f2efe9] dark:bg-[#1e1e1b]">
                <h3 className="font-title font-bold text-lg">智能草稿板</h3>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setEraseMode(!eraseMode)} className={eraseMode ? "bg-[#c44a3d]/10 text-[#c44a3d]" : ""}>
                    <Eraser className="w-4 h-4 mr-1" />
                    {eraseMode ? "橡皮擦" : "橡皮擦"}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => {
                    const ctx = canvasRef.current?.getContext("2d");
                    if (ctx && canvasRef.current) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
                  }}>清空</Button>
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
                  }} className="bg-[#617a55] hover:bg-[#4e6344] text-white">
                    <Check className="w-4 h-4 mr-1" /> 完成
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setIsDrawing(false)}><X className="w-4 h-4" /></Button>
                </div>
              </div>
              <div className="flex-1 relative bg-white" style={{ cursor: eraseMode ? 'crosshair' : 'crosshair' }}>
                <canvas
                  ref={canvasRef}
                  width={1000}
                  height={800}
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
                      ctx.strokeStyle = eraseMode ? "white" : "black";
                      ctx.lineWidth = eraseMode ? 20 : 3;
                      ctx.lineCap = "round";
                      ctx.lineJoin = "round";
                      ctx.stroke();
                    }
                  }}
                  onPointerUp={() => isDrawingRef.current = false}
                  onPointerOut={() => isDrawingRef.current = false}
                />
              </div>
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border-subtle)] bg-transparent p-3 relative z-10">
          <div className="flex flex-wrap gap-2 text-xs">
            <Button variant="ghost" size="sm" onClick={() => insert("$\\int  dx$")} className="h-8 rounded-full text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] font-medium transition-all">积分</Button>
            <Button variant="ghost" size="sm" onClick={() => insert("$\\lim_{x \\to 0}$")} className="h-8 rounded-full text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] font-medium transition-all">极限</Button>
            <Button variant="ghost" size="sm" onClick={() => insert("$\\frac{}{}$")} className="h-8 rounded-full text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] font-medium transition-all">分式</Button>
            <Button variant="ghost" size="sm" onClick={() => insert("$\\begin{pmatrix}  \\\\  \\end{pmatrix}$")} className="h-8 rounded-full text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] font-medium transition-all">矩阵</Button>
            
            <div className="w-px h-4 bg-[var(--border-primary)] my-auto mx-1" />
            <input type="file" accept="image/*" className="hidden" ref={fileInputRef} onChange={handleFileSelect} />
            <Button variant="ghost" size="sm" onClick={() => requestAction("image")} className="h-8 rounded-full text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/10 font-medium transition-all" title="上传数学图片识别">
              <ImageIcon className="w-4 h-4 mr-1" />
              识图提取
            </Button>
            <Button variant="ghost" size="sm" onClick={() => requestAction("canvas")} className="h-8 rounded-full text-teal-600 dark:text-teal-400 hover:bg-teal-500/10 font-medium transition-all" title="打开草稿板">
              <PenTool className="w-4 h-4 mr-1" />
              草稿板
            </Button>
            <div className="w-px h-4 bg-[var(--border-primary)] my-auto mx-1" />
            <Button variant="ghost" size="sm" onClick={onHint} className="h-8 rounded-full text-amber-600 dark:text-amber-500 hover:bg-amber-500/10 hover:text-amber-700 dark:hover:text-amber-400 font-medium transition-all">获取提示</Button>
            <Button variant="ghost" size="sm" onClick={onDirect} className="h-8 rounded-full text-blue-600 dark:text-blue-400 hover:bg-blue-500/10 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-all">看完整解答</Button>
            <Button variant="ghost" size="sm" onClick={onSimilar} className="h-8 rounded-full text-emerald-600 dark:text-emerald-500 hover:bg-emerald-500/10 hover:text-emerald-700 dark:hover:text-emerald-400 font-medium transition-all">生成类似题</Button>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsStepMode(!isStepMode)}
              className="flex items-center gap-2 text-xs font-medium text-[var(--text-secondary)] transition-all"
            >
              <div className="relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center justify-center rounded-full outline-none">
                <div className={`absolute inset-0 rounded-full transition-colors duration-300 ${isStepMode ? "bg-[var(--accent)]" : "bg-[var(--bg-hover)]"}`} />
                <div className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-transform duration-300 ${isStepMode ? "translate-x-4" : "translate-x-0"}`} />
              </div>
              分步提交
            </button>
            <Button disabled={disabled || isUploading} onClick={submit} className="h-9 rounded-full bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white shadow-md shadow-[var(--accent-light)] px-6 font-semibold transition-all">
              {isUploading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              {isUploading ? "提取中..." : "发送"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
