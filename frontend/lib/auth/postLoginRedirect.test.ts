import { describe, expect, it } from "vitest";

import { getPostLoginPath, safeInternalPath } from "./postLoginRedirect";

describe("postLoginRedirect", () => {
  it("rejects unsafe next paths", () => {
    expect(safeInternalPath("//evil.com")).toBeNull();
    expect(safeInternalPath("https://x")).toBeNull();
    expect(safeInternalPath("/dashboard")).toBe("/dashboard");
  });

  it("sends staff to dashboard by default", () => {
    expect(getPostLoginPath("staff", null)).toBe("/dashboard");
  });

  it("sends client to portal by default", () => {
    expect(getPostLoginPath("client", null)).toBe("/portal");
  });

  it("honours safe next for staff", () => {
    expect(getPostLoginPath("staff", "/companies")).toBe("/companies");
  });

  it("ignores staff next pointing at portal", () => {
    expect(getPostLoginPath("staff", "/portal")).toBe("/dashboard");
  });

  it("honours portal subtree for clients", () => {
    expect(getPostLoginPath("client", "/portal/invoices")).toBe("/portal/invoices");
  });
});
