# 07 — Caching

## Layers

| Layer | What | Key | Eviction |
|---|---|---|---|
| **L0 HTTP** | Browser/CDN cache for immutable pin URLs (`@vX.Y.Z-national/...`) | URL | CDN TTL; no cache-busting query strings |
| **L1 memory** | Parsed JSON/GeoJSON + hood filter results | `pin + path` or `pin + hoodId + shardHash` | Byte-budgeted LRU; **never evict active selection chain** (country→…→place) |
| **L2 Cache Storage** | SW implemented (`apps/demo/sw.js`) | `geoatlas-pin-{dataset_version}` | `SET_PIN` message purges other pin caches |
| **IndexedDB** | Only if L2 insufficient for large boundaries on weak devices | same as L2 | Justify in P2; default off |

## Single-flight

In-flight `Map<url, Promise>` dedupes concurrent fetches (Bakı union, double-click). Abort still rejects waiters that passed the same `AbortSignal`; shared flyers without abort complete and fill L1.

## Worker parse

Large JSON/GeoJSON parse and point-in-polygon run in a Web Worker. Main thread receives structured clones / transferable where applicable. Plan only — implementation is a later code step.

## Concurrency

Global fetch semaphore **4–6**. Prefetch uses lower priority and same cap.

## Compression

jsDelivr typically serves br/gzip (**assumed** until measured). Prefer accepting `br`. Record `Content-Encoding` + `Content-Length` in [MEASUREMENTS](./worker/MEASUREMENTS.md).

## Measured vs assumed

| Item | Status |
|---|---|
| L0 hit on warm second visit | assumed ≥90% bytes — **measure** P0/P2 |
| L1 active-chain pin | design rule |
| br ratios for catalog/places/boundaries | **unmeasured** |
| SW benefit on AZ networks | **unmeasured** (needs RUM) |

## Anti-patterns

- `?v=Date.now()` on pin URLs  
- Caching `@main`  
- Evicting selected boundary while user still viewing it  
- Serving `boundaries-preview` from L1 under the `boundary` contract key  
