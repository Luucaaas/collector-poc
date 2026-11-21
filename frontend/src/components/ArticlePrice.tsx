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
  /** Missing or invalid fee (live preview): shown as "—" instead of a made-up amount. */
  shippingFee?: string;
  currency: string;
  large?: boolean;
}) {
  const free = shippingFee !== undefined && Number(shippingFee) === 0;
  return (
    <Stack direction="row" spacing={1.5} sx={{ alignItems: "baseline", flexWrap: "wrap" }}>
      <Typography
        component="span"
        sx={{ fontWeight: 700, fontSize: large ? "1.75rem" : "1.1rem", color: "primary.main" }}
      >
        {formatMoney(price, currency)}
      </Typography>
      <Typography component="span" variant="body2" color="text.secondary">
        {free ? "Livraison offerte" : `Frais de port : ${shippingFee === undefined ? "—" : formatMoney(shippingFee, currency)}`}
      </Typography>
    </Stack>
  );
}
