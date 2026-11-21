import { StrictMode } from "react";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { InterestsPage } from "../pages/InterestsPage";
import { ConfigContext } from "../config";
import { CONFIG, json, stubApi, type Call } from "../test/api";
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

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

/** Answers every call; `total` is the number of notifications of the buyer. */
function stubBuyerApi(total = 0) {
  return stubApi((call: Call) => {
    if (call.path.startsWith("/me/notifications")) return json({ items: [], total });
    if (call.path.startsWith("/me/")) return json(call.path === "/me/interests" ? { category_ids: [] } : { new_article: true, price_changed: true });
    return json({ items: [], total: 0 });
  });
}

function renderLayout(roles: string[] | null) {
  stubBuyerApi();
  auth.current =
    roles === null
      ? { isLoading: false, isAuthenticated: false, user: null, signinRedirect: vi.fn() }
      : {
          isLoading: false,
          isAuthenticated: true,
          user: { access_token: fakeAccessToken(roles), profile: { preferred_username: "chloe" } },
        };
  render(
    <ConfigContext.Provider value={CONFIG}>
      <MemoryRouter>
        <Layout />
      </MemoryRouter>
    </ConfigContext.Provider>,
  );
}

describe("Layout: menus by role", () => {
  it("a buyer-only user sees neither \"Vendre\" nor \"Catégories\"", () => {
    renderLayout(["buyer"]);
    expect(screen.getByRole("link", { name: "Catalogue" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Mes centres d'intérêt/ })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Vendre" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Catégories" })).not.toBeInTheDocument();
  });

  it("a seller sees \"Vendre\", an admin sees \"Catégories\"", () => {
    renderLayout(["seller", "admin"]);
    expect(screen.getByRole("link", { name: "Vendre" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Catégories" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Mes centres d'intérêt/ })).not.toBeInTheDocument();
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

  it("names the mobile menu dialog and lists its links as list items", async () => {
    setMobile(true);
    renderLayout(["buyer"]);
    await userEvent.click(screen.getByRole("button", { name: "Ouvrir le menu" }));
    const dialog = await screen.findByRole("dialog", { name: "Menu" });
    expect(within(dialog).getAllByRole("listitem")).toHaveLength(3);
  });

  it("references the drawer from the menu button only while the drawer is mounted", async () => {
    setMobile(true);
    renderLayout(["buyer"]);
    const button = screen.getByRole("button", { name: "Ouvrir le menu" });
    expect(button).not.toHaveAttribute("aria-controls");
    await userEvent.click(button);
    await screen.findByRole("link", { name: /Mes centres d'intérêt/ });
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

const notificationCalls = (calls: Call[]) => calls.filter((c) => c.path.startsWith("/me/notifications")).length;

function renderRoutes(roles: string[], path: string) {
  auth.current = {
    isLoading: false,
    isAuthenticated: true,
    user: { access_token: fakeAccessToken(roles), profile: { preferred_username: "chloe", sub: "u1" } },
  };
  render(
    <ConfigContext.Provider value={CONFIG}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="centres-interet" element={<InterestsPage />} />
            <Route path="catalogue" element={<p>Catalogue</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </ConfigContext.Provider>,
  );
}

describe("Layout: notification badge", () => {
  it("shows the number of notifications to a buyer, with an accessible name", async () => {
    stubBuyerApi(3);
    renderRoutes(["buyer"], "/catalogue");
    const link = await screen.findByRole("link", { name: /^Mes centres d'intérêt \(3 notifications\)$/ });
    expect(link).toHaveTextContent("3");
  });

  it("uses the singular for one notification and \"99+\" above 99", async () => {
    stubBuyerApi(1);
    renderRoutes(["buyer"], "/catalogue");
    expect(await screen.findByRole("link", { name: /\(1 notification\)/ })).toBeInTheDocument();
  });

  it("shows \"99+\" for a very large number", async () => {
    stubBuyerApi(250);
    renderRoutes(["buyer"], "/catalogue");
    expect(await screen.findByText("99+")).toBeInTheDocument();
  });

  it("shows no badge when the buyer has no notification", async () => {
    const calls = stubBuyerApi(0);
    renderRoutes(["buyer"], "/catalogue");
    await screen.findByRole("link", { name: "Mes centres d'intérêt" });
    await vi.waitFor(() => expect(notificationCalls(calls)).toBe(1));
    expect(screen.getByRole("link", { name: "Mes centres d'intérêt" })).toBeInTheDocument();
  });

  it("is never shown, and nothing is requested, for a seller or an admin", async () => {
    const calls = stubBuyerApi(5);
    renderRoutes(["seller", "admin"], "/catalogue");
    await screen.findByRole("link", { name: "Vendre" });
    expect(screen.queryByText("5")).not.toBeInTheDocument();
    expect(notificationCalls(calls)).toBe(0);
  });

  it("is shown in the mobile menu too", async () => {
    setMobile(true);
    stubBuyerApi(2);
    renderRoutes(["buyer"], "/catalogue");
    await userEvent.click(screen.getByRole("button", { name: "Ouvrir le menu" }));
    expect(await screen.findByRole("link", { name: /^Mes centres d'intérêt \(2 notifications\)$/ })).toBeInTheDocument();
  });

  it("is fed by a single polling loop, shared with the notifications page", async () => {
    vi.useFakeTimers();
    const calls = stubBuyerApi(2);
    renderRoutes(["buyer"], "/centres-interet");
    await act(() => vi.advanceTimersByTimeAsync(0));
    expect(notificationCalls(calls)).toBe(1);
    await act(() => vi.advanceTimersByTimeAsync(10_000));
    expect(notificationCalls(calls)).toBe(2);
    await act(() => vi.advanceTimersByTimeAsync(10_000));
    expect(notificationCalls(calls)).toBe(3);
  });
});

describe("Layout: focus after navigation", () => {
  it("does not move the focus on the first display, even when StrictMode replays the effects", async () => {
    stubBuyerApi(0);
    auth.current = { isLoading: false, isAuthenticated: false, user: null, signinRedirect: vi.fn() };
    render(
      <StrictMode>
        <ConfigContext.Provider value={CONFIG}>
          <MemoryRouter initialEntries={["/catalogue"]}>
            <Routes>
              <Route element={<Layout />}>
                <Route path="catalogue" element={<p>Catalogue</p>} />
              </Route>
            </Routes>
          </MemoryRouter>
        </ConfigContext.Provider>
      </StrictMode>,
    );
    await screen.findByText("Catalogue", { selector: "p" });
    expect(screen.getByRole("main")).not.toHaveFocus();
  });

  it("moves the focus to the content when the page changes, not on the first display", async () => {
    stubBuyerApi(0);
    renderRoutes(["buyer"], "/centres-interet");
    await screen.findByRole("heading", { level: 1, name: "Mes centres d'intérêt" });
    expect(screen.getByRole("main")).not.toHaveFocus();
    await userEvent.click(screen.getByRole("link", { name: "Catalogue" }));
    await screen.findByText("Catalogue", { selector: "p" });
    expect(screen.getByRole("main")).toHaveFocus();
  });
});
