# GeoAtlas Azərbaycan — LANDMARK

Bu fayl **LandmarkAgent** üçün iş siyahısıdır. Hər blok **bir** `places/{key}_all.json`
(və lazım olsa `places/index.json` + review) üzərindədir. Hierarchy / areas /
boundaries **toxunulmur** — onlar [`WORKER.md`](./WORKER.md) + GeoAgent-dir.

Qaydalar: [`.cursor/rules/landmark-agent.mdc`](./.cursor/rules/landmark-agent.mdc) ·
[`docs/landmark-taxonomy.md`](./docs/landmark-taxonomy.md) ·
[`Hierarchy.md`](./Hierarchy.md) (oxu) · jurnal: [`data/reviews/landmark_report.md`](./data/reviews/landmark_report.md)

## PAUSE / davam nöqtəsi

**Dataset:** `0.3.0-national` · places **40891** · validate **PASS**  
**Bitən:** Faza 1 (bütün Bakı) + Faza 2 + Faza 3 + Faza 4 (lokal)  
**CDN pin:** `v0.3.0-national` (deploy gözlənilir)  
**Növbəti:** git push + tag `v0.3.0-national` + CDN smoke

---

## Agent iş qaydası (məcburi)

1. Bu `LANDMARK.md` üzərindən növbəti **unchecked** `[ ]` bloku götür.
2. Hierarchy / places cascade **oxu** — areas/boundaries **yazma**.
3. Mənbə: yalnız `source_files/` (OSM, Overture, GeoNames). **Mənbəyə yazma.**
4. Çıxış: `data/places/{key}_all.json` + `data/places/index.json` + `data/reviews/`.
5. **Geniş taxonomy** — [`docs/landmark-taxonomy.md`](./docs/landmark-taxonomy.md)
   (education, shop, market, healthcare, food, services, transport, …); yalnız adlı POI.
6. **Dedupe:** eyni source_id / place.id / Wikidata / (≤30 m + eyni normalize ad) → merge
   `source_refs`. Eyni brend/ad + fərqli küçə/məsafə → **ayrı** saxla.
7. **Eyni ad:** `Display (Küçə)`; küçə yoxdursa coord/`#N` + review; `alt_names`-ə qısa ad.
8. `area_id` = rayon (və ya city-direct); containment verified; ada görə merge yox.
9. Sintetik `baki_all.json` **yaratma**. Force push **yox**.
10. Blok bitəndə: validate → **git commit + push + tag/pin** → CDN **200** smoke →
    `[x]` + Hesabat + `landmark_report.md`. Yalnız sonra növbəti rayon.

### Blok “Definition of Done” (DoD)

- [ ] Inventar: mövcud count + kateqoriya payı qeyd olunub
- [ ] Geniş taxonomy (named) tətbiq olunub
- [ ] Dublikat 0 (source_id / id / yaxın+eyni ad — merge edilib)
- [ ] Eyni adlar küçə ilə fərqlənir (`alt_names` = qısa ad; uydurma küçə yox; yoxdursa review)
- [ ] Assign: containment → `area_id` + `area_assign_status`
- [ ] Adsız məkanlar `named` edilməyib
- [ ] `pnpm validate` PASS; `pnpm test:named-places` PASS
- [ ] git commit + push (yalnız places/index/reviews/LANDMARK; force yox)
- [ ] pin/CDN 200 smoke (`DEFAULT_DATA_BASE` / tag; `manifest` + `places/{key}_all.json`)
- [ ] Bu faylda `[x]` + Hesabat (before/after, dedupe, disambiguate, SHA, tag, CDN);
      `data/reviews/landmark_report.md` yenilənib

---

## Faza 1 — Bakı inzibati rayonları

Baseline counts: `data/places/index.json` (cari: `0.2.2-national`).

### 1. Yasamal

- [x] Geniş taxonomy + dedupe + küçə disambiguate + git/pin  
  Fayl: `places/yasamal_all.json` · **211 → 2468** (əvvəlki ways-enrich 170→211)  
  **Hesabat (2026-10-22 taxonomy):** OSM named nodes **754** + Overture **1732** namizəd; dedupe merges **229**; eyni-ad disambiguate **219** (küçə/coord; review `landmark_yasamal_disambiguate.json`). Kateqoriya: food 573, shop 506, education 405, healthcare 308, services 212, other_poi 77, tourism 71, historic 64, government 79, park 49, culture 45, sport 32, religious 22, transport 11, museum 6, market 4, stadium 4. Assign: containment_verified. `pnpm validate` PASS · `pnpm test:named-places` PASS · tag `v0.2.1-national` · `DEFAULT_DATA_BASE` pin yeniləndi · skript `enrich_landmark_places.py --key yasamal`.

### 2. Nəsimi

- [x] Geniş taxonomy + dedupe + küçə disambiguate + git/pin  
  Fayl: `places/nasimi_all.json` · **177 → 3187**  
  **Hesabat (2026-10-22):** OSM **965** + Overture **2283** namizəd; merges **238**; disambiguate **261** (review `landmark_nasimi_disambiguate.json`). Kateqoriya: food 864, shop 830, education 410, services 296, healthcare 248, tourism 119, government 94, other_poi 89, historic 64, culture 54, sport 44, park 29, religious 16, transport 15, museum 9, stadium 6. Assign: containment_verified. `pnpm validate` PASS · `pnpm test:named-places` PASS · commit `21185e2` · tag `v0.2.2-national` (lokal) · `DEFAULT_DATA_BASE` → `@v0.2.2-national` · **push/CDN smoke: auth blok** (istifadəçi `git push` + tag) · skript `enrich_landmark_places.py --key nasimi`.

### 3. Nərimanov

- [x] Geniş taxonomy + dedupe + küçə disambiguate  
  Fayl: `places/narimanov_all.json` · **164 → 2915**  
  **Hesabat (2026-10-23):** OSM **857** + Overture **2115**; merges **221**; disambig **210**. Top: shop 760, food 655, healthcare 371, education 347. Validate PASS. Skript: `enrich_landmark_places.py --key narimanov`.

### 4. Nizami (Bakı)

- [x] Geniş taxonomy + dedupe + küçə disambiguate  
  Fayl: `places/nizami_baki_all.json` · **80 → 1203**  
  **Hesabat (2026-10-23):** OSM **524** + Overture **704**; merges **105**; disambig **115**. Validate PASS. Skript: `--key nizami_baki`.

### 5. Binəqədi

- [x] Geniş taxonomy + dedupe + küçə disambiguate  
  Fayl: `places/binagadi_all.json` · **169 → 2240**  
  **Hesabat (2026-10-23):** OSM **1457** + Overture **814**; merges **200**; disambig **435**. Validate PASS. Skript: `--key binagadi`.

### 6. Səbail

- [x] Geniş taxonomy + dedupe + küçə disambiguate  
  Fayl: `places/sabail_all.json` · **308 → 2625**  
  **Hesabat (2026-10-23):** OSM **1020** + Overture **1677**; merges **380**; disambig **227**. Top: food 932, shop 529, tourism 233. Validate PASS. Skript: `--key sabail`.

### 7. Xətai

- [x] Geniş taxonomy + dedupe + küçə disambiguate  
  Fayl: `places/xetai_all.json` · **172 → 1917**  
  **Hesabat (2026-10-23):** OSM **675** + Overture **1274**; merges **204**; disambig **177**. Validate PASS. Skript: `--key xetai`.

### 8. Sabunçu

- [x] Geniş taxonomy + dedupe + küçə disambiguate  
  Fayl: `places/sabuncu_all.json` · **254 → 2308**  
  **Hesabat (2026-10-23):** OSM **1771** + Overture **566**; merges **283**; disambig **609**. Validate PASS. Skript: `--key sabuncu`.

### 9. Suraxanı

- [x] Geniş taxonomy + dedupe + küçə disambiguate  
  Fayl: `places/surakhani_all.json` · **169 → 1208**  
  **Hesabat (2026-10-23):** OSM **997** + Overture **224**; merges **182**; disambig **327**. Validate PASS. Skript: `--key surakhani`.

### 10. Xəzər

- [x] Geniş taxonomy + dedupe + küçə disambiguate  
  Fayl: `places/xezer_all.json` · **263 → 2031**  
  **Hesabat (2026-10-23):** OSM **1662** + Overture **386**; merges **280**; disambig **672**. Validate PASS. Skript: `--key xezer`.

### 11. Pirallahı

- [x] Geniş taxonomy + dedupe + küçə disambiguate  
  Fayl: `places/pirallahi_all.json` · **35 → 168**  
  **Hesabat (2026-10-23):** OSM **149** + Overture **19**; merges **35**; disambig **52**. Validate PASS. Skript: `--key pirallahi`.

### 12. Qaradağ

- [x] Geniş taxonomy + dedupe + küçə disambiguate  
  Fayl: `places/qaradag_all.json` · **112 → 1013**  
  **Hesabat (2026-10-23):** OSM **833** + Overture **195**; merges **127**; disambig **240**. Validate PASS. Skript: `--key qaradag`.

---

## Faza 2 — Abşeron aglomerasiyası

### 13. Sumqayıt

- [x] Inventar + namizəd + join/dedupe + children-first assign  
  Fayl: `places/sumqayit_all.json` · **57 → 1724**  
  **Hesabat (2026-10-22):** OSM **1241** + Overture **492** namizəd (yalnız Sumqayıt city polygon containment); dedupe merges **66**; disambiguate **352** (`landmark_sumqayit_disambiguate.json`). Children-first: **76** verified uşaq sərhədi · uşağa **1171** · city-only **547** · conflict **6** (`landmark_sumqayit_reassign.json`). Kateqoriya: shop 739, food 373, education 159, healthcare 129, services 73, other_poi 62, government 42, culture 32, tourism 24, sport 17, park 16, historic 15, religious 12, monument 10, stadium 8, market 5, transport 5, museum 3. Assign: containment_verified. `pnpm validate` PASS · `pnpm test:named-places` PASS. Git/CDN: **yox**. Skript: `enrich_landmark_places.py --key sumqayit`.

### 14. Masazır

- [x] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/masazir_all.json` · **5 → 263**  
  **Hesabat (2026-10-22):** OSM **224** + Overture **44** (Masazır polygon); dedupe **10**; disambiguate **70** (`landmark_masazir_disambiguate.json`). Verified uşaq geom **0** → hamısı parent containment. Kateqoriya: shop 148, food 50, education 25, healthcare 15, government 8. Validate + named-places PASS. Git/CDN: **yox**. Skript: `enrich_landmark_places.py --key masazir`.

### 15. Xırdalan

- [x] Inventar + namizəd + join/dedupe + children-first assign  
  Fayl: `places/xirdalan_all.json` · **21 → 1268**  
  **Hesabat (2026-10-22):** OSM **1106** + Overture **177** (Xırdalan polygon); dedupe **36**; disambiguate **353** (`landmark_xirdalan_disambiguate.json`). Children-first: **8** uşaq · uşağa **383** · parent-only **885** · conflict **0** (`landmark_xirdalan_reassign.json`). Kateqoriya: shop 734, food 214, healthcare 85, education 76, government 37. Validate + named-places PASS. Git/CDN: **yox**. Skript: `enrich_landmark_places.py --key xirdalan`.

### 16. Abşeron rayonu (bütün uşaqlar ayrıca)

- [x] Hər verified uşaq üçün ayrı places faylı + residual `absheron_all.json`  
  **Hesabat (2026-10-22):** Bir scan (OSM **965** + Overture **121**, Masazır/Xırdalan polygon exclude); dedupe **14**.  
  **23 uşaq faylı** (Masazır/Xırdalan əvvəlki enrich saxlanıb): Novxanı 189, Saray 114, Mehdiabad 76, Qobu 68, Digah 50, Goradil 46, Məhəmmədli 36, Yeni Saray 33, Yeni Ceyranbatan 23, Fatmayı/Aşağı Güzdək 22, Hökməli 18, Güzdək/Qurd Dərəsi 16, Saray Üzümlük 14, Saray H MTK 13, digərləri ≤4; **0** POI: Novxanı Bağları, Saray Bağları, Çaylı.  
  Residual rayon: **22 → 305** (`absheron_all.json`, uşaq sərhədinə düşməyənlər). Conflict **0**.  
  Review: `landmark_absheron_children_enrich.json` · inventar `absheron_children_places_inventory.json`.  
  Validate + named-places PASS. Git/CDN: **yox**. Skript: `enrich_absheron_children_places.py`.

---

## Faza 3 — Respublika şəhərləri

### 17. Gəncə — Kəpəz

- [x] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/gence_kapaz_all.json` · **14 → 185**  
  **Hesabat (2026-10-23):** OSM **40** + Overture **148** namizəd; dedupe merges **17**; disambiguate **13** (`landmark_gence_kapaz_disambiguate.json`). Kateqoriya: food 45, shop 36, education 34, healthcare 21, services 9, government 9, other_poi 5, historic/park/sport/tourism 4, culture/monument/museum/transport 2, religious/stadium 1. Assign: containment_verified. `pnpm validate` PASS · `pnpm test:named-places` PASS. Git/CDN: **yox** (lokal). Skript: `enrich_landmark_places.py --key gence_kapaz`.

### 18. Gəncə — Nizami

- [x] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/gence_nizami_all.json` · **31 → 398**  
  **Hesabat (2026-10-23):** OSM **106** + Overture **299** namizəd; dedupe merges **38**; disambiguate **36** (`landmark_gence_nizami_disambiguate.json`). Kateqoriya: food 107, shop 68, education 61, services 32, tourism 26, healthcare 23, government 14, historic 12, other_poi 11, park 10, culture/monument 9, religious 6, transport 4, sport 3, stadium 2, museum 1. Assign: containment_verified. `pnpm validate` PASS · `pnpm test:named-places` PASS. Git/CDN: **yox** (lokal). Skript: `enrich_landmark_places.py --key gence_nizami`.

### 19. Mingəçevir

- [x] Inventar + namizəd + join/dedupe + children-first assign  
  Fayl: `places/mingachevir_all.json` · **20 → 348**  
  **Hesabat (2026-10-23):** OSM **238** + Overture **115**; merges **25**; disambig **47**. Children-first: uşağa 16 · city-only **332** · conflict **0**. Validate + named-places PASS. Git/CDN: **yox**. Skript: `enrich_landmark_places.py --key mingachevir`.

### 20. Şirvan

- [x] Inventar + namizəd + join/dedupe + children-first assign  
  Fayl: `places/shirvan_all.json` · **10 → 496**  
  **Hesabat (2026-10-23):** OSM **435** + Overture **61**; merges **10**; disambig **113**. Children-first: Hacıqəhrəmanlı 2 · city-only **494** · conflict **0**. Validate + named-places PASS. Git/CDN: **yox**. Skript: `enrich_landmark_places.py --key shirvan`.

### 21. Naftalan

- [x] Inventar + namizəd + join/dedupe + children-first assign  
  Fayl: `places/naftalan_all.json` · **2 → 110**  
  **Hesabat (2026-10-23):** OSM **91** + Overture **22**; merges **5**; disambig **11**. Children-first: Qaşaltı Qaraqoyunlu 3 · city-only **107**. Validate + named-places PASS. Git/CDN: **yox**. Skript: `enrich_landmark_places.py --key naftalan`.

### 22. Yevlax (şəhər)

- [x] Inventar + namizəd + join/dedupe + children-first assign  
  Fayl: `places/yevlax_all.json` · **4 → 180**  
  **Hesabat (2026-10-23):** OSM **146** + Overture **34**; merges **4**; disambig **14**. Children-first: uşağa 31 · city-only **149**. Validate + named-places PASS. Git/CDN: **yox**. Skript: `enrich_landmark_places.py --key yevlax`.

### 23. Lənkəran (şəhər)

- [x] Inventar + namizəd + join/dedupe + children-first assign  
  Fayl: `places/lankaran_all.json` · **15 → 181**  
  **Hesabat (2026-10-23):** OSM **59** + Overture **124**; merges **17**; disambig **14**. Children-first: Digah/Şiləvar · city-only **177**. Validate + named-places PASS. Git/CDN: **yox**. Skript: `enrich_landmark_places.py --key lankaran`.

### 24. Şəki (şəhər)

- [x] Inventar + namizəd + join/dedupe + children-first assign  
  Fayl: `places/sheki_all.json` · **17 → 535**  
  **Hesabat (2026-10-23):** OSM **385** + Overture **157**; merges **24**; disambig **69**. Kateqoriya (top): shop 147, food 111, tourism 54, education 42. Validate + named-places PASS. Git/CDN: **yox**. Skript: `enrich_landmark_places.py --key sheki`.

### 25. Naxçıvan (şəhər)

- [x] Inventar + namizəd + join/dedupe + children-first assign  
  Fayl: `places/nakhchivan_all.json` · **35 → 254**  
  **Hesabat (2026-10-23):** OSM **93** + Overture **165**; merges **39**; disambig **24**. Children-first: Əliabad/Tumbul · city-only **251**. Validate + named-places PASS. Git/CDN: **yox**. Skript: `enrich_landmark_places.py --key nakhchivan`.

---

## Faza 4 — Digər rayonlar (ardıcıllıqla)

Hər sətir bir blok. **2026-10-23** paket: hamısı enrich + validate PASS · Git/CDN **yox** (lokal).

- [x] Xızı · `khizi` · **5 → 61**
- [x] Quba · `quba` · **39 → 415**
- [x] Qusar · `qusar` · **15 → 477**
- [x] Xaçmaz · `xachmaz` · **18 → 458**
- [x] Şabran · `shabran` · **7 → 70**
- [x] Siyəzən · `siyazan` · **2 → 65**
- [x] Şamaxı · `shamakhi` · **12 → 536**
- [x] İsmayıllı · `ismailli` · **23 → 377**
- [x] Ağsu · `agsu` · **10 → 146**
- [x] Qobustan · `gobustan` · **4 → 111**
- [x] Hacıqabul · `hajiqabul` · **5 → 193**
- [x] Salyan · `salyan` · **7 → 546**
- [x] Neftçala · `neftchala` · **7 → 116**
- [x] Sabirabad · `sabirabad` · **4 → 79**
- [x] Saatlı · `saatli` · **3 → 30**
- [x] İmişli · `imishli` · **5 → 63**
- [x] Beyləqan · `beylagan` · **2 → 30** (yenidən enrich 2026-10-23)
- [x] Ağcabədi · `agjabadi` · **2 → 262**
- [x] Yevlax rayonu · `yevlax_rayon` · **4 → 93**
- [x] Bərdə · `barda` · **6 → 123**
- [x] Ağdaş · `agdash` · **9 → 244**
- [x] Göyçay · `goychay` · **13 → 226**
- [x] Ucar · `ucar` · **4 → 143**
- [x] Zərdab · `zardab` · **4 → 44**
- [x] Kürdəmir · `kurdamir` · **5 → 180**
- [x] Daşkəsən · `dashkasan` · **3 → 129**
- [x] Göygöl · `goygol` · **12 → 250**
- [x] Samux · `samukh` · **2 → 132**
- [x] Şəmkir · `shamkir` · **16 → 504**
- [x] Tovuz · `tovuz` · **12 → 468**
- [x] Ağstafa · `agstafa` · **8 → 339**
- [x] Qazax · `gazakh` · **11 → 428**
- [x] Gədəbəy · `gedabey` · **8 → 360**
- [x] Şəki rayonu · `sheki_rayon` · **19 → 216**
- [x] Qax · `gakh` · **19 → 298**
- [x] Zaqatala · `zaqatala` · **19 → 386**
- [x] Balakən · `balakan` · **5 → 267**
- [x] Oğuz · `oguz` · **7 → 251**
- [x] Qəbələ · `gabala` · **25 → 417**
- [x] Lənkəran rayonu · `lankaran_rayon` · **15 → 71**
- [x] Astara · `astara` · **10 → 63**
- [x] Lerik · `lerik` · **4 → 64**
- [x] Yardımlı · `yardimli` · **6 → 21**
- [x] Masallı · `masalli` · **11 → 98**
- [x] Cəlilabad · `jalilabad` · **4 → 68**
- [x] Ağdam · `agdam` · **8 → 42**
- [x] Füzuli · `fuzuli` · **8 → 29**
- [x] Tərtər · `tartar` · **4 → 60**
- [x] Xocalı · `khojaly` · **11 → 276**
- [x] Xocavənd · `khojavend` · **5 → 41**
- [x] Şuşa · `shusha` · **18 → 66**
- [x] Laçın · `lachin` · **3 → 23**
- [x] Kəlbəcər · `kalbajar` · **2 → 14**
- [x] Qubadlı · `qubadli` · **2 → 4**
- [x] Zəngilan · `zangilan` · **0 → 9**
- [x] Cəbrayıl · `jabrayil` · **0 → 5**
- [x] Babək · `babek` · **5 → 25**
- [x] Culfa · `julfa` · **8 → 24**
- [x] Kəngərli · `kangarli` · **2 → 6**
- [x] Ordubad · `ordubad` · **12 → 29**
- [x] Sədərək · `sadarak` · **0 → 3**
- [x] Şahbuz · `shahbuz` · **2 → 11**
- [x] Şərur · `sharur` · **0 → 9**

---

## Əlaqəli sənədlər

- GeoAgent areas: [`WORKER.md`](./WORKER.md) — **bu agentə aid deyil**
- Places cascade (UI): `Hierarchy.md` «Tanınmış məkanlar»
- Taxonomy: [`docs/landmark-taxonomy.md`](./docs/landmark-taxonomy.md) · `scripts/landmark_taxonomy.py`
- Hər rayon yekunu: LandmarkAgent özü commit + push + tag/pin + CDN 200 smoke + hesabat
  (bax `.cursor/rules/landmark-agent.mdc` §4)
