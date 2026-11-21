import { Box, Button, Stack, Typography } from "@mui/material";
import { useAuth } from "react-oidc-context";
import { Link } from "react-router";
import { getRoles } from "../auth/roles";
import { ItemCard } from "../components/ItemCard";
import { usePageTitle } from "../usePageTitle";

/** Landing page: what Collector.shop does and where to go next, depending on the roles. */
export function HomePage() {
  usePageTitle("Accueil");
  const auth = useAuth();
  const roles = getRoles(auth.user);

  return (
    <Stack spacing={5}>
      <Box sx={{ py: { xs: 2, md: 5 } }}>
        <Typography variant="h3" component="h1" sx={{ fontSize: { xs: "2rem", md: "3rem" } }}>
          Collector.shop
        </Typography>
        <Typography variant="h6" component="p" color="text.secondary" sx={{ mt: 2, maxWidth: 640, fontWeight: 400 }}>
          La place de marché des objets de collection entre particuliers : publiez vos pièces, suivez les catégories qui
          vous passionnent et soyez prévenu dès qu'un article correspond.
        </Typography>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mt: 3 }}>
          <Button variant="contained" size="large" component={Link} to="/catalogue">
            Parcourir le catalogue
          </Button>
          {roles.includes("seller") && (
            <Button variant="outlined" size="large" component={Link} to="/vendre">
              Mettre un article en vente
            </Button>
          )}
          {roles.includes("buyer") && (
            <Button variant="outlined" size="large" component={Link} to="/centres-interet">
              Mes centres d'intérêt
            </Button>
          )}
        </Stack>
      </Box>

      <Box
        component="ul"
        sx={{ listStyle: "none", p: 0, m: 0, display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(3, 1fr)" } }}
      >
        <Box component="li">
          <ItemCard title="Vendez en confiance" seed="Vendre">
            <Typography color="text.secondary">
              Chaque annonce est contrôlée automatiquement : pas de coordonnées dans le texte, un prix valide.
            </Typography>
          </ItemCard>
        </Box>
        <Box component="li">
          <ItemCard title="Suivez vos passions" seed="Suivre">
            <Typography color="text.secondary">
              Choisissez vos catégories et vos préférences pour ne rien manquer.
            </Typography>
          </ItemCard>
        </Box>
        <Box component="li">
          <ItemCard title="Soyez prévenu" seed="Notifier">
            <Typography color="text.secondary">
              Nouveaux articles et baisses de prix arrivent dans vos notifications.
            </Typography>
          </ItemCard>
        </Box>
      </Box>
    </Stack>
  );
}
