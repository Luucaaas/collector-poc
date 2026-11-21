import { Box, Card, CardContent, Chip, Stack, Typography } from "@mui/material";
import { ArticlePrice } from "./ArticlePrice";
import { Tile } from "./ItemCard";
import { normalizeAmount } from "../money";

interface Props {
  title: string;
  description: string;
  price: string;
  shippingFee: string;
  categoryName?: string;
  shopName?: string;
}

/** Preview of the listing as buyers will see it in the catalogue; empty fields show a placeholder. */
export function ArticlePreview({ title, description, price, shippingFee, categoryName, shopName }: Props) {
  const normalizedPrice = normalizeAmount(price);
  const normalizedFee = normalizeAmount(shippingFee);
  const shownTitle = title.trim();
  return (
    <Card component="section" aria-label="Aperçu de l'annonce">
      <CardContent>
        <Typography variant="overline" color="text.secondary" component="p">
          Aperçu de l'annonce
        </Typography>
        <Stack direction="row" spacing={2} sx={{ alignItems: "flex-start" }}>
          <Tile seed={shownTitle || "Article"} size={72} />
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="h6" component="p" sx={{ overflowWrap: "anywhere" }}>
              {shownTitle || "Titre de l'article"}
            </Typography>
            {normalizedPrice ? (
              <ArticlePrice price={normalizedPrice} shippingFee={normalizedFee ?? undefined} currency="EUR" />
            ) : (
              <Typography color="text.secondary">Prix à renseigner</Typography>
            )}
            <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: "wrap", rowGap: 1 }}>
              {categoryName && <Chip size="small" label={categoryName} />}
              {shopName && <Chip size="small" variant="outlined" label={shopName} />}
            </Stack>
          </Box>
        </Stack>
        <Typography
          color={description.trim() ? "text.primary" : "text.secondary"}
          sx={{ mt: 2, whiteSpace: "pre-line", overflowWrap: "anywhere" }}
        >
          {description.trim() || "La description de l'article apparaîtra ici."}
        </Typography>
      </CardContent>
    </Card>
  );
}
