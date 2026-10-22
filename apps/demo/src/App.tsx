import { useCallback, useEffect, useMemo, useState } from "react";
import type { Area, Manifest, Place, ReviewItem } from "@geoatlas/types";
import {
  areaBreadcrumb,
  boundaryDisplayMode,
  categoryLabel,
  centerOf,
  cityHasRayonLevel,
  filterNamedPlaces,
  filterPlacesByCategory,
  getArea,
  loadAreas,
  loadBoundary,
  loadManifest,
  loadAllCatalogPlaces,
  loadPlacesForArea,
  loadReviews,
  searchAreas,
  searchPlaces,
  verifiedChildrenOf,
  verifiedChildrenOfType,
} from "@geoatlas/data";
import MapView from "./MapView";
import GeoJSONInspector from "./GeoJSONInspector";
import SearchableSelect from "./components/SearchableSelect";
import TruncatedText from "./components/TruncatedText";
import { resolveAppMode } from "./appMode";

const DATA_BASE = ""; // Vite publicDir = ../../data
const APP_MODE = resolveAppMode();
const IS_CUSTOMER = APP_MODE === "customer";

const CATEGORIES = [
  "all",
  "historic",
  "park",
  "museum",
  "monument",
  "religious",
  "tourism",
  "culture",
  "stadium",
  "education",
  "government",
] as const;

export default function App() {
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [areas, setAreas] = useState<Area[]>([]);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [countryId, setCountryId] = useState<string>("");
  const [cityId, setCityId] = useState<string>("");
  const [rayonId, setRayonId] = useState<string>("");
  const [neighborhoodId, setNeighborhoodId] = useState<string>("");
  /** Optional drill-down under a settlement (e.g. Xırdalan → 24-cü Məhəllə). */
  const [microhoodId, setMicrohoodId] = useState<string>("");

  const [selectedAreaId, setSelectedAreaId] = useState<string | null>(null);
  const [countryBoundary, setCountryBoundary] =
    useState<GeoJSON.FeatureCollection | null>(null);
  const [selectedBoundary, setSelectedBoundary] =
    useState<GeoJSON.FeatureCollection | null>(null);
  const [boundaryLoading, setBoundaryLoading] = useState(false);
  const [boundaryLoadError, setBoundaryLoadError] = useState<string | null>(
    null,
  );
  const [places, setPlaces] = useState<Place[]>([]);
  const [catalogPlaces, setCatalogPlaces] = useState<Place[]>([]);
  const [placesLoading, setPlacesLoading] = useState(false);
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null);
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]>("all");
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const [m, a, r] = await Promise.all([
          loadManifest(DATA_BASE || "/"),
          loadAreas(DATA_BASE || "/"),
          loadReviews(DATA_BASE || "/"),
        ]);
        if (cancelled) return;
        setManifest(m);
        setAreas(a);
        setReviews(r);
        const country = a.find((x) => x.type === "country");
        const catalog = filterNamedPlaces(await loadAllCatalogPlaces("/"));
        if (!cancelled) setCatalogPlaces(catalog);
        if (country) {
          setCountryId(country.id);
          setSelectedAreaId(country.id);
          setBoundaryLoading(true);
          setBoundaryLoadError(null);
          try {
            const gj = await loadBoundary("/", country);
            if (!cancelled) {
              setCountryBoundary(gj);
              setSelectedBoundary(gj);
              if (!gj) setBoundaryLoadError("Ölkə sərhədi yüklənmədi");
            }
          } catch {
            if (!cancelled)
              setBoundaryLoadError("Ölkə sərhədi yüklənərkən xəta");
          } finally {
            if (!cancelled) setBoundaryLoading(false);
          }
        }
      } catch (e) {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Dataset yüklənmədi");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedArea = selectedAreaId
    ? getArea(areas, selectedAreaId)
    : undefined;
  const selectedCenter = selectedArea ? centerOf(selectedArea) : null;
  const mapBoundaryMode = selectedArea
    ? boundaryDisplayMode(selectedArea)
    : "none";

  // Mid-level under country: şəhər (Bakı, Sumqayıt) OR top-level rayon (Abşeron).
  const midLevelUnits = useMemo(() => {
    if (!countryId) return [];
    return verifiedChildrenOf(areas, countryId)
      .filter((a) => a.type === "city" || a.type === "rayon")
      .slice()
      .sort((a, b) => a.name.localeCompare(b.name, "az"));
  }, [areas, countryId]);

  const selectedMid = cityId ? getArea(areas, cityId) : undefined;

  // District rayons only under a city (Bakı). Hidden for Sumqayıt / Abşeron.
  const rayons = useMemo(
    () =>
      selectedMid?.type === "city"
        ? verifiedChildrenOfType(areas, cityId, "rayon")
        : [],
    [areas, cityId, selectedMid?.type],
  );
  const showRayonDropdown = Boolean(
    selectedMid?.type === "city" && cityHasRayonLevel(areas, cityId),
  );

  const hoodTypes = ["neighborhood", "settlement"] as const;

  // Bakı: city→rayon→məhəllə | Sumqayıt: city→məhəllə | Abşeron: rayon→qəsəbə/şəhər
  const neighborhoods = useMemo(() => {
    if (showRayonDropdown) {
      return rayonId
        ? verifiedChildrenOfType(areas, rayonId, [...hoodTypes])
        : [];
    }
    if (cityId) {
      return verifiedChildrenOfType(areas, cityId, [...hoodTypes]);
    }
    return [];
  }, [areas, rayonId, cityId, showRayonDropdown]);

  // Xırdalan-style: settlement has its own verified microhood children
  const microhoods = useMemo(
    () =>
      neighborhoodId
        ? verifiedChildrenOfType(areas, neighborhoodId, [...hoodTypes])
        : [],
    [areas, neighborhoodId],
  );
  const showMicrohoodDropdown = microhoods.length > 0;

  const namedPlaces = useMemo(() => filterNamedPlaces(places), [places]);
  const filteredPlaces = useMemo(
    () => filterPlacesByCategory(namedPlaces, category),
    [namedPlaces, category],
  );

  const selectedPlace = selectedPlaceId
    ? (namedPlaces.find((p) => p.id === selectedPlaceId) ??
      catalogPlaces.find((p) => p.id === selectedPlaceId))
    : undefined;

  // Category filter clears incompatible place selection.
  useEffect(() => {
    if (!selectedPlaceId) return;
    if (!filteredPlaces.some((p) => p.id === selectedPlaceId)) {
      // Keep selection if place is only in catalog (search) but still matches category.
      const fromCatalog = catalogPlaces.find((p) => p.id === selectedPlaceId);
      if (
        fromCatalog &&
        (category === "all" || fromCatalog.category === category)
      ) {
        return;
      }
      setSelectedPlaceId(null);
    }
  }, [category, filteredPlaces, selectedPlaceId, catalogPlaces]);

  const selectArea = useCallback(
    async (
      area: Area,
      opts?: { placeId?: string | null; clearPlace?: boolean },
    ) => {
      setSelectedAreaId(area.id);
      if (opts?.placeId != null) {
        setSelectedPlaceId(opts.placeId);
      } else if (opts?.clearPlace !== false) {
        setSelectedPlaceId(null);
      }

      if (area.type === "country") {
        setCountryId(area.id);
        setCityId("");
        setRayonId("");
        setNeighborhoodId("");
        setMicrohoodId("");
      } else if (area.type === "city") {
        setCountryId(area.parent_id ?? countryId);
        setCityId(area.id);
        setRayonId("");
        setNeighborhoodId("");
        setMicrohoodId("");
      } else if (area.type === "rayon") {
        const parent = area.parent_id
          ? getArea(areas, area.parent_id)
          : undefined;
        if (parent?.type === "country") {
          setCountryId(parent.id);
          setCityId(area.id);
          setRayonId("");
          setNeighborhoodId("");
          setMicrohoodId("");
        } else {
          setCityId(area.parent_id ?? cityId);
          setRayonId(area.id);
          setNeighborhoodId("");
          setMicrohoodId("");
          if (parent?.parent_id) setCountryId(parent.parent_id);
        }
      } else if (area.type === "neighborhood" || area.type === "settlement") {
        const parent = area.parent_id
          ? getArea(areas, area.parent_id)
          : undefined;
        if (
          parent &&
          (parent.type === "neighborhood" || parent.type === "settlement")
        ) {
          // Microhood under settlement (Xırdalan → 24-cü Məhəllə)
          setMicrohoodId(area.id);
          setNeighborhoodId(parent.id);
          const grand = parent.parent_id
            ? getArea(areas, parent.parent_id)
            : undefined;
          if (grand?.type === "rayon") {
            const great = grand.parent_id
              ? getArea(areas, grand.parent_id)
              : undefined;
            if (great?.type === "country") {
              setCountryId(great.id);
              setCityId(grand.id);
              setRayonId("");
            } else {
              setRayonId(grand.id);
              if (grand.parent_id) setCityId(grand.parent_id);
              if (great?.parent_id) setCountryId(great.parent_id);
            }
          } else if (grand?.type === "city") {
            setCityId(grand.id);
            setRayonId("");
            if (grand.parent_id) setCountryId(grand.parent_id);
          }
        } else {
          setMicrohoodId("");
          setNeighborhoodId(area.id);
          if (parent?.type === "city") {
            setCityId(parent.id);
            setRayonId("");
            if (parent.parent_id) setCountryId(parent.parent_id);
          } else if (parent?.type === "rayon") {
            const grand = parent.parent_id
              ? getArea(areas, parent.parent_id)
              : undefined;
            if (grand?.type === "country") {
              setCountryId(grand.id);
              setCityId(parent.id);
              setRayonId("");
            } else {
              setRayonId(parent.id);
              if (parent.parent_id) {
                setCityId(parent.parent_id);
                if (grand?.parent_id) setCountryId(grand.parent_id);
              }
            }
          }
        }
      }

      setBoundaryLoading(true);
      setBoundaryLoadError(null);
      try {
        const gj = await loadBoundary("/", area);
        setSelectedBoundary(gj);
        if (area.boundary_file && !gj) {
          setBoundaryLoadError(
            `Sərhəd yüklənmədi: ${area.boundary_file}`,
          );
        } else if (!area.boundary_file || area.geom_status === "missing") {
          setBoundaryLoadError("Bu ərazi üçün sərhəd məlumatı yoxdur");
        }
      } catch {
        setSelectedBoundary(null);
        setBoundaryLoadError("Sərhəd GeoJSON yüklənərkən xəta baş verdi");
      } finally {
        setBoundaryLoading(false);
      }

      setPlacesLoading(true);
      try {
        const pls = await loadPlacesForArea("/", area, areas);
        setPlaces(pls);
        if (opts?.placeId) {
          const named = filterNamedPlaces(pls);
          if (!named.some((p) => p.id === opts.placeId)) {
            // Place may still be valid via catalog (same rayon file).
            const cat = catalogPlaces.find((p) => p.id === opts.placeId);
            if (!cat) setSelectedPlaceId(null);
          }
        }
      } finally {
        setPlacesLoading(false);
      }
    },
    [areas, cityId, countryId, rayonId, catalogPlaces],
  );

  const selectPlaceById = useCallback(
    (placeId: string) => {
      const place =
        namedPlaces.find((p) => p.id === placeId) ??
        catalogPlaces.find((p) => p.id === placeId);
      if (!place) return;
      setSelectedPlaceId(place.id);
      if (place.area_id) {
        const a = getArea(areas, place.area_id);
        if (a) void selectArea(a, { placeId: place.id, clearPlace: false });
      }
    },
    [namedPlaces, catalogPlaces, areas, selectArea],
  );

  const areaHits = useMemo(
    () => searchAreas(areas, query, 12),
    [areas, query],
  );
  const placeHits = useMemo(
    () => searchPlaces(catalogPlaces, query, 12),
    [catalogPlaces, query],
  );

  const midOptions = useMemo(
    () =>
      midLevelUnits.map((a) => ({
        id: a.id,
        label: a.type === "rayon" ? `${a.name} (rayon)` : a.name,
      })),
    [midLevelUnits],
  );
  const rayonOptions = useMemo(
    () =>
      rayons.map((a) => ({
        id: a.id,
        label:
          a.geom_status !== "verified"
            ? `${a.name} (${a.geom_status})`
            : a.name,
      })),
    [rayons],
  );
  const neighborhoodOptions = useMemo(
    () => neighborhoods.map((a) => ({ id: a.id, label: a.name })),
    [neighborhoods],
  );
  const microhoodOptions = useMemo(
    () => microhoods.map((a) => ({ id: a.id, label: a.name })),
    [microhoods],
  );
  const placeOptions = useMemo(
    () =>
      filteredPlaces.map((p) => ({
        id: p.id,
        label: p.displayName ?? p.name,
      })),
    [filteredPlaces],
  );

  if (loading) {
    return (
      <div className="loading">
        <strong>GeoAtlas yüklənir…</strong>
        <span className="meta">Canonical dataset oxunur</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <strong>Xəta</strong>
        <div>{error}</div>
        <span className="meta">
          `pnpm validate` və `data/` mövcudluğunu yoxlayın
        </span>
      </div>
    );
  }

  const countryName =
    (countryId ? getArea(areas, countryId)?.name : undefined) ?? "Azərbaycan";

  const hoodEmptyHint = showRayonDropdown && !rayonId && cityId
    ? "Əvvəlcə rayon seçin."
    : !neighborhoods.length &&
        ((showRayonDropdown && rayonId) || (!showRayonDropdown && cityId))
      ? IS_CUSTOMER
        ? "Bu ərazi üçün məhəllə/qəsəbə yoxdur."
        : "Bu ərazi üçün verified məhəllə/qəsəbə yoxdur (bax reviews)."
      : undefined;

  const placeEmptyHint = placesLoading
    ? "Məkanlar yüklənir…"
    : filteredPlaces.length
      ? IS_CUSTOMER
        ? `${filteredPlaces.length} məkan`
        : `${filteredPlaces.length} adlı məkan (adsız gizlədilib)`
      : cityId || rayonId || neighborhoodId
        ? "Bu ərazidə adlı məkan yoxdur"
        : showRayonDropdown
          ? "Rayon və ya məhəllə seçin"
          : "Şəhər və ya məhəllə seçin";

  return (
    <div className={`app mode-${APP_MODE}`}>
      <aside className="sidebar">
        <div className="brand">
          <h1>GeoAtlas Azərbaycan</h1>
          <p className="map-title">{countryName} xəritəsi</p>
          {!IS_CUSTOMER && (
            <p>
              Şəhər/rayon → (daxili rayon, varsa) → məhəllə/qəsəbə → məkan.
              Daxili rayon yoxdursa o səviyyə gizlidir.
            </p>
          )}
        </div>

        {!IS_CUSTOMER && (
          <div className="badge-row">
            <span className="badge ok">{APP_MODE}</span>
            <span className="badge ok">
              {manifest?.dataset_version ?? "—"}
            </span>
            <span className="badge">
              {manifest?.coverage.areas ?? areas.length} area
            </span>
            <span className="badge">
              {manifest?.coverage.places ?? "?"} place
            </span>
            <span className="badge warn">{reviews.length} review</span>
          </div>
        )}

        <div className="field">
          <label>Axtarış</label>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ərazi və ya məkan adı…"
            aria-label="Axtarış"
          />
        </div>

        {query.trim() && (
          <ul className="search-results">
            {areaHits.map((a) => (
              <li key={a.id}>
                <button
                  type="button"
                  onClick={() => {
                    setQuery("");
                    void selectArea(a);
                  }}
                >
                  <TruncatedText text={a.name} as="strong" />
                  <div className="meta">
                    <TruncatedText
                      text={`${IS_CUSTOMER ? "" : `area · ${a.type} · `}${areaBreadcrumb(areas, a.id)}`}
                    />
                  </div>
                </button>
              </li>
            ))}
            {placeHits.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => {
                    setQuery("");
                    selectPlaceById(p.id);
                  }}
                >
                  <TruncatedText
                    text={p.displayName ?? p.name}
                    as="strong"
                  />
                  <div className="meta">
                    <TruncatedText
                      text={`${IS_CUSTOMER ? "" : `place · ${categoryLabel(String(p.category))} · `}${areaBreadcrumb(areas, p.area_id)}`}
                    />
                  </div>
                </button>
              </li>
            ))}
            {!areaHits.length && !placeHits.length && (
              <li>
                <div className="empty" style={{ padding: "0.75rem" }}>
                  Nəticə yoxdur
                </div>
              </li>
            )}
          </ul>
        )}

        <div className="cascade">
          <SearchableSelect
            label="Şəhər / rayon"
            options={midOptions}
            value={cityId}
            disabled={!midLevelUnits.length}
            onChange={(id) => {
              if (!id) {
                const country = countryId
                  ? getArea(areas, countryId)
                  : undefined;
                if (country) void selectArea(country);
                return;
              }
              const a = getArea(areas, id);
              if (a) void selectArea(a);
            }}
          />

          {showRayonDropdown && (
            <SearchableSelect
              label="Rayon"
              options={rayonOptions}
              value={rayonId}
              disabled={!rayons.length}
              onChange={(id) => {
                if (!id) {
                  const city = cityId ? getArea(areas, cityId) : undefined;
                  if (city) void selectArea(city);
                  return;
                }
                const a = getArea(areas, id);
                if (a) void selectArea(a);
              }}
            />
          )}

          <SearchableSelect
            label="Məhəllə / qəsəbə"
            options={neighborhoodOptions}
            value={neighborhoodId}
            disabled={
              !neighborhoods.length || (showRayonDropdown && !rayonId)
            }
            emptyHint={hoodEmptyHint}
            onChange={(id) => {
              if (!id) {
                const parent = showRayonDropdown
                  ? rayonId
                    ? getArea(areas, rayonId)
                    : undefined
                  : cityId
                    ? getArea(areas, cityId)
                    : undefined;
                if (parent) void selectArea(parent);
                else setNeighborhoodId("");
                return;
              }
              const a = getArea(areas, id);
              if (a) void selectArea(a);
            }}
          />

          {showMicrohoodDropdown && (
            <SearchableSelect
              label="Mikrorayon / məhəllə"
              options={microhoodOptions}
              value={microhoodId}
              onChange={(id) => {
                if (!id) {
                  const parent = neighborhoodId
                    ? getArea(areas, neighborhoodId)
                    : undefined;
                  if (parent) void selectArea(parent);
                  else setMicrohoodId("");
                  return;
                }
                const a = getArea(areas, id);
                if (a) void selectArea(a);
              }}
            />
          )}

          <SearchableSelect
            label="Tanınmış məkan"
            options={placeOptions}
            value={selectedPlaceId ?? ""}
            disabled={!filteredPlaces.length}
            emptyHint={placeEmptyHint}
            onChange={(id) => {
              if (!id) {
                setSelectedPlaceId(null);
                return;
              }
              setSelectedPlaceId(id);
            }}
          />
        </div>

        {selectedArea && (
          <div className="detail">
            <h2>
              <TruncatedText text={selectedArea.name} as="span" />
            </h2>
            <p className="meta breadcrumb">
              <TruncatedText
                text={areaBreadcrumb(areas, selectedArea.id)}
              />
            </p>
            {!IS_CUSTOMER && (
              <>
                <div className="badge-row">
                  <StatusBadge
                    label={`parent: ${selectedArea.parent_status}`}
                    tone={toneFor(selectedArea.parent_status)}
                  />
                  <StatusBadge
                    label={`boundary: ${selectedArea.geom_status}`}
                    tone={toneFor(selectedArea.geom_status)}
                  />
                  <StatusBadge
                    label={`center: ${selectedArea.center_status ?? "missing"}`}
                    tone={toneFor(
                      String(selectedArea.center_status ?? "missing"),
                    )}
                  />
                </div>
                {selectedArea.geom_status !== "verified" && (
                  <p className="meta">
                    Sərhəd dəqiq verified deyil
                    {selectedArea.geom_status_reason
                      ? ` — ${selectedArea.geom_status_reason}`
                      : ""}
                    . Xəritədə{" "}
                    {mapBoundaryMode === "partial_outline"
                      ? "qırıq xətt / xəbərdarlıq rəngi"
                      : "sərhəd çəkilmir"}
                    .
                  </p>
                )}
                <dl>
                  <dt>Tip</dt>
                  <dd>
                    {selectedArea.type}
                    {selectedArea.subtype
                      ? ` / ${selectedArea.subtype}`
                      : ""}
                  </dd>
                  <dt>Wikidata</dt>
                  <dd>{selectedArea.wikidata ?? "—"}</dd>
                  <dt>Mərkəz</dt>
                  <dd>
                    {selectedCenter
                      ? `${selectedCenter.latitude.toFixed(6)}, ${selectedCenter.longitude.toFixed(6)}`
                      : "missing"}
                  </dd>
                  <dt>Center method</dt>
                  <dd>
                    {selectedArea.center_method ?? "—"}
                    {selectedArea.center_within_boundary == null
                      ? ""
                      : selectedArea.center_within_boundary
                        ? " · within boundary"
                        : " · OUTSIDE boundary"}
                  </dd>
                  <dt>Boundary</dt>
                  <dd>
                    <TruncatedText
                      text={selectedArea.boundary_file ?? "—"}
                    />
                  </dd>
                  <dt>CRS</dt>
                  <dd>{selectedArea.crs ?? "—"}</dd>
                  <dt>Məkanlar</dt>
                  <dd>
                    {placesLoading
                      ? "yüklənir…"
                      : `${filteredPlaces.length} adlı / ${places.length} cəmi`}
                  </dd>
                </dl>
                {selectedArea.notes && (
                  <p className="meta">
                    <TruncatedText text={selectedArea.notes} />
                  </p>
                )}
              </>
            )}
          </div>
        )}

        <div className="field">
          <label>Kateqoriya filtri</label>
          <div className="filters">
            {CATEGORIES.map((c) => (
              <button
                key={c}
                type="button"
                className={category === c ? "on" : ""}
                onClick={() => setCategory(c)}
              >
                {categoryLabel(c)}
              </button>
            ))}
          </div>
        </div>

        {selectedPlace && (
          <div className="detail">
            <h2>
              <TruncatedText
                text={selectedPlace.displayName ?? selectedPlace.name}
                as="span"
              />
            </h2>
            {IS_CUSTOMER ? (
              <p className="meta">
                <TruncatedText
                  text={`${categoryLabel(String(selectedPlace.category))}${
                    selectedPlace.area_id
                      ? ` · ${getArea(areas, selectedPlace.area_id)?.name ?? ""}`
                      : ""
                  }`}
                />
              </p>
            ) : (
              <dl>
                <dt>ID</dt>
                <dd>
                  <code>{selectedPlace.id}</code>
                </dd>
                <dt>Kateqoriya</dt>
                <dd>{categoryLabel(String(selectedPlace.category))}</dd>
                <dt>Name status</dt>
                <dd>{selectedPlace.nameStatus ?? "named"}</dd>
                <dt>Yoxlama</dt>
                <dd>
                  {selectedPlace.verificationStatus ??
                    selectedPlace.area_assign_status ??
                    "—"}
                </dd>
                <dt>Area</dt>
                <dd>
                  {selectedPlace.area_id
                    ? (getArea(areas, selectedPlace.area_id)?.name ??
                      selectedPlace.area_id)
                    : "—"}
                </dd>
                <dt>Mənbə</dt>
                <dd>
                  <TruncatedText
                    text={selectedPlace.source_refs
                      .map((r) => `${r.source}:${r.source_id}`)
                      .join(", ")}
                  />
                </dd>
              </dl>
            )}
          </div>
        )}

        {!IS_CUSTOMER && !!reviews.length && (
          <div className="detail">
            <h2>Açıq review-lar</h2>
            <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
              {reviews.slice(0, 6).map((r) => (
                <li key={r.id} className="meta">
                  <strong>{r.entity}</strong> — {r.kind}: {r.detail}
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="attribution">
          {IS_CUSTOMER
            ? "© GeoAtlas · xəritə məlumatları"
            : `Sərhədlər və markerlər: GeoAtlas canonical data. Basemap: ${manifest?.basemap.provider}. OSM © OpenStreetMap contributors (ODbL). Overture Maps Foundation. GeoNames CC BY 4.0.`}
        </p>
      </aside>

      <main className="map-wrap">
        <div className="map-pane">
          <MapView
            countryBoundary={countryBoundary}
            selectedBoundary={
              mapBoundaryMode === "none" ? null : selectedBoundary
            }
            boundaryMode={mapBoundaryMode}
            places={filteredPlaces}
            selectedPlaceId={selectedPlaceId}
            selectedArea={selectedArea ?? null}
            onPlaceClick={setSelectedPlaceId}
          />
          <div className="map-overlay">
            <div className="card meta">
              {selectedArea ? (
                <TruncatedText
                  text={
                    IS_CUSTOMER
                      ? selectedArea.name
                      : `${selectedArea.name} · boundary ${selectedArea.geom_status} · center ${selectedArea.center_status ?? "?"} · parent ${selectedArea.parent_status}`
                  }
                />
              ) : (
                "Ərazi seçin"
              )}
              {placesLoading ? " · məkanlar yüklənir…" : ""}
            </div>
            <div className="map-legend card meta">
              <span className="legend-item">
                <i className="swatch center" /> Ərazi mərkəzi
              </span>
              <span className="legend-item">
                <i className="swatch place" /> Tanınmış məkan
              </span>
              <span className="legend-item">
                <i className="swatch place-selected" /> Seçilmiş məkan
              </span>
            </div>
          </div>
        </div>
        {!IS_CUSTOMER && (
          <GeoJSONInspector
            areas={areas}
            selectedArea={selectedArea ?? null}
            selectedBoundary={selectedBoundary}
            boundaryLoadError={boundaryLoadError}
            boundaryLoading={boundaryLoading}
            selectedPlace={selectedPlace ?? null}
          />
        )}
      </main>
    </div>
  );
}

function StatusBadge({
  label,
  tone,
}: {
  label: string;
  tone: "ok" | "warn" | "err";
}) {
  return <span className={`badge ${tone}`}>{label}</span>;
}

function toneFor(status: string): "ok" | "warn" | "err" {
  if (status === "verified") return "ok";
  if (status === "missing" || status === "conflict") return "err";
  return "warn";
}
