/// <reference types="vite/client" />
/// <reference types="geojson" />

interface ImportMetaEnv {
  readonly VITE_APP_MODE?: "dev" | "customer";
  /** Shell layout: `default` floating | `form` top toolbar (real estate) */
  readonly VITE_SHELL_VARIANT?: "default" | "form";
  /** `cdn` | `local` | `derived` | `cdn-derived` | absolute URL */
  readonly VITE_GEOATLAS_DATA_BASE?: string;
  /** Local root when BASE=local|derived (default `/` = Vite publicDir) */
  readonly VITE_GEOATLAS_DATA_LOCAL?: string;
  /** jsDelivr derived pin when BASE=cdn (default consumer) */
  readonly VITE_GEOATLAS_DATA_CDN?: string;
  /** jsDelivr fat data/ pin when BASE=cdn-canonical */
  readonly VITE_GEOATLAS_DATA_CDN_CANONICAL?: string;
  /** Service Worker L2: `1`/`true` on, `0`/`false` off; default = production only */
  readonly VITE_GEOATLAS_SW?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
