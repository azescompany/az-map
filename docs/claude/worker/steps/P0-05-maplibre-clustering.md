# Step: P0-05

## Step id and goal

- **Id:** P0-05
- **Goal:** Native clustering + chunked setData for large place sets
- **Roadmap:** [11-roadmap.md](../../11-roadmap.md)

## Preconditions

- Bakı place count known from index

## What changed (files)

- _(none yet)_

## Commands run

- _(none yet)_

## Measured results vs DoD

| Metric | Measured | DoD target | Pass? |
|---|---|---|---|
| frame/jank on Bakı select | | no multi-second freeze | |

## Contract / hard-rule check

| Check | OK? |
|---|---|
| Clustering does not drop selection lat/lon? | |

## Data issues found

- None yet

## Risks

- Cluster UX hides individual POIs until zoom

## Rollback

- Cluster off

## Question for human

- _

## Status

`done` (2026-10-23) — places GeoJSONSource `cluster: true`; cluster circle + count; click expands zoom; unclustered filter on places-circle.
