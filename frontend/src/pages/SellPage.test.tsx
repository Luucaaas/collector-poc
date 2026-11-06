import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Article } from "../api/types";
import { json, problem, renderWithConfig, stubApi, type Call } from "../test/api";
import { SellPage } from "./SellPage";
import { authorLabel } from "./sell/ShopArticles";

vi.mock("react-oidc-context", () => ({ useAuth: () => ({ user: { access_token: "jeton-vendeur", profile: { sub: "u1" } } }) }));
afterEach(() => vi.unstubAllGlobals());

const SHOP = { id: "s1", owner_id: "u1", name: "Boutique Alice", description: null, seller_type: "INDIVIDUAL", created_at: "2026-11-01T00:00:00Z" };
const CATEGORIES = { items: [{ id: "c1", name: "Figurines", slug: "figurines", created_at: "2026-11-01T00:00:00Z" }], total: 1 };
const article = (over: Partial<Article> = {}): Article => ({
  id: "a1",
  shop_id: "s1",
  category_id: "c1",
  seller_id: "u1",
  title: "Boba Fett Kenner 1979",
  description: "Figurine originale Kenner de 1979, très bon état.",
  photo_urls: ["https://img.test/1.jpg"],
  price: "120.00",
  shipping_fee: "8.00",
  currency: "EUR",
  status: "PUBLISHED",
  rejection_reasons: [],
  created_at: "2026-11-02T14:05:00Z",
  ...over,
});

function api(opts: { shops?: unknown[]; extra?: (call: Call) => Response | undefined } = {}) {
  const shops = opts.shops ?? [SHOP];
  return stubApi((call) => {
    const custom = opts.extra?.(call);
    if (custom) return custom;
    if (call.path === "/shops/me") return json({ items: shops, total: shops.length });
    if (call.path === "/categories") return json(CATEGORIES);
    if (call.path.startsWith("/articles?shop_id=")) return json({ items: [article()], total: 1 });
    return problem(404);
  });
}

async function fillArticle(overrides: { description?: string; price?: string } = {}) {
  await screen.findByRole("form", { name: "Mettre un article en vente" });
  await userEvent.selectOptions(screen.getByLabelText("Catégorie"), "c1");
  await userEvent.type(screen.getByLabelText(/Titre de l'article/), "Boba Fett Kenner 1979");
  await userEvent.type(
    screen.getByLabelText(/Description de l'article/),
    overrides.description ?? "Figurine originale Kenner de 1979, très bon état.",
  );
  await userEvent.type(screen.getByLabelText(/Adresse de la photo/), "https://img.test/1.jpg");
  await userEvent.type(screen.getByLabelText(/Prix \(€\)/), overrides.price ?? "120,5");
}

describe("SellPage : boutiques", () => {
  it("crée une boutique puis recharge la liste", async () => {
    let shops: unknown[] = [];
    const calls = api({
      extra: (c) => {
        if (c.method === "POST" && c.path === "/shops") {
          shops = [SHOP];
          return json(SHOP, 201);
        }
        return c.path === "/shops/me" ? json({ items: shops, total: shops.length }) : undefined;
      },
    });
    renderWithConfig(<SellPage />);
    expect(await screen.findByText(/pas encore de boutique/)).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText(/Nom de la boutique/), "Boutique Alice");
    await userEvent.click(screen.getByRole("button", { name: "Créer la boutique" }));
    expect(await screen.findByText("Boutique « Boutique Alice » créée.")).toBeInTheDocument();
    const list = await screen.findByRole("list", { name: "Liste de mes boutiques" });
    expect(within(list).getByText("Particulier")).toBeInTheDocument();
    expect(calls.find((c) => c.method === "POST")?.body).toEqual({ name: "Boutique Alice" });
  });

  it("affiche le refus d'un numéro de téléphone et marque le champ", async () => {
    api({
      shops: [],
      extra: (c) =>
        c.method === "POST" ? problem(422, { errors: [{ field: "description", code: "CONTACT_PHONE" }] }) : undefined,
    });
    renderWithConfig(<SellPage />);
    await screen.findByText(/pas encore de boutique/);
    await userEvent.type(screen.getByLabelText(/Nom de la boutique/), "Boutique Bob");
    await userEvent.type(screen.getByLabelText(/Description de la boutique/), "Appelez le 06 12 34 56 78");
    await userEvent.click(screen.getByRole("button", { name: "Créer la boutique" }));
    expect(await screen.findByText(/aucun numéro de téléphone/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description de la boutique/)).toHaveAttribute("aria-invalid", "true");
  });
});

describe("SellPage : mise en vente", () => {
  it("publie un article accepté, prix envoyé en chaîne décimale", async () => {
    const calls = api({ extra: (c) => (c.method === "POST" && c.path === "/articles" ? json(article(), 201) : undefined) });
    renderWithConfig(<SellPage />);
    await fillArticle();
    await userEvent.click(screen.getByRole("button", { name: "Mettre en vente" }));
    expect(await screen.findByText("Article publié")).toBeInTheDocument();
    const body = calls.find((c) => c.method === "POST" && c.path === "/articles")?.body;
    expect(body).toMatchObject({ shop_id: "s1", category_id: "c1", price: "120.50", shipping_fee: "0.00", currency: "EUR" });
    expect(typeof (body as { price: unknown }).price).toBe("string");
  });

  it("affiche un article rejeté avec ses motifs traduits", async () => {
    api({
      extra: (c) =>
        c.method === "POST" && c.path === "/articles"
          ? json(article({ status: "REJECTED", rejection_reasons: ["CONTACT_EMAIL", "CONTACT_PHONE"] }), 201)
          : undefined,
    });
    renderWithConfig(<SellPage />);
    await fillArticle({ description: "Écrivez à moi@example.com ou au 06 12 34 56 78" });
    await userEvent.click(screen.getByRole("button", { name: "Mettre en vente" }));
    expect(await screen.findByText("Article rejeté par le contrôle automatique")).toBeInTheDocument();
    expect(screen.getByText("le texte contient une adresse email")).toBeInTheDocument();
    expect(screen.getByText("le texte contient un numéro de téléphone")).toBeInTheDocument();
    expect(screen.queryByText("Article publié")).not.toBeInTheDocument();
    expect(screen.queryByText("Saisie à corriger")).not.toBeInTheDocument();
  });

  it("distingue un 422 de validation (erreur de saisie) d'un rejet", async () => {
    api({
      extra: (c) =>
        c.method === "POST" && c.path === "/articles"
          ? problem(422, { errors: [{ field: "title", code: "STRING_TOO_SHORT" }] })
          : undefined,
    });
    renderWithConfig(<SellPage />);
    await fillArticle();
    await userEvent.click(screen.getByRole("button", { name: "Mettre en vente" }));
    expect(await screen.findByText("Saisie à corriger")).toBeInTheDocument();
    expect(screen.getByText(/titre \(texte trop court\)/)).toBeInTheDocument();
    expect(screen.queryByText("Article rejeté par le contrôle automatique")).not.toBeInTheDocument();
  });

  it("refuse côté navigateur un prix nul ou à trois décimales, sans appeler l'API", async () => {
    const calls = api();
    renderWithConfig(<SellPage />);
    await fillArticle({ price: "0" });
    await userEvent.click(screen.getByRole("button", { name: "Mettre en vente" }));
    expect(await screen.findByText("Le prix doit être supérieur à 0.")).toBeInTheDocument();
    await userEvent.clear(screen.getByLabelText(/Prix \(€\)/));
    await userEvent.type(screen.getByLabelText(/Prix \(€\)/), "1.234");
    await userEvent.click(screen.getByRole("button", { name: "Mettre en vente" }));
    expect(await screen.findByText(/montant valide/)).toBeInTheDocument();
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });
});

describe("authorLabel", () => {
  it("dit « par vous » pour l'utilisateur connecté, sinon abrège l'identifiant", () => {
    expect(authorLabel("u1", "u1")).toBe("par vous");
    expect(authorLabel("a7f3c2e1-5b4d-4c3a-9e8f-1d2c3b4a5f60", "u1")).toBe("par a7f3c2e1…");
    expect(authorLabel("u1", undefined)).toBe("par u1…");
  });
});

describe("SellPage : prix des articles", () => {
  const priceForm = () => screen.findByRole("form", { name: /Modifier le prix de Boba Fett/ });

  it("modifie le prix et affiche l'historique", async () => {
    let history: unknown[] = [];
    const calls = api({
      extra: (c) => {
        if (c.method === "PUT") {
          history = [{ old_price: "120.00", new_price: "95.00", changed_by: "u1", changed_at: "2026-11-02T15:00:00Z" }];
          return json(article({ price: "95.00" }));
        }
        if (c.path === "/articles/a1/price-history") return json({ items: history, total: history.length });
        return undefined;
      },
    });
    renderWithConfig(<SellPage />);
    const form = await priceForm();
    await userEvent.type(within(form).getByLabelText(/Nouveau prix/), "95");
    await userEvent.click(within(form).getByRole("button", { name: "Modifier le prix" }));
    expect(await screen.findByText(/Prix modifié : 95,00/)).toBeInTheDocument();
    expect(calls.find((c) => c.method === "PUT")).toMatchObject({ path: "/articles/a1/price", body: { price: "95.00" } });

    await userEvent.click(screen.getByRole("button", { name: "Historique des prix" }));
    const table = await screen.findByRole("table", { name: "Historique des prix" });
    const cells = within(table).getAllByRole("cell").map((c) => c.textContent?.replace(/\s/g, " "));
    expect(cells[1]).toBe("120,00 €");
    expect(cells[2]).toBe("95,00 €");
    expect(cells[3]).toBe("par vous");
  });

  it("dit qu'un prix identique ne change rien, sans appeler l'API", async () => {
    const calls = api();
    renderWithConfig(<SellPage />);
    const form = await priceForm();
    await userEvent.type(within(form).getByLabelText(/Nouveau prix/), "120,00");
    await userEvent.click(within(form).getByRole("button", { name: "Modifier le prix" }));
    expect(await screen.findByText(/identique au prix actuel/)).toBeInTheDocument();
    expect(calls.some((c) => c.method === "PUT")).toBe(false);
  });

  it("affiche le conflit 409 d'un article non publié", async () => {
    api({ extra: (c) => (c.method === "PUT" ? problem(409) : undefined) });
    renderWithConfig(<SellPage />);
    const form = await priceForm();
    await userEvent.type(within(form).getByLabelText(/Nouveau prix/), "95");
    await userEvent.click(within(form).getByRole("button", { name: "Modifier le prix" }));
    expect(await screen.findByText("Cet article n'est plus publié : son prix ne peut pas être modifié.")).toBeInTheDocument();
  });

  it("désactive le bouton pendant l'envoi (pas de double soumission)", async () => {
    let release: (r: Response) => void = () => {};
    const pending = new Promise<Response>((resolve) => (release = resolve));
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string, init?: RequestInit) => {
        const url = new URL(input);
        const path = url.pathname.replace(/^.*\/api\/v1/, "") + url.search;
        calls.push(`${init?.method ?? "GET"} ${path}`);
        if (init?.method === "PUT") return pending;
        if (path === "/shops/me") return Promise.resolve(json({ items: [SHOP], total: 1 }));
        if (path === "/categories") return Promise.resolve(json(CATEGORIES));
        return Promise.resolve(json({ items: [article()], total: 1 }));
      }),
    );
    renderWithConfig(<SellPage />);
    const form = await priceForm();
    await userEvent.type(within(form).getByLabelText(/Nouveau prix/), "95");
    const button = within(form).getByRole("button", { name: "Modifier le prix" });
    await userEvent.click(button);
    await waitFor(() => expect(within(form).getByRole("button", { name: "Envoi…" })).toBeDisabled());
    release(json(article({ price: "95.00" })));
    await waitFor(() => expect(calls.filter((c) => c.startsWith("PUT"))).toHaveLength(1));
  });
});
