import { Alert, Typography } from "@mui/material";

/** Emplacement des pages métier, réalisées dans la tâche suivante (P7-02). */
export function Placeholder({ title }: { title: string }) {
  return (
    <>
      <Typography variant="h4" component="h1" gutterBottom>
        {title}
      </Typography>
      <Alert severity="info">Cette page sera réalisée dans une prochaine étape.</Alert>
    </>
  );
}
