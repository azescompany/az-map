# Step: P1-04

## Step id and goal

- **Id:** P1-04
- **Goal:** Derive search/{areaId}.json with Azerbaijani normalization
- **Roadmap:** [11-roadmap.md](../../11-roadmap.md)

## Preconditions

- P1-01

## What changed (files)

- _(none yet)_

## Commands run

- _(none yet)_

## Measured results vs DoD

| Metric | Measured | DoD target | Pass? |
|---|---|---|---|
| search bytes vs full catalog | | much smaller | |

## Contract / hard-rule check

| Check | OK? |
|---|---|
| Named only? | |
| lat/lon in search rows? | |

## Data issues found

- None yet

## Risks

- Normalize misses ə ı ö ü ç ş ğ

## Rollback

- Filter loaded shard only

## Question for human

- _

## Status

`done` (2026-10-23) — derive emits `search/{areaId}.json` per shard; UI/loader wiring deferred until pin switch.
