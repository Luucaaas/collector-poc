import { Box, Card, CardActionArea, CardContent, Typography } from "@mui/material";
import type { ReactNode } from "react";
import { Link } from "react-router";

const TILE_COLORS = ["#1f3a5f", "#7a3b00", "#1d5c4a", "#6b2d5c", "#3c4a8a", "#5a4a00"];

/** Stable colour for a given text: the same seed always gives the same tile. */
export function tileColor(seed: string): string {
  let hash = 0;
  for (const char of seed) hash = (hash * 31 + char.codePointAt(0)!) >>> 0;
  return TILE_COLORS[hash % TILE_COLORS.length]!;
}

export function initials(text: string): string {
  const words = text.trim().split(/\s+/).filter(Boolean);
  return words
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
}

/** Illustration generated locally (colour and initials), since the API stores no photo. */
export function Tile({ seed, size = 56 }: { seed: string; size?: number }) {
  return (
    <Box
      aria-hidden="true"
      sx={{
        width: size,
        height: size,
        borderRadius: 2,
        flexShrink: 0,
        display: "grid",
        placeItems: "center",
        bgcolor: tileColor(seed),
        color: "#fff",
        fontWeight: 700,
        fontSize: size / 2.6,
      }}
    >
      {initials(seed)}
    </Box>
  );
}

/** Reusable card: generated illustration, title, free content; the whole card links to `to` when given. */
export function ItemCard({
  title,
  seed,
  to,
  titleAs = "h2",
  children,
}: {
  title: string;
  seed?: string;
  to?: string;
  titleAs?: "h2" | "h3";
  children?: ReactNode;
}) {
  const content = (
    <CardContent sx={{ display: "flex", gap: 2, alignItems: "flex-start" }}>
      <Tile seed={seed ?? title} />
      <Box sx={{ minWidth: 0 }}>
        <Typography variant="h6" component={titleAs}>
          {title}
        </Typography>
        {children}
      </Box>
    </CardContent>
  );
  return (
    <Card>
      {to ? (
        <CardActionArea component={Link} to={to}>
          {content}
        </CardActionArea>
      ) : (
        content
      )}
    </Card>
  );
}
