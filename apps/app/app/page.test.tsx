import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Commercial home", () => {
  it("identifies the internal commercial product", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: "ProcessOS Commercial" })).toBeInTheDocument();
  });
});
