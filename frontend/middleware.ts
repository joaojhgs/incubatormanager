import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { isClientRole, isStaffRole } from "@/lib/auth/constants";
import { getRefreshTokenCookieName } from "@/lib/auth/cookies";
import { getRouteGate } from "@/lib/auth/routeGate";
import { verifyRefreshJwtHS256 } from "@/lib/auth/sessionJwt";

function safeInternalPath(next: string | null): string | null {
  if (!next || !next.startsWith("/") || next.startsWith("//")) return null;
  return next;
}

export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const cookieName = getRefreshTokenCookieName();
  const raw = request.cookies.get(cookieName)?.value;
  const secret = process.env.AUTH_JWT_SECRET;
  const payload = await verifyRefreshJwtHS256(raw, secret);
  const role = payload?.role;
  const hasSession = Boolean(payload && typeof role === "string");

  if (pathname === "/login" || pathname.startsWith("/login/")) {
    if (hasSession) {
      if (isClientRole(role)) {
        return NextResponse.redirect(new URL("/portal", request.url));
      }
      if (isStaffRole(role)) {
        const next = safeInternalPath(request.nextUrl.searchParams.get("next"));
        return NextResponse.redirect(new URL(next ?? "/dashboard", request.url));
      }
    }
    return NextResponse.next();
  }

  const gate = getRouteGate(pathname);
  if (gate === "public") {
    return NextResponse.next();
  }

  if (!hasSession) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login);
  }

  if (gate === "staff" && !isStaffRole(role)) {
    if (isClientRole(role)) {
      return NextResponse.redirect(new URL("/portal", request.url));
    }
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login);
  }

  if (gate === "client" && !isClientRole(role)) {
    if (isStaffRole(role)) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
