import { describe, expect, it } from "vitest";

import { decodeAccessTokenPayload } from "./accessTokenClaims";

function makeJwt(payload: Record<string, unknown>): string {
  const header = Buffer.from(JSON.stringify({ alg: "none" }), "utf8").toString("base64url");
  const body = Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
  return `${header}.${body}.sig`;
}

describe("decodeAccessTokenPayload", () => {
  it("decodes a JWT payload segment", () => {
    const token = makeJwt({
      sub: "u-1",
      user_id: "legacy-u-1",
      role: "director",
      company_id: "c-9",
    });
    const claims = decodeAccessTokenPayload(token);
    expect(claims?.sub).toBe("u-1");
    expect(claims?.user_id).toBe("legacy-u-1");
    expect(claims?.role).toBe("director");
    expect(claims?.company_id).toBe("c-9");
  });

  it("returns null for invalid input", () => {
    expect(decodeAccessTokenPayload(null)).toBeNull();
    expect(decodeAccessTokenPayload("not-a-jwt")).toBeNull();
    expect(decodeAccessTokenPayload("a.b")).toBeNull();
  });
});
