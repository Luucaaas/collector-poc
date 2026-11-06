import { Alert, Button, CircularProgress, List, ListItem, ListItemText, Stack, TextField, Typography } from "@mui/material";
import { useState, type FormEvent } from "react";
import type { Category, Page, Shop } from "../api/types";
import { useAction } from "../api/useAction";
import { useApi } from "../api/useApi";
import { useAsync } from "../api/useAsync";
import { ArticleForm } from "./sell/ArticleForm";
import { ShopArticles } from "./sell/ShopArticles";

const SELLER_TYPES: Record<string, string> = { INDIVIDUAL: "Particulier" };

/** Page « Vendre » (seller, US-02 à US-04) : boutiques, mise en vente, mes articles et leur prix. */
export function SellPage() {
  const api = useApi();
  const [shopsVersion, setShopsVersion] = useState(0);
  const [articlesVersion, setArticlesVersion] = useState(0);
  const shops = useAsync((signal) => api.catalog<Page<Shop>>("/shops/me", { signal }), [api, shopsVersion]);
  const categories = useAsync((signal) => api.catalog<Page<Category>>("/categories", { signal }), [api]);

  return (
    <Stack spacing={4}>
      <Typography variant="h4" component="h1">
        Vendre
      </Typography>

      <Stack spacing={2} component="section" aria-labelledby="shops-title">
        <Typography variant="h5" component="h2" id="shops-title">
          Mes boutiques
        </Typography>
        {shops.status === "loading" && <CircularProgress aria-label="Chargement des boutiques" />}
        {shops.status === "error" && <Alert severity="error">{shops.message}</Alert>}
        {shops.status === "success" && shops.data.items.length === 0 && (
          <Alert severity="info">Vous n'avez pas encore de boutique : créez-en une pour mettre un article en vente.</Alert>
        )}
        {shops.status === "success" && shops.data.items.length > 0 && (
          <List aria-label="Liste de mes boutiques" dense>
            {shops.data.items.map((shop) => (
              <ListItem key={shop.id} divider>
                <ListItemText primary={shop.name} secondary={`${SELLER_TYPES[shop.seller_type] ?? shop.seller_type}${shop.description ? ` — ${shop.description}` : ""}`} />
              </ListItem>
            ))}
          </List>
        )}
        <ShopForm onCreated={() => setShopsVersion((v) => v + 1)} />
      </Stack>

      {shops.status === "success" && shops.data.items.length > 0 && (
        <>
          <ArticleForm
            shops={shops.data.items}
            categories={categories.status === "success" ? categories.data.items : []}
            categoriesError={categories.status === "error" ? categories.message : null}
            onPublished={() => setArticlesVersion((v) => v + 1)}
          />
          <ShopArticles shops={shops.data.items} version={articlesVersion} />
        </>
      )}
    </Stack>
  );
}

function ShopForm({ onCreated }: { onCreated: () => void }) {
  const api = useApi();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [created, setCreated] = useState<string | null>(null);
  const action = useAction();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setCreated(null);
    const body: { name: string; description?: string } = { name };
    if (description.trim() !== "") body.description = description;
    const shop = await action.run(() => api.catalog<Shop>("/shops", { method: "POST", body }));
    if (shop) {
      setCreated(shop.name);
      setName("");
      setDescription("");
      onCreated();
    }
  }

  return (
    <Stack component="form" spacing={2} onSubmit={submit} sx={{ maxWidth: 520 }} aria-label="Créer une boutique">
      <Typography variant="h6" component="h3">
        Créer une boutique
      </Typography>
      <TextField
        label="Nom de la boutique"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
        error={action.errorFields.includes("name")}
        helperText="Entre 3 et 60 caractères."
        slotProps={{ htmlInput: { maxLength: 60 } }}
      />
      <TextField
        label="Description de la boutique"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        multiline
        minRows={2}
        error={action.errorFields.includes("description")}
        helperText="Facultative. Sans adresse email ni numéro de téléphone."
        slotProps={{ htmlInput: { maxLength: 1000 } }}
      />
      <Button type="submit" variant="contained" disabled={action.pending || name.trim().length < 3}>
        {action.pending ? "Création…" : "Créer la boutique"}
      </Button>
      {action.message && <Alert severity="error">{action.message}</Alert>}
      {created && <Alert severity="success">Boutique « {created} » créée.</Alert>}
    </Stack>
  );
}
