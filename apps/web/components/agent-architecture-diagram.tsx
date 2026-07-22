import {
  ArrowRight,
  BookOpenCheck,
  BrainCircuit,
  CheckCircle2,
  FileText,
  Gauge,
  MessageSquareText,
  Radar,
  Route,
  Search,
  UploadCloud,
} from "lucide-react";

const inputNodes = [
  { title: "题目对话", desc: "自然语言追问", icon: MessageSquareText },
  { title: "上传材料", desc: "图片 / PDF / Word", icon: UploadCloud },
  { title: "历史状态", desc: "会话、错题、笔记", icon: BookOpenCheck },
];

const agentNodes = [
  { title: "解题引导 Agent", desc: "题型识别、第一步规则、分步追问", icon: BrainCircuit, tone: "green" },
  { title: "校验与错因 Agent", desc: "步骤验证、误区定位、相似题生成", icon: CheckCircle2, tone: "red" },
  { title: "笔记复盘 Agent", desc: "随堂笔记、状态复盘、下一步建议", icon: FileText, tone: "green" },
  { title: "掌握度 Agent", desc: "BKT 更新、雷达图、综合趋势", icon: Radar, tone: "red" },
] as const;

function MiniNode({
  title,
  desc,
  icon: Icon,
}: {
  title: string;
  desc: string;
  icon: typeof MessageSquareText;
}) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-[#d6d0ba]/70 bg-white/50 p-4 shadow-sm backdrop-blur-sm dark:border-[#3e3f36] dark:bg-[#242421]/70">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[#617a55]/10 text-[#617a55]">
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <div className="font-title text-sm font-bold tracking-wide text-[#2a2b26] dark:text-[#e6e4dc]">{title}</div>
        <div className="mt-1 text-xs leading-relaxed text-[#757a6b] dark:text-[#a6a194]">{desc}</div>
      </div>
    </div>
  );
}

function AgentNode({
  title,
  desc,
  icon: Icon,
  tone,
}: {
  title: string;
  desc: string;
  icon: typeof BrainCircuit;
  tone: "green" | "red";
}) {
  const color = tone === "green" ? "#617a55" : "#c44a3d";
  return (
    <div className="relative rounded-lg border border-[#d6d0ba]/70 bg-[#faf7f2]/80 p-5 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md dark:border-[#3e3f36] dark:bg-[#242421]/80">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-md" style={{ backgroundColor: `${color}18`, color }}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="font-title text-base font-bold text-[#2a2b26] dark:text-[#e6e4dc]">{title}</div>
      </div>
      <p className="text-sm leading-relaxed text-[#4a4d44] dark:text-[#c5c2b6]">{desc}</p>
    </div>
  );
}

export function AgentArchitectureDiagram() {
  return (
    <section className="relative z-10 w-full border-t border-[#d6d0ba]/30 px-4 py-24 dark:border-[#3e3f36]/30">
      <div className="mx-auto max-w-6xl">
        <div className="mb-12 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.35em] text-[#617a55]">Agent Framework</p>
            <h2 className="font-title text-4xl font-bold tracking-widest text-[#2a2b26] dark:text-[#e6e4dc] sm:text-5xl">
              助教框架 / <span className="text-[#617a55]">从输入到复盘</span>
            </h2>
          </div>
          <p className="max-w-xl text-sm leading-7 text-[#757a6b] dark:text-[#a6a194]">
            系统不是单次问答，而是一条学习闭环：先收集题目和上下文，再调度不同 Agent 协作，最后把解题过程沉淀到掌握度、笔记和下一步建议里。
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_auto_1.2fr_auto_1fr] lg:items-center">
          <div className="space-y-3">
            <div className="mb-3 flex items-center gap-2 text-sm font-bold text-[#617a55]">
              <Search className="h-4 w-4" />
              输入与上下文
            </div>
            {inputNodes.map((node) => (
              <MiniNode key={node.title} {...node} />
            ))}
          </div>

          <div className="hidden items-center justify-center text-[#617a55] lg:flex">
            <ArrowRight className="h-8 w-8" />
          </div>

          <div className="rounded-lg border border-[#617a55]/30 bg-[#617a55]/10 p-5 shadow-sm backdrop-blur-sm">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <div className="font-title text-xl font-bold text-[#2a2b26] dark:text-[#e6e4dc]">条件调度中枢</div>
                <div className="mt-1 text-xs text-[#757a6b] dark:text-[#a6a194]">Fast Context + Policy Router + Tutor Graph</div>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-md bg-[#617a55] text-[#faf7f2]">
                <Route className="h-6 w-6" />
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {["秒级开场", "检索上下文", "按需调用"].map((item) => (
                <div key={item} className="rounded-md border border-white/50 bg-white/50 px-3 py-2 text-center text-xs font-bold text-[#617a55] dark:border-[#3e3f36] dark:bg-[#1e1e1b]/40">
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="hidden items-center justify-center text-[#c44a3d] lg:flex">
            <ArrowRight className="h-8 w-8" />
          </div>

          <div>
            <div className="mb-3 flex items-center gap-2 text-sm font-bold text-[#c44a3d]">
              <Gauge className="h-4 w-4" />
              协作 Agent
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              {agentNodes.map((node) => (
                <AgentNode key={node.title} {...node} />
              ))}
            </div>
          </div>
        </div>

        <div className="mt-8 rounded-lg border border-[#d6d0ba]/70 bg-white/45 px-5 py-4 text-center text-sm leading-7 text-[#4a4d44] shadow-sm backdrop-blur-sm dark:border-[#3e3f36] dark:bg-[#242421]/60 dark:text-[#c5c2b6]">
          输出闭环：第一步提示 → 分步解题 → 错因复盘 → 随堂笔记 → 掌握度雷达 → 下一轮学习建议
        </div>
      </div>
    </section>
  );
}
