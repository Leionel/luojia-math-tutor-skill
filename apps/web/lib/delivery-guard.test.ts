import test from "node:test";
import assert from "node:assert/strict";
import { deliveryGuardLabel } from "./delivery-guard.ts";

test("delivery status cannot be confused with mathematical verification", () => {
  assert.match(deliveryGuardLabel({version:"delivery-v1",scope:"delivery_rules_only",status:"repaired"})!, /不代表数学/);
  assert.match(deliveryGuardLabel({version:"delivery-v1",scope:"delivery_rules_only",status:"withheld"})!, /未交付/);
  assert.match(deliveryGuardLabel({version:"delivery-v1",scope:"delivery_rules_only",status:"passed",enabled:false})!, /未启用/);
  assert.equal(deliveryGuardLabel({version:"unknown",scope:"delivery_rules_only",status:"passed"}), null);
});
