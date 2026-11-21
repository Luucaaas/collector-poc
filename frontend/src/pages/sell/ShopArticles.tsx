import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Link as MuiLink,
  Pagination,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useState, type FormEvent } from "react";
import { useAuth } from "react-oidc-context";
import { Link } from "react-router";
import type { Article, Page, PriceHistoryEntry, Shop } from "../../api/types";
import { useAction } from "../../api/useAction";
import { useApi } from "../../api/useApi";
import { useAsync } from "../../api/useAsync";
import { ArticlePrice } from "../../components/ArticlePrice";
import { EmptyState } from "../../components/EmptyState";
import { Tile } from "../../components/ItemCard";
import { LoadingSkeleton } from "../../components/LoadingSkeleton";
import { useRejectedArticles } from "../../components/RejectedArticles";
import { useToast } from "../../components/Toast";
import { formatDateTime, formatMoney } from "../../format";
import { validatePrice } from "../../money";
import { adviceForReason, shortReason } from "../../reasons";

export const ARTICLES_PAGE_SIZE = 10;

interface Props {
  shops: Shop[];
  version: number;
}

/** My articles, per shop: published ones with price change and history (US-04), rejected ones with their reasons. */
export function ShopArticles({ shops, version }: Props) {
  const { rejected } = useRejectedArticles();
  const api = useApi();
  const [shopId, setShopId] = useState(shops[0]?.id ?? "");
  const [page, setPage] = useState(1);
  const articles = useAsync(
    (signal) =>
      api.catalog<Page<Article>>(
        `/articles?shop_id=${encodeURIComponent(shopId)}&limit=${ARTICLES_PAGE_SIZE}&offset=${(page - 1) * ARTICLES_PAGE_SIZE}`,
        { signal },
      ),
    [api, shopId, page, version],
  );
  // Refused listings are not on the server list: shown once, above the first page only.
  const shopRejected = page === 1 ? rejected.filter((a) => a.shop_id === shopId) : [];

  return (
    <Stack spacing={2} component="section" aria-labelledby="my-articles-title">
      <Typography variant="h5" component="h2" id="my-articles-title">
        Mes articles
      </Typography>
      <TextField
        select
        label="Boutique des articles"
        value={shopId}
        onChange={(e) => {
          setShopId(e.target.value);
          setPage(1);
        }}
        slotProps={{ select: { native: true } }}
        sx={{ maxWidth: 320 }}
      >
        {shops.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </TextField>
      <Typography variant="body2" color="text.secondary">
        Les annonces refusées restent visibles ici jusqu'au rechargement de la page.
      </Typography>

      {articles.status === "loading" && <LoadingSkeleton label="Chargement des articles" />}
      {articles.status === "error" && <Alert severity="error">{articles.message}</Alert>}
      {articles.status === "success" && articles.data.items.length === 0 && shopRejected.length === 0 && (
        <EmptyState title="Aucun article dans cette boutique" description="Mettez un premier article en vente avec le formulaire ci-dessus." />
      )}
      {articles.status === "success" && (articles.data.items.length > 0 || shopRejected.length > 0) && (
        <>
          <Stack component="ul" spacing={2} sx={{ listStyle: "none", p: 0, m: 0 }} aria-label="Liste de mes articles">
            {shopRejected.map((article) => (
              <RejectedRow key={article.id} article={article} />
            ))}
            {articles.data.items.map((article) => (
              <ArticleRow key={article.id} initial={article} />
            ))}
          </Stack>
          {articles.data.total > ARTICLES_PAGE_SIZE && (
            <Pagination
              count={Math.ceil(articles.data.total / ARTICLES_PAGE_SIZE)}
              page={page}
              onChange={(_e, value) => setPage(value)}
              aria-label="Pagination de mes articles"
            />
          )}
        </>
      )}
    </Stack>
  );
}

function ArticleTitle({ article }: { article: Article }) {
  return (
    <Stack direction="row" spacing={2} sx={{ alignItems: "flex-start" }}>
      <Tile seed={article.title} />
      <Box sx={{ minWidth: 0 }}>
        <Typography variant="h6" component="h3" sx={{ overflowWrap: "anywhere" }}>
          <MuiLink component={Link} to={`/catalogue/${encodeURIComponent(article.id)}`} color="inherit" underline="hover">
            {article.title}
          </MuiLink>
        </Typography>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap", rowGap: 0.5 }}>
          <Chip
            size="small"
            variant="outlined"
            color={article.status === "PUBLISHED" ? "success" : "error"}
            label={article.status === "PUBLISHED" ? "Publié" : "Rejeté"}
          />
          <Typography variant="body2" color="text.secondary">
            {formatDateTime(article.created_at)}
          </Typography>
        </Stack>
      </Box>
    </Stack>
  );
}

function RejectedRow({ article }: { article: Article }) {
  return (
    <Card component="li" variant="outlined">
      <CardContent>
        <Stack spacing={1.5}>
          <ArticleTitle article={article} />
          <Typography>
            Motif{article.rejection_reasons.length > 1 ? "s" : ""} du rejet :{" "}
            {article.rejection_reasons.map(shortReason).join(", ")}.
          </Typography>
          {article.rejection_reasons.map((reason) => {
            const advice = adviceForReason(reason);
            return advice ? (
              <Typography key={reason} variant="body2" color="text.secondary">
                {advice}
              </Typography>
            ) : null;
          })}
        </Stack>
      </CardContent>
    </Card>
  );
}

// The article keeps its own state: after a price change, the row updates without reloading the list.
function ArticleRow({ initial }: { initial: Article }) {
  const api = useApi();
  const [article, setArticle] = useState(initial);
  const [newPrice, setNewPrice] = useState("");
  const [attempted, setAttempted] = useState(false);
  const toast = useToast();
  const [info, setInfo] = useState<{ severity: "success" | "info"; text: string } | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [historyVersion, setHistoryVersion] = useState(0);
  const action = useAction();
  // Live check: the message follows the typing; an empty field is only reported after a submit attempt.
  const parsed = validatePrice(newPrice);
  const localError = "error" in parsed && (attempted || newPrice.trim() !== "") ? parsed.error : null;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setInfo(null);
    setAttempted(true);
    if ("error" in parsed) return;
    if (parsed.value === article.price) {
      // RM-04: an identical price creates no history row or event; do not pretend a change happened.
      setInfo({ severity: "info", text: "Ce prix est identique au prix actuel : aucune modification n'a été enregistrée." });
      return;
    }
    const updated = await action.run(() =>
      api.catalog<Article>(`/articles/${article.id}/price`, { method: "PUT", body: { price: parsed.value } }),
      {
        conflict: "Cet article n'est plus publié : son prix ne peut pas être modifié.",
        onError: () => toast("Le prix n'a pas été modifié : voir le message sous le champ.", "error"),
      },
    );
    if (updated) {
      setInfo({ severity: "success", text: `Prix modifié : ${formatMoney(updated.price, updated.currency)}.` });
      toast(`Le prix de « ${updated.title} » est maintenant de ${formatMoney(updated.price, updated.currency)}.`, "success");
      setArticle(updated);
      setNewPrice("");
      setAttempted(false);
      setHistoryVersion((v) => v + 1);
    }
  }

  return (
    <Card component="li" variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <ArticleTitle article={article} />
          <ArticlePrice price={article.price} shippingFee={article.shipping_fee} currency={article.currency} />
          <Stack component="form" direction={{ xs: "column", sm: "row" }} spacing={2} onSubmit={submit} noValidate aria-label={`Modifier le prix de ${article.title}`}>
            <TextField
              size="small"
              label="Nouveau prix (€)"
              value={newPrice}
              onChange={(e) => setNewPrice(e.target.value)}
              error={!!localError}
              helperText={localError}
              slotProps={{ htmlInput: { inputMode: "decimal" } }}
            />
            <Button type="submit" variant="contained" disabled={action.pending} sx={{ alignSelf: "flex-start" }}>
              {action.pending ? "Envoi…" : "Modifier le prix"}
            </Button>
            <Button variant="outlined" onClick={() => setShowHistory((v) => !v)} sx={{ alignSelf: "flex-start" }}>
              {showHistory ? "Masquer l'historique" : "Historique des prix"}
            </Button>
          </Stack>
          {action.message && <Alert severity="error">{action.message}</Alert>}
          {info && <Alert severity={info.severity}>{info.text}</Alert>}
          {showHistory && <PriceHistory articleId={article.id} currency={article.currency} version={historyVersion} />}
        </Stack>
      </CardContent>
    </Card>
  );
}

function PriceHistory({ articleId, currency, version }: { articleId: string; currency: string; version: number }) {
  const api = useApi();
  const userId = useAuth().user?.profile?.sub;
  const history = useAsync(
    (signal) => api.catalog<Page<PriceHistoryEntry>>(`/articles/${articleId}/price-history`, { signal }),
    [api, articleId, version],
  );
  if (history.status === "loading") return <LoadingSkeleton label="Chargement de l'historique" />;
  if (history.status === "error") return <Alert severity="error">{history.message}</Alert>;
  if (history.data.items.length === 0) return <Alert severity="info">Aucun changement de prix pour cet article.</Alert>;
  return (
    <TableContainer>
      <Table size="small" aria-label="Historique des prix" sx={{ "& th, & td": { px: 1 } }}>
        <TableHead>
          <TableRow>
            <TableCell scope="col">Date</TableCell>
            <TableCell scope="col" align="right">
              Ancien prix
            </TableCell>
            <TableCell scope="col" align="right">
              Nouveau prix
            </TableCell>
            <TableCell scope="col" sx={{ display: { xs: "none", sm: "table-cell" } }}>
              Auteur
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {history.data.items.map((entry) => (
            <TableRow key={`${entry.changed_at}-${entry.new_price}`}>
              <TableCell sx={{ whiteSpace: "nowrap" }}>
                {formatDateTime(entry.changed_at)}
                {/* Narrow screens: the author moves under the date so the table never scrolls sideways. */}
                <Box component="span" sx={{ display: { xs: "block", sm: "none" }, color: "text.secondary", fontSize: "0.8rem" }}>
                  {authorLabel(entry.changed_by, userId)}
                </Box>
              </TableCell>
              <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                {formatMoney(entry.old_price, currency)}
              </TableCell>
              <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                {formatMoney(entry.new_price, currency)}
              </TableCell>
              <TableCell sx={{ whiteSpace: "nowrap", display: { xs: "none", sm: "table-cell" } }}>
                {authorLabel(entry.changed_by, userId)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

/** Author of a change: the contract only gives the `sub`; say "vous" or abbreviate the identifier. */
export function authorLabel(changedBy: string, userId: string | undefined): string {
  if (userId && changedBy === userId) return "par vous";
  return `par ${changedBy.slice(0, 8)}…`;
}
