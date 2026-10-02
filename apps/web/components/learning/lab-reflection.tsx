"use client";
import {useEffect, useState} from "react";
import {getCurrentUserId} from "@/lib/demo-auth";
import {learningInput} from "./learning-shell";

export function LabReflection({runId}: {runId:string}) {
  const [reflection,setReflection]=useState("");
  const key=`lab-reflection:${getCurrentUserId()}:${runId}`;
  useEffect(()=>{setReflection(localStorage.getItem(key)??"");},[key]);
  return <section className="mt-6 border-t border-[var(--border-subtle)] pt-5"><label htmlFor="lab-reflection" className="block text-lg font-semibold">用观察修订我的预测</label><p className="my-3 leading-7 text-[var(--text-secondary)]">哪一步与预测不同？改变一个参数后，你预计会怎样？这段复盘保存在当前浏览器，绑定本次实验。</p><textarea id="lab-reflection" maxLength={2000} rows={3} value={reflection} onChange={e=>{setReflection(e.target.value);localStorage.setItem(key,e.target.value);}} className={learningInput} placeholder="我原本认为…；在第 k 步观察到…；下次只改变…来检验。"/></section>;
}
