import { describe, expect, it } from "vitest";

import { statusLabel } from "./status";

describe("statusLabel", () => {
  it("localizes operational API statuses", () => {
    expect(statusLabel("Active")).toBe("Ativo");
    expect(statusLabel("pending")).toBe("Pendente");
    expect(statusLabel("In use")).toBe("Em utilização");
    expect(statusLabel("Waiting response")).toBe("A aguardar resposta");
  });

  it("normalizes API status separators and preserves unknown values", () => {
    expect(statusLabel("in_progress")).toBe("Em curso");
    expect(statusLabel("not-yet-mapped")).toBe("not-yet-mapped");
  });
});
