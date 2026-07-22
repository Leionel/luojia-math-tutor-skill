import assert from "node:assert/strict";
import test from "node:test";

import { grantDemoAccess, hasDemoAccess } from "./demo-auth.ts";

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
