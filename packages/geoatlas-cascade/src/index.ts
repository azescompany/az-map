import type { Area, Place } from "@geoatlas/types";
import {
  centerOf,
  cityHasRayonLevel,
  getArea,
  verifiedChildrenOf,
  verifiedChildrenOfType,
} from "@geoatlas/data";

export type CascadeLevel =
  | "country"
  | "city"
  | "rayon"
  | "neighborhood"
  | "microhood"
  | "place";

export type CascadeSelection = {
  countryId: string | null;
  /** Mid-level: city (Bakı) or top-level rayon (Abşeron) */
  cityId: string | null;
  rayonId: string | null;
  neighborhoodId: string | null;
  microhoodId: string | null;
  placeId: string | null;
};

export type CascadeOption = { id: string; label: string };

export type LeafGeo = {
  area: Area | null;
  center: { lat: number; lon: number } | null;
};

const HOOD_TYPES = ["neighborhood", "settlement"] as const;

export function emptySelection(): CascadeSelection {
  return {
    countryId: null,
    cityId: null,
    rayonId: null,
    neighborhoodId: null,
    microhoodId: null,
    placeId: null,
  };
}

/** Deepest selected area id (place excluded). */
export function leafAreaId(sel: CascadeSelection): string | null {
  return (
    sel.microhoodId ||
    sel.neighborhoodId ||
    sel.rayonId ||
    sel.cityId ||
    sel.countryId
  );
}

export function leafArea(areas: Area[], sel: CascadeSelection): Area | null {
  const id = leafAreaId(sel);
  return id ? (getArea(areas, id) ?? null) : null;
}

export function leafGeo(areas: Area[], sel: CascadeSelection): LeafGeo {
  const area = leafArea(areas, sel);
  if (!area) return { area: null, center: null };
  const c = centerOf(area);
  return {
    area,
    center: c ? { lat: c.latitude, lon: c.longitude } : null,
  };
}

export function midLevelUnits(areas: Area[], countryId: string | null): Area[] {
  if (!countryId) return [];
  return verifiedChildrenOf(areas, countryId)
    .filter((a) => a.type === "city" || a.type === "rayon")
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name, "az"));
}

export function showRayonLevel(areas: Area[], cityId: string | null): boolean {
  const mid = cityId ? getArea(areas, cityId) : undefined;
  return Boolean(mid?.type === "city" && cityHasRayonLevel(areas, cityId));
}

export function rayonUnits(areas: Area[], cityId: string | null): Area[] {
  const mid = cityId ? getArea(areas, cityId) : undefined;
  if (mid?.type !== "city") return [];
  return verifiedChildrenOfType(areas, cityId, "rayon");
}

export function neighborhoodUnits(
  areas: Area[],
  sel: CascadeSelection,
): Area[] {
  if (showRayonLevel(areas, sel.cityId)) {
    return sel.rayonId
      ? verifiedChildrenOfType(areas, sel.rayonId, [...HOOD_TYPES])
      : [];
  }
  if (sel.cityId) {
    return verifiedChildrenOfType(areas, sel.cityId, [...HOOD_TYPES]);
  }
  return [];
}

export function microhoodUnits(
  areas: Area[],
  neighborhoodId: string | null,
): Area[] {
  if (!neighborhoodId) return [];
  return verifiedChildrenOfType(areas, neighborhoodId, [...HOOD_TYPES]);
}

export function toOptions(list: Area[]): CascadeOption[] {
  return list.map((a) => ({
    id: a.id,
    label:
      a.type === "rayon" && !a.name.toLowerCase().includes("rayon")
        ? `${a.name} (rayon)`
        : a.geom_status && a.geom_status !== "verified"
          ? `${a.name} (${a.geom_status})`
          : a.name,
  }));
}

export function placeOptions(places: Place[]): CascadeOption[] {
  return places.map((p) => ({
    id: p.id,
    label: p.displayName ?? p.name,
  }));
}

/**
 * Apply a level change and clear dependent levels (parent→child cascade).
 */
export function selectCascadeLevel(
  _areas: Area[],
  prev: CascadeSelection,
  level: CascadeLevel,
  id: string | null,
): CascadeSelection {
  if (level === "country") {
    return { ...emptySelection(), countryId: id };
  }
  if (level === "city") {
    return {
      ...prev,
      cityId: id,
      rayonId: null,
      neighborhoodId: null,
      microhoodId: null,
      placeId: null,
    };
  }
  if (level === "rayon") {
    return {
      ...prev,
      rayonId: id,
      neighborhoodId: null,
      microhoodId: null,
      placeId: null,
    };
  }
  if (level === "neighborhood") {
    return {
      ...prev,
      neighborhoodId: id,
      microhoodId: null,
      placeId: null,
    };
  }
  if (level === "microhood") {
    return { ...prev, microhoodId: id, placeId: null };
  }
  if (level === "place") {
    return { ...prev, placeId: id };
  }
  return { ...prev };
}

export function visibleAreaLevels(
  areas: Area[],
  sel: CascadeSelection,
  includePlace = true,
): CascadeLevel[] {
  const levels: CascadeLevel[] = ["city"];
  if (showRayonLevel(areas, sel.cityId)) levels.push("rayon");
  levels.push("neighborhood");
  if (microhoodUnits(areas, sel.neighborhoodId).length) {
    levels.push("microhood");
  }
  if (includePlace) levels.push("place");
  return levels;
}

export function createGeoCascade(areas: Area[]) {
  return {
    midLevelUnits: (countryId: string | null) =>
      midLevelUnits(areas, countryId),
    showRayonLevel: (cityId: string | null) => showRayonLevel(areas, cityId),
    rayonUnits: (cityId: string | null) => rayonUnits(areas, cityId),
    neighborhoodUnits: (sel: CascadeSelection) =>
      neighborhoodUnits(areas, sel),
    microhoodUnits: (neighborhoodId: string | null) =>
      microhoodUnits(areas, neighborhoodId),
    leafArea: (sel: CascadeSelection) => leafArea(areas, sel),
    leafGeo: (sel: CascadeSelection) => leafGeo(areas, sel),
    selectLevel: (
      prev: CascadeSelection,
      level: CascadeLevel,
      id: string | null,
    ) => selectCascadeLevel(areas, prev, level, id),
    visibleAreaLevels: (sel: CascadeSelection, includePlace?: boolean) =>
      visibleAreaLevels(areas, sel, includePlace),
    toOptions,
    placeOptions,
    getArea: (id: string) => getArea(areas, id),
  };
}

export type GeoCascade = ReturnType<typeof createGeoCascade>;
