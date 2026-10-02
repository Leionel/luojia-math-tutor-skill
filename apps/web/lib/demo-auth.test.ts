import assert from "node:assert/strict";
import test from "node:test";

import { grantDemoAccess, hasDemoAccess, clearAuthSession, getAuthHeaders, getCurrentUserId } from "./demo-auth.ts";

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
