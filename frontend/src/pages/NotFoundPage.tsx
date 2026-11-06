import { Alert, Typography } from "@mui/material";

export function NotFoundPage() {
  return (
    <>
      <Typography variant="h4" component="h1" gutterBottom>
        Page introuvable
      </Typography>
      <Alert severity="info">Cette adresse ne correspond à aucune page de l'application.</Alert>
    </>
  );
}
