# Hierarchy rules (pilot)

1. **Never invent** parents, names, or polygons.
2. **Never merge by name alone** — require Wikidata, stable source ID, and/or geometry agreement.
3. **Admin hierarchy ≠ containment** — both are stored; conflicts are reviewed.
4. **Bakı districts** come from OSM administrative relations; Overture `parent_division_id` for Bakı region is incomplete and is not the sole authority.
5. **2-ci Alatava** may be a verified Yasamal child only when Overture parent and geometry containment agree.
6. **1-ci Alatava** is under **Nəsimi**, not Yasamal — do not present it as a verified Yasamal child.
7. Cascading dropdowns expose only `parent_status=verified` children.
8. `geom_status=partial` / `conflict` must be visible in the UI.

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
