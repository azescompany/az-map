# Step: P0-04

## Step id and goal

- **Id:** P0-04
- **Goal:** Remove default loadAllCatalogPlaces from cold start/search
- **Roadmap:** [11-roadmap.md](../../11-roadmap.md)

## Preconditions

- Search UX alternative agreed (scoped)

## What changed (files)

- _(none yet)_

## Commands run

- _(none yet)_

## Measured results vs DoD

| Metric | Measured | DoD target | Pass? |
|---|---|---|---|
| cold start place shard fetches | | 0 | |
| cold start request count | | ≤ 4 | |

## Contract / hard-rule check

| Check | OK? |
|---|---|
| Unnamed still hidden? | |

## Data issues found

- None yet

## Risks

- Search regression until P1-04

## Rollback

- Feature flag restore catalog load

## Question for human

- Accept scoped-only search until P1?

## Status

`done` (2026-10-23) — demo cold start no longer calls `loadAllCatalogPlaces`; `searchPlaces` accumulates from selections.
