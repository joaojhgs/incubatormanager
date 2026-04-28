/** httpOnly refresh cookie set by the login proxy / backend (must match server-side name). */
export const DEFAULT_REFRESH_TOKEN_COOKIE_NAME = "ilb.refresh_token";

/** JWT `role` claim value for incubator client users (client portal). */
export const ROLE_CLIENT = "client";

/** Roles that may access staff route group `/(staff)` (JWT `role` claim). */
export const STAFF_ROLES: readonly string[] = ["director", "manager", "coordinator", "staff"];

export function isClientRole(role: unknown): role is string {
  return role === ROLE_CLIENT;
}

export function isStaffRole(role: unknown): boolean {
  if (typeof role !== "string" || !role) return false;
  return STAFF_ROLES.includes(role);
}

/** JWT `role` claim for Director-only staff screens (user administration). */
export const ROLE_DIRECTOR = "director";

export function isDirectorRole(role: unknown): boolean {
  return typeof role === "string" && role.toLowerCase() === ROLE_DIRECTOR;
}
