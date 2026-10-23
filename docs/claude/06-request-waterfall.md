# 06 — Request waterfall

KB targets are **assumed** until [MEASUREMENTS](./worker/MEASUREMENTS.md). Parallel = same tick / `Promise.all`. Concurrency cap 4–6 ([07](./07-caching.md)).

## Cold start (P1 derived; P0 uses `manifest` + `areas.json`)

| # | Request | Parallel | KB target (br) | Notes |
|---|---|---|---|---|
| 1 | `manifest.json` | with 2 | tiny / unmeasured | pin check |
| 2 | `catalog/top.json` | with 1 | part of **60–150 KB** target with #1 | validate P0-01; may revise |
| 3 | (idle) `catalog/children/{countryId}.json` | after 1–2 | unmeasured | prefetch optional |

**DoD intent:** ≤ 4 requests before interactive cascade; no places shards; no `loadAllCatalogPlaces`.

## Select city — Bakı (rayon children)

| # | Request | Parallel | KB (assumed) |
|---|---|---|---|
| 1 | `catalog/children/{bakiId}.json` | — | unmeasured |
| 2 | `boundaries/{bakiId}.geojson` | ∥ places fan-out | unmeasured (~city boundary) |
| 3…N | `places/index/{rayonId}.json` × verified rayons | ∥ each other + boundary | unmeasured; N≈12 Bakı |

Places = union; `failedAreaIds` if any 404. Prefetch: hover rayon → that shard + boundary.

## Select city-direct — Sumqayıt

| # | Request | Parallel |
|---|---|---|
| 1 | `catalog/children/{sumqayitId}.json` | ∥ 2,3 |
| 2 | `boundaries/{sumqayitId}.geojson` | ∥ |
| 3 | `places/index/{sumqayitId}.json` | ∥ |

No rayon fan-out. KB: boundary + one places shard (**unmeasured**; raw places ~1.3 MB).

## Select country→rayon — Abşeron

| # | Request | Parallel |
|---|---|---|
| 1 | children of Absheron | — |
| 2 | `boundaries/{absheronId}.geojson` | ∥ places |
| 3 | `places/index/{absheronId}.json` | ∥ |
| 4+ | distinct settlement shards (Masazır, Xırdalan, …) | ∥ if distinct files |

## Select district (rayon)

| # | Request | Parallel |
|---|---|---|
| 1 | `boundaries/{rayonId}.geojson` | ∥ 2 |
| 2 | `places/index/{rayonId}.json` | ∥ 1 |
| 3 | `catalog/children/{rayonId}.json` | ∥ or after | hood dropdown |

**DoD:** zero sequential dependency between boundary and places on select-district.

## Select neighborhood

| # | Request | Parallel |
|---|---|---|
| 1 | `boundaries/{hoodId}.geojson` | ∥ 2 (parent shard if not L1) |
| 2 | parent `places/index/{rayonId}.json` | ∥ 1 if miss |
| — | Worker: bbox → PIP | local | `basis=polygon` (P1) or `bbox_approx` (P0) |

## Select place

| # | Request | Parallel |
|---|---|---|
| 1 | Ensure parent `AreaSelection` (boundary + center) | reuse L1 |
| 2 | Place row from loaded shard / search hit | usually 0 network |

Contract: [04](./04-selection-contract.md) `PlaceSelection.parentArea` required.

## Deep-link to place (`?placeId=`)

| # | Request | Parallel |
|---|---|---|
| 1 | manifest + catalog/top (if cold) | — |
| 2 | Resolve place via `search/{areaId}` or shard map from deep-link metadata | — |
| 3 | Parent boundary ∥ parent places index | ∥ |
| 4 | Ancestors children catalogs as needed for cascade UI | prefetch |

Avoid downloading all national shards.

## Prefetch rules

- Hover/focus verified child → children catalog + boundary + places index (priority below active select).
- Never prefetch all Bakı rayons on country select.
- Cancel prefetch on rapid cascade change (`AbortSignal`).
