import { NextResponse } from "next/server";

import { callBackend, isSameOrigin } from "@/lib/backend";

export async function POST(request: Request) {
  if (!isSameOrigin(request)) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const response = await callBackend("/auth/password-reset", {
    method: "POST",
    body: JSON.stringify(await request.json()),
  });
  if (response.status === 204) return new NextResponse(null, { status: 204 });
  return NextResponse.json(await response.json(), { status: response.status });
}
