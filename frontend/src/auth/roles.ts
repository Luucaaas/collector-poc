import type { User } from "oidc-client-ts";

export type Role = "buyer" | "seller" | "admin";

function decodePayload(jwt: string): Record<string, unknown> {
  try {
    const part = jwt.split(".")[1] ?? "";
    const base64 = part.replace(/-/g, "+").replace(/_/g, "/");
    const json = new TextDecoder().decode(Uint8Array.from(atob(base64), (c) => c.charCodeAt(0)));
    return JSON.parse(json) as Record<string, unknown>;
  } catch {
    return {};
  }
}

/**
 * Rôles du realm (claim `realm_access.roles` du jeton d'accès), POUR L'AFFICHAGE SEULEMENT :
 * masquer un menu n'est pas un contrôle d'accès. La signature du jeton n'est pas vérifiée ici ;
 * ce sont les API qui vérifient la signature et les rôles à chaque requête.
 */
export function getRoles(user: User | null | undefined): string[] {
  if (!user?.access_token) return [];
  const realmAccess = decodePayload(user.access_token).realm_access as { roles?: unknown } | undefined;
  const roles = realmAccess?.roles;
  return Array.isArray(roles) ? roles.filter((r): r is string => typeof r === "string") : [];
}

export function displayName(user: User | null | undefined): string {
  const profile = user?.profile;
  // Le realm ne fournit que `preferred_username` (minimisation des données).
  return profile?.preferred_username ?? "Utilisateur connecté";
}
