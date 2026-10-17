// Saved learning records live on the server. These prefixes are browser-only
// drafts, request fingerprints, and pointers to saved discussions.
const LEARNING_PREFIXES=[
 "reading-selection:","reading-question:","reading-note:","note-request:","explanation-request:",
 "luojia_reference_chat:","luojia_lab_chat:","teach-back-draft:","teach-back-request:",
 "code-workshop:","assessment-draft:","lab-draft:","lab-request:","lab-reflection:",
 "learning-trace:","learning-request:","newton-activity:","lab-action:","numerical-request:",
 "luojia_private_chat_ref_v1:","luojia_chat_draft_v1:",
  "luojia_exploration_draft_v1:","luojia_experiment_editor:","trace-draft:",
];
const LEARNING_EXACT_KEYS=new Set(["pendingQuiz","luojia_user_api_key"]);

function keys(storage:Storage):string[]{return Array.from({length:storage.length},(_,index)=>storage.key(index)).filter((key):key is string=>key!==null);}

export function clearLearningBrowserState(local:Storage,session:Storage):void{
 for(const storage of [local,session])for(const key of keys(storage))if(LEARNING_EXACT_KEYS.has(key)||LEARNING_PREFIXES.some(prefix=>key.startsWith(prefix)))storage.removeItem(key);
}

/** Move old private reading references out of persistent storage without losing the current owner's same-tab draft. */
export function migratePrivateReadingStorage(local:Storage,session:Storage,owner:string):void{
 for(const key of keys(local)){
  const selection=key.startsWith("reading-selection:");
  const privateChat=key.startsWith("luojia_reference_chat:")&&key.includes(":reading:")&&key.includes(":[");
  if(!selection&&!privateChat)continue;
  const raw=local.getItem(key);
  let privateSelection=false;
  if(selection)try{
   const parsed=JSON.parse(raw??"null");
   if(!parsed||typeof parsed!=="object"){local.removeItem(key);continue;}
   privateSelection=Boolean(parsed.problem_text);
  }catch{local.removeItem(key);continue;}
  if(!privateSelection&&!privateChat)continue;
  const mine=key.startsWith(`${selection?"reading-selection":"luojia_reference_chat"}:${owner}:`);
  if(mine&&raw!==null)try{if(session.getItem(key)===null)session.setItem(key,raw);}catch{/* Privacy takes precedence if session storage is unavailable. */}
  local.removeItem(key);
 }
}

export function referenceBrowserStorage(privateReading:boolean,local:Storage,session:Storage):Storage{
 return privateReading?session:local;
}
