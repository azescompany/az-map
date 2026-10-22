# Landmark enrich — jurnal

LandmarkAgent blok hesabatları. Hər tamamlanmış `LANDMARK.md` bloku üçün
bir qeyd əlavə et (tarix, key, before→after count, dedupe, conflict, validate).

**Dataset pin:** `0.2.2-national` · places total **9822** (lokal Sumqayıt enrich daxil)  
**Status:** Sumqayıt lokal DONE · Faza 2 növbəti Masazır · Git/CDN yox

---

## Jurnal

### 2026-10-22 — sumqayit (Sumqayıt şəhəri)

- Baseline → after: **57 → 1724** (named)
- Mənbə: OSM named nodes **1241** + Overture **492** · yalnız **city polygon** daxilində
- Dedupe merges **66**; disambiguate **352**; review `landmark_sumqayit_disambiguate.json`
- Children-first assign: **76** verified uşaq geom · uşağa **1171** · city-only **547** · conflict **6**
  (`landmark_sumqayit_reassign.json`)
- Kateqoriya (top): shop 739, food 373, education 159, healthcare 129, services 73
- Validate + named-places: **PASS**
- Git/CDN: **yox** (LandmarkAgent)
- Skript: `enrich_landmark_places.py --key sumqayit`
- Qeyd: areas/boundaries toxunulmayıb; parent uydurma yox

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
- Git/tag/CDN: commit `21185e2` + annotated tag `v0.2.2-national` (lokal);
  `DEFAULT_DATA_BASE` → `@v0.2.2-national/data/`;
  **push + CDN 200 smoke BLOKER** — agent mühitində GitHub auth dialoqu ləğv olundu;
  insan: `git push origin master` && `git push origin v0.2.2-national` → jsDelivr smoke
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
