import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map, type GeoJSONSource } from "maplibre-gl";
import type { Area, Place } from "@geoatlas/types";
import { centerOf } from "@geoatlas/data";

const BASEMAP = "https://tiles.openfreemap.org/styles/liberty";
const AZ_BOUNDS: [[number, number], [number, number]] = [
  [44.7, 38.3],
  [50.9, 42.0],
];

export type BoundaryMode = "exact" | "partial_outline" | "none";

type Props = {
  countryBoundary: GeoJSON.FeatureCollection | null;
  selectedBoundary: GeoJSON.FeatureCollection | null;
  boundaryMode: BoundaryMode;
  places: Place[];
  selectedPlaceId: string | null;
  selectedArea: Area | null;
  onPlaceClick: (placeId: string) => void;
};

export default function MapView({
  countryBoundary,
  selectedBoundary,
  boundaryMode,
  places,
  selectedPlaceId,
  selectedArea,
  onPlaceClick,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const onPlaceClickRef = useRef(onPlaceClick);
  const [ready, setReady] = useState(false);
  onPlaceClickRef.current = onPlaceClick;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP,
      bounds: AZ_BOUNDS,
      fitBoundsOptions: { padding: 40 },
      attributionControl: {},
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      map.addSource("country", { type: "geojson", data: emptyFc() });
      map.addLayer({
        id: "country-fill",
        type: "fill",
        source: "country",
        paint: { "fill-color": "#3d9cf0", "fill-opacity": 0.06 },
      });
      map.addLayer({
        id: "country-line",
        type: "line",
        source: "country",
        paint: {
          "line-color": "#3d9cf0",
          "line-width": 2,
          "line-opacity": 0.85,
        },
      });

      map.addSource("selected-area", { type: "geojson", data: emptyFc() });
      map.addLayer({
        id: "selected-fill",
        type: "fill",
        source: "selected-area",
        paint: {
          "fill-color": "#f0b429",
          "fill-opacity": 0.18,
        },
      });
      map.addLayer({
        id: "selected-line",
        type: "line",
        source: "selected-area",
        paint: {
          "line-color": "#f0b429",
          "line-width": 2.5,
        },
      });

      map.addSource("area-center", { type: "geojson", data: emptyFc() });
      map.addLayer({
        id: "area-center-halo",
        type: "circle",
        source: "area-center",
        paint: {
          "circle-radius": 10,
          "circle-color": "#ffffff",
          "circle-opacity": 0.85,
        },
      });
      map.addLayer({
        id: "area-center-point",
        type: "circle",
        source: "area-center",
        paint: {
          "circle-radius": 5,
          "circle-color": [
            "match",
            ["get", "status"],
            "verified",
            "#3ecf8e",
            "label_fallback",
            "#f0b429",
            "conflict",
            "#e85d5d",
            "#9aabbc",
          ],
          "circle-stroke-width": 1,
          "circle-stroke-color": "#0f1419",
        },
      });

      map.addSource("places", { type: "geojson", data: emptyFc() });
      map.addLayer({
        id: "places-circle",
        type: "circle",
        source: "places",
        paint: {
          "circle-radius": [
            "case",
            ["boolean", ["get", "selected"], false],
            9,
            6,
          ],
          "circle-color": [
            "match",
            ["get", "category"],
            "historic",
            "#e8a44a",
            "park",
            "#3ecf8e",
            "museum",
            "#c084fc",
            "religious",
            "#60a5fa",
            "stadium",
            "#f472b6",
            "monument",
            "#fbbf24",
            "tourism",
            "#34d399",
            "culture",
            "#a78bfa",
            "education",
            "#38bdf8",
            "government",
            "#94a3b8",
            "#3d9cf0",
          ],
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "#0f1419",
          "circle-opacity": 0.95,
        },
      });

      map.on("click", "places-circle", (e) => {
        const id = e.features?.[0]?.properties?.id;
        if (typeof id === "string") onPlaceClickRef.current(id);
      });
      map.on("mouseenter", "places-circle", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "places-circle", () => {
        map.getCanvas().style.cursor = "";
      });
      setReady(true);
    });

    return () => {
      setReady(false);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    (map.getSource("country") as GeoJSONSource).setData(
      countryBoundary ?? emptyFc(),
    );
    if (countryBoundary?.features?.[0]?.geometry) {
      const b = bboxOf(countryBoundary);
      if (b) map.fitBounds(b, { padding: 48, duration: 800, maxZoom: 7.2 });
    }
  }, [countryBoundary, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const src = map.getSource("selected-area") as GeoJSONSource;
    if (boundaryMode === "none" || !selectedBoundary) {
      src.setData(emptyFc());
    } else {
      const tagged: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: selectedBoundary.features.map((f) => ({
          ...f,
          properties: { ...(f.properties ?? {}), mode: boundaryMode },
        })),
      };
      src.setData(tagged);
      const partial = boundaryMode === "partial_outline";
      map.setPaintProperty(
        "selected-fill",
        "fill-color",
        partial ? "#e85d5d" : "#f0b429",
      );
      map.setPaintProperty(
        "selected-fill",
        "fill-opacity",
        partial ? 0.08 : 0.18,
      );
      map.setPaintProperty(
        "selected-line",
        "line-color",
        partial ? "#e85d5d" : "#f0b429",
      );
      if (partial) {
        map.setPaintProperty("selected-line", "line-dasharray", [1.5, 1.2]);
      } else {
        try {
          map.setPaintProperty("selected-line", "line-dasharray", undefined);
        } catch {
          map.setPaintProperty("selected-line", "line-dasharray", [1, 0]);
        }
      }
      const b = bboxOf(selectedBoundary);
      if (b) map.fitBounds(b, { padding: 56, duration: 700, maxZoom: 14 });
    }

    const c = selectedArea ? centerOf(selectedArea) : null;
    const centerSrc = map.getSource("area-center") as GeoJSONSource;
    if (c) {
      centerSrc.setData({
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: {
              status: selectedArea?.center_status ?? "missing",
              method: selectedArea?.center_method ?? "",
            },
            geometry: {
              type: "Point",
              coordinates: [c.longitude, c.latitude],
            },
          },
        ],
      });
      if (boundaryMode === "none") {
        map.flyTo({
          center: [c.longitude, c.latitude],
          zoom: 11,
          duration: 700,
        });
      }
    } else {
      centerSrc.setData(emptyFc());
    }
  }, [selectedBoundary, selectedArea, boundaryMode, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    (map.getSource("places") as GeoJSONSource).setData({
      type: "FeatureCollection",
      features: places.map((p) => ({
        type: "Feature",
        properties: {
          id: p.id,
          name: p.name,
          category: p.category,
          selected: p.id === selectedPlaceId,
        },
        geometry: {
          type: "Point",
          coordinates: [p.coordinates.lon, p.coordinates.lat],
        },
      })),
    });
  }, [places, selectedPlaceId, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !selectedPlaceId) return;
    const place = places.find((p) => p.id === selectedPlaceId);
    if (!place) return;
    map.flyTo({
      center: [place.coordinates.lon, place.coordinates.lat],
      zoom: Math.max(map.getZoom(), 13.5),
      duration: 500,
    });
  }, [selectedPlaceId, places, ready]);

  return <div className="map" ref={containerRef} />;
}

function emptyFc(): GeoJSON.FeatureCollection {
  return { type: "FeatureCollection", features: [] };
}

function bboxOf(
  fc: GeoJSON.FeatureCollection,
): [[number, number], [number, number]] | null {
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;
  const walk = (coords: unknown): void => {
    if (!Array.isArray(coords)) return;
    if (typeof coords[0] === "number" && typeof coords[1] === "number") {
      minX = Math.min(minX, coords[0]);
      minY = Math.min(minY, coords[1]);
      maxX = Math.max(maxX, coords[0]);
      maxY = Math.max(maxY, coords[1]);
      return;
    }
    for (const c of coords) walk(c);
  };
  for (const f of fc.features) {
    const g = f.geometry;
    if (!g || g.type === "GeometryCollection") continue;
    walk(g.coordinates);
  }
  if (!Number.isFinite(minX)) return null;
  return [
    [minX, minY],
    [maxX, maxY],
  ];
}
