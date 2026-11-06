import {
  Alert,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  FormControlLabel,
  FormGroup,
  Pagination,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";
import type { AppNotification, Category, Interests, Page, Preferences } from "../api/types";
import { useAction } from "../api/useAction";
import { useApi } from "../api/useApi";
import { useAsync } from "../api/useAsync";
import { formatDateTime, formatMoney } from "../format";

export const NOTIFICATIONS_PAGE_SIZE = 10;

/** Page « Mes centres d'intérêt » (buyer, US-05) : catégories, préférences, notifications. */
export function InterestsPage() {
  return (
    <Stack spacing={4}>
      <Typography variant="h4" component="h1">
        Mes centres d'intérêt
      </Typography>
      <InterestsSection />
      <PreferencesSection />
      <NotificationsSection />
    </Stack>
  );
}

function InterestsSection() {
  const api = useApi();
  const categories = useAsync((signal) => api.catalog<Page<Category>>("/categories", { signal }), [api]);
  const interests = useAsync((signal) => api.notification<Interests>("/me/interests", { signal }), [api]);

  return (
    <Stack spacing={2} component="section" aria-labelledby="interests-title">
      <Typography variant="h5" component="h2" id="interests-title">
        Catégories suivies
      </Typography>
      {(categories.status === "loading" || interests.status === "loading") && (
        <CircularProgress aria-label="Chargement des catégories" />
      )}
      {categories.status === "error" && <Alert severity="error">{categories.message}</Alert>}
      {interests.status === "error" && <Alert severity="error">{interests.message}</Alert>}
      {categories.status === "success" && interests.status === "success" && (
        <InterestsForm categories={categories.data.items} initial={interests.data.category_ids} />
      )}
    </Stack>
  );
}

function InterestsForm({ categories, initial }: { categories: Category[]; initial: string[] }) {
  const api = useApi();
  const [selected, setSelected] = useState<Set<string>>(new Set(initial));
  const [saved, setSaved] = useState(false);
  const action = useAction();

  if (categories.length === 0) return <Alert severity="info">Aucune catégorie n'existe encore.</Alert>;

  function toggle(id: string) {
    setSaved(false);
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function save() {
    setSaved(false);
    const result = await action.run(() =>
      api.notification<Interests>("/me/interests", { method: "PUT", body: { category_ids: [...selected] } }),
    );
    if (result) setSaved(true);
  }

  return (
    <>
      <FormGroup role="group" aria-label="Catégories d'intérêt">
        {categories.map((category) => (
          <FormControlLabel
            key={category.id}
            label={category.name}
            control={<Checkbox checked={selected.has(category.id)} onChange={() => toggle(category.id)} />}
          />
        ))}
      </FormGroup>
      <Button variant="contained" onClick={save} disabled={action.pending} sx={{ alignSelf: "flex-start" }}>
        {action.pending ? "Enregistrement…" : "Enregistrer mes centres d'intérêt"}
      </Button>
      {action.message && <Alert severity="error">{action.message}</Alert>}
      {saved && <Alert severity="success">Centres d'intérêt enregistrés.</Alert>}
    </>
  );
}

function PreferencesSection() {
  const api = useApi();
  const preferences = useAsync((signal) => api.notification<Preferences>("/me/preferences", { signal }), [api]);

  return (
    <Stack spacing={2} component="section" aria-labelledby="preferences-title">
      <Typography variant="h5" component="h2" id="preferences-title">
        Préférences de notification
      </Typography>
      {preferences.status === "loading" && <CircularProgress aria-label="Chargement des préférences" />}
      {preferences.status === "error" && <Alert severity="error">{preferences.message}</Alert>}
      {preferences.status === "success" && <PreferencesForm initial={preferences.data} />}
    </Stack>
  );
}

function PreferencesForm({ initial }: { initial: Preferences }) {
  const api = useApi();
  const [values, setValues] = useState<Preferences>(initial);
  const [saved, setSaved] = useState(false);
  const action = useAction();

  function change(patch: Partial<Preferences>) {
    setSaved(false);
    setValues((v) => ({ ...v, ...patch }));
  }

  async function save() {
    setSaved(false);
    const result = await action.run(() => api.notification<Preferences>("/me/preferences", { method: "PUT", body: values }));
    if (result) setSaved(true);
  }

  return (
    <>
      <FormGroup role="group" aria-label="Types de notification">
        <FormControlLabel
          label="Être prévenu d'un nouvel article"
          control={<Checkbox checked={values.new_article} onChange={(e) => change({ new_article: e.target.checked })} />}
        />
        <FormControlLabel
          label="Être prévenu d'un changement de prix"
          control={<Checkbox checked={values.price_changed} onChange={(e) => change({ price_changed: e.target.checked })} />}
        />
      </FormGroup>
      <Button variant="contained" onClick={save} disabled={action.pending} sx={{ alignSelf: "flex-start" }}>
        {action.pending ? "Enregistrement…" : "Enregistrer mes préférences"}
      </Button>
      {action.message && <Alert severity="error">{action.message}</Alert>}
      {saved && <Alert severity="success">Préférences enregistrées.</Alert>}
    </>
  );
}

/** Texte lisible d'une notification, d'après son type (contrats.md §2.2). */
export function notificationText(n: AppNotification): string {
  const c = n.content;
  const money = (amount: string | undefined) => (amount ? formatMoney(amount, c.currency ?? "EUR") : "?");
  if (n.type === "NEW_ARTICLE") return `Nouvel article : « ${c.title} » à ${money(c.price)}`;
  return `Changement de prix : « ${c.title} » passe de ${money(c.old_price)} à ${money(c.new_price)}`;
}

function NotificationsSection() {
  const api = useApi();
  const [page, setPage] = useState(1);
  const [version, setVersion] = useState(0);
  const notifications = useAsync(
    (signal) =>
      api.notification<Page<AppNotification>>(
        `/me/notifications?limit=${NOTIFICATIONS_PAGE_SIZE}&offset=${(page - 1) * NOTIFICATIONS_PAGE_SIZE}`,
        { signal },
      ),
    [api, page, version],
  );

  return (
    <Stack spacing={2} component="section" aria-labelledby="notifications-title">
      <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
        <Typography variant="h5" component="h2" id="notifications-title">
          Mes notifications
        </Typography>
        <Button variant="outlined" onClick={() => setVersion((v) => v + 1)} disabled={notifications.status === "loading"}>
          Actualiser
        </Button>
      </Stack>
      {notifications.status === "loading" && <CircularProgress aria-label="Chargement des notifications" />}
      {notifications.status === "error" && <Alert severity="error">{notifications.message}</Alert>}
      {notifications.status === "success" && notifications.data.items.length === 0 && (
        <Alert severity="info">Aucune notification pour le moment.</Alert>
      )}
      {notifications.status === "success" && notifications.data.items.length > 0 && (
        <>
          <Stack component="ul" spacing={1} sx={{ listStyle: "none", p: 0, m: 0 }} aria-label="Liste des notifications">
            {notifications.data.items.map((n) => (
              <Card component="li" key={n.id} variant="outlined">
                <CardContent>
                  <Typography>{notificationText(n)}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatDateTime(n.created_at)}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
          {notifications.data.total > NOTIFICATIONS_PAGE_SIZE && (
            <Pagination
              count={Math.ceil(notifications.data.total / NOTIFICATIONS_PAGE_SIZE)}
              page={page}
              onChange={(_e, value) => setPage(value)}
              aria-label="Pagination des notifications"
            />
          )}
        </>
      )}
    </Stack>
  );
}
