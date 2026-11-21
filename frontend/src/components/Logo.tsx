import { Box } from "@mui/material";

/** Collector.shop logo: a stylised "C" token with a spark, drawn in SVG (no external file). */
export function Logo() {
  return (
    <Box
      component="svg"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      width={32}
      height={32}
      role="img"
      aria-label="Logo Collector.shop"
      sx={{ display: "block", flexShrink: 0 }}
    >
      <rect width="32" height="32" rx="9" fill="#f6f5f1" />
      <path
        d="M21.5 10.2A8 8 0 1 0 21.5 21.8"
        fill="none"
        stroke="#1f3a5f"
        strokeWidth="3.4"
        strokeLinecap="round"
      />
      <path d="M23.6 8.4l1 2.2 2.2 1-2.2 1-1 2.2-1-2.2-2.2-1 2.2-1z" fill="#c2610a" />
    </Box>
  );
}
