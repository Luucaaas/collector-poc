import { expect, type Page } from "@playwright/test";

export type Account = "admin" | "alice" | "chloe";

const PASSWORD_VARIABLES: Record<Account, string> = {
  admin: "E2E_ADMIN_PASSWORD",
  alice: "E2E_ALICE_PASSWORD",
  chloe: "E2E_CHLOE_PASSWORD",
};

/** Suffixe unique par exécution : les parcours se relancent sans réinitialiser la base. */
export const RUN = Date.now().toString(36);

/**
 * Connexion par la vraie page de Keycloak. Le mot de passe vient de l'environnement ; il est posé
 * par `evaluate` (et non `fill`) car les arguments de `evaluate` n'apparaissent ni dans le journal
 * d'appels ni dans les messages d'erreur de Playwright.
 */
export async function login(page: Page, account: Account): Promise<void> {
  const variable = PASSWORD_VARIABLES[account];
  const password = process.env[variable];
  if (!password) throw new Error(`Variable d'environnement ${variable} absente (voir e2e/run-compose.sh).`);

  await page.goto("/");
  await page.getByRole("button", { name: "Connexion" }).click();
  await page.locator("#username").fill(account);
  await page.locator("#password").evaluate((input: HTMLInputElement, value: string) => {
    input.value = value;
  }, password);
  await page.locator("#kc-login").click();
  await expect(page.getByRole("button", { name: "Déconnexion" })).toBeVisible();
  await expect(page.getByRole("banner").locator("p").filter({ hasText: new RegExp(`^${account}$`) })).toBeVisible();
}

export async function goTo(page: Page, menu: string): Promise<void> {
  await page.getByRole("navigation", { name: "Navigation principale" }).getByRole("link", { name: menu }).click();
}
