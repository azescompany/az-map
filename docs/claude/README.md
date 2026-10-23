# GeoAtlas performance architecture

Master prompt: [PROMPT.md](./PROMPT.md)  
**Closeout:** [CLOSEOUT.md](./CLOSEOUT.md) (2026-10-23 — Option B shipped)  
Perf Worker log: [worker/README.md](./worker/README.md) (≠ root GeoAgent WORKER.md)

| Doc | Topic |
|---|---|
| [CLOSEOUT](./CLOSEOUT.md) | **Final status** |
| [00](./00-findings.md) | Repo findings (baseline → shipped) |
| [01](./01-executive-recommendation.md) | Option B chosen |
| [02](./02-architecture.md) | Components + mermaid |
| [03](./03-cdn-file-plan.md) | `data-derived/` tree |
| [04](./04-selection-contract.md) | selectEntity contract |
| [05](./05-place-sources-and-neighborhoods.md) | Union + hood PIP |
| [06](./06-request-waterfall.md) | Request tables |
| [07](./07-caching.md) | L0/L1/L2 |
| [08](./08-performance-maximization.md) | Ranked optimizations |
| [09](./09-tradeoffs.md) | A/B/C |
| [10](./10-risks.md) | Risks |
| [11](./11-roadmap.md) | P0/P1/P2 |
| [12](./12-ci-gates.md) | Fail-the-build |
| [13](./13-what-not-to-do.md) | Negatives |
| [14](./14-open-questions.md) | Questions (resolved / deferred) |
| [15](./15-test-plan.md) | Tests + measurement specs |

Docs in this folder are the architecture record. Implementation lives in `packages/`, `apps/demo`, `scripts/derive_publish.py`, `data-derived/`.
