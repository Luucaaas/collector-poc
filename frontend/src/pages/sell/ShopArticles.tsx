import {
  Alert,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Pagination,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState, type FormEvent } from "react";
import { useAuth } from "react-oidc-context";
import type { Article, Page, PriceHistoryEntry, Shop } from "../../api/types";
import { useAction } from "../../api/useAction";
import { useApi } from "../../api/useApi";
import { useAsync } from "../../api/useAsync";
import { formatDateTime, formatMoney } from "../../format";
import { validatePrice } from "../../money";

export const ARTICLES_PAGE_SIZE = 10;

/** Mes articles publiés, par boutique, avec modification du prix et historique (US-04). */
export function ShopArticles({ shops, version }: { shops: Shop[]; version: number }) {
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

  return (
    <Stack spacing={2} component="section" aria-labelledby="my-articles-title">
      <Typography variant="h5" component="h2" id="my-articles-title">
        Mes articles publiés
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
        Les articles rejetés par le contrôle automatique ne sont affichés qu'au moment de leur création.
      </Typography>

      {articles.status === "loading" && <CircularProgress aria-label="Chargement des articles" />}
      {articles.status === "error" && <Alert severity="error">{articles.message}</Alert>}
      {articles.status === "success" && articles.data.items.length === 0 && (
        <Alert severity="info">Aucun article publié dans cette boutique.</Alert>
      )}
      {articles.status === "success" && articles.data.items.length > 0 && (
        <>
          <Stack component="ul" spacing={2} sx={{ listStyle: "none", p: 0, m: 0 }} aria-label="Liste de mes articles">
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

// L'article garde son propre état : après un changement de prix, la ligne se met à jour sans recharger la liste.
function ArticleRow({ initial }: { initial: Article }) {
  const api = useApi();
  const [article, setArticle] = useState(initial);
  const [newPrice, setNewPrice] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [info, setInfo] = useState<{ severity: "success" | "info"; text: string } | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [historyVersion, setHistoryVersion] = useState(0);
  const action = useAction();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setInfo(null);
    const parsed = validatePrice(newPrice);
    if ("error" in parsed) {
      setLocalError(parsed.error);
      return;
    }
    setLocalError(null);
    if (parsed.value === article.price) {
      // RM-04 : un prix identique ne crée ni ligne d'historique ni événement ; on ne fait pas croire à un changement.
      setInfo({ severity: "info", text: "Ce prix est identique au prix actuel : aucune modification n'a été enregistrée." });
      return;
    }
    const updated = await action.run(() =>
      api.catalog<Article>(`/articles/${article.id}/price`, { method: "PUT", body: { price: parsed.value } }),
      { conflict: "Cet article n'est plus publié : son prix ne peut pas être modifié." },
    );
    if (updated) {
      setInfo({ severity: "success", text: `Prix modifié : ${formatMoney(updated.price, updated.currency)}.` });
      setArticle(updated);
      setNewPrice("");
      setHistoryVersion((v) => v + 1);
    }
  }

  return (
    <Card component="li" variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6" component="h3">
            {article.title}
          </Typography>
          <Typography>
            Prix actuel : <strong>{formatMoney(article.price, article.currency)}</strong>
          </Typography>
          <Stack component="form" direction="row" spacing={2} onSubmit={submit} noValidate aria-label={`Modifier le prix de ${article.title}`}>
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
  if (history.status === "loading") return <CircularProgress aria-label="Chargement de l'historique" />;
  if (history.status === "error") return <Alert severity="error">{history.message}</Alert>;
  if (history.data.items.length === 0) return <Alert severity="info">Aucun changement de prix pour cet article.</Alert>;
  return (
    <table aria-label="Historique des prix">
      <thead>
        <tr>
          <th scope="col">Date</th>
          <th scope="col">Ancien prix</th>
          <th scope="col">Nouveau prix</th>
          <th scope="col">Auteur</th>
        </tr>
      </thead>
      <tbody>
        {history.data.items.map((entry) => (
          <tr key={`${entry.changed_at}-${entry.new_price}`}>
            <td>{formatDateTime(entry.changed_at)}</td>
            <td>{formatMoney(entry.old_price, currency)}</td>
            <td>{formatMoney(entry.new_price, currency)}</td>
            <td>{authorLabel(entry.changed_by, userId)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Auteur d'un changement : le contrat ne donne que le `sub` ; on dit « vous » ou on abrège l'identifiant. */
export function authorLabel(changedBy: string, userId: string | undefined): string {
  if (userId && changedBy === userId) return "par vous";
  return `par ${changedBy.slice(0, 8)}…`;
}
