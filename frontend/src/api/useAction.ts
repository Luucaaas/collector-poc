import { useCallback, useRef, useState } from "react";
import { ApiError, describeError } from "./errors";

export interface ActionState {
  /** True while sending: buttons must be disabled (no double submission). */
  pending: boolean;
  /** French message of the last error, or null. */
  message: string | null;
  /** Fields named by the last 422 error (to mark them in red). */
  errorFields: string[];
  /** Runs the action; returns its result, or undefined if it failed or another one is running. */
  run: <T>(action: () => Promise<T>, options?: { conflict?: string }) => Promise<T | undefined>;
  reset: () => void;
}

/** Form submission: "pending" state, translated error, guard against double submission. */
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
