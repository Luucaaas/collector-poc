import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:5173";

// End-to-end journeys in a real browser (Chromium only), OUTSIDE CI (processus-test.md).
// By default they target the application served by Vite (npm run dev) in front of the docker compose stack.
// No trace, screenshot or video, and no HTML report: Playwright reports repeat the
// typed values (demo account passwords) in the step titles.
export default defineConfig({
  testDir: "./e2e",
  // The screenshots for the defense (CAPTURES=1) and the Grafana ones (GRAFANA_CAPTURES=1, protocol 5)
  // are run separately, never with the journeys.
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
  // Starts the Vite dev server only if the targeted address is the default one.
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : { command: "npm run dev", url: baseURL, reuseExistingServer: true, timeout: 60_000 },
});
