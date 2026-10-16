import test from "node:test";
import assert from "node:assert/strict";
import {mergeAgentRun,parseAgentRun,parseRunUsage,receiptSteps} from "./agent-run.ts";
const run={version:"run-v1",scope:"execution_only",run_id:"12345678-1234-1234-1234-123456789012",status:"running",seq:1,steps:[{seq:1,phase:"model",status:"started"}],truncated:false};
test("execution protocol ignores unknown versions and strips payload fields",()=>{
 assert.equal(parseAgentRun({...run,version:"run-v2"}),undefined);
 assert.equal(parseAgentRun({...run,scope:"mathematical_proof"}),undefined);
 const parsed=parseAgentRun({...run,prompt:"private",steps:[{...run.steps[0],stdout:"private"}]});
 assert.ok(parsed); assert.equal(JSON.stringify(parsed).includes("private"),false);
 assert.equal(parseAgentRun({...run,steps:[...run.steps,...run.steps]}),undefined);
});
test("receipt presentation groups dispatch events but retains distinct calls",()=>{
 const span="a".repeat(32),other="b".repeat(32);
 const steps:Parameters<typeof receiptSteps>[0]=[
  {seq:1,phase:"context",status:"started"},
  {seq:2,phase:"model",status:"started",span_id:span},
  {seq:3,phase:"model",status:"started",span_id:span,request_sent:true},
  {seq:4,phase:"model",status:"succeeded",span_id:span},
  {seq:5,phase:"context",status:"succeeded"},
  {seq:6,phase:"model",status:"started",span_id:other}];
 assert.deepEqual(receiptSteps(steps).map(s=>s.seq),[4,5,6]);
});

const usage={version:"usage-v1",model_attempts:3,model_requests:2,reported_requests:1,coverage:"partial",
 known_tokens:{prompt_tokens:10,completion_tokens:5,total_tokens:15},cost:null,cost_status:"unavailable"};
test("provider usage stays partial and old missing usage stays unknown",()=>{
 assert.equal(parseAgentRun(run)?.usage,null);
 assert.equal(parseRunUsage({...usage,reported_requests:3}),null);
 assert.equal(parseRunUsage({...usage,known_tokens:{...usage.known_tokens,total_tokens:100}}),null);
 const parsed=parseRunUsage({...usage,prompt:"private",known_tokens:{...usage.known_tokens,secret:"private"}});
 assert.equal(parsed?.coverage,"partial");assert.equal(parsed?.known_tokens.total_tokens,15);
 assert.equal(JSON.stringify(parsed).includes("private"),false);
});
test("versioned cost and safe spans survive refresh without tool arguments",()=>{
 const span="a".repeat(32);
 const parsed=parseAgentRun({...run,usage:{...usage,cost_status:"partial",cost:{amount:"0.00002000",currency:"USD",
  price_version:"2026-10-03-v1",scope:"reported_plain_tokens_estimate",key:"private"}},
  steps:[{...run.steps[0],span_id:span,call_id:span,parent_id:run.run_id,model_stage:"guard_repair",first_content_ms:42,
   arguments:"private",usage:{...usage.known_tokens,prompt:"private"}}]});
 assert.equal(parsed?.steps[0].span_id,span);assert.equal(parsed?.steps[0].model_stage,"guard_repair");
 assert.equal(parsed?.usage?.cost?.price_version,"2026-10-03-v1");assert.equal(parsed?.usage?.cost_status,"partial");
 assert.equal(JSON.stringify(parsed).includes("private"),false);
 assert.equal(parseRunUsage({...usage,cost:{amount:"NaN",currency:"USD"},cost_status:"complete"})?.cost,null);
});
test("duplicates and late running events cannot regress a terminal receipt",()=>{
 const done={...run,status:"succeeded"};
 assert.equal(mergeAgentRun(done,{...run,seq:2})?.status,"succeeded");
 assert.equal(mergeAgentRun({...run,seq:2},run)?.seq,2);
 assert.equal(mergeAgentRun(run,done)?.status,"succeeded");
 assert.equal(mergeAgentRun(done,{...done,status:"failed"})?.status,"succeeded");
});
