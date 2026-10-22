# Hierarchy rules (pilot)

Working tree + Bakı extract procedure: see root [`Hierarchy.md`](../Hierarchy.md).

1. **Never invent** parents, names, or polygons.
2. **Never merge by name alone** — require Wikidata, stable source ID, and/or geometry agreement.
3. **Admin hierarchy ≠ containment** — both are stored; conflicts are reviewed.
4. **Bakı districts** come from OSM administrative relations; Overture `parent_division_id` for Bakı region is incomplete and is not the sole authority.
5. **2-ci Alatava** may be a verified Yasamal child only when Overture parent and geometry containment agree.
6. **1-ci Alatava** is under **Nəsimi**, not Yasamal — do not present it as a verified Yasamal child.
7. Cascading dropdowns expose only `parent_status=verified` children.
8. `geom_status=partial` / `conflict` must be visible in the UI.
9. `geom_status=verified` requires a real source polygon, valid non-empty geometry, CRS EPSG:4326, boundary `source_ref`, and an interior center within the polygon. Validity alone is not official accuracy.
10. Centers use interior representative points when the boundary is verified. Label/node points are `center_status=label_fallback`, never presented as official geographic centers.
11. **Places cascade:** city with verified rayon children → union of those children’s existing `places/{key}_all.json` (dedupe by `place.id`); do not invent `baki_all.json`. Rayon → that file’s full list. Neighborhood / settlement → filter parent file by `area_id`, else bbox. Country → empty. Unnamed places stay hidden via `filterNamedPlaces`.
12. Extract `area_id` stays rayon-scoped; load/filter implements hierarchy for UI — no mass re-assign of place parents in this phase.

## Pilot tree (verified UI path)

```
Azərbaycan
 └── Bakı
      ├── Yasamal rayonu
      │    ├── 2-ci Alatava (if verified)
      │    ├── Yeni Yasamal (if verified)
      │    └── …
      ├── Nəsimi rayonu
      │    └── 1-ci Alatava
      └── other Bakı districts (OSM)
```
