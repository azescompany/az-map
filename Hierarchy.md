# GeoAtlas Azərbaycan — Hierarchy (agent working note)

Bu fayl **Yasamal nümunəsinə** əsasən ərazi iyerarxiyasının necə qurulduğunu
və digər şəhər/rayonlara necə tətbiq ediləcəyini təsvir edir.

**İş növbəsi / checkbox hesabat:** [`WORKER.md`](./WORKER.md)  
**GeoAgent qaydası:** `.cursor/rules/geoagent.mdc`

Mənbə faylləri (`source_files/`) dəyişdirilmir; yalnız `data/` yazılır.

## UI cascade

```
Ölkə → Şəhər → Rayon → Məhəllə / qəsəbə → Tanınmış məkan
```

- Dropdown-larda yalnız `parent_status = verified` uşaqlar görünür.
- Adsız məkanlar UI-da gizlədilir (`nameStatus != named` / `filterNamedPlaces`).
- Rayon / məhəllə dəyişəndə uyğun olmayan məkan seçimi sıfırlanır.
- Tanınmış məkanlar seçilmiş əraziyə görə **places cascade** ilə yüklənir
  (`loadPlacesForArea` — aşağıdakı bölmə); UI əlavə hack yazmır.

## Yasamal nümunə ağacı (verified UI)

```
Azərbaycan                          (country · Overture + OSM)
 └── Bakı                           (city · OSM admin relation)
      └── Yasamal rayonu            (rayon · OSM admin_level 7/8)
           ├── 2-ci Alatava         (macrohood · Overture parent=Yasamal + containment)
           ├── Yeni Yasamal         (microhood · Overture parent=Yasamal + containment)
           ├── Yasamal              (macrohood · Overture parent=Yasamal + containment)
           ├── Mirvari Park kompleksi
           └── Park Yasamal YK
```

Xüsusi qayda: **1-ci Alatava** → `Nəsimi rayonu` (Yasamal uşağı deyil).

Extract nəticəsi: `data/reviews/baki_neighborhoods_extract.json`

## Parent / child təsdiq qaydaları (Yasamal ilə eyni)

Uşaq (məhəllə / qəsəbə / mikrorayon) UI-da **verified** sayılır yalnız belədirsə:

1. **Ad** — boş olmayan mənbə adı (`names.primary` və ya OSM `name`).
2. **Mənbə ID** — sabit Overture `division.id` (və mümkünsə OSM relation/way).
3. **Overture parent** — `parent_division_id` seçilmiş **rayon locality** id-sinə bərabərdir.
4. **Sərhəd həndəsəsi** — `division_area` polygon/multipolygon mövcuddur (uydurma yoxdur).
5. **Containment** — uşağın `representative_point`-i valideyn rayon polygonunda (covers/intersects).
6. **Tip** — `microhood` | `macrohood` | `neighborhood` | `locality` (qəsəbə).

**Verified edilmir / UI-dan çıxarılır:**

| Hal | `parent_status` | Qeyd |
|---|---|---|
| Parent id uyğun gəlmir | `conflict` | review yazılır |
| Containment uğursuz | `conflict` | review yazılır |
| Həndəsə yoxdur | `missing` | sərhəd çəkilmir |
| Ad = `Bakı` və ya `* rayonu` | skip | iyerarxiya qarışıqlığı |
| Yalnız ada görə merge | qadağan | Wikidata / id / geom tələb olunur |

**Vacib:** Admin parent ≠ təkbaşına containment; hər ikisi saxlanılır.
**Vacib:** Adlı məkan avtomatik coğrafi `verified` sayılmır.

## Rayon / şəhər səviyyəsi (artıq var)

Bakı rayonları OSM admin relation-larından gəlir (Overture Bakı region parent
siyahısı natamamdır — tək mənbə kimi istifadə olunmur):

Yasamal, Nəsimi, Nərimanov, Nizami, Binəqədi, Səbail, Xətai, Sabunçu,
Suraxanı, Xəzər, Pirallahı, Qaradağ.

**Sumqayıt** (city, OSM al=8 core + al=6 municipal extent): məhəllə/qəsəbə
birbaşa şəhərin verified uşaqlarıdır — sintetik rayon yaradılmır.
Skript: `pnpm extract:sumqayit`.

**Abşeron rayonu** (top-level `type=rayon` under country, OSM al=6):
UI mid-level “Şəhər / rayon”. Uşaqlar: Masazır, Xırdalan (+microhood), digər qəsəbələr.
Skriptlər: `pnpm extract:masazir` · `pnpm extract:xirdalan` · `pnpm extract:absheron`.

**Gəncə** (city under country, OSM al=6 `Gəncə İnzibati Ərazisi`): Bakı kimi
`Şəhər → Rayon (Kəpəz, Nizami) → məhəllə`. Skript: `pnpm extract:gence`.
Qeyd: Overture “Nizami” uşaqları Bakı Nizami-yə aid deyil.

**Mingəçevir** (city-direct, Sumqayıt kimi): `pnpm extract:mingachevir`.

**Şirvan** (city-direct): `pnpm extract:shirvan` — Sumqayıt uşağı «Şirvan qəsəbəsi» deyil.

**Naftalan** (city-direct): `pnpm extract:naftalan`.

**Yevlax şəhər** (city-direct mikrorayon; rayon kəndləri ayrıca): `pnpm extract:yevlax`.

**Lənkəran şəhər** (city-direct; rayon kəndləri ayrıca): `pnpm extract:lankaran`.

**Şəki şəhər:** `pnpm extract:sheki` · **Naxçıvan şəhər:** `pnpm extract:nakhchivan`.

**Xızı rayonu** (top-level rayon, Absheron kimi): `pnpm extract:khizi`.

**Milli bağlama (Faza 4):** dataset `0.2.0-national` — bütün inzibati rayonlar +
respublika şəhərləri extract olunub; demo axtarış `places/index.json` katalogu +
seçilmiş ərazi breadcrumb.

## Məhəllə / qəsəbə extract (bütün Bakı rayonları)

Skript: `pnpm extract:baki-hoods` → `scripts/extract_baki_neighborhoods.py`

Hər rayon üçün:

1. Overture-də eyni adlı `locality` tap.
2. `parent_division_id == rayon.locality.id` olan uşaqları götür.
3. Yuxarıdakı verified qaydalarını tətbiq et.
4. Mövcud Yasamal/Nəsimi qeydlərini (eyni Overture id) təkrar yazma.
5. `data/areas/areas.json` + `data/boundaries/neighborhood_*.geojson` yenilə.
6. `pnpm quality:gate` ilə mərkəz / CRS / geom_status yenilə.

Qaradağ: Overture-də `Qaradağ rayonu` locality tapılmaya bilər → uşaqlar
yalnız başqa sübutla (gələcək review); uydurma əlavə olunmur.

## Tanınmış məkanlar

Skript: `pnpm extract:baki-places` (və digər regional extract-lər) →
`data/places/{key}_all.json` + `data/places/index.json`.

Extract modeli (dəyişmir):

- Landmark taxonomy (park, muzey, historic, …) + adlı OSM node-lar.
- `area_id` = **rayon** (və ya şəhər-direct / settlement extract id); kütləvi
  məhəlləyə köçürmə bu fazada yoxdur.
- Polygon olmayan məkanlar nöqtə kimi qalır (sərhəd uydurulmur).
- Sintetik `baki_all.json` və ya digər uydurma aggregate fayl **yaradılmır**.

### Places cascade (UI / `loadPlacesForArea`)

Seçilmiş əraziyə görə adlı məkanların yüklənməsi ierarxiya ilə uyğundur:

| Seçim | Davranış |
| --- | --- |
| **Ölkə** | Boş (dəyişmir) |
| **Şəhər** (Bakı, Gəncə, …) — verified rayon uşaqları varsa | Hər verified uşaq rayonu (və şəhərə birbaşa bağlı, öz places faylı olan settlement) üçün mövcud `{key}_all.json` yüklənir, **place.id** üzrə dedupe, birləşmə qaytarılır |
| **Şəhər** city-direct (Sumqayıt, …) — rayon uşağı yox | Öz `places/{key}_all.json` (indiki) |
| **Rayon** (Yasamal və s.) | Həmin rayon's places faylının tam siyahısı |
| **Ölkəaltı rayon** (Abşeron) — uşaq settlement-lərin ayrı places faylı varsa | Öz fayl + fərqli uşaq faylları (Masazır/Xırdalan), id dedupe |
| **Məhəllə / qəsəbə / microhood** | Parent places faylından: əvvəl `area_id === area.id`, yoxdursa **bbox** filter; digər rayonların məkanları düşməsin |

Qadağalar: uydurma parent / ad / polygon yox; ada görə merge yox; `source_files/` toxunulmur.

## Yenidən generasiya ardıcıllığı

```bash
pnpm extract:pilot          # ölkə / Bakı / rayon sərhədləri (lazım olanda)
pnpm extract:baki-hoods     # məhəllə / qəsəbə (bu sənəd)
pnpm extract:baki-places    # tanınmış məkanlar
pnpm quality:gate
pnpm validate
```

## Əlaqəli sənədlər

- `docs/hierarchy-rules.md` — qısa məhsul qaydaları
- `docs/provenance.md` — mənbə / lisenziya
