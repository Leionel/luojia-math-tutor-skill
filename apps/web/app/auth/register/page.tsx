"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, type Variants } from "framer-motion";
import { ArrowRight, KeyRound, User, Mail } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [isInitializing, setIsInitializing] = useState(false);

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    setIsInitializing(true);
    // Mock authentication
    setTimeout(() => {
      router.push("/chat");
    }, 800);
  };

  const containerVariants: Variants = {
    hidden: { opacity: 0, scale: 0.95 },
    show: { opacity: 1, scale: 1, transition: { duration: 0.4, ease: "easeOut", staggerChildren: 0.1 } }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="w-full border border-[#d6d0ba] dark:border-[#3e3f36] bg-[#faf7f2]/90 dark:bg-[#1e1e1b]/90 p-10 backdrop-blur-md relative rounded-lg shadow-lg"
    >
      <div className="absolute top-0 right-0 w-2 h-full bg-[#617a55] rounded-r-lg" />
      
      <motion.div variants={itemVariants} className="mb-8 text-right">
        <h2 className="text-3xl font-bold font-title tracking-wide text-[#2a2b26] dark:text-[#e6e4dc] mb-2">
          注册账号
        </h2>
        <p className="text-sm font-body text-[#757a6b] dark:text-[#8d8a7d]">
          创建账号以体验珞珈数智助教。
        </p>
      </motion.div>

      <motion.form variants={itemVariants} onSubmit={handleRegister} className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-body text-[#4a4d44] dark:text-[#c5c2b6] tracking-widest">用户名</label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#757a6b]" />
            <input 
              type="text" 
              required
              className="w-full bg-transparent border border-[#d6d0ba] dark:border-[#3e3f36] p-3 pl-10 text-[#2a2b26] dark:text-[#e6e4dc] font-body text-sm focus:outline-none focus:border-[#617a55] focus:shadow-[0_0_10px_-2px_rgba(97,122,85,0.3)] transition-all placeholder:text-[#a0a596] dark:placeholder:text-[#5c5a4d] rounded-md"
              placeholder="您的称呼"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-body text-[#4a4d44] dark:text-[#c5c2b6] tracking-widest">邮箱</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#757a6b]" />
            <input 
              type="email" 
              required
              className="w-full bg-transparent border border-[#d6d0ba] dark:border-[#3e3f36] p-3 pl-10 text-[#2a2b26] dark:text-[#e6e4dc] font-body text-sm focus:outline-none focus:border-[#617a55] focus:shadow-[0_0_10px_-2px_rgba(97,122,85,0.3)] transition-all placeholder:text-[#a0a596] dark:placeholder:text-[#5c5a4d] rounded-md"
              placeholder="user@domain.com"
            />
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-body text-[#4a4d44] dark:text-[#c5c2b6] tracking-widest">就读院校</label>
            <div className="relative">
              <input 
                type="text" 
                className="w-full bg-transparent border border-[#d6d0ba] dark:border-[#3e3f36] p-3 text-[#2a2b26] dark:text-[#e6e4dc] font-body text-sm focus:outline-none focus:border-[#617a55] focus:shadow-[0_0_10px_-2px_rgba(97,122,85,0.3)] transition-all placeholder:text-[#a0a596] dark:placeholder:text-[#5c5a4d] rounded-md"
                placeholder="例如：武汉大学"
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-body text-[#4a4d44] dark:text-[#c5c2b6] tracking-widest">主修专业</label>
            <div className="relative">
              <input 
                type="text" 
                className="w-full bg-transparent border border-[#d6d0ba] dark:border-[#3e3f36] p-3 text-[#2a2b26] dark:text-[#e6e4dc] font-body text-sm focus:outline-none focus:border-[#617a55] focus:shadow-[0_0_10px_-2px_rgba(97,122,85,0.3)] transition-all placeholder:text-[#a0a596] dark:placeholder:text-[#5c5a4d] rounded-md"
                placeholder="例如：计算机科学"
              />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-body text-[#4a4d44] dark:text-[#c5c2b6] tracking-widest">密码</label>
            <span className="text-xs text-[#a0a596] dark:text-[#757a6b]">至少 8 个字符</span>
          </div>
          <div className="relative">
            <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#757a6b]" />
            <input 
              type="password" 
              required
              minLength={8}
              maxLength={32}
              className="w-full bg-transparent border border-[#d6d0ba] dark:border-[#3e3f36] p-3 pl-10 text-[#2a2b26] dark:text-[#e6e4dc] font-body text-sm focus:outline-none focus:border-[#617a55] focus:shadow-[0_0_10px_-2px_rgba(97,122,85,0.3)] transition-all placeholder:text-[#a0a596] dark:placeholder:text-[#5c5a4d] rounded-md"
              placeholder="••••••••"
            />
          </div>
        </div>

        <motion.div variants={itemVariants} className="pt-4">
          <button 
            type="submit"
            disabled={isInitializing}
            className="group relative w-full flex h-12 items-center justify-center overflow-hidden border border-[#617a55] bg-[#617a55]/10 px-8 font-title text-lg text-[#617a55] transition-all hover:bg-[#617a55] hover:text-[#faf7f2] rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="mr-2">{isInitializing ? "注册中..." : "注册并进入"}</span>
            {!isInitializing && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />}
          </button>
        </motion.div>
      </motion.form>

      <motion.div variants={itemVariants} className="mt-8 pt-6 border-t border-[#d6d0ba] dark:border-[#3e3f36] text-center">
        <p className="text-sm font-body text-[#757a6b] dark:text-[#8d8a7d]">
          已有账号？{" "}
          <Link href="/auth/login" className="text-[#c44a3d] hover:text-[#a33b30] transition-colors font-medium">
            前往登录
          </Link>
        </p>
      </motion.div>
    </motion.div>
  );
}
