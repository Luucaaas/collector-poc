import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AppNotification } from "../api/types";
import { json, problem, renderWithConfig, stubApi, type Call } from "../test/api";
import { InterestsPage } from "./InterestsPage";

vi.mock("react-oidc-context", () => ({ useAuth: () => ({ user: { access_token: "jeton-acheteur" } }) }));
afterEach(() => vi.unstubAllGlobals());

const CATEGORIES = {
  items: [
    { id: "c1", name: "Figurines", slug: "figurines", created_at: "2026-11-01T00:00:00Z" },
    { id: "c2", name: "Cartes", slug: "cartes", created_at: "2026-11-01T00:00:00Z" },
  ],
  total: 2,
};
const NOTIFICATIONS: AppNotification[] = [
  {
    id: "n2",
    type: "PRICE_CHANGED",
    article_id: "a1",
    content: { title: "Boba Fett Kenner 1979", old_price: "120.00", new_price: "95.00", currency: "EUR" },
    created_at: "2026-11-02T15:00:00Z",
  },
  {
    id: "n1",
    type: "NEW_ARTICLE",
    article_id: "a1",
    content: { title: "Boba Fett Kenner 1979", price: "120.00", currency: "EUR" },
    created_at: "2026-11-02T14:05:00Z",
  },
];

function api(extra: (call: Call) => Response | undefined = () => undefined) {
  return stubApi((call) => {
    const custom = extra(call);
    if (custom) return custom;
    if (call.path === "/categories") return json(CATEGORIES);
    if (call.path === "/me/interests") return json({ category_ids: ["c2"] });
    if (call.path === "/me/preferences") return json({ new_article: true, price_changed: true });
    if (call.path.startsWith("/me/notifications")) return json({ items: NOTIFICATIONS, total: 2 });
    return problem(404);
  });
}

describe("InterestsPage", () => {
  it("pré-coche la sélection actuelle et enregistre les centres d'intérêt", async () => {
    const calls = api((c) => (c.method === "PUT" && c.path === "/me/interests" ? json(c.body) : undefined));
    renderWithConfig(<InterestsPage />);
    const figurines = await screen.findByRole("checkbox", { name: "Figurines" });
    expect(screen.getByRole("checkbox", { name: "Cartes" })).toBeChecked();
    expect(figurines).not.toBeChecked();

    await userEvent.click(figurines);
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer mes centres d'intérêt" }));

    expect(await screen.findByText("Centres d'intérêt enregistrés.")).toBeInTheDocument();
    const put = calls.find((c) => c.method === "PUT" && c.path === "/me/interests");
    expect((put?.body as { category_ids: string[] }).category_ids.sort()).toEqual(["c1", "c2"]);
  });

  it("affiche le refus de plus de 20 catégories", async () => {
    api((c) =>
      c.method === "PUT" && c.path === "/me/interests"
        ? problem(422, { errors: [{ field: "category_ids", code: "TOO_MANY_CATEGORIES" }] })
        : undefined,
    );
    renderWithConfig(<InterestsPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Enregistrer mes centres d'intérêt" }));
    expect(await screen.findByText(/plus de 20 catégories/)).toBeInTheDocument();
  });

  it("enregistre les préférences de notification", async () => {
    const calls = api((c) => (c.method === "PUT" && c.path === "/me/preferences" ? json(c.body) : undefined));
    renderWithConfig(<InterestsPage />);
    const priceChanged = await screen.findByRole("checkbox", { name: "Être prévenu d'un changement de prix" });
    expect(priceChanged).toBeChecked();
    await userEvent.click(priceChanged);
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer mes préférences" }));
    expect(await screen.findByText("Préférences enregistrées.")).toBeInTheDocument();
    expect(calls.find((c) => c.method === "PUT" && c.path === "/me/preferences")?.body).toEqual({
      new_article: true,
      price_changed: false,
    });
  });

  it("affiche les deux types de notification en texte lisible", async () => {
    const calls = api();
    renderWithConfig(<InterestsPage />);
    const list = await screen.findByRole("list", { name: "Liste des notifications" });
    const items = within(list).getAllByRole("listitem").map((li) => li.textContent?.replace(/\s/g, " "));
    expect(items[0]).toContain("Changement de prix : « Boba Fett Kenner 1979 » passe de 120,00 € à 95,00 €");
    expect(items[1]).toContain("Nouvel article : « Boba Fett Kenner 1979 » à 120,00 €");
    expect(calls.some((c) => c.path === "/me/notifications?limit=10&offset=0")).toBe(true);
  });

  it("recharge les notifications avec « Actualiser » et gère la liste vide", async () => {
    let empty = true;
    const calls = api((c) =>
      c.path.startsWith("/me/notifications") ? json(empty ? { items: [], total: 0 } : { items: NOTIFICATIONS, total: 2 }) : undefined,
    );
    renderWithConfig(<InterestsPage />);
    expect(await screen.findByText("Aucune notification pour le moment.")).toBeInTheDocument();
    empty = false;
    await userEvent.click(screen.getByRole("button", { name: "Actualiser" }));
    expect(await screen.findByRole("list", { name: "Liste des notifications" })).toBeInTheDocument();
    expect(calls.filter((c) => c.path.startsWith("/me/notifications"))).toHaveLength(2);
  });
});
