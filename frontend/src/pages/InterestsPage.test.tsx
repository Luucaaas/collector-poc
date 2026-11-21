import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AppNotification } from "../api/types";
import { json, problem, renderAsBuyer, stubApi, type Call } from "../test/api";
import { InterestsPage } from "./InterestsPage";

vi.mock("react-oidc-context", () => ({ useAuth: () => ({ user: { access_token: "jeton-acheteur" } }) }));
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

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
  it("pre-checks the current selection and saves the interests", async () => {
    const calls = api((c) => (c.method === "PUT" && c.path === "/me/interests" ? json(c.body) : undefined));
    renderAsBuyer(<InterestsPage />);
    const figurines = await screen.findByRole("checkbox", { name: "Figurines" });
    expect(screen.getByRole("checkbox", { name: "Cartes" })).toBeChecked();
    expect(figurines).not.toBeChecked();

    await userEvent.click(figurines);
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer mes centres d'intérêt" }));

    expect(await screen.findByText("Centres d'intérêt enregistrés.")).toBeInTheDocument();
    const put = calls.find((c) => c.method === "PUT" && c.path === "/me/interests");
    expect((put?.body as { category_ids: string[] }).category_ids.sort()).toEqual(["c1", "c2"]);
  });

  it("shows the refusal of more than 20 categories", async () => {
    api((c) =>
      c.method === "PUT" && c.path === "/me/interests"
        ? problem(422, { errors: [{ field: "category_ids", code: "TOO_MANY_CATEGORIES" }] })
        : undefined,
    );
    renderAsBuyer(<InterestsPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Enregistrer mes centres d'intérêt" }));
    expect(await screen.findByText(/plus de 20 catégories/)).toBeInTheDocument();
  });

  it("saves the notification preferences", async () => {
    const calls = api((c) => (c.method === "PUT" && c.path === "/me/preferences" ? json(c.body) : undefined));
    renderAsBuyer(<InterestsPage />);
    const priceChanged = await screen.findByRole("switch", { name: "Être prévenu d'un changement de prix" });
    expect(priceChanged).toBeChecked();
    await userEvent.click(priceChanged);
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer mes préférences" }));
    expect(await screen.findByText("Préférences enregistrées.")).toBeInTheDocument();
    expect(calls.find((c) => c.method === "PUT" && c.path === "/me/preferences")?.body).toEqual({
      new_article: true,
      price_changed: false,
    });
  });

  it("shows both notification types as readable text", async () => {
    const calls = api();
    renderAsBuyer(<InterestsPage />);
    const list = await screen.findByRole("list", { name: "Liste des notifications" });
    const items = within(list).getAllByRole("listitem").map((li) => li.textContent?.replace(/\s/g, " "));
    expect(items[0]).toContain("Changement de prix : « Boba Fett Kenner 1979 » passe de 120,00 € à 95,00 €");
    expect(items[1]).toContain("Nouvel article : « Boba Fett Kenner 1979 » à 120,00 €");
    expect(calls.some((c) => c.path === "/me/notifications?limit=10&offset=0")).toBe(true);
  });

  it("reloads notifications with \"Actualiser\" and handles the empty list", async () => {
    let empty = true;
    const calls = api((c) =>
      c.path.startsWith("/me/notifications") ? json(empty ? { items: [], total: 0 } : { items: NOTIFICATIONS, total: 2 }) : undefined,
    );
    renderAsBuyer(<InterestsPage />);
    expect(await screen.findByText("Aucune notification pour le moment.")).toBeInTheDocument();
    empty = false;
    await userEvent.click(screen.getByRole("button", { name: "Actualiser" }));
    expect(await screen.findByRole("list", { name: "Liste des notifications" })).toBeInTheDocument();
    expect(calls.filter((c) => c.path.startsWith("/me/notifications"))).toHaveLength(2);
  });

  it("links each notification to the article page, with a distinct accessible name", async () => {
    api();
    renderAsBuyer(<InterestsPage />);
    const links = await screen.findAllByRole("link", { name: "Voir l'article « Boba Fett Kenner 1979 »" });
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "/catalogue/a1");
  });

  it("shows new notifications without any click, through the periodic polling", async () => {
    vi.useFakeTimers();
    let items: AppNotification[] = [];
    const calls = api((c) =>
      c.path.startsWith("/me/notifications") ? json({ items, total: items.length }) : undefined,
    );
    renderAsBuyer(<InterestsPage />);
    await act(() => vi.advanceTimersByTimeAsync(0));
    expect(screen.getByText("Aucune notification pour le moment.")).toBeInTheDocument();
    items = NOTIFICATIONS;
    await act(() => vi.advanceTimersByTimeAsync(10_000));
    expect(screen.getByRole("list", { name: "Liste des notifications" })).toBeInTheDocument();
    expect(screen.getByText("2 notifications au total")).toBeInTheDocument();
    expect(calls.filter((c) => c.path.startsWith("/me/notifications"))).toHaveLength(2);
  });

  it("disables \"Actualiser\" while an update is running", async () => {
    let release: (r: Response) => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string) =>
        new URL(input).pathname.endsWith("/me/notifications")
          ? new Promise<Response>((r) => (release = r))
          : Promise.resolve(json(input.endsWith("/categories") ? CATEGORIES : { category_ids: [], new_article: true, price_changed: true })),
      ),
    );
    renderAsBuyer(<InterestsPage />);
    expect(await screen.findByRole("button", { name: "Actualiser" })).toBeDisabled();
    expect(screen.getByRole("status", { name: "Chargement des notifications" })).toBeInTheDocument();
    release(json({ items: NOTIFICATIONS, total: 2 }));
    expect(await screen.findByRole("list", { name: "Liste des notifications" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Actualiser" })).toBeEnabled();
  });

  it("keeps the notifications and warns when an update fails", async () => {
    let fail = false;
    api((c) => (fail && c.path.startsWith("/me/notifications") ? problem(500) : undefined));
    renderAsBuyer(<InterestsPage />);
    await screen.findByRole("list", { name: "Liste des notifications" });
    fail = true;
    await userEvent.click(screen.getByRole("button", { name: "Actualiser" }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Liste des notifications" })).toBeInTheDocument();
  });

  it("loads the other pages of notifications by offset", async () => {
    const calls = api((c) =>
      c.path.startsWith("/me/notifications")
        ? json({ items: c.path.includes("offset=10") ? [{ ...NOTIFICATIONS[1]!, id: "old" }] : NOTIFICATIONS, total: 11 })
        : undefined,
    );
    renderAsBuyer(<InterestsPage />);
    await userEvent.click(await screen.findByRole("button", { name: /page 2/i }));
    await vi.waitFor(() =>
      expect(within(screen.getByRole("list", { name: "Liste des notifications" })).getAllByRole("listitem")).toHaveLength(1),
    );
    expect(calls.some((c) => c.path === "/me/notifications?limit=10&offset=10")).toBe(true);
  });

  it("counts the followed categories live, flags unsaved changes, and blocks more than 20", async () => {
    const many = {
      items: Array.from({ length: 21 }, (_, i) => ({ id: `k${i}`, name: `Catégorie ${i}`, slug: `c${i}`, created_at: "2026-11-01T00:00:00Z" })),
      total: 21,
    };
    api((c) => (c.path === "/categories" ? json(many) : c.path === "/me/interests" ? json({ category_ids: ["k0"] }) : undefined));
    renderAsBuyer(<InterestsPage />);
    await screen.findByRole("checkbox", { name: "Catégorie 0" });
    expect(screen.getByText("1 sur 20 catégories au maximum.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("checkbox", { name: "Catégorie 1" }));
    expect(screen.getByText("2 sur 20 catégories au maximum. Modifications non enregistrées.")).toBeInTheDocument();
    for (let i = 2; i < 21; i++) await userEvent.click(screen.getByRole("checkbox", { name: `Catégorie ${i}` }));
    expect(screen.getByText(/plus de 20 catégories : décochez-en 1/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enregistrer mes centres d'intérêt" })).toBeDisabled();
  });

  it("explains each notification preference to assistive technologies", async () => {
    api();
    renderAsBuyer(<InterestsPage />);
    const sw = await screen.findByRole("switch", { name: "Être prévenu d'un nouvel article" });
    expect(sw).toHaveAccessibleDescription("Un article vient d'être publié dans l'une de vos catégories.");
  });

  it("has a single h1 and named groups for the forms", async () => {
    api();
    renderAsBuyer(<InterestsPage />);
    await screen.findByRole("checkbox", { name: "Cartes" });
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("group", { name: "Catégories suivies" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Préférences de notification" })).toBeInTheDocument();
  });
});
