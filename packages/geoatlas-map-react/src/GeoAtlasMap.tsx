import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map, type GeoJSONSource } from "maplibre-gl";
import type { Area, Place } from "@geoatlas/types";
import { centerOf } from "@geoatlas/data";

const BASEMAP = "https://tiles.openfreemap.org/styles/liberty";

/** Approx Azerbaijan extent — used when clipToCountry and no country FC yet */
export const AZ_BOUNDS: [[number, number], [number, number]] = [
  [44.7, 38.3],
  [50.9, 42.0],
];

export type BoundaryMode = "exact" | "partial_outline" | "none";

/** Emitted when user picks a place / map point — lat/lon for forms / real estate. */
export type LocationSelectPayload = {
  lat: number;
  lon: number;
  placeId?: string;
  areaId?: string;
  name?: string;
  source?: "place" | "area" | "map";
};

export type GeoAtlasMapProps = {
  countryBoundary?: GeoJSON.FeatureCollection | null;
  selectedBoundary?: GeoJSON.FeatureCollection | null;
  boundaryMode?: BoundaryMode;
  places?: Place[];
  selectedPlaceId?: string | null;
  selectedArea?: Area | null;
  onPlaceClick?: (placeId: string) => void;
  /** Place marker select → lat/lon (and optional ids) for parent forms */
  onLocationSelect?: (payload: LocationSelectPayload) => void;
  /** Click empty map → lat/lon (+ pick marker when true) */
  enableMapPick?: boolean;
  onMapClick?: (payload: LocationSelectPayload) => void;
  /** Restrict pan/zoom to Azerbaijan (default true) */
  clipToCountry?: boolean;
  className?: string;
  basemapUrl?: string;
  /** Built-in MapLibre +/- control (default true). Shell UI usually sets false. */
  showNavigationControl?: boolean;
  /** Imperative map handle for custom toolbars */
  onMapReady?: (map: Map) => void;
};

const PLACE_HIT_LAYERS = [
  "places-circle",
  "places-clusters",
  "places-cluster-count",
] as const;

export function GeoAtlasMap({
  countryBoundary = null,
  selectedBoundary = null,
  boundaryMode = "none",
  places = [],
  selectedPlaceId = null,
  selectedArea = null,
  onPlaceClick,
  onLocationSelect,
  enableMapPick = false,
  onMapClick,
  clipToCountry = true,
  className = "geoatlas-map map",
  basemapUrl = BASEMAP,
  showNavigationControl = true,
  onMapReady,
}: GeoAtlasMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const onPlaceClickRef = useRef(onPlaceClick);
  const onLocationSelectRef = useRef(onLocationSelect);
  const onMapClickRef = useRef(onMapClick);
  const enableMapPickRef = useRef(enableMapPick);
  const onMapReadyRef = useRef(onMapReady);
  const [ready, setReady] = useState(false);
  onPlaceClickRef.current = onPlaceClick;
  onLocationSelectRef.current = onLocationSelect;
  onMapClickRef.current = onMapClick;
  enableMapPickRef.current = enableMapPick;
  onMapReadyRef.current = onMapReady;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const mapOpts: maplibregl.MapOptions & {
      transformStyle?: (
        prev: maplibregl.StyleSpecification | undefined,
        next: maplibregl.StyleSpecification,
      ) => maplibregl.StyleSpecification;
    } = {
      container: containerRef.current,
      style: basemapUrl,
      bounds: AZ_BOUNDS,
      fitBoundsOptions: { padding: 40 },
      maxBounds: clipToCountry ? AZ_BOUNDS : undefined,
      attributionControl: {},
      // Strip DEM/terrain before MapLibre applies it (Liberty → null DEM tile spam).
      transformStyle: (_prev, next) => {
        if (!next) return next;
        const style = { ...next } as maplibregl.StyleSpecification & {
          terrain?: unknown;
        };
        delete style.terrain;
        if (style.sources) {
          const sources = { ...style.sources };
          for (const [key, src] of Object.entries(sources)) {
            if (
              src &&
              typeof src === "object" &&
              "type" in src &&
              (src as { type?: string }).type === "raster-dem"
            ) {
              delete sources[key];
            }
          }
          style.sources = sources;
        }
        if (Array.isArray(style.layers)) {
          style.layers = style.layers.filter((l) => l.type !== "hillshade");
        }
        return style;
      },
    };
    const map = new maplibregl.Map(mapOpts);
    if (showNavigationControl) {
      map.addControl(
        new maplibregl.NavigationControl({ showCompass: false }),
        "top-right",
      );
    }
    mapRef.current = map;
    onMapReadyRef.current?.(map);

    map.on("load", () => {
      try {
        if (map.getTerrain()) map.setTerrain(null);
      } catch {
        /* no terrain */
      }
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

      map.addSource("map-pick", { type: "geojson", data: emptyFc() });
      map.addLayer({
        id: "map-pick-halo",
        type: "circle",
        source: "map-pick",
        paint: {
          "circle-radius": 14,
          "circle-color": "#0f766e",
          "circle-opacity": 0.22,
        },
      });
      map.addLayer({
        id: "map-pick-point",
        type: "circle",
        source: "map-pick",
        paint: {
          "circle-radius": 7,
          "circle-color": "#0f766e",
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });

      map.addSource("places", {
        type: "geojson",
        data: emptyFc(),
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 50,
      });
      map.addLayer({
        id: "places-clusters",
        type: "circle",
        source: "places",
        filter: ["has", "point_count"],
        paint: {
          "circle-color": "#3d9cf0",
          "circle-radius": [
            "step",
            ["get", "point_count"],
            16,
            25,
            22,
            100,
            28,
            500,
            36,
          ],
          "circle-opacity": 0.85,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#0f1419",
        },
      });
      map.addLayer({
        id: "places-cluster-count",
        type: "symbol",
        source: "places",
        filter: ["has", "point_count"],
        layout: {
          "text-field": ["get", "point_count_abbreviated"],
          "text-size": 12,
        },
        paint: {
          "text-color": "#ffffff",
        },
      });
      map.addLayer({
        id: "places-circle",
        type: "circle",
        source: "places",
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-radius": [
            "case",
            ["boolean", ["get", "selected"], false],
            10,
            6,
          ],
          "circle-color": [
            "case",
            ["boolean", ["get", "selected"], false],
            "#ff6b6b",
            [
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
          ],
          "circle-stroke-width": [
            "case",
            ["boolean", ["get", "selected"], false],
            2.5,
            1.5,
          ],
          "circle-stroke-color": [
            "case",
            ["boolean", ["get", "selected"], false],
            "#ffffff",
            "#0f1419",
          ],
          "circle-opacity": 0.95,
        },
      });

      map.on("click", "places-clusters", (e) => {
        const feature = e.features?.[0];
        const clusterId = feature?.properties?.cluster_id;
        const src = map.getSource("places") as GeoJSONSource;
        if (
          clusterId == null ||
          !feature?.geometry ||
          !("coordinates" in feature.geometry)
        ) {
          return;
        }
        const coords = feature.geometry.coordinates as [number, number];
        void Promise.resolve(src.getClusterExpansionZoom(clusterId)).then(
          (zoom) => {
            if (typeof zoom !== "number") return;
            map.easeTo({ center: coords, zoom });
          },
        );
      });
      map.on("click", "places-circle", (e) => {
        e.originalEvent.stopPropagation();
        const feature = e.features?.[0];
        const id = feature?.properties?.id;
        if (typeof id === "string") onPlaceClickRef.current?.(id);
        const geom = feature?.geometry;
        if (geom && geom.type === "Point" && Array.isArray(geom.coordinates)) {
          const [lon, lat] = geom.coordinates as [number, number];
          if (Number.isFinite(lat) && Number.isFinite(lon)) {
            const rawName = feature?.properties?.name;
            onLocationSelectRef.current?.({
              lat,
              lon,
              placeId: typeof id === "string" ? id : undefined,
              name: typeof rawName === "string" ? rawName : undefined,
              source: "place",
            });
          }
        }
      });
      map.on("click", (e) => {
        if (!enableMapPickRef.current) return;
        const hits = map.queryRenderedFeatures(e.point, {
          layers: [...PLACE_HIT_LAYERS],
        });
        if (hits.length) return;
        const { lng: lon, lat } = e.lngLat;
        if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
        const pickSrc = map.getSource("map-pick") as GeoJSONSource | undefined;
        pickSrc?.setData({
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              properties: {},
              geometry: { type: "Point", coordinates: [lon, lat] },
            },
          ],
        });
        onMapClickRef.current?.({ lat, lon, source: "map" });
      });
      map.on("mouseenter", "places-clusters", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "places-clusters", () => {
        map.getCanvas().style.cursor = "";
      });
      map.on("mouseenter", "places-circle", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "places-circle", () => {
        map.getCanvas().style.cursor = "";
      });
      // Container may have been 0×0 before layout; resize after paint.
      requestAnimationFrame(() => {
        map.resize();
        setReady(true);
      });
    });

    return () => {
      setReady(false);
      map.remove();
      mapRef.current = null;
    };
  }, [basemapUrl, clipToCountry]);

  useEffect(() => {
    const map = mapRef.current;
    const el = containerRef.current;
    if (!map || !el || !ready) return;
    const ro = new ResizeObserver(() => map.resize());
    ro.observe(el);
    return () => ro.disconnect();
  }, [ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    if (clipToCountry) {
      const b = countryBoundary ? bboxOf(countryBoundary) : null;
      map.setMaxBounds(b ?? AZ_BOUNDS);
    }
  }, [clipToCountry, countryBoundary, ready]);


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
    if (
      c &&
      Number.isFinite(c.latitude) &&
      Number.isFinite(c.longitude)
    ) {
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
    const visible = selectedPlaceId
      ? places.filter((p) => p.id === selectedPlaceId)
      : places;
    const withCoords = visible.filter(
      (p) =>
        p.coordinates &&
        Number.isFinite(p.coordinates.lon) &&
        Number.isFinite(p.coordinates.lat),
    );
    (map.getSource("places") as GeoJSONSource).setData({
      type: "FeatureCollection",
      features: withCoords.map((p) => ({
        type: "Feature",
        properties: {
          id: p.id,
          name: p.displayName ?? p.name,
          category: p.category,
          selected: p.id === selectedPlaceId,
          role: "named_place",
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
    if (
      !place?.coordinates ||
      !Number.isFinite(place.coordinates.lon) ||
      !Number.isFinite(place.coordinates.lat)
    ) {
      return;
    }
    // Clear map-pick when a named place is chosen
    (map.getSource("map-pick") as GeoJSONSource | undefined)?.setData(
      emptyFc(),
    );
    map.flyTo({
      center: [place.coordinates.lon, place.coordinates.lat],
      zoom: 16,
      duration: 700,
    });
  }, [selectedPlaceId, places, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || enableMapPick) return;
    (map.getSource("map-pick") as GeoJSONSource | undefined)?.setData(
      emptyFc(),
    );
  }, [enableMapPick, ready]);

  return <div className={className} ref={containerRef} />;
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
    if (
      typeof coords[0] === "number" &&
      typeof coords[1] === "number" &&
      Number.isFinite(coords[0]) &&
      Number.isFinite(coords[1])
    ) {
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

/** @deprecated Use GeoAtlasMap — kept for demo drop-in */
export default GeoAtlasMap;
