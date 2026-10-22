# GeoAtlas Azərbaycan — LANDMARK

Bu fayl **LandmarkAgent** üçün tanınmış məkan (places) iş siyahısıdır.
Hər rayon/şəhər bloku **ardıcıllıqla** yerinə yetirilir.
Hierarchy / areas / boundaries — [`Hierarchy.md`](./Hierarchy.md) + GeoAgent;
bu faylda **yalnız places enrich**.

## PAUSE / davam nöqtəsi

**Dataset:** `0.2.0-national` (manifest) · places baseline bax `data/places/index.json`  
**Rule:** `.cursor/rules/landmark-agent.mdc`  
**Jurnal:** `data/reviews/landmark_report.md`

**Bitən:** Yasamal enrich (170→211)  
**Növbəti:** Nəsimi

---

## Agent iş qaydası (məcburi)

1. Bu fayldan ilk unchecked `[ ]` bloku götür.
2. Hierarchy qaydalarını **oxu**; areas/boundaries **yazma**.
3. Mənbə: `source_files/` oxu only.
4. Çıxış: `data/places/{key}_all.json` + `index.json` + reviews.
5. `area_id` = rayon/city-direct; containment; dedupe; adsız UI-da gizli qalır.
6. Blok bitəndə: validate (+ named-places test) → `[x]` + **Hesabat:** → jurnal.

### Blok DoD

- [ ] Mövcud places inventar (before count)
- [ ] Namizəd mənbə + taxonomy (yalnız adlı)
- [ ] Dedupe (id / source_id); ada görə merge yox
- [ ] Containment assign → düzgün `area_id`
- [ ] `places/index.json` count yenilənib
- [ ] `pnpm validate` PASS; conflict-lər review-də
- [ ] `LANDMARK.md` checkbox + Hesabat; `landmark_report.md` sətir

---

## Faza L0 — Scaffold

- [x] **LandmarkAgent rule + LANDMARK.md**  
  **Hesabat:** P2 scaffold; enrich hələ başlamayıb.

---

## Faza L1 — Bakı rayonları (prioritet)

Ardıcıllıq (birini bitirmədən növbətiyə keçmə):

- [x] **Yasamal** — `places/yasamal_all.json` · 170→211  
  **Hesabat:** OSM named ways +41; validate PASS (bax `LANDMARK.md`)
- [x] **Nəsimi** — `places/nasimi_all.json`
- [x] **Nərimanov** — `places/narimanov_all.json`
- [x] **Nizami (Bakı)** — `places/nizami_baki_all.json`
- [x] **Binəqədi** — `places/binagadi_all.json`
- [x] **Səbail** — `places/sabail_all.json`
- [x] **Xətai** — `places/xetai_all.json`
- [x] **Sabunçu** — `places/sabuncu_all.json`
- [x] **Suraxanı** — `places/surakhani_all.json`
- [x] **Xəzər** — `places/xezer_all.json`
- [x] **Pirallahı** — `places/pirallahi_all.json`
- [x] **Qaradağ** — `places/qaradag_all.json`

---

## Faza L2 — Abşeron / Sumqayıt (L1 bitəndən sonra)

- [x] **Sumqayıt** — `places/sumqayit_all.json`
- [x] **Masazır** — `places/masazir_all.json`
- [x] **Xırdalan** — `places/xirdalan_all.json`
- [x] **Abşeron (rayon qalıq)** — `places/absheron_all.json` (scope review-də yaz)

---

## Faza L3+ — digər şəhər/rayon

`data/places/index.json` `by_rayon` sırası ilə; hər sətir bir `[ ]` blok.
(Agent scaffold zamanı index-dən L1/L2-də olmayan key-ləri qısa checklist olaraq əlavə edə bilər — hamısını enrich etmə.)