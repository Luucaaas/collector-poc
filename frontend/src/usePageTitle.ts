import { useEffect } from "react";

export const APP_NAME = "Collector.shop";

/** Sets the browser tab title ("Page · Collector.shop"), which screen readers announce on navigation. */
export function usePageTitle(title: string): void {
  useEffect(() => {
    document.title = `${title} · ${APP_NAME}`;
    return () => {
      document.title = APP_NAME;
    };
  }, [title]);
}
