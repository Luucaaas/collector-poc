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
  it("accepts a valid configuration and strips the trailing slash from addresses", async () => {
    const config = await loadConfig(fetchOf(Response.json(VALID)));
    expect(config.catalogApiUrl).toBe("https://api.example/catalog/api/v1");
    expect(config.clientId).toBe("collector-web");
  });

  it("reports a missing file (404) with a French message", async () => {
    await expect(loadConfig(fetchOf(new Response("", { status: 404 })))).rejects.toThrow(/introuvable \(HTTP 404\)/);
  });

  it("reports a network failure", async () => {
    await expect(loadConfig(fetchOf(new TypeError("network")))).rejects.toThrow(/Impossible de charger/);
  });

  it("reports unreadable JSON", async () => {
    await expect(loadConfig(fetchOf(new Response("not json")))).rejects.toThrow(/pas un JSON valide/);
  });

  it("rejects a missing field or an invalid address", () => {
    expect(() => parseConfig({ ...VALID, clientId: "" })).toThrow(ConfigError);
    expect(() => parseConfig({ ...VALID, authority: "n'importe quoi" })).toThrow(/« authority »/);
    expect(() => parseConfig({ ...VALID, catalogApiUrl: undefined })).toThrow(/« catalogApiUrl »/);
    expect(() => parseConfig({ ...VALID, notificationApiUrl: "ftp://x" })).toThrow(/« notificationApiUrl »/);
    expect(() => parseConfig(null)).toThrow(ConfigError);
  });
});
