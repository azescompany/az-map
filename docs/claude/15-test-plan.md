# 15 — Test plan

Contract and performance tests (implement later). Specs only.

## Contract tests

| # | Case | Expect |
|---|---|---|
| C1 | Every resolved `AreaSelection` | `area.center` finite; `boundary` is exact\|partial\|none |
| C2 | `PlaceSelection` | place lat/lon + `parentArea.center` + parent boundary state |
| C3 | Repeat same selection (L1 warm) | 0 network requests |
| C4 | Bakı city | Union of verified rayon shards; no aggregate file |
| C5 | Sumqayıt city-direct | Single shard; no rayon fan-out |
| C6 | Abşeron | Own + distinct settlement shards |
| C7 | Partial shard failure | `failedAreaIds` non-empty; UI incomplete |
| C8 | Abort/race | Stale response does not overwrite newer leaf |
| C9 | Neighborhood | `basis=polygon` when PIP on; never label bbox as exact |
| C10 | Verbatim boundary | Derived bytes hash == canonical (P1) |
| C11 | Center missing | `CenterMissing` / validate fail; no invent |
| C12 | Unnamed places | Not in dropdown / index |

## Measurement scripts (spec)

1. **payload_probe** — GET pinned URLs with `Accept-Encoding: br,gzip`; record raw local size vs `Content-Length` / encoding.  
2. **selection_trace** — Puppeteer/Playwright or manual DevTools export: cold, Bakı, Sumqayıt, rayon, hood, place, deep-link.  
3. **cache_hit_replay** — scripted second visit; % bytes from disk cache / SW.  
4. **hood_basis_audit** — for sample hoods: counts area_id match / bbox / polygon.  
5. **center_audit** — count verified/selectable without center (expect 0).

Outputs append to [MEASUREMENTS](./worker/MEASUREMENTS.md).

## Map budget (qualitative until device lab)

- Selecting Bakı must not freeze UI > ~200 ms without cluster (**assumed** budget; measure on mid Android).  
- Chunk `setData` if feature count > threshold (e.g. 500) — threshold **unmeasured**.
