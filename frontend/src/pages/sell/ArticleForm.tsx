import { Alert, AlertTitle, Box, Button, Stack, TextField, Typography } from "@mui/material";
import { useState, type FormEvent } from "react";
import { CONTACT_EMAIL, detectContact } from "../../contact";
import type { Article, ArticleCreateBody, Category, Shop } from "../../api/types";
import { useAction } from "../../api/useAction";
import { useApi } from "../../api/useApi";
import { ArticlePreview } from "../../components/ArticlePreview";
import { RejectionNotice } from "../../components/RejectionNotice";
import { useToast } from "../../components/Toast";
import { validateFee, validatePrice } from "../../money";

interface Props {
  shops: Shop[];
  categories: Category[];
  categoriesError: string | null;
  /** Called with the article returned by the API, published or rejected. */
  onSubmitted: (article: Article) => void;
}

interface Values {
  shopId: string;
  categoryId: string;
  title: string;
  description: string;
  photoUrl: string;
  price: string;
  fee: string;
}

type Errors = Partial<Record<"shop" | "category" | "title" | "description" | "photo" | "price" | "fee", string>>;

const TITLE_MAX = 120;
const DESCRIPTION_MAX = 5000;

/** Field-by-field check, run on every render so the messages follow the typing. */
export function validateArticleValues(v: Values): Errors {
  const errors: Errors = {};
  if (!v.shopId) errors.shop = "Choisissez une boutique.";
  if (!v.categoryId) errors.category = "Choisissez une catégorie.";
  if (v.title.trim().length < 5) errors.title = "Le titre doit contenir au moins 5 caractères.";
  if (v.description.trim().length < 20) errors.description = "La description doit contenir au moins 20 caractères.";
  if (!/^https:\/\/[^\s/]+(\/\S*)?$/.test(v.photoUrl.trim())) errors.photo = "Saisissez une adresse de photo en https://.";
  const price = validatePrice(v.price);
  if ("error" in price) errors.price = price.error;
  const fee = validateFee(v.fee);
  if ("error" in fee) errors.fee = fee.error;
  return errors;
}

/**
 * Listing (US-03). Live validation helps the seller; the API stays the authority. Three distinct
 * outcomes: published article (201 PUBLISHED), article rejected by the automatic check (201
 * REJECTED, with reasons) and malformed request (422, input error).
 */
export function ArticleForm({ shops, categories, categoriesError, onSubmitted }: Props) {
  const api = useApi();
  const toast = useToast();
  const [values, setValues] = useState<Values>({
    shopId: shops[0]?.id ?? "",
    categoryId: "",
    title: "",
    description: "",
    photoUrl: "",
    price: "",
    fee: "0.00",
  });
  const [touched, setTouched] = useState<Set<string>>(new Set());
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<Article | null>(null);
  const action = useAction();

  const errors = validateArticleValues(values);
  const set = (field: keyof Values) => (value: string) => setValues((v) => ({ ...v, [field]: value }));
  const touch = (field: string) => () => setTouched((t) => new Set(t).add(field));
  const shown = (field: keyof Errors) => (submitted || touched.has(field) ? errors[field] : undefined);
  const invalid = (field: string) => action.errorFields.includes(field);
  const contact = detectContact(values.title, values.description);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setResult(null);
    setSubmitted(true);
    const price = validatePrice(values.price);
    const fee = validateFee(values.fee);
    if (Object.keys(errors).length > 0 || !("value" in price) || !("value" in fee)) return;
    const body: ArticleCreateBody = {
      shop_id: values.shopId,
      category_id: values.categoryId,
      title: values.title.trim(),
      description: values.description.trim(),
      photo_urls: [values.photoUrl.trim()],
      price: price.value,
      shipping_fee: fee.value,
      currency: "EUR",
    };
    const article = await action.run(() => api.catalog<Article>("/articles", { method: "POST", body }), {
      onError: () => toast("La publication a échoué : voir le message sous le formulaire.", "error"),
    });
    if (!article) return;
    setResult(article);
    onSubmitted(article);
    if (article.status === "PUBLISHED") {
      toast(`« ${article.title} » est en vente dans le catalogue.`, "success");
      setValues((v) => ({ ...v, title: "", description: "", photoUrl: "", price: "" }));
      setTouched(new Set());
      setSubmitted(false);
    } else {
      toast("L'article a été rejeté par le contrôle automatique.", "warning");
    }
  }

  return (
    <Box
      sx={{
        display: "grid",
        gap: 3,
        gridTemplateColumns: { xs: "minmax(0, 1fr)", md: "minmax(0, 3fr) minmax(0, 2fr)" },
        alignItems: "start",
      }}
    >
      <Stack component="form" spacing={2} onSubmit={submit} noValidate aria-label="Mettre un article en vente">
        <Typography variant="h5" component="h2">
          Mettre un article en vente
        </Typography>
        {categoriesError && <Alert severity="warning">{categoriesError}</Alert>}
        <TextField
          select
          label="Boutique"
          value={values.shopId}
          onChange={(e) => set("shopId")(e.target.value)}
          slotProps={{ select: { native: true } }}
          error={!!shown("shop") || invalid("shop_id")}
          helperText={shown("shop")}
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
          value={values.categoryId}
          onChange={(e) => set("categoryId")(e.target.value)}
          onBlur={touch("category")}
          slotProps={{ select: { native: true } }}
          error={!!shown("category") || invalid("category_id")}
          helperText={shown("category")}
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
          value={values.title}
          onChange={(e) => set("title")(e.target.value)}
          onBlur={touch("title")}
          required
          error={!!shown("title") || invalid("title")}
          helperText={shown("title") ?? `Entre 5 et ${TITLE_MAX} caractères (${values.title.length}/${TITLE_MAX}).`}
          slotProps={{ htmlInput: { maxLength: TITLE_MAX } }}
        />
        <TextField
          label="Description de l'article"
          value={values.description}
          onChange={(e) => set("description")(e.target.value)}
          onBlur={touch("description")}
          required
          multiline
          minRows={3}
          error={!!shown("description") || invalid("description")}
          helperText={
            shown("description") ??
            `Au moins 20 caractères (${values.description.length}/${DESCRIPTION_MAX}). Sans adresse email ni numéro de téléphone.`
          }
          slotProps={{ htmlInput: { maxLength: DESCRIPTION_MAX } }}
        />
        {contact.length > 0 && (
          <Alert severity="warning" role="status">
            <AlertTitle>Cette annonce serait rejetée</AlertTitle>
            Le texte semble contenir {contact.map((c) => (c === CONTACT_EMAIL ? "une adresse email" : "un numéro de téléphone")).join(" et ")}.
            Les échanges passent par la plateforme : retirez ces coordonnées avant de publier.
          </Alert>
        )}
        <TextField
          label="Adresse de la photo (https)"
          value={values.photoUrl}
          onChange={(e) => set("photoUrl")(e.target.value)}
          onBlur={touch("photo")}
          required
          error={!!shown("photo") || invalid("photo_urls")}
          helperText={shown("photo") ?? "Obligatoire pour l'API ; l'aperçu n'affiche pas la photo."}
        />
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            label="Prix (€)"
            value={values.price}
            onChange={(e) => set("price")(e.target.value)}
            onBlur={touch("price")}
            required
            error={!!shown("price") || invalid("price")}
            helperText={shown("price") ?? "Supérieur à 0, deux décimales au plus."}
            slotProps={{ htmlInput: { inputMode: "decimal" } }}
            sx={{ flex: 1 }}
          />
          <TextField
            label="Frais de port (€)"
            value={values.fee}
            onChange={(e) => set("fee")(e.target.value)}
            onBlur={touch("fee")}
            required
            error={!!shown("fee") || invalid("shipping_fee")}
            helperText={shown("fee") ?? "0,00 pour une livraison gratuite."}
            slotProps={{ htmlInput: { inputMode: "decimal" } }}
            sx={{ flex: 1 }}
          />
        </Stack>
        <Button type="submit" variant="contained" size="large" disabled={action.pending}>
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
        {result?.status === "REJECTED" && <RejectionNotice title={result.title} reasons={result.rejection_reasons} />}
      </Stack>

      <Box sx={{ position: { md: "sticky" }, top: { md: 88 } }}>
        <ArticlePreview
          title={values.title}
          description={values.description}
          price={values.price}
          shippingFee={values.fee}
          categoryName={categories.find((c) => c.id === values.categoryId)?.name}
          shopName={shops.find((s) => s.id === values.shopId)?.name}
        />
      </Box>
    </Box>
  );
}
