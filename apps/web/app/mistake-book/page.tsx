"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, BookOpen, AlertCircle, Plus, X, Flame, Printer } from "lucide-react";
import { listUserMistakes, addMistake, generateQuiz, createSession } from "@/lib/api";
import { KnowledgeGraph } from "@/components/knowledge-graph";

export default function MistakeBookPage() {
  const router = useRouter();
  const [mistakes, setMistakes] = useState<Array<{ id?: string, mistake_code: string; concept: string; subject: string; created_at: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [generatingFor, setGeneratingFor] = useState<string | null>(null);
  const [formData, setFormData] = useState({ subject: "foundations", mistake_code: "", concept: "" });
  const [activeTab, setActiveTab] = useState<"list" | "tree">("list");

  const refresh = () => {
    setLoading(true);
    listUserMistakes("demo-user")
      .then(setMistakes)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const handleGenerateQuiz = async (mistake: any) => {
    if (!mistake.id) return alert("只支持系统自动生成的错题记录");
    try {
      setGeneratingFor(mistake.id);
      // 1. Generate quiz content
      const { quiz_content } = await generateQuiz("demo-user", mistake.id);
      // 2. Create new session
      const { session_id } = await createSession(mistake.subject as any);
      // 3. (Optional) pre-fill the quiz by fetching stream (or just we send the quiz to the LLM backend directly in a message)
      // We can just open the chat with a URL param or something, but the easiest is to just navigate. 
      // The backend actually just gave us the prompt. Let's encode it in the URL so the chat page can auto-send it.
      // Or we can save it as an initial system message.
      // Wait, we don't have an addMessage frontend api exposed that takes raw content easily without stream.
      // Let's just pass it via localStorage for the chat to pick up, or URL param `?initialPrompt=...`
      sessionStorage.setItem("pendingQuiz", quiz_content);
      
      router.push(`/chat?sessionId=${session_id}`);
    } catch (e) {
      console.error(e);
      alert("生成练习题失败");
    } finally {
      setGeneratingFor(null);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] transition-colors duration-300">
      <header className="sticky top-0 z-10 flex h-16 items-center border-b border-[var(--border-primary)] bg-[var(--bg-header)] px-4 sm:px-6 backdrop-blur-md">
        <Link href="/" className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
          <ArrowLeft className="w-4 h-4" />
          返回学习
        </Link>
        <div className="ml-auto flex items-center gap-4">
          <button onClick={() => window.print()} className="print:hidden flex items-center gap-1.5 text-xs font-bold bg-[#faf7f2] dark:bg-[#2a2b26] hover:bg-[#e3dec9] dark:hover:bg-[#33342d] border border-[#d6d0ba] dark:border-[#3e3f36] px-3 py-1.5 rounded-md transition-colors text-[#2a2b26] dark:text-[#e6e4dc]">
            <Printer className="w-3.5 h-3.5" /> 导出/打印
          </button>
          <button onClick={() => setIsAdding(true)} className="print:hidden flex items-center gap-1.5 text-xs font-bold bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] border border-[var(--border-primary)] px-3 py-1.5 rounded-md transition-colors text-[var(--text-primary)]">
            <Plus className="w-3.5 h-3.5" /> 手动添加
          </button>
          <div className="flex items-center gap-2 font-bold tracking-widest uppercase">
            <BookOpen className="w-4 h-4 text-rose-500" />
            <span className="hidden sm:inline">错题本 (Mistake Book)</span>
          </div>
        </div>
      </header>
      
      <main className="max-w-4xl mx-auto py-12 px-4 sm:px-6">
        <div className="mb-10 text-center">
          <h1 className="text-3xl font-bold mb-4 font-mono">
            LOGIC <span className="text-rose-500">DEVIATIONS</span>
          </h1>
          <p className="text-[var(--text-muted)] text-sm max-w-lg mx-auto leading-relaxed mb-8">
            Every mistake is an opportunity to refine the architecture of your mathematical understanding. Review your past deviations here.
          </p>

          <div className="flex justify-center mb-8">
            <div className="flex items-center gap-1 bg-[var(--bg-tertiary)] p-1 rounded-xl border border-[var(--border-subtle)]">
              <button 
                onClick={() => setActiveTab("list")}
                className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === "list" ? "bg-[var(--bg-card)] shadow-sm text-rose-500" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
              >
                错题追踪
              </button>
              <button 
                onClick={() => setActiveTab("tree")}
                className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === "tree" ? "bg-[var(--bg-card)] shadow-sm text-cyan-500" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
              >
                技能树谱
              </button>
            </div>
          </div>
        </div>

        {activeTab === "tree" ? (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <KnowledgeGraph />
          </div>
        ) : loading ? (
          <div className="flex justify-center p-12">
            <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : mistakes.length === 0 ? (
          <div className="text-center p-12 border border-dashed border-[var(--border-primary)] rounded-xl bg-[var(--bg-tertiary)]">
            <p className="text-[var(--text-muted)]">No recorded deviations yet.</p>
          </div>
        ) : (
          <div className="relative border-l border-[var(--border-primary)] ml-3 md:ml-6 space-y-8 pb-12">
            {mistakes.map((mistake, index) => (
              <div key={`${mistake.mistake_code}-${index}`} className="relative pl-6 md:pl-8 group print:break-inside-avoid print:mb-24">
                <div className="absolute -left-1.5 top-2 w-3 h-3 rounded-full bg-[var(--bg-primary)] border-2 border-rose-500 transition-colors group-hover:bg-rose-500 print:hidden" />
                <div className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] p-5 shadow-sm transition-all duration-300 hover:shadow-md hover:border-rose-500/30 group-hover:-translate-y-1 print:border-black print:shadow-none print:transform-none">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold px-2 py-1 bg-[var(--bg-tertiary)] text-[var(--text-secondary)] uppercase tracking-wider rounded-md border border-[var(--border-subtle)]">
                        {mistake.subject}
                      </span>
                      <span className="text-xs font-bold text-rose-500 uppercase tracking-widest flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" />
                        {mistake.mistake_code}
                      </span>
                    </div>
                    <time className="text-xs text-[var(--text-muted)] font-mono">
                      {new Date(mistake.created_at).toLocaleString()}
                    </time>
                  </div>
                  <h3 className="text-lg font-bold mb-2 print:text-black">
                    {mistake.concept || mistake.mistake_code}
                  </h3>
                  
                  {/* Print spacing block for student to write notes offline */}
                  <div className="hidden print:block h-32 border-t border-dashed border-gray-300 mt-4 pt-2 text-xs text-gray-400">
                    复盘与推导区域 / Notes:
                  </div>

                  <div className="flex items-center mt-4 print:hidden">
                    <button 
                      onClick={() => handleGenerateQuiz(mistake)}
                      disabled={generatingFor === mistake.id}
                      className="text-sm font-medium text-[#c44a3d] hover:text-[#a0362b] dark:text-[#c44a3d] transition-colors flex items-center gap-1.5 border border-[#c44a3d]/20 bg-[#c44a3d]/5 px-3 py-1.5 rounded-full"
                    >
                      {generatingFor === mistake.id ? (
                        <div className="w-4 h-4 border-2 border-[#c44a3d] border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Flame className="w-4 h-4" />
                      )}
                      举一反三 (生成练习)
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {isAdding && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="flex justify-between items-center p-4 border-b border-[var(--border-primary)]">
              <h3 className="font-bold text-[var(--text-primary)]">手动添加错题</h3>
              <button onClick={() => setIsAdding(false)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">场景 (Subject)</label>
                <select 
                  className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-md px-3 py-2 text-sm text-[var(--text-primary)] outline-none focus:border-cyan-500"
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                >
                  <option value="calculus">高等数学</option>
                  <option value="linear_algebra">线性代数</option>
                  <option value="probability">概率论与数统</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">错误名称 / 代码 (Mistake Code)</label>
                <input 
                  type="text" 
                  placeholder="例如: 积分常数遗漏"
                  className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-md px-3 py-2 text-sm text-[var(--text-primary)] outline-none focus:border-rose-500"
                  value={formData.mistake_code}
                  onChange={(e) => setFormData({ ...formData, mistake_code: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">关联知识点 (Concept)</label>
                <input 
                  type="text" 
                  placeholder="例如: 不定积分"
                  className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-md px-3 py-2 text-sm text-[var(--text-primary)] outline-none focus:border-cyan-500"
                  value={formData.concept}
                  onChange={(e) => setFormData({ ...formData, concept: e.target.value })}
                />
              </div>
            </div>
            <div className="p-4 border-t border-[var(--border-primary)] bg-[var(--bg-tertiary)] flex justify-end gap-2">
              <button onClick={() => setIsAdding(false)} className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
                取消
              </button>
              <button 
                onClick={() => {
                  if (!formData.mistake_code) return;
                  addMistake("demo-user", formData).then(() => {
                    setIsAdding(false);
                    setFormData({ subject: "foundations", mistake_code: "", concept: "" });
                    refresh();
                  });
                }} 
                className="px-4 py-2 text-sm font-medium bg-rose-500 text-white rounded-md hover:bg-rose-600 transition-colors shadow-sm"
              >
                保存记录
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ArrowRight(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  );
}
