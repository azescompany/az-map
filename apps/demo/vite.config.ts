import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Serve curated canonical dataset as static files
  publicDir: path.resolve(__dirname, "../../data"),
  server: {
    port: 1555,
    strictPort: true,
    fs: {
      allow: [path.resolve(__dirname, "../..")],
    },
  },
  resolve: {
    alias: {
      "@geoatlas/types": path.resolve(__dirname, "../../packages/geoatlas-types/src/index.ts"),
      "@geoatlas/data": path.resolve(__dirname, "../../packages/geoatlas-data/src/index.ts"),
    },
  },
});
