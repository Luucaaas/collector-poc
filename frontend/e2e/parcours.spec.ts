import { expect, test } from "@playwright/test";
import { goTo, login, RUN } from "./helpers";

// Les parcours s'enchaînent (la catégorie créée en 1 sert en 2 et 3, les articles de 3 en 4).
test.describe.configure({ mode: "serial" });

const CATEGORY = `E2E Figurines ${RUN}`;
const SHOP = `Boutique E2E ${RUN}`;
const ACCEPTED_TITLE = `Boba Fett Kenner ${RUN}`;
const REJECTED_TITLE = `Fausse annonce ${RUN}`;
const PHOTO = "https://images.example.com/boba-1.jpg";

test("1. admin crée une catégorie", async ({ page }) => {
  await login(page, "admin");
  await goTo(page, "Catégories");
  await page.getByLabel("Nom de la catégorie").fill(CATEGORY);
  await page.getByRole("button", { name: "Créer la catégorie" }).click();
  await expect(page.getByText(`Catégorie « ${CATEGORY} » créée.`)).toBeVisible();
  await expect(page.getByRole("list", { name: "Liste des catégories" }).getByText(CATEGORY, { exact: true })).toBeVisible();
});

test("2. chloe choisit cette catégorie comme centre d'intérêt", async ({ page }) => {
  await login(page, "chloe");
  await goTo(page, "Mes centres d'intérêt");
  const group = page.getByRole("group", { name: "Catégories d'intérêt" });
  const ours = group.getByRole("checkbox", { name: CATEGORY, exact: true });
  await expect(ours).toBeVisible();
  // On ne garde que la catégorie de cet essai : les exécutions précédentes ne doivent pas s'accumuler (maximum 20).
  for (const box of await group.getByRole("checkbox").all()) {
    if (await box.isChecked()) await box.uncheck();
  }
  await ours.check();
  await page.getByRole("button", { name: "Enregistrer mes centres d'intérêt" }).click();
  await expect(page.getByText("Centres d'intérêt enregistrés.")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("group", { name: "Catégories d'intérêt" }).getByRole("checkbox", { name: CATEGORY, exact: true })).toBeChecked();
});

test("3. alice crée une boutique, publie, voit un rejet, change le prix", async ({ page }) => {
  await login(page, "alice");
  await goTo(page, "Vendre");

  await page.getByLabel("Nom de la boutique").fill(SHOP);
  await page.getByRole("button", { name: "Créer la boutique" }).click();
  await expect(page.getByText(`Boutique « ${SHOP} » créée.`)).toBeVisible();

  const form = page.getByRole("form", { name: "Mettre un article en vente" });
  await form.getByLabel("Boutique", { exact: true }).selectOption({ label: SHOP });
  await form.getByLabel("Catégorie").selectOption({ label: CATEGORY });

  // Article conforme → PUBLISHED
  await form.getByLabel(/Titre de l'article/).fill(ACCEPTED_TITLE);
  await form.getByLabel(/Description de l'article/).fill("Figurine originale Kenner de 1979, complète, très bon état.");
  await form.getByLabel(/Adresse de la photo/).fill(PHOTO);
  await form.getByLabel(/Prix \(€\)/).fill("120,00");
  await form.getByLabel(/Frais de port/).fill("8,00");
  await form.getByRole("button", { name: "Mettre en vente" }).click();
  await expect(page.getByText("Article publié", { exact: true })).toBeVisible();

  // Article avec un téléphone dans la description → REJECTED, motif affiché
  await form.getByLabel(/Titre de l'article/).fill(REJECTED_TITLE);
  await form.getByLabel(/Description de l'article/).fill("Contactez-moi directement au 06 12 34 56 78 pour traiter hors site.");
  await form.getByLabel(/Adresse de la photo/).fill(PHOTO);
  await form.getByLabel(/Prix \(€\)/).fill("50,00");
  await form.getByRole("button", { name: "Mettre en vente" }).click();
  await expect(page.getByText("Article rejeté par le contrôle automatique")).toBeVisible();
  await expect(page.getByText("le texte contient un numéro de téléphone")).toBeVisible();

  // Changement de prix de l'article accepté, puis historique
  await page.getByLabel("Boutique des articles").selectOption({ label: SHOP });
  const row = page.getByRole("listitem").filter({ hasText: ACCEPTED_TITLE });
  await expect(row).toBeVisible();
  await expect(page.getByRole("listitem").filter({ hasText: REJECTED_TITLE })).toHaveCount(0);
  await row.getByLabel(/Nouveau prix/).fill("95");
  await row.getByRole("button", { name: "Modifier le prix" }).click();
  await expect(row.getByText(/Prix modifié : 95,00/)).toBeVisible();
  await row.getByRole("button", { name: "Historique des prix" }).click();
  const history = row.getByRole("table", { name: "Historique des prix" });
  await expect(history.getByRole("cell").filter({ hasText: /120,00/ })).toBeVisible();
  await expect(history.getByRole("cell").filter({ hasText: /95,00/ })).toBeVisible();
});

test("4. chloe voit les deux notifications", async ({ page }) => {
  await login(page, "chloe");
  await goTo(page, "Mes centres d'intérêt");
  const list = page.getByRole("list", { name: "Liste des notifications" });
  const newArticle = list.getByRole("listitem").filter({ hasText: `Nouvel article : « ${ACCEPTED_TITLE} »` });
  const priceChanged = list.getByRole("listitem").filter({ hasText: `Changement de prix : « ${ACCEPTED_TITLE} » passe de` });
  // Les événements RabbitMQ sont asynchrones : on actualise jusqu'à leur arrivée.
  await expect(async () => {
    await page.getByRole("button", { name: "Actualiser" }).click();
    await expect(newArticle).toBeVisible({ timeout: 1_500 });
    await expect(priceChanged).toBeVisible({ timeout: 1_500 });
  }).toPass({ timeout: 30_000 });
  await expect(newArticle).toContainText(/120,00/);
  await expect(priceChanged).toContainText(/120,00.*95,00/);
});

test("5. la déconnexion revient sur l'application", async ({ page, baseURL }) => {
  await login(page, "alice");
  await page.getByRole("button", { name: "Déconnexion" }).click();
  await expect(page).toHaveURL(new RegExp(`^${baseURL?.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}/?$`));
  await expect(page.getByRole("button", { name: "Connexion" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Déconnexion" })).toHaveCount(0);
});

test("6. aucun jeton dans localStorage ni sessionStorage après connexion", async ({ page }) => {
  await login(page, "alice");
  await goTo(page, "Vendre"); // une page qui appelle l'API avec le jeton
  await expect(page.getByRole("heading", { name: "Mes boutiques" })).toBeVisible();
  const stored = await page.evaluate(() => {
    const dump = (storage: Storage) => Object.keys(storage).map((key) => ({ key, value: storage.getItem(key) ?? "" }));
    return { local: dump(localStorage), session: dump(sessionStorage) };
  });
  const jwt = /eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*/;
  for (const { key, value } of [...stored.local, ...stored.session]) {
    expect(key, `clé ${key}`).not.toMatch(/oidc\.user|token/i);
    expect(jwt.test(value), `valeur de la clé ${key} (un jeton ?)`).toBe(false);
    expect(value, `valeur de la clé ${key}`).not.toMatch(/access_token|refresh_token|id_token/);
  }
  expect(stored.local).toHaveLength(0);
});
