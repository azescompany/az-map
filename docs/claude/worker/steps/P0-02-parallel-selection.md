# Step: P0-02

## Step id and goal

- **Id:** P0-02
- **Goal:** Boundary ∥ places; AbortSignal; zero sequential select-district
- **Roadmap:** [11-roadmap.md](../../11-roadmap.md)

## Preconditions

- P0-01 recommended; contract [04](../../04-selection-contract.md)

## What changed (files)

- _(none yet — Eng code later)_

## Commands run

- _(none yet)_

## Measured results vs DoD

| Metric | Measured | DoD target | Pass? |
|---|---|---|---|
| sequential deps on select-district | | 0 | |
| abort/race tests | | pass | |

## Contract / hard-rule check

| Check | OK? |
|---|---|
| Boundary fully loaded before resolve? | |
| lat/lon present? | |

## Data issues found

- None yet

## Risks

- Stale response races

## Rollback

- Revert client PR (future)

## Question for human

- _

## Status

`done` (2026-10-23) — `GeoCascadeProvider` leaf effect and demo `selectArea` use `Promise.all([loadBoundary, loadPlacesForArea])`.
