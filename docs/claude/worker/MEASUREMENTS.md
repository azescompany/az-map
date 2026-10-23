# Measurements baseline

Local compress via Node `zlib` (gzip level 9, default brotli). **CDN Content-Encoding / Content-Length:** unmeasured this run (probe deferred).

## Payload table

| file | raw bytes | gzip | br | Content-Encoding | Content-Length (CDN) | note |
|---|---|---|---|---|---|---|
| data/manifest.json | 1871 | 918 | 773 | unmeasured | unmeasured | measured local 2026-10-23 |
| data/areas/areas.json | 5081982 | 431226 | 344331 | unmeasured | unmeasured | ~336 KB br — cold-start budget 60–150 KB **misses without slim catalog** |
| data/places/index.json | 25096 | 5725 | 4966 | unmeasured | unmeasured | |
| data/places/nasimi_all.json | 2382795 | 281015 | 234878 | unmeasured | unmeasured | |
| data/places/yasamal_all.json | 1857181 | 219651 | 183081 | unmeasured | unmeasured | |
| data/places/sumqayit_all.json | 1269964 | 141289 | 107049 | unmeasured | unmeasured | |
| data/boundaries/country_AZ.geojson | 1285386 | 123642 | 80279 | unmeasured | unmeasured | |
| data/boundaries/rayon_gazakh.geojson | 171883 | 17400 | 10645 | unmeasured | unmeasured | large rayon sample |
| data/boundaries/rayon_yasamal.geojson | 14285 | 1641 | 1146 | unmeasured | unmeasured | |

**Cold-start today (canonical):** manifest + areas + places/index + reviews ≈ areas dominates (**~344 KB br** areas alone).

**P1 derived (measured 2026-10-23 after `pnpm derive:publish`):**

| file | raw | br |
|---|---|---|
| data-derived/catalog/top.json | 45653 | **6306** |
| data-derived/manifest.json | 2211 | **889** |
| **sum top+manifest** | | **~7195 br** |
| data-derived/catalog/all-slim.json | 2024844 | **247936** |

Target 60–150 KB for **top+manifest only**: **PASS** (~7 KB br).  

**Lazy cold start (implemented):** manifest + `catalog/top.json` + country `children` ≈ **13.5 KB br** (**measured** components: top 6306 + country children 6274 + manifest 889). Bakı children add ~1.3 KB br on select.

## Request trace (design / post P0-02–04)

| scenario | # requests (design) | sequential deps? | notes |
|---|---|---|---|
| cold start | 4 (manifest, areas, reviews, places/index) — **no** all place shards | parallel Promise.all | P0-04 removes loadAllCatalogPlaces |
| select district | 2 (boundary ∥ places) | **0** sequential | P0-02 |
| select Bakı | 1+ boundary + up to ~12 place shards | places parallel among themselves | fan-out |
| select Sumqayıt | boundary ∥ 1 places shard | 0 | |
| repeat select (L1 warm) | 0 network | — | P0-03 cache |

Manual DevTools traces: fill after demo smoke.

## Cache-hit table

| visit | % bytes from cache | L1 hits | L2/SW | notes |
|---|---|---|---|---|
| first | 0 | miss | n/a | |
| second (same session) | high for same URLs | yes (L1) | n/a P2 | implemented in `@geoatlas/data` cache |

## Neighborhood basis table

| hood | area_id match count | bbox count | polygon count | notes |
|---|---|---|---|---|
| (typical Bakı hood) | ~0 | ~100% of loads | 0 until P1-03 | by design: area_id=rayon |

## Verified / selectable without center

| count | query / method | expect |
|---|---|---|
| **0** | areas.json: center lat/lon null | 0 |

areas count **3486**; `missingCenter=0` (**measured**).
