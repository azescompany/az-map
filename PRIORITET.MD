Prioritet düzgündür. Aşağıda **sıra + nə etmək + mənim əlavələrim** — implement Ask mode-da yox, Agent-ə verəndə bu planla get.

---

## Prioritet sırası (razılaşdırılmış)

| # | İş | Niyə əvvəl | Status |
|---|---|---|---|
| **P0** | Data CDN base URL | Bunsuz npm/demo “git data” ilə işləmir | **DONE** — tag `v0.2.0-national` |
| **P1** | `@geoatlas/data` + demo CDN/default | İstənilən app `npm`/`pnpm` ilə eyni mənbə | **DONE** — `DEFAULT_DATA_BASE` |
| **P2** | Landmark Agent (rules + `LANDMARK.md` / report) | Hierarchy sabit qalır; places hissə-hissə | **Rules genişləndirildi** (dedupe, taxonomy, küçə, git+pin DoD) · enrich: `LANDMARK.md` növbəsi |

Git: `azescompany/az-map` @ tag `v0.2.0-national` (= `d80cf64`).

---

## P0 — Lokal → CDN ✅

**Base (pin):**

```text
https://cdn.jsdelivr.net/gh/azescompany/az-map@v0.2.1-national/data/
```

Nümunə: `manifest.json`, `areas/areas.json`, `places/yasamal_all.json`, `boundaries/city_baki.geojson`.

**Kod:** `@geoatlas/data` → `DEFAULT_DATA_BASE`; demo → eyni default.
Override: `VITE_GEOATLAS_DATA_BASE=local` (Vite `publicDir`) və ya `http://localhost:1555/`.
Ətraflı: [`apps/demo/README.md`](apps/demo/README.md).

---

## P1 — NPM paket + istənilən app ✅

```ts
import { DEFAULT_DATA_BASE, loadAreas } from "@geoatlas/data";
const areas = await loadAreas(DEFAULT_DATA_BASE);
```

Paketə GeoJSON kopyalanmır — yalnız URL + loader. Public npm publish bu sprintdə məcburi deyil.

---

## P2 — Landmark Agent (hierarchy pozmadan) ✅ scaffold

**Status:** qaydalar = dedupe / taxonomy / küçə; **git push LƏĞV** (lokal `data/`). Demo: `local` + `CDN` ayrı env. Enrich: [`LANDMARK.md`](LANDMARK.md). Git: Bakı bitəndə Worker.

| Fayl | Rol |
|---|---|
| [`.cursor/rules/landmark-agent.mdc`](.cursor/rules/landmark-agent.mdc) | Agent kimliyi, qadağalar, DoD |
| [`LANDMARK.md`](LANDMARK.md) | Checkbox iş növbəsi (WORKER üslubu) |
| [`data/reviews/landmark_report.md`](data/reviews/landmark_report.md) | Blok jurnalı |
| `Hierarchy.md` + `docs/hierarchy-rules.md` | **oxu** (areas/boundaries yazma) |

**Agent vəzifəsi (qısa):** `LANDMARK.md` ilk `[ ]` → yalnız `data/places/*` + index/review →
mənbə `source_files/` oxu → geniş taxonomy (named) → dedupe → küçə disambiguate →
containment → `pnpm validate` + `pnpm test:named-places` → `[x]` + hesabat.
**Git/push/tag/pin — etmə.**

**Addımlar:** inventar → namizəd → join/dedupe → street → assign → yaz → validate → report (lokal).

---

## Mənim əlavələrim (vacib)

1. **Pin version:** CDN-də `main` yox, **git tag** = `dataset_version` — breaking data sürprizi olmasın.  
2. **Lazy load qalsın:** areas bir dəfə; boundary/places seçimə görə — 100–1000 user üçün.  
3. **Lokal fallback:** `GEOATLAS_DATA_BASE=local` → Vite `publicDir` (offline extract).  
4. **Health:** `GET manifest` + `dataset_version` UI-da göstər (hansı release).  
5. **Landmark scope bir rayon/blok** — bütün ölkə bir PR-da yox.  
6. **Lisenziya:** OSM/Overture attribution `manifest` / README-də qalsın (CDN public olanda).  
7. **Hooks bug** (`App.tsx` early return) — CDN-dən əvvəl və ya eyni PR-da düzəlt; demo çökürsə P0 korlanır.  
8. **Paketə data qoyma** — yalnız URL + loader; npm ölçüsü kiçik qalsın.  
9. **jsDelivr purge/cache:** data update → yeni tag; köhnə pin qorunur.  
10. **P2-də areas.json hierarchy-ni “düzəltmə”** — Landmark yalnız places.

---

## Tövsiyə olunan icra sırası (agent sprint)

```text
Sprint A (P0): DONE — CDN pin v0.2.0-national
Sprint B (P1): DONE — DEFAULT_DATA_BASE + demo
Sprint C (P2): scaffold DONE — enrich: LANDMARK.md → Yasamal [ ]
```

**Növbəti iş:** LandmarkAgent — `LANDMARK.md` növbəti `[ ]` (lokal enrich). Bakı bitəndə Worker git deploy.