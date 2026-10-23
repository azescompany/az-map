# GeoAtlas performance architecture (docs only)

Master prompt: [PROMPT.md](./PROMPT.md)  
Perf Worker log: [worker/README.md](./worker/README.md) (≠ root GeoAgent WORKER.md)

| Doc | Topic |
|---|---|
| [00](./00-findings.md) | Repo findings |
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
| [14](./14-open-questions.md) | Open questions |
| [15](./15-test-plan.md) | Tests + measurement specs |

**No production code in this folder.** Implementation is a later Eng phase gated by humans for tag/pin.
