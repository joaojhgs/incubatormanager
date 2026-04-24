/**
 * Maps URL paths to middleware protection mode.
 * Staff UI lives at first-level segments (route group `(staff)` is not in the URL).
 */

export type RouteGate = "public" | "staff" | "client";

const STAFF_FIRST_SEGMENTS = new Set([
  "dashboard",
  "companies",
  "contracts",
  "finance",
  "spaces",
  "bookings",
  "inventory",
  "tickets",
  "users",
]);

export function getRouteGate(pathname: string): RouteGate {
  const path = pathname.split("?")[0] ?? pathname;
  if (path === "/login" || path.startsWith("/login/")) {
    return "public";
  }
  if (path === "/" || path === "") {
    return "staff";
  }
  const parts = path.split("/").filter(Boolean);
  const first = parts[0];
  if (!first) {
    return "staff";
  }
  if (first === "portal") {
    return "client";
  }
  if (STAFF_FIRST_SEGMENTS.has(first)) {
    return "staff";
  }
  return "public";
}
