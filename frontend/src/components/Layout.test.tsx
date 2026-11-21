import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fakeAccessToken } from "../test/jwt";
import { Layout } from "./Layout";

const auth = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));
vi.mock("react-oidc-context", () => ({ useAuth: () => auth.current }));

function setMobile(mobile: boolean) {
  vi.stubGlobal(
    "matchMedia",
    (query: string) => ({ matches: mobile && query.includes("max-width"), media: query, addEventListener() {}, removeEventListener() {} }),
  );
}

afterEach(() => vi.unstubAllGlobals());

function renderLayout(roles: string[] | null) {
  auth.current =
    roles === null
      ? { isLoading: false, isAuthenticated: false, user: null, signinRedirect: vi.fn() }
      : {
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

describe("Layout: menus by role", () => {
  it("a buyer-only user sees neither \"Vendre\" nor \"Catégories\"", () => {
    renderLayout(["buyer"]);
    expect(screen.getByRole("link", { name: "Catalogue" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Mes centres d'intérêt" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Vendre" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Catégories" })).not.toBeInTheDocument();
  });

  it("a seller sees \"Vendre\", an admin sees \"Catégories\"", () => {
    renderLayout(["seller", "admin"]);
    expect(screen.getByRole("link", { name: "Vendre" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Catégories" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Mes centres d'intérêt" })).not.toBeInTheDocument();
  });
});

describe("Layout: visitor, home link and mobile menu", () => {
  it("a visitor sees Accueil, Catalogue and Connexion only", () => {
    renderLayout(null);
    expect(screen.getByRole("link", { name: "Accueil" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Catalogue" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Vendre" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Connexion" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Collector.shop, accueil" })).toBeInTheDocument();
  });

  it("on a narrow screen the links are in a drawer opened by the menu button, filtered by role", async () => {
    setMobile(true);
    renderLayout(["seller"]);
    expect(screen.queryByRole("link", { name: "Vendre" })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Ouvrir le menu" }));
    expect(await screen.findByRole("link", { name: "Vendre" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Catégories" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Déconnexion" })).toBeInTheDocument();
  });

  it("references the drawer from the menu button only while the drawer is mounted", async () => {
    setMobile(true);
    renderLayout(["buyer"]);
    const button = screen.getByRole("button", { name: "Ouvrir le menu" });
    expect(button).not.toHaveAttribute("aria-controls");
    await userEvent.click(button);
    await screen.findByRole("link", { name: "Mes centres d'intérêt" });
    expect(button).toHaveAttribute("aria-controls", "mobile-menu");
  });

  it("shows the roles in French", () => {
    renderLayout(["buyer", "seller", "admin"]);
    expect(screen.getByText("acheteur")).toBeInTheDocument();
    expect(screen.getByText("vendeur")).toBeInTheDocument();
    expect(screen.getByText("administrateur")).toBeInTheDocument();
    expect(screen.queryByText("seller")).not.toBeInTheDocument();
  });

  it("offers a skip link to the main content", () => {
    renderLayout(["buyer"]);
    expect(screen.getByRole("link", { name: "Aller au contenu" })).toHaveAttribute("href", "#main");
    expect(screen.getByRole("main")).toHaveAttribute("id", "main");
  });
});
