import { Alert, Button, CircularProgress, List, ListItem, ListItemText, Stack, TextField, Typography } from "@mui/material";
import { useState, type FormEvent } from "react";
import type { Category, Page } from "../api/types";
import { useAction } from "../api/useAction";
import { useApi } from "../api/useApi";
import { useAsync } from "../api/useAsync";

/** Page « Catégories » (admin, US-01) : liste et création. */
export function CategoriesPage() {
  const api = useApi();
  const [version, setVersion] = useState(0);
  const [name, setName] = useState("");
  const [created, setCreated] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const action = useAction();
  const categories = useAsync((signal) => api.catalog<Page<Category>>("/categories", { signal }), [api, version]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setCreated(null);
    if (name.trim().length < 2) {
      setLocalError("Le nom doit contenir entre 2 et 60 caractères.");
      return;
    }
    setLocalError(null);
    const category = await action.run(() => api.catalog<Category>("/categories", { method: "POST", body: { name } }));
    if (category) {
      setCreated(category.name);
      setName("");
      setVersion((v) => v + 1);
    }
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4" component="h1">
        Catégories
      </Typography>

      <Stack component="form" spacing={2} onSubmit={submit} sx={{ maxWidth: 420 }} aria-label="Créer une catégorie">
        <TextField
          label="Nom de la catégorie"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          error={!!localError || action.errorFields.includes("name")}
          helperText={localError ?? "Entre 2 et 60 caractères."}
          slotProps={{ htmlInput: { maxLength: 60 } }}
        />
        <Button type="submit" variant="contained" disabled={action.pending}>
          {action.pending ? "Création…" : "Créer la catégorie"}
        </Button>
        {action.message && <Alert severity="error">{action.message}</Alert>}
        {created && <Alert severity="success">Catégorie « {created} » créée.</Alert>}
      </Stack>

      <Typography variant="h5" component="h2">
        Catégories existantes
      </Typography>
      {categories.status === "loading" && <CircularProgress aria-label="Chargement des catégories" />}
      {categories.status === "error" && <Alert severity="error">{categories.message}</Alert>}
      {categories.status === "success" && categories.data.items.length === 0 && (
        <Alert severity="info">Aucune catégorie pour le moment.</Alert>
      )}
      {categories.status === "success" && categories.data.items.length > 0 && (
        <List aria-label="Liste des catégories" dense>
          {categories.data.items.map((c) => (
            <ListItem key={c.id} divider>
              <ListItemText primary={c.name} secondary={c.slug} />
            </ListItem>
          ))}
        </List>
      )}
    </Stack>
  );
}
