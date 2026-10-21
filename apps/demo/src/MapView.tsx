import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map, type GeoJSONSource } from "maplibre-gl";
import type { Area, Place } from "@geoatlas/types";

const BASEMAP = "https://tiles.openfreemap.org/styles/liberty";
const AZ_BOUNDS: [[number, number], [number, number]] = [
  [44.7, 38.3],
  [50.9, 42.0],
];

type Props = {
  countryBoundary: GeoJSON.FeatureCollection | null;
  selectedBoundary: GeoJSON.FeatureCollection | null;
  places: Place[];
  selectedPlaceId: string | null;
  selectedArea: Area | null;
  onPlaceClick: (placeId: string) => void;
};

export default function MapView({
  countryBoundary,
  selectedBoundary,
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
        paint: { "fill-color": "#f0b429", "fill-opacity": 0.18 },
      });
      map.addLayer({
        id: "selected-line",
        type: "line",
        source: "selected-area",
        paint: { "line-color": "#f0b429", "line-width": 2.5 },
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
    (map.getSource("selected-area") as GeoJSONSource).setData(
      selectedBoundary ?? emptyFc(),
    );
    if (selectedBoundary?.features?.length) {
      const b = bboxOf(selectedBoundary);
      if (b) map.fitBounds(b, { padding: 56, duration: 700, maxZoom: 14 });
    } else if (selectedArea?.center) {
      map.flyTo({
        center: [selectedArea.center.lon, selectedArea.center.lat],
        zoom: 11,
        duration: 700,
      });
    }
  }, [selectedBoundary, selectedArea, ready]);

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
