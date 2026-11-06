import {
  Alert,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Pagination,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useApi } from "../api/useApi";
import { useAsync } from "../api/useAsync";
import type { Article, Category, Page } from "../api/types";
import { formatMoney } from "../format";

export const PAGE_SIZE = 12;

/** Catalogue public : articles PUBLISHED, filtre par catégorie, pagination limit / offset. */
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

  return (
    <Stack spacing={3}>
      <Typography variant="h4" component="h1">
        Catalogue
      </Typography>

      <FormControl sx={{ maxWidth: 320 }}>
        <InputLabel id="category-filter-label">Catégorie</InputLabel>
        <Select
          labelId="category-filter-label"
          label="Catégorie"
          value={categoryId}
          onChange={(event) => {
            setCategoryId(event.target.value);
            setPage(1);
          }}
        >
          <MenuItem value="">Toutes les catégories</MenuItem>
          {categoryItems.map((category) => (
            <MenuItem key={category.id} value={category.id}>
              {category.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      {categories.status === "error" && <Alert severity="warning">{categories.message}</Alert>}

      {articles.status === "loading" && <CircularProgress aria-label="Chargement des articles" />}
      {articles.status === "error" && <Alert severity="error">{articles.message}</Alert>}
      {articles.status === "success" && articles.data.items.length === 0 && (
        <Alert severity="info">Aucun article à afficher pour le moment.</Alert>
      )}
      {articles.status === "success" && articles.data.items.length > 0 && (
        <>
          <Stack component="ul" spacing={2} sx={{ listStyle: "none", p: 0, m: 0 }}>
            {articles.data.items.map((article) => (
              <Card component="li" key={article.id} variant="outlined">
                <CardContent>
                  <Typography variant="h6" component="h2">
                    {article.title}
                  </Typography>
                  <Stack direction="row" spacing={2} sx={{ mt: 1, alignItems: "center" }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
                      {formatMoney(article.price, article.currency)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Frais de port : {formatMoney(article.shipping_fee, article.currency)}
                    </Typography>
                    <Chip size="small" label={categoryName(article.category_id)} />
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
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
