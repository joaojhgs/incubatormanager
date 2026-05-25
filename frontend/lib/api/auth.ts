import { AUTH_LOGOUT_PATH } from "./constants";
import { getDefaultApiClient } from "./client";

/** Calls backend logout to revoke the refresh cookie/session when available. */
export async function logoutSession(): Promise<void> {
  await getDefaultApiClient().post(AUTH_LOGOUT_PATH, {});
}

/** Same-site fallback that asks the auth endpoint to clear the httpOnly refresh cookie. */
export function redirectToCookieClearingLogout(next = "/login"): void {
  if (typeof window === "undefined") return;
  const target = next.startsWith("/") && !next.startsWith("//") ? next : "/login";
  window.location.assign(`/api/auth/logout/?next=${encodeURIComponent(target)}`);
}
