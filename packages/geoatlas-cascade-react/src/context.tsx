import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Area, Place } from "@geoatlas/types";
import {
  DEFAULT_DATA_BASE,
  areaBreadcrumb,
  boundaryDisplayMode,
  filterNamedPlaces,
  loadAreas,
  loadBoundary,
  loadPlacesForArea,
} from "@geoatlas/data";
import {
  createGeoCascade,
  emptySelection,
  leafAreaId,
  placeOptions,
  toOptions,
  type CascadeLevel,
  type CascadeOption,
  type CascadeSelection,
} from "@geoatlas/cascade";

export type GeoCascadeContextValue = {
  dataBase: string;
  loading: boolean;
  error: string | null;
  areas: Area[];
  selection: CascadeSelection;
  setLevel: (level: CascadeLevel, id: string | null) => void;
  selectArea: (area: Area) => void;
  leaf: Area | null;
  leafCenter: { lat: number; lon: number } | null;
  breadcrumb: string;
  boundary: GeoJSON.FeatureCollection | null;
  boundaryLoading: boolean;
  boundaryMode: ReturnType<typeof boundaryDisplayMode>;
  places: Place[];
  placesLoading: boolean;
  placeOptions: CascadeOption[];
  midOptions: CascadeOption[];
  rayonOptions: CascadeOption[];
  neighborhoodOptions: CascadeOption[];
  microhoodOptions: CascadeOption[];
  showRayon: boolean;
  showMicrohood: boolean;
  setPlaceId: (id: string | null) => void;
};

const GeoCascadeContext = createContext<GeoCascadeContextValue | null>(null);

export type GeoCascadeProviderProps = {
  /** CDN or local data root (trailing slash recommended). Default: DEFAULT_DATA_BASE */
  dataBase?: string;
  /** Include place level loading when leaf area changes. Default true */
  loadPlaces?: boolean;
  children: ReactNode;
  onSelectionChange?: (value: {
    selection: CascadeSelection;
    leaf: Area | null;
    center: { lat: number; lon: number } | null;
    places: Place[];
    boundary: GeoJSON.FeatureCollection | null;
  }) => void;
};

export function GeoCascadeProvider({
  dataBase = DEFAULT_DATA_BASE,
  loadPlaces: shouldLoadPlaces = true,
  children,
  onSelectionChange,
}: GeoCascadeProviderProps) {
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selection, setSelection] = useState<CascadeSelection>(emptySelection);
  const [boundary, setBoundary] =
    useState<GeoJSON.FeatureCollection | null>(null);
  const [boundaryLoading, setBoundaryLoading] = useState(false);
  const [places, setPlaces] = useState<Place[]>([]);
  const [placesLoading, setPlacesLoading] = useState(false);

  const cascade = useMemo(() => createGeoCascade(areas), [areas]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const list = await loadAreas(dataBase);
        if (cancelled) return;
        setAreas(list);
        const country = list.find((a) => a.type === "country");
        if (country) {
          setSelection((s) => ({ ...s, countryId: country.id }));
        }
        setError(null);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Areas yüklənmədi");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [dataBase]);

  const leaf = cascade.leafArea(selection);
  const leafCenter = cascade.leafGeo(selection).center;
  const leafId = leafAreaId(selection);

  useEffect(() => {
    if (!leaf) {
      setBoundary(null);
      setPlaces([]);
      return;
    }
    let cancelled = false;
    (async () => {
      setBoundaryLoading(true);
      try {
        const gj = await loadBoundary(dataBase, leaf);
        if (!cancelled) setBoundary(gj);
      } finally {
        if (!cancelled) setBoundaryLoading(false);
      }
      if (!shouldLoadPlaces) {
        if (!cancelled) setPlaces([]);
        return;
      }
      setPlacesLoading(true);
      try {
        const pls = filterNamedPlaces(
          await loadPlacesForArea(dataBase, leaf, areas),
        );
        if (!cancelled) setPlaces(pls);
      } finally {
        if (!cancelled) setPlacesLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [dataBase, leafId, leaf, areas, shouldLoadPlaces]);

  useEffect(() => {
    onSelectionChange?.({
      selection,
      leaf,
      center: leafCenter,
      places,
      boundary,
    });
  }, [selection, leaf, leafCenter, places, boundary, onSelectionChange]);

  const setLevel = useCallback(
    (level: CascadeLevel, id: string | null) => {
      setSelection((prev) => cascade.selectLevel(prev, level, id));
    },
    [cascade],
  );

  const selectArea = useCallback(
    (area: Area) => {
      if (area.type === "country") {
        setSelection({ ...emptySelection(), countryId: area.id });
        return;
      }
      if (area.type === "city" || (area.type === "rayon" && area.parent_id)) {
        const parent = area.parent_id
          ? cascade.getArea(area.parent_id)
          : undefined;
        if (area.type === "rayon" && parent?.type === "country") {
          setSelection({
            ...emptySelection(),
            countryId: parent.id,
            cityId: area.id,
          });
          return;
        }
        if (area.type === "city") {
          setSelection({
            ...emptySelection(),
            countryId: area.parent_id,
            cityId: area.id,
          });
          return;
        }
        if (area.type === "rayon" && parent?.type === "city") {
          setSelection({
            countryId: parent.parent_id,
            cityId: parent.id,
            rayonId: area.id,
            neighborhoodId: null,
            microhoodId: null,
            placeId: null,
          });
          return;
        }
      }
      if (area.type === "neighborhood" || area.type === "settlement") {
        const parent = area.parent_id
          ? cascade.getArea(area.parent_id)
          : undefined;
        if (
          parent &&
          (parent.type === "neighborhood" || parent.type === "settlement")
        ) {
          const grand = parent.parent_id
            ? cascade.getArea(parent.parent_id)
            : undefined;
          if (grand?.type === "rayon") {
            const city = grand.parent_id
              ? cascade.getArea(grand.parent_id)
              : undefined;
            if (city?.type === "country") {
              setSelection({
                countryId: city.id,
                cityId: grand.id,
                rayonId: null,
                neighborhoodId: parent.id,
                microhoodId: area.id,
                placeId: null,
              });
            } else {
              setSelection({
                countryId: city?.parent_id ?? null,
                cityId: city?.id ?? null,
                rayonId: grand.id,
                neighborhoodId: parent.id,
                microhoodId: area.id,
                placeId: null,
              });
            }
            return;
          }
          if (grand?.type === "city") {
            setSelection({
              countryId: grand.parent_id,
              cityId: grand.id,
              rayonId: null,
              neighborhoodId: parent.id,
              microhoodId: area.id,
              placeId: null,
            });
            return;
          }
        }
        if (parent?.type === "city") {
          setSelection({
            countryId: parent.parent_id,
            cityId: parent.id,
            rayonId: null,
            neighborhoodId: area.id,
            microhoodId: null,
            placeId: null,
          });
          return;
        }
        if (parent?.type === "rayon") {
          const grand = parent.parent_id
            ? cascade.getArea(parent.parent_id)
            : undefined;
          if (grand?.type === "country") {
            setSelection({
              countryId: grand.id,
              cityId: parent.id,
              rayonId: null,
              neighborhoodId: area.id,
              microhoodId: null,
              placeId: null,
            });
          } else {
            setSelection({
              countryId: grand?.parent_id ?? null,
              cityId: grand?.id ?? null,
              rayonId: parent.id,
              neighborhoodId: area.id,
              microhoodId: null,
              placeId: null,
            });
          }
        }
      }
    },
    [cascade],
  );

  const setPlaceId = useCallback((id: string | null) => {
    setSelection((s) => ({ ...s, placeId: id }));
  }, []);

  const showRayon = cascade.showRayonLevel(selection.cityId);
  const microList = cascade.microhoodUnits(selection.neighborhoodId);

  const value: GeoCascadeContextValue = {
    dataBase,
    loading,
    error,
    areas,
    selection,
    setLevel,
    selectArea,
    leaf,
    leafCenter,
    breadcrumb: leaf ? areaBreadcrumb(areas, leaf.id) : "",
    boundary,
    boundaryLoading,
    boundaryMode: leaf ? boundaryDisplayMode(leaf) : "none",
    places,
    placesLoading,
    placeOptions: placeOptions(places),
    midOptions: toOptions(cascade.midLevelUnits(selection.countryId)),
    rayonOptions: toOptions(cascade.rayonUnits(selection.cityId)),
    neighborhoodOptions: toOptions(cascade.neighborhoodUnits(selection)),
    microhoodOptions: toOptions(microList),
    showRayon,
    showMicrohood: microList.length > 0,
    setPlaceId,
  };

  return (
    <GeoCascadeContext.Provider value={value}>
      {children}
    </GeoCascadeContext.Provider>
  );
}

export function useGeoCascade(): GeoCascadeContextValue {
  const ctx = useContext(GeoCascadeContext);
  if (!ctx) {
    throw new Error("useGeoCascade must be used within GeoCascadeProvider");
  }
  return ctx;
}
