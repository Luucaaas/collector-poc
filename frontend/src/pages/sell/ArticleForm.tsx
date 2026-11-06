import { Alert, AlertTitle, Button, Stack, TextField, Typography } from "@mui/material";
import { useState, type FormEvent } from "react";
import type { Article, ArticleCreateBody, Category, Shop } from "../../api/types";
import { useAction } from "../../api/useAction";
import { useApi } from "../../api/useApi";
import { validateFee, validatePrice } from "../../money";
import { describeReason } from "../../reasons";

interface Props {
  shops: Shop[];
  categories: Category[];
  categoriesError: string | null;
  onPublished: () => void;
}

/**
 * Mise en vente (US-03). Trois issues bien distinctes : article publié (201 PUBLISHED), article rejeté
 * par le contrôle automatique (201 REJECTED, avec motifs) et requête mal formée (422, erreur de saisie).
 */
export function ArticleForm({ shops, categories, categoriesError, onPublished }: Props) {
  const api = useApi();
  const [shopId, setShopId] = useState(shops[0]?.id ?? "");
  const [categoryId, setCategoryId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [price, setPrice] = useState("");
  const [fee, setFee] = useState("0.00");
  const [localErrors, setLocalErrors] = useState<Record<string, string>>({});
  const [result, setResult] = useState<Article | null>(null);
  const action = useAction();

  function validate(): ArticleCreateBody | null {
    const errors: Record<string, string> = {};
    if (!shopId) errors.shop = "Choisissez une boutique.";
    if (!categoryId) errors.category = "Choisissez une catégorie.";
    if (title.trim().length < 5) errors.title = "Le titre doit contenir au moins 5 caractères.";
    if (description.trim().length < 20) errors.description = "La description doit contenir au moins 20 caractères.";
    if (!/^https:\/\/[^\s/]+(\/\S*)?$/.test(photoUrl.trim())) errors.photo = "Saisissez une adresse de photo en https://.";
    const p = validatePrice(price);
    if ("error" in p) errors.price = p.error;
    const f = validateFee(fee);
    if ("error" in f) errors.fee = f.error;
    setLocalErrors(errors);
    if (Object.keys(errors).length > 0 || !("value" in p) || !("value" in f)) return null;
    return {
      shop_id: shopId,
      category_id: categoryId,
      title: title.trim(),
      description: description.trim(),
      photo_urls: [photoUrl.trim()],
      price: p.value,
      shipping_fee: f.value,
      currency: "EUR",
    };
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setResult(null);
    const body = validate();
    if (!body) return;
    const article = await action.run(() => api.catalog<Article>("/articles", { method: "POST", body }));
    if (article) {
      setResult(article);
      if (article.status === "PUBLISHED") {
        setTitle("");
        setDescription("");
        setPhotoUrl("");
        setPrice("");
        onPublished();
      }
    }
  }

  const invalid = (field: string) => action.errorFields.includes(field);

  return (
    <Stack component="form" spacing={2} onSubmit={submit} noValidate sx={{ maxWidth: 620 }} aria-label="Mettre un article en vente">
      <Typography variant="h5" component="h2">
        Mettre un article en vente
      </Typography>
      {categoriesError && <Alert severity="warning">{categoriesError}</Alert>}
      <TextField
        select
        label="Boutique"
        value={shopId}
        onChange={(e) => setShopId(e.target.value)}
        slotProps={{ select: { native: true } }}
        error={!!localErrors.shop || invalid("shop_id")}
        helperText={localErrors.shop}
      >
        {shops.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </TextField>
      <TextField
        select
        label="Catégorie"
        value={categoryId}
        onChange={(e) => setCategoryId(e.target.value)}
        slotProps={{ select: { native: true } }}
        error={!!localErrors.category || invalid("category_id")}
        helperText={localErrors.category}
      >
        <option value="">— Choisir —</option>
        {categories.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </TextField>
      <TextField
        label="Titre de l'article"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
        error={!!localErrors.title || invalid("title")}
        helperText={localErrors.title ?? "Entre 5 et 120 caractères."}
        slotProps={{ htmlInput: { maxLength: 120 } }}
      />
      <TextField
        label="Description de l'article"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        required
        multiline
        minRows={3}
        error={!!localErrors.description || invalid("description")}
        helperText={localErrors.description ?? "Au moins 20 caractères. Sans adresse email ni numéro de téléphone."}
        slotProps={{ htmlInput: { maxLength: 5000 } }}
      />
      <TextField
        label="Adresse de la photo (https)"
        value={photoUrl}
        onChange={(e) => setPhotoUrl(e.target.value)}
        required
        error={!!localErrors.photo || invalid("photo_urls")}
        helperText={localErrors.photo}
      />
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField
          label="Prix (€)"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          required
          error={!!localErrors.price || invalid("price")}
          helperText={localErrors.price ?? "Supérieur à 0, deux décimales au plus."}
          slotProps={{ htmlInput: { inputMode: "decimal" } }}
        />
        <TextField
          label="Frais de port (€)"
          value={fee}
          onChange={(e) => setFee(e.target.value)}
          required
          error={!!localErrors.fee || invalid("shipping_fee")}
          helperText={localErrors.fee ?? "0,00 pour une livraison gratuite."}
          slotProps={{ htmlInput: { inputMode: "decimal" } }}
        />
      </Stack>
      <Button type="submit" variant="contained" disabled={action.pending}>
        {action.pending ? "Envoi…" : "Mettre en vente"}
      </Button>

      {action.message && (
        <Alert severity="error">
          <AlertTitle>Saisie à corriger</AlertTitle>
          {action.message}
        </Alert>
      )}
      {result?.status === "PUBLISHED" && (
        <Alert severity="success">
          <AlertTitle>Article publié</AlertTitle>« {result.title} » est visible dans le catalogue.
        </Alert>
      )}
      {result?.status === "REJECTED" && (
        <Alert severity="warning">
          <AlertTitle>Article rejeté par le contrôle automatique</AlertTitle>
          « {result.title} » n'a pas été publié :
          <ul>
            {result.rejection_reasons.map((reason) => (
              <li key={reason}>{describeReason(reason)}</li>
            ))}
          </ul>
          Corrigez le texte puis mettez l'article en vente à nouveau.
        </Alert>
      )}
    </Stack>
  );
}
