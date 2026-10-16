/** Read server-saved provenance without assigning a version to legacy notes. */
export function documentNoteSource(note:{content:string;session_id:string}) {
  const match=note.content.match(/^<!-- luojia-document-source ([^\n]{1,2048}) -->\n/);
  if(!match)return {content:note.content,source:null};
  try{const value=JSON.parse(match[1]);
    if(typeof value.document_id!=="string"||note.session_id!==`document:${value.document_id}`||!/^[a-f0-9]{64}$/.test(value.source_hash)||value.coverage!=="heading_outline_and_sampled_body"||!Number.isSafeInteger(value.sample_chars)||!Number.isSafeInteger(value.source_chars)||value.sample_chars<0||value.source_chars<1)return {content:note.content,source:null};
    return {content:note.content.slice(match[0].length),source:{documentId:value.document_id as string,sourceHash:value.source_hash as string,sampleChars:value.sample_chars as number,sourceChars:value.source_chars as number}};
  }catch{return {content:note.content,source:null};}
}
