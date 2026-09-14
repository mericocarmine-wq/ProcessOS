import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("communicates the ProcessOS foundation", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: "ProcessOS" })).toBeInTheDocument();
  });
});

