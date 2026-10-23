# Perf Worker reporting

**This is not GeoAgent [`WORKER.md`](../../../WORKER.md).** Scope: execute and log performance/architecture steps under `docs/claude/` only, unless a later Human assigns Eng code work outside this tree.

## After EVERY executed step

1. Append a row to [STEP-LOG.md](./STEP-LOG.md).  
2. Update the matching file under [steps/](./steps/) from [_TEMPLATE.md](./steps/_TEMPLATE.md).  
3. If data defects found: append [DATA-ISSUES.md](./DATA-ISSUES.md) — **do not patch data**.  
4. If measurements taken: fill [MEASUREMENTS.md](./MEASUREMENTS.md).  
5. Never perform [HUMAN-GATES.md](./HUMAN-GATES.md) actions; mark blocked and ask Human.

## Status values

`planned` | `in-progress` | `done` | `blocked`

## Step ids

Defined in [11-roadmap.md](../11-roadmap.md). Prefill files start as `planned`.
