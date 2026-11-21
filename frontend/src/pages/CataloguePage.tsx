import { Alert, Box, Chip, Pagination, Skeleton, Stack, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { ArticlePrice } from "../components/ArticlePrice";
import { EmptyState } from "../components/EmptyState";
import { ItemCard } from "../components/ItemCard";
import { PageHeader } from "../components/PageHeader";
import { useApi } from "../api/useApi";
import { useAsync } from "../api/useAsync";
import { useShopNames } from "../api/useShopNames";
import type { Article, Category, Page } from "../api/types";

export const PAGE_SIZE = 12;

const GRID_SX = {
  listStyle: "none",
  p: 0,
  m: 0,
  display: "grid",
  gap: 2,
  gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" },
} as const;

function CardsSkeleton() {
  return (
    <Box role="status" aria-label="Chargement des articles" aria-busy="true" sx={GRID_SX}>
      {Array.from({ length: 6 }, (_, i) => (
        <Skeleton key={i} variant="rounded" height={132} />
      ))}
    </Box>
  );
}

/** Public catalogue: PUBLISHED articles as cards, category filter chips, limit / offset pagination. */
export function CataloguePage() {
  const api = useApi();
  const [categoryId, setCategoryId] = useState("");
  const [page, setPage] = useState(1);

  const categories = useAsync((signal) => api.catalog<Page<Category>>("/categories", { signal }), [api]);
  const articles = useAsync(
    (signal) => {
      const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String((page - 1) * PAGE_SIZE) });
      if (categoryId) params.set("category_id", categoryId);
      return api.catalog<Page<Article>>(`/articles?${params.toString()}`, { signal });
    },
    [api, categoryId, page],
  );

  const categoryItems = categories.status === "success" ? categories.data.items : [];
  const categoryName = (id: string) => categoryItems.find((c) => c.id === id)?.name ?? "Catégorie inconnue";
  const items = useMemo(() => (articles.status === "success" ? articles.data.items : []), [articles]);
  const shopNames = useShopNames(useMemo(() => items.map((a) => a.shop_id), [items]));

  const select = (id: string) => {
    setCategoryId(id);
    setPage(1);
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Catalogue" subtitle="Les objets de collection mis en vente par la communauté." />

      <Stack component="section" aria-label="Filtrer par catégorie" direction="row" useFlexGap sx={{ gap: 1, flexWrap: "wrap" }}>
        <Chip
          label="Toutes les catégories"
          color={categoryId === "" ? "primary" : "default"}
          variant={categoryId === "" ? "filled" : "outlined"}
          onClick={() => select("")}
          aria-pressed={categoryId === ""}
        />
        {categoryItems.map((category) => (
          <Chip
            key={category.id}
            label={category.name}
            color={categoryId === category.id ? "primary" : "default"}
            variant={categoryId === category.id ? "filled" : "outlined"}
            onClick={() => select(category.id)}
            aria-pressed={categoryId === category.id}
          />
        ))}
      </Stack>
      {categories.status === "error" && <Alert severity="warning">{categories.message}</Alert>}

      {articles.status === "loading" && <CardsSkeleton />}
      {articles.status === "error" && <Alert severity="error">{articles.message}</Alert>}
      {articles.status === "success" && items.length === 0 && (
        <EmptyState
          title="Aucun article à afficher pour le moment."
          description={
            categoryId ? "Aucun article dans cette catégorie : essayez-en une autre." : "Revenez bientôt, de nouvelles pièces arrivent."
          }
        />
      )}
      {articles.status === "success" && items.length > 0 && (
        <>
          <Box component="ul" sx={GRID_SX}>
            {items.map((article) => (
              <Box component="li" key={article.id} sx={{ display: "flex", "& > *": { flex: 1 } }}>
                <ItemCard title={article.title} to={`/catalogue/${encodeURIComponent(article.id)}`}>
                  <ArticlePrice price={article.price} shippingFee={article.shipping_fee} currency={article.currency} />
                  <Stack direction="row" useFlexGap sx={{ mt: 1, gap: 1, flexWrap: "wrap", alignItems: "center" }}>
                    <Chip size="small" label={categoryName(article.category_id)} />
                    <Typography variant="body2" color="text.secondary">
                      {shopNames[article.shop_id] ?? "Boutique"}
                    </Typography>
                  </Stack>
                </ItemCard>
              </Box>
            ))}
          </Box>
          {articles.data.total > PAGE_SIZE && (
            <Pagination
              count={Math.ceil(articles.data.total / PAGE_SIZE)}
              page={page}
              onChange={(_event, value) => setPage(value)}
              aria-label="Pagination du catalogue"
            />
          )}
        </>
      )}
    </Stack>
  );
}
