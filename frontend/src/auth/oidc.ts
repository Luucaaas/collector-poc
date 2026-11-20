import { InMemoryWebStorage, WebStorageStateStore, type UserManagerSettings } from "oidc-client-ts";
import type { AppConfig } from "../config";

/**
 * OIDC settings: Authorization Code (PKCE S256 applied by oidc-client-ts), tokens in memory.
 *
 * - `userStore`: the signed-in user (access, refresh and identity tokens) lives in a
 *   JavaScript object. Nothing is written to localStorage or sessionStorage: an injected
 *   script (XSS) cannot read them from persistent storage, and reloading the page forces a
 *   new sign-in (the Keycloak session cookie makes it immediate).
 * - `stateStore`: only the transient redirect state (state, code_verifier) must survive the
 *   page change, so it sits in sessionStorage (tab-scoped) and oidc-client-ts removes it as
 *   soon as Keycloak returns. It contains no token.
 */
export function createOidcSettings(config: AppConfig, origin: string): UserManagerSettings {
  return {
    authority: config.authority,
    client_id: config.clientId,
    redirect_uri: `${origin}/`,
    post_logout_redirect_uri: `${origin}/`,
    response_type: "code",
    // "profile" brings preferred_username (realm client scope, a single mapper).
    scope: "openid profile",
    automaticSilentRenew: true,
    userStore: new WebStorageStateStore({ store: new InMemoryWebStorage() }),
    stateStore: new WebStorageStateStore({ store: window.sessionStorage }),
  };
}
