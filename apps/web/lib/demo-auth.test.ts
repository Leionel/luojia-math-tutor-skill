import assert from "node:assert/strict";
import test from "node:test";

import {authenticate,grantDemoAccess,hasDemoAccess,clearAuthSession,getAuthHeaders,getCurrentUserId,signOutCurrentSession,isAuthStorageKey} from "./demo-auth.ts";

test("sign out clears credentials and demo access while preserving learning drafts",()=>{
  const store=installStorage({luojia_auth_token:"test-token",luojia_auth_user:"alice",luojia_demo_access:"true",mock_auth_token:"true","reading-note:alice:test":"draft"});
  clearAuthSession();
  assert.deepEqual(getAuthHeaders(),{});
  assert.equal(getCurrentUserId(),"demo-user");
  assert.equal(hasDemoAccess(),false);
  assert.equal(store.get("reading-note:alice:test"),"draft");
});

function installStorage(initial: Record<string, string> = {}) {
  const store = new Map(Object.entries(initial));
  (globalThis as any).window = {
    localStorage: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => store.set(key, value),
      removeItem: (key: string) => store.delete(key),
    },
  };
  return store;
}

test("recognizes legacy demo access", () => {
  installStorage({ mock_auth_token: "true" });

  assert.equal(hasDemoAccess(), true);
});

test("grants demo access and clears legacy key", () => {
  const store = installStorage({ mock_auth_token: "true" });

  grantDemoAccess();

  assert.equal(store.get("luojia_demo_access"), "true");
  assert.equal(store.has("mock_auth_token"), false);
});

test("server-confirmed logout clears only credentials and preserves drafts",async()=>{
 const store=installStorage({luojia_auth_token:"synthetic-token",luojia_auth_user:"alice","reading-note:alice:test":"draft"});
 const before=globalThis.fetch;
 try{globalThis.fetch=async(_url,options)=>{assert.equal((options?.headers as Record<string,string>).Authorization,"Bearer synthetic-token");return {ok:true,json:async()=>({revoked:true,scope:"current_session"})} as Response;};
 assert.equal(await signOutCurrentSession(),"server");assert.equal(store.has("luojia_auth_token"),false);assert.equal(store.get("reading-note:alice:test"),"draft");
 }finally{globalThis.fetch=before;}
});

test("failed or unknown revocation keeps the login and does not report success",async()=>{
 const before=globalThis.fetch;
 try{for(const response of [null,{ok:false},{ok:true,json:async()=>({revoked:false})}]){
  const store=installStorage({luojia_auth_token:"synthetic-token",luojia_auth_user:"alice"});
  globalThis.fetch=async()=>{if(response===null)throw Error("offline");return response as Response;};
  await assert.rejects(signOutCurrentSession());assert.equal(store.get("luojia_auth_token"),"synthetic-token");
 }}finally{globalThis.fetch=before;}
});

test("late logout cannot clear the next account credentials",async()=>{
 const store=installStorage({luojia_auth_token:"old",luojia_auth_user:"alice"}),before=globalThis.fetch;
 try{globalThis.fetch=async()=>{store.set("luojia_auth_token","new");store.set("luojia_auth_user","bob");return {ok:true,json:async()=>({revoked:true,scope:"current_session"})} as Response;};
 await assert.rejects(signOutCurrentSession(),/身份已变化/);assert.equal(store.get("luojia_auth_token"),"new");assert.equal(store.get("luojia_auth_user"),"bob");
 }finally{globalThis.fetch=before;}
});

test("demo logout does not call the server and auth changes exclude preferences",async()=>{
 installStorage({luojia_demo_access:"true"});assert.equal(await signOutCurrentSession(),"demo");
 for(const key of [null,"luojia_auth_token","luojia_auth_user","luojia_demo_access","mock_auth_token"])assert.equal(isAuthStorageKey(key),true);
 assert.equal(isAuthStorageKey("luojia-theme"),false);
});

test("authentication saves only a confirmed v2 response for the requested owner",async()=>{
 const before=globalThis.fetch;
 try{const valid={auth_version:2,token_type:"bearer",access_token:"synthetic-session",user_id:"alice"};
 for(const body of [{...valid,auth_version:1},{...valid,user_id:"bob"},{...valid,access_token:""}]){
  const store=installStorage({luojia_auth_token:"original",luojia_auth_user:"old"});globalThis.fetch=async()=>({ok:true,json:async()=>body}) as Response;
  await assert.rejects(authenticate("login","alice","synthetic-passphrase"));assert.equal(store.get("luojia_auth_token"),"original");
 }
 const store=installStorage();globalThis.fetch=async()=>({ok:true,json:async()=>valid}) as Response;await authenticate("login","alice","synthetic-passphrase");assert.equal(store.get("luojia_auth_user"),"alice");
 }finally{globalThis.fetch=before;}
});
