import { Alert, Box, Button, Stack, TextField, Typography } from "@mui/material";
import { useState, type FormEvent } from "react";
import type { Article, Category, Page, Shop } from "../api/types";
import { useAction } from "../api/useAction";
import { useApi } from "../api/useApi";
import { useAsync } from "../api/useAsync";
import { detectContact } from "../contact";
import { EmptyState } from "../components/EmptyState";
import { ItemCard } from "../components/ItemCard";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { PageHeader } from "../components/PageHeader";
import { useRejectedArticles } from "../components/RejectedArticles";
import { useToast } from "../components/Toast";
import { ArticleForm } from "./sell/ArticleForm";
import { ShopArticles } from "./sell/ShopArticles";

const SELLER_TYPES: Record<string, string> = { INDIVIDUAL: "Particulier" };
const SHOP_NAME_MIN = 3;
const SHOP_NAME_MAX = 60;
const SHOP_DESCRIPTION_MAX = 1000;

/** "Vendre" page (seller, US-02 to US-04): shops, listing, my articles and their price. */
export function SellPage() {
  const api = useApi();
  const [shopsVersion, setShopsVersion] = useState(0);
  const [articlesVersion, setArticlesVersion] = useState(0);
  const { add: addRejected } = useRejectedArticles();
  const shops = useAsync((signal) => api.catalog<Page<Shop>>("/shops/me", { signal }), [api, shopsVersion]);
  const categories = useAsync((signal) => api.catalog<Page<Category>>("/categories", { signal }), [api]);

  function onSubmitted(article: Article) {
    if (article.status === "PUBLISHED") setArticlesVersion((v) => v + 1);
    else addRejected(article);
  }

  return (
    <Stack spacing={5}>
      <PageHeader
        title="Vendre"
        subtitle="Gérez vos boutiques, mettez des articles en vente et suivez leur prix. Chaque annonce passe un contrôle automatique."
      />

      <Stack spacing={2} component="section" aria-labelledby="shops-title">
        <Typography variant="h5" component="h2" id="shops-title">
          Mes boutiques
        </Typography>
        {shops.status === "loading" && <LoadingSkeleton label="Chargement des boutiques" />}
        {shops.status === "error" && <Alert severity="error">{shops.message}</Alert>}
        {shops.status === "success" && shops.data.items.length === 0 && (
          <EmptyState
            title="Vous n'avez pas encore de boutique"
            description="Créez-en une ci-dessous pour mettre un article en vente."
          />
        )}
        {shops.status === "success" && shops.data.items.length > 0 && (
          <Box
            component="ul"
            aria-label="Liste de mes boutiques"
            sx={{
              listStyle: "none",
              p: 0,
              m: 0,
              display: "grid",
              gap: 2,
              gridTemplateColumns: { xs: "minmax(0, 1fr)", sm: "repeat(2, minmax(0, 1fr))", md: "repeat(3, minmax(0, 1fr))" },
            }}
          >
            {shops.data.items.map((shop) => (
              <li key={shop.id}>
                <ItemCard title={shop.name} titleAs="h3">
                  <Typography variant="body2" color="text.secondary">
                    {SELLER_TYPES[shop.seller_type] ?? shop.seller_type}
                  </Typography>
                  {shop.description && (
                    <Typography variant="body2" sx={{ mt: 0.5, overflowWrap: "anywhere" }}>
                      {shop.description}
                    </Typography>
                  )}
                </ItemCard>
              </li>
            ))}
          </Box>
        )}
        <ShopForm onCreated={() => setShopsVersion((v) => v + 1)} />
      </Stack>

      {shops.status === "success" && shops.data.items.length > 0 && (
        <>
          <ArticleForm
            shops={shops.data.items}
            categories={categories.status === "success" ? categories.data.items : []}
            categoriesError={categories.status === "error" ? categories.message : null}
            onSubmitted={onSubmitted}
          />
          <ShopArticles shops={shops.data.items} version={articlesVersion} />
        </>
      )}
    </Stack>
  );
}

function ShopForm({ onCreated }: { onCreated: () => void }) {
  const api = useApi();
  const toast = useToast();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [nameTouched, setNameTouched] = useState(false);
  const [created, setCreated] = useState<string | null>(null);
  const action = useAction();

  const nameError = name.trim().length < SHOP_NAME_MIN ? `Le nom doit contenir au moins ${SHOP_NAME_MIN} caractères.` : null;
  const contact = detectContact(name, description);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setCreated(null);
    setNameTouched(true);
    if (nameError) return;
    const body: { name: string; description?: string } = { name };
    if (description.trim() !== "") body.description = description;
    const shop = await action.run(() => api.catalog<Shop>("/shops", { method: "POST", body }), {
      onError: () => toast("La boutique n'a pas été créée : voir le message sous le formulaire.", "error"),
    });
    if (shop) {
      setCreated(shop.name);
      toast("Votre boutique est créée : vous pouvez y mettre des articles en vente.", "success");
      setName("");
      setDescription("");
      setNameTouched(false);
      onCreated();
    }
  }

  return (
    <Stack component="form" spacing={2} onSubmit={submit} noValidate sx={{ maxWidth: 520 }} aria-label="Créer une boutique">
      <Typography variant="h6" component="h3">
        Créer une boutique
      </Typography>
      <TextField
        label="Nom de la boutique"
        value={name}
        onChange={(e) => setName(e.target.value)}
        onBlur={() => setNameTouched(true)}
        required
        error={(nameTouched && !!nameError) || action.errorFields.includes("name")}
        helperText={(nameTouched && nameError) || `Entre ${SHOP_NAME_MIN} et ${SHOP_NAME_MAX} caractères (${name.length}/${SHOP_NAME_MAX}).`}
        slotProps={{ htmlInput: { maxLength: SHOP_NAME_MAX } }}
      />
      <TextField
        label="Description de la boutique"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        multiline
        minRows={2}
        error={action.errorFields.includes("description")}
        helperText={`Facultative (${description.length}/${SHOP_DESCRIPTION_MAX}). Sans adresse email ni numéro de téléphone.`}
        slotProps={{ htmlInput: { maxLength: SHOP_DESCRIPTION_MAX } }}
      />
      {contact.length > 0 && (
        <Alert severity="warning" role="status">
          Le nom ou la description semble contenir des coordonnées : la boutique serait refusée. Retirez l'adresse email ou le
          numéro de téléphone.
        </Alert>
      )}
      <Button type="submit" variant="contained" disabled={action.pending}>
        {action.pending ? "Création…" : "Créer la boutique"}
      </Button>
      {action.message && <Alert severity="error">{action.message}</Alert>}
      {created && <Alert severity="success">Boutique « {created} » créée.</Alert>}
    </Stack>
  );
}
