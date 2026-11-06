// Types des réponses, d'après docs/02-architecture/contrats.md. Les montants sont des chaînes
// décimales ("120.00") : on ne les convertit jamais en nombre pour calculer.

export interface Category {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface Shop {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  seller_type: string;
  created_at: string;
}

export type ArticleStatus = "PUBLISHED" | "REJECTED";

export interface Article {
  id: string;
  shop_id: string;
  category_id: string;
  seller_id: string;
  title: string;
  description: string;
  photo_urls: string[];
  price: string;
  shipping_fee: string;
  currency: string;
  status: ArticleStatus;
  rejection_reasons: string[];
  created_at: string;
}

export interface PriceHistoryEntry {
  old_price: string;
  new_price: string;
  changed_by: string;
  changed_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
}

export type NotificationType = "NEW_ARTICLE" | "PRICE_CHANGED";

export interface Interests {
  category_ids: string[];
}

export interface Preferences {
  new_article: boolean;
  price_changed: boolean;
}

export interface AppNotification {
  id: string;
  type: NotificationType;
  article_id: string;
  content: Record<string, string>;
  created_at: string;
}

/** Corps d'erreur RFC 9457 (application/problem+json), contrats.md §1.3. */
export interface ProblemDetails {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  errors?: { field?: string; code?: string }[];
  correlation_id?: string;
}

/** Corps de POST /articles (montants en chaîne décimale). */
export interface ArticleCreateBody {
  shop_id: string;
  category_id: string;
  title: string;
  description: string;
  photo_urls: string[];
  price: string;
  shipping_fee: string;
  currency: "EUR";
}
