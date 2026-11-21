import AxeBuilder from "@axe-core/playwright";
import { expect, test as base, type Page } from "@playwright/test";

export type Account = "admin" | "alice" | "chloe";

const PASSWORD_VARIABLES: Record<Account, string> = {
  admin: "E2E_ADMIN_PASSWORD",
  alice: "E2E_ALICE_PASSWORD",
  chloe: "E2E_CHLOE_PASSWORD",
};

/** Unique suffix per run: journeys can be rerun without resetting the database. */
export const RUN = Date.now().toString(36);

/**
 * Sign-in through the real Keycloak page. The password comes from the environment; it is set
 * by `evaluate` (not `fill`) because the arguments of `evaluate` appear neither in the call log
 * nor in Playwright error messages.
 */
export async function login(
  page: Page,
  account: Account,
  beforeCredentials?: () => Promise<void>,
  mobile = false,
): Promise<void> {
  const variable = PASSWORD_VARIABLES[account];
  const password = process.env[variable];
  if (!password) throw new Error(`Environment variable ${variable} missing (see e2e/run-compose.sh).`);

  await page.goto("/");
  // On a phone-sized screen the account block lives in the side menu.
  if (mobile) await page.getByRole("button", { name: "Ouvrir le menu" }).click();
  await page.getByRole("button", { name: "Connexion" }).click();
  await page.locator("#username").waitFor();
  await checkKeycloakPage(page);
  if (beforeCredentials) await beforeCredentials();
  await page.locator("#username").fill(account);
  await page.locator("#password").evaluate((input: HTMLInputElement, value: string) => {
    input.value = value;
  }, password);
  await page.locator("#kc-login").click();
  if (mobile) {
    await page.getByRole("button", { name: "Ouvrir le menu" }).click();
    await expect(page.getByRole("dialog", { name: "Menu" }).getByRole("button", { name: "Déconnexion" })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog", { name: "Menu" })).toHaveCount(0);
    return;
  }
  await expect(page.getByRole("button", { name: "Déconnexion" })).toBeVisible();
  await expect(page.getByRole("banner").locator("p").filter({ hasText: new RegExp(`^${account}$`) })).toBeVisible();
}

/**
 * On the cluster (host `app.127.0.0.1.sslip.io`), the sign-in page must come from
 * `https://auth.127.0.0.1.sslip.io` and be in French. On the compose stack, Keycloak is on
 * localhost: only French is checked.
 */
async function checkKeycloakPage(page: Page): Promise<void> {
  const url = new URL(page.url());
  if (new URL(process.env.E2E_BASE_URL ?? "http://localhost").hostname.startsWith("app.")) {
    expect(url.origin, "origin of the sign-in page").toBe("https://auth.127.0.0.1.sslip.io");
  }
  await expect(page.locator("html")).toHaveAttribute("lang", "fr");
}

/** Navigates through the menu: the top bar on a desktop screen, the side menu on a phone-sized one. */
export async function goTo(page: Page, menu: string): Promise<void> {
  const burger = page.getByRole("button", { name: "Ouvrir le menu" });
  if (await burger.isVisible()) await burger.click();
  await page.getByRole("navigation", { name: "Navigation principale" }).getByRole("link", { name: menu }).click();
}

/**
 * Accessibility check with axe-core (WCAG 2.0, 2.1 and 2.2, levels A and AA) on the page as it is
 * displayed: fails with the rule, the impact and the first elements of every violation.
 */
export async function expectNoAccessibilityViolation(page: Page, where: string): Promise<void> {
  // Skeletons and toasts are transitions: axe looks at the settled page.
  await expect(page.locator('[aria-busy="true"]')).toHaveCount(0);
  await page.waitForLoadState("networkidle");
  // A toast fading in is semi-transparent: axe would measure a blended colour. Wait for the
  // finite animations and transitions to end (the timeout covers an animation that never ends).
  await page
    .evaluate(() =>
      Promise.race([
        Promise.all(document.getAnimations().map((a) => a.finished.catch(() => undefined))),
        new Promise((resolve) => setTimeout(resolve, 3_000)),
      ]),
    )
    .catch(() => undefined);
  const { violations } = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  const report = violations.map(
    (v) => `${v.id} (${v.impact}): ${v.help} - ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`,
  );
  expect(report, `axe violations on ${where}`).toEqual([]);
}

/**
 * The project's `test`: besides Playwright's `test`, an automatic check on every test.
 * It fails the test if, during the journey, the browser reports a violation of the
 * Content-Security-Policy (`securitypolicyviolation` event or console message) or if an
 * API call (`/api/v1/`) fails (network error or unexpected 4xx/5xx status).
 */
export const test = base.extend<{ watchBrowser: void }>({
  watchBrowser: [
    async ({ page }, use) => {
      const problems: string[] = [];
      await page.exposeFunction("__reportCsp", (directive: string, blocked: string) => {
        problems.push(`CSP violation: ${directive} blocked ${blocked}`);
      });
      await page.addInitScript(() => {
        const report = (window as unknown as { __reportCsp: (d: string, b: string) => void }).__reportCsp;
        document.addEventListener("securitypolicyviolation", (event) => {
          report(event.violatedDirective, event.blockedURI);
        });
      });
      page.on("console", (message) => {
        if (/Content[- ]Security[- ]Policy/i.test(message.text())) problems.push(`console: ${message.text()}`);
      });
      page.on("requestfailed", (request) => {
        const error = request.failure()?.errorText ?? "";
        // A request aborted by a navigation (sign-out) is not an API error.
        if (request.url().includes("/api/v1/") && !error.includes("ERR_ABORTED")) {
          problems.push(`API call failed: ${request.method()} ${request.url()} (${error})`);
        }
      });
      page.on("response", (response) => {
        if (response.url().includes("/api/v1/") && response.status() >= 400) {
          problems.push(`API call error: ${response.request().method()} ${response.url()} (${response.status()})`);
        }
      });
      await use();
      // Lets the last events (CSP report, API response) arrive before the check.
      await page.waitForLoadState("networkidle").catch(() => undefined);
      expect(problems, "CSP violations or network errors during the journey").toEqual([]);
    },
    { auto: true },
  ],
});

export { expect };
