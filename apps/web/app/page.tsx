"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, PenTool, Lightbulb, Target, Quote, FileText, Printer, Video, LineChart, BrainCircuit } from "lucide-react";
import { motion } from "framer-motion";
import { ParticleField } from "@/components/particle-field";
import { LiveSandbox } from "@/components/live-sandbox";

const MARQUEE_CONCEPTS = [
  "洛必达法则", "泰勒公式", "特征值与特征向量", "正态分布", "全概率公式与贝叶斯公式",
  "实对称矩阵的对角化", "函数的极值与导数", "斯托克斯公式", "隐函数求导", "方向导数与梯度",
  "离散型随机变量", "二重积分在极坐标下的计算", "同底数幂的乘法", "解直角三角形",
  "最大似然估计法", "复数的四则运算", "中心对称与中心对称图形", "抛物线的简单几何性质"
];

export default function SplashPage() {
  const [mounted, setMounted] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Simulate auth state checking
    if (localStorage.getItem("mock_auth_token")) {
      setIsLoggedIn(true);
    }
  }, []);

  if (!mounted) return null;

  const fadeUpVariants = {
    hidden: { opacity: 0, y: 40 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 20 } }
  } as const;

  const staggerContainer = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2,
      }
    }
  } as const;

  return (
    <div className="relative flex flex-col w-full min-h-screen bg-[#faf7f2] dark:bg-[#1e1e1b] text-[#2a2b26] dark:text-[#e6e4dc] selection:bg-[#617a55]/30">
      {/* FIXED INK WASH BACKGROUND ELEMENTS */}
      <div className="fixed inset-0 z-0 opacity-40 pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[800px] h-[800px] bg-[#617a55] rounded-full mix-blend-multiply dark:mix-blend-lighten filter blur-[150px] opacity-20" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-[#c44a3d] rounded-full mix-blend-multiply dark:mix-blend-lighten filter blur-[150px] opacity-10" />
        <div className="absolute top-1/2 left-1/2 w-[1000px] h-[1000px] bg-[#d6d0ba] dark:bg-[#3e3f36] rounded-full filter blur-[120px] opacity-20 transform -translate-x-1/2 -translate-y-1/2" />
        
        {/* Subtle bamboo/rice paper texture */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noise%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.05%22 numOctaves=%222%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noise)%22 opacity=%220.05%22/%3E%3C/svg%3E')] opacity-30" />
        
        {/* Interactive 3D Math Particle Field */}
        <ParticleField />
      </div>

      {/* TOP NAVIGATION */}
      <motion.nav 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="absolute top-0 left-0 right-0 z-50 flex items-center justify-between px-6 sm:px-12 py-8"
      >
        <div className="text-[#617a55] font-title font-bold text-xl tracking-widest flex items-center gap-2 opacity-80">
          <BookOpen className="w-5 h-5" />
          <span>珞珈数智</span>
        </div>
        <div className="flex items-center gap-6">
          {isLoggedIn ? (
            <Link href="/chat" className="px-6 py-2 text-sm font-title tracking-widest bg-[#617a55] text-[#faf7f2] hover:bg-transparent hover:text-[#617a55] dark:hover:text-[#879f7a] border border-[#617a55] rounded-full transition-all shadow-sm">
              进入学习系统 (Enter)
            </Link>
          ) : (
            <>
              <button 
                onClick={() => { localStorage.setItem("mock_auth_token", "true"); setIsLoggedIn(true); }} 
                className="text-sm font-title tracking-widest text-[#4a4d44] dark:text-[#c5c2b6] hover:text-[#617a55] dark:hover:text-[#879f7a] transition-colors"
              >
                登 录 (Login)
              </button>
              <button 
                onClick={() => { localStorage.setItem("mock_auth_token", "true"); setIsLoggedIn(true); }}
                className="px-6 py-2 text-sm font-title tracking-widest bg-[#617a55] text-[#faf7f2] hover:bg-transparent hover:text-[#617a55] dark:hover:text-[#879f7a] border border-[#617a55] rounded-full transition-all shadow-sm"
              >
                注 册 (Register)
              </button>
            </>
          )}
        </div>
      </motion.nav>

      {/* HERO SECTION */}
      <section className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4 py-20">
        <motion.div 
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          className="flex flex-col items-center text-center w-full max-w-6xl mx-auto"
        >
          <motion.div variants={fadeUpVariants} className="mb-4">
            <BookOpen className="w-12 h-12 text-[#617a55] mx-auto opacity-80" />
          </motion.div>
          
          <motion.h1 variants={fadeUpVariants} className="text-5xl sm:text-7xl font-bold tracking-widest mb-6 font-title text-[#2a2b26] dark:text-[#e6e4dc]">
            <span className="block mb-4">珞珈数智助教</span>
            <span className="block text-3xl sm:text-4xl text-[#617a55] tracking-widest">Luojia Math Tutor</span>
          </motion.h1>
          
          <motion.p variants={fadeUpVariants} className="max-w-xl text-lg font-body text-[#4a4d44] dark:text-[#c5c2b6] mb-16 leading-loose px-4">
            在自然与逻辑的交汇处，以东方美学重塑数学之美。
            探寻数理的本源，开启智慧的启迪。
          </motion.p>

          <motion.div variants={fadeUpVariants} className="grid grid-cols-1 sm:grid-cols-2 gap-8 mb-16 max-w-4xl w-full text-left">
            {/* Feature 1 */}
            <div className="relative group flex flex-col space-y-3 border border-[#d6d0ba] dark:border-[#3e3f36] bg-white/40 dark:bg-[#242421]/60 p-8 hover:border-[#617a55] transition-all rounded-lg overflow-hidden backdrop-blur-md">
              <div className="absolute top-4 right-4 text-4xl text-[#617a55] opacity-10 font-title">壹</div>
              <h3 className="text-[#617a55] font-title font-bold text-2xl tracking-wide">启发式教学</h3>
              <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] font-body tracking-widest">Socratic Heuristics</p>
              <p className="text-sm text-[#4a4d44] dark:text-[#c5c2b6] mt-4 leading-relaxed font-body">
                不直接提供答案，而是以苏格拉底式的提问引导思考。在问答之间，培养真正的数学直觉与逻辑深度。
              </p>
            </div>
            {/* Feature 2 */}
            <div className="relative group flex flex-col space-y-3 border border-[#d6d0ba] dark:border-[#3e3f36] bg-white/40 dark:bg-[#242421]/60 p-8 hover:border-[#617a55] transition-all rounded-lg overflow-hidden backdrop-blur-md">
              <div className="absolute top-4 right-4 text-4xl text-[#617a55] opacity-10 font-title">贰</div>
              <h3 className="text-[#617a55] font-title font-bold text-2xl tracking-wide">自动错题本</h3>
              <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] font-body tracking-widest">Auto Mistake Book</p>
              <p className="text-sm text-[#4a4d44] dark:text-[#c5c2b6] mt-4 leading-relaxed font-body">
                智能捕捉推导中的谬误，并自动记录成册。温故而知新，避免在同样的逻辑迷宫中徘徊。
              </p>
            </div>
            {/* Feature 3 */}
            <div className="relative group flex flex-col space-y-3 border border-[#d6d0ba] dark:border-[#3e3f36] bg-white/40 dark:bg-[#242421]/60 p-8 hover:border-[#617a55] transition-all rounded-lg overflow-hidden backdrop-blur-md">
              <div className="absolute top-4 right-4 text-4xl text-[#617a55] opacity-10 font-title">叁</div>
              <h3 className="text-[#617a55] font-title font-bold text-2xl tracking-wide">动态可视化</h3>
              <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] font-body tracking-widest">Dynamic Visualization</p>
              <p className="text-sm text-[#4a4d44] dark:text-[#c5c2b6] mt-4 leading-relaxed font-body">
                抽象的几何与代数在水墨氤氲中徐徐展开。通过动态可视化的渲染，让复杂的数学结构呈现出独有的灵动与韵味。
              </p>
            </div>
            {/* Feature 4 */}
            <div className="relative group flex flex-col space-y-3 border border-[#d6d0ba] dark:border-[#3e3f36] bg-white/40 dark:bg-[#242421]/60 p-8 hover:border-[#617a55] transition-all rounded-lg overflow-hidden backdrop-blur-md">
              <div className="absolute top-4 right-4 text-4xl text-[#617a55] opacity-10 font-title">肆</div>
              <h3 className="text-[#617a55] font-title font-bold text-2xl tracking-wide">多模型基座</h3>
              <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] font-body tracking-widest">Multi-Model Architecture</p>
              <p className="text-sm text-[#4a4d44] dark:text-[#c5c2b6] mt-4 leading-relaxed font-body">
                集百家之长，汇聚多种AI模型的智慧。在后台默契配合，为你提供最精准、多维度的学情推演。
              </p>
            </div>
          </motion.div>
          
          <motion.div variants={fadeUpVariants}>
            {isLoggedIn ? (
              <Link 
                href="/chat" 
                className="group relative inline-flex h-14 items-center justify-center overflow-hidden border border-[#617a55] bg-transparent px-10 font-title text-xl text-[#617a55] transition-all hover:bg-[#617a55] hover:text-[#faf7f2] rounded-md shadow-sm"
              >
                <span className="mr-3">进入系统 (Enter)</span>
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Link>
            ) : (
              <button 
                onClick={() => { localStorage.setItem("mock_auth_token", "true"); setIsLoggedIn(true); }}
                className="group relative inline-flex h-14 items-center justify-center overflow-hidden border border-[#617a55] bg-transparent px-10 font-title text-xl text-[#617a55] transition-all hover:bg-[#617a55] hover:text-[#faf7f2] rounded-md shadow-sm"
              >
                <span className="mr-3">启程 (Initialize)</span>
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </button>
            )}
          </motion.div>

          <motion.div variants={fadeUpVariants} className="w-full mt-12">
            <LiveSandbox />
          </motion.div>
        </motion.div>

        {/* Decorative vertical text (Hero) */}
        <div 
          className="hidden md:block absolute left-8 top-1/4 text-2xl font-title text-[#2a2b26] dark:text-[#e6e4dc] opacity-20 tracking-[1em]"
          style={{ writingMode: 'vertical-rl' }}
        >
          格物致知，知行合一。
        </div>

        {/* INFINITE MARQUEE */}
        <div className="absolute bottom-12 left-0 w-full overflow-hidden whitespace-nowrap opacity-[0.07] dark:opacity-10 pointer-events-none select-none flex mask-image-gradient">
          <div className="animate-marquee flex gap-16 text-3xl sm:text-5xl font-title text-[#617a55] dark:text-[#e6e4dc]">
            {[...MARQUEE_CONCEPTS, ...MARQUEE_CONCEPTS].map((concept, i) => (
              <span key={i} className="inline-block hover:text-[#c44a3d] transition-colors duration-300">{concept}</span>
            ))}
          </div>
        </div>
      </section>
      {/* SECTION 0.5: EPIC UPGRADES (四大史诗级升级) */}
      <section className="relative z-10 w-full py-24 px-4 bg-[#617a55]/5 dark:bg-[#617a55]/10 border-t border-[#d6d0ba]/30 dark:border-[#3e3f36]/30">
        <div className="max-w-6xl mx-auto">
          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="text-center mb-16"
          >
            <motion.h2 variants={fadeUpVariants} className="text-4xl sm:text-5xl font-bold tracking-widest font-title text-[#2a2b26] dark:text-[#e6e4dc] mb-4">
              史诗进化 / <span className="text-[#617a55]">全新纪元</span>
            </motion.h2>
            <motion.p variants={fadeUpVariants} className="text-lg font-body text-[#757a6b] dark:text-[#8d8a7d]">
              突破维度的四大全新能力，重塑数字学习的交互边界。
            </motion.p>
          </motion.div>

          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={staggerContainer}
            className="grid grid-cols-1 md:grid-cols-2 gap-8 relative"
          >
            {/* Upgrade 1 */}
            <motion.div variants={fadeUpVariants} className="group flex items-start gap-4 p-6 bg-white/40 dark:bg-[#242421]/60 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 rounded-lg hover:border-[#617a55] transition-all backdrop-blur-sm">
              <div className="w-12 h-12 shrink-0 rounded-full bg-[#617a55]/10 flex items-center justify-center">
                <Video className="w-6 h-6 text-[#617a55]" />
              </div>
              <div>
                <h3 className="text-xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">语音伴读 (Voice TTS)</h3>
                <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed">
                  通过正则表达式无损过滤数学公式代码，调用原生接口带来沉浸式的女声流利朗读，让枯燥的推导变得生动。
                </p>
              </div>
            </motion.div>

            {/* Upgrade 2 */}
            <motion.div variants={fadeUpVariants} className="group flex items-start gap-4 p-6 bg-white/40 dark:bg-[#242421]/60 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 rounded-lg hover:border-[#c44a3d] transition-all backdrop-blur-sm">
              <div className="w-12 h-12 shrink-0 rounded-full bg-[#c44a3d]/10 flex items-center justify-center">
                <FileText className="w-6 h-6 text-[#c44a3d]" />
              </div>
              <div>
                <h3 className="text-xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">随堂笔记 (Notes Agent)</h3>
                <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed">
                  一键从散乱的对话中提炼出结构化的核心考点、推导过程与易错陷阱，并支持原生排版打印与PDF导出。
                </p>
              </div>
            </motion.div>

            {/* Upgrade 3 */}
            <motion.div variants={fadeUpVariants} className="group flex items-start gap-4 p-6 bg-white/40 dark:bg-[#242421]/60 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 rounded-lg hover:border-[#617a55] transition-all backdrop-blur-sm">
              <div className="w-12 h-12 shrink-0 rounded-full bg-[#617a55]/10 flex items-center justify-center">
                <Quote className="w-6 h-6 text-[#617a55]" />
              </div>
              <div>
                <h3 className="text-xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">理科键盘 (Math Keyboard)</h3>
                <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed">
                  全面进化的虚拟符号面板，微积分、希腊字母一应俱全。告别复杂的代码输入，实现所见即所得的极客输入体验。
                </p>
              </div>
            </motion.div>

            {/* Upgrade 4 */}
            <motion.div variants={fadeUpVariants} className="group flex items-start gap-4 p-6 bg-white/40 dark:bg-[#242421]/60 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 rounded-lg hover:border-[#c44a3d] transition-all backdrop-blur-sm">
              <div className="w-12 h-12 shrink-0 rounded-full bg-[#c44a3d]/10 flex items-center justify-center">
                <BrainCircuit className="w-6 h-6 text-[#c44a3d]" />
              </div>
              <div>
                <h3 className="text-xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">动态技能树 (Knowledge Graph)</h3>
                <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed">
                  错题本不再是冰冷的列表，而是跨越三大知识谱系的23个核心节点技能树。结合游戏化理念点亮属于你的数理世界观。
                </p>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* SECTION 1: WORKFLOW (学习之境 / 耕读流转) */}
      <section className="relative z-10 w-full py-24 px-4 border-t border-[#d6d0ba]/30 dark:border-[#3e3f36]/30">
        <div className="max-w-5xl mx-auto">
          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="text-center mb-16"
          >
            <motion.h2 variants={fadeUpVariants} className="text-4xl sm:text-5xl font-bold tracking-widest font-title text-[#2a2b26] dark:text-[#e6e4dc] mb-4">
              学习之境 / <span className="text-[#617a55]">耕读流转</span>
            </motion.h2>
            <motion.p variants={fadeUpVariants} className="text-lg font-body text-[#757a6b] dark:text-[#8d8a7d]">
              循序渐进，道法自然。在这里，解题不仅是计算，更是一场思想的远足。
            </motion.p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <motion.div 
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUpVariants}
              className="flex flex-col items-center text-center p-8 bg-white/30 dark:bg-[#242421]/40 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 rounded-lg backdrop-blur-sm"
            >
              <div className="w-16 h-16 rounded-full bg-[#617a55]/10 flex items-center justify-center mb-6">
                <PenTool className="w-8 h-8 text-[#617a55]" />
              </div>
              <h4 className="text-2xl font-title font-bold mb-2">一、抛砖引玉</h4>
              <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] mb-4 tracking-widest uppercase">Ask a question</p>
              <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body leading-relaxed">
                投石问路，将心中的疑惑和难以理清的乱绪倾注于此。无论是微积分的涟漪还是线性空间的迷雾，皆可作发端。
              </p>
            </motion.div>

            <motion.div 
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUpVariants}
              className="flex flex-col items-center text-center p-8 bg-white/30 dark:bg-[#242421]/40 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 rounded-lg backdrop-blur-sm"
            >
              <div className="w-16 h-16 rounded-full bg-[#617a55]/10 flex items-center justify-center mb-6">
                <Lightbulb className="w-8 h-8 text-[#617a55]" />
              </div>
              <h4 className="text-2xl font-title font-bold mb-2">二、抽丝剥茧</h4>
              <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] mb-4 tracking-widest uppercase">Socratic Dialogue</p>
              <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body leading-relaxed">
                助教不予现成之答，而是步步为营，循循善诱。于思维的交锋与诘问中，理清脉络，剥去繁杂，得见真章。
              </p>
            </motion.div>

            <motion.div 
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUpVariants}
              className="flex flex-col items-center text-center p-8 bg-white/30 dark:bg-[#242421]/40 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 rounded-lg backdrop-blur-sm"
            >
              <div className="w-16 h-16 rounded-full bg-[#617a55]/10 flex items-center justify-center mb-6">
                <Target className="w-8 h-8 text-[#617a55]" />
              </div>
              <h4 className="text-2xl font-title font-bold mb-2">三、水到渠成</h4>
              <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] mb-4 tracking-widest uppercase">Mastery</p>
              <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body leading-relaxed">
                豁然开朗，洞悉本质。知识的碎片在此刻拼凑成完整的画卷。错题亦如秋叶归根，化作来年新知的养分。
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* SECTION 1.5: USAGE GUIDE (使用指南 / 游园指南) */}
      <section className="relative z-10 w-full py-24 px-4 bg-[#617a55]/5 dark:bg-[#617a55]/10 border-t border-[#d6d0ba]/30 dark:border-[#3e3f36]/30">
        <div className="max-w-6xl mx-auto">
          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="text-center mb-16"
          >
            <motion.h2 variants={fadeUpVariants} className="text-4xl sm:text-5xl font-bold tracking-widest font-title text-[#2a2b26] dark:text-[#e6e4dc] mb-4">
              使用指南 / <span className="text-[#617a55]">游园指南</span>
            </motion.h2>
            <motion.p variants={fadeUpVariants} className="text-lg font-body text-[#757a6b] dark:text-[#8d8a7d]">
              四步踏入数理之境，让思维在引导中自由生长。
            </motion.p>
          </motion.div>

          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={staggerContainer}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative"
          >
            {/* Guide 1 */}
            <motion.div variants={fadeUpVariants} className="group relative bg-white/60 dark:bg-[#242421]/80 border border-[#d6d0ba] dark:border-[#3e3f36] p-8 hover:-translate-y-2 hover:shadow-xl transition-all duration-300 rounded-lg overflow-hidden backdrop-blur-md">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#617a55] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="text-7xl font-title text-[#617a55] opacity-10 absolute -right-2 -bottom-6 group-hover:scale-110 transition-transform">1</div>
              <h3 className="text-xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">叩问 (Query)</h3>
              <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed relative z-10">
                无论是高数极限的迷思，还是解析几何的困局，直接抛出你的疑问。甚至是一张模糊的草稿图片。
              </p>
            </motion.div>

            {/* Guide 2 */}
            <motion.div variants={fadeUpVariants} className="group relative bg-white/60 dark:bg-[#242421]/80 border border-[#d6d0ba] dark:border-[#3e3f36] p-8 hover:-translate-y-2 hover:shadow-xl transition-all duration-300 rounded-lg overflow-hidden backdrop-blur-md">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#c44a3d] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="text-7xl font-title text-[#c44a3d] opacity-[0.07] absolute -right-2 -bottom-6 group-hover:scale-110 transition-transform">2</div>
              <h3 className="text-xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">对弈 (Dialogue)</h3>
              <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed relative z-10">
                不要期待直接的答案。系统将通过反问与提示，引导你自行发现破局的线索，享受顿悟的快感。
              </p>
            </motion.div>

            {/* Guide 3 */}
            <motion.div variants={fadeUpVariants} className="group relative bg-white/60 dark:bg-[#242421]/80 border border-[#d6d0ba] dark:border-[#3e3f36] p-8 hover:-translate-y-2 hover:shadow-xl transition-all duration-300 rounded-lg overflow-hidden backdrop-blur-md">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#617a55] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="text-7xl font-title text-[#617a55] opacity-10 absolute -right-2 -bottom-6 group-hover:scale-110 transition-transform">3</div>
              <h3 className="text-xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">观象 (Visualize)</h3>
              <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed relative z-10">
                当文字难以名状，系统会实时渲染出精美的数学公式与动态几何图形，让抽象的数理跃然纸上。
              </p>
            </motion.div>

            {/* Guide 4 */}
            <motion.div variants={fadeUpVariants} className="group relative bg-white/60 dark:bg-[#242421]/80 border border-[#d6d0ba] dark:border-[#3e3f36] p-8 hover:-translate-y-2 hover:shadow-xl transition-all duration-300 rounded-lg overflow-hidden backdrop-blur-md">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#c44a3d] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="text-7xl font-title text-[#c44a3d] opacity-[0.07] absolute -right-2 -bottom-6 group-hover:scale-110 transition-transform">4</div>
              <h3 className="text-xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">借力 (Fallback)</h3>
              <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed relative z-10">
                若仍感迷茫，只需对助教说“推荐讲解视频”，即可从 200+ 核心微观小节库中，秒刷全网最顶级的教学名师视频。
              </p>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* SECTION 2: SUBJECTS (数理领域 / 兼容并蓄) */}
      <section className="relative z-10 w-full py-24 px-4 bg-[#f2efe8]/30 dark:bg-[#1a1a18]/30 border-y border-[#d6d0ba]/30 dark:border-[#3e3f36]/30 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto">
          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="text-center mb-16"
          >
            <motion.h2 variants={fadeUpVariants} className="text-4xl sm:text-5xl font-bold tracking-widest font-title text-[#2a2b26] dark:text-[#e6e4dc] mb-4">
              数理领域 / <span className="text-[#617a55]">兼容并蓄</span>
            </motion.h2>
            <motion.p variants={fadeUpVariants} className="text-lg font-body text-[#757a6b] dark:text-[#8d8a7d]">
              涵盖大学核心数理学科，从极限的微末到多维矩阵的浩瀚。
            </motion.p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <motion.div 
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUpVariants}
              className="group relative flex flex-col p-8 bg-white/50 dark:bg-[#242421]/60 border-l-4 border-[#617a55] shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="text-2xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-3">基础概念</h3>
              <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] mb-4 uppercase tracking-wider">Foundations</p>
              <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-loose">
                无论是高数中的极限与连续，还是线代中的向量空间，助教将以生动形象的类比，带你跨过入门的门槛。
              </p>
            </motion.div>
            
            <motion.div 
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUpVariants}
              className="group relative flex flex-col p-8 bg-white/50 dark:bg-[#242421]/60 border-l-4 border-[#c44a3d] shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="text-2xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-3">深度推导</h3>
              <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] mb-4 uppercase tracking-wider">Derivations</p>
              <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-loose">
                从泰勒展开的严密推证，到概率论中大数定律的深刻洞见。陪伴你在定理的丛林中拨开荆棘，领略逻辑之美。
              </p>
            </motion.div>

            <motion.div 
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUpVariants}
              className="group relative flex flex-col p-8 bg-white/50 dark:bg-[#242421]/60 border-l-4 border-[#d6d0ba] dark:border-[#5a5c53] shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="text-2xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-3">实战解题</h3>
              <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] mb-4 uppercase tracking-wider">Problem Solving</p>
              <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-loose">
                将抽象理论应用于实际计算。特征值与特征向量的求解、多重积分的坐标变换，助教为你拆解繁杂的计算步骤。
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* SECTION 2.5: MODES (学习模式 / 因材施教) */}
      <section className="relative z-10 w-full py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="text-center mb-16"
          >
            <motion.h2 variants={fadeUpVariants} className="text-4xl sm:text-5xl font-bold tracking-widest font-title text-[#2a2b26] dark:text-[#e6e4dc] mb-4">
              学习模式 / <span className="text-[#617a55]">因材施教</span>
            </motion.h2>
            <motion.p variants={fadeUpVariants} className="text-lg font-body text-[#757a6b] dark:text-[#8d8a7d]">
              三种对话心法，随心切换，满足不同场景的求知诉求。
            </motion.p>
          </motion.div>

          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={staggerContainer}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {/* Mode 1: Socratic */}
            <motion.div variants={fadeUpVariants} className="group overflow-hidden rounded-xl bg-white/40 dark:bg-[#242421]/50 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 hover:border-[#617a55] transition-colors backdrop-blur-sm">
              <div className="h-32 bg-[#617a55]/10 flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9IiM2MTdhNTUiIGZpbGwtb3BhY2l0eT0iMC4yIi8+PC9zdmc+')] opacity-50"></div>
                <Lightbulb className="w-12 h-12 text-[#617a55] relative z-10 group-hover:scale-110 transition-transform duration-500" />
              </div>
              <div className="p-8">
                <h3 className="text-2xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">启发式教学</h3>
                <p className="text-xs text-[#617a55] mb-4 tracking-widest uppercase font-bold">Socratic Mode</p>
                <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed">
                  默认核心模式。拒绝直接投喂答案，通过苏格拉底式的不断追问，帮你剥茧抽丝，建立底层的数学直觉。适合预习与深度探究。
                </p>
              </div>
            </motion.div>

            {/* Mode 2: Direct */}
            <motion.div variants={fadeUpVariants} className="group overflow-hidden rounded-xl bg-white/40 dark:bg-[#242421]/50 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 hover:border-[#c44a3d] transition-colors backdrop-blur-sm">
              <div className="h-32 bg-[#c44a3d]/10 flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCI+PHBvbHlnb24gcG9pbnRzPSIwLDIwIDIwLDAgMCwwIiBmaWxsPSIjYzQ0YTNkIiBmaWxsLW9wYWNpdHk9IjAuMSIvPjwvc3ZnPg==')] opacity-50"></div>
                <Target className="w-12 h-12 text-[#c44a3d] relative z-10 group-hover:scale-110 transition-transform duration-500" />
              </div>
              <div className="p-8">
                <h3 className="text-2xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">直接解答</h3>
                <p className="text-xs text-[#c44a3d] mb-4 tracking-widest uppercase font-bold">Direct Mode</p>
                <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed">
                  直奔主题，快速突击。当你面临期末考试前的冲刺，或是需要快速核对繁杂的计算步骤时，一键获取严谨详尽的完整解答。
                </p>
              </div>
            </motion.div>

            {/* Mode 3: Practice */}
            <motion.div variants={fadeUpVariants} className="group overflow-hidden rounded-xl bg-white/40 dark:bg-[#242421]/50 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 hover:border-[#d6d0ba] dark:hover:border-[#8d8a7d] transition-colors backdrop-blur-sm">
              <div className="h-32 bg-[#d6d0ba]/30 dark:bg-[#3e3f36]/50 flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCI+PHJlY3Qgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiBmaWxsPSIjZDZkMGJhIiBmaWxsLW9wYWNpdHk9IjAuNCIvPjwvc3ZnPg==')] opacity-50"></div>
                <PenTool className="w-12 h-12 text-[#757a6b] dark:text-[#c5c2b6] relative z-10 group-hover:scale-110 transition-transform duration-500" />
              </div>
              <div className="p-8">
                <h3 className="text-2xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">刷题模式</h3>
                <p className="text-xs text-[#757a6b] dark:text-[#8d8a7d] mb-4 tracking-widest uppercase font-bold">Practice Mode</p>
                <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed">
                  举一反三，温故知新。基于你当前的错题薄与能力模型，系统将自动生成难度匹配的同源变式题，陪你进行刻意练习。
                </p>
              </div>
            </motion.div>

            {/* Mode 4: Notes */}
            <motion.div variants={fadeUpVariants} className="group overflow-hidden rounded-xl bg-white/40 dark:bg-[#242421]/50 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 hover:border-[#879f7a] transition-colors backdrop-blur-sm">
              <div className="h-32 bg-[#879f7a]/10 flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCI+PHBhdGggZD0iTTAgMEwyMCAyME0yMCAwTDAgMjAiIHN0cm9rZT0iIzg3OWY3YSIgc3Ryb2tlLW9wYWNpdHk9IjAuMSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9zdmc+')] opacity-50"></div>
                <FileText className="w-12 h-12 text-[#879f7a] relative z-10 group-hover:scale-110 transition-transform duration-500" />
              </div>
              <div className="p-8">
                <h3 className="text-2xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">整理笔记</h3>
                <p className="text-xs text-[#879f7a] mb-4 tracking-widest uppercase font-bold">Notes Mode</p>
                <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-sm leading-relaxed">
                  化繁为简，提炼精粹。将你凌乱的草稿或杂乱的思绪发送给助教，它将自动生成结构清晰、排版绝美的 Markdown/LaTeX 数学笔记。
                </p>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* SECTION 2.8: CORE CAPABILITIES BENTO (核心矩阵) */}
      <section className="relative z-10 w-full py-24 px-4 border-t border-[#d6d0ba]/30 dark:border-[#3e3f36]/30 bg-[#faf7f2]/50 dark:bg-[#1e1e1b]/50">
        <div className="max-w-5xl mx-auto">
          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="text-center mb-16"
          >
            <motion.h2 variants={fadeUpVariants} className="text-4xl sm:text-5xl font-bold tracking-widest font-title text-[#2a2b26] dark:text-[#e6e4dc] mb-4">
              引擎矩阵 / <span className="text-[#c44a3d]">生态底座</span>
            </motion.h2>
            <motion.p variants={fadeUpVariants} className="text-lg font-body text-[#757a6b] dark:text-[#8d8a7d]">
              极致的工程化打磨，为您提供行业顶配的数智学习生态。
            </motion.p>
          </motion.div>

          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={staggerContainer}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-[200px]"
          >
            {/* Bento 1: Auto Mistake Book (Large) */}
            <motion.div variants={fadeUpVariants} className="md:col-span-2 row-span-1 md:row-span-2 group overflow-hidden rounded-2xl bg-gradient-to-br from-white/60 to-[#f2efe9]/40 dark:from-[#242421]/80 dark:to-[#1e1e1b]/40 border border-[#d6d0ba]/60 dark:border-[#3e3f36]/60 hover:border-[#c44a3d] transition-all duration-300 backdrop-blur-md flex flex-col justify-between p-8 relative">
              <div className="absolute -right-10 -top-10 w-48 h-48 bg-[#c44a3d]/10 rounded-full blur-3xl group-hover:bg-[#c44a3d]/20 transition-all duration-500"></div>
              <div>
                <div className="w-14 h-14 rounded-xl bg-[#c44a3d]/10 flex items-center justify-center mb-6">
                  <Printer className="w-7 h-7 text-[#c44a3d]" />
                </div>
                <h3 className="text-2xl sm:text-3xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-3">全自动错题实体卷导出</h3>
                <p className="text-[#4a4d44] dark:text-[#c5c2b6] font-body text-base leading-relaxed max-w-md">
                  诊断学习瓶颈后自动收录错题。一键切换「实体试卷」模式，自动抹除 UI 干扰、排版留白，直接导出完美 A4 格式进行线下打印复习。
                </p>
              </div>
            </motion.div>

            {/* Bento 2: Video DB */}
            <motion.div variants={fadeUpVariants} className="col-span-1 group overflow-hidden rounded-2xl bg-white/40 dark:bg-[#242421]/50 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 hover:border-[#617a55] transition-colors backdrop-blur-sm p-8 relative flex flex-col justify-end">
              <div className="absolute top-8 right-8 text-[#617a55] opacity-20 group-hover:opacity-100 group-hover:scale-110 transition-all duration-500">
                <Video className="w-12 h-12" />
              </div>
              <h3 className="text-xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">262 项课本级视频库</h3>
              <p className="text-[#757a6b] dark:text-[#8d8a7d] text-sm leading-relaxed">
                覆盖高数、线代、概统全部小节的精选 B站讲解视频精准投喂。
              </p>
            </motion.div>

            {/* Bento 3: Memory */}
            <motion.div variants={fadeUpVariants} className="col-span-1 group overflow-hidden rounded-2xl bg-white/40 dark:bg-[#242421]/50 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 hover:border-[#879f7a] transition-colors backdrop-blur-sm p-8 relative flex flex-col justify-end">
              <div className="absolute top-8 right-8 text-[#879f7a] opacity-20 group-hover:opacity-100 group-hover:scale-110 transition-all duration-500">
                <BrainCircuit className="w-12 h-12" />
              </div>
              <h3 className="text-xl font-title font-bold text-[#2a2b26] dark:text-[#e6e4dc] mb-2">记忆体与智能分流</h3>
              <p className="text-[#757a6b] dark:text-[#8d8a7d] text-sm leading-relaxed">
                全时记忆对话历史，首句提问自动凝练为精准的会话标签。
              </p>
            </motion.div>

            {/* Bento 4: Dynamic Math (Wide) */}
            <motion.div variants={fadeUpVariants} className="col-span-1 md:col-span-3 group overflow-hidden rounded-2xl bg-[#2a2b26] dark:bg-[#151513] border border-[#d6d0ba]/30 dark:border-[#3e3f36]/30 hover:border-[#d6d0ba] transition-all duration-300 backdrop-blur-md p-8 relative flex items-center overflow-hidden">
              <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCI+PHBhdGggZD0iTTAgMEwyMCAyME0yMCAwTDAgMjAiIHN0cm9rZT0iI2Q2ZDBiYSIgc3Ryb2tlLW9wYWNpdHk9IjAuMDUiIHN0cm9rZS13aWR0aD0iMSIvPjwvc3ZnPg==')] opacity-40"></div>
              <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between w-full gap-8">
                <div>
                  <div className="w-12 h-12 rounded-full bg-[#faf7f2]/10 flex items-center justify-center mb-4">
                    <LineChart className="w-6 h-6 text-[#d6d0ba]" />
                  </div>
                  <h3 className="text-2xl font-title font-bold text-[#faf7f2] mb-2">JSXGraph 动态几何域</h3>
                  <p className="text-[#d6d0ba] text-sm leading-relaxed max-w-lg">
                    不仅仅是 LaTeX 公式。从函数微积分曲线，到高维线性代数变换，通过内嵌交互式绘图板，让死板的公式真正“动”起来。
                  </p>
                </div>
                <div className="hidden md:flex flex-1 justify-end opacity-60 mix-blend-screen">
                  <div className="w-48 h-24 border-b-2 border-l-2 border-[#617a55] relative">
                    <svg className="absolute inset-0 w-full h-full overflow-visible" preserveAspectRatio="none">
                      <path d="M 0,96 Q 96,96 96,0 T 192,-96" fill="none" stroke="#c44a3d" strokeWidth="3" />
                    </svg>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* SECTION 3: TESTIMONIALS (学子心声) */}
      <section className="relative z-10 w-full py-24 px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div 
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="text-center mb-16"
          >
            <motion.h2 variants={fadeUpVariants} className="text-4xl sm:text-5xl font-bold tracking-widest font-title text-[#2a2b26] dark:text-[#e6e4dc] mb-4">
              学子心声
            </motion.h2>
            <motion.p variants={fadeUpVariants} className="text-lg font-body text-[#757a6b] dark:text-[#8d8a7d]">
              闻道有先后，术业有专攻。听听先行者的回音。
            </motion.p>
          </motion.div>

          <div className="space-y-8">
            <motion.div 
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUpVariants}
              className="relative p-8 md:p-12 bg-white/40 dark:bg-[#242421]/50 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 rounded-xl backdrop-blur-md italic font-body"
            >
              <Quote className="absolute top-6 left-6 w-12 h-12 text-[#617a55] opacity-20" />
              <p className="text-lg md:text-xl text-[#4a4d44] dark:text-[#c5c2b6] leading-relaxed relative z-10 pl-8">
                “再也不用害怕线性代数里的多维矩阵了，助教一步步把我从迷雾中拉出来。”
              </p>
              <div className="mt-6 pl-8 text-right text-[#757a6b] dark:text-[#8d8a7d] font-title">
                —— 山野樵夫
              </div>
            </motion.div>

            <motion.div 
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUpVariants}
              className="relative p-8 md:p-12 bg-white/40 dark:bg-[#242421]/50 border border-[#d6d0ba]/50 dark:border-[#3e3f36]/50 rounded-xl backdrop-blur-md italic font-body"
            >
              <Quote className="absolute top-6 left-6 w-12 h-12 text-[#c44a3d] opacity-10" />
              <p className="text-lg md:text-xl text-[#4a4d44] dark:text-[#c5c2b6] leading-relaxed relative z-10 pl-8">
                “以前算积分总是一团麻，现在的错题本让我知道自己究竟错在哪里。”
              </p>
              <div className="mt-6 pl-8 text-right text-[#757a6b] dark:text-[#8d8a7d] font-title">
                —— 渡水学子
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* SECTION 4: CALL TO ACTION & FOOTER (结语与入口) */}
      <section className="relative z-10 w-full pt-24 pb-12 px-4 flex flex-col items-center justify-center border-t border-[#d6d0ba]/30 dark:border-[#3e3f36]/30 bg-gradient-to-b from-transparent to-[#e8e4d8]/40 dark:to-[#171715]/60">
        <motion.div 
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          variants={staggerContainer}
          className="text-center max-w-2xl mx-auto mb-20"
        >
          <motion.h2 variants={fadeUpVariants} className="text-3xl sm:text-4xl font-bold tracking-widest font-title text-[#2a2b26] dark:text-[#e6e4dc] mb-8">
            欲穷千里目，更上一层楼。
          </motion.h2>
          
          <motion.div variants={fadeUpVariants}>
            {isLoggedIn ? (
              <Link 
                href="/chat" 
                className="group relative inline-flex h-14 items-center justify-center overflow-hidden border border-[#617a55] bg-[#617a55] px-12 font-title text-xl text-[#faf7f2] transition-all hover:bg-transparent hover:text-[#617a55] hover:border-[#617a55] rounded-md shadow-md"
              >
                <span className="mr-3">进入系统 (Enter)</span>
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Link>
            ) : (
              <button 
                onClick={() => { localStorage.setItem("mock_auth_token", "true"); setIsLoggedIn(true); }}
                className="group relative inline-flex h-14 items-center justify-center overflow-hidden border border-[#617a55] bg-[#617a55] px-12 font-title text-xl text-[#faf7f2] transition-all hover:bg-transparent hover:text-[#617a55] hover:border-[#617a55] rounded-md shadow-md"
              >
                <span className="mr-3">入园 (Initialize)</span>
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </button>
            )}
          </motion.div>
        </motion.div>

        <footer className="w-full text-center text-sm font-body text-[#757a6b] dark:text-[#8d8a7d]">
          <p>珞珈数智农场 © 2026</p>
          <p className="mt-2 text-xs opacity-60 font-title tracking-widest">Luojia Math Tutor V2.0</p>
        </footer>
      </section>

    </div>
  );
}
