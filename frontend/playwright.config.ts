import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:5173";

// Parcours de bout en bout dans un vrai navigateur (Chromium seul), HORS CI (processus-test.md).
// Par défaut, ils visent l'application servie par Vite (npm run dev) devant la pile docker compose.
// Aucune trace, capture ni vidéo, et pas de rapport HTML : les rapports Playwright reprennent les
// valeurs saisies (mots de passe des comptes de démo) dans le titre des étapes.
export default defineConfig({
  testDir: "./e2e",
  // Les captures pour la soutenance (CAPTURES=1) et celles de Grafana (GRAFANA_CAPTURES=1, protocole 5)
  // sont lancées à part, jamais avec les parcours.
  testMatch: process.env.GRAFANA_CAPTURES
    ? /grafana\.spec\.ts/
    : process.env.CAPTURES
      ? /captures\.spec\.ts/
      : /parcours\.spec\.ts/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL,
    locale: "fr-FR",
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  // Lance le serveur de développement de Vite seulement si l'adresse visée est celle par défaut.
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : { command: "npm run dev", url: baseURL, reuseExistingServer: true, timeout: 60_000 },
});
