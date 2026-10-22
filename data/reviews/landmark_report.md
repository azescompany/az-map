# Landmark enrich — jurnal

LandmarkAgent blok hesabatları. Hər tamamlanmış `LANDMARK.md` bloku üçün
bir qeyd əlavə et (tarix, key, before→after count, dedupe, conflict, validate).

**Dataset pin:** `0.2.2-national` · places total **8183** (CDN Yasamal+Nəsimi; +lokal Beyləqan)  
**Status:** Beyləqan lokal DONE · Faza 4 növbəti Ağcabədi · Bakı CDN növbəti Nərimanov

---

## Jurnal

### 2026-10-22 — beylagan (Beyləqan)

- Baseline → after: **2 → 30** (named)
- Dedupe merges **2**; disambiguate **2**; review `landmark_beylagan_disambiguate.json`
- Kateqoriya (top): education 7, shop 6, government 5, healthcare 2, services 2
- Assign: containment verified · validate + named-places **PASS**
- Git/CDN: **yox** (LandmarkAgent) — `0.2.2-national` bazasında lokal
- Qeyd: əvvəlki Faza 3–4 lokal enrich-lər `v0.2.2-national` pin ilə baseline-a qayıdıb
- Skript: `enrich_landmark_places.py --key beylagan`

### 2026-10-22 — nasimi (Nəsimi rayonu)

- Baseline → after: **177 → 3187** (named)
- Əlavə: expanded OSM+Overture taxonomy
- Dedupe: merges **238** (source_id / id / Wikidata / ≤30 m + eyni ad)
- Disambiguate: **261**; review `landmark_nasimi_disambiguate.json`
- Assign: Nəsimi polygon containment → verified
- Validate: **PASS**; `pnpm test:named-places`: **PASS**
- Git/tag/CDN: commit + push `master` + annotated tag `v0.2.2-national`;
  `DEFAULT_DATA_BASE` → `@v0.2.2-national/data/`; smoke: manifest + `places/nasimi_all.json`
- Skript: `enrich_landmark_places.py --key nasimi`
- Qeyd: yalnız Nəsimi bu pinə daxil

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
