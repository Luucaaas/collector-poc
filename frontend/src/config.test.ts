import { describe, expect, it } from "vitest";
import { ConfigError, loadConfig, parseConfig } from "./config";

const VALID = {
  authority: "https://auth.example/realms/collector",
  clientId: "collector-web",
  catalogApiUrl: "https://api.example/catalog/api/v1/",
  notificationApiUrl: "https://api.example/notification/api/v1",
};

const fetchOf = (response: Response | Error): typeof fetch =>
  (() => (response instanceof Error ? Promise.reject(response) : Promise.resolve(response))) as typeof fetch;

describe("configuration", () => {
  it("accepte une configuration valide et retire la barre finale des adresses", async () => {
    const config = await loadConfig(fetchOf(Response.json(VALID)));
    expect(config.catalogApiUrl).toBe("https://api.example/catalog/api/v1");
    expect(config.clientId).toBe("collector-web");
  });

  it("signale un fichier absent (404) par un message en français", async () => {
    await expect(loadConfig(fetchOf(new Response("", { status: 404 })))).rejects.toThrow(/introuvable \(HTTP 404\)/);
  });

  it("signale une panne réseau", async () => {
    await expect(loadConfig(fetchOf(new TypeError("réseau")))).rejects.toThrow(/Impossible de charger/);
  });

  it("signale un JSON illisible", async () => {
    await expect(loadConfig(fetchOf(new Response("pas du json")))).rejects.toThrow(/pas un JSON valide/);
  });

  it("refuse un champ manquant ou une adresse invalide", () => {
    expect(() => parseConfig({ ...VALID, clientId: "" })).toThrow(ConfigError);
    expect(() => parseConfig({ ...VALID, authority: "n'importe quoi" })).toThrow(/« authority »/);
    expect(() => parseConfig({ ...VALID, catalogApiUrl: undefined })).toThrow(/« catalogApiUrl »/);
    expect(() => parseConfig({ ...VALID, notificationApiUrl: "ftp://x" })).toThrow(/« notificationApiUrl »/);
    expect(() => parseConfig(null)).toThrow(ConfigError);
  });
});
