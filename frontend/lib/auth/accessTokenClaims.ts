export interface AccessTokenClaims {
  sub?: string;
  email?: string;
  role?: string;
  company_id?: string | null;
}

function base64UrlToUtf8(segment: string): string {
  const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
  const pad = base64.length % 4 === 0 ? "" : "=".repeat(4 - (base64.length % 4));
  const bin = atob(base64 + pad);
  const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
  return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
}

/**
 * Reads JWT payload JSON from an access token without cryptographic verification.
 * UI-only; APIs must still authorize server-side.
 */
export function decodeAccessTokenPayload(
  token: string | null | undefined,
): AccessTokenClaims | null {
  if (!token || typeof token !== "string") return null;
  const trimmed = token.trim();
  const parts = trimmed.split(".");
  if (parts.length !== 3) return null;
  try {
    const json = base64UrlToUtf8(parts[1] ?? "");
    const data = JSON.parse(json) as AccessTokenClaims;
    return data && typeof data === "object" ? data : null;
  } catch {
    return null;
  }
}
