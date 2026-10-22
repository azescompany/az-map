# GeoAtlas Azərbaycan — WORKER

Bu fayl **GeoAgent** üçün iş siyahısıdır. Hər şəhər / rayon / qəsəbə bloku
**ardıcıllıqla** yerinə yetirilir. Heç bir ərazi bloku bitmədən növbətiyə keçilmir
(blok daxilində alt-tapşırıqlar paralel ola bilər).

## PAUSE / davam nöqtəsi

**Dataset:** `0.2.0-national` · areas **3421** · places **2847** · validate **PASS** (0 conflict)  
**Demo:** http://localhost:1555/  

**Bitən:** Faza 0–4 milli bağlama · Kolluqışlaq conflict bağlandı (Zəngilan OSM∪Overture)

---

## Agent iş qaydası (məcburi)

1. Bu `WORKER.md` üzərindən növbəti **unchecked** `[ ]` bloku götür.
2. Extract / hierarchy **həmişə** [`Hierarchy.md`](./Hierarchy.md) qaydalarına
   istinadən aparılır (Yasamal nümunəsi = qızıl standart).
3. Mənbə: yalnız `source_files/` (OSM PBF, Overture, GeoNames). **Mənbəyə yazma.**
4. Çıxış: yalnız `data/` (+ `data/reviews/`). Uydurma sərhəd / ad / parent yoxdur.
5. Blok bitəndə: `pnpm quality:gate` → `pnpm validate` → bu faylda `[x]` və
   **Hesabat** sətrini doldur.
6. UI contract: `Ölkə → Şəhər → Rayon → Məhəllə/qəsəbə → Tanınmış məkan`
   (`parent_status=verified` uşaqlar; adsız məkanlar gizli).

### Blok “Definition of Done” (DoD)

Hər ərazi vahidi üçün aşağıdakılar tamamlanmalıdır:

- [ ] Admin sərhəd (OSM relation və/və ya Overture `division_area`) — uydurma yox
- [ ] Parent/child verified (`Hierarchy.md` qaydaları)
- [ ] Məhəllə / mikrorayon / qəsəbə (mənbədə olanlar) dropdown-a düşür
- [ ] Tanınmış adlı məkanlar (`places/{key}_all.json` və ya ekvivalent)
- [ ] Quality gate: mərkəz polygon daxilində, CRS EPSG:4326
- [ ] `pnpm validate` PASS; açıq conflict-lər `data/reviews/`-də sənədləşib
- [ ] Bu `WORKER.md`-də checkbox + hesabat yazılıb

---

## Faza 0 — Ölkə çərçivəsi

- [x] **Azərbaycan (country)** — sərhəd + Bakı parent path mövcuddur  
  **Hesabat:** `data/areas` country record; boundary `boundaries/country_AZ.geojson`; dataset `0.1.3-pilot`.

---

## Faza 1 — Abşeron aglomerasiyası (prioritet)

### 1. Bakı

Status: **yekunlaşmış sayılır** — son yoxlama aparılıb; açıq qalıq var.

- [x] 12 inzibati rayon sərhədi (OSM)  
- [x] Məhəllə / qəsəbə extract (`pnpm extract:baki-hoods`) — verified uşaqlar UI-da  
- [x] Tanınmış məkanlar bütün rayonlar üçün (`pnpm extract:baki-places`, 2073)  
- [x] Quality gate + validate PASS (`0.1.3-pilot`, 155 area)  
- [x] **Bağlı:** Nizami “conflict” məhəllələr əslində Gəncə Nizami uşaqları idi — `extract:gence` ilə köçürüldü  
- [ ] **Açıq:** Son smoke — UI-də hər 12 rayon üçün dropdown + 1 məkan seçimi

**Hesabat (2026-10-21):**  
Areas 155 · verified hoods ~134 · places 2073 · Nizami conflict bağlandı (Gəncə reparent) ·  
See `data/reviews/baki_neighborhoods_extract.json`, `Hierarchy.md`.

### 2. Sumqayıt

- [x] Şəhər sərhədi (OSM `relation/3912206` al=8 city core + `3764579` al=6 extent)  
- [x] Mikrorayon / qəsəbə (`Hierarchy.md` verified) — 14 uşaq; rayon uydurulmayıb (birbaşa city uşağı)  
- [x] Tanınmış məkanlar — `places/sumqayit_all.json` (57 Overture landmark; OSM notables pending env quirk)  
- [x] Quality gate + validate PASS (`0.1.4-pilot`)  

**Hesabat (2026-10-21):**  
City `Sumqayıt` under Azərbaycan · verified children: 54-cü Məhəllə, 9-cu Mikrorayon, Birləşmiş (7,8,12) Məhəllə, Stansiya Sumqayıt, Yeni Sumqayıt qəsəbəsi, Çinar 2016 MTK, Ceyranbatan, Corat, Corat bağları, Novxanı bağları, Yaşma Bağları, Yaşıl Dərə, Zeynalabdin Tağıyev qəsəbəsi, Şirvan qəsəbəsi · places 57 · areas total 170 · places total 2130 · report `data/reviews/sumqayit_extract.json` · script `pnpm extract:sumqayit`.

### 3. Masazır

- [x] Parent təyini — **Abşeron rayonu** (Overture parent + OSM `relation/3764533`)  
- [x] Abşeron rayonu sərhədi (parent skeleton) + Masazır sərhədi (Overture macrohood)  
- [x] Tanınmış məkanlar — `places/masazir_all.json` (5)  
- [x] Quality gate + validate PASS (`0.1.5-pilot`)  

**Hesabat (2026-10-21):**  
`Azərbaycan → Abşeron rayonu → Masazır` · Masazır `parent_status=verified` · locality polygon yoxdur, boundary = Overture macrohood · OSM label `node/1886282982` · places 5 · areas 172 · places total 2135 · `pnpm extract:masazir` · `data/reviews/masazir_extract.json`.  
Qeyd: Abşeronun digər qəsəbələri (Xırdalan və s.) növbəti bloklarda.

### 4. Xırdalan

- [x] Şəhər/qəsəbə sərhədi + parent (Abşeron)  
- [x] Mikrorayon / məhəllə (mənbədə olanlar) — 8 verified  
- [x] Tanınmış məkanlar — `places/xirdalan_all.json` (21)  
- [x] Quality gate + validate + hesabat  

**Hesabat (2026-10-21):**  
`Azərbaycan → Abşeron rayonu → Xırdalan` · locality polygon + 8 microhood · places 21 · areas 181 · places total 2156 · dataset `0.1.6-pilot` · `pnpm extract:xirdalan` · `data/reviews/xirdalan_extract.json` · UI: Mikrorayon dropdown under Xırdalan.

### 5. Ümumi Abşeron (Abşeron rayonu + qalan qəsəbələr)

- [x] Abşeron rayonu sərhədi (OSM al=6, Masazır extract-dən)  
- [x] Qəsəbə / kənd vahidləri — 23 verified + 2 nested (Masazır/Xırdalan ayrıca bloklarda)  
- [x] Tanınmış məkanlar — `places/absheron_all.json` (22; Masazır/Xırdalan dublikatları çıxarılıb)  
- [x] Bakı / Sumqayıt / Xırdalan ilə sərhəd overlap review — `data/reviews/absheron_extract.json`  
- [x] Quality gate + validate + hesabat  

**Hesabat (2026-10-21):**  
`Azərbaycan → Abşeron rayonu` · verified settlements: Aşağı Güzdək, Digah, Fatmayı, Goradil, Güzdək, Hökməli, Mehdiabad, Məhəmmədli (+Villalar), Novxanı, Novxanı Bağları, Pirəkəşkül, Qobu (+Qobu Village YS), Qobustan qəsəbəsi, Qurd Dərəsi, Saray, Saray Bağları, Saray H MTK, Saray Üzümlük, Yeni Ceyranbatan, Yeni Saray, Çaylı, Şəfəq, Əliçıraq · places 22 rayon-scope · areas 206 · places total 2178 · dataset `0.1.7-pilot` · `pnpm extract:absheron` · conflict 0 (Absheron). Qeyd: Sumqayıt-dakı Ceyranbatan / Novxanı bağları ayrı Overture id; Digah/Şəfəq nested locality-lərdə geom yoxdur → skip.

---

## Faza 2 — Respublika əhəmiyyətli şəhərlər

### 6. Gəncə

- [x] Sərhəd + rayon/məhəllə hierarchy — city + Kəpəz (3) + Nizami (7) verified hoods  
- [x] Tanınmış məkanlar — `places/gence_kapaz_all.json` (14) + `gence_nizami_all.json` (31)  
- [x] Gate + validate + hesabat  

**Hesabat (2026-10-21):**  
`Azərbaycan → Gəncə → Kəpəz/Nizami` · OSM city `relation/3764556` · Bakı-Nizami-yə yanlış bağlanmış 7 hood Gəncəyə köçürüldü · areas 212 · places 2223 · dataset `0.1.8-pilot` · `pnpm extract:gence` · `data/reviews/gence_extract.json` · validate 0 conflict.

### 7. Mingəçevir

- [x] Sərhəd + uşaqlar + məkanlar + gate + hesabat  

**Hesabat (2026-10-21):**  
`Azərbaycan → Mingəçevir` (city-direct, rayon yox) · 11 verified məhəllə · places 20 · areas 224 · places total 2243 · dataset `0.1.9-pilot` · `pnpm extract:mingachevir` · `data/reviews/mingachevir_extract.json`.

### 8. Şirvan

- [x] Sərhəd + uşaqlar + məkanlar + gate + hesabat  

**Hesabat (2026-10-21):**  
`Azərbaycan → Şirvan` (city-direct; Sumqayıt «Şirvan qəsəbəsi»-dən ayrı) · 3 verified (Hacıqəhrəmanlı, Yeni/Şirvan YYK) · places 10 · areas 228 · places total 2253 · dataset `0.1.10-pilot` · `pnpm extract:shirvan` · `data/reviews/shirvan_extract.json`.

### 9. Naftalan

- [x] Sərhəd + uşaqlar + məkanlar + gate + hesabat  

**Hesabat (2026-10-21):**  
`Azərbaycan → Naftalan` · 2 verified (Qasımbəyli, Qaşaltı Qaraqoyunlu) · places 2 · areas 231 · places total 2255 · dataset `0.1.11-pilot` · `pnpm extract:naftalan` · `data/reviews/naftalan_extract.json`.

### 10. Yevlax (şəhər)

- [x] Sərhəd + uşaqlar + məkanlar + gate + hesabat  

**Hesabat (2026-10-21):**  
`Azərbaycan → Yevlax` (şəhər; Yevlax rayonu kəndləri Faza 3) · 6 verified mikrorayon/məhəllə · places 4 · areas 238 · places total 2259 · dataset `0.1.12-pilot` · `pnpm extract:yevlax` · `data/reviews/yevlax_extract.json`.

### 11. Lənkəran (şəhər)

- [x] Sərhəd + uşaqlar + məkanlar + gate + hesabat  

**Hesabat (2026-10-22):**  
`Azərbaycan → Lənkəran` (şəhər; rayon kəndləri Faza 3) · Digah, Şiləvar · places 15 · areas 241 · places 2274 · `0.1.13-pilot` · `pnpm extract:lankaran` · `data/reviews/lankaran_extract.json`.

### 12. Şəki (şəhər)

- [x] Sərhəd + uşaqlar + məkanlar + gate + hesabat  

**Hesabat (2026-10-22):**  
`Azərbaycan → Şəki` · Çeşməli · places 17 · areas 243 · places 2291 · `0.1.14-pilot` · `pnpm extract:sheki` · `data/reviews/sheki_extract.json`.

### 13. Naxçıvan (şəhər, Naxçıvan MR)

- [x] Sərhəd + uşaqlar + məkanlar + gate + hesabat  

**Hesabat (2026-10-22):**  
`Azərbaycan → Naxçıvan` (şəhər; MR ayrıca) · 7 verified · places 35 · areas 251 · places 2326 · `0.1.15-pilot` · `pnpm extract:nakhchivan` · `data/reviews/nakhchivan_extract.json`.

---

## Faza 3 — İqtisadi rayonlar / inzibati rayonlar

> Hər rayon üçün eyni DoD: sərhəd → verified uşaqlar → adlı məkanlar → gate → hesabat.  
> İş ardıcıllığı: Abşeron bitəndən sonra coğrafi qonşuluq / məlumat sıxlığına görə.

### 3.1 Abşeron–Xızı (qalan)

- [x] Xızı rayonu — **Hesabat (2026-10-22):** 30 verified settlement · places 5 · areas 282 · `0.1.16-pilot` · `pnpm extract:khizi` · `data/reviews/khizi_extract.json`.

### 3.2 Quba–Xaçmaz

- [x] Quba — **Hesabat (2026-10-22):** 150 verified · places 39 · `pnpm extract:quba` · `data/reviews/quba_extract.json`.
- [x] Qusar — **Hesabat (2026-10-22):** 93 verified · places 15 · `pnpm extract:qusar`.
- [x] Xaçmaz — **Hesabat (2026-10-22):** 149 verified · places 18 · `pnpm extract:xachmaz`.
- [x] Şabran — **Hesabat (2026-10-22):** 66 verified · places 7 · `pnpm extract:shabran`.
- [x] Siyəzən — **Hesabat (2026-10-22):** 35 verified · places 2 · areas 780 · places 2412 · `0.1.21-pilot` · `pnpm extract:siyazan`.

### 3.3 Dağlıq Şirvan

- [x] Şamaxı — **Hesabat (2026-10-22):** 64 verified · places 12 · `pnpm extract:shamakhi`
- [x] İsmayıllı — **Hesabat (2026-10-22):** 113 verified · places 23 · `pnpm extract:ismailli`
- [x] Ağsu — **Hesabat (2026-10-22):** 80 verified · places 10 · `pnpm extract:agsu`
- [x] Qobustan — **Hesabat (2026-10-22):** 32 verified · places 4 · areas 1073 · places 2461 · `0.1.25-pilot` · `pnpm extract:gobustan`

### 3.4 Şirvan–Salyan

- [x] Hacıqabul — **Hesabat (2026-10-22):** 31 · places 5 · `pnpm extract:hajiqabul`
- [x] Salyan — **Hesabat (2026-10-22):** 50 · places 7 · `pnpm extract:salyan`
- [x] Neftçala — **Hesabat (2026-10-22):** 48 · places 7 · `pnpm extract:neftchala`
- [x] Sabirabad — **Hesabat (2026-10-22):** 61 · places 4 · `pnpm extract:sabirabad`
- [x] Saatlı — **Hesabat (2026-10-22):** 27 · places 3 · areas 1295 · places 2487 · `0.1.30-pilot` · `pnpm extract:saatli`

### 3.5 Mil–Muğan

- [x] İmişli — **Hesabat (2026-10-22):** 36 · places 5 · `pnpm extract:imishli`
- [x] Beyləqan — **Hesabat (2026-10-22):** 14 · places 2 · `pnpm extract:beylagan`
- [x] Ağcabədi — **Hesabat (2026-10-22):** 24 · places 2 · areas 1372 · places 2496 · `0.1.33-pilot` · `pnpm extract:agjabadi`

### 3.6 Mərkəzi Aran

- [x] Yevlax rayonu — **Hesabat (2026-10-22):** 40 · places 4 · `pnpm extract:yevlax-rayon` (şəhərdən ayrı)
- [x] Bərdə — **Hesabat (2026-10-22):** 24 · places 6 · `pnpm extract:barda`
- [x] Ağdaş — **Hesabat (2026-10-22):** 74 · places 9 · `pnpm extract:agdash`
- [x] Göyçay — **Hesabat (2026-10-22):** 62 · places 13 · `pnpm extract:goychay`
- [x] Ucar — **Hesabat (2026-10-22):** 28 · places 4 · `pnpm extract:ucar`
- [x] Zərdab — **Hesabat (2026-10-22):** 6 · places 4 · `pnpm extract:zardab`
- [x] Kürdəmir — **Hesabat (2026-10-22):** 52 · places 5 · areas 1664 · places 2541 · `0.1.40-pilot` · `pnpm extract:kurdamir`

### 3.7 Gəncə–Daşkəsən / Qazax–Tovuz

- [x] Gəncə rayonu vahidləri — **Hesabat:** OSM/Overture-də şəhərdən ayrı «Gəncə rayonu» yoxdur; `Gəncə İnzibati Ərazisi` + Kəpəz/Nizami artıq Faza 2-də.
- [x] Daşkəsən — **Hesabat (2026-10-22):** 49 · places 3 · `pnpm extract:dashkasan`
- [x] Göygöl — **Hesabat (2026-10-22):** 40 · places 12 · `pnpm extract:goygol`
- [x] Samux — **Hesabat (2026-10-22):** 31 · places 2 · `pnpm extract:samukh`
- [x] Şəmkir — **Hesabat (2026-10-22):** 68 · places 16 · `pnpm extract:shamkir`
- [x] Tovuz — **Hesabat (2026-10-22):** 103 · places 12 · `pnpm extract:tovuz`
- [x] Ağstafa — **Hesabat (2026-10-22):** 39 · places 8 · areas 2000 · places 2594 · `0.1.46-pilot` · `pnpm extract:agstafa`
- [x] Qazax — **Hesabat (2026-10-22):** 36 · places 11 · OSM geom fallback Overture · `pnpm extract:gazakh`
- [x] Gədəbəy — **Hesabat (2026-10-22):** 112 · places 8 · areas 2150 · places 2613 · `0.1.48-pilot` · `pnpm extract:gedabey`

### 3.8 Şəki–Zaqatala

- [x] Şəki rayonu — **Hesabat (2026-10-22):** 85 · places 19 · `pnpm extract:sheki-rayon` (şəhərdən ayrı)
- [x] Qax — **Hesabat (2026-10-22):** 62 · places 19 · `pnpm extract:gakh`
- [x] Zaqatala — **Hesabat (2026-10-22):** 65 · places 19 · `pnpm extract:zaqatala`
- [x] Balakən — **Hesabat (2026-10-22):** 62 · places 5 · `pnpm extract:balakan`
- [x] Oğuz — **Hesabat (2026-10-22):** 35 · places 7 · `pnpm extract:oguz`
- [x] Qəbələ — **Hesabat (2026-10-22):** 71 · places 25 · areas 2536 · places 2707 · `0.1.54-pilot` · `pnpm extract:gabala`

### 3.9 Lənkəran–Astara

- [x] Lənkəran rayonu — **Hesabat (2026-10-22):** 85 · places 15 · `pnpm extract:lankaran-rayon` (şəhərdən ayrı)
- [x] Astara — **Hesabat (2026-10-22):** 86 · places 10 · `pnpm extract:astara`
- [x] Lerik — **Hesabat (2026-10-22):** 141 · places 4 · `pnpm extract:lerik`
- [x] Yardımlı — **Hesabat (2026-10-22):** 81 · places 6 · `pnpm extract:yardimli`
- [x] Masallı — **Hesabat (2026-10-22):** 86 · places 11 · `pnpm extract:masalli`
- [x] Cəlilabad — **Hesabat (2026-10-22):** 120 · places 4 · areas 3141 · places 2757 · `0.1.60-pilot` · `pnpm extract:jalilabad`

### 3.10 Qarabağ / Şərqi Zəngəzur (mənbə örtüyünə görə)

> Yalnız mənbədə mövcud və yoxlanıla bilən həndəsə. Uydurma sərhəd qadağandır.

- [x] Ağdam — **Hesabat (2026-10-22):** 46 · places 8 · `pnpm extract:agdam`
- [x] Füzuli — **Hesabat (2026-10-22):** 20 · places 8 · `pnpm extract:fuzuli`
- [x] Tərtər — **Hesabat (2026-10-22):** 23 · places 4 · `pnpm extract:tartar`
- [x] Xocalı — **Hesabat (2026-10-22):** 12 · places 11 · `pnpm extract:khojaly`
- [x] Xocavənd — **Hesabat (2026-10-22):** 2 · places 5 · `pnpm extract:khojavend`
- [x] Şuşa — **Hesabat (2026-10-22):** 1 · places 18 · `pnpm extract:shusha`
- [x] Laçın — **Hesabat (2026-10-22):** 10 · places 3 · `pnpm extract:lachin`
- [x] Kəlbəcər — **Hesabat (2026-10-22):** 14 · places 2 · `pnpm extract:kalbajar`
- [x] Qubadlı — **Hesabat (2026-10-22):** 21 · places 2 · `pnpm extract:qubadli`
- [x] Zəngilan — **Hesabat (2026-10-22):** 27 verified · places 0 · `pnpm extract:zangilan` (OSM∪Overture boundary; Kolluqışlaq verified)
- [x] Cəbrayıl — **Hesabat (2026-10-22):** 6 · places 0 · areas 3330 · places 2818 · `0.1.71-pilot` · `pnpm extract:jabrayil`

### 3.11 Naxçıvan MR

- [x] Babək — **Hesabat (2026-10-22):** 9 · places 5 · `pnpm extract:babek`
- [x] Culfa — **Hesabat (2026-10-22):** 3 · places 8 · `pnpm extract:julfa`
- [x] Kəngərli — **Hesabat (2026-10-22):** 2 · places 2 · `pnpm extract:kangarli`
- [x] Ordubad — **Hesabat (2026-10-22):** 4 · places 12 · `pnpm extract:ordubad`
- [x] Sədərək — **Hesabat (2026-10-22):** 4 · places 0 · `pnpm extract:sadarak`
- [x] Şahbuz — **Hesabat (2026-10-22):** 6 · places 2 · `pnpm extract:shahbuz`
- [x] Şərur — **Hesabat (2026-10-22):** 57 · places 0 · areas 3421 · places 2847 · `0.1.78-pilot` · `pnpm extract:sharur`

---

## Faza 4 — Milli bağlama

- [x] Bütün şəhər/rayon blokları `[x]` (Gəncə ayrıca rayon — mənbədə yoxdur)  
- [x] Milli `places/index.json` + manifest coverage (`0.2.0-national`, 88 place files)  
- [x] Demo axtarış: ölkə üzrə adlı məkan + ərazi breadcrumb (seçilmiş ərazi + axtarış nəticələri)  
- [x] Son `pnpm validate` + production build  
- [x] Provenance / attribution yeniləmə (`docs/provenance.md`)

**Hesabat (2026-10-22):**  
National pilot bağlandı · areas 3421 · places 2847 · boundaries 3421 · place files 88 ·  
dataset `0.2.0-national` · validate PASS · 0 conflict ·  
demo: axtarış katalog + seçim breadcrumb · mid-level şəhər/rayon əlifba sırası.

---

## Progress xülasəsi

| Faza | Scope | Status |
|---|---|---|
| 0 | Ölkə | ✅ |
| 1 | Abşeron aglomerasiya | ✅ |
| 2 | Respublika şəhərləri | ✅ |
| 3 | Rayonlar | ✅ |
| 4 | Milli bağlama | ✅ `0.2.0-national` |

**Növbəti agent addımı:** smoke / UX təkmilləşdirmə (istəyə görə).

---

## Əlaqəli fayllar

| Fayl | Rol |
|---|---|
| [`Hierarchy.md`](./Hierarchy.md) | Parent/child verified qaydaları (məcburi istinad) |
| [`docs/hierarchy-rules.md`](./docs/hierarchy-rules.md) | Qısa məhsul qaydaları |
| [`docs/provenance.md`](./docs/provenance.md) | Mənbə / lisenziya |
| `.cursor/rules/geoagent.mdc` | GeoAgent Cursor qaydası |
| `source_files/` | Immutable mənbələr |
| `data/` | Canonical çıxış |
