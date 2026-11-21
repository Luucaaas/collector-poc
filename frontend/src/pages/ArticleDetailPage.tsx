import { Alert, Box, Button, Chip, Divider, Skeleton, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import { useAuth } from "react-oidc-context";
import { Link, useParams } from "react-router";
import type { Article, Category, Page, PriceHistoryEntry, Shop } from "../api/types";
import { useApi } from "../api/useApi";
import { useAsync } from "../api/useAsync";
import { getRoles } from "../auth/roles";
import { ArticlePrice } from "../components/ArticlePrice";
import { Tile } from "../components/ItemCard";
import { PageHeader } from "../components/PageHeader";
import { formatDateTime, formatMoney } from "../format";
import { describeReason } from "../reasons";

const BackLink = () => (
  <Button component={Link} to="/catalogue" sx={{ alignSelf: "flex-start" }}>
    ← Retour au catalogue
  </Button>
);

function DetailSkeleton() {
  return (
    <Stack spacing={2} role="status" aria-label="Chargement de l'article" aria-busy="true">
      <Skeleton variant="text" width="50%" height={44} />
      <Skeleton variant="rounded" height={160} />
      <Skeleton variant="rounded" height={96} />
    </Stack>
  );
}

/** Price history table: only fetched for the owner or an admin (the API refuses anyone else). */
function PriceHistory({ article }: { article: Article }) {
  const api = useApi();
  const history = useAsync(
    (signal) => api.catalog<Page<PriceHistoryEntry>>(`/articles/${encodeURIComponent(article.id)}/price-history`, { signal }),
    [api, article.id],
  );
  return (
    <Stack component="section" aria-labelledby="history-title" spacing={1}>
      <Typography variant="h5" component="h2" id="history-title">
        Historique des prix
      </Typography>
      {history.status === "loading" && <Skeleton variant="rounded" height={72} role="status" aria-label="Chargement de l'historique" />}
      {history.status === "error" && <Alert severity="error">{history.message}</Alert>}
      {history.status === "success" && history.data.items.length === 0 && (
        <Typography color="text.secondary">Le prix n'a jamais été modifié.</Typography>
      )}
      {history.status === "success" && history.data.items.length > 0 && (
        <Box sx={{ overflowX: "auto" }}>
          <Table size="small" aria-label="Historique des prix">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Ancien prix</TableCell>
                <TableCell>Nouveau prix</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {history.data.items.map((entry) => (
                <TableRow key={`${entry.changed_at}-${entry.new_price}`}>
                  <TableCell>{formatDateTime(entry.changed_at)}</TableCell>
                  <TableCell>{formatMoney(entry.old_price, article.currency)}</TableCell>
                  <TableCell>{formatMoney(entry.new_price, article.currency)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      )}
    </Stack>
  );
}

function ArticleDetail({ article }: { article: Article }) {
  const api = useApi();
  const auth = useAuth();
  const categories = useAsync((signal) => api.catalog<Page<Category>>("/categories", { signal }), [api]);
  const shop = useAsync((signal) => api.catalog<Shop>(`/shops/${encodeURIComponent(article.shop_id)}`, { signal }), [api, article.shop_id]);

  const categoryName =
    categories.status === "success" ? (categories.data.items.find((c) => c.id === article.category_id)?.name ?? "Catégorie inconnue") : "…";
  const canSeeHistory = auth.user?.profile.sub === article.seller_id || getRoles(auth.user).includes("admin");

  return (
    <Stack spacing={3}>
      <BackLink />
      <PageHeader title={article.title} />
      <Stack direction={{ xs: "column", sm: "row" }} spacing={3} sx={{ alignItems: { xs: "flex-start", sm: "center" } }}>
        <Tile seed={article.title} size={120} />
        <Stack spacing={1.5}>
          <ArticlePrice price={article.price} shippingFee={article.shipping_fee} currency={article.currency} large />
          <Stack direction="row" useFlexGap sx={{ gap: 1, flexWrap: "wrap", alignItems: "center" }}>
            <Chip size="small" label={categoryName} />
            {article.status === "REJECTED" && <Chip size="small" color="error" label="Rejeté par le contrôle automatique" />}
            <Typography variant="body2" color="text.secondary">
              {shop.status === "success" ? `Boutique : ${shop.data.name}` : "Boutique"} · mis en vente le {formatDateTime(article.created_at)}
            </Typography>
          </Stack>
        </Stack>
      </Stack>
      {article.status === "REJECTED" && article.rejection_reasons.length > 0 && (
        <Alert severity="error">
          Motifs du rejet : {article.rejection_reasons.map(describeReason).join(", ")}.
        </Alert>
      )}
      <Divider />
      <Stack component="section" aria-labelledby="description-title" spacing={1}>
        <Typography variant="h5" component="h2" id="description-title">
          Description
        </Typography>
        <Typography sx={{ whiteSpace: "pre-line", overflowWrap: "anywhere" }}>{article.description}</Typography>
      </Stack>
      {canSeeHistory && <PriceHistory article={article} />}
    </Stack>
  );
}

/** Article detail page (`/catalogue/:articleId`): public for a PUBLISHED article. */
export function ArticleDetailPage() {
  const { articleId = "" } = useParams();
  const api = useApi();
  const article = useAsync(
    (signal) => api.catalog<Article>(`/articles/${encodeURIComponent(articleId)}`, { signal }),
    [api, articleId],
  );
  if (article.status === "loading") return <DetailSkeleton />;
  if (article.status === "error") {
    return (
      <Stack spacing={3}>
        <BackLink />
        <PageHeader title="Article indisponible" />
        <Alert severity="error">{article.message}</Alert>
      </Stack>
    );
  }
  return <ArticleDetail article={article.data} />;
}
