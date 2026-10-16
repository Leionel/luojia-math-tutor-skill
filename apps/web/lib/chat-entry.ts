const PREFIX="luojia_chat_draft_v1:";
type StorageLike=Pick<Storage,"getItem"|"setItem"|"removeItem">;
export function storeChatEntry(storage:StorageLike,owner:string,id:string,text:string,now=Date.now()){
  if(!/^[a-f0-9-]{36}$/.test(id)||!text.trim()||text.length>4000)throw Error("请填写 1–4000 字符的问题。");
  storage.setItem(PREFIX+id,JSON.stringify({owner,text,at:now}));
}
export function readChatEntry(storage:StorageLike,owner:string,id:string,now=Date.now()):string|null{
  if(!/^[a-f0-9-]{36}$/.test(id))return null;
  try{const value=JSON.parse(storage.getItem(PREFIX+id)||"null");
    if(value?.owner!==owner||typeof value.text!=="string"||!value.text.trim()||value.text.length>4000||!Number.isFinite(value.at)||now<value.at||now-value.at>30*60*1000)return null;
    return value.text;
  }catch{return null;}
}
