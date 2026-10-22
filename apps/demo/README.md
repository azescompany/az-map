# GeoAtlas demo

MapLibre UI over the canonical Azerbaijan dataset.

## Data source (CDN default)

By default the demo loads curated JSON/GeoJSON from jsDelivr (not from the npm package):

```text
https://cdn.jsdelivr.net/gh/azescompany/az-map@v0.2.2-national/data/
```

Consumer one-liner:

```ts
import { DEFAULT_DATA_BASE, loadAreas } from "@geoatlas/data";
const areas = await loadAreas(DEFAULT_DATA_BASE);
```

### Override

| `VITE_GEOATLAS_DATA_BASE` | Behaviour |
| --- | --- |
| unset / empty / `cdn` | CDN pin above |
| `local` | Vite `publicDir` → repo `data/` at `/` |
| `http://localhost:1555/` | Same host static files |

```bash
pnpm --filter @geoatlas/demo dev
# offline / extract work:
VITE_GEOATLAS_DATA_BASE=local pnpm --filter @geoatlas/demo dev
```

On Windows PowerShell:

```powershell
$env:VITE_GEOATLAS_DATA_BASE="local"; pnpm --filter @geoatlas/demo dev
```
