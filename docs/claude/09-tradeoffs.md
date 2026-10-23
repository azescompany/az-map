# 09 — Tradeoffs

## A — Fat files + better client loading only

Keep `areas.json` + `places/{key}_all.json`. Add parallel fetch, L1, clustering, stop full catalog search load.

| Pros | Cons |
|---|---|
| Fast to ship (P0) | Cold start still ~5 MB areas (**measured** raw) |
| No derive CI | Search/national patterns stay painful |
| No consumer URL break | Ceiling below “maximum achievable” |

**Use for:** P0 immediately.

## B — Slim derived publish pipeline + best client loading (CHOSEN)

Canonical `data/` unchanged for agents; CI emits `data-derived/`; pin switches after HUMAN gate.

| Pros | Cons |
|---|---|
| Cold start / search / shard URLs tunable | Derive + CI gates cost |
| Preserves GeoAgent/Landmark workflows | Compat / dual-read period |
| Still static on jsDelivr | File-count risk if over-sharded |

**Use for:** P1 goal state. See [01](./01-executive-recommendation.md).

## C — Edge API later

Workers/R2 dynamic API in front of data.

| Pros | Cons |
|---|---|
| Server filter/aggregate | Extra hop, cost, ops |
| Can hide fan-out | Unnecessary if B + client union works |
| Regional edge control | Violates “no paid/dynamic API” goal for now |

**Justified when:** AZ RUM shows jsDelivr p95 still unacceptable after B; or product needs auth’d / personalized queries; or fan-out exceeds jsDelivr soft limits despite sharding discipline.

## Skeptical default

Do not introduce C in this plan’s P0–P2 except as a documented exit ramp in [10](./10-risks.md) / [14](./14-open-questions.md).
