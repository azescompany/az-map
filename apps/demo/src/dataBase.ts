import {
  DEFAULT_DATA_BASE,
  DEFAULT_DATA_BASE_CANONICAL,
} from "@geoatlas/data";

export type DataSourceHint = "cdn" | "local" | "derived";

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
 * - Default / `cdn` / `cdn-derived` → jsDelivr **data-derived/** pin (`DEFAULT_DATA_BASE`)
 * - `cdn-canonical` → jsDelivr fat `data/` pin (`DEFAULT_DATA_BASE_CANONICAL`)
 * - `local` → Vite `publicDir` = repo `data/`
 * - `derived` → Vite `publicDir` = repo `data-derived/`
 */
export function resolveDataBase(
  envValue: string | undefined = import.meta.env.VITE_GEOATLAS_DATA_BASE,
): ResolvedDataBase {
  const raw = (envValue ?? "").trim().toLowerCase();
  const localRaw = (import.meta.env.VITE_GEOATLAS_DATA_LOCAL ?? "/").trim() || "/";
  // Root-relative `/` must stay a single slash for join() → `/manifest.json`
  const localBase = localRaw === "/" ? "/" : withTrailingSlash(localRaw);
  const cdnDerivedBase = withTrailingSlash(
    (import.meta.env.VITE_GEOATLAS_DATA_CDN ?? DEFAULT_DATA_BASE).trim() ||
      DEFAULT_DATA_BASE,
  );
  const cdnCanonicalBase = withTrailingSlash(
    (
      import.meta.env.VITE_GEOATLAS_DATA_CDN_CANONICAL ??
      DEFAULT_DATA_BASE_CANONICAL
    ).trim() || DEFAULT_DATA_BASE_CANONICAL,
  );

  // unset / empty / cdn / cdn-derived → jsDelivr derived pin (default consumer)
  if (!raw || raw === "cdn" || raw === "default" || raw === "cdn-derived") {
    return { base: cdnDerivedBase, source: "cdn" };
  }
  if (raw === "cdn-canonical") {
    return { base: cdnCanonicalBase, source: "cdn" };
  }
  if (raw === "derived") {
    // Served from Vite publicDir = data-derived/ (see vite.config.ts)
    return { base: localBase, source: "derived" };
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
  const looksDerived = /data-derived/i.test(base);
  return {
    base,
    source: looksDerived ? "derived" : isLocal ? "local" : "cdn",
  };
}
