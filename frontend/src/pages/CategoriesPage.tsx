import { Alert, Box, Button, Card, CardContent, Skeleton, Stack, TextField, Typography } from "@mui/material";
import { useState, type FormEvent } from "react";
import type { Category, Page } from "../api/types";
import { useAction } from "../api/useAction";
import { useApi } from "../api/useApi";
import { useAsync } from "../api/useAsync";
import { EmptyState } from "../components/EmptyState";
import { ItemCard } from "../components/ItemCard";
import { PageHeader } from "../components/PageHeader";
import { useToast } from "../components/Toast";
import { formatDateTime } from "../format";

const NAME_MIN = 2;
const NAME_MAX = 60;
const NAME_ERROR = `Le nom doit contenir entre ${NAME_MIN} et ${NAME_MAX} caractères.`;

const GRID_SX = {
  listStyle: "none",
  p: 0,
  m: 0,
  display: "grid",
  gap: 2,
  gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" },
} as const;

/** "Catégories" page (admin, US-01): creation with live checks, and the existing categories as cards. */
export function CategoriesPage() {
  const api = useApi();
  const toast = useToast();
  const [version, setVersion] = useState(0);
  const [name, setName] = useState("");
  const [touched, setTouched] = useState(false);
  const action = useAction();
  const categories = useAsync((signal) => api.catalog<Page<Category>>("/categories", { signal }), [api, version]);

  const length = name.trim().length;
  const invalid = length < NAME_MIN || length > NAME_MAX;
  const existing = categories.status === "success" ? categories.data.items : [];
  // Heads-up only: the API (409) has the last word on uniqueness.
  const duplicate = existing.some((c) => c.name.trim().toLowerCase() === name.trim().toLowerCase()) && length > 0;
  const showError = touched && invalid;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setTouched(true);
    if (invalid) return;
    const category = await action.run(() => api.catalog<Category>("/categories", { method: "POST", body: { name } }));
    if (category) {
      toast(`Catégorie « ${category.name} » créée.`, "success");
      setName("");
      setTouched(false);
      setVersion((v) => v + 1);
    }
  }

  const helper = showError
    ? NAME_ERROR
    : duplicate
      ? "Une catégorie porte déjà ce nom : l'enregistrement sera refusé."
      : `Entre ${NAME_MIN} et ${NAME_MAX} caractères (${name.length}/${NAME_MAX}).`;

  return (
    <Stack spacing={4}>
      <PageHeader
        title="Catégories"
        subtitle="Les catégories classent les articles et servent aux acheteurs à suivre ce qui les intéresse."
      />

      <Card component="section" aria-labelledby="new-category-title">
        <CardContent>
          <Stack component="form" spacing={2} onSubmit={submit} noValidate aria-labelledby="new-category-title" sx={{ maxWidth: 480 }}>
            <Typography variant="h5" component="h2" id="new-category-title">
              Créer une catégorie
            </Typography>
            <TextField
              label="Nom de la catégorie"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onBlur={() => name !== "" && setTouched(true)}
              required
              error={showError || action.errorFields.includes("name")}
              helperText={helper}
              slotProps={{ htmlInput: { maxLength: NAME_MAX } }}
            />
            <Button type="submit" variant="contained" disabled={action.pending} sx={{ alignSelf: "flex-start" }}>
              {action.pending ? "Création…" : "Créer la catégorie"}
            </Button>
            {action.message && <Alert severity="error">{action.message}</Alert>}
          </Stack>
        </CardContent>
      </Card>

      <Stack spacing={2} component="section" aria-labelledby="categories-title">
        <Typography variant="h5" component="h2" id="categories-title">
          Catégories existantes{categories.status === "success" ? ` (${categories.data.total})` : ""}
        </Typography>
        {categories.status === "loading" && (
          <Box role="status" aria-label="Chargement des catégories" aria-busy="true" sx={GRID_SX}>
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} variant="rounded" height={92} />
            ))}
          </Box>
        )}
        {categories.status === "error" && <Alert severity="error">{categories.message}</Alert>}
        {categories.status === "success" && categories.data.items.length === 0 && (
          <EmptyState
            title="Aucune catégorie pour le moment."
            description="Créez la première avec le formulaire ci-dessus : les acheteurs pourront alors la suivre."
          />
        )}
        {categories.status === "success" && categories.data.items.length > 0 && (
          <Box component="ul" aria-label="Liste des catégories" sx={GRID_SX}>
            {categories.data.items.map((c) => (
              <Box component="li" key={c.id} sx={{ display: "flex", "& > *": { flex: 1 } }}>
                <ItemCard title={c.name} titleAs="h3">
                  <Typography variant="body2" color="text.secondary">
                    {c.slug}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Créée le {formatDateTime(c.created_at)}
                  </Typography>
                </ItemCard>
              </Box>
            ))}
          </Box>
        )}
      </Stack>
    </Stack>
  );
}
