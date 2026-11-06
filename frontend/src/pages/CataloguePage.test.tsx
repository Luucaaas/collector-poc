import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Article } from "../api/types";
import { ConfigContext } from "../config";
import { CataloguePage } from "./CataloguePage";

vi.mock("react-oidc-context", () => ({ useAuth: () => ({ user: null }) }));

const CONFIG = {
  authority: "https://auth.test/realms/collector",
  clientId: "collector-web",
  catalogApiUrl: "https://api.test/catalog/api/v1",
  notificationApiUrl: "https://api.test/notification/api/v1",
};
const CATEGORIES = {
  items: [
    { id: "c1", name: "Figurines", slug: "figurines", created_at: "2026-11-01T00:00:00Z" },
    { id: "c2", name: "Cartes", slug: "cartes", created_at: "2026-11-01T00:00:00Z" },
  ],
  total: 2,
};
const article = (over: Partial<Article>): Article => ({
  id: "a1",
  shop_id: "s1",
  category_id: "c1",
  seller_id: "u1",
  title: "Boba Fett Kenner 1979",
  description: "Figurine",
  photo_urls: ["https://img.test/1.jpg"],
  price: "120.00",
  shipping_fee: "8.00",
  currency: "EUR",
  status: "PUBLISHED",
  rejection_reasons: [],
  created_at: "2026-11-02T14:05:00Z",
  ...over,
});

let calls: string[];
function route(handler: (url: URL) => Response) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string) => {
      calls.push(input);
      return Promise.resolve(handler(new URL(input)));
    }),
  );
}

const renderPage = () =>
  render(
    <ConfigContext.Provider value={CONFIG}>
      <CataloguePage />
    </ConfigContext.Provider>,
  );

beforeEach(() => {
  calls = [];
});
afterEach(() => vi.unstubAllGlobals());

describe("CataloguePage", () => {
  it("liste les articles avec prix et frais de port en euros et la catégorie", async () => {
    route((url) =>
      url.pathname.endsWith("/categories")
        ? Response.json(CATEGORIES)
        : Response.json({ items: [article({})], total: 1 }),
    );
    renderPage();
    const item = (await screen.findByText("Boba Fett Kenner 1979")).closest("li") as HTMLElement;
    expect(item.textContent?.replace(/\s/g, " ")).toContain("120,00 €");
    expect(item.textContent?.replace(/\s/g, " ")).toContain("Frais de port : 8,00 €");
    await waitFor(() => expect(within(item).getByText("Figurines")).toBeInTheDocument());
    expect(calls.some((u) => u.includes("/articles?limit=12&offset=0"))).toBe(true);
  });

  it("filtre par catégorie", async () => {
    route((url) =>
      url.pathname.endsWith("/categories")
        ? Response.json(CATEGORIES)
        : Response.json({ items: [article({})], total: 1 }),
    );
    renderPage();
    await screen.findByText("Boba Fett Kenner 1979");
    await userEvent.click(screen.getByRole("combobox", { name: "Catégorie" }));
    await userEvent.click(await screen.findByRole("option", { name: "Cartes" }));
    await waitFor(() => expect(calls.some((u) => u.includes("category_id=c2"))).toBe(true));
  });

  it("affiche un message quand la liste est vide", async () => {
    route((url) =>
      url.pathname.endsWith("/categories") ? Response.json(CATEGORIES) : Response.json({ items: [], total: 0 }),
    );
    renderPage();
    expect(await screen.findByText("Aucun article à afficher pour le moment.")).toBeInTheDocument();
  });

  it("affiche l'erreur traduite quand l'API échoue", async () => {
    route((url) =>
      url.pathname.endsWith("/categories")
        ? Response.json(CATEGORIES)
        : new Response(JSON.stringify({ status: 500 }), { status: 500 }),
    );
    renderPage();
    expect(await screen.findByText(/Le serveur a rencontré une erreur/)).toBeInTheDocument();
  });

  it("pagine avec limit et offset", async () => {
    route((url) =>
      url.pathname.endsWith("/categories")
        ? Response.json(CATEGORIES)
        : Response.json({ items: [article({})], total: 30 }),
    );
    renderPage();
    await screen.findByText("Boba Fett Kenner 1979");
    await userEvent.click(screen.getByRole("button", { name: /page 2/i }));
    await waitFor(() => expect(calls.some((u) => u.includes("limit=12&offset=12"))).toBe(true));
  });
});
