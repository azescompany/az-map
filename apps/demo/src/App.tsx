import { useCallback, useEffect, useMemo, useState } from "react";
import type { Area, Manifest, Place, ReviewItem } from "@geoatlas/types";
import {
  boundaryDisplayMode,
  centerOf,
  getArea,
  loadAreas,
  loadBoundary,
  loadManifest,
  loadPlacesForArea,
  loadReviews,
  searchAreas,
  searchPlaces,
  verifiedChildrenOf,
} from "@geoatlas/data";
import MapView from "./MapView";

const DATA_BASE = ""; // Vite publicDir = ../../data

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

  const [selectedAreaId, setSelectedAreaId] = useState<string | null>(null);
  const [countryBoundary, setCountryBoundary] =
    useState<GeoJSON.FeatureCollection | null>(null);
  const [selectedBoundary, setSelectedBoundary] =
    useState<GeoJSON.FeatureCollection | null>(null);
  const [places, setPlaces] = useState<Place[]>([]);
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
        if (country) {
          setCountryId(country.id);
          setSelectedAreaId(country.id);
          const gj = await loadBoundary("/", country);
          if (!cancelled) setCountryBoundary(gj);
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

  const cities = useMemo(
    () => (countryId ? verifiedChildrenOf(areas, countryId) : []),
    [areas, countryId],
  );
  const rayons = useMemo(
    () => (cityId ? verifiedChildrenOf(areas, cityId) : []),
    [areas, cityId],
  );
  const neighborhoods = useMemo(
    () => (rayonId ? verifiedChildrenOf(areas, rayonId) : []),
    [areas, rayonId],
  );

  const selectArea = useCallback(
    async (area: Area) => {
      setSelectedAreaId(area.id);
      setSelectedPlaceId(null);

      // sync cascade
      if (area.type === "country") {
        setCountryId(area.id);
        setCityId("");
        setRayonId("");
        setNeighborhoodId("");
      } else if (area.type === "city") {
        setCountryId(area.parent_id ?? countryId);
        setCityId(area.id);
        setRayonId("");
        setNeighborhoodId("");
      } else if (area.type === "rayon") {
        setCityId(area.parent_id ?? cityId);
        setRayonId(area.id);
        setNeighborhoodId("");
        if (area.parent_id) {
          const city = getArea(areas, area.parent_id);
          if (city?.parent_id) setCountryId(city.parent_id);
        }
      } else if (area.type === "neighborhood") {
        setNeighborhoodId(area.id);
        setRayonId(area.parent_id ?? rayonId);
        const rayon = area.parent_id
          ? getArea(areas, area.parent_id)
          : undefined;
        if (rayon?.parent_id) {
          setCityId(rayon.parent_id);
          const city = getArea(areas, rayon.parent_id);
          if (city?.parent_id) setCountryId(city.parent_id);
        }
      }

      const gj = await loadBoundary("/", area);
      setSelectedBoundary(gj);

      setPlacesLoading(true);
      try {
        const pls = await loadPlacesForArea("/", area);
        setPlaces(pls);
      } finally {
        setPlacesLoading(false);
      }
    },
    [areas, cityId, countryId, rayonId],
  );

  const allPlacesFlat = useMemo(() => places, [places]);

  const filteredPlaces = useMemo(() => {
    if (category === "all") return places;
    return places.filter((p) => p.category === category);
  }, [places, category]);

  const selectedPlace = selectedPlaceId
    ? places.find((p) => p.id === selectedPlaceId)
    : undefined;

  const areaHits = useMemo(
    () => searchAreas(areas, query, 12),
    [areas, query],
  );
  const placeHits = useMemo(
    () => searchPlaces(allPlacesFlat, query, 12),
    [allPlacesFlat, query],
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

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <h1>GeoAtlas Azərbaycan</h1>
          <p>
            Pilot: ölkə → Bakı → Yasamal → yoxlanılmış məhəllələr. Mənbə
            faylları dəyişilməyib.
          </p>
        </div>

        <div className="badge-row">
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
                <button type="button" onClick={() => void selectArea(a)}>
                  <strong>{a.name}</strong>
                  <div className="meta">
                    area · {a.type} · {a.parent_status}/{a.geom_status}
                  </div>
                </button>
              </li>
            ))}
            {placeHits.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedPlaceId(p.id);
                    if (p.area_id) {
                      const a = getArea(areas, p.area_id);
                      if (a) void selectArea(a);
                    }
                  }}
                >
                  <strong>{p.name}</strong>
                  <div className="meta">place · {p.category}</div>
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
          <div className="field">
            <label>Ölkə</label>
            <select
              value={countryId}
              onChange={(e) => {
                const a = getArea(areas, e.target.value);
                if (a) void selectArea(a);
              }}
            >
              {areas
                .filter((a) => a.type === "country")
                .map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
            </select>
          </div>

          <div className="field">
            <label>Şəhər</label>
            <select
              value={cityId}
              disabled={!cities.length}
              onChange={(e) => {
                const a = getArea(areas, e.target.value);
                if (a) void selectArea(a);
              }}
            >
              <option value="">— seçin —</option>
              {cities.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Rayon</label>
            <select
              value={rayonId}
              disabled={!rayons.length}
              onChange={(e) => {
                const a = getArea(areas, e.target.value);
                if (a) void selectArea(a);
              }}
            >
              <option value="">— seçin —</option>
              {rayons.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                  {a.geom_status !== "verified" ? ` (${a.geom_status})` : ""}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Məhəllə / qəsəbə</label>
            <select
              value={neighborhoodId}
              disabled={!neighborhoods.length}
              onChange={(e) => {
                const a = getArea(areas, e.target.value);
                if (a) void selectArea(a);
              }}
            >
              <option value="">— seçin —</option>
              {neighborhoods.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
            {!neighborhoods.length && rayonId && (
              <span className="empty">
                Bu rayon üçün verified uşaq yoxdur (bax reviews).
              </span>
            )}
          </div>
        </div>

        {selectedArea && (
          <div className="detail">
            <h2>{selectedArea.name}</h2>
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
                tone={toneFor(String(selectedArea.center_status ?? "missing"))}
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
              <dd>{selectedArea.boundary_file ?? "—"}</dd>
              <dt>CRS</dt>
              <dd>{selectedArea.crs ?? "—"}</dd>
              <dt>Məkanlar</dt>
              <dd>
                {placesLoading
                  ? "yüklənir…"
                  : `${filteredPlaces.length} / ${places.length}`}
              </dd>
            </dl>
            {selectedArea.notes && (
              <p className="meta">{selectedArea.notes}</p>
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
                {c}
              </button>
            ))}
          </div>
        </div>

        {selectedPlace && (
          <div className="detail">
            <h2>{selectedPlace.name}</h2>
            <dl>
              <dt>Kateqoriya</dt>
              <dd>{selectedPlace.category}</dd>
              <dt>Status</dt>
              <dd>{selectedPlace.status}</dd>
              <dt>Area</dt>
              <dd>
                {selectedPlace.area_id
                  ? (getArea(areas, selectedPlace.area_id)?.name ??
                    selectedPlace.area_id)
                  : "—"}
              </dd>
              <dt>Mənbə</dt>
              <dd>
                {selectedPlace.source_refs
                  .map((r) => `${r.source}:${r.source_id}`)
                  .join(", ")}
              </dd>
            </dl>
          </div>
        )}

        {!!reviews.length && (
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
          Sərhədlər və markerlər: GeoAtlas canonical data. Basemap:{" "}
          {manifest?.basemap.provider}. OSM © OpenStreetMap contributors (ODbL).
          Overture Maps Foundation. GeoNames CC BY 4.0.
        </p>
      </aside>

      <main className="map-wrap">
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
            {selectedArea
              ? `${selectedArea.name} · boundary ${selectedArea.geom_status} · center ${selectedArea.center_status ?? "?"} · parent ${selectedArea.parent_status}`
              : "Ərazi seçin"}
            {placesLoading ? " · məkanlar yüklənir…" : ""}
          </div>
        </div>
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
