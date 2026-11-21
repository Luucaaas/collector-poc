import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Link as MuiLink,
  Pagination,
  Stack,
  Switch,
  Typography,
} from "@mui/material";
import { useState, type ReactNode } from "react";
import { Link } from "react-router";
import type { AppNotification, Category, Interests, Page, Preferences } from "../api/types";
import { useAction } from "../api/useAction";
import { useApi } from "../api/useApi";
import { useAsync } from "../api/useAsync";
import { EmptyState } from "../components/EmptyState";
import { Tile } from "../components/ItemCard";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { NOTIFICATIONS_PAGE_SIZE, useNotifications } from "../components/Notifications";
import { PageHeader } from "../components/PageHeader";
import { useToast } from "../components/Toast";
import { formatDateTime, formatMoney, formatTime } from "../format";

/** The API refuses more than 20 followed categories (RM-08, `TOO_MANY_CATEGORIES`). */
export const MAX_INTERESTS = 20;

/** "Mes centres d'intérêt" page (buyer, US-05): notifications, followed categories, preferences. */
export function InterestsPage() {
  return (
    <Stack spacing={3}>
      <PageHeader
        title="Mes centres d'intérêt"
        subtitle="Suivez des catégories : vous êtes prévenu dès qu'un article y est publié ou change de prix."
      />
      <Box
        sx={{
          display: "grid",
          gap: 3,
          alignItems: "start",
          gridTemplateColumns: { xs: "minmax(0, 1fr)", md: "minmax(0, 7fr) minmax(0, 5fr)" },
        }}
      >
        <NotificationsSection />
        <Stack spacing={3}>
          <InterestsSection />
          <PreferencesSection />
        </Stack>
      </Box>
    </Stack>
  );
}

function SettingsCard({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <Card component="section" aria-labelledby={id}>
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h5" component="h2" id={id}>
            {title}
          </Typography>
          {children}
        </Stack>
      </CardContent>
    </Card>
  );
}

function InterestsSection() {
  const api = useApi();
  const categories = useAsync((signal) => api.catalog<Page<Category>>("/categories", { signal }), [api]);
  const interests = useAsync((signal) => api.notification<Interests>("/me/interests", { signal }), [api]);

  return (
    <SettingsCard id="interests-title" title="Catégories suivies">
      {(categories.status === "loading" || interests.status === "loading") && (
        <LoadingSkeleton label="Chargement des catégories" />
      )}
      {categories.status === "error" && <Alert severity="error">{categories.message}</Alert>}
      {interests.status === "error" && <Alert severity="error">{interests.message}</Alert>}
      {categories.status === "success" && interests.status === "success" && (
        <InterestsForm categories={categories.data.items} initial={interests.data.category_ids} />
      )}
    </SettingsCard>
  );
}

function sameSet(a: Set<string>, b: Set<string>): boolean {
  return a.size === b.size && [...a].every((id) => b.has(id));
}

function InterestsForm({ categories, initial }: { categories: Category[]; initial: string[] }) {
  const api = useApi();
  const toast = useToast();
  const [selected, setSelected] = useState<Set<string>>(new Set(initial));
  const [saved, setSaved] = useState<Set<string>>(new Set(initial));
  const action = useAction();

  if (categories.length === 0) {
    return <EmptyState title="Aucune catégorie n'existe encore." description="L'administrateur n'en a pas encore créé." />;
  }

  const dirty = !sameSet(selected, saved);
  const tooMany = selected.size > MAX_INTERESTS;

  function toggle(id: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function save() {
    const result = await action.run(() =>
      api.notification<Interests>("/me/interests", { method: "PUT", body: { category_ids: [...selected] } }),
    );
    if (result) {
      setSaved(new Set(selected));
      toast("Centres d'intérêt enregistrés.", "success");
    }
  }

  return (
    <>
      <FormGroup
        role="group"
        aria-labelledby="interests-title"
        sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)", md: "1fr" } }}
      >
        {categories.map((category) => (
          <FormControlLabel
            key={category.id}
            label={category.name}
            control={<Checkbox checked={selected.has(category.id)} onChange={() => toggle(category.id)} />}
          />
        ))}
      </FormGroup>
      <Typography variant="body2" color={tooMany ? "error" : "text.secondary"} role="status">
        {tooMany
          ? `Vous ne pouvez pas suivre plus de ${MAX_INTERESTS} catégories : décochez-en ${selected.size - MAX_INTERESTS}.`
          : `${selected.size} sur ${MAX_INTERESTS} catégories au maximum${dirty ? ". Modifications non enregistrées." : "."}`}
      </Typography>
      <Button variant="contained" onClick={save} disabled={action.pending || tooMany} sx={{ alignSelf: "flex-start" }}>
        {action.pending ? "Enregistrement…" : "Enregistrer mes centres d'intérêt"}
      </Button>
      {action.message && <Alert severity="error">{action.message}</Alert>}
    </>
  );
}

function PreferencesSection() {
  const api = useApi();
  const preferences = useAsync((signal) => api.notification<Preferences>("/me/preferences", { signal }), [api]);

  return (
    <SettingsCard id="preferences-title" title="Préférences de notification">
      {preferences.status === "loading" && <LoadingSkeleton label="Chargement des préférences" />}
      {preferences.status === "error" && <Alert severity="error">{preferences.message}</Alert>}
      {preferences.status === "success" && <PreferencesForm initial={preferences.data} />}
    </SettingsCard>
  );
}

function PreferenceSwitch({
  label,
  help,
  id,
  checked,
  onChange,
}: {
  label: string;
  help: string;
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <Box>
      <FormControlLabel
        label={label}
        control={
          <Switch
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            slotProps={{ input: { "aria-describedby": id } }}
          />
        }
      />
      <Typography id={id} variant="body2" color="text.secondary" sx={{ ml: 6 }}>
        {help}
      </Typography>
    </Box>
  );
}

function PreferencesForm({ initial }: { initial: Preferences }) {
  const api = useApi();
  const toast = useToast();
  const [values, setValues] = useState<Preferences>(initial);
  const action = useAction();

  async function save() {
    const result = await action.run(() => api.notification<Preferences>("/me/preferences", { method: "PUT", body: values }));
    if (result) toast("Préférences enregistrées.", "success");
  }

  return (
    <>
      <FormGroup role="group" aria-labelledby="preferences-title" sx={{ gap: 1 }}>
        <PreferenceSwitch
          id="pref-new-article-help"
          label="Être prévenu d'un nouvel article"
          help="Un article vient d'être publié dans l'une de vos catégories."
          checked={values.new_article}
          onChange={(new_article) => setValues((v) => ({ ...v, new_article }))}
        />
        <PreferenceSwitch
          id="pref-price-changed-help"
          label="Être prévenu d'un changement de prix"
          help="Le vendeur modifie le prix d'un article de l'une de vos catégories."
          checked={values.price_changed}
          onChange={(price_changed) => setValues((v) => ({ ...v, price_changed }))}
        />
      </FormGroup>
      <Button variant="contained" onClick={save} disabled={action.pending} sx={{ alignSelf: "flex-start" }}>
        {action.pending ? "Enregistrement…" : "Enregistrer mes préférences"}
      </Button>
      {action.message && <Alert severity="error">{action.message}</Alert>}
    </>
  );
}

/** Readable text of a notification, from its type (contrats.md §2.2). */
export function notificationText(n: AppNotification): string {
  const c = n.content;
  const money = (amount: string | undefined) => (amount ? formatMoney(amount, c.currency ?? "EUR") : "?");
  if (n.type === "NEW_ARTICLE") return `Nouvel article : « ${c.title} » à ${money(c.price)}`;
  return `Changement de prix : « ${c.title} » passe de ${money(c.old_price)} à ${money(c.new_price)}`;
}

function NotificationList({ items }: { items: AppNotification[] }) {
  return (
    <Stack component="ul" spacing={1} sx={{ listStyle: "none", p: 0, m: 0 }} aria-label="Liste des notifications">
      {items.map((n) => (
        <Card component="li" key={n.id}>
          <CardContent sx={{ display: "flex", gap: 2, alignItems: "flex-start" }}>
            <Tile seed={n.content.title ?? n.type} size={44} />
            <Box sx={{ minWidth: 0 }}>
              <Typography>{notificationText(n)}</Typography>
              <Stack direction="row" useFlexGap sx={{ gap: 1.5, flexWrap: "wrap", alignItems: "center" }}>
                <Typography variant="caption" color="text.secondary">
                  {formatDateTime(n.created_at)}
                </Typography>
                <MuiLink
                  component={Link}
                  to={`/catalogue/${encodeURIComponent(n.article_id)}`}
                  variant="body2"
                  aria-label={`Voir l'article « ${n.content.title ?? ""} »`}
                >
                  Voir l'article
                </MuiLink>
              </Stack>
            </Box>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
}

/** Pages after the first one: loaded once, and again when the total changes (the first page comes from the shared feed). */
function OlderNotifications({ page, total }: { page: number; total: number }) {
  const api = useApi();
  const older = useAsync(
    (signal) =>
      api.notification<Page<AppNotification>>(
        `/me/notifications?limit=${NOTIFICATIONS_PAGE_SIZE}&offset=${(page - 1) * NOTIFICATIONS_PAGE_SIZE}`,
        { signal },
      ),
    [api, page, total],
  );
  if (older.status === "loading") return <LoadingSkeleton label="Chargement des notifications" />;
  if (older.status === "error") return <Alert severity="error">{older.message}</Alert>;
  return <NotificationList items={older.data.items} />;
}

function NotificationsSection() {
  const feed = useNotifications();
  const [page, setPage] = useState(1);
  const total = feed.page?.total ?? 0;

  return (
    <Stack spacing={2} component="section" aria-labelledby="notifications-title">
      <Stack direction="row" useFlexGap sx={{ gap: 2, alignItems: "center", flexWrap: "wrap" }}>
        <Typography variant="h5" component="h2" id="notifications-title">
          Mes notifications
        </Typography>
        <Button variant="outlined" size="small" onClick={feed.refresh} disabled={feed.loading}>
          Actualiser
        </Button>
        {feed.updatedAt && (
          <Typography variant="caption" color="text.secondary">
            Mis à jour à {formatTime(feed.updatedAt)}, puis toutes les 10 secondes
          </Typography>
        )}
      </Stack>
      {!feed.page && !feed.message && <LoadingSkeleton label="Chargement des notifications" />}
      {feed.message && <Alert severity={feed.page ? "warning" : "error"}>{feed.message}</Alert>}
      {feed.page && feed.page.items.length === 0 && (
        <EmptyState
          title="Aucune notification pour le moment."
          description="Elles apparaîtront ici dès qu'un article sera publié, ou changera de prix, dans l'une de vos catégories suivies."
        />
      )}
      {feed.page && feed.page.items.length > 0 && (
        <>
          <Typography variant="body2" color="text.secondary" role="status">
            {total} notification{total > 1 ? "s" : ""} au total
          </Typography>
          {page === 1 ? <NotificationList items={feed.page.items} /> : <OlderNotifications page={page} total={total} />}
          {total > NOTIFICATIONS_PAGE_SIZE && (
            <Pagination
              count={Math.ceil(total / NOTIFICATIONS_PAGE_SIZE)}
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
