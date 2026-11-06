import { expect, test } from "@playwright/test";

// Captures du tableau de bord Grafana pour le protocole 5 (charge et disponibilité), lancées à part
// par docs/04-experimentations/05-charge-disponibilite/run.sh (GRAFANA_CAPTURES=1, voir
// playwright.config.ts), jamais avec les parcours.
// Le mot de passe de `admin` vient de l'environnement ; il est posé par `evaluate` (comme dans
// helpers.ts : ses arguments n'apparaissent ni dans le journal d'appels ni dans les erreurs).
// Aucune capture n'est prise sur la page de connexion. La vérification TLS reste active.
const GRAFANA = "https://grafana.127.0.0.1.sslip.io";

interface Capture {
  file: string; // chemin du PNG
  service: string; // valeur de la variable `service` du tableau de bord
  from: number; // début de la plage (ms depuis 1970)
  to: number;
}

test.use({ viewport: { width: 1600, height: 1100 }, locale: "fr-FR" });

test("captures Grafana : tableau de bord Collector - service", async ({ page }) => {
  const password = process.env.GRAFANA_PASSWORD;
  const plan = process.env.GRAFANA_CAPTURE_PLAN;
  if (!password) throw new Error("Variable d'environnement GRAFANA_PASSWORD absente (voir run.sh).");
  if (!plan) throw new Error("Variable d'environnement GRAFANA_CAPTURE_PLAN absente (voir run.sh).");
  const captures = JSON.parse(plan) as Capture[];

  await page.goto(`${GRAFANA}/login`);
  await page.locator('input[name="user"]').fill("admin");
  await page.locator('input[name="password"]').evaluate((input: HTMLInputElement, value: string) => {
    // React suit la valeur d'un champ par son propre accesseur : on appelle celui du navigateur,
    // puis l'événement `input` prévient React de la nouvelle valeur.
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
    setter?.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  }, password);
  await page.locator('button[type="submit"]').click();
  await expect(page).not.toHaveURL(/\/login/);
  // Grafana propose parfois de changer le mot de passe à la première connexion : on passe.
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
    await page.waitForTimeout(4_000); // laisse les panneaux finir leur dessin
    await page.screenshot({ path: capture.file });
  }
});
