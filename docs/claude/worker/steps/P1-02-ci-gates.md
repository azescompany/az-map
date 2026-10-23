# Step: P1-02

## Step id and goal

- **Id:** P1-02
- **Goal:** Implement fail-the-build gates from 12-ci-gates.md
- **Roadmap:** [11-roadmap.md](../../11-roadmap.md)

## Preconditions

- P1-01 derive exists

## What changed (files)

- _(none yet)_

## Commands run

- _(none yet)_

## Measured results vs DoD

| Metric | Measured | DoD target | Pass? |
|---|---|---|---|
| boundary sha256 equality | | 100% | |

## Contract / hard-rule check

| Check | OK? |
|---|---|
| All gates 1–9 defined? | |

## Data issues found

- None yet

## Risks

- Flaky normalize of GeoJSON before hash

## Rollback

- Block release instead of shipping ungated

## Question for human

- _

## Status

`done` (2026-10-23) — `pnpm validate:derived` → 0 errors / 0 warnings.
