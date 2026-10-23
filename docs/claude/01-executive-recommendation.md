# 01 — Executive recommendation

Index: [README](./README.md) · Prompt: [PROMPT](./PROMPT.md)

**Chosen option: B — slim derived publish pipeline from Git + best client loading.**

Keep canonical Git layout (`areas/areas.json`, `places/{key}_all.json`, `boundaries/*` via `boundary_file`) as GeoAgent/Landmark output. At release, CI **derives** a consumer tree (recommend `data-derived/` in tag, or release-only artifact mirrored to the same jsDelivr path convention) with slim catalogs, per-area shards, and search indexes. Clients use pinned immutable tags only; L1 memory (+ later L2 SW) and parallel `selectEntity`; MapLibre clustering; stop full-catalog place fetch on cold start.

**Why not A (fat files + better loading only):** Client parallel/cache helps, but cold start still pays ~5 MB `areas.json` and search still fans out every shard. Ceiling is too low for “maximum achievable” on Git+jsDelivr.

**Why not C (edge API) yet:** Adds hop, cost, and ops for static JSON already CDN-friendly. Revisit only if RUM shows jsDelivr p95 unacceptable after B, or query patterns need server aggregation beyond client union ([09](./09-tradeoffs.md)).

**Phasing:** P0 = measure + client loading (no tree migration required). P1 = derive tree + CI gates + neighborhood polygon filter. P2 = SW cache, national search, optional mirror/`pin.json`. Human gates for tag/push/`DEFAULT_DATA_BASE` ([worker/HUMAN-GATES.md](./worker/HUMAN-GATES.md)).

**Non-negotiable:** Selected entity always returns verbatim full boundary + lat/lon; no `baki_all`; no `@main`.
