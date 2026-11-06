import { OidcClient, User, UserManager } from "oidc-client-ts";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fakeAccessToken } from "../test/jwt";
import { createOidcSettings } from "./oidc";
import { displayName, getRoles } from "./roles";

const CONFIG = {
  authority: "https://auth.test/realms/collector",
  clientId: "collector-web",
  catalogApiUrl: "https://api.test/catalog/api/v1",
  notificationApiUrl: "https://api.test/notification/api/v1",
};

const oidcKeys = (storage: Storage) => Object.keys(storage).filter((k) => k.startsWith("oidc."));

function makeUser() {
  return new User({
    access_token: fakeAccessToken(["buyer", "default-roles-collector"]),
    token_type: "Bearer",
    refresh_token: "refresh-factice",
    id_token: "id-factice",
    scope: "openid profile",
    expires_at: Math.floor(Date.now() / 1000) + 300,
    profile: { sub: "u1", iss: CONFIG.authority, aud: "collector-web", exp: 0, iat: 0, preferred_username: "alice" },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("réglages OIDC", () => {
  it("utilise le flux Authorization Code, renouvelle automatiquement et revient sur la racine", () => {
    const settings = createOidcSettings(CONFIG, "https://app.test");
    expect(settings.response_type).toBe("code");
    expect(settings.scope).toBe("openid profile");
    expect(settings.client_id).toBe("collector-web");
    expect(settings.redirect_uri).toBe("https://app.test/");
    expect(settings.post_logout_redirect_uri).toBe("https://app.test/");
    expect(settings.automaticSilentRenew).toBe(true);
  });

  it("n'écrit aucune clé oidc.* dans localStorage ni sessionStorage après une connexion", async () => {
    const manager = new UserManager(createOidcSettings(CONFIG, "https://app.test"));
    await manager.storeUser(makeUser());

    // L'utilisateur est bien disponible (en mémoire) ...
    const stored = await manager.getUser();
    expect(stored?.profile.preferred_username).toBe("alice");
    // ... mais rien n'est persisté dans les stockages du navigateur.
    expect(oidcKeys(localStorage)).toEqual([]);
    expect(oidcKeys(sessionStorage)).toEqual([]);
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it("garde le jeton hors de localStorage même pendant la redirection (état transitoire en sessionStorage)", async () => {
    // Document de découverte OIDC simulé : aucun accès réseau.
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          Response.json({
            issuer: CONFIG.authority,
            authorization_endpoint: `${CONFIG.authority}/protocol/openid-connect/auth`,
            token_endpoint: `${CONFIG.authority}/protocol/openid-connect/token`,
          }),
        ),
      ),
    );
    const client = new OidcClient(createOidcSettings(CONFIG, "https://app.test"));
    const request = await client.createSigninRequest({});
    const url = new URL(request.url);
    expect(url.searchParams.get("response_type")).toBe("code");
    expect(url.searchParams.get("code_challenge_method")).toBe("S256");
    expect(url.searchParams.get("code_challenge")).toBeTruthy();
    expect(oidcKeys(localStorage)).toEqual([]);
    // Seul l'état de la redirection (state, code_verifier), sans jeton, est dans sessionStorage.
    expect(oidcKeys(sessionStorage)).toHaveLength(1);
    expect(sessionStorage.getItem(oidcKeys(sessionStorage)[0])).not.toContain("access_token");
  });
});

describe("rôles", () => {
  it("lit realm_access.roles dans le jeton d'accès", () => {
    expect(getRoles(makeUser())).toEqual(["buyer", "default-roles-collector"]);
  });

  it("renvoie une liste vide sans utilisateur ou avec un jeton illisible", () => {
    expect(getRoles(null)).toEqual([]);
    const user = makeUser();
    user.access_token = "pas-un-jwt";
    expect(getRoles(user)).toEqual([]);
  });

  it("affiche le nom d'utilisateur", () => {
    expect(displayName(makeUser())).toBe("alice");
    expect(displayName(null)).toBe("Utilisateur connecté");
    const anonymous = makeUser();
    anonymous.profile = { ...anonymous.profile, preferred_username: undefined };
    expect(displayName(anonymous)).toBe("Utilisateur connecté");
  });
});
