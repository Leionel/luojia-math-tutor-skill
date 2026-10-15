import test from "node:test";
import assert from "node:assert/strict";
import {clearLearningBrowserState,migratePrivateReadingStorage,referenceBrowserStorage} from "./learning-browser-storage.ts";

function storage(initial:Record<string,string>={}):Storage{
 const items=new Map(Object.entries(initial));
 return {get length(){return items.size;},key:index=>Array.from(items.keys())[index]??null,
  getItem:key=>items.get(key)??null,setItem:(key,value)=>{items.set(key,value);},removeItem:key=>{items.delete(key);},
  clear:()=>items.clear()} as Storage;
}

test("old private reading questions and their discussion drafts move to tab storage",()=>{
 const privateRef={kind:"reading",problem_text:"学生私题",start:0,end:3};
 const local=storage({"reading-selection:alice:source":JSON.stringify(privateRef),
  "reading-selection:alice:public":JSON.stringify({kind:"reading",start:0,end:3}),
  "reading-selection:bob:source":JSON.stringify(privateRef),
  "reading-selection:alice:broken":"{学生私题",
  'luojia_reference_chat:alice:reading:source:[0,3,"学生私题"]:draft':"未发出的追问",
  "luojia-theme":"dark"});
 const session=storage({"reading-selection:alice:source":JSON.stringify({...privateRef,problem_text:"本标签页新题"})});
 migratePrivateReadingStorage(local,session,"alice");
 assert.equal(local.getItem("reading-selection:alice:source"),null);
 assert.equal(session.getItem("reading-selection:alice:source"),JSON.stringify({...privateRef,problem_text:"本标签页新题"}));
 assert.equal(local.getItem("reading-selection:bob:source"),null);
 assert.equal(local.getItem("reading-selection:alice:broken"),null);
 assert.equal(session.getItem("reading-selection:bob:source"),null);
 assert.equal(local.getItem("reading-selection:alice:public"),JSON.stringify({kind:"reading",start:0,end:3}));
 assert.equal(session.getItem('luojia_reference_chat:alice:reading:source:[0,3,"学生私题"]:draft'),"未发出的追问");
 assert.equal(local.getItem("luojia-theme"),"dark");
 assert.equal(referenceBrowserStorage(true,local,session),session);
 assert.equal(referenceBrowserStorage(false,local,session),local);
});

test("logout clears learning drafts and private handoffs from both stores, not preferences",()=>{
 const local=storage({"reading-note:alice:source":"未保存笔记","trace-draft:alice:task_1":"x0=1.5;x1=1.414","code-workshop:alice:new:code":"print(1)","luojia_user_api_key":"synthetic-key","luojia-theme":"dark"});
 const session=storage({"reading-selection:alice:source":"私题","luojia_private_chat_ref_v1:ref":"私题","pendingQuiz":"待讨论"});
 clearLearningBrowserState(local,session);
 assert.equal(local.getItem("reading-note:alice:source"),null);
 assert.equal(local.getItem("trace-draft:alice:task_1"),null);
 assert.equal(local.getItem("code-workshop:alice:new:code"),null);
 assert.equal(local.getItem("luojia_user_api_key"),null);
 assert.equal(session.length,0);
 assert.equal(local.getItem("luojia-theme"),"dark");
});
