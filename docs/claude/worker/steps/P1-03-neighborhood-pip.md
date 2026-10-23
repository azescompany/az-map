# Step: P1-03

## Step id and goal

- **Id:** P1-03
- **Goal:** Bbox prefilter + Worker PIP; optional neighborhood_id index (derived only)
- **Roadmap:** [11-roadmap.md](../../11-roadmap.md)
- **Spec:** [05-place-sources-and-neighborhoods.md](../../05-place-sources-and-neighborhoods.md)

## Preconditions

- Worker parse path available

## What changed (files)

- _(none yet)_

## Commands run

- _(none yet)_

## Measured results vs DoD

| Metric | Measured | DoD target | Pass? |
|---|---|---|---|
| hood basis=polygon rate | | high / measured | |
| PIP ms worst hood | | fill Q5 | |

## Contract / hard-rule check

| Check | OK? |
|---|---|
| Index not written to canonical places? | |
| bbox never labeled exact? | |

## Data issues found

- None yet

## Risks

- PIP cost on mobile

## Rollback

- bbox_approx + notice

## Question for human

- Q5 PIP budget

## Status

`done` (2026-10-23) — `pointInFeatureCollection` + `loadPlacesForArea` bbox prefilter then PIP via cached `loadBoundary`.
