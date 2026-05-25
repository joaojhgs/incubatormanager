import { describe, expect, it } from "vitest";

import { tApp } from "./app";

describe("tApp", () => {
  it("provides server-safe app metadata strings", () => {
    expect(tApp("metadataTitle")).toBe("ILB Incubator");
    expect(tApp("metadataDescription")).toContain("ILB Incubator");
  });
});
