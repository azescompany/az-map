# Human gates (agents must not perform)

| Gate | Action | Accountable role | Status |
|---|---|---|---|
| P0-H1 | Approve P0 measurement baselines / budget revision (areas alone ~344 KB br — slim catalog required for 60–150 KB) | Data lead + Eng lead | open — awaiting sign-off |
| P1-H1 | Create annotated git tag `vX.Y.Z-national` | **Data lead** | open |
| P1-H1b | `git push` tag (+ commit if needed) | **Data lead** / maintainer | open |
| P1-H2 | CDN pin to derived (`DEFAULT_DATA_BASE` → `data-derived/` @ v0.3.1-national) | **Eng lead** / agent (user-authorized 2026-10-23) | code done — push/tag if not yet on remote |
| P2-H1 | Decide mirror and/or `pin.json` data-only rollout | Eng lead + Human | open |
| Copy | Approve az/en strings for partial / bbox_approx ([14](../14-open-questions.md)) | Product / Data lead | open |

Named individuals: see open questions Q1–Q2 in [14-open-questions.md](../14-open-questions.md).
