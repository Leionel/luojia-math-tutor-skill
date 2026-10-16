import test from "node:test";
import assert from "node:assert/strict";
import {messageStatus} from "./message-status.ts";
import type {TutorMeta} from "./api.ts";
const base:TutorMeta={intent:"concept",subject:"numerical_analysis",concepts:[],verified:false,is_correct:null,mistake:null,verifier_summary:""};
test("each response retains its own check and teaching mode",()=>{
  const old={...base,verified:true,verification_kind:"symbolic" as const,teaching_mode:"direct" as const};
  const next={...base,verification_kind:"llm_review" as const,teaching_mode:"practice" as const};
  assert.equal(messageStatus(old),"历史检查（范围未记录） · 直接讲解");
  assert.equal(messageStatus(next),"推理审查未完成 · 练习模式");
  assert.equal(messageStatus(old),"历史检查（范围未记录） · 直接讲解");
});
test("legacy responses do not invent a mode or claim checks were unnecessary",()=>{
  assert.equal(messageStatus({...base,verification_kind:"none"}),"历史回答（核验范围未记录）");
  assert.equal(messageStatus(null),undefined);
});
test("failure and vision confirmation supersede positive badges",()=>{
  assert.equal(messageStatus({...base,verified:true,error:{code:"timeout",message:"failed"}}),"本轮未完成");
  assert.equal(messageStatus({...base,awaiting_confirmation:true}),"等待题目核对");
});

const checked={version:"step-v1",execution_status:"succeeded" as const,origin:"student_claim",scope:"derivative",assumptions:["x为实数"],scope_complete:true,input_hash:"a".repeat(64),candidate_hash:"b".repeat(64),eligible_learning_evidence:true,unknown_reason:""};
test("current scoped checks do not inherit legacy certainty",()=>{
  assert.equal(messageStatus({...base,verified:true,is_correct:true,step_check:checked}),"本步候选核对通过（限指定范围）");
  assert.equal(messageStatus({...base,verified:true,is_correct:false,step_check:checked}),"本步候选存在差异（限指定范围）");
});
test("successful reference computation does not grade a student",()=>{
  assert.equal(messageStatus({...base,step_check:{...checked,origin:"system_calculation",candidate_hash:null,eligible_learning_evidence:false}}),"参考计算（未核对学生答案）");
});
test("timeout rejection and failure stay distinct from unrequested checks",()=>{
  assert.equal(messageStatus({...base,step_check:{...checked,execution_status:"timeout"}}),"本步核验未确定（超时）");
  assert.equal(messageStatus({...base,step_check:{...checked,execution_status:"rejected"}}),"本步核验未确定（输入或范围不受支持）");
  assert.equal(messageStatus({...base,step_check:{...checked,execution_status:"failed"}}),"本步核验未确定（检查失败）");
  assert.equal(messageStatus({...base,step_check:{...checked,execution_status:"not_requested",origin:"none"}}),"本轮未请求步骤检查");
});
test("Lhopital classification never advertises theorem verification",()=>{
  assert.equal(messageStatus({...base,verified:true,step_check:{...checked,origin:"classification",scope:"indeterminate_form",eligible_learning_evidence:false}}),"已检查未定式类型（未确认定理适用）");
});
test("model review does not replace scoped unknown",()=>{
  assert.equal(messageStatus({...base,verified:true,verification_kind:"llm_review",step_check:{...checked,execution_status:"timeout"}}),"本步核验未确定（超时） · 推理审查意见");
});
