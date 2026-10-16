import test from "node:test";
import assert from "node:assert/strict";
import {documentUploadError,materialStatus} from "./material-policy.ts";
import {documentNoteSource} from "./document-note-source.ts";

test("documents use a bounded binary upload path; pictures stay separate",()=>{
  for(const name of ["lecture.pdf","lecture.DOCX","lecture.doc","slides.pptx"])assert.equal(documentUploadError({name,size:1}),null);
  for(const name of ["secret.exe","picture.png","fake.pdf.exe","script.svg"])assert.ok(documentUploadError({name,size:1}));
  assert.ok(documentUploadError({name:"a.pdf",size:0}));
  assert.equal(documentUploadError({name:"a.pdf",size:200*1024*1024}),null);
  assert.ok(documentUploadError({name:"a.pdf",size:200*1024*1024+1}));
});
test("legacy status is never presented as successful parsing",()=>{
  assert.equal(materialStatus("ready"),"原文已保存");
  assert.match(materialStatus("source_missing"),/缺少/);
  assert.match(materialStatus(undefined),/待核对/);
});
test("saved note scope stays tied to its real document and version",()=>{
  const provenance={document_id:"doc_a",source_hash:"a".repeat(64),coverage:"heading_outline_and_sampled_body",sample_chars:30,source_chars:100};
  const body="范围说明\n# 笔记";
  const content=`<!-- luojia-document-source ${JSON.stringify(provenance)} -->\n${body}`;
  const result=documentNoteSource({session_id:"document:doc_a",content});
  assert.equal(result.content,body);
  assert.deepEqual(result.source,{documentId:"doc_a",sourceHash:"a".repeat(64),sampleChars:30,sourceChars:100});
  assert.equal(documentNoteSource({session_id:"document:doc_b",content}).source,null);
  assert.equal(documentNoteSource({session_id:"document:doc_a",content:content.replace("a".repeat(64),"unknown")}).source,null);
});
test("old notes and malformed metadata preserve original content without inventing source",()=>{
  for(const content of ["# 旧笔记",'<!-- luojia-document-source {"source_hash":""} -->\n原文',"<!-- luojia-document-source invalid -->\n正文"]){
    assert.deepEqual(documentNoteSource({session_id:"document:legacy",content}),{content,source:null});
  }
});
