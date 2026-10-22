# GeoAtlas Azərbaycan — LANDMARK

Bu fayl **LandmarkAgent** üçün iş siyahısıdır. Hər blok **bir** `places/{key}_all.json`
(və lazım olsa `places/index.json` + review) üzərindədir. Hierarchy / areas /
boundaries **toxunulmur** — onlar [`WORKER.md`](./WORKER.md) + GeoAgent-dir.

Qaydalar: [`.cursor/rules/landmark-agent.mdc`](./.cursor/rules/landmark-agent.mdc) ·
[`docs/landmark-taxonomy.md`](./docs/landmark-taxonomy.md) ·
[`Hierarchy.md`](./Hierarchy.md) (oxu) · jurnal: [`data/reviews/landmark_report.md`](./data/reviews/landmark_report.md)

## PAUSE / davam nöqtəsi

**Dataset:** `0.2.1-national` · places **5145** · validate **PASS**  
**Bitən:** Yasamal — geniş taxonomy + dedupe + küçə disambiguate + git/pin  
**CDN pin:** `v0.2.1-national`  
**Növbəti:** **Nəsimi** (`nasimi_all.json`)

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

Baseline counts: `data/places/index.json` (cari: `0.2.1-national`).

### 1. Yasamal

- [x] Geniş taxonomy + dedupe + küçə disambiguate + git/pin  
  Fayl: `places/yasamal_all.json` · **211 → 2468** (əvvəlki ways-enrich 170→211)  
  **Hesabat (2026-10-22 taxonomy):** OSM named nodes **754** + Overture **1732** namizəd; dedupe merges **229**; eyni-ad disambiguate **219** (küçə/coord; review `landmark_yasamal_disambiguate.json`). Kateqoriya: food 573, shop 506, education 405, healthcare 308, services 212, other_poi 77, tourism 71, historic 64, government 79, park 49, culture 45, sport 32, religious 22, transport 11, museum 6, market 4, stadium 4. Assign: containment_verified. `pnpm validate` PASS · `pnpm test:named-places` PASS · tag `v0.2.1-national` · `DEFAULT_DATA_BASE` pin yeniləndi · skript `enrich_landmark_places.py --key yasamal`.

### 2. Nəsimi

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/nasimi_all.json` · baseline **177**  
  **Hesabat:** _

### 3. Nərimanov

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/narimanov_all.json` · baseline **164**  
  **Hesabat:** _

### 4. Nizami (Bakı)

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/nizami_baki_all.json` · baseline **80**  
  **Hesabat:** _

### 5. Binəqədi

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/binagadi_all.json` · baseline **169**  
  **Hesabat:** _

### 6. Səbail

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/sabail_all.json` · baseline **308**  
  **Hesabat:** _

### 7. Xətai

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/xetai_all.json` · baseline **172**  
  **Hesabat:** _

### 8. Sabunçu

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/sabuncu_all.json` · baseline **254**  
  **Hesabat:** _

### 9. Suraxanı

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/surakhani_all.json` · baseline **169**  
  **Hesabat:** _

### 10. Xəzər

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/xezer_all.json` · baseline **263**  
  **Hesabat:** _

### 11. Pirallahı

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/pirallahi_all.json` · baseline **35**  
  **Hesabat:** _

### 12. Qaradağ

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/qaradag_all.json` · baseline **112**  
  **Hesabat:** _

---

## Faza 2 — Abşeron aglomerasiyası

### 13. Sumqayıt

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/sumqayit_all.json` · baseline **57**  
  **Hesabat:** _

### 14. Masazır

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/masazir_all.json` · baseline **5**  
  **Hesabat:** _

### 15. Xırdalan

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/xirdalan_all.json` · baseline **21**  
  **Hesabat:** _

### 16. Abşeron rayonu (qalan settlement-lər)

- [ ] Inventar + namizəd + join/dedupe + assign  
  Fayl: `places/absheron_all.json` · baseline **22**  
  Qeyd: Masazır/Xırdalan ayrı fayllar — dublikat id yox.  
  **Hesabat:** _

---

## Faza 3 — Respublika şəhərləri

### 17. Gəncə — Kəpəz

- [ ] `places/gence_kapaz_all.json` · baseline **14** · **Hesabat:** _

### 18. Gəncə — Nizami

- [ ] `places/gence_nizami_all.json` · baseline **31** · **Hesabat:** _

### 19. Mingəçevir

- [ ] `places/mingachevir_all.json` · baseline **20** · **Hesabat:** _

### 20. Şirvan

- [ ] `places/shirvan_all.json` · baseline **10** · **Hesabat:** _

### 21. Naftalan

- [ ] `places/naftalan_all.json` · baseline **2** · **Hesabat:** _

### 22. Yevlax (şəhər)

- [ ] `places/yevlax_all.json` · baseline **4** · **Hesabat:** _

### 23. Lənkəran (şəhər)

- [ ] `places/lankaran_all.json` · baseline **15** · **Hesabat:** _

### 24. Şəki (şəhər)

- [ ] `places/sheki_all.json` · baseline **17** · **Hesabat:** _

### 25. Naxçıvan (şəhər)

- [ ] `places/nakhchivan_all.json` · baseline **35** · **Hesabat:** _

---

## Faza 4 — Digər rayonlar (ardıcıllıqla)

Hər sətir bir blok. Baseline = `index.json` count.

- [ ] Xızı · `khizi` · **5**
- [ ] Quba · `quba` · **39**
- [ ] Qusar · `qusar` · **15**
- [ ] Xaçmaz · `xachmaz` · **18**
- [ ] Şabran · `shabran` · **7**
- [ ] Siyəzən · `siyazan` · **2**
- [ ] Şamaxı · `shamakhi` · **12**
- [ ] İsmayıllı · `ismailli` · **23**
- [ ] Ağsu · `agsu` · **10**
- [ ] Qobustan · `gobustan` · **4**
- [ ] Hacıqabul · `hajiqabul` · **5**
- [ ] Salyan · `salyan` · **7**
- [ ] Neftçala · `neftchala` · **7**
- [ ] Sabirabad · `sabirabad` · **4**
- [ ] Saatlı · `saatli` · **3**
- [ ] İmişli · `imishli` · **5**
- [ ] Beyləqan · `beylagan` · **2**
- [ ] Ağcabədi · `agjabadi` · **2**
- [ ] Yevlax rayonu · `yevlax_rayon` · **4**
- [ ] Bərdə · `barda` · **6**
- [ ] Ağdaş · `agdash` · **9**
- [ ] Göyçay · `goychay` · **13**
- [ ] Ucar · `ucar` · **4**
- [ ] Zərdab · `zardab` · **4**
- [ ] Kürdəmir · `kurdamir` · **5**
- [ ] Daşkəsən · `dashkasan` · **3**
- [ ] Göygöl · `goygol` · **12**
- [ ] Samux · `samukh` · **2**
- [ ] Şəmkir · `shamkir` · **16**
- [ ] Tovuz · `tovuz` · **12**
- [ ] Ağstafa · `agstafa` · **8**
- [ ] Qazax · `gazakh` · **11**
- [ ] Gədəbəy · `gedabey` · **8**
- [ ] Şəki rayonu · `sheki_rayon` · **19**
- [ ] Qax · `gakh` · **19**
- [ ] Zaqatala · `zaqatala` · **19**
- [ ] Balakən · `balakan` · **5**
- [ ] Oğuz · `oguz` · **7**
- [ ] Qəbələ · `gabala` · **25**
- [ ] Lənkəran rayonu · `lankaran_rayon` · **15**
- [ ] Astara · `astara` · **10**
- [ ] Lerik · `lerik` · **4**
- [ ] Yardımlı · `yardimli` · **6**
- [ ] Masallı · `masalli` · **11**
- [ ] Cəlilabad · `jalilabad` · **4**
- [ ] Ağdam · `agdam` · **8**
- [ ] Füzuli · `fuzuli` · **8**
- [ ] Tərtər · `tartar` · **4**
- [ ] Xocalı · `khojaly` · **11**
- [ ] Xocavənd · `khojavend` · **5**
- [ ] Şuşa · `shusha` · **18**
- [ ] Laçın · `lachin` · **3**
- [ ] Kəlbəcər · `kalbajar` · **2**
- [ ] Qubadlı · `qubadli` · **2**
- [ ] Zəngilan · `zangilan` · **0** _(boş baseline — mənbədən ehtiyatla)_
- [ ] Cəbrayıl · `jabrayil` · **0**
- [ ] Babək · `babek` · **5**
- [ ] Culfa · `julfa` · **8**
- [ ] Kəngərli · `kangarli` · **2**
- [ ] Ordubad · `ordubad` · **12**
- [ ] Sədərək · `sadarak` · **0**
- [ ] Şahbuz · `shahbuz` · **2**
- [ ] Şərur · `sharur` · **0**

---

## Əlaqəli sənədlər

- GeoAgent areas: [`WORKER.md`](./WORKER.md) — **bu agentə aid deyil**
- Places cascade (UI): `Hierarchy.md` «Tanınmış məkanlar»
- Taxonomy: [`docs/landmark-taxonomy.md`](./docs/landmark-taxonomy.md) · `scripts/landmark_taxonomy.py`
- Hər rayon yekunu: LandmarkAgent özü commit + push + tag/pin + CDN 200 smoke + hesabat
  (bax `.cursor/rules/landmark-agent.mdc` §4)
