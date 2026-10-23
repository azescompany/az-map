# 05 — Place sources and neighborhoods

Canonical assign: `area_id` = **rayon** or **city-direct / settlement** extract id ([Hierarchy](../../Hierarchy.md)). No mass re-assign into canonical `data/places`.

## Two-mode (plus Absheron) union

| Selection | Places source |
|---|---|
| **City with verified rayon children** (Bakı, Gəncə) | Client-side **union** of each verified child rayon shard (`places/index\|detail/{childAreaId}`); dedupe by `place.id`. **No** `baki_all.json`. |
| **City-direct** (Sumqayıt, …) | Own shard for that city `areaId`. |
| **Country→rayon** with distinct settlement shards (Abşeron) | Rayon shard ∪ distinct verified settlement shards (Masazır, Xırdalan, …); dedupe by id. |
| **Rayon / settlement** (shard owner) | That area’s shard full named list. |
| **Neighborhood / microhood** | Parent shard → filter (below). |
| **Country** | Empty places. |

Partial shard failure: return ready places + `failedAreaIds`; UI must not imply complete coverage ([04](./04-selection-contract.md)).

## Neighborhood filter (correctness)

**Today (canonical loaders):** `area_id === hood.id` almost never hits → **bbox fallback ~100%** ([00](./00-findings.md)). Wrong-neighbor risk via AABB is real.

**Target path:**

1. Load parent places shard(s) + hood **verbatim** boundary.
2. **Bbox prefilter** (cheap) in Worker.
3. **Point-in-polygon** final decision in Worker against hood polygon.
4. Cache result by `hoodId` (+ pin + shard etag/hash) in L1.
5. Set `places.basis = "polygon"`. Cache key must not claim exact if PIP skipped.

**P0:** May still use bbox for hoods if PIP not shipped; then `basis = "bbox_approx"` and `placesBasisNotice` required (copy: [14](./14-open-questions.md)). Never label bbox as exact.

**P1 derived index:** CI builds `neighborhood_id` → place ids (or place→hood) from containment against canonical boundaries. Stored only under `data-derived/` (e.g. side table or field in `places/index/{rayonId}.json`). **Not** written into canonical `data/places/*`. Speeds filter; PIP remains authority if index missing.

## Shard map

`places/shards.json` maps: `rayon_key` / settlement key → `areaId` → derived paths. Deterministic URL building kills invent-404 paths ([08](./08-performance-maximization.md)).

## Unnamed places

Filter at derive (index/search omit) and at UI (`filterNamedPlaces`). Hidden, not deleted from canonical if present.
