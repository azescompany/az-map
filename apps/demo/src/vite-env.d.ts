/// <reference types="vite/client" />
/// <reference types="geojson" />

interface ImportMetaEnv {
  readonly VITE_APP_MODE?: "dev" | "customer";
  /** unset|cdn → CDN; local|/ → Vite publicDir; or absolute URL */
  readonly VITE_GEOATLAS_DATA_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
