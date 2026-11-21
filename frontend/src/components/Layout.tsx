import {
  AppBar,
  Box,
  Button,
  Container,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  SvgIcon,
  Toolbar,
  Typography,
  useMediaQuery,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { Suspense, useState } from "react";
import { useAuth } from "react-oidc-context";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { getRoles, type Role } from "../auth/roles";
import { AccountBlock } from "./AccountBlock";
import { ErrorBoundary } from "./ErrorBoundary";
import { LoadingSkeleton } from "./LoadingSkeleton";
import { Logo } from "./Logo";
import { RejectedArticlesProvider } from "./RejectedArticles";
import { ToastProvider } from "./Toast";

const NAV: { to: string; label: string; role?: Role }[] = [
  { to: "/", label: "Accueil" },
  { to: "/catalogue", label: "Catalogue" },
  { to: "/vendre", label: "Vendre", role: "seller" },
  { to: "/centres-interet", label: "Mes centres d'intérêt", role: "buyer" },
  { to: "/categories", label: "Catégories", role: "admin" },
];

function MenuIcon() {
  return (
    <SvgIcon>
      <path d="M3 6h18v2H3zm0 5h18v2H3zm0 5h18v2H3z" />
    </SvgIcon>
  );
}

/** Header (logo, menus by role: display only, mobile drawer, sign-in) and content area. */
export function Layout() {
  const auth = useAuth();
  const location = useLocation();
  const theme = useTheme();
  const mobile = useMediaQuery(theme.breakpoints.down("md"));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const roles = getRoles(auth.user);
  const items = NAV.filter((item) => !item.role || roles.includes(item.role));

  return (
    <ToastProvider>
      <RejectedArticlesProvider>
      <Box component="a" href="#main" sx={skipLink}>
        Aller au contenu
      </Box>
      <AppBar position="sticky" component="header">
        <Toolbar sx={{ gap: 2 }}>
          {mobile && (
            <IconButton
              color="inherit"
              edge="start"
              aria-label="Ouvrir le menu"
              aria-expanded={drawerOpen}
              aria-controls={drawerOpen ? "mobile-menu" : undefined}
              onClick={() => setDrawerOpen(true)}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Stack
            direction="row"
            component={Link}
            to="/"
            aria-label="Collector.shop, accueil"
            spacing={1}
            sx={{ alignItems: "center", color: "inherit", textDecoration: "none" }}
          >
            <Logo />
            <Typography variant="h6" component="span">
              Collector.shop
            </Typography>
          </Stack>
          {!mobile && (
            <Stack component="nav" direction="row" spacing={0.5} aria-label="Navigation principale">
              {items.map((item) => (
                <Button key={item.to} color="inherit" component={NavLink} to={item.to} end sx={navLink}>
                  {item.label}
                </Button>
              ))}
            </Stack>
          )}
          <Box sx={{ flexGrow: 1 }} />
          {!mobile && <AccountBlock />}
        </Toolbar>
      </AppBar>

      <Drawer anchor="left" open={mobile && drawerOpen} onClose={() => setDrawerOpen(false)} slotProps={{ paper: { id: "mobile-menu" } }}>
        <Box sx={{ width: 280, p: 2 }} role="presentation">
          <Typography variant="h6" component="p" sx={{ mb: 1 }}>
            Menu
          </Typography>
          <Box component="nav" aria-label="Navigation principale">
            <List>
              {items.map((item) => (
                <ListItemButton
                  key={item.to}
                  component={NavLink}
                  to={item.to}
                  end
                  onClick={() => setDrawerOpen(false)}
                  sx={{ borderRadius: 2, "&.active": { bgcolor: "action.selected" } }}
                >
                  <ListItemText primary={item.label} />
                </ListItemButton>
              ))}
            </List>
          </Box>
          <Divider sx={{ my: 1 }} />
          <AccountBlock inDrawer />
        </Box>
      </Drawer>

      <Container component="main" id="main" tabIndex={-1} sx={{ py: { xs: 3, md: 5 }, px: { xs: 2, sm: 3 } }}>
        <ErrorBoundary key={location.pathname}>
          <Suspense fallback={<LoadingSkeleton />}>
            <Outlet />
          </Suspense>
        </ErrorBoundary>
      </Container>
      </RejectedArticlesProvider>
    </ToastProvider>
  );
}

const navLink = {
  borderRadius: 2,
  "&.active": { bgcolor: "rgba(255,255,255,0.18)" },
};

const skipLink = {
  position: "absolute",
  left: 8,
  top: -48,
  zIndex: 2000,
  bgcolor: "background.paper",
  color: "primary.main",
  px: 2,
  py: 1,
  borderRadius: 1,
  "&:focus": { top: 8 },
};
