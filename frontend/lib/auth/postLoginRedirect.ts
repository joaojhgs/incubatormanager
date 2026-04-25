import { isClientRole, isStaffRole } from "@/lib/auth/constants";

/** Returns a safe same-origin path for redirects, or null if untrusted. */
export function safeInternalPath(next: string | null): string | null {
  if (!next || !next.startsWith("/") || next.startsWith("//")) return null;
  return next;
}

/**
 * Target path after a successful login, using role and optional `next` query
 * (mirrors middleware naming).
 */
export function getPostLoginPath(role: string, nextParam: string | null): string {
  const next = safeInternalPath(nextParam);
  if (isClientRole(role)) {
    if (next?.startsWith("/portal")) return next;
    return "/portal";
  }
  if (isStaffRole(role)) {
    if (next && !next.startsWith("/portal")) return next;
    return "/dashboard";
  }
  return "/dashboard";
}
