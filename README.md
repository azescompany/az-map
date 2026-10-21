# GeoAtlas Azərbaycan

Standalone pilot: canonical administrative hierarchy + MapLibre demo.

Original Overture / OSM / GeoNames files remain immutable under `source_files/` (not committed).

## Quick start

```bash
pnpm install
pnpm validate
pnpm dev
```

Open http://localhost:5173

## Commands

| Command | Purpose |
|--|--|
| `pnpm dev` | Run interactive demo |
| `pnpm validate` | Validate curated `data/` |
| `pnpm extract:pilot` | Rebuild pilot from `source_files/` (read-only sources) |
| `pnpm build` | Production build |

## Layout

- `apps/demo` — React + Vite + MapLibre UI
- `packages/geoatlas-types` — TypeScript types
- `packages/geoatlas-data` — loaders / search helpers
- `data/` — versioned canonical JSON + GeoJSON
- `scripts/` — extract + validate
- `docs/` — data model, hierarchy, provenance
- `source_files/` — **immutable** raw sources (gitignored)

## Pilot coverage

Not full national coverage. Includes:

- Azərbaycan country boundary (Overture)
- Bakı + city districts (OSM admin relations)
- Yasamal neighborhoods with verification rules
- Notable places inside Yasamal (Overture landmarks + OSM notables)

See `data/manifest.json` and `data/reviews/`.
