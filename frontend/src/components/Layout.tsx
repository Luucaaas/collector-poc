import { AppBar, Box, Button, Chip, Container, Stack, Toolbar, Typography } from "@mui/material";
import { useAuth } from "react-oidc-context";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { displayName, getRoles, type Role } from "../auth/roles";

const NAV: { to: string; label: string; role?: Role }[] = [
  { to: "/", label: "Catalogue" },
  { to: "/vendre", label: "Vendre", role: "seller" },
  { to: "/centres-interet", label: "Mes centres d'intérêt", role: "buyer" },
  { to: "/categories", label: "Catégories", role: "admin" },
];

/** Barre de navigation (menus selon les rôles, affichage seulement) et zone de contenu. */
export function Layout() {
  const auth = useAuth();
  const location = useLocation();
  const roles = getRoles(auth.user);

  return (
    <>
      <AppBar position="static">
        <Toolbar sx={{ gap: 2, flexWrap: "wrap" }}>
          <Typography variant="h6" component={Link} to="/" sx={{ color: "inherit", textDecoration: "none" }}>
            Collector.shop
          </Typography>
          <Stack component="nav" direction="row" spacing={1} aria-label="Navigation principale">
            {NAV.filter((item) => !item.role || roles.includes(item.role)).map((item) => (
              <Button key={item.to} color="inherit" component={NavLink} to={item.to} end>
                {item.label}
              </Button>
            ))}
          </Stack>
          <Box sx={{ flexGrow: 1 }} />
          {auth.isAuthenticated ? (
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
              <Typography>{displayName(auth.user)}</Typography>
              {roles
                .filter((r) => ["buyer", "seller", "admin"].includes(r))
                .map((r) => (
                  <Chip key={r} size="small" label={r} />
                ))}
              <Button
                color="inherit"
                variant="outlined"
                onClick={() => void auth.signoutRedirect({ post_logout_redirect_uri: `${window.location.origin}/` })}
              >
                Déconnexion
              </Button>
            </Stack>
          ) : (
            <Button
              color="inherit"
              variant="outlined"
              disabled={auth.isLoading}
              onClick={() => void auth.signinRedirect({ state: { returnTo: location.pathname } })}
            >
              Connexion
            </Button>
          )}
        </Toolbar>
      </AppBar>
      <Container sx={{ py: 4 }} component="main">
        <Outlet />
      </Container>
    </>
  );
}
