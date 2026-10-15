import assert from "node:assert/strict";
import test from "node:test";
import {ChatLifetime} from "./chat-lifetime.ts";
import {parseRootProposals, sameContext, previewMatches} from "./learning-actions.ts";

test("lazy session creation locks before await; a switched view rejects every old callback",()=>{
  const chat=new ChatLifetime(), old=chat.begin("alice")!;
  assert.equal(chat.begin("alice"),null);
  chat.invalidate(); const next=chat.begin("alice")!;
  assert.equal(old.controller.signal.aborted,true);
  assert.equal(chat.current(old,"alice"),false);
  chat.finish(old); assert.equal(chat.current(next,"alice"),true);
  assert.equal(chat.current(next,"bob"),false);
  chat.cancel(); assert.equal(next.controller.signal.aborted,true);
  assert.equal(chat.current(next,"alice"),true,"cancel can reconcile only its own receipt");
  chat.finish(next); assert.equal(chat.current(next,"alice"),false);
});
const context={kind:"root_lab" as const,record_id:"lab-one",input_hash:"a".repeat(64),runner_version:"v1",graph_revision:"graph1",selected_step:null};
test("generic preview controls cannot attach to a selected activity claim or newer revision",()=>{
  const claim={...context,activity_claim:{activity_id:"newton-cycle-v1" as const,activity_version:"newton-participation-v1" as const,claim_kind:"explanation" as const,request_id:"claim-a",revision_count:0}};
  assert.equal(sameContext(context,claim),false);
  assert.equal(sameContext(claim,{...claim,activity_claim:{...claim.activity_claim,revision_count:1}}),false);
});
const proposal={version:"tutor-artifact-v1",kind:"root_parameter_proposal",action:"preview_root_lab",artifact_id:"a1",run_id:"r1",origin:"server",context,
  parameters:{initial_value:-2,tolerance:0.0001,max_iterations:20},created_at:"2026-10-03T00:00:00Z",expires_at:"2026-10-04T00:00:00Z",evidence_kind:"reference_help",independent_success:false,preview_budget:3};
test("only the fixed card contract can render; forged operation names and nonfinite drafts are rejected",()=>{
  assert.equal(parseRootProposals([proposal]).length,1);
  for(const patch of [{action:"execute_python"},{origin:"model"},{independent_success:true},{parameters:{...proposal.parameters,initial_value:Infinity}},{parameters:{...proposal.parameters,max_iterations:101}},{context:{...context,input_hash:"fake"}}]) {
    assert.deepEqual(parseRootProposals([{...proposal,...patch}]),[]);
  }
  assert.deepEqual(parseRootProposals({html:"<script>"}),[]);
});
test("record versions and selected steps are pinned; dirty parameters cannot save the previous preview",()=>{
  assert.equal(sameContext(context,{...context}),true);
  for(const patch of [{record_id:"another"},{input_hash:"b".repeat(64)},{graph_revision:"new"},{runner_version:"v2"},{selected_step:1}]) assert.equal(sameContext(context,{...context,...patch}),false);
  assert.equal(sameContext(context,undefined),false);
  const preview={parameters:{method:"newton" as const,function:"x^3-2*x+2",initial_value:-2,tolerance:.0001,goal:"residual" as const},max_iterations:20,id:"p1",context,input_hash:"a".repeat(64),runner_version:"v1",graph_revision:"g1",rows:[],stop_detail:"stop",diagnosis:{summary:"summary",status:"s",complete:false}};
  assert.equal(previewMatches(preview,proposal.parameters),true);
  assert.equal(previewMatches(preview,{...proposal.parameters,initial_value:0}),false);
  assert.equal(previewMatches(preview,{...proposal.parameters,max_iterations:10}),false);
});


// Deferred source validation must not revive an explicitly cleared reference.
import {ReferenceSelection} from "./reference-selection.ts";
test("clearing a reference and a newer selection supersede pending validation", async () => {
  const selection = new ReferenceSelection();
  let finish!: () => void;
  const pending = new Promise<void>(resolve => {finish=resolve;});
  const old = selection.begin(() => true);
  let bound = "lab";
  const validation = pending.then(() => {if(old()) bound="late lab";});
  const cleared = selection.begin(() => true);
  bound = "none";
  finish(); await validation;
  assert.equal(bound,"none"); assert.equal(cleared(),true);
  const latest = selection.begin(() => true);
  assert.equal(cleared(),false); assert.equal(latest(),true);
});
test("reference validation cannot finish in a changed account or session", () => {
  const selection = new ReferenceSelection();
  let environment=true;
  const current = selection.begin(() => environment);
  assert.equal(current(),true); environment=false; assert.equal(current(),false);
});
test("conversation busy state blocks source replacement until generation releases its lease", () => {
  const lifetime = new ChatLifetime();
  assert.equal(lifetime.busy,false);
  const lease=lifetime.begin("alice")!;
  assert.equal(lifetime.busy,true);
  lifetime.finish(lease); assert.equal(lifetime.busy,false);
});
