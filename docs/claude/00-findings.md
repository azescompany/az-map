# 00 — Findings (repo as of plan date)

**Role:** PerfDocsArchitect only. Distinct from GeoAgent [`WORKER.md`](../../WORKER.md) / LandmarkAgent [`LANDMARK.md`](../../LANDMARK.md). Master prompt: [`PROMPT.md`](./PROMPT.md). Index: [`README.md`](./README.md).

## What exists today

| Layer | Today |
|---|---|
| SoT | Git `data/` from extract scripts; `source_files/` immutable |
| Delivery | jsDelivr pin `DEFAULT_DATA_BASE` → `@v0.2.3-national/data/` |
| Areas | Single `areas/areas.json` (~5 MB raw, **measured** earlier); `manifest.json` coverage.areas **3486** |
| Places | `places/{key}_all.json` + `places/index.json` (`total` **24068**); `area_id` rayon / city-direct |
| Boundaries | `boundaries/*` paths via `Area.boundary_file`; tree ~20 MB raw (**measured** sum) |
| Loaders | `@geoatlas/data`: `loadAreas`, `loadPlacesForArea`, `loadBoundary`, `loadAllCatalogPlaces` |
| Cascade UI | `@geoatlas/cascade-react`: leaf effect loads **boundary then places** (sequential) |
| Map | MapLibre circles; **no** clustering; OpenFreeMap basemap |
| Search | Demo cold-loads **all** place shards via `loadAllCatalogPlaces` |
| Pin | Git tag = `dataset_version`; **no** `pin.json` |
| Reviews | `data/reviews/` (audit; must not be consumer-critical path) |

## Hierarchy modes (must support)

1. **City → rayon → hood** (Bakı, Gəncə)  
2. **City-direct** (Sumqayıt, Mingəçevir, Şirvan, Naftalan, Yevlax city, Lənkəran city, Şəki, Naxçıvan)  
3. **Country → rayon → settlement** (Abşeron, Xızı, …)

## Known sizes (raw measured; compressed **unmeasured**)

`areas.json` ~5 MB · `nasimi_all` ~2.4 MB · `yasamal_all` ~1.8 MB · `sumqayit_all` ~1.3 MB · `country_AZ` ~1.3 MB · typical rayon boundary ~0.17 MB.

## Contradictions / stale notes

| Item | Detail |
|---|---|
| Place totals | `places/index.json` + `manifest` = **24068**; older chat note 18521 **stale**; `LANDMARK.md` PAUSE “14916” **stale vs disk** |
| jsDelivr file limit | External notes cite ~20 MB vs ~50 MB — **confirm official docs** ([14](./14-open-questions.md)) |
| Derive vs canonical | Plan chooses **derived publish tree**; canonical `data/` layout stays for GeoAgent/Landmark |

## Questions (do not guess)

See [14-open-questions.md](./14-open-questions.md). Blocked on humans: RACI tag/pin, AZ RUM, UI copy for `bbox_approx` / partial boundary, compressed baselines (P0-01).
