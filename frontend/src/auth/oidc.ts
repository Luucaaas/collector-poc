import { InMemoryWebStorage, WebStorageStateStore, type UserManagerSettings } from "oidc-client-ts";
import type { AppConfig } from "../config";

/**
 * Réglages OIDC : Authorization Code (PKCE S256 appliqué par oidc-client-ts), jetons en mémoire.
 *
 * - `userStore` : l'utilisateur connecté (jetons d'accès, de rafraîchissement et d'identité) vit
 *   dans un objet JavaScript. Rien n'est écrit dans localStorage ni sessionStorage : un script
 *   injecté (XSS) ne peut pas les lire dans un stockage persistant, et recharger la page oblige à
 *   se reconnecter (le cookie de session Keycloak rend cette reconnexion immédiate).
 * - `stateStore` : seul l'état transitoire de la redirection (state, code_verifier) doit survivre
 *   au changement de page, donc il est dans sessionStorage (limité à l'onglet) et oidc-client-ts le
 *   supprime dès le retour de Keycloak. Il ne contient aucun jeton.
 */
export function createOidcSettings(config: AppConfig, origin: string): UserManagerSettings {
  return {
    authority: config.authority,
    client_id: config.clientId,
    redirect_uri: `${origin}/`,
    post_logout_redirect_uri: `${origin}/`,
    response_type: "code",
    // « profile » apporte preferred_username (client scope du realm, un seul mapper).
    scope: "openid profile",
    automaticSilentRenew: true,
    userStore: new WebStorageStateStore({ store: new InMemoryWebStorage() }),
    stateStore: new WebStorageStateStore({ store: window.sessionStorage }),
  };
}
