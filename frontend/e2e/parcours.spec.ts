import { expect, expectNoAccessibilityViolation, goTo, login, RUN, test } from "./helpers";

// The journeys run in sequence (the category created in 1 is used in 2 and 3, the articles of 3 in 4).
test.describe.configure({ mode: "serial" });

const CATEGORY = `E2E Figurines ${RUN}`;
const SHOP = `Boutique E2E ${RUN}`;
const ACCEPTED_TITLE = `Boba Fett Kenner ${RUN}`;
const REJECTED_TITLE = `Fausse annonce ${RUN}`;
const PHOTO = "https://images.example.com/boba-1.jpg";

test("1. admin creates a category", async ({ page }) => {
  await login(page, "admin");
  await goTo(page, "Catégories");
  await page.getByLabel("Nom de la catégorie").fill(CATEGORY);
  await page.getByRole("button", { name: "Créer la catégorie" }).click();
  await expect(page.getByText(`Catégorie « ${CATEGORY} » créée.`)).toBeVisible();
  await expect(page.getByRole("list", { name: "Liste des catégories" }).getByText(CATEGORY, { exact: true })).toBeVisible();
});

test("2. chloe picks this category as an interest", async ({ page }) => {
  await login(page, "chloe");
  await goTo(page, "Mes centres d'intérêt");
  const group = page.getByRole("group", { name: "Catégories suivies" });
  const ours = group.getByRole("checkbox", { name: CATEGORY, exact: true });
  await expect(ours).toBeVisible();
  // Keep only this run's category: previous runs must not pile up (maximum 20).
  await page.waitForLoadState("networkidle"); // the interests already saved arrive after the category list
  for (const box of await group.getByRole("checkbox").all()) {
    if (await box.isChecked()) await box.uncheck();
  }
  await ours.check();
  await page.getByRole("button", { name: "Enregistrer mes centres d'intérêt" }).click();
  await expect(page.getByText("Centres d'intérêt enregistrés.")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("group", { name: "Catégories suivies" }).getByRole("checkbox", { name: CATEGORY, exact: true })).toBeChecked();
});

test("3. alice creates a shop, publishes, sees a rejection, changes the price", async ({ page }) => {
  await login(page, "alice");
  await goTo(page, "Vendre");

  await page.getByLabel("Nom de la boutique").fill(SHOP);
  await page.getByRole("button", { name: "Créer la boutique" }).click();
  await expect(page.getByText(`Boutique « ${SHOP} » créée.`)).toBeVisible();

  const form = page.getByRole("form", { name: "Mettre un article en vente" });
  await form.getByLabel("Boutique", { exact: true }).selectOption({ label: SHOP });
  await form.getByLabel("Catégorie").selectOption({ label: CATEGORY });

  // Compliant article → PUBLISHED
  await form.getByLabel(/Titre de l'article/).fill(ACCEPTED_TITLE);
  await form.getByLabel(/Description de l'article/).fill("Figurine originale Kenner de 1979, complète, très bon état.");
  await form.getByLabel(/Adresse de la photo/).fill(PHOTO);
  await form.getByLabel(/Prix \(€\)/).fill("120,00");
  await form.getByLabel(/Frais de port/).fill("8,00");
  await form.getByRole("button", { name: "Mettre en vente" }).click();
  await expect(page.getByText("Article publié", { exact: true })).toBeVisible();

  // Article with a phone number in the description → REJECTED, reason displayed
  await form.getByLabel(/Titre de l'article/).fill(REJECTED_TITLE);
  await form.getByLabel(/Description de l'article/).fill("Contactez-moi directement au 06 12 34 56 78 pour traiter hors site.");
  await form.getByLabel(/Adresse de la photo/).fill(PHOTO);
  await form.getByLabel(/Prix \(€\)/).fill("50,00");
  await form.getByRole("button", { name: "Mettre en vente" }).click();
  await expect(page.getByText("Article rejeté par le contrôle automatique")).toBeVisible();
  await expect(page.getByText("le texte contient un numéro de téléphone")).toBeVisible();

  // Price change of the accepted article, then history
  await page.getByLabel("Boutique des articles").selectOption({ label: SHOP });
  const row = page.getByRole("listitem").filter({ hasText: ACCEPTED_TITLE });
  await expect(row).toBeVisible();
  // The rejected article stays listed for this visit, with its status and no price form.
  const rejectedRow = page.getByRole("listitem").filter({ hasText: REJECTED_TITLE });
  await expect(rejectedRow.getByText("Rejeté")).toBeVisible();
  await expect(rejectedRow.getByLabel(/Nouveau prix/)).toHaveCount(0);
  // The API lists only published articles: the rejected one survives navigation inside the
  // application (not a reload), then is looked up again when the shop is selected.
  await goTo(page, "Catalogue");
  await expect(page.getByRole("heading", { level: 1, name: "Catalogue" })).toBeVisible();
  await goTo(page, "Vendre");
  await page.getByLabel("Boutique des articles").selectOption({ label: SHOP });
  await expect(page.getByRole("listitem").filter({ hasText: REJECTED_TITLE }).getByText("Rejeté")).toBeVisible();
  await row.getByLabel(/Nouveau prix/).fill("95");
  await row.getByRole("button", { name: "Modifier le prix" }).click();
  await expect(row.getByText(/Prix modifié : 95,00/)).toBeVisible();
  await row.getByRole("button", { name: "Historique des prix" }).click();
  const history = row.getByRole("table", { name: "Historique des prix" });
  await expect(history.getByRole("cell").filter({ hasText: /120,00/ })).toBeVisible();
  await expect(history.getByRole("cell").filter({ hasText: /95,00/ })).toBeVisible();
});

test("4. chloe sees both notifications", async ({ page }) => {
  await login(page, "chloe");
  await goTo(page, "Mes centres d'intérêt");
  const list = page.getByRole("list", { name: "Liste des notifications" });
  const newArticle = list.getByRole("listitem").filter({ hasText: `Nouvel article : « ${ACCEPTED_TITLE} »` });
  const priceChanged = list.getByRole("listitem").filter({ hasText: `Changement de prix : « ${ACCEPTED_TITLE} » passe de` });
  // RabbitMQ events are asynchronous and the page polls the API every 10 s (no click, no reload):
  // the notifications must appear by themselves.
  await expect(newArticle).toBeVisible({ timeout: 25_000 });
  await expect(priceChanged).toBeVisible({ timeout: 25_000 });
  await expect(newArticle).toContainText(/120,00/);
  await expect(priceChanged).toContainText(/120,00.*95,00/);
});

test("5. sign-out returns to the application", async ({ page, baseURL }) => {
  await login(page, "alice");
  await page.getByRole("button", { name: "Déconnexion" }).click();
  await expect(page).toHaveURL(new RegExp(`^${baseURL?.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}/?$`));
  await expect(page.getByRole("button", { name: "Connexion" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Déconnexion" })).toHaveCount(0);
});

test("6. no token in localStorage or sessionStorage after sign-in", async ({ page }) => {
  await login(page, "alice");
  await goTo(page, "Vendre"); // a page that calls the API with the token
  await expect(page.getByRole("heading", { name: "Mes boutiques" })).toBeVisible();
  const stored = await page.evaluate(() => {
    const dump = (storage: Storage) => Object.keys(storage).map((key) => ({ key, value: storage.getItem(key) ?? "" }));
    return { local: dump(localStorage), session: dump(sessionStorage) };
  });
  const jwt = /eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*/;
  for (const { key, value } of [...stored.local, ...stored.session]) {
    expect(key, `key ${key}`).not.toMatch(/oidc\.user|token/i);
    expect(jwt.test(value), `value of key ${key} (a token?)`).toBe(false);
    expect(value, `value of key ${key}`).not.toMatch(/access_token|refresh_token|id_token/);
  }
  expect(stored.local).toHaveLength(0);
});

test("7. chloe sees a new notification arrive by itself (at most 10 s), switches and chips work", async ({ page, browser, baseURL }) => {
  const liveTitle = `Live ${RUN}`;
  await login(page, "chloe");
  await goTo(page, "Mes centres d'intérêt");
  await expect(page.getByRole("list", { name: "Liste des notifications" })).toBeVisible();

  // Alice publishes in the category followed by chloe, from another browser context.
  const context = await browser.newContext({ baseURL, locale: "fr-FR" });
  const alicePage = await context.newPage();
  await login(alicePage, "alice");
  await goTo(alicePage, "Vendre");
  const form = alicePage.getByRole("form", { name: "Mettre un article en vente" });
  await form.getByLabel("Boutique", { exact: true }).selectOption({ label: SHOP });
  await form.getByLabel("Catégorie").selectOption({ label: CATEGORY });
  await form.getByLabel(/Titre de l'article/).fill(liveTitle);
  await form.getByLabel(/Description de l'article/).fill("Seconde annonce, publiée pendant que l'acheteuse regarde sa page.");
  await form.getByLabel(/Adresse de la photo/).fill(PHOTO);
  await form.getByLabel(/Prix \(€\)/).fill("40,00");
  await form.getByRole("button", { name: "Mettre en vente" }).click();
  await expect(alicePage.getByText(`« ${liveTitle} » est en vente dans le catalogue.`)).toBeVisible();
  const publishedAt = Date.now();
  await context.close();

  // No click on "Actualiser", no reload: the polling loop brings it, 10 s at most plus the event processing.
  const live = page.getByRole("list", { name: "Liste des notifications" }).getByRole("listitem").filter({ hasText: `Nouvel article : « ${liveTitle} »` });
  await expect(live).toBeVisible({ timeout: 15_000 });
  console.log(`notification arrived ${((Date.now() - publishedAt) / 1000).toFixed(1)} s after publication, without click`);
  await expect(page.getByRole("link", { name: "Mes centres d'intérêt", exact: false })).toContainText(/\d+/); // badge

  // Switches: on = primary colour (dark blue track), off = grey track, contrast 3:1 at least.
  const track = (name: string) =>
    page.getByRole("switch", { name }).evaluate((input) => {
      const root = input.closest(".MuiSwitch-root");
      return getComputedStyle(root?.querySelector(".MuiSwitch-track") as Element).backgroundColor;
    });
  const newArticleSwitch = page.getByRole("switch", { name: "Être prévenu d'un nouvel article" });
  await expect(newArticleSwitch).toBeChecked();
  await expect.poll(() => track("Être prévenu d'un nouvel article")).toBe("rgb(31, 58, 95)");
  await newArticleSwitch.uncheck();
  // The colour change is animated: poll until the transition ends.
  await expect.poll(() => track("Être prévenu d'un nouvel article")).toBe("rgb(107, 114, 128)");
  await newArticleSwitch.check(); // nothing was saved

  // Filter chips by keyboard: Enter on a category, Space on "Toutes les catégories".
  await goTo(page, "Catalogue");
  const chip = page.getByRole("button", { name: CATEGORY, exact: true });
  const all = page.getByRole("button", { name: "Toutes les catégories" });
  await expect(all).toHaveAttribute("aria-pressed", "true");
  await chip.focus();
  await page.keyboard.press("Enter");
  await expect(chip).toHaveAttribute("aria-pressed", "true");
  await expect(all).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByRole("link", { name: new RegExp(ACCEPTED_TITLE) })).toBeVisible();
  await all.focus();
  await page.keyboard.press("Space");
  await expect(all).toHaveAttribute("aria-pressed", "true");
  await expect(chip).toHaveAttribute("aria-pressed", "false");
});

for (const screen of [
  { name: "desktop", viewport: { width: 1280, height: 800 }, mobile: false },
  { name: "mobile", viewport: { width: 375, height: 812 }, mobile: true },
]) {
  test(`8. axe finds no WCAG A or AA violation on any page (${screen.name})`, async ({ page }) => {
    test.setTimeout(180_000);
    await page.setViewportSize(screen.viewport);

    // Signed out: home, catalogue, article page, unknown route.
    await page.goto("/");
    await expectNoAccessibilityViolation(page, `${screen.name}, home, signed out`);
    await goTo(page, "Catalogue");
    await expect(page.getByRole("heading", { level: 1, name: "Catalogue" })).toBeVisible();
    await expect(page.getByText(ACCEPTED_TITLE).first()).toBeVisible();
    await expectNoAccessibilityViolation(page, `${screen.name}, catalogue, signed out`);
    await page.getByRole("link", { name: new RegExp(ACCEPTED_TITLE) }).first().click();
    await expect(page.getByRole("heading", { level: 1, name: ACCEPTED_TITLE })).toBeVisible();
    await expectNoAccessibilityViolation(page, `${screen.name}, article page, signed out`);
    await page.goto("/page-inconnue");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expectNoAccessibilityViolation(page, `${screen.name}, not found, signed out`);

    // Signed in: home and the page of each role.
    const pages: Array<["admin" | "alice" | "chloe", string, string]> = [
      ["admin", "Catégories", "categories"],
      ["alice", "Vendre", "seller area"],
      ["chloe", "Mes centres d'intérêt", "interests and notifications"],
    ];
    for (const [account, menu, label] of pages) {
      await login(page, account, undefined, screen.mobile);
      await expectNoAccessibilityViolation(page, `${screen.name}, home, ${account}`);
      await goTo(page, menu);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await expectNoAccessibilityViolation(page, `${screen.name}, ${label}, ${account}`);
      if (account === "alice") {
        // The seller page with a rejected article and a price history on screen.
        const form = page.getByRole("form", { name: "Mettre un article en vente" });
        await form.getByLabel("Boutique", { exact: true }).selectOption({ label: SHOP });
        await form.getByLabel("Catégorie").selectOption({ label: CATEGORY });
        await form.getByLabel(/Titre de l'article/).fill(`Axe ${RUN} ${screen.name}`);
        await form.getByLabel(/Description de l'article/).fill("Écrivez-moi à axe@example.com pour conclure hors du site.");
        await expect(form.getByRole("status")).toBeVisible(); // live warning (contact details)
        await expectNoAccessibilityViolation(page, `${screen.name}, seller form with a warning`);
        await form.getByLabel(/Adresse de la photo/).fill(PHOTO);
        await form.getByLabel(/Prix \(€\)/).fill("10,00");
        await form.getByRole("button", { name: "Mettre en vente" }).click();
        await expect(page.getByText("Article rejeté par le contrôle automatique")).toBeVisible();
        await page.getByLabel("Boutique des articles").selectOption({ label: SHOP });
        const row = page.getByRole("listitem").filter({ hasText: ACCEPTED_TITLE });
        await row.getByRole("button", { name: "Historique des prix" }).click();
        await expect(row.getByRole("table", { name: "Historique des prix" })).toBeVisible();
        await expectNoAccessibilityViolation(page, `${screen.name}, seller page with rejection and history`);
      }
      if (screen.mobile) {
        await page.getByRole("button", { name: "Ouvrir le menu" }).click();
        await expect(page.getByRole("dialog", { name: "Menu" })).toBeVisible();
        await expectNoAccessibilityViolation(page, `${screen.name}, open menu, ${account}`);
        await page.getByRole("dialog", { name: "Menu" }).getByRole("button", { name: "Déconnexion" }).click();
      } else {
        await page.getByRole("button", { name: "Déconnexion" }).click();
      }
      await expect(page.getByRole("button", { name: screen.mobile ? "Ouvrir le menu" : "Connexion" })).toBeVisible();
    }
  });
}
