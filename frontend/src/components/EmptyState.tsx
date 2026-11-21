import { Box, Typography } from "@mui/material";
import type { ReactNode } from "react";

/** Friendly placeholder when a list has nothing to show; `action` is an optional call to action. */
export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <Box
      sx={{
        textAlign: "center",
        py: 6,
        px: 2,
        border: "1px dashed",
        borderColor: "divider",
        borderRadius: 3,
        bgcolor: "background.paper",
      }}
    >
      <Typography variant="h6" component="p">
        {title}
      </Typography>
      {description && (
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          {description}
        </Typography>
      )}
      {action && <Box sx={{ mt: 2 }}>{action}</Box>}
    </Box>
  );
}
