# 10 — Risks

| Risk | Mitigation | Owner |
|---|---|---|
| **Stale pin** — app points at old tag | Manifest version badge; pin PR checklist; never `@main` | Eng lead |
| **404 / purged tag** | Immutable tags; smoke 200 on release; keep prior pins | Data lead + Eng |
| **jsDelivr file/repo limits** — notes disagree (~20 MB vs ~50 MB); confirm official docs | Keep files ≪ 20 MB; no mega-aggregates; confirm before large boundary | Eng lead ([14](./14-open-questions.md)) |
| **File-count fan-out** — thousands of `{areaId}` files | Shard places at rayon/settlement; children catalogs only where needed; monitor soft limits | Perf + Data |
| **Bakı union fan-out** (~12 shards) | Concurrency 4–6; L1; prefetch limited; `failedAreaIds` honesty | Eng |
| **Map jank vs network** | Clustering; chunked setData; Worker parse | Eng |
| **Derived-data drift** | CI hash equality canonical↔derived boundary; center catalog==detail | CI / Data |
| **Bbox wrong-parent** | PIP + optional neighborhood index; `bbox_approx` notice | Eng + Data |
| **Partial union shown as complete** | `failedAreaIds` + UI banner | Eng |
| **Boundary precision temptation** (simplify as boundary) | Hard rule; preview path only; contract tests | All |
| **Politically sensitive geometry/naming** | Hierarchy provenance; no invent; human review before tag | Data lead |
| **Memory growth on mobile** | L1 byte budget; cluster; don’t hold all Bakı detail+index forever | Eng |
| **Perf Worker confused with GeoAgent** | Docs-only scope; [PROMPT](./PROMPT.md) | PerfDocsArchitect |

Each data defect found during work → [DATA-ISSUES](./worker/DATA-ISSUES.md) (**NOT patched** by Perf agent).
