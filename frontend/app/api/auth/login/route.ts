import { NextResponse, type NextRequest } from "next/server";

import { getRefreshTokenCookieName } from "@/lib/auth/cookies";

function upstreamLoginUrl(): string {
  const base =
    process.env.INTERNAL_API_URL?.trim() ||
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    "http://localhost/api";
  return `${base.replace(/\/$/, "")}/auth/login`;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  if (!body || typeof body !== "object") {
    return NextResponse.json({ detail: "Expected JSON object" }, { status: 400 });
  }

  const email = (body as { email?: unknown }).email;
  const password = (body as { password?: unknown }).password;
  if (typeof email !== "string" || typeof password !== "string") {
    return NextResponse.json({ detail: "email and password are required" }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(upstreamLoginUrl(), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    return NextResponse.json({ detail: "Auth service unreachable" }, { status: 502 });
  }

  let data: unknown;
  try {
    data = await upstream.json();
  } catch {
    return NextResponse.json({ detail: "Invalid auth response" }, { status: 502 });
  }

  if (!upstream.ok) {
    return NextResponse.json(data, { status: upstream.status });
  }

  const record = data as { access?: unknown; refresh?: unknown };
  const access = record.access;
  const refresh = record.refresh;
  if (typeof access !== "string" || typeof refresh !== "string") {
    return NextResponse.json(
      { detail: "Invalid token payload from auth service" },
      { status: 502 },
    );
  }

  const response = NextResponse.json({ access });
  const cookieName = getRefreshTokenCookieName();
  response.cookies.set(cookieName, refresh, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
    secure: process.env.NODE_ENV === "production",
  });
  return response;
}
