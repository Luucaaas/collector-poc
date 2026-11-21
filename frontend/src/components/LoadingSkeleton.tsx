import { Skeleton, Stack } from "@mui/material";

/** Placeholder shown while content loads (also the fallback of the lazy-loaded pages). */
export function LoadingSkeleton({ label = "Chargement" }: { label?: string }) {
  return (
    <Stack spacing={2} role="status" aria-label={label} aria-busy="true">
      <Skeleton variant="text" width="40%" height={44} />
      {Array.from({ length: 3 }, (_, i) => (
        <Skeleton key={i} variant="rounded" height={72} />
      ))}
    </Stack>
  );
}
