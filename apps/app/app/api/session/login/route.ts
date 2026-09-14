import { NextResponse } from "next/server";

import { callBackend, isSameOrigin, SESSION_COOKIE } from "@/lib/backend";

export async function POST(request: Request) {
  if (!isSameOrigin(request)) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const response = await callBackend("/auth/login", {
    method: "POST",
    body: JSON.stringify(await request.json()),
  });
  const payload = await response.json();
  if (!response.ok) return NextResponse.json(payload, { status: response.status });

  const result = NextResponse.json({ expires_at: payload.expires_at });
  result.cookies.set(SESSION_COOKIE, payload.access_token, {
    httpOnly: true,
    sameSite: "strict",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 30 * 60,
  });
  return result;
}
