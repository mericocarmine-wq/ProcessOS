import { NextResponse } from "next/server";

import { callBackend } from "@/lib/backend";

export async function GET() {
  const response = await callBackend("/auth/me", {}, true);
  const payload = await response.json();
  return NextResponse.json(payload, { status: response.status });
}
