import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { fakeAccessToken } from "../test/jwt";
import { Layout } from "./Layout";

const auth = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));
vi.mock("react-oidc-context", () => ({ useAuth: () => auth.current }));

function renderLayout(roles: string[]) {
  auth.current = {
    isLoading: false,
    isAuthenticated: true,
    user: { access_token: fakeAccessToken(roles), profile: { preferred_username: "chloe" } },
  };
  render(
    <MemoryRouter>
      <Layout />
    </MemoryRouter>,
  );
}

describe("Layout : menus selon les rôles", () => {
  it("un utilisateur buyer seul ne voit ni « Vendre » ni « Catégories »", () => {
    renderLayout(["buyer"]);
    expect(screen.getByRole("link", { name: "Catalogue" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Mes centres d'intérêt" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Vendre" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Catégories" })).not.toBeInTheDocument();
  });

  it("un vendeur voit « Vendre », un administrateur voit « Catégories »", () => {
    renderLayout(["seller", "admin"]);
    expect(screen.getByRole("link", { name: "Vendre" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Catégories" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Mes centres d'intérêt" })).not.toBeInTheDocument();
  });
});
