import { useEffect, useMemo, useState } from "react";
import type { Area, Place } from "@geoatlas/types";
import { areaBreadcrumb, categoryLabel, centerOf } from "@geoatlas/data";

type ViewMode = "summary" | "geojson";

type Props = {
  areas: Area[];
  selectedArea: Area | null;
  selectedBoundary: GeoJSON.FeatureCollection | null;
  boundaryLoadError: string | null;
  boundaryLoading: boolean;
  selectedPlace: Place | null;
};

export default function GeoJSONInspector({
  areas,
  selectedArea,
  selectedBoundary,
  boundaryLoadError,
  boundaryLoading,
  selectedPlace,
}: Props) {
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<ViewMode>("summary");
  const [copyState, setCopyState] = useState<"idle" | "ok" | "err">("idle");

  useEffect(() => {
    setCopyState("idle");
  }, [selectedArea?.id, selectedPlace?.id, view]);

  const areaCenter = selectedArea ? centerOf(selectedArea) : null;
  const geomType = useMemo(
    () => geometryTypeOf(selectedBoundary),
    [selectedBoundary],
  );

  const geojsonPayload = useMemo(() => {
    if (selectedPlace) {
      return buildPlaceFeatureCollection(
        selectedPlace,
        selectedArea,
        selectedBoundary,
      );
    }
    if (selectedArea) {
      return buildAreaFeatureCollection(selectedArea, selectedBoundary);
    }
    return null;
  }, [selectedPlace, selectedArea, selectedBoundary]);

  const geojsonText = useMemo(
    () => (geojsonPayload ? JSON.stringify(geojsonPayload, null, 2) : ""),
    [geojsonPayload],
  );

  const title = selectedPlace
    ? "Seçilmiş məkan — GeoJSON və koordinatlar"
    : "Seçilmiş ərazi — GeoJSON və koordinatlar";

  async function copyJson() {
    if (!geojsonText) return;
    try {
      await navigator.clipboard.writeText(geojsonText);
      setCopyState("ok");
    } catch {
      setCopyState("err");
    }
  }

  return (
    <section className={`inspector ${open ? "open" : "collapsed"}`}>
      <button
        type="button"
        className="inspector-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span>{title}</span>
        <span className="meta">{open ? "▼" : "▲"} yığ / aç</span>
      </button>

      {open && (
        <div className="inspector-body">
          {!selectedArea && !selectedPlace && (
            <p className="empty">Ərazi və ya tanınmış məkan seçin.</p>
          )}

          {(selectedArea || selectedPlace) && (
            <>
              <div className="inspector-tabs">
                <button
                  type="button"
                  className={view === "summary" ? "on" : ""}
                  onClick={() => setView("summary")}
                >
                  Xülasə
                </button>
                <button
                  type="button"
                  className={view === "geojson" ? "on" : ""}
                  onClick={() => setView("geojson")}
                >
                  GeoJSON
                </button>
                <button
                  type="button"
                  className="copy-btn"
                  onClick={() => void copyJson()}
                  disabled={!geojsonText}
                >
                  {copyState === "ok"
                    ? "Kopyalandı"
                    : copyState === "err"
                      ? "Kopyalama alınmadı"
                      : "JSON-u kopyala"}
                </button>
              </div>

              {view === "summary" ? (
                <div className="inspector-summary">
                  {selectedPlace ? (
                    <PlaceSummary
                      place={selectedPlace}
                      area={selectedArea}
                      areas={areas}
                      areaGeomType={geomType}
                      boundaryLoading={boundaryLoading}
                      boundaryLoadError={boundaryLoadError}
                      hasAreaBoundary={!!selectedBoundary?.features?.length}
                    />
                  ) : selectedArea ? (
                    <AreaSummary
                      area={selectedArea}
                      areas={areas}
                      center={areaCenter}
                      geomType={geomType}
                      boundaryLoading={boundaryLoading}
                      boundaryLoadError={boundaryLoadError}
                      hasBoundary={!!selectedBoundary?.features?.length}
                    />
                  ) : null}
                </div>
              ) : (
                <div className="inspector-geojson">
                  {boundaryLoading && (
                    <p className="meta">Sərhəd GeoJSON yüklənir…</p>
                  )}
                  {boundaryLoadError && (
                    <p className="inspector-error">{boundaryLoadError}</p>
                  )}
                  {!boundaryLoading && !geojsonText && (
                    <p className="empty">Göstəriləcək GeoJSON yoxdur.</p>
                  )}
                  {geojsonText && (
                    <pre className="geojson-pre" tabIndex={0}>
                      {geojsonText}
                    </pre>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}

function AreaSummary({
  area,
  areas,
  center,
  geomType,
  boundaryLoading,
  boundaryLoadError,
  hasBoundary,
}: {
  area: Area;
  areas: Area[];
  center: { latitude: number; longitude: number } | null;
  geomType: string | null;
  boundaryLoading: boolean;
  boundaryLoadError: string | null;
  hasBoundary: boolean;
}) {
  const parent = area.parent_id
    ? areas.find((a) => a.id === area.parent_id)
    : null;
  return (
    <dl>
      <dt>Ərazi ID</dt>
      <dd>
        <code>{area.id}</code>
      </dd>
      <dt>Ad / tip</dt>
      <dd>
        {area.name} · {area.type}
        {area.subtype ? ` / ${area.subtype}` : ""}
      </dd>
      <dt>Valideyn ID</dt>
      <dd>
        {area.parent_id ? (
          <>
            <code>{area.parent_id}</code>
            {parent ? ` (${parent.name})` : ""}
          </>
        ) : (
          "—"
        )}
      </dd>
      <dt>Sərhəd statusu</dt>
      <dd>
        {area.geom_status}
        {area.geom_status_reason ? ` — ${area.geom_status_reason}` : ""}
      </dd>
      <dt>Həndəsə tipi</dt>
      <dd>
        {boundaryLoading
          ? "yüklənir…"
          : boundaryLoadError
            ? "yüklənmədi"
            : (geomType ?? (hasBoundary ? "unknown" : "sərhəd yoxdur"))}
      </dd>
      <dt>Mərkəz (lat, lon)</dt>
      <dd>
        {center
          ? `${center.latitude.toFixed(6)}, ${center.longitude.toFixed(6)}`
          : "missing"}
      </dd>
      <dt>Mərkəz metodu</dt>
      <dd>
        {area.center_method ?? "—"}
        {area.center_method === "interior_representative_point" ||
        area.center_method === "rep_point"
          ? " · hesablanmış daxili nöqtə (rəsmi inzibati mərkəz deyil)"
          : ""}
        {area.center_within_boundary == null
          ? ""
          : area.center_within_boundary
            ? " · polygon daxilində"
            : " · polygon xaricində"}
      </dd>
      <dt>CRS</dt>
      <dd>
        {area.crs ?? "mənbədə təsdiqlənməyib"}
        {!area.crs ? " (təsdiqlənmiş sayılmır)" : ""}
      </dd>
      <dt>Mənbə / provenance</dt>
      <dd>{formatSourceRefs(area.source_refs)}</dd>
      <dt>Boundary faylı</dt>
      <dd>{area.boundary_file ?? "—"}</dd>
      {boundaryLoadError && (
        <>
          <dt>Yükləmə</dt>
          <dd className="inspector-error">{boundaryLoadError}</dd>
        </>
      )}
    </dl>
  );
}

function PlaceSummary({
  place,
  area,
  areas,
  areaGeomType,
  boundaryLoading,
  boundaryLoadError,
  hasAreaBoundary,
}: {
  place: Place;
  area: Area | null;
  areas: Area[];
  areaGeomType: string | null;
  boundaryLoading: boolean;
  boundaryLoadError: string | null;
  hasAreaBoundary: boolean;
}) {
  const placeArea = place.area_id
    ? (areas.find((a) => a.id === place.area_id) ?? area)
    : area;
  const hasPlaceCoords =
    place.coordinates &&
    Number.isFinite(place.coordinates.lat) &&
    Number.isFinite(place.coordinates.lon);
  const placeBoundary = place.boundary_file ?? null;
  const placeGeom = place.geometry_type ?? "Point";

  return (
    <dl>
      <dt>Məkan ID</dt>
      <dd>
        <code>{place.id}</code>
      </dd>
      <dt>Ad</dt>
      <dd>{place.displayName ?? place.name}</dd>
      <dt>Kateqoriya</dt>
      <dd>{categoryLabel(String(place.category))}</dd>
      <dt>Aid olduğu ərazi</dt>
      <dd>
        {placeArea
          ? `${placeArea.name} (${placeArea.id})`
          : (place.area_id ?? "—")}
        <div className="meta">{areaBreadcrumb(areas, place.area_id)}</div>
      </dd>
      <dt>Məkan koordinatları (lat, lon)</dt>
      <dd>
        {hasPlaceCoords
          ? `${place.coordinates.lat.toFixed(6)}, ${place.coordinates.lon.toFixed(6)}`
          : "koordinat yoxdur (marker yaradılmayıb)"}
      </dd>
      <dt>Məkan həndəsəsi</dt>
      <dd>
        {placeGeom}
        {placeBoundary
          ? ` · sərhəd faylı: ${placeBoundary}`
          : " · yalnız nöqtə; məkan polygon-u yoxdur"}
      </dd>
      <dt>Ərazi sərhədi (ayrı)</dt>
      <dd>
        {boundaryLoading
          ? "yüklənir…"
          : hasAreaBoundary
            ? `${areaGeomType ?? "Polygon/MultiPolygon"} — ərazi sərhədi (məkan nöqtəsi deyil)`
            : "ərazi sərhədi yoxdur"}
        {boundaryLoadError ? ` · ${boundaryLoadError}` : ""}
      </dd>
      <dt>Yoxlama statusu</dt>
      <dd>
        name: {place.nameStatus ?? "?"} · geo/area:{" "}
        {place.verificationStatus ?? place.area_assign_status ?? "unverified"} ·
        record: {place.status}
      </dd>
      <dt>Mənbə identifikatorları</dt>
      <dd>{formatSourceRefs(place.source_refs)}</dd>
    </dl>
  );
}

function formatSourceRefs(
  refs: { source: string; source_id: string; release?: string }[],
): string {
  if (!refs?.length) return "—";
  return refs
    .map((r) => `${r.source}:${r.source_id}${r.release ? `@${r.release}` : ""}`)
    .join(", ");
}

function geometryTypeOf(
  fc: GeoJSON.FeatureCollection | null,
): string | null {
  if (!fc?.features?.length) return null;
  const types = new Set(
    fc.features
      .map((f) => f.geometry?.type)
      .filter((t): t is NonNullable<typeof t> => typeof t === "string"),
  );
  if (!types.size) return null;
  return [...types].join(", ");
}

function buildAreaFeatureCollection(
  area: Area,
  boundary: GeoJSON.FeatureCollection | null,
): GeoJSON.FeatureCollection {
  const c = centerOf(area);
  const features: GeoJSON.Feature[] = [];

  if (boundary?.features?.length) {
    for (const f of boundary.features) {
      features.push({
        type: "Feature",
        properties: {
          ...(f.properties ?? {}),
          role: "area_boundary",
          area_id: area.id,
          name: area.name,
          geom_status: area.geom_status,
          crs: area.crs ?? null,
        },
        geometry: f.geometry,
      });
    }
  }

  if (c) {
    features.push({
      type: "Feature",
      properties: {
        role: "area_center",
        area_id: area.id,
        name: area.name,
        center_method: area.center_method,
        center_status: area.center_status,
        center_within_boundary: area.center_within_boundary,
        note:
          area.center_method === "interior_representative_point" ||
          area.center_method === "rep_point"
            ? "Computed interior point — not an official administrative center"
            : null,
      },
      geometry: {
        type: "Point",
        coordinates: [c.longitude, c.latitude],
      },
    });
  }

  return { type: "FeatureCollection", features };
}

function buildPlaceFeatureCollection(
  place: Place,
  area: Area | null,
  areaBoundary: GeoJSON.FeatureCollection | null,
): GeoJSON.FeatureCollection {
  const features: GeoJSON.Feature[] = [];

  if (
    place.coordinates &&
    Number.isFinite(place.coordinates.lon) &&
    Number.isFinite(place.coordinates.lat)
  ) {
    features.push({
      type: "Feature",
      properties: {
        role: "place_point",
        place_id: place.id,
        name: place.displayName ?? place.name,
        category: place.category,
        nameStatus: place.nameStatus,
        verificationStatus: place.verificationStatus,
        area_id: place.area_id,
        note: "Place point — not the parent area boundary",
      },
      geometry: {
        type: "Point",
        coordinates: [place.coordinates.lon, place.coordinates.lat],
      },
    });
  }

  // Place footprint only if present (pilot has none — do not invent).
  // When boundary_file exists, caller would load it separately; we never
  // substitute area polygon as place geometry.

  if (areaBoundary?.features?.length && area) {
    for (const f of areaBoundary.features) {
      features.push({
        type: "Feature",
        properties: {
          ...(f.properties ?? {}),
          role: "containing_area_boundary",
          area_id: area.id,
          area_name: area.name,
          note: "Parent/selected area boundary — distinct from place point",
        },
        geometry: f.geometry,
      });
    }
  }

  return { type: "FeatureCollection", features };
}
