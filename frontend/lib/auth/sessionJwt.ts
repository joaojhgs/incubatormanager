import * as jose from "jose";

/**
 * Verifies an HS256 JWT (intended for the httpOnly refresh cookie in middleware).
 */
export async function verifyRefreshJwtHS256(
  token: string | undefined,
  secret: string | undefined,
): Promise<jose.JWTPayload | null> {
  if (!token || !secret) return null;
  try {
    const key = new TextEncoder().encode(secret);
    const { payload } = await jose.jwtVerify(token, key, { algorithms: ["HS256"] });
    return payload;
  } catch {
    return null;
  }
}
