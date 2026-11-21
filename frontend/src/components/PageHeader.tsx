import { Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";
import { usePageTitle } from "../usePageTitle";

/** Page heading: the single `h1` of the page, plus the document title. */
export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  usePageTitle(title);
  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      spacing={2}
      sx={{ justifyContent: "space-between", alignItems: { xs: "flex-start", sm: "center" } }}
    >
      <div>
        <Typography variant="h4" component="h1">
          {title}
        </Typography>
        {subtitle && (
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            {subtitle}
          </Typography>
        )}
      </div>
      {actions}
    </Stack>
  );
}
