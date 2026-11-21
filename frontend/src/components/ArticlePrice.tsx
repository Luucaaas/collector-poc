import { Stack, Typography } from "@mui/material";
import { formatMoney } from "../format";

/** Price and shipping fee in French euros; a zero fee reads "Livraison offerte". */
export function ArticlePrice({
  price,
  shippingFee,
  currency,
  large = false,
}: {
  price: string;
  shippingFee: string;
  currency: string;
  large?: boolean;
}) {
  const free = Number(shippingFee) === 0;
  return (
    <Stack direction="row" spacing={1.5} sx={{ alignItems: "baseline", flexWrap: "wrap" }}>
      <Typography
        component="span"
        sx={{ fontWeight: 700, fontSize: large ? "1.75rem" : "1.1rem", color: "primary.main" }}
      >
        {formatMoney(price, currency)}
      </Typography>
      <Typography component="span" variant="body2" color="text.secondary">
        {free ? "Livraison offerte" : `Frais de port : ${formatMoney(shippingFee, currency)}`}
      </Typography>
    </Stack>
  );
}
