import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { fakeAccessToken } from "../test/jwt";
import { HomePage } from "./HomePage";

const auth = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));
vi.mock("react-oidc-context", () => ({ useAuth: () => auth.current }));

function renderHome(roles: string[] | null) {
  auth.current =
    roles === null
      ? { isAuthenticated: false, user: null }
      : { isAuthenticated: true, user: { access_token: fakeAccessToken(roles) } };
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );
}

describe("HomePage", () => {
  it("shows the heading, the title and the catalogue link to a visitor", () => {
    renderHome(null);
    expect(screen.getByRole("heading", { level: 1, name: "Collector.shop" })).toBeInTheDocument();
    expect(document.title).toBe("Accueil · Collector.shop");
    expect(screen.getByRole("link", { name: "Parcourir le catalogue" })).toHaveAttribute("href", "/catalogue");
    expect(screen.queryByRole("link", { name: "Mettre un article en vente" })).not.toBeInTheDocument();
  });

  it("adds role-specific shortcuts", () => {
    renderHome(["seller", "buyer"]);
    expect(screen.getByRole("link", { name: "Mettre un article en vente" })).toHaveAttribute("href", "/vendre");
    expect(screen.getByRole("link", { name: "Mes centres d'intérêt" })).toHaveAttribute("href", "/centres-interet");
  });
});
