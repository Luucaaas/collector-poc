import { Alert, Stack } from "@mui/material";
import { PageHeader } from "../components/PageHeader";

export function NotFoundPage() {
  return (
    <Stack spacing={2}>
      <PageHeader title="Page introuvable" />
      <Alert severity="info">Cette adresse ne correspond à aucune page de l'application.</Alert>
    </Stack>
  );
}
