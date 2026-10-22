import { DEFAULT_DATA_BASE } from "@geoatlas/data";

export type DataSourceHint = "cdn" | "local";

export type ResolvedDataBase = {
  /** Trailing-slash base for `@geoatlas/data` loaders */
  base: string;
  source: DataSourceHint;
};

function withTrailingSlash(url: string): string {
  return url.endsWith("/") ? url : `${url}/`;
}

/**
 * Resolve curated data root.
 *
 * Default = **CDN** (`DEFAULT_DATA_BASE` / jsDelivr pin).
 * Local Vite `publicDir` only when `VITE_GEOATLAS_DATA_BASE=local` (or `/`).
 */
export function resolveDataBase(
  envValue: string | undefined = import.meta.env.VITE_GEOATLAS_DATA_BASE,
): ResolvedDataBase {
  const raw = (envValue ?? "").trim().toLowerCase();
  const localRaw = (import.meta.env.VITE_GEOATLAS_DATA_LOCAL ?? "/").trim() || "/";
  // Root-relative `/` must stay a single slash for join() → `/manifest.json`
  const localBase = localRaw === "/" ? "/" : withTrailingSlash(localRaw);
  const cdnBase = withTrailingSlash(
    (import.meta.env.VITE_GEOATLAS_DATA_CDN ?? DEFAULT_DATA_BASE).trim() ||
      DEFAULT_DATA_BASE,
  );

  // unset / empty / explicit cdn → jsDelivr pin (never Vite publicDir)
  if (!raw || raw === "cdn" || raw === "default") {
    return { base: cdnBase, source: "cdn" };
  }
  if (raw === "local" || raw === "/") {
    return { base: localBase, source: "local" };
  }

  // Absolute override (e.g. http://localhost:1555/ or full jsDelivr URL)
  const original = (envValue ?? "").trim();
  const base = withTrailingSlash(original);
  const isLocal =
    /localhost|127\.0\.0\.1/i.test(base) ||
    base.startsWith("/") ||
    base.startsWith("./");
  return { base, source: isLocal ? "local" : "cdn" };
}
