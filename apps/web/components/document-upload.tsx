"use client";
import {useEffect,useRef,useState} from "react";
import {Upload,Loader2} from "lucide-react";
import {uploadTextbook} from "@/lib/api";
import {getCurrentUserId,getAuthHeaders,isAuthStorageKey} from "@/lib/demo-auth";
import {DOCUMENT_ACCEPT,documentUploadError} from "@/lib/material-policy";

/** The only binary document upload UI. Parsing never starts note generation. */
export function DocumentUpload({onUploaded,disabled=false}: {onUploaded:(id:string)=>void;disabled?:boolean}) {
  const [phase,setPhase]=useState<"idle"|"requesting"|"success"|"failed">("idle");
  const [error,setError]=useState(""),[name,setName]=useState("");
  const request=useRef<AbortController|null>(null),alive=useRef(true),input=useRef<HTMLInputElement>(null);
  useEffect(()=>{
    alive.current=true;
    const changed=()=>{request.current?.abort();setPhase("idle");setError("");setName("");};
    const storage=(e:StorageEvent)=>{if(isAuthStorageKey(e.key))changed();};
    window.addEventListener("luojia-auth-change",changed);window.addEventListener("storage",storage);
    return()=>{alive.current=false;request.current?.abort();window.removeEventListener("luojia-auth-change",changed);window.removeEventListener("storage",storage);};
  },[]);
  async function upload(file:File){
    if(disabled||phase==="requesting")return;
    const validation=documentUploadError(file);if(validation){setError(validation);setPhase("failed");return;}
    const controller=new AbortController();request.current=controller;
    const owner=getCurrentUserId(),credential=getAuthHeaders().Authorization;
    const current=()=>alive.current&&!controller.signal.aborted&&owner===getCurrentUserId()&&credential===getAuthHeaders().Authorization;
    setName(file.name);setError("");setPhase("requesting");
    try{const result=await uploadTextbook(file,controller.signal);
      if(!current())return;
      if(!result.document_id||result.parse_error)throw Error("未确认解析资料已保存，请重试。");
      setPhase("success");onUploaded(result.document_id);
    }catch(e){if(current()){setPhase("failed");setError(e instanceof Error?e.message:"解析或保存未完成，请重试。");}}
  }
  return <section aria-label="导入学习资料" className="space-y-3 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-4">
    <p className="text-sm font-medium">导入资料</p>
    <p className="text-xs leading-6 text-[var(--text-secondary)]">支持 PDF、Word、PPTX，最多 200MB；PDF 最多 200 页。MinerU 解析可能需要数分钟，完成后再选择阅读、对话或生成笔记。</p>
    <input ref={input} type="file" aria-label="选择要解析的资料" accept={DOCUMENT_ACCEPT} disabled={disabled||phase==="requesting"} onChange={e=>{const file=e.target.files?.[0];e.target.value="";if(file)void upload(file);}} className="block w-full min-w-0 text-sm"/>
    {phase==="requesting"&&<p role="status" className="flex items-start gap-2 text-xs leading-6"><Loader2 className="mt-1 size-4 shrink-0 animate-spin"/>正在上传并请求解析：{name}。此页只跟踪当前请求，刷新或关闭后不再跟踪；如请求中断，请先在“我的资料”刷新检查，避免重复上传。</p>}
    {phase==="success"&&<p role="status" className="flex items-center gap-2 text-sm text-olive-700 dark:text-olive-300"><Upload className="size-4"/>{name}：原文已保存，尚未生成笔记。</p>}
    {error&&<p role="alert" className="text-sm leading-6 text-cinnabar-700 dark:text-cinnabar-300">{error} 可以重新选择文件重试；网络中断时请先检查资料列表。</p>}
  </section>;
}
