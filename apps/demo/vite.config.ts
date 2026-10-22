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
      "@geoatlas/types": path.resolve(
        __dirname,
        "../../packages/geoatlas-types/src/index.ts",
      ),
      "@geoatlas/data": path.resolve(
        __dirname,
        "../../packages/geoatlas-data/src/index.ts",
      ),
      "@geoatlas/cascade": path.resolve(
        __dirname,
        "../../packages/geoatlas-cascade/src/index.ts",
      ),
      "@geoatlas/cascade-react": path.resolve(
        __dirname,
        "../../packages/geoatlas-cascade-react/src/index.ts",
      ),
      "@geoatlas/map-react": path.resolve(
        __dirname,
        "../../packages/geoatlas-map-react/src/index.ts",
      ),
      "@geoatlas/shell-react/styles.css": path.resolve(
        __dirname,
        "../../packages/geoatlas-shell-react/src/shell.css",
      ),
      "@geoatlas/shell-react/tokens.css": path.resolve(
        __dirname,
        "../../packages/geoatlas-shell-react/src/tokens.css",
      ),
      "@geoatlas/shell-react": path.resolve(
        __dirname,
        "../../packages/geoatlas-shell-react/src/index.ts",
      ),
    },
  },
});

