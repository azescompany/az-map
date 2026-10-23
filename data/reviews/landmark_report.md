# Landmark enrich — jurnal

LandmarkAgent blok hesabatları. Hər tamamlanmış `LANDMARK.md` bloku üçün
bir qeyd əlavə et (tarix, key, before→after count, dedupe, conflict, validate).

**Dataset pin:** `0.3.0-national` · places total **40891**  
**Status:** Faza 1–4 DONE · pin `DEFAULT_DATA_BASE` → `@v0.3.0-national` · deploy (push/tag) gözlənilir

---

## Jurnal

### 2026-10-23 — Faza 1 paket (Bakı qalan 10 rayon)

| key | before → after |
|-----|----------------|
| narimanov | 164 → 2915 |
| nizami_baki | 80 → 1203 |
| binagadi | 169 → 2240 |
| sabail | 308 → 2625 |
| xetai | 172 → 1917 |
| sabuncu | 254 → 2308 |
| surakhani | 169 → 1208 |
| xezer | 263 → 2031 |
| pirallahi | 35 → 168 |
| qaradag | 112 → 1013 |

- Index total **40891** · dataset `0.3.0-national`
- Validate + named-places: **PASS**
- Skript: `enrich_landmark_places.py --key <rayon>`

### 2026-10-23 — Faza 4 paket (bütün digər rayonlar)

- Xızı→Şərur + Beyləqan yenidən: named places **~12.3k → 24.9k** (index total)
- Validate + named-places: **PASS** · Git/CDN: **yox**
- Skript: `enrich_landmark_places.py --key <rayon>`
- Qeyd: Qarabağ / Naxçıvan MR-də mənbə nazik — count kiçik qala bilər

### 2026-10-23 — Faza 3 paket (Mingəçevir → Naxçıvan)

| key | before → after | OSM+Ov | merges | disambig |
|-----|----------------|--------|--------|----------|
| mingachevir | 20 → 348 | 238+115 | 25 | 47 |
| shirvan | 10 → 496 | 435+61 | 10 | 113 |
| naftalan | 2 → 110 | 91+22 | 5 | 11 |
| yevlax | 4 → 180 | 146+34 | 4 | 14 |
| lankaran | 15 → 181 | 59+124 | 17 | 14 |
| sheki | 17 → 535 | 385+157 | 24 | 69 |
| nakhchivan | 35 → 254 | 93+165 | 39 | 24 |

- Validate + named-places: **PASS** · Git/CDN: **yox**
- Skript: `enrich_landmark_places.py --key <city>`

### 2026-10-23 — gence_nizami (Gəncə — Nizami)

- Baseline → after: **31 → 398** (named)
- OSM **106** + Overture **299** · yalnız Nizami rayon polygon
- Dedupe **38**; disambiguate **36**; `landmark_gence_nizami_disambiguate.json`
- Kateqoriya (top): food 107, shop 68, education 61, services 32, tourism 26
- Validate + named-places: **PASS** · Git/CDN: **yox**
- Skript: `enrich_landmark_places.py --key gence_nizami`

### 2026-10-23 — gence_kapaz (Gəncə — Kəpəz)

- Baseline → after: **14 → 185** (named)
- OSM **40** + Overture **148** · yalnız Kəpəz rayon polygon
- Dedupe **17**; disambiguate **13**; `landmark_gence_kapaz_disambiguate.json`
- Kateqoriya (top): food 45, shop 36, education 34, healthcare 21
- Validate + named-places: **PASS** · Git/CDN: **yox**
- Skript: `enrich_landmark_places.py --key gence_kapaz`

### 2026-10-22 — absheron children (Abşeron rayonu uşaqları)

- Metod: tək OSM+Overture scan · children-first PIP · **ayrı** `places/{key}_all.json`
- Exclude: Masazır + Xırdalan (əvvəlki bloklar)
- Uşaqlara **767** · residual `absheron_all` **305** · conflict **0**
- Top: Novxanı 189, Saray 114, Mehdiabad 76, Qobu 68, Digah 50, Goradil 46
- Boş (named POI yox): Novxanı Bağları, Saray Bağları, Çaylı
- Review: `landmark_absheron_children_enrich.json`
- Validate + named-places: **PASS** · Git/CDN: **yox**
- Skript: `enrich_absheron_children_places.py`

### 2026-10-22 — xirdalan (Xırdalan)

- Baseline → after: **21 → 1268** (named)
- OSM **1106** + Overture **177** · yalnız Xırdalan polygon
- Dedupe **36**; disambiguate **353**; `landmark_xirdalan_disambiguate.json`
- Children-first: **8** verified uşaq · uşağa **383** · parent-only **885** · conflict **0**
  (`landmark_xirdalan_reassign.json`)
- Kateqoriya (top): shop 734, food 214, healthcare 85, education 76
- Validate + named-places: **PASS** · Git/CDN: **yox**
- Skript: `enrich_landmark_places.py --key xirdalan`

### 2026-10-22 — masazir (Masazır)

- Baseline → after: **5 → 263** (named)
- OSM **224** + Overture **44** · yalnız Masazır polygon
- Dedupe **10**; disambiguate **70**; `landmark_masazir_disambiguate.json`
- Verified uşaq geom **0** → hamısı parent containment · conflict **0**
  (`landmark_masazir_reassign.json`)
- Kateqoriya (top): shop 148, food 50, education 25, healthcare 15
- Validate + named-places: **PASS** · Git/CDN: **yox**
- Skript: `enrich_landmark_places.py --key masazir`

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
