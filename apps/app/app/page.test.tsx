import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import Home from "./page";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function searchWith(result: () => Promise<Response>) {
  vi.stubGlobal("fetch", vi.fn(async (path: string) => {
    if (path.endsWith("/session/me")) return Response.json({
      email: "owner@example.com", organization_name: "Test", role: "owner",
      permissions: ["commercial.read", "commercial.write"],
    });
    if (path.endsWith("/discovery/search")) return result();
    if (path.endsWith("/today")) return Response.json({ calls_completed: 0,
      overdue_actions: 0, hot_leads: 0, next_actions: [] });
    return Response.json([]);
  }));
  render(<Home />);
  fireEvent.click(await screen.findByRole("button", { name: "Discovery" }));
  fireEvent.change(screen.getByLabelText("Localidad o latitud,longitud"), { target: { value: "Madrid" } });
  fireEvent.click(screen.getByRole("button", { name: "Buscar empresas" }));
}

describe("Commercial home", () => {
  it("identifies the internal commercial product", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 401 })));
    render(<Home />);
    expect(await screen.findByRole("heading", { name: "Control comercial" })).toBeInTheDocument();
  });

  it("shows imported and duplicate counts and releases the button", async () => {
    await searchWith(async () => Response.json({ processed_count: 5, created_count: 4,
      duplicate_count: 1, failed_count: 0 }));
    expect(await screen.findByRole("status")).toHaveTextContent("5 empresas encontradas: 4 nuevas, 1 duplicadas");
    expect(screen.getByRole("button", { name: "Buscar empresas" })).toBeEnabled();
  });

  it("explains zero coverage instead of claiming there are no companies", async () => {
    await searchWith(async () => Response.json({ processed_count: 0, created_count: 0,
      duplicate_count: 0, failed_count: 0 }));
    expect(await screen.findByRole("status")).toHaveTextContent("No significa que no existan empresas");
  });

  it("shows provider errors and permits a retry", async () => {
    await searchWith(async () => Response.json({ detail: "Proveedor no disponible" }, { status: 503 }));
    expect(await screen.findByText("Proveedor no disponible")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Buscar empresas" })).toBeEnabled();
  });

  it("distinguishes connection failure from a search timeout", async () => {
    await searchWith(async () => { throw new TypeError("Failed to fetch"); });
    expect(await screen.findByText(/No se pudo conectar con el CRM/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Buscar empresas" })).toBeEnabled();
  });
});
