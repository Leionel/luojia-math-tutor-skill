import test from "node:test";
import assert from "node:assert/strict";
import {selectionRange,linearContextRef,newtonActivityContextRef,teachBackContextRef,referenceChatKey,studyRequested,referenceHref,restoreReadingReference,numericalContextRef,referenceDescription,verifiedReferenceSession} from "./learning-context.ts";
import {studyTaskHref,recommendationHref} from "./study-summary.ts";
import type {NumericalRun} from "./numerical-lab.ts";
import type {NewtonActivityState,TeachBack} from "./learning-api.ts";
const run={id:"record",source_hash:"a".repeat(64),schema_version:"numerical-lab-v1",task:{domain:"linear_system"},rows:[{k:0},{k:1}]} as unknown as NumericalRun;
test("reading refresh restores the exact span and rejects changed sources or invalid storage",()=>{
 const source={source_id:"course",source_hash:"a".repeat(64),section_id:null,graph_revision:"v1"};
 const ref={kind:"reading",...source,start:3,end:8};
 assert.deepEqual(restoreReadingReference(JSON.stringify(ref),source,10),ref);
 for(const changed of [{...ref,source_hash:"b".repeat(64)},{...ref,graph_revision:"v2"},{...ref,end:11},{...ref,start:-1}])assert.equal(restoreReadingReference(JSON.stringify(changed),source,10),null);
 assert.equal(restoreReadingReference("null",source,10),null);
 assert.equal(restoreReadingReference("broken",source,10),null);
});
test("condition comparison keeps student markings unverified and bound to the card version",()=>{
 const source={source_id:"NA_NEWTON",source_hash:"a".repeat(64),section_id:null,graph_revision:"v1",condition_hash:"b".repeat(64)};
 const ref={kind:"reading" as const,...source,start:0,end:8,problem_text:"已知 f 在区间内可导，问能否使用 Newton 法？",claimed_known:[0]};
 assert.deepEqual(restoreReadingReference(JSON.stringify(ref),source,10,2),ref);
 assert.equal(restoreReadingReference(JSON.stringify(ref),{...source,condition_hash:"c".repeat(64)},10,2),null);
 assert.equal(restoreReadingReference(JSON.stringify({...ref,claimed_known:[3]}),source,10,2),null);
 assert.notEqual(referenceChatKey("alice",ref),referenceChatKey("alice",{...ref,problem_text:"另一题"}));
 const href=referenceHref({ref,citation:{quote:"q",start:0,end:8,conditions:[]}} as unknown as Parameters<typeof referenceHref>[0]);
 assert.equal(href,"/reading?unit=NA_NEWTON#reading-discussion");
 assert.ok(!href.includes(ref.problem_text));
});
test("explicit iteration reference is immutable while playback changes",()=>{const ref=linearContextRef(run,1);run.rows.push({k:2} as NumericalRun["rows"][number]);assert.equal(ref.selected_step,1);assert.equal(ref.record_id,"record");});
test("linear reference rejects old versions and invalid steps",()=>{assert.throws(()=>linearContextRef({...run,schema_version:"old"},0));assert.throws(()=>linearContextRef(run,100));});
test("reading offsets use codepoints and retain the second repeated passage",()=>{const text="甲📘乙重复乙重复";assert.deepEqual(selectionRange(text,6,9),{start:5,end:8});assert.equal(Array.from(text).slice(5,8).join(""),"乙重复");});
test("source discussion cache cannot cross owners or namespaces",()=>{const ref=linearContextRef(run,0);assert.notEqual(referenceChatKey("alice",ref),referenceChatKey("bob",ref));assert.notEqual(referenceChatKey("alice",ref),referenceChatKey("alice",{kind:"reading",source_id:"record",source_hash:"a".repeat(64),section_id:"0",start:0,end:1,graph_revision:null}));});
test("task navigation is a bounded command instead of math keyword interception",()=>{assert.ok(studyRequested("今天学什么？"));assert.ok(!studyRequested("今天学什么，并求x²=2"));});
test("stale or missing-session task cannot become a resume link",()=>{const t={id:"task1",title:"任务",state:"in_progress",stale:false,session_available:true,kind:"practice"};assert.equal(studyTaskHref(t),"/study?task=task1");assert.equal(studyTaskHref({...t,stale:true}),null);assert.equal(studyTaskHref({...t,session_available:false}),null);assert.equal(studyTaskHref({...t,id:"../private"}),null);});
test("state recommendation only opens bounded workspace routes",()=>{const base={policy_version:"r1-b1-v1",graph_revision:"v1",evidence_kind:"saved_state_only",mastery_claim:false,kind:"resume_task",title:"下一步",reason:"已保存状态",source_id:"id"} as const;assert.equal(recommendationHref({...base,href:"/study?task=task_1"}),"/study?task=task_1");assert.equal(recommendationHref({...base,href:"javascript:alert(1)"}),"/study");assert.equal(recommendationHref({...base,href:"/reading?unit=../private"}),"/study");});
test("reading source link uses section without invented page numbers",()=>{const s={version:"learning-context-v1",title:"source",evidence_kind:"reference_help",independent_success:false,ref:{kind:"reading",source_id:"record",source_hash:"a".repeat(64),section_id:"2",start:0,end:1,graph_revision:null},citation:{quote:"q",start:0,end:1,conditions:[]},source_kind:"uploaded_markdown"} as const;assert.equal(referenceHref(s as unknown as Parameters<typeof referenceHref>[0]),"/reading?document=record&section=2");});

test("integration has its own namespace and retains estimator scope",()=>{
 const integral={...run,task:{domain:"integration",method:"simpson",expression:"exp(x)",left:0,right:1}} as unknown as NumericalRun;
 const ref=numericalContextRef(integral,0);assert.equal(ref.kind,"integration_lab");
 assert.notEqual(referenceChatKey("alice",ref),referenceChatKey("alice",linearContextRef(run,0)));
 const snapshot={task:integral.task,ref} as unknown as Parameters<typeof referenceDescription>[0];
 assert.match(referenceDescription(snapshot),/误差估计，非严格界/);
});

test("reference sessions require a current owner match and missing sessions remain a lazy draft",()=>{
 assert.equal(verifiedReferenceSession("old",[],"alice"),undefined);
 assert.equal(verifiedReferenceSession("old",[{id:"old",user_id:"bob"}],"alice"),undefined);
 assert.equal(verifiedReferenceSession("old",[{id:"old",user_id:"alice"}],"alice"),"old");
 assert.equal(verifiedReferenceSession(null,[{id:"old",user_id:"alice"}],"alice"),undefined);
});

test("explicit Newton explanation uses a versioned claim and returns to the activity",()=>{
 const run={id:"newton-run",input_hash:"a".repeat(64),runner_version:"root-v1",graph_revision:"graph-v1",rows:[{k:0}]} as NewtonActivityState["run"];
 const activity={id:"newton-cycle-v1",version:"newton-participation-v1",run,context_current:true,
  explanation:{text:"我的解释",request_id:"explain-1",run_id:"newton-run",input_hash:"a".repeat(64),at:"now"},revisions:[]} as unknown as NewtonActivityState;
 const ref=newtonActivityContextRef(activity,"explanation","explain-1");
 assert.equal(ref.activity_claim?.request_id,"explain-1");
 assert.equal(ref.activity_claim?.revision_count,0);
 assert.notEqual(referenceChatKey("alice",ref),referenceChatKey("alice",{...ref,activity_claim:undefined}));
 assert.notEqual(referenceChatKey("alice",ref),referenceChatKey("bob",ref));
 assert.equal(referenceHref({ref} as Parameters<typeof referenceHref>[0]),"/lab?activity=newton-cycle-v1&run=newton-run&claim=explain-1&step=0#newton-activity");
 assert.throws(()=>newtonActivityContextRef({...activity,context_current:false},"explanation","explain-1"));
 assert.throws(()=>newtonActivityContextRef(activity,"explanation","not-selected"));
});

test("selected teach-back condition keeps its saved version and own chat return link",()=>{
 const saved={id:"teach-1",source_hash:"a".repeat(64),condition_hash:"b".repeat(64),graph_revision:"g1",evidence_version:"teachback-evidence-v1",conditions:[{condition_id:"NA_NEWTON:0"}]} as TeachBack;
 const ref=teachBackContextRef(saved,"NA_NEWTON:0");
 assert.equal(referenceHref({ref} as Parameters<typeof referenceHref>[0]),"/teach-back?id=teach-1&condition=NA_NEWTON%3A0");
 assert.notEqual(referenceChatKey("alice",ref),referenceChatKey("bob",ref));
 assert.throws(()=>teachBackContextRef({...saved,condition_hash:"old"},"NA_NEWTON:0"));
 assert.throws(()=>teachBackContextRef(saved,"NA_NEWTON:9"));
});
