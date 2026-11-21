import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";

vi.mock("react-oidc-context", () => ({
  useAuth: () => ({ isLoading: false, isAuthenticated: false, user: null, signinRedirect: vi.fn() }),
}));

describe("App routing (lazy pages)", () => {
  it("shows the home page on / and the not-found page on an unknown address", async () => {
    const { unmount } = render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );
    expect(await screen.findByRole("heading", { level: 1, name: "Collector.shop" })).toBeInTheDocument();
    unmount();
    render(
      <MemoryRouter initialEntries={["/nimporte-quoi"]}>
        <App />
      </MemoryRouter>,
    );
    expect(await screen.findByRole("heading", { level: 1, name: "Page introuvable" })).toBeInTheDocument();
  });
});
