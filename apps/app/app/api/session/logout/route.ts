import { NextResponse } from "next/server";

import { callBackend, isSameOrigin, SESSION_COOKIE } from "@/lib/backend";

export async function POST(request: Request) {
  if (!isSameOrigin(request)) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  await callBackend("/auth/logout", { method: "POST" }, true);
  const response = new NextResponse(null, { status: 204 });
  response.cookies.delete(SESSION_COOKIE);
  return response;
}
