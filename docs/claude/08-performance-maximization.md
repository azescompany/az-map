# 08 — Performance maximization (ranked)

Git + jsDelivr only. Impact/cost are qualitative until measured. **needs measurement** = do not treat as fact.

| Rank | Optimization | Impact | Cost | Risk | How to measure |
|---|---|---|---|---|---|
| 1 | **Slim catalog split** (`catalog/top` vs fat `areas.json`) | Critical cold start | Derive CI | Drift if CI weak | br size cold path; TTI |
| 2 | **Stop `loadAllCatalogPlaces` on search** | Critical cold/search | Demo/search UX change | Incomplete search until scoped index | Request count; bytes on load |
| 3 | **Parallel boundary ∥ places** on select | High selection latency | Small client change | Race/abort bugs | time-to-boundary + time-to-places |
| 4 | **Single-flight + L1 LRU (active-chain pin)** | High repeat nav | Client | Stale pin if key wrong | cache hit %; 0-network reselect |
| 5 | **Per-area places sharding + deterministic URLs** | High (kill 404 invent) | Derive | File-count pressure | 404 rate; fan-out N |
| 6 | **Worker parse + PIP for hoods** | High correctness + jank | Worker code | PIP cost on complex polys | main-thread blocking; filter ms |
| 7 | **MapLibre native clustering + chunked setData** | High UI jank (7k Bakı) | Map code | Cluster UX | frame time; FPS on select city |
| 8 | **Scoped then national search index** (az normalize əıöüçşğ) | High search bytes | CI derive | Normalize bugs | search bytes; recall sample |
| 9 | **Derived indexes in CI** (`neighborhood_id`, shards map) | Medium–high | CI | Drift | hood basis=polygon rate |
| 10 | **Hover prefetch** (child boundary/places) | Medium perceived | Bandwidth | Waste on rapid change | prefetch abort rate; TTFB feel |
| 11 | **HTTP/2 multiplexing + request budget 4–6** | Medium | Client | Starvation if mis-tuned | waterfalls in DevTools |
| 12 | **Immutable tag cache-key stability** | Medium long-term | Process | Stale app on old pin | accidental `@main` audits |
| 13 | **Avoid cache-busting query strings** | Medium | Discipline | — | Lighthouse cache |
| 14 | **Boundary byte-identity gate** (canonical vs derived) | Medium trust | CI | Release block | sha256 equality 100% |
| 15 | **SW L2 pin-namespaced cache** | Medium warm revisit | P2 eng | SW bugs | warm ≥90% bytes |
| 16 | **boundaries-preview separate** (never as boundary) | Low–medium map first paint | Derive | Mis-wire to contract | contract tests |
| 17 | **Slim places index vs detail** | Medium POI bytes | Derive | Missing fields for UI | places index br size |
| 18 | **Mirror failover (R2 etc.)** | Situational | Ops/cost | Premature | AZ RUM p95; only if justified |
| 19 | **pin.json data-only rollout** | Process | P2 | Pin confusion | deploy without app bump |
| 20 | **Remove audit files from consumer path** | Low bytes / clarity | Packaging | — | CDN path audit |

## Top 10 (execution priority)

1. Slim catalog split  
2. Stop full-catalog place fetch  
3. Parallel selection loads  
4. Single-flight + L1  
5. Deterministic per-area URLs / shards  
6. Worker parse + PIP  
7. MapLibre clustering  
8. Scoped search index  
9. CI derived indexes  
10. Hover prefetch  

Details for phasing: [11](./11-roadmap.md). Tradeoffs: [09](./09-tradeoffs.md).
