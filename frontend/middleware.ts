import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

/**
 * Route protection and auth will be implemented here (JWT cookie, role checks).
 */
export function middleware(_request: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except static files and Next.js internals.
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
