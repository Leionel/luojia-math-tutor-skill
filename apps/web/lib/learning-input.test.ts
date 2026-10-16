import assert from "node:assert/strict";
import test from "node:test";
import {parseTrace, finiteNumber, stableRequestId, paragraphSpans, notesForSource, assessmentDraft} from "./learning-input.ts";

test("assessment recovery excludes confirmed, unrelated and invalid draft options",()=>{
  const questions=[{id:"saved",options:["A","B"]},{id:"next",options:["A","B"]},{id:"invalid",options:["A"]}];
  assert.deepEqual(assessmentDraft(JSON.stringify({saved:0,next:1,invalid:3,foreign:0}),questions,{saved:1}),{next:1});
  for(const raw of ["broken", "[]", "null", '{"next":"1"}', '{"next":0.5}', '{"next":-1}']) assert.deepEqual(assessmentDraft(raw,questions,{}),{});
});

test("private document notes stay with their source and original section",()=>{
  const notes=[{id:"first",source_id:"doc-a",section_id:"0"},{id:"second",source_id:"doc-a",section_id:"1"},{id:"other-doc",source_id:"doc-b",section_id:"0"},{id:"course",source_id:"NA_NEWTON",section_id:null}];
  assert.deepEqual(notesForSource(notes,"doc-a","1").map(n=>n.id),["second"]);
  assert.deepEqual(notesForSource(notes,"doc-b","0").map(n=>n.id),["other-doc"]);
  assert.deepEqual(notesForSource(notes,"NA_NEWTON").map(n=>n.id),["course"]);
  assert.deepEqual(notesForSource(notes,undefined,"0"),[]);
});

test("trace input accepts separators and explicit nonfinite diagnostic values",()=>{
  assert.deepEqual(parseTrace("1，1.5\n1.4166666667"),[1,1.5,1.4166666667]);
  assert.deepEqual(parseTrace("1,NaN,Inf,-Inf"),[1,"NaN","Inf","-Inf"]);
  for(const input of ["", "1", "1,window.alert(1)","1,1e100",Array(102).fill("1").join(",")]) assert.throws(()=>parseTrace(input));
});
test("empty and nonfinite parameter inputs cannot become zero or NaN",()=>{
  assert.equal(finiteNumber("0","初值"),0);
  assert.equal(finiteNumber("1e-4","阈值"),.0001);
  for(const input of ["", " ", "NaN", "Infinity", "1/0"]) assert.throws(()=>finiteNumber(input,"参数"));
});
test("network retries preserve request identity while changed payload gets a new one",()=>{
  const data=new Map<string,string>();let count=0;
  const storage={getItem:(key:string)=>data.get(key)??null,setItem:(key:string,value:string)=>{data.set(key,value);}};
  const id=()=>`id-${++count}`;
  assert.equal(stableRequestId(storage,"alice:task",{trace:[1,1.5]},id),"id-1");
  assert.equal(stableRequestId(storage,"alice:task",{trace:[1,1.5]},id),"id-1");
  assert.equal(stableRequestId(storage,"alice:task",{trace:[1,1.4]},id),"id-2");
  assert.equal(stableRequestId(storage,"bob:task",{trace:[1,1.4]},id),"id-3");
  data.set("broken","bad json");assert.equal(stableRequestId(storage,"broken",{},id),"id-4");
});

test("source spans match Python Unicode character offsets and stay bounded",()=>{
  const quote="原文🙂\n\n第二段";
  const spans=paragraphSpans(quote);
  const characters=Array.from(quote);
  assert.equal(characters.slice(spans[1].start,spans[1].end).join(""),"原文🙂");
  assert.equal(characters.slice(spans[2].start,spans[2].end).join(""),"第二段");
  assert.ok(paragraphSpans("x".repeat(9000)).every(s=>s.end-s.start<=6000));
});
