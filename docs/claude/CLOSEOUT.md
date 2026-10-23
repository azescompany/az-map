# Perf architecture closeout (2026-10-23)

**Verdict:** Option B shipped. Agent engineering complete. Human gates closed below; ops follow-ups deferred (not blockers).

## Shipped

| Track | Deliverable |
|---|---|
| P0 | Measure, parallel select, L1+single-flight, no full-catalog cold load, MapLibre clustering, boundary notices |
| P1 | `data-derived/`, dual-read loaders, lazy catalog (~13.5 KB br cold), PIP hood filter, CI/validate gates, pin `@v0.3.x-national` |
| P2 | SW L2 pin cache, national search (lazy), `pin.json`, Worker JSON parse ≥48 KiB, hover/↑↓ prefetch |

**Hard rules held:** verbatim boundary + lat/lon; no `baki_all`; no `@main`.

## Human decisions (recorded)

| Gate | Decision |
|---|---|
| P0-H1 | Baselines accepted. Cold budget **only** with derived lazy pin (not fat `areas.json`). |
| P1-H1 / H1b | Tags `v0.3.1-national` / `v0.3.2-national` pushed (user-authorized). |
| P1-H2 | `DEFAULT_DATA_BASE` → derived CDN pin; smoke 200. |
| P2-H1 | Adopt `pin.json`. **No** day-1 mirror — revisit only if AZ RUM demands. |
| Copy Q8 | Working copy approved (az/en drafts in [14](./14-open-questions.md); wired in demo). |

## Deferred (optional, not open roadmap work)

- AZ ISP RUM p50/p95 → jsDelivr; CDN Content-Length probe  
- Formal warm-visit ≥90% cache-hit DevTools table  
- Mobile PIP ms profiling (Q5)  
- Named individuals for Q1/Q2 (roles already clear: Data lead / Eng lead)

## Where to look

- Log: [worker/STEP-LOG.md](./worker/STEP-LOG.md)  
- Gates: [worker/HUMAN-GATES.md](./worker/HUMAN-GATES.md)  
- Numbers: [worker/MEASUREMENTS.md](./worker/MEASUREMENTS.md)  
- Roadmap: [11-roadmap.md](./11-roadmap.md)  
