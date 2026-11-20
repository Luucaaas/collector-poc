import react from "@vitejs/plugin-react";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";
import devConfig from "./config.dev.json" with { type: "json" };

// In development only, the Vite server answers /config.json with config.dev.json
// (docker compose stack). This file is at the root, outside public/: it never enters dist/,
// where /config.json is the cluster one (public/config.json).
const serveDevConfig: Plugin = {
  name: "serve-dev-config",
  apply: "serve",
  configureServer(server) {
    server.middlewares.use("/config.json", (_req, res) => {
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(devConfig));
    });
  },
};

export default defineConfig({
  plugins: [react(), serveDevConfig],
  server: { port: 5173, strictPort: true },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    // The Playwright journeys (e2e/*.spec.ts) are run separately, by `npm run e2e`.
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
