export type AppMode = "dev" | "customer";

/** URL ?mode= → VITE_APP_MODE → default customer */
export function resolveAppMode(): AppMode {
  if (typeof window !== "undefined") {
    const q = new URLSearchParams(window.location.search).get("mode");
    if (q === "dev" || q === "customer") return q;
  }
  const env = import.meta.env.VITE_APP_MODE;
  if (env === "customer" || env === "dev") return env;
  return "customer";
}

export function isCustomerMode(mode: AppMode = resolveAppMode()): boolean {
  return mode === "customer";
}
