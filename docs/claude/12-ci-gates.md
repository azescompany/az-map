# 12 — CI gates (fail the build)

Apply to **derive** job producing `data-derived/` (P1). Canonical `pnpm validate` remains GeoAgent/Landmark duty.

| # | Gate | Fail if |
|---|---|---|
| 1 | **Boundary hash equality** | sha256(derived `boundaries/{id}.geojson` geometry payload) ≠ canonical `boundary_file` bytes (normalized agreement rule documented in derive) |
| 2 | **Place coordinates + name** | Indexed place lacks finite lat/lon or empty name |
| 3 | **Verified children consistency** | Verified child missing from parent `catalog/children/{parentId}.json` OR `boundary_ref` does not resolve |
| 4 | **Verified ⇒ center** | Selectable/verified row missing center; if `geom_status=verified`, center must be inside polygon |
| 5 | **Single area ownership** | Same place id assigned to >1 `area_id` shard owner without documented dedupe rule |
| 6 | **No cross-district aggregate** | File named/role like `baki_all` / multi-rayon merge artifact present |
| 7 | **No audit on consumer path** | `reviews/`, `*_audit.*` under `data-derived/` |
| 8 | **Catalog center == detail center** | Mismatch lat/lon or status/method disagreement beyond allowlist |
| 9 | **Manifest totals match disk** | `coverage.*` / shard counts ≠ enumerated derived files |
| 10 | **Release smoke** | After HUMAN tag: HTTP 200 on pinned `catalog/top.json` + one sample `boundaries/{id}.geojson` |

Smoke is a **release** check (may run post-tag). Gates 1–9 block merge of derive output.
