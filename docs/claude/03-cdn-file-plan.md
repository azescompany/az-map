# 03 — CDN file plan (`data-derived/`)

Canonical SoT stays [`data/`](../../data/). This tree is the **consumer publish** artifact. See [02](./02-architecture.md).

Sizes: **unmeasured** until [P0-01](./11-roadmap.md) fills [worker/MEASUREMENTS.md](./worker/MEASUREMENTS.md).

## Directory tree

```text
data-derived/
  manifest.json
  catalog/
    top.json                          # country + mid-level units (cities, country-rayons)
    all-slim.json                     # all areas as slim rows (dual-read loadAreas)
    children/{areaId}.json            # verified children only (slim rows)
  areas/
    {areaId}.json                     # area detail (no inline polygon)
  boundaries/
    {areaId}.geojson                  # VERBATIM FeatureCollection (selected-entity path)
  boundaries-preview/                 # OPTIONAL lo-res; NEVER returned as boundary
    {areaId}.geojson
  places/
    index/{areaId}.json               # slim named places for that shard owner
    detail/{areaId}.json              # fuller place records (still no invented geom)
    shards.json                       # key → areaId → canonical source file map
  search/
    {areaId}.json                     # scoped name index (az normalize)
  pin.json                            # OPTIONAL P2: { tag, dataset_version } for data-only rollout
```

**Excluded from consumer path:** anything under canonical `data/reviews/`, audit dumps, quality reports.

## Path mapping (canonical → derived)

| Canonical | Derived |
|---|---|
| `manifest.json` | `manifest.json` (+ derive schema version field) |
| `areas/areas.json` row | `catalog/top.json` and/or `catalog/children/{parentId}.json` + `areas/{id}.json` |
| `Area.boundary_file` e.g. `boundaries/rayon_yasamal.geojson` | `boundaries/{areaId}.geojson` (byte-identical geom; CI hash vs canonical file) |
| `places/{key}_all.json` | `places/index/{areaId}.json` + `places/detail/{areaId}.json`; `shards.json` records `key` |
| `places/index.json` | Replaced by `shards.json` + per-area index files |

## Field lists

### Slim catalog row (`catalog/top.json`, `catalog/children/{areaId}.json`)

`id`, `name`, `name_normalized`, `type`, `subtype`, `parent_id`, `parent_status`, `geom_status`, `center` (lat/lon required if selectable), `center_status`, `center_method`, `bbox`, `boundary_ref` (`boundaries/{id}.geojson` or null), `places_shard_area_id` (nullable)

### Area detail (`areas/{areaId}.json`)

All catalog fields plus: `alt_names`, `source_refs`, `wikidata`, `notes`, `crs`, `geometry_type`, `center_within_boundary`. **No** inline polygon. `center` **must equal** catalog row (CI fail on mismatch). **Center authority = catalog row.**

### Boundary (`boundaries/{areaId}.geojson`)

Full GeoJSON FeatureCollection, **verbatim** from canonical `boundary_file`. Selected-entity path uses only this (or rejects / `none` if missing). Preview files are separate.

### Places index (`places/index/{areaId}.json`)

Named places only: `id`, `name`, `name_normalized`, `category`, `coordinates.lat/lon`, `area_id` (rayon/city-direct), optional derived `neighborhood_id` (P1 index, not written back to canonical `data/places`).

### Places detail (`places/detail/{areaId}.json`)

Index fields + `alt_names`, `source_refs`, `area_assign_status`, `status`, confidence, street disambiguation fields as present in source.

### Search (`search/{areaId}.json`)

`id`, `name_normalized` (ə ı ö ü ç ş ğ aware), `category`, `lat`, `lon`, `area_id`.

## Size classes (unmeasured)

| Class | Est. role | Status |
|---|---|---|
| `manifest.json` | tiny | unmeasured |
| `catalog/top.json` | cold start | **target** 60–150 KB br with manifest — validate P0-01 |
| `catalog/children/{id}.json` | per parent | unmeasured |
| `areas/{id}.json` | detail | unmeasured |
| `boundaries/{id}.geojson` | full geom | unmeasured (canonical raw known ~0.17 MB typical rayon) |
| `places/index/{id}.json` | slim POI | unmeasured |
| `places/detail/{id}.json` | fuller POI | unmeasured |
| `search/{id}.json` | scoped search | unmeasured |

## Compat

P0: consumers keep `DEFAULT_DATA_BASE` → canonical `data/`. P1: HUMAN pin PR switches to `…/data-derived/` (or dual-read). See [11](./11-roadmap.md).
