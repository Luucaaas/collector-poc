import { Alert, AlertTitle, Box } from "@mui/material";
import { adviceForReason, describeReason } from "../reasons";

/**
 * Explains a rejection by the automatic check: each reason in French, with what to do about it.
 * `title` is the article title, shown so the seller knows which listing is concerned.
 */
export function RejectionNotice({ title, reasons }: { title: string; reasons: string[] }) {
  return (
    <Alert severity="warning">
      <AlertTitle>Article rejeté par le contrôle automatique</AlertTitle>
      « {title} » n'a pas été publié, car :
      <Box component="ul" sx={{ my: 0.5, pl: 3 }}>
        {reasons.map((reason) => (
          <li key={reason}>
            <span>{describeReason(reason)}</span>
            {adviceForReason(reason) && (
              <Box component="span" sx={{ display: "block", fontSize: "0.875rem" }}>
                {adviceForReason(reason)}
              </Box>
            )}
          </li>
        ))}
      </Box>
      Corrigez le texte puis mettez l'article en vente à nouveau.
    </Alert>
  );
}
