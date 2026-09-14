import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("communicates the audit purpose", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: "Conoce mejor tu empresa" })).toBeInTheDocument();
  });
});
