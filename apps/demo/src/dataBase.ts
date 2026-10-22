import { DEFAULT_DATA_BASE } from "@geoatlas/data";

export type DataSourceHint = "cdn" | "local";

export type ResolvedDataBase = {
  /** Trailing-slash base for `@geoatlas/data` loaders */
  base: string;
  source: DataSourceHint;
};

/**
 * Resolve curated data root.
 * - unset / empty / `cdn` → {@link DEFAULT_DATA_BASE}
 * - `local` → Vite `publicDir` (`../../data`) at `/`
 * - absolute URL (e.g. `http://localhost:1555/`) → as given (normalized slash)
 */
export function resolveDataBase(
  envValue: string | undefined = import.meta.env.VITE_GEOATLAS_DATA_BASE,
): ResolvedDataBase {
  const raw = (envValue ?? "").trim();
  if (!raw || raw.toLowerCase() === "cdn") {
    return { base: DEFAULT_DATA_BASE, source: "cdn" };
  }
  if (raw.toLowerCase() === "local" || raw === "/" || raw === "") {
    return { base: "/", source: "local" };
  }
  const base = raw.endsWith("/") ? raw : `${raw}/`;
  const local =
    /localhost|127\.0\.0\.1/i.test(base) ||
    base.startsWith("/") ||
    base.startsWith("./");
  return { base, source: local ? "local" : "cdn" };
}
