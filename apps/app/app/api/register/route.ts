import { NextResponse } from "next/server";

import { callBackend, isSameOrigin } from "@/lib/backend";

export async function POST(request: Request) {
  if (!isSameOrigin(request)) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const response = await callBackend("/auth/register", {
    method: "POST",
    body: JSON.stringify(await request.json()),
  });
  const payload = await response.json();
  return NextResponse.json(payload, { status: response.status });
}
