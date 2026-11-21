import type { Locator, Page } from "@playwright/test";
import { expect, goTo, login, test } from "./helpers";

// Screenshots for the defense, run separately (CAPTURES=1, see playwright.config.ts).
// No screenshot shows a password being typed (the Keycloak page is captured empty).
//
// They must show the demo data of docs/07-soutenance/demo/donnees-demo.sh (5 categories, 2 shops,
// 11 articles), so this spec runs on a FRESH cluster, after donnees-demo.sh and BEFORE any
// journey (parcours.spec.ts adds "E2E" data). It creates a handful of readable objects (one
// accepted article, one rejected, one price change) and refuses to start if they already exist.
const DIR = "e2e/resultats/captures";
const SHOP = "Le Comptoir d'Alice"; // shop of alice in donnees_demo.py
const CATEGORY = "Figurines"; // category followed by chloe in donnees_demo.py
const DEMO_ARTICLE = "Figurine Dark Vador Kenner 1978"; // article of donnees_demo.py (alice, Figurines)
const TITLE = "Figurine Boba Fett Kenner 1979";
const REJECTED_TITLE = "Figurine Yoda Kenner 1980";
const PHOTO = "https://images.example.com/boba-fett.jpg";

test.describe.configure({ mode: "serial" });
test.use({ viewport: { width: 1280, height: 800 } });

/**
 * Viewport screenshot with `target` at the top of the window, under the sticky header
 * (a full-page capture would show that header in the middle of the page).
 */
async function shoot(page: Page, name: string, target: Locator): Promise<void> {
  await target.evaluate((el) => window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 80));
  await page.waitForTimeout(600); // end of the toast and scroll animations
  await page.screenshot({ path: `${DIR}/${name}.png` });
}

test("screenshots: demo journey", async ({ page }) => {
  // Public pages first (signed out), on the demo data alone.
  await page.goto("/catalogue");
  await expect(
    page.getByText(DEMO_ARTICLE).first(),
    "demo data missing: run docs/07-soutenance/demo/donnees-demo.sh on a fresh cluster first",
  ).toBeVisible();
  await expect(page.getByText(TITLE), "captures already taken on this cluster: use a fresh cluster").toHaveCount(0);
  await page.screenshot({ path: `${DIR}/01-catalogue-public.png`, fullPage: true });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.screenshot({ path: `${DIR}/08-accueil-visiteur.png`, fullPage: true });
  await page.goto("/catalogue");
  await page.getByRole("link", { name: new RegExp(DEMO_ARTICLE) }).first().click();
  await expect(page.getByRole("heading", { level: 1, name: DEMO_ARTICLE })).toBeVisible();
  await page.screenshot({ path: `${DIR}/09-article-detail.png`, fullPage: true });

  // phone-sized screen (375 px): catalogue, signed out
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/catalogue");
  await expect(page.getByText(DEMO_ARTICLE).first()).toBeVisible();
  await page.screenshot({ path: `${DIR}/10-catalogue-mobile.png` });
  await page.setViewportSize({ width: 1280, height: 800 });

  // admin: Catégories page (the 5 demo categories)
  await login(page, "admin", async () => {
    await page.screenshot({ path: `${DIR}/02-connexion-keycloak.png` });
  });
  await goTo(page, "Catégories");
  await expect(page.getByRole("list", { name: "Liste des catégories" }).getByText(CATEGORY, { exact: true })).toBeVisible();
  await page.screenshot({ path: `${DIR}/07-admin-categories.png` });
  await page.getByRole("button", { name: "Déconnexion" }).click();

  // alice: publication, rejection, price (chloe already follows "Figurines": donnees-demo.sh)
  await login(page, "alice");
  await goTo(page, "Vendre");
  const form = page.getByRole("form", { name: "Mettre un article en vente" });
  await form.getByLabel("Boutique", { exact: true }).selectOption({ label: SHOP });
  await form.getByLabel("Catégorie").selectOption({ label: CATEGORY });
  await form.getByLabel(/Titre de l'article/).fill(TITLE);
  await form.getByLabel(/Description de l'article/).fill("Figurine originale Kenner de 1979, complète, très bon état.");
  await form.getByLabel(/Adresse de la photo/).fill(PHOTO);
  await form.getByLabel(/Prix \(€\)/).fill("120,00");
  await form.getByLabel(/Frais de port/).fill("8,00");
  await form.getByRole("button", { name: "Mettre en vente" }).click();
  await expect(page.getByText("Article publié", { exact: true })).toBeVisible();
  await shoot(page, "03-vendre-article-publie", form);

  await form.getByLabel(/Titre de l'article/).fill(REJECTED_TITLE);
  await form.getByLabel(/Description de l'article/).fill("Contactez-moi directement au 06 12 34 56 78 pour traiter hors site.");
  await form.getByLabel(/Adresse de la photo/).fill(PHOTO);
  await form.getByLabel(/Prix \(€\)/).fill("50,00");
  await form.getByRole("button", { name: "Mettre en vente" }).click();
  await expect(page.getByText("le texte contient un numéro de téléphone")).toBeVisible();
  await shoot(page, "04-vendre-article-rejete", form);

  await page.getByLabel("Boutique des articles").selectOption({ label: SHOP });
  const row = page.getByRole("listitem").filter({ hasText: TITLE });
  await row.getByLabel(/Nouveau prix/).fill("95");
  await row.getByRole("button", { name: "Modifier le prix" }).click();
  await expect(row.getByText(/Prix modifié : 95,00/)).toBeVisible();
  await row.getByRole("button", { name: "Historique des prix" }).click();
  await expect(row.getByRole("table", { name: "Historique des prix" })).toBeVisible();
  await shoot(page, "05-vendre-historique-des-prix", row);
  await page.getByRole("button", { name: "Déconnexion" }).click();

  // chloe: notifications
  await login(page, "chloe");
  await goTo(page, "Mes centres d'intérêt");
  const item = page.getByRole("list", { name: "Liste des notifications" }).getByRole("listitem").filter({ hasText: TITLE });
  // No click: the page polls the API every 10 s, the notifications must arrive by themselves.
  await expect(item.first()).toBeVisible({ timeout: 25_000 });
  await expect(item).toHaveCount(2, { timeout: 25_000 });
  await page.screenshot({ path: `${DIR}/06-notifications-chloe.png`, fullPage: true });
  await page.getByRole("button", { name: "Déconnexion" }).click();
});
