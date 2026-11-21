import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RejectedArticlesProvider } from "../components/RejectedArticles";
import { ToastProvider } from "../components/Toast";
import type { Article } from "../api/types";
import { json, problem, renderWithConfig, stubApi, type Call } from "../test/api";
import { SellPage } from "./SellPage";

vi.mock("react-oidc-context", () => ({ useAuth: () => ({ user: { access_token: "jeton-vendeur", profile: { sub: "u1" } } }) }));
afterEach(() => vi.unstubAllGlobals());

const SHOP = { id: "s1", owner_id: "u1", name: "Boutique Alice", description: "Figurines rares", seller_type: "INDIVIDUAL", created_at: "2026-11-01T00:00:00Z" };
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

function api(extra?: (call: Call) => Response | undefined) {
  return stubApi((call) => {
    const custom = extra?.(call);
    if (custom) return custom;
    if (call.path === "/shops/me") return json({ items: [SHOP], total: 1 });
    if (call.path === "/categories") return json(CATEGORIES);
    if (call.path.startsWith("/articles?shop_id=")) return json({ items: [], total: 0 });
    return problem(404);
  });
}

const renderPage = () =>
  renderWithConfig(
    <MemoryRouter>
      <ToastProvider>
        <RejectedArticlesProvider>
          <SellPage />
        </RejectedArticlesProvider>
      </ToastProvider>
    </MemoryRouter>,
  );

const form = () => screen.findByRole("form", { name: "Mettre un article en vente" });
const type = (label: RegExp, text: string) => userEvent.type(screen.getByLabelText(label), text);

describe("Seller space: live validation", () => {
  it("reports a short title after leaving the field, then clears the message as the title grows", async () => {
    api();
    renderPage();
    await form();
    expect(screen.queryByText("Le titre doit contenir au moins 5 caractères.")).not.toBeInTheDocument();
    await type(/Titre de l'article/, "Boba");
    await userEvent.tab();
    expect(screen.getByText("Le titre doit contenir au moins 5 caractères.")).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText(/Titre de l'article/), " Fett");
    expect(screen.queryByText("Le titre doit contenir au moins 5 caractères.")).not.toBeInTheDocument();
    expect(screen.getByText(/9\/120/)).toBeInTheDocument();
  });

  it("reports every missing field when submitting, without calling the API", async () => {
    const calls = api();
    renderPage();
    await form();
    await userEvent.click(screen.getByRole("button", { name: "Mettre en vente" }));
    expect(screen.getByText("Choisissez une catégorie.")).toBeInTheDocument();
    expect(screen.getByText("La description doit contenir au moins 20 caractères.")).toBeInTheDocument();
    expect(screen.getByText("Saisissez une adresse de photo en https://.")).toBeInTheDocument();
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });

  it("flags a malformed price while typing in the price change form", async () => {
    api((c) => (c.path.startsWith("/articles?shop_id=") ? json({ items: [article()], total: 1 }) : undefined));
    renderPage();
    const priceForm = await screen.findByRole("form", { name: /Modifier le prix de Boba Fett/ });
    await userEvent.type(within(priceForm).getByLabelText(/Nouveau prix/), "1.234");
    expect(within(priceForm).getByText(/montant valide/)).toBeInTheDocument();
  });

  it("warns before publishing when the text holds an email or a phone number, without blocking", async () => {
    api();
    renderPage();
    await form();
    await type(/Description de l'article/, "Écrivez à moi@example.com ou au 06 12 34 56 78");
    const warning = screen.getByRole("status");
    expect(within(warning).getByText("Cette annonce serait rejetée")).toBeInTheDocument();
    expect(warning).toHaveTextContent("une adresse email et un numéro de téléphone");
    expect(screen.getByRole("button", { name: "Mettre en vente" })).toBeEnabled();
  });

  it("warns about contact details in a shop description", async () => {
    api();
    renderPage();
    await form();
    await type(/Description de la boutique/, "Mon mail : a@b.fr");
    expect(screen.getByText(/la boutique serait refusée/)).toBeInTheDocument();
  });

  it("asks for a shop name of at least 3 characters", async () => {
    const calls = api();
    renderPage();
    await form();
    await type(/Nom de la boutique/, "ab");
    await userEvent.click(screen.getByRole("button", { name: "Créer la boutique" }));
    expect(screen.getByText("Le nom doit contenir au moins 3 caractères.")).toBeInTheDocument();
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });
});

describe("Seller space: preview", () => {
  it("follows the form and shows free delivery for a zero fee", async () => {
    api();
    renderPage();
    await form();
    const preview = screen.getByRole("region", { name: "Aperçu de l'annonce" });
    expect(within(preview).getByText("Titre de l'article")).toBeInTheDocument();
    expect(within(preview).getByText("Prix à renseigner")).toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Catégorie"), "c1");
    await type(/Titre de l'article/, "Boba Fett Kenner 1979");
    await type(/Prix \(€\)/, "120,5");
    expect(within(preview).getByText("Boba Fett Kenner 1979")).toBeInTheDocument();
    expect(within(preview).getByText("Figurines")).toBeInTheDocument();
    expect(within(preview).getByText("Boutique Alice")).toBeInTheDocument();
    expect(within(preview).getByText(/120,50/)).toBeInTheDocument();
    expect(within(preview).getByText("Livraison offerte")).toBeInTheDocument();
    await userEvent.clear(screen.getByLabelText(/Frais de port/));
    await userEvent.type(screen.getByLabelText(/Frais de port/), "8");
    expect(within(preview).getByText(/Frais de port : 8,00/)).toBeInTheDocument();
    // An invalid fee never shows as a made-up amount.
    await userEvent.type(screen.getByLabelText(/Frais de port/), "x");
    expect(within(preview).getByText("Frais de port : —")).toBeInTheDocument();
    expect(within(preview).queryByText(/0,00/)).not.toBeInTheDocument();
  });
});

async function fillValid(description = "Figurine originale Kenner de 1979, très bon état.") {
  await form();
  await userEvent.selectOptions(screen.getByLabelText("Catégorie"), "c1");
  await type(/Titre de l'article/, "Boba Fett Kenner 1979");
  await type(/Description de l'article/, description);
  await type(/Adresse de la photo/, "https://img.test/1.jpg");
  await type(/Prix \(€\)/, "120");
}

describe("Seller space: outcomes and toasts", () => {
  it("shows a toast and clears the form after a publication", async () => {
    api((c) => (c.method === "POST" && c.path === "/articles" ? json(article(), 201) : undefined));
    renderPage();
    await fillValid();
    await userEvent.click(screen.getByRole("button", { name: "Mettre en vente" }));
    expect(await screen.findByText("« Boba Fett Kenner 1979 » est en vente dans le catalogue.")).toBeInTheDocument();
    expect(screen.getByLabelText(/Titre de l'article/)).toHaveValue("");
    // Validation messages do not reappear on the freshly cleared form.
    expect(screen.queryByText("Le titre doit contenir au moins 5 caractères.")).not.toBeInTheDocument();
  });

  it("explains a rejection with advice, keeps the form and lists the rejected article with its status", async () => {
    api((c) =>
      c.method === "POST" && c.path === "/articles"
        ? json(article({ status: "REJECTED", rejection_reasons: ["CONTACT_EMAIL"], title: "Fausse annonce" }), 201)
        : undefined,
    );
    renderPage();
    await fillValid("Écrivez-moi à moi@example.com pour traiter hors site.");
    await userEvent.click(screen.getByRole("button", { name: "Mettre en vente" }));
    expect(await screen.findByText("Article rejeté par le contrôle automatique")).toBeInTheDocument();
    expect(screen.getByText("le texte contient une adresse email")).toBeInTheDocument();
    expect(screen.getByText(/les échanges passent par la plateforme/i, { selector: "span" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Titre de l'article/)).toHaveValue("Boba Fett Kenner 1979");
    expect(screen.getByText("L'article a été rejeté par le contrôle automatique.")).toBeInTheDocument();

    const list = await screen.findByRole("list", { name: "Liste de mes articles" });
    const row = within(list).getByText("Fausse annonce").closest("li") as HTMLElement;
    expect(within(row).getByText("Rejeté")).toBeInTheDocument();
    expect(within(row).getByText(/adresse email dans le texte/)).toBeInTheDocument();
    expect(within(row).queryByLabelText(/Nouveau prix/)).not.toBeInTheDocument();
  });

  it("lists a published article with its status and a link to the detail page", async () => {
    api((c) => (c.path.startsWith("/articles?shop_id=") ? json({ items: [article()], total: 1 }) : undefined));
    renderPage();
    const list = await screen.findByRole("list", { name: "Liste de mes articles" });
    expect(within(list).getByText("Publié")).toBeInTheDocument();
    expect(within(list).getByRole("link", { name: "Boba Fett Kenner 1979" })).toHaveAttribute("href", "/catalogue/a1");
    expect(within(list).getByText(/Frais de port : 8,00/)).toBeInTheDocument();
  });

  it("shows refused listings above the first page only", async () => {
    const many = Array.from({ length: 11 }, (_, i) => article({ id: `p${i}`, title: `Publié numéro ${i}` }));
    api((c) => {
      if (c.method === "POST" && c.path === "/articles")
        return json(article({ id: "r1", status: "REJECTED", rejection_reasons: ["CONTACT_EMAIL"], title: "Annonce refusée" }), 201);
      if (c.path.startsWith("/articles?shop_id=")) {
        const offset = Number(new URL(`https://x${c.path}`).searchParams.get("offset"));
        return json({ items: many.slice(offset, offset + 10), total: 11 });
      }
      return undefined;
    });
    renderPage();
    await fillValid("Écrivez-moi à moi@example.com pour traiter hors site.");
    await userEvent.click(screen.getByRole("button", { name: "Mettre en vente" }));
    const list = await screen.findByRole("list", { name: "Liste de mes articles" });
    expect(within(list).getByText("Annonce refusée")).toBeInTheDocument();
    expect(screen.getByText("Les annonces refusées restent visibles ici jusqu'au rechargement de la page.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /page 2/i }));
    expect(await screen.findByText("Publié numéro 10")).toBeInTheDocument();
    expect(screen.queryByText("Annonce refusée")).not.toBeInTheDocument();
  });

  it.each([
    ["SHOP_NOT_FOUND", "La boutique choisie n'existe pas."],
    ["CATEGORY_NOT_FOUND", "La catégorie choisie n'existe pas."],
    ["CONTACT_PHONE", "Le texte ne doit contenir aucun numéro de téléphone."],
  ])("explains the API error %s in French and raises an error toast", async (code, message) => {
    api((c) => (c.method === "POST" && c.path === "/articles" ? problem(422, { errors: [{ field: "x", code }] }) : undefined));
    renderPage();
    await fillValid();
    await userEvent.click(screen.getByRole("button", { name: "Mettre en vente" }));
    expect(await screen.findByText("Saisie à corriger")).toBeInTheDocument();
    expect(screen.getByText(message)).toBeInTheDocument();
    expect(screen.getByText("La publication a échoué : voir le message sous le formulaire.")).toBeInTheDocument();
  });

  it("links an invalid field to its message for assistive technologies", async () => {
    api();
    renderPage();
    await form();
    const title = screen.getByLabelText(/Titre de l'article/);
    expect(title).not.toHaveAttribute("aria-invalid", "true");
    await userEvent.type(title, "Boba");
    await userEvent.tab();
    expect(title).toHaveAttribute("aria-invalid", "true");
    const message = screen.getByText("Le titre doit contenir au moins 5 caractères.");
    expect(title.getAttribute("aria-describedby")).toBe(message.id);
    expect(message.id).not.toBe("");
  });

  it("shows a toast when a shop is created", async () => {
    let shops: unknown[] = [];
    api((c) => {
      if (c.method === "POST" && c.path === "/shops") {
        shops = [SHOP];
        return json(SHOP, 201);
      }
      return c.path === "/shops/me" ? json({ items: shops, total: shops.length }) : undefined;
    });
    renderPage();
    expect(await screen.findByText("Vous n'avez pas encore de boutique")).toBeInTheDocument();
    await type(/Nom de la boutique/, "Boutique Alice");
    await userEvent.click(screen.getByRole("button", { name: "Créer la boutique" }));
    expect(await screen.findByText(/Votre boutique est créée/)).toBeInTheDocument();
  });

  it("raises a toast when the price change succeeds", async () => {
    api((c) => {
      if (c.path.startsWith("/articles?shop_id=")) return json({ items: [article()], total: 1 });
      if (c.method === "PUT") return json(article({ price: "95.00" }));
      return undefined;
    });
    renderPage();
    const priceForm = await screen.findByRole("form", { name: /Modifier le prix de Boba Fett/ });
    await userEvent.type(within(priceForm).getByLabelText(/Nouveau prix/), "95");
    await userEvent.click(within(priceForm).getByRole("button", { name: "Modifier le prix" }));
    expect(await screen.findByText(/est maintenant de 95,00/)).toBeInTheDocument();
  });
});
