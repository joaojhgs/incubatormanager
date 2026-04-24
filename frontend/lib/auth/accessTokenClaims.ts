export interface AccessTokenClaims {
  sub?: string;
  email?: string;
  role?: string;
  company_id?: string | null;
}

function base64UrlToUtf8(segment: string): string {
  if (typeof Buffer !== "undefined") {
    return Buffer.from(segment, "base64url").toString("utf8");
  }
  const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
  const pad = base64.length % 4 === 0 ? "" : "=".repeat(4 - (base64.length % 4));
  return atob(base64 + pad);
}

/**
 * Reads JWT payload JSON from an access token without cryptographic verification.
 * UI-only; APIs must still authorize server-side.
 */
export function decodeAccessTokenPayload(
  token: string | null | undefined,
): AccessTokenClaims | null {
  if (!token || typeof token !== "string") return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const json = base64UrlToUtf8(parts[1] ?? "");
    const data = JSON.parse(json) as AccessTokenClaims;
    return data && typeof data === "object" ? data : null;
  } catch {
    return null;
  }
}
