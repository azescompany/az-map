# 00 — Findings

Baseline (plan date) → **shipped closeout 2026-10-23** ([CLOSEOUT](./CLOSEOUT.md)).

## What exists now (shipped)

| Layer | Status |
|---|---|
| SoT | Git `data/` from extract; `source_files/` immutable |
| Consumer publish | `data-derived/` via `pnpm derive:publish`; pin `@v0.3.x-national` |
| Delivery | jsDelivr `DEFAULT_DATA_BASE` → derived; `pin.json` for discovery |
| Areas | Lazy: `catalog/top.json` + country children (~13.5 KB br cold); dual-read vs canonical |
| Places | Shards + index; city/rayon cascade union; no `baki_all` |
| Boundaries | Verbatim GeoJSON; selected entity always full boundary + lat/lon |
| Loaders | `@geoatlas/data`: L1+single-flight, Worker parse ≥48 KiB, `prefetchAreaData` |
| Cascade UI | Parallel boundary ∥ places; hover/keyboard prefetch |
| Map | MapLibre clustering |
| Search | Scoped `search/{areaId}`; national lazy on focus (~1.49 MB br) |
| Cache | L1 memory + SW L2 pin version |
| Reviews | `data/reviews/` audit path; not cold-critical |

## Hierarchy modes (supported)

1. **City → rayon → hood** (Bakı, Gəncə)  
2. **City-direct** (Sumqayıt, …)  
3. **Country → rayon → settlement** (Abşeron, …)

## Key measured sizes

Canonical `areas.json` ~344 KB br (too fat for cold). Derived lazy cold ~13.5 KB br. See [MEASUREMENTS](./worker/MEASUREMENTS.md).
