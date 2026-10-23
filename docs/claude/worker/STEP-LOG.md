# STEP-LOG (append-only)

| step id | date | agent/human | status | files changed | measured vs DoD | commit hash | next action |
|---|---|---|---|---|---|---|---|
| P0-01 | 2026-10-23 | agent | done | MEASUREMENTS.md | local raw/gzip/br filled | — | — |
| P0-02 | 2026-10-23 | agent | done | cascade-react, demo App | parallel boundary∥places | — | — |
| P0-03 | 2026-10-23 | agent | done | geoatlas-data cache.ts | L1 + single-flight | — | — |
| P0-04 | 2026-10-23 | agent | done | demo App.tsx | no full catalog cold load | — | — |
| P0-05 | 2026-10-23 | agent | done | map-react clustering | cluster layers | — | — |
| P0-06 | 2026-10-23 | agent | done | demo status notice | draft AZ; Q8 open | — | Human Q8 |
| P0-H1 | — | human | planned | — | — | — | Approve baselines |
| P1-01 | 2026-10-23 | agent | done | scripts/derive_publish.py, data-derived/ | top.json ~7KB br with manifest | — | Human pin later |
| P1-02 | 2026-10-23 | agent | done | scripts/validate_derived.py | 0 errors | — | Wire CI job optional |
| P1-03 | 2026-10-23 | agent | done | geo.ts + loadPlacesForArea PIP | bbox→polygon | — | Smoke hood select |
| P1-04 | 2026-10-23 | agent | done | derive writes search/{areaId}.json | shards present | — | Loader/UI later |
| P1-H1 | — | human | planned | — | — | — | Tag + push (incl. derived if desired) |
| P1-dual | 2026-10-23 | agent | done | layout.ts, loaders, vite derived mode, all-slim | dual-read; `pnpm dev:derived` | — | Human CDN pin still open |
| P1-lazy | 2026-10-23 | agent | done | loadCatalogTop/Children, demo+cascade lazy, search index | cold ~13.5 KB br | — | Smoke `pnpm dev:derived` |
| P2-01 | 2026-10-23 | agent | done | apps/demo/sw.js + registerSw + vite plugin | L2 pin cache; PROD or VITE_GEOATLAS_SW=1 | — | Measure warm hit %; CDN pin still human |
| P1-H2 | 2026-10-23 | agent | done | DEFAULT_DATA_BASE → data-derived @ v0.3.1; data-derived tracked | pin code; push/tag pending remote | — | Smoke CDN 200 after push |
| P2-01 | — | — | planned | — | — | — | SW L2 |
| P2-02 | — | — | planned | — | — | — | National search |
| P2-03 | — | — | planned | — | — | — | Mirror/pin.json |
| P2-H1 | — | human | planned | — | — | — | Mirror decision |
