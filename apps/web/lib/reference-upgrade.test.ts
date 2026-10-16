import test from "node:test";
import assert from "node:assert/strict";
import {selectionRange,linearContextRef,newtonActivityContextRef,teachBackContextRef,referenceChatKey,studyRequested,referenceHref,restoreReadingReference,numericalContextRef,referenceDescription,verifiedReferenceSession,chatReferenceHref,storePrivateChatHandoff,restorePrivateChatHandoff} from "./learning-context.ts";
import {studyTaskHref,recommendationHref,homeNextStep} from "./study-summary.ts";
import type {NumericalRun} from "./numerical-lab.ts";
import type {LearningOverview,NewtonActivityState,TeachBack} from "./learning-api.ts";
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
test("private reading question crosses to Chat without entering the URL",()=>{
 const ref={kind:"reading" as const,source_id:"NA_NEWTON",source_hash:"a".repeat(64),section_id:null,start:0,end:8,graph_revision:"v1",problem_text:"我的未公开题目原话",claimed_known:[0],condition_hash:"b".repeat(64)};
 const id="12345678-1234-4123-8123-123456789abc",items=new Map<string,string>();
 const storage={setItem:(key:string,value:string)=>{items.set(key,value);},getItem:(key:string)=>items.get(key)??null};
 const href=chatReferenceHref(ref,id);
 assert.equal(href,`/chat?handoff=${id}`);
 assert.ok(!href.includes(ref.problem_text)&&!href.includes("problem_text"));
 storePrivateChatHandoff(storage,"alice",id,ref,1000);
 assert.deepEqual(restorePrivateChatHandoff(storage,"alice",id,1001),ref);
 assert.equal(restorePrivateChatHandoff(storage,"bob",id,1001),null);
 assert.equal(restorePrivateChatHandoff(storage,"alice",id,1000+31*60*1000),null);
 assert.equal(restorePrivateChatHandoff(storage,"alice","../bad",1001),null);
 assert.equal(chatReferenceHref({...ref,problem_text:undefined}),`/chat?ref=${encodeURIComponent(JSON.stringify({...ref,problem_text:undefined}))}`);
});
test("explicit iteration reference is immutable while playback changes",()=>{const ref=linearContextRef(run,1);run.rows.push({k:2} as NumericalRun["rows"][number]);assert.equal(ref.selected_step,1);assert.equal(ref.record_id,"record");});
test("linear reference rejects old versions and invalid steps",()=>{assert.throws(()=>linearContextRef({...run,schema_version:"old"},0));assert.throws(()=>linearContextRef(run,100));});
test("reading offsets use codepoints and retain the second repeated passage",()=>{const text="甲📘乙重复乙重复";assert.deepEqual(selectionRange(text,6,9),{start:5,end:8});assert.equal(Array.from(text).slice(5,8).join(""),"乙重复");});
test("source discussion cache cannot cross owners or namespaces",()=>{const ref=linearContextRef(run,0);assert.notEqual(referenceChatKey("alice",ref),referenceChatKey("bob",ref));assert.notEqual(referenceChatKey("alice",ref),referenceChatKey("alice",{kind:"reading",source_id:"record",source_hash:"a".repeat(64),section_id:"0",start:0,end:1,graph_revision:null}));});
test("task navigation is a bounded command instead of math keyword interception",()=>{assert.ok(studyRequested("今天学什么？"));assert.ok(!studyRequested("今天学什么，并求x²=2"));});
test("stale or missing-session task cannot become a resume link",()=>{const t={id:"task1",title:"任务",state:"in_progress",stale:false,session_available:true,kind:"practice"};assert.equal(studyTaskHref(t),"/study?task=task1");assert.equal(studyTaskHref({...t,stale:true}),null);assert.equal(studyTaskHref({...t,session_available:false}),null);assert.equal(studyTaskHref({...t,id:"../private"}),null);});
test("state recommendation only opens bounded workspace routes",()=>{const base={policy_version:"r1-b1-v1",graph_revision:"v1",evidence_kind:"saved_state_only",mastery_claim:false,kind:"resume_task",title:"下一步",reason:"已保存状态",source_id:"id"} as const;assert.equal(recommendationHref({...base,href:"/study?task=task_1"}),"/study?task=task_1");assert.equal(recommendationHref({...base,href:"javascript:alert(1)"}),"/study");assert.equal(recommendationHref({...base,href:"/reading?unit=../private"}),"/study");});
test("home follows the server recommendation when an assessment and task coexist",()=>{const recommendation={policy_version:"r1-b1-v1",graph_revision:"v1",evidence_kind:"saved_state_only",mastery_claim:false,kind:"assessment_in_progress",title:"继续当前章节自检",reason:"自检尚未交卷",href:"/assessment",source_id:"exam"} as const;const step=homeNextStep({recommendation,active_assessment:{id:"exam",answered:2,total:6},next_task:{id:"task",title:"旧待办"} as LearningOverview["next_task"]});assert.equal(step.href,"/assessment");assert.equal(step.label,"继续章节自检");assert.match(step.reason,/2 \/ 6/);});
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

test("B5 return links keep the saved object and leave private code out of URLs",()=>{
 const linear=linearContextRef(run,1);
 assert.equal(referenceHref({ref:linear} as Parameters<typeof referenceHref>[0]),"/numerical-lab?id=record&step=1");
 const code={kind:"code_static" as const,record_id:"submission_1",code_hash:"a".repeat(64),static_rule_version:"newton-static-v2",selected_finding:0};
 assert.equal(referenceHref({ref:code} as Parameters<typeof referenceHref>[0]),"/code-workshop?id=submission_1");
 assert.notEqual(referenceChatKey("alice",code),referenceChatKey("bob",code));
 assert.notEqual(referenceChatKey("alice",code),referenceChatKey("alice",{...code,code_hash:"b".repeat(64)}));
});

test("reading unit and document references enforce field contracts and prevent section_id confusion",()=>{
 // 1. 课程大纲单元：section_id 必为 null
 const unitRef = {kind: "reading" as const, source_id: "NA_NEWTON", source_hash: "a".repeat(64), section_id: null, start: 0, end: 15, graph_revision: "v1"};
 const unitSnapshot = {ref: unitRef, source_kind: "unit", citation: {quote: "定理2.1收敛性", start: 0, end: 15, conditions: []}} as unknown as Parameters<typeof referenceHref>[0];
 assert.equal(referenceHref(unitSnapshot), "/reading?unit=NA_NEWTON");
 assert.ok(referenceChatKey("alice", unitRef).includes(":course"));

 // 2. 上传文档：section_id 为章节 ID（非 source_document_id）
 const docRef = {kind: "reading" as const, source_id: "doc_abc123", source_hash: "b".repeat(64), section_id: "sec_4", start: 10, end: 30, graph_revision: null};
 const docSnapshot = {ref: docRef, source_kind: "document", citation: {quote: "弦截法推导", start: 10, end: 30, conditions: []}} as unknown as Parameters<typeof referenceHref>[0];
 assert.equal(referenceHref(docSnapshot), "/reading?document=doc_abc123&section=sec_4");
 assert.ok(referenceChatKey("alice", docRef).includes(":sec_4"));

 // 3. 严禁混淆：若将 source_document_id 填入 section_id，生成的链接与键严格不相符
 const confusedRef = {...docRef, section_id: docRef.source_id};
 assert.notEqual(referenceChatKey("alice", docRef), referenceChatKey("alice", confusedRef));
 assert.notEqual(referenceHref(docSnapshot), referenceHref({ref: confusedRef} as unknown as Parameters<typeof referenceHref>[0]));
});

test("reading reference restoration rejects hash mismatch, corrupted spans, and cross-owner handoff",()=>{
 const source = {source_id: "doc_test", source_hash: "1".repeat(64), section_id: "sec_1", graph_revision: null};
 const rawValid = JSON.stringify({kind: "reading", ...source, start: 5, end: 20});
 assert.deepEqual(restoreReadingReference(rawValid, source, 50), {kind: "reading", ...source, start: 5, end: 20});

 // Hash 漂移（文档内容已重新解析/更新）严格拒绝恢复
 const rawDriftedHash = JSON.stringify({kind: "reading", ...source, source_hash: "2".repeat(64), start: 5, end: 20});
 assert.equal(restoreReadingReference(rawDriftedHash, source, 50), null);

 // 选段超出当前新正文长度严格拒绝
 const rawOverflow = JSON.stringify({kind: "reading", ...source, start: 5, end: 60});
 assert.equal(restoreReadingReference(rawOverflow, source, 50), null);

 // 选段倒置或负数严格拒绝
 assert.equal(restoreReadingReference(JSON.stringify({kind: "reading", ...source, start: 20, end: 5}), source, 50), null);
 assert.equal(restoreReadingReference(JSON.stringify({kind: "reading", ...source, start: -1, end: 10}), source, 50), null);
});


import {readingSourceRef, codeContextRef} from "./learning-context.ts";
test("ordinary course discussion has no condition-comparison authority and uses Unicode offsets",()=>{
 const ref=readingSourceRef({id:"NA_NEWTON",source_hash:"a".repeat(64),graph_revision:"g1"},"甲📘乙");
 assert.equal(ref.end,3);assert.equal(ref.section_id,null);
 assert.equal("condition_hash" in ref,false);assert.equal("problem_text" in ref,false);
 const document=readingSourceRef({id:"document1",source_hash:"b".repeat(64)},"摘录","section2");
 assert.equal(document.section_id,"section2");assert.equal(document.graph_revision,null);
 assert.throws(()=>readingSourceRef({id:"unit",source_hash:"a".repeat(64),graph_revision:"g1"},"a".repeat(6001)));
 assert.throws(()=>readingSourceRef({id:"unit",source_hash:"a".repeat(64)},"摘录"));
});

test("code workshop reference enforces finding bounds and returns to code-workshop",()=>{
 const submission = {
   id: "sub-123",
   code_hash: "c".repeat(64),
   static_rule_version: "v2",
   findings: [{kind: "naming", line: 3, message: "变量命名规范"}],
 } as unknown as Parameters<typeof codeContextRef>[0];
 const ref = codeContextRef(submission, 0);
 assert.equal(ref.kind, "code_static");
 assert.equal(ref.record_id, "sub-123");
 assert.equal(ref.selected_finding, 0);
 assert.equal(referenceHref({ref} as unknown as Parameters<typeof referenceHref>[0]), "/code-workshop?id=sub-123");
 assert.throws(() => codeContextRef(submission, 1));
});
