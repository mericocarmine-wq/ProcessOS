import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Home from "./page";

describe("Commercial home", () => {
  it("identifies the internal commercial product", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 401 })));
    render(<Home />);
    expect(await screen.findByRole("heading", { name: "Control comercial" })).toBeInTheDocument();
  });
});
