import { useCallback, useRef, useState } from "react";
import { ApiError, describeError } from "./errors";

export interface ActionState {
  /** Vrai pendant l'envoi : les boutons doivent être désactivés (pas de double soumission). */
  pending: boolean;
  /** Message en français de la dernière erreur, ou null. */
  message: string | null;
  /** Champs désignés par la dernière erreur 422 (pour les marquer en rouge). */
  errorFields: string[];
  /** Exécute l'action ; renvoie son résultat, ou undefined si elle a échoué ou si une autre est en cours. */
  run: <T>(action: () => Promise<T>, options?: { conflict?: string }) => Promise<T | undefined>;
  reset: () => void;
}

/** Envoi d'un formulaire : état « en cours », erreur traduite, garde contre la double soumission. */
export function useAction(): ActionState {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [errorFields, setErrorFields] = useState<string[]>([]);
  const running = useRef(false);

  const run = useCallback(async <T,>(action: () => Promise<T>, options?: { conflict?: string }): Promise<T | undefined> => {
    if (running.current) return undefined;
    running.current = true;
    setPending(true);
    setMessage(null);
    setErrorFields([]);
    try {
      return await action();
    } catch (error) {
      setMessage(describeError(error, options));
      if (error instanceof ApiError) {
        setErrorFields(error.fields.flatMap((e) => (e.field ? [e.field] : [])));
      }
      return undefined;
    } finally {
      running.current = false;
      setPending(false);
    }
  }, []);

  const reset = useCallback(() => {
    setMessage(null);
    setErrorFields([]);
  }, []);

  return { pending, message, errorFields, run, reset };
}
