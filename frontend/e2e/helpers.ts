import { expect, test as base, type Page } from "@playwright/test";

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
export async function login(
  page: Page,
  account: Account,
  beforeCredentials?: () => Promise<void>,
): Promise<void> {
  const variable = PASSWORD_VARIABLES[account];
  const password = process.env[variable];
  if (!password) throw new Error(`Variable d'environnement ${variable} absente (voir e2e/run-compose.sh).`);

  await page.goto("/");
  await page.getByRole("button", { name: "Connexion" }).click();
  await page.locator("#username").waitFor();
  await checkKeycloakPage(page);
  if (beforeCredentials) await beforeCredentials();
  await page.locator("#username").fill(account);
  await page.locator("#password").evaluate((input: HTMLInputElement, value: string) => {
    input.value = value;
  }, password);
  await page.locator("#kc-login").click();
  await expect(page.getByRole("button", { name: "Déconnexion" })).toBeVisible();
  await expect(page.getByRole("banner").locator("p").filter({ hasText: new RegExp(`^${account}$`) })).toBeVisible();
}

/**
 * Sur le cluster (hôte `app.127.0.0.1.sslip.io`), la page de connexion doit venir de
 * `https://auth.127.0.0.1.sslip.io` et être en français. Sur la pile compose, Keycloak est sur
 * localhost : seul le français est vérifié.
 */
async function checkKeycloakPage(page: Page): Promise<void> {
  const url = new URL(page.url());
  if (new URL(process.env.E2E_BASE_URL ?? "http://localhost").hostname.startsWith("app.")) {
    expect(url.origin, "origine de la page de connexion").toBe("https://auth.127.0.0.1.sslip.io");
  }
  await expect(page.locator("html")).toHaveAttribute("lang", "fr");
}

export async function goTo(page: Page, menu: string): Promise<void> {
  await page.getByRole("navigation", { name: "Navigation principale" }).getByRole("link", { name: menu }).click();
}

/**
 * `test` du projet : en plus du `test` de Playwright, un contrôle automatique sur chaque test.
 * Il fait échouer le test si, pendant le parcours, le navigateur signale une violation de la
 * Content-Security-Policy (événement `securitypolicyviolation` ou message de console) ou si un
 * appel à l'API (`/api/v1/`) échoue (erreur réseau ou statut 4xx/5xx non attendu).
 */
export const test = base.extend<{ watchBrowser: void }>({
  watchBrowser: [
    async ({ page }, use) => {
      const problems: string[] = [];
      await page.exposeFunction("__reportCsp", (directive: string, blocked: string) => {
        problems.push(`violation CSP : ${directive} a bloqué ${blocked}`);
      });
      await page.addInitScript(() => {
        const report = (window as unknown as { __reportCsp: (d: string, b: string) => void }).__reportCsp;
        document.addEventListener("securitypolicyviolation", (event) => {
          report(event.violatedDirective, event.blockedURI);
        });
      });
      page.on("console", (message) => {
        if (/Content[- ]Security[- ]Policy/i.test(message.text())) problems.push(`console : ${message.text()}`);
      });
      page.on("requestfailed", (request) => {
        const error = request.failure()?.errorText ?? "";
        // Une requête interrompue par une navigation (déconnexion) n'est pas une erreur de l'API.
        if (request.url().includes("/api/v1/") && !error.includes("ERR_ABORTED")) {
          problems.push(`appel API en échec : ${request.method()} ${request.url()} (${error})`);
        }
      });
      page.on("response", (response) => {
        if (response.url().includes("/api/v1/") && response.status() >= 400) {
          problems.push(`appel API en erreur : ${response.request().method()} ${response.url()} (${response.status()})`);
        }
      });
      await use();
      // Laisse arriver les derniers événements (rapport CSP, réponse d'API) avant le contrôle.
      await page.waitForLoadState("networkidle").catch(() => undefined);
      expect(problems, "violations CSP ou erreurs réseau pendant le parcours").toEqual([]);
    },
    { auto: true },
  ],
});

export { expect };
