import { Alert, CircularProgress, Stack } from "@mui/material";
import type { ReactNode } from "react";
import { useEffect } from "react";
import { useAuth } from "react-oidc-context";
import { useLocation } from "react-router";
import { getRoles, type Role } from "./roles";

/**
 * Garde de route : non connecté → redirection vers la connexion Keycloak (puis retour sur la page
 * demandée) ; connecté sans le rôle → « accès refusé ». Garde d'affichage seulement.
 */
export function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const auth = useAuth();
  const location = useLocation();
  const returnTo = location.pathname + location.search;
  const mustSignIn = !auth.isLoading && !auth.isAuthenticated && !auth.error;

  useEffect(() => {
    if (mustSignIn) void auth.signinRedirect({ state: { returnTo } });
    // `auth` change à chaque rendu ; seuls `mustSignIn` et `returnTo` déclenchent la redirection.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mustSignIn, returnTo]);

  if (auth.error) {
    return <Alert severity="error">La connexion a échoué : {auth.error.message}</Alert>;
  }
  if (auth.isLoading || !auth.isAuthenticated) {
    return (
      <Stack direction="row" spacing={2} role="status" sx={{ alignItems: "center" }}>
        <CircularProgress size={20} />
        <span>Redirection vers la connexion…</span>
      </Stack>
    );
  }
  if (!getRoles(auth.user).includes(role)) {
    return (
      <Alert severity="warning">
        Accès refusé : cette page est réservée aux utilisateurs ayant le rôle « {role} ».
      </Alert>
    );
  }
  return <>{children}</>;
}
