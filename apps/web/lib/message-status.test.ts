import test from "node:test";
import assert from "node:assert/strict";
import {messageStatus} from "./message-status.ts";
import type {TutorMeta} from "./api.ts";
const base:TutorMeta={intent:"concept",subject:"numerical_analysis",concepts:[],verified:false,is_correct:null,mistake:null,verifier_summary:""};
test("each response retains its own check and teaching mode",()=>{
  const old={...base,verified:true,verification_kind:"symbolic" as const,teaching_mode:"direct" as const};
  const next={...base,verification_kind:"llm_review" as const,teaching_mode:"practice" as const};
  assert.equal(messageStatus(old),"已完成本步检查 · 直接讲解");
  assert.equal(messageStatus(next),"推理审查未完成 · 练习模式");
  assert.equal(messageStatus(old),"已完成本步检查 · 直接讲解");
});
test("legacy responses do not invent a mode or claim checks were unnecessary",()=>{
  assert.equal(messageStatus({...base,verification_kind:"none"}),"本轮未进行步骤检查");
  assert.equal(messageStatus(null),undefined);
});
test("failure and vision confirmation supersede positive badges",()=>{
  assert.equal(messageStatus({...base,verified:true,error:{code:"timeout",message:"failed"}}),"本轮未完成");
  assert.equal(messageStatus({...base,awaiting_confirmation:true}),"等待题目核对");
});
