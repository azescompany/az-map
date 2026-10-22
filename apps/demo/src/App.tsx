import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Map as MapLibreMap } from "maplibre-gl";
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
  verifiedChildrenOf,
  verifiedChildrenOfType,
} from "@geoatlas/data";
import { GeoAtlasShell } from "@geoatlas/shell-react";
import MapView from "./MapView";
import SearchableSelect from "./components/SearchableSelect";
import GlobalSearch from "./components/GlobalSearch";
import TruncatedText from "./components/TruncatedText";
import { resolveAppMode } from "./appMode";
import { resolveDataBase } from "./dataBase";

/** CDN (jsDelivr pin) by default; set VITE_GEOATLAS_DATA_BASE=local for repo data/. */
const { base: DATA_BASE, source: DATA_SOURCE } = resolveDataBase(
  import.meta.env.VITE_GEOATLAS_DATA_BASE,
);
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
  "sport",
  "stadium",
  "education",
  "shop",
  "market",
  "healthcare",
  "food",
  "services",
  "transport",
  "government",
  "other_poi",
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
  const [devDrawerOpen, setDevDrawerOpen] = useState(false);
  const mapApiRef = useRef<MapLibreMap | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const [m, a, r] = await Promise.all([
          loadManifest(DATA_BASE),
          loadAreas(DATA_BASE),
          loadReviews(DATA_BASE),
        ]);
        if (cancelled) return;
        setManifest(m);
        setAreas(a);
        setReviews(r);
        const country = a.find((x) => x.type === "country");
        const catalog = filterNamedPlaces(
          await loadAllCatalogPlaces(DATA_BASE),
        );
        if (!cancelled) setCatalogPlaces(catalog);
        if (country) {
          setCountryId(country.id);
          setSelectedAreaId(country.id);
          setBoundaryLoading(true);
          setBoundaryLoadError(null);
          try {
            const gj = await loadBoundary(DATA_BASE, country);
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
        const gj = await loadBoundary(DATA_BASE, area);
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
        const pls = await loadPlacesForArea(DATA_BASE, area, areas);
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

  const geojsonText = useMemo(() => {
    if (selectedPlace?.coordinates) {
      return JSON.stringify(
        {
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              properties: {
                id: selectedPlace.id,
                name: selectedPlace.displayName ?? selectedPlace.name,
                category: selectedPlace.category,
              },
              geometry: {
                type: "Point",
                coordinates: [
                  selectedPlace.coordinates.lon,
                  selectedPlace.coordinates.lat,
                ],
              },
            },
          ],
        },
        null,
        2,
      );
    }
    if (selectedBoundary) {
      return JSON.stringify(selectedBoundary, null, 2);
    }
    return null;
  }, [selectedPlace, selectedBoundary]);

  const resultItems = useMemo(
    () =>
      filteredPlaces.slice(0, 40).map((p) => ({
        id: p.id,
        title: p.displayName ?? p.name,
        subtitle: categoryLabel(String(p.category)),
        active: p.id === selectedPlaceId,
        onClick: () => setSelectedPlaceId(p.id),
      })),
    [filteredPlaces, selectedPlaceId],
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
    <div className={`app demo-root mode-${APP_MODE}`}>
      <GeoAtlasShell
        theme="dark"
        showDeveloperPanel={!IS_CUSTOMER}
        developerOpen={devDrawerOpen}
        onDeveloperOpenChange={setDevDrawerOpen}
        labels={{ brand: "GeoAtlas Azərbaycan" }}
        map={
          <MapView
            className="geoatlas-map map"
            countryBoundary={countryBoundary}
            selectedBoundary={
              mapBoundaryMode === "none" ? null : selectedBoundary
            }
            boundaryMode={mapBoundaryMode}
            places={filteredPlaces}
            selectedPlaceId={selectedPlaceId}
            selectedArea={selectedArea ?? null}
            onPlaceClick={setSelectedPlaceId}
            clipToCountry
            showNavigationControl={false}
            onMapReady={(m) => {
              mapApiRef.current = m;
            }}
          />
        }
        search={
          <GlobalSearch
            areas={areas}
            places={catalogPlaces}
            customer={IS_CUSTOMER}
            onSelectArea={(a) => void selectArea(a)}
            onSelectPlace={selectPlaceById}
          />
        }
        cascade={
          <>
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
          </>
        }
        chips={CATEGORIES.map((c) => ({
          id: c,
          label: categoryLabel(c),
          active: category === c,
          onClick: () => setCategory(c),
        }))}
        showResults={Boolean(cityId || rayonId || neighborhoodId)}
        results={resultItems}
        resultsLoading={placesLoading}
        onZoomIn={() => mapApiRef.current?.zoomIn()}
        onZoomOut={() => mapApiRef.current?.zoomOut()}
        onLocate={() => {
          const c = selectedCenter;
          if (c && mapApiRef.current) {
            mapApiRef.current.easeTo({
              center: [c.longitude, c.latitude],
              zoom: Math.max(mapApiRef.current.getZoom(), 12),
            });
          }
        }}
        onFullscreen={() => {
          const el = document.querySelector(".geoatlas-shell");
          if (!el) return;
          if (document.fullscreenElement) void document.exitFullscreen();
          else void el.requestFullscreen();
        }}
        status={
          <div className="geoatlas-status__card geoatlas-glass">
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
            {boundaryLoadError ? ` · ${boundaryLoadError}` : ""}
            {boundaryLoading ? " · sərhəd…" : ""}
          </div>
        }
        legend={
          <div className="geoatlas-legend geoatlas-glass">
            <span className="geoatlas-legend__item">
              <i className="geoatlas-swatch geoatlas-swatch--center" /> Ərazi
              mərkəzi
            </span>
            <span className="geoatlas-legend__item">
              <i className="geoatlas-swatch geoatlas-swatch--place" /> Tanınmış
              məkan
            </span>
            <span className="geoatlas-legend__item">
              <i className="geoatlas-swatch geoatlas-swatch--selected" /> Seçilmiş
              məkan
            </span>
          </div>
        }
        developerBadges={
          <>
            <span className="geoatlas-badge geoatlas-badge--ok">{APP_MODE}</span>
            <span className="geoatlas-badge geoatlas-badge--ok">
              {manifest?.dataset_version ?? "—"}
            </span>
            <span className="geoatlas-badge" title={DATA_BASE}>
              data:{DATA_SOURCE}
            </span>
            <span className="geoatlas-badge">
              {manifest?.coverage.areas ?? areas.length} area
            </span>
            <span className="geoatlas-badge">
              {manifest?.coverage.places ?? "?"} place
            </span>
            <span className="geoatlas-badge geoatlas-badge--warn">
              {reviews.length} review
            </span>
          </>
        }
        metadataPanel={
          <div className="geoatlas-detail">
            {selectedArea ? (
              <>
                <h2>
                  <TruncatedText text={selectedArea.name} as="span" />
                </h2>
                <p className="meta">
                  <TruncatedText
                    text={areaBreadcrumb(areas, selectedArea.id)}
                  />
                </p>
                <div className="geoatlas-badge-row" style={{ marginBottom: 8 }}>
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
                <dl>
                  <dt>Tip</dt>
                  <dd>
                    {selectedArea.type}
                    {selectedArea.subtype ? ` / ${selectedArea.subtype}` : ""}
                  </dd>
                  <dt>Wikidata</dt>
                  <dd>{selectedArea.wikidata ?? "—"}</dd>
                  <dt>Mərkəz</dt>
                  <dd>
                    {selectedCenter
                      ? `${selectedCenter.latitude.toFixed(6)}, ${selectedCenter.longitude.toFixed(6)}`
                      : "missing"}
                  </dd>
                  <dt>Boundary</dt>
                  <dd>
                    <TruncatedText text={selectedArea.boundary_file ?? "—"} />
                  </dd>
                  <dt>Məkanlar</dt>
                  <dd>
                    {placesLoading
                      ? "yüklənir…"
                      : `${filteredPlaces.length} adlı / ${places.length} cəmi`}
                  </dd>
                </dl>
              </>
            ) : (
              <p className="meta">Ərazi seçin — metadata burada görünəcək.</p>
            )}
            {selectedPlace && (
              <>
                <h2 style={{ marginTop: 16 }}>
                  <TruncatedText
                    text={selectedPlace.displayName ?? selectedPlace.name}
                    as="span"
                  />
                </h2>
                <dl>
                  <dt>ID</dt>
                  <dd>
                    <code>{selectedPlace.id}</code>
                  </dd>
                  <dt>Kateqoriya</dt>
                  <dd>{categoryLabel(String(selectedPlace.category))}</dd>
                  <dt>Koordinat</dt>
                  <dd>
                    {selectedPlace.coordinates
                      ? `${selectedPlace.coordinates.lat.toFixed(6)}, ${selectedPlace.coordinates.lon.toFixed(6)}`
                      : "—"}
                  </dd>
                </dl>
              </>
            )}
            <p className="geoatlas-attribution">
              Dataset {manifest?.dataset_version ?? "—"} · {DATA_SOURCE}. Basemap:{" "}
              {manifest?.basemap.provider}. OSM © OpenStreetMap contributors.
            </p>
          </div>
        }
        reviewPanel={
          <div className="geoatlas-detail">
            {reviews.length ? (
              <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
                {reviews.slice(0, 20).map((r) => (
                  <li key={r.id} className="meta">
                    <strong>{r.entity}</strong> — {r.kind}: {r.detail}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="meta">Açıq review yoxdur.</p>
            )}
          </div>
        }
        geojsonText={geojsonText}
      />
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
  return (
    <span className={`geoatlas-badge geoatlas-badge--${tone}`}>{label}</span>
  );
}

function toneFor(status: string): "ok" | "warn" | "err" {
  if (status === "verified") return "ok";
  if (status === "missing" || status === "conflict") return "err";
  return "warn";
}
