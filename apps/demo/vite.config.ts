import fs from "node:fs";
import path from "node:path";
import type { Plugin } from "vite";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const swSrc = path.resolve(__dirname, "sw.js");

/** Serve / emit sw.js even when publicDir is data/ or data-derived/. */
function geoatlasSwPlugin(): Plugin {
  return {
    name: "geoatlas-sw",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url?.split("?")[0];
        if (url !== "/sw.js") {
          next();
          return;
        }
        res.setHeader("Content-Type", "application/javascript; charset=utf-8");
        res.setHeader("Cache-Control", "no-cache");
        fs.createReadStream(swSrc).pipe(res);
      });
    },
    writeBundle(outputOptions) {
      const dir = outputOptions.dir;
      if (!dir) return;
      fs.copyFileSync(swSrc, path.join(dir, "sw.js"));
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, "");
  const baseHint = (env.VITE_GEOATLAS_DATA_BASE || "").trim().toLowerCase();
  const useDerived = mode === "derived" || baseHint === "derived";
  const publicDir = path.resolve(
    __dirname,
    useDerived ? "../../data-derived" : "../../data",
  );

  // default/customer/dev → 1555; form (real estate) → 1556
  const port = mode === "form" ? 1556 : 1555;

  return {
    plugins: [react(), geoatlasSwPlugin()],
    // canonical data/ or derived data-derived/ as static root
    publicDir,
    server: {
      port,
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
  };
});
