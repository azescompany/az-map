# Step: P0-03

## Step id and goal

- **Id:** P0-03
- **Goal:** L1 LRU + single-flight; active-chain pin; repeat select 0 network
- **Roadmap:** [11-roadmap.md](../../11-roadmap.md)

## Preconditions

- [07-caching.md](../../07-caching.md)

## What changed (files)

- _(none yet)_

## Commands run

- _(none yet)_

## Measured results vs DoD

| Metric | Measured | DoD target | Pass? |
|---|---|---|---|
| repeat selection network | | 0 | |

## Contract / hard-rule check

| Check | OK? |
|---|---|
| Active chain not evicted? | |

## Data issues found

- None yet

## Risks

- Wrong cache key → stale pin data

## Rollback

- Disable L1

## Question for human

- _

## Status

`done` (2026-10-23) — `packages/geoatlas-data/src/cache.ts`; wired into manifest/areas/reviews/places index/places files/boundary; `pinActiveAreaUrls` for active chain.
