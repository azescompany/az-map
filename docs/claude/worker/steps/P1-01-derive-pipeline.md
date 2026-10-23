# Step: P1-01

## Step id and goal

- **Id:** P1-01
- **Goal:** CI derive `data-derived/` from canonical `data/`
- **Roadmap:** [11-roadmap.md](../../11-roadmap.md)
- **Spec:** [03-cdn-file-plan.md](../../03-cdn-file-plan.md)

## Preconditions

- P0-H1 approved

## What changed (files)

- _(none yet — Eng later)_

## Commands run

- _(none yet)_

## Measured results vs DoD

| Metric | Measured | DoD target | Pass? |
|---|---|---|---|
| catalog/top br size | | target 60–150 KB with manifest | |
| mapping coverage | | all consumer paths | |

## Contract / hard-rule check

| Check | OK? |
|---|---|
| Canonical data/ untouched by hand? | |
| No audit under derived? | |
| No aggregates? | |

## Data issues found

- None yet

## Risks

- File-count fan-out

## Rollback

- Keep serving canonical `data/`

## Question for human

- _

## Status

`done` (2026-10-23) — `pnpm derive:publish` → catalog/top 45 653 raw / **6 306 br**; children 93; boundaries 3486; place shards 111.
