import { describe, expect, it } from "vitest";

import { statusColor } from "./format";

describe("statusColor", () => {
  it("colors exact normalized statuses without substring false positives", () => {
    expect(statusColor("active")).toBe("green");
    expect(statusColor("inactive")).toBe("default");
    expect(statusColor("in_progress")).toBe("blue");
    expect(statusColor("overdue")).toBe("red");
  });
});
