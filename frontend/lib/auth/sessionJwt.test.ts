import { SignJWT } from "jose";
import { describe, expect, it } from "vitest";

import { verifyRefreshJwtHS256 } from "./sessionJwt";

const secret = "unit-test-secret-at-least-32-chars!!";

describe("verifyRefreshJwtHS256", () => {
  it("returns payload for a valid HS256 token", async () => {
    const token = await new SignJWT({ role: "staff", sub: "user-1" })
      .setProtectedHeader({ alg: "HS256" })
      .setIssuedAt()
      .setExpirationTime("2h")
      .sign(new TextEncoder().encode(secret));

    const payload = await verifyRefreshJwtHS256(token, secret);
    expect(payload?.role).toBe("staff");
    expect(payload?.sub).toBe("user-1");
  });

  it("returns null when the secret does not match", async () => {
    const token = await new SignJWT({ role: "staff" })
      .setProtectedHeader({ alg: "HS256" })
      .setExpirationTime("2h")
      .sign(new TextEncoder().encode(secret));

    const payload = await verifyRefreshJwtHS256(token, "wrong-secret-wrong-secret-wrong");
    expect(payload).toBeNull();
  });

  it("returns null when token or secret is missing", async () => {
    expect(await verifyRefreshJwtHS256(undefined, secret)).toBeNull();
    expect(await verifyRefreshJwtHS256("x.y.z", undefined)).toBeNull();
  });
});
