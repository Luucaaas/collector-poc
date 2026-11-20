import { expect, test } from "@playwright/test";

// Screenshots of the Grafana dashboard for protocol 5 (load and availability), run separately
// by docs/04-experimentations/05-charge-disponibilite/run.sh (GRAFANA_CAPTURES=1, see
// playwright.config.ts), never with the journeys.
// The `admin` password comes from the environment; it is set by `evaluate` (as in
// helpers.ts: its arguments appear neither in the call log nor in errors).
// No screenshot is taken on the sign-in page. TLS verification stays enabled.
const GRAFANA = "https://grafana.127.0.0.1.sslip.io";

interface Capture {
  file: string; // PNG path
  service: string; // value of the dashboard `service` variable
  from: number; // start of the range (ms since 1970)
  to: number;
}

test.use({ viewport: { width: 1600, height: 1100 }, locale: "fr-FR" });

test("Grafana screenshots: Collector - service dashboard", async ({ page }) => {
  const password = process.env.GRAFANA_PASSWORD;
  const plan = process.env.GRAFANA_CAPTURE_PLAN;
  if (!password) throw new Error("Variable d'environnement GRAFANA_PASSWORD absente (voir run.sh).");
  if (!plan) throw new Error("Variable d'environnement GRAFANA_CAPTURE_PLAN absente (voir run.sh).");
  const captures = JSON.parse(plan) as Capture[];

  await page.goto(`${GRAFANA}/login`);
  await page.locator('input[name="user"]').fill("admin");
  await page.locator('input[name="password"]').evaluate((input: HTMLInputElement, value: string) => {
    // React tracks a field's value through its own accessor: we call the browser's one,
    // then the `input` event tells React about the new value.
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
    setter?.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  }, password);
  await page.locator('button[type="submit"]').click();
  await expect(page).not.toHaveURL(/\/login/);
  // Grafana sometimes offers to change the password at first sign-in: skip it.
  const skip = page.getByRole("button", { name: /Skip|Ignorer/ });
  if (await skip.isVisible().catch(() => false)) await skip.click();

  for (const capture of captures) {
    const query = new URLSearchParams({
      orgId: "1",
      from: String(capture.from),
      to: String(capture.to),
      "var-service": capture.service,
      refresh: "",
      kiosk: "true",
    });
    await page.goto(`${GRAFANA}/d/collector-service?${query.toString()}`);
    await expect(page.getByText("Débit (requêtes par seconde)").first()).toBeVisible();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(4_000); // lets the panels finish drawing
    await page.screenshot({ path: capture.file });
  }
});
