# Landmark enrich — jurnal

LandmarkAgent blok hesabatları. Hər tamamlanmış `LANDMARK.md` bloku üçün
bir qeyd əlavə et (tarix, key, before→after count, dedupe, conflict, validate).

**Dataset pin:** `0.2.1-national` · places total **5145** (index)  
**Status:** Yasamal taxonomy enrich bitib · növbəti: **Nəsimi**

---

## Jurnal

### 2026-10-22 — yasamal (Yasamal rayonu) — geniş taxonomy

- Baseline → after: **211 → 2468** (named)
- Əlavə: expanded OSM+Overture taxonomy (shop, food, healthcare, education, services, …)
- Dedupe: merges **229** (source_id / id / Wikidata / ≤30 m + eyni ad); ada görə 4×Araz birləşdirilməyib
- Disambiguate: **219** eyni-ad qrup üzvü (küçə / coord / `#N`); review `landmark_yasamal_disambiguate.json`
- Assign: Yasamal polygon containment → `area_id` verified
- Validate: **PASS**; `pnpm test:named-places`: **PASS**
- Git/tag/CDN: commit `53a8446` + push `master` + annotated tag `v0.2.1-national`;
  `DEFAULT_DATA_BASE` → `@v0.2.1-national/data/`; smoke: manifest + `places/yasamal_all.json`
- Skript: `scripts/enrich_landmark_places.py` + `scripts/landmark_taxonomy.py`
- Qeyd: areas/boundaries toxunulmayıb; sintetik `baki_all` yox; force push yox

### 2026-10-22 — yasamal (əvvəlki OSM ways pass)

- Baseline → after: **170 → 211** (named ways enrich; taxonomiya dar idi)
- Skript: `scripts/enrich_landmark_yasamal.py` (superseded by `enrich_landmark_places.py`)
