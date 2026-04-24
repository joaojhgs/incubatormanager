import { describe, expect, it } from "vitest";

import { getRouteGate } from "./routeGate";

describe("getRouteGate", () => {
  it("treats /login as public", () => {
    expect(getRouteGate("/login")).toBe("public");
    expect(getRouteGate("/login/reset")).toBe("public");
  });

  it("treats staff home as staff", () => {
    expect(getRouteGate("/")).toBe("staff");
    expect(getRouteGate("")).toBe("staff");
  });

  it("maps first-level staff segments", () => {
    expect(getRouteGate("/dashboard")).toBe("staff");
    expect(getRouteGate("/companies")).toBe("staff");
    expect(getRouteGate("/users")).toBe("staff");
  });

  it("maps client portal prefix", () => {
    expect(getRouteGate("/portal")).toBe("client");
    expect(getRouteGate("/portal/invoices")).toBe("client");
  });

  it("treats unknown top-level paths as public", () => {
    expect(getRouteGate("/booking-request")).toBe("public");
  });
});
