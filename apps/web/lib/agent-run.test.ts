import test from "node:test";
import assert from "node:assert/strict";
import {mergeAgentRun,parseAgentRun} from "./agent-run.ts";
const run={version:"run-v1",scope:"execution_only",run_id:"12345678-1234-1234-1234-123456789012",status:"running",seq:1,steps:[{seq:1,phase:"model",status:"started"}],truncated:false};
test("execution protocol ignores unknown versions and strips payload fields",()=>{
 assert.equal(parseAgentRun({...run,version:"run-v2"}),undefined);
 assert.equal(parseAgentRun({...run,scope:"mathematical_proof"}),undefined);
 const parsed=parseAgentRun({...run,prompt:"private",steps:[{...run.steps[0],stdout:"private"}]});
 assert.ok(parsed); assert.equal(JSON.stringify(parsed).includes("private"),false);
 assert.equal(parseAgentRun({...run,steps:[...run.steps,...run.steps]}),undefined);
});
test("duplicates and late running events cannot regress a terminal receipt",()=>{
 const done={...run,status:"succeeded"};
 assert.equal(mergeAgentRun(done,{...run,seq:2})?.status,"succeeded");
 assert.equal(mergeAgentRun({...run,seq:2},run)?.seq,2);
 assert.equal(mergeAgentRun(run,done)?.status,"succeeded");
 assert.equal(mergeAgentRun(done,{...done,status:"failed"})?.status,"succeeded");
});
