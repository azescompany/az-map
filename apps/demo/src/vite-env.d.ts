/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_MODE?: "dev" | "customer";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
