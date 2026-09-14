import { NextResponse } from "next/server";

import { callBackend, isSameOrigin } from "@/lib/backend";

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: Request, context: RouteContext) {
  const method = request.method;
  if (method !== "GET" && !isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const suffix = (await context.params).path.join("/");
  const body = method === "GET" ? undefined : await request.text();
  const response = await callBackend(`/commercial/${suffix}`, { method, body }, true);
  if (response.status === 204) return new NextResponse(null, { status: 204 });
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return NextResponse.json(
      { detail: "El servicio comercial no pudo completar la operación." },
      { status: response.status },
    );
  }
  return NextResponse.json(await response.json(), { status: response.status });
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
