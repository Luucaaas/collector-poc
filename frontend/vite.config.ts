import react from "@vitejs/plugin-react";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";
import devConfig from "./config.dev.json" with { type: "json" };

// En développement seulement, le serveur Vite répond à /config.json avec config.dev.json
// (pile docker compose). Ce fichier est à la racine, hors de public/ : il n'entre jamais dans dist/,
// où /config.json est celui du cluster (public/config.json).
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
    // Les parcours Playwright (e2e/*.spec.ts) sont lancés à part, par `npm run e2e`.
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
