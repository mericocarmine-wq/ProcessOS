import { cookies } from "next/headers";

export const SESSION_COOKIE = "processos_session";

const apiUrl = process.env.PROCESSOS_API_URL ?? "http://localhost:8000";

export async function callBackend(path: string, init: RequestInit = {}, authenticated = false) {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (authenticated) {
    const token = (await cookies()).get(SESSION_COOKIE)?.value;
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(`${apiUrl}${path}`, { ...init, headers, cache: "no-store" });
}

export function isSameOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return true;
  return new URL(origin).host === request.headers.get("host");
}
