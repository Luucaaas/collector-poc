import { screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Article } from "../api/types";
import { json, problem, renderWithConfig, stubApi } from "../test/api";
import { fakeAccessToken } from "../test/jwt";
import { ArticleDetailPage } from "./ArticleDetailPage";

let user: { access_token: string; profile: { sub: string } } | null;
vi.mock("react-oidc-context", () => ({ useAuth: () => ({ user }) }));

const article = (over: Partial<Article> = {}): Article => ({
  id: "a1",
  shop_id: "s1",
  category_id: "c1",
  seller_id: "u1",
  title: "Boba Fett Kenner 1979",
  description: "Figurine d'origine.\nBoîte incluse.",
  photo_urls: [],
  price: "95.00",
  shipping_fee: "8.00",
  currency: "EUR",
  status: "PUBLISHED",
  rejection_reasons: [],
  created_at: "2026-11-02T14:05:00Z",
  ...over,
});
const HISTORY = {
  items: [{ old_price: "120.00", new_price: "95.00", changed_by: "u1", changed_at: "2026-11-03T09:00:00Z" }],
  total: 1,
};

function serve(art: Article | Response, history: Response = json(HISTORY)) {
  return stubApi((call) => {
    if (call.path.startsWith("/categories")) return json({ items: [{ id: "c1", name: "Figurines", slug: "f", created_at: "x" }], total: 1 });
    if (call.path.startsWith("/shops/")) return json({ id: "s1", name: "Boutique Rétro" });
    if (call.path.endsWith("/price-history")) return history;
    return art instanceof Response ? art : json(art);
  });
}

const renderPage = () =>
  renderWithConfig(
    <MemoryRouter initialEntries={["/catalogue/a1"]}>
      <Routes>
        <Route path="/catalogue/:articleId" element={<ArticleDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );

beforeEach(() => {
  user = null;
});
afterEach(() => vi.unstubAllGlobals());

describe("ArticleDetailPage", () => {
  it("shows the article with French money formats, category and shop, without history for a visitor", async () => {
    const calls = serve(article());
    renderPage();
    expect(await screen.findByRole("heading", { level: 1, name: "Boba Fett Kenner 1979" })).toBeInTheDocument();
    expect(document.body.textContent?.replace(/\s/g, " ")).toContain("95,00 €");
    expect(document.body.textContent?.replace(/\s/g, " ")).toContain("Frais de port : 8,00 €");
    expect(await screen.findByText("Figurines")).toBeInTheDocument();
    expect(await screen.findByText(/Boutique : Boutique Rétro/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Retour au catalogue/ })).toHaveAttribute("href", "/catalogue");
    expect(screen.queryByText("Historique des prix")).not.toBeInTheDocument();
    expect(calls.some((c) => c.path.endsWith("/price-history"))).toBe(false);
  });

  it("shows a loading skeleton first", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    renderPage();
    expect(screen.getByRole("status", { name: "Chargement de l'article" })).toBeInTheDocument();
  });

  it("shows the translated error and a way back when the article is not found", async () => {
    serve(problem(404));
    renderPage();
    expect(await screen.findByText("La ressource demandée est introuvable.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Retour au catalogue/ })).toBeInTheDocument();
  });

  it("shows the price history to the owner", async () => {
    user = { access_token: fakeAccessToken(["seller"]), profile: { sub: "u1" } };
    serve(article());
    renderPage();
    expect(await screen.findByRole("heading", { name: "Historique des prix" })).toBeInTheDocument();
    const row = (await screen.findByText("03/11/2026", { exact: false })).closest("tr") as HTMLElement;
    expect(row.textContent?.replace(/\s/g, " ")).toContain("120,00 €");
    expect(row.textContent?.replace(/\s/g, " ")).toContain("95,00 €");
  });

  it("shows the price history to an admin and an empty message when nothing changed", async () => {
    user = { access_token: fakeAccessToken(["admin"]), profile: { sub: "other" } };
    serve(article(), json({ items: [], total: 0 }));
    renderPage();
    expect(await screen.findByText("Le prix n'a jamais été modifié.")).toBeInTheDocument();
  });

  it("does not request the history for another seller", async () => {
    user = { access_token: fakeAccessToken(["seller"]), profile: { sub: "u2" } };
    const calls = serve(article());
    renderPage();
    await screen.findByText(/Boutique : Boutique Rétro/);
    await waitFor(() => expect(calls.some((c) => c.path.endsWith("/price-history"))).toBe(false));
  });

  it("shows the translated rejection reasons of a rejected article", async () => {
    serve(article({ status: "REJECTED", rejection_reasons: ["CONTACT_EMAIL"] }));
    renderPage();
    expect(await screen.findByText(/Motifs du rejet : le texte contient une adresse email/)).toBeInTheDocument();
  });
});
