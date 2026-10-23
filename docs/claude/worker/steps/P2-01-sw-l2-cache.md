# Step: P2-01

## Step id and goal

- **Id:** P2-01
- **Goal:** Service Worker Cache Storage namespaced by pin; old-pin eviction
- **Roadmap:** [11-roadmap.md](../../11-roadmap.md)

## Preconditions

- P1 pin on derived root stable

## What changed (files)

- _(none yet)_

## Commands run

- _(none yet)_

## Measured results vs DoD

| Metric | Measured | DoD target | Pass? |
|---|---|---|---|
| warm second visit bytes from cache | | ≥ 90% | |

## Contract / hard-rule check

| Check | OK? |
|---|---|
| Cache namespaced by dataset_version? | |

## Data issues found

- None yet

## Risks

- SW update bugs; stale derived

## Rollback

- Unregister SW

## Question for human

- _

## Status

`done` (2026-10-23) — `sw.js` cache-first for same-origin catalog/places/boundaries + jsDelivr az-map pins; `SET_PIN` purges old `geoatlas-pin-*`; register via `registerSw.ts` (PROD or `VITE_GEOATLAS_SW=1`).
