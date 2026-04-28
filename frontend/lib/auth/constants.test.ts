import { describe, expect, it } from "vitest";

import { isClientRole, isDirectorRole, isStaffRole, ROLE_CLIENT } from "./constants";

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

  it("detects director role case-insensitively", () => {
    expect(isDirectorRole("director")).toBe(true);
    expect(isDirectorRole("Director")).toBe(true);
    expect(isDirectorRole("staff")).toBe(false);
    expect(isDirectorRole(undefined)).toBe(false);
  });
});
