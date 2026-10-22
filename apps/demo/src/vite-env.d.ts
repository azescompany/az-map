/// <reference types="vite/client" />
/// <reference types="geojson" />

interface ImportMetaEnv {
  readonly VITE_APP_MODE?: "dev" | "customer";
  /** `local` (default) | `cdn` | absolute URL */
  readonly VITE_GEOATLAS_DATA_BASE?: string;
  /** Local root when BASE=local (default `/` = Vite publicDir) */
  readonly VITE_GEOATLAS_DATA_LOCAL?: string;
  /** jsDelivr pin when BASE=cdn */
  readonly VITE_GEOATLAS_DATA_CDN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
