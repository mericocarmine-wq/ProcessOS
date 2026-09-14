import { NextResponse } from "next/server";

import { callBackend, isSameOrigin } from "@/lib/backend";

export async function POST(request: Request) {
  if (!isSameOrigin(request)) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const response = await callBackend("/auth/password-recovery", {
    method: "POST",
    body: JSON.stringify(await request.json()),
  });
  if (response.status === 204 || response.status === 202) {
    return new NextResponse(null, { status: response.status });
  }
  return NextResponse.json(await response.json(), { status: response.status });
}
