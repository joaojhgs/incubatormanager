import { describe, expect, it } from "vitest";

import { isClientRole, isStaffRole, ROLE_CLIENT } from "./constants";

describe("role helpers", () => {
  it("detects staff roles", () => {
    expect(isStaffRole("director")).toBe(true);
    expect(isStaffRole("staff")).toBe(true);
    expect(isStaffRole("client")).toBe(false);
  });

  it("detects client role", () => {
    expect(isClientRole(ROLE_CLIENT)).toBe(true);
    expect(isClientRole("staff")).toBe(false);
  });
});
