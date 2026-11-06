import { expect, goTo, login, RUN, test } from "./helpers";

// Captures d'écran pour la soutenance, lancées à part (CAPTURES=1, voir playwright.config.ts).
// Aucune capture n'est prise pendant ou après la saisie d'un mot de passe.
const DIR = "e2e/resultats/captures";
const CATEGORY = `Figurines vintage ${RUN}`;
const SHOP = `Boutique démo ${RUN}`;
const TITLE = `Boba Fett Kenner ${RUN}`;
const REJECTED_TITLE = `Fausse annonce ${RUN}`;
const PHOTO = "https://images.example.com/boba-1.jpg";

test.describe.configure({ mode: "serial" });
test.use({ viewport: { width: 1280, height: 800 } });

test("captures : parcours de démonstration", async ({ page }) => {
  // admin : page Catégories
  await login(page, "admin", async () => {
    await page.screenshot({ path: `${DIR}/02-connexion-keycloak.png` });
  });
  await goTo(page, "Catégories");
  await page.getByLabel("Nom de la catégorie").fill(CATEGORY);
  await page.getByRole("button", { name: "Créer la catégorie" }).click();
  await expect(page.getByText(`Catégorie « ${CATEGORY} » créée.`)).toBeVisible();
  await page.screenshot({ path: `${DIR}/07-admin-categories.png` });
  await page.getByRole("button", { name: "Déconnexion" }).click();

  // chloe : centre d'intérêt
  await login(page, "chloe");
  await goTo(page, "Mes centres d'intérêt");
  const group = page.getByRole("group", { name: "Catégories d'intérêt" });
  await page.waitForLoadState("networkidle"); // les centres d'intérêt déjà enregistrés arrivent après la liste des catégories
  for (const box of await group.getByRole("checkbox").all()) {
    if (await box.isChecked()) await box.uncheck();
  }
  await group.getByRole("checkbox", { name: CATEGORY, exact: true }).check();
  await page.getByRole("button", { name: "Enregistrer mes centres d'intérêt" }).click();
  await expect(page.getByText("Centres d'intérêt enregistrés.")).toBeVisible();
  await page.getByRole("button", { name: "Déconnexion" }).click();

  // alice : publication, rejet, prix
  await login(page, "alice");
  await goTo(page, "Vendre");
  await page.getByLabel("Nom de la boutique").fill(SHOP);
  await page.getByRole("button", { name: "Créer la boutique" }).click();
  await expect(page.getByText(`Boutique « ${SHOP} » créée.`)).toBeVisible();
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
  await page.screenshot({ path: `${DIR}/03-vendre-article-publie.png`, fullPage: true });

  await form.getByLabel(/Titre de l'article/).fill(REJECTED_TITLE);
  await form.getByLabel(/Description de l'article/).fill("Contactez-moi directement au 06 12 34 56 78 pour traiter hors site.");
  await form.getByLabel(/Adresse de la photo/).fill(PHOTO);
  await form.getByLabel(/Prix \(€\)/).fill("50,00");
  await form.getByRole("button", { name: "Mettre en vente" }).click();
  await expect(page.getByText("le texte contient un numéro de téléphone")).toBeVisible();
  await page.screenshot({ path: `${DIR}/04-vendre-article-rejete.png`, fullPage: true });

  await page.getByLabel("Boutique des articles").selectOption({ label: SHOP });
  const row = page.getByRole("listitem").filter({ hasText: TITLE });
  await row.getByLabel(/Nouveau prix/).fill("95");
  await row.getByRole("button", { name: "Modifier le prix" }).click();
  await expect(row.getByText(/Prix modifié : 95,00/)).toBeVisible();
  await row.getByRole("button", { name: "Historique des prix" }).click();
  await expect(row.getByRole("table", { name: "Historique des prix" })).toBeVisible();
  await row.scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${DIR}/05-vendre-historique-des-prix.png`, fullPage: true });
  await page.getByRole("button", { name: "Déconnexion" }).click();

  // chloe : notifications
  await login(page, "chloe");
  await goTo(page, "Mes centres d'intérêt");
  const item = page.getByRole("list", { name: "Liste des notifications" }).getByRole("listitem").filter({ hasText: TITLE });
  await expect(async () => {
    await page.getByRole("button", { name: "Actualiser" }).click();
    await expect(item.first()).toBeVisible({ timeout: 1_500 });
    await expect(item).toHaveCount(2, { timeout: 1_500 });
  }).toPass({ timeout: 30_000 });
  await page.screenshot({ path: `${DIR}/06-notifications-chloe.png`, fullPage: true });
  await page.getByRole("button", { name: "Déconnexion" }).click();

  // catalogue public (sans connexion), avec l'article publié
  await page.goto("/");
  await expect(page.getByText(TITLE).first()).toBeVisible();
  await page.screenshot({ path: `${DIR}/01-catalogue-public.png`, fullPage: true });
});
