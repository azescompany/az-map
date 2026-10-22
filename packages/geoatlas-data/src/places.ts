import type { Area, Place } from "@geoatlas/types";
import { normalize } from "./normalize";

export function hasReliableName(name: unknown): boolean {
  return typeof name === "string" && name.trim().length > 0;
}

/** Enrich place records for UI; does not invent names. */
export function enrichPlace(place: Place): Place {
  const named = hasReliableName(place.name);
  const displayName = named ? place.name.trim() : null;
  return {
    ...place,
    displayName,
    nameStatus: place.nameStatus ?? (named ? "named" : "unnamed"),
    verificationStatus:
      place.verificationStatus ??
      (place.area_assign_status === "verified" ? "area_containment_verified" : "unverified"),
    geometry_type: place.geometry_type ?? "Point",
    boundary_file: place.boundary_file ?? null,
  };
}

/** Places allowed in dropdowns, search, and map markers. */
export function isDisplayableNamedPlace(place: Place): boolean {
  const p = enrichPlace(place);
  if (p.nameStatus === "unnamed") return false;
  if (!hasReliableName(p.displayName ?? p.name)) return false;
  if (!p.id) return false;
  if (!p.source_refs?.length) return false;
  return true;
}

export function filterNamedPlaces(places: Place[]): Place[] {
  return places.map(enrichPlace).filter(isDisplayableNamedPlace);
}

export function filterPlacesByCategory(
  places: Place[],
  category: string,
): Place[] {
  const named = filterNamedPlaces(places);
  if (!category || category === "all") return named;
  return named.filter((p) => p.category === category);
}

export function searchNamedPlaces(
  places: Place[],
  query: string,
  limit = 30,
): Place[] {
  const q = normalize(query);
  if (!q) return [];
  return filterNamedPlaces(places)
    .filter((p) => {
      const dn = normalize(p.displayName ?? p.name);
      if (dn.includes(q)) return true;
      return p.alt_names.some((n) => normalize(n).includes(q));
    })
    .slice(0, limit);
}

export function placeInAreaBbox(place: Place, area: Area): boolean {
  if (!area.bbox || area.bbox.length < 4) return false;
  const [minLon, minLat, maxLon, maxLat] = area.bbox;
  const { lat, lon } = place.coordinates;
  return lon >= minLon && lon <= maxLon && lat >= minLat && lat <= maxLat;
}

export function areaBreadcrumb(areas: Area[], areaId: string | null): string {
  if (!areaId) return "";
  const byId = new Map(areas.map((a) => [a.id, a]));
  const parts: string[] = [];
  let cur = byId.get(areaId);
  const guard = new Set<string>();
  while (cur && !guard.has(cur.id)) {
    guard.add(cur.id);
    parts.unshift(cur.name);
    cur = cur.parent_id ? byId.get(cur.parent_id) : undefined;
  }
  return parts.join(" → ");
}

export const CATEGORY_LABELS: Record<string, string> = {
  all: "Hamısı",
  historic: "Tarixi məkan",
  park: "Park",
  museum: "Muzey",
  monument: "Abidə",
  religious: "Dini məkan",
  tourism: "Turizm",
  culture: "Mədəniyyət",
  stadium: "Stadion",
  education: "Təhsil",
  government: "Hökumət",
  other_poi: "Digər",
};

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category;
}
