# GeoAtlas data model

Canonical curated records live under `data/`. Original sources stay immutable in `source_files/` (gitignored).

## Areas (`data/areas/areas.json`)

| Field | Meaning |
|--|--|
| `id` | Stable UUID v5 (`geoatlas-aze:…`) |
| `name` / `name_normalized` / `alt_names` | Display + search |
| `type` | country, city, rayon, neighborhood, … |
| `parent_id` | Administrative parent when verified |
| `parent_status` | verified \| inferred_spatial \| conflict \| missing \| partial |
| `geom_status` | verified \| partial \| missing |
| `center` + `center_method` | Representative point provenance |
| `wikidata` | Cross-source join key when known |
| `source_refs` | Overture / OSM / GeoNames IDs + release |
| `boundary_file` | Relative path under `data/` |

Administrative parent links are **not** inferred solely from geometric containment. Containment is checked during extract and conflicts go to `data/reviews/`.

## Boundaries (`data/boundaries/*.geojson`)

WGS84 GeoJSON `FeatureCollection` with Polygon/MultiPolygon geometries.

## Places (`data/places/`)

Curated notable places for the pilot (Yasamal). Categories are normalized (`historic`, `park`, …). Each place keeps `source_refs` and optional `area_id` with `area_assign_status`.

## Manifest (`data/manifest.json`)

Dataset version, counts, source releases, basemap dependency note, hierarchy policy.
