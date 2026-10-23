# Step: P0-01

## Step id and goal

- **Id:** P0-01
- **Goal:** Fill MEASUREMENTS.md with raw/gzip/br and selection traces
- **Roadmap:** [11-roadmap.md](../../11-roadmap.md)

## Preconditions

- Access to local `data/` and live jsDelivr pin URL

## What changed (files)

- _(none yet)_

## Commands run

- _(none yet)_

## Measured results vs DoD

| Metric | Measured | DoD target | Pass? |
|---|---|---|---|
| payload table | | non-empty measured | |
| request traces | | cold + key selections | |
| verified-without-center | | 0 expected | |

## Contract / hard-rule check

| Check | OK? |
|---|---|
| Boundary verbatim? | n/a (measure only) |
| Numbers labeled measured vs assumed? | |

## Data issues found

- None yet

## Risks

- CDN encoding may differ from local gzip probe

## Rollback

- n/a

## Question for human

- Approve baselines at P0-H1 after fill

## Status

`done` (2026-10-23) — local zlib table in MEASUREMENTS.md; CDN headers still unmeasured; areas br ~344 KB ⇒ slim catalog required for 60–150 KB target.
