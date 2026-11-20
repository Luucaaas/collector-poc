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

describe("OIDC settings", () => {
  it("uses the Authorization Code flow, renews automatically and returns to the root", () => {
    const settings = createOidcSettings(CONFIG, "https://app.test");
    expect(settings.response_type).toBe("code");
    expect(settings.scope).toBe("openid profile");
    expect(settings.client_id).toBe("collector-web");
    expect(settings.redirect_uri).toBe("https://app.test/");
    expect(settings.post_logout_redirect_uri).toBe("https://app.test/");
    expect(settings.automaticSilentRenew).toBe(true);
  });

  it("writes no oidc.* key to localStorage or sessionStorage after sign-in", async () => {
    const manager = new UserManager(createOidcSettings(CONFIG, "https://app.test"));
    await manager.storeUser(makeUser());

    // The user is available (in memory) ...
    const stored = await manager.getUser();
    expect(stored?.profile.preferred_username).toBe("alice");
    // ... but nothing is persisted in the browser storages.
    expect(oidcKeys(localStorage)).toEqual([]);
    expect(oidcKeys(sessionStorage)).toEqual([]);
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it("keeps the token out of localStorage even during the redirect (transient state in sessionStorage)", async () => {
    // Mocked OIDC discovery document: no network access.
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
    // Only the redirect state (state, code_verifier), without a token, is in sessionStorage.
    expect(oidcKeys(sessionStorage)).toHaveLength(1);
    expect(sessionStorage.getItem(oidcKeys(sessionStorage)[0])).not.toContain("access_token");
  });
});

describe("roles", () => {
  it("reads realm_access.roles from the access token", () => {
    expect(getRoles(makeUser())).toEqual(["buyer", "default-roles-collector"]);
  });

  it("returns an empty list without a user or with an unreadable token", () => {
    expect(getRoles(null)).toEqual([]);
    const user = makeUser();
    user.access_token = "pas-un-jwt";
    expect(getRoles(user)).toEqual([]);
  });

  it("shows the user name", () => {
    expect(displayName(makeUser())).toBe("alice");
    expect(displayName(null)).toBe("Utilisateur connecté");
    const anonymous = makeUser();
    anonymous.profile = { ...anonymous.profile, preferred_username: undefined };
    expect(displayName(anonymous)).toBe("Utilisateur connecté");
  });
});
