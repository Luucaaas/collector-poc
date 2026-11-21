import { Button, Chip, Stack, Typography } from "@mui/material";
import { useAuth } from "react-oidc-context";
import { useLocation } from "react-router";
import { displayName, getRoles, isAppRole, ROLE_LABELS } from "../auth/roles";

/** Sign-in button, or name + role chips + sign-out button. `inDrawer` stacks them vertically. */
export function AccountBlock({ inDrawer = false }: { inDrawer?: boolean }) {
  const auth = useAuth();
  const location = useLocation();

  if (!auth.isAuthenticated) {
    return (
      <Button
        color={inDrawer ? "primary" : "inherit"}
        variant={inDrawer ? "contained" : "outlined"}
        fullWidth={inDrawer}
        disabled={auth.isLoading}
        onClick={() => void auth.signinRedirect({ state: { returnTo: location.pathname } })}
      >
        Connexion
      </Button>
    );
  }

  const roles = getRoles(auth.user).filter(isAppRole);
  return (
    <Stack direction={inDrawer ? "column" : "row"} spacing={1} sx={{ alignItems: inDrawer ? "stretch" : "center" }}>
      <Typography>{displayName(auth.user)}</Typography>
      <Stack direction="row" spacing={1}>
        {roles.map((r) => (
          <Chip
            key={r}
            size="small"
            label={ROLE_LABELS[r]}
            variant={inDrawer ? "filled" : "outlined"}
            sx={inDrawer ? undefined : { color: "inherit", borderColor: "currentColor" }}
          />
        ))}
      </Stack>
      <Button
        color={inDrawer ? "primary" : "inherit"}
        variant="outlined"
        onClick={() => void auth.signoutRedirect({ post_logout_redirect_uri: `${window.location.origin}/` })}
      >
        Déconnexion
      </Button>
    </Stack>
  );
}
