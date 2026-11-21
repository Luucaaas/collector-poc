import { Alert, Snackbar, type AlertColor } from "@mui/material";
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

interface ToastMessage {
  id: number;
  text: string;
  severity: AlertColor;
}

type Notify = (text: string, severity?: AlertColor) => void;

// Outside a provider (isolated tests of a page), notifications are ignored.
const ToastContext = createContext<Notify>(() => {});

/** Global toast: `useToast()("Saved", "success")` from any component under the provider. */
export const useToast = () => useContext(ToastContext);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [current, setCurrent] = useState<ToastMessage | null>(null);
  const [open, setOpen] = useState(false);

  const notify = useCallback<Notify>((text, severity = "info") => {
    setCurrent({ id: Date.now() + Math.random(), text, severity });
    setOpen(true);
  }, []);
  const value = useMemo(() => notify, [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <Snackbar
        key={current?.id}
        open={open}
        autoHideDuration={5000}
        onClose={(_event, reason) => {
          if (reason !== "clickaway") setOpen(false);
        }}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        {current ? (
          <Alert severity={current.severity} variant="filled" onClose={() => setOpen(false)} sx={{ width: "100%" }}>
            {current.text}
          </Alert>
        ) : undefined}
      </Snackbar>
    </ToastContext.Provider>
  );
}
