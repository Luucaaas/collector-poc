import type { User } from "oidc-client-ts";

export type Role = "buyer" | "seller" | "admin";

/** French labels shown to people; the technical role values never change. */
export const ROLE_LABELS: Record<Role, string> = { buyer: "acheteur", seller: "vendeur", admin: "administrateur" };

export const isAppRole = (role: string): role is Role => Object.hasOwn(ROLE_LABELS, role);

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
 * Realm roles (`realm_access.roles` claim of the access token), FOR DISPLAY ONLY:
 * hiding a menu is not access control. The token signature is not verified here;
 * the APIs verify the signature and the roles on every request.
 */
export function getRoles(user: User | null | undefined): string[] {
  if (!user?.access_token) return [];
  const realmAccess = decodePayload(user.access_token).realm_access as { roles?: unknown } | undefined;
  const roles = realmAccess?.roles;
  return Array.isArray(roles) ? roles.filter((r): r is string => typeof r === "string") : [];
}

export function displayName(user: User | null | undefined): string {
  const profile = user?.profile;
  // The realm only provides `preferred_username` (data minimization).
  return profile?.preferred_username ?? "Utilisateur connecté";
}
