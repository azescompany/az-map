import type {
  Area,
  AreaCollection,
  AreaDetail,
  Manifest,
  Place,
  PlaceCollection,
  ReviewItem,
} from "@geoatlas/types";

export type GeoAtlasDataset = {
  manifest: Manifest;
  areas: Area[];
  reviews: ReviewItem[];
  placesByArea: Map<string, Place[]>;
};

const VERIFIED_CHILDREN = new Set(["verified"]);

export function childrenOf(
  areas: Area[],
  parentId: string | null,
  opts?: { includeUnverified?: boolean },
): Area[] {
  return areas
    .filter((a) => a.parent_id === parentId)
    .filter((a) =>
      opts?.includeUnverified
        ? true
        : VERIFIED_CHILDREN.has(a.parent_status) || a.parent_status === "conflict",
    )
    .filter((a) => {
      // conflict parents still listed but UI must badge them; exclude only missing
      if (!opts?.includeUnverified && a.parent_status === "missing") return false;
      return true;
    })
    .sort((a, b) => a.name.localeCompare(b.name, "az"));
}

/** Children shown in cascading dropdowns as selectable verified links. */
export function verifiedChildrenOf(areas: Area[], parentId: string | null): Area[] {
  return areas
    .filter((a) => a.parent_id === parentId && a.parent_status === "verified")
    .sort((a, b) => a.name.localeCompare(b.name, "az"));
}

export function getArea(areas: Area[], id: string): Area | undefined {
  return areas.find((a) => a.id === id);
}

export function searchAreas(areas: Area[], query: string, limit = 20): Area[] {
  const q = normalize(query);
  if (!q) return [];
  return areas
    .filter((a) => {
      if (a.name_normalized.includes(q)) return true;
      return a.alt_names.some((n) => normalize(n).includes(q));
    })
    .slice(0, limit);
}

export function searchPlaces(places: Place[], query: string, limit = 30): Place[] {
  const q = normalize(query);
  if (!q) return [];
  return places
    .filter(
      (p) =>
        p.name_normalized.includes(q) ||
        p.alt_names.some((n) => normalize(n).includes(q)),
    )
    .slice(0, limit);
}

export function normalize(s: string): string {
  let out = (s || "").toLocaleLowerCase("az");
  out = out
    .replace(/ə/g, "e")
    .replace(/ı/g, "i")
    .replace(/ö/g, "o")
    .replace(/ü/g, "u")
    .replace(/ğ/g, "g")
    .replace(/ş/g, "s")
    .replace(/ç/g, "c");
  return out.replace(/[^a-z0-9]+/g, " ").trim().replace(/\s+/g, " ");
}

export async function loadManifest(baseUrl: string): Promise<Manifest> {
  const res = await fetch(join(baseUrl, "manifest.json"));
  if (!res.ok) throw new Error(`Failed to load manifest: ${res.status}`);
  return res.json();
}

export async function loadAreas(baseUrl: string): Promise<Area[]> {
  const res = await fetch(join(baseUrl, "areas/areas.json"));
  if (!res.ok) throw new Error(`Failed to load areas: ${res.status}`);
  const data = (await res.json()) as AreaCollection;
  return data.areas;
}

export async function loadReviews(baseUrl: string): Promise<ReviewItem[]> {
  const res = await fetch(join(baseUrl, "reviews/pilot_reviews.json"));
  if (!res.ok) return [];
  const data = (await res.json()) as { reviews: ReviewItem[] };
  return data.reviews ?? [];
}

export async function loadPlacesForArea(
  baseUrl: string,
  area: Area,
): Promise<Place[]> {
  // Pilot: Yasamal places file; later region chunks
  if (area.boundary_file?.includes("yasamal") || area.name.includes("Yasamal")) {
    const res = await fetch(join(baseUrl, "places/yasamal_all.json"));
    if (!res.ok) return [];
    const data = (await res.json()) as PlaceCollection;
    if (area.name === "Yasamal rayonu") return data.places;
    // child neighborhood: filter by containment already done at extract for rayon;
    // for neighborhood, filter by name/area later — for now filter client-side by bbox if present
    if (!area.bbox) return [];
    const [minLon, minLat, maxLon, maxLat] = area.bbox;
    return data.places.filter(
      (p) =>
        p.coordinates.lon >= minLon &&
        p.coordinates.lon <= maxLon &&
        p.coordinates.lat >= minLat &&
        p.coordinates.lat <= maxLat,
    );
  }
  return [];
}

export async function loadBoundary(
  baseUrl: string,
  area: Area,
): Promise<GeoJSON.FeatureCollection | null> {
  if (!area.boundary_file || area.geom_status === "missing") return null;
  const res = await fetch(join(baseUrl, area.boundary_file));
  if (!res.ok) return null;
  return res.json();
}

export async function loadDataset(baseUrl: string): Promise<GeoAtlasDataset> {
  const [manifest, areas, reviews] = await Promise.all([
    loadManifest(baseUrl),
    loadAreas(baseUrl),
    loadReviews(baseUrl),
  ]);
  return {
    manifest,
    areas,
    reviews,
    placesByArea: new Map(),
  };
}

export function centerOf(area: Area): { latitude: number; longitude: number } | null {
  const c = area.center;
  if (!c) return null;
  const latitude = c.latitude ?? c.lat;
  const longitude = c.longitude ?? c.lon;
  if (latitude == null || longitude == null) return null;
  return { latitude, longitude };
}

/** Static-demo equivalent of GET /v1/areas/:id detail contract. */
export async function getAreaDetail(
  baseUrl: string,
  areas: Area[],
  area: Area,
): Promise<AreaDetail> {
  const places = await loadPlacesForArea(baseUrl, area);
  const c = centerOf(area);
  return {
    id: area.id,
    name: area.name,
    type: area.type,
    subtype: area.subtype,
    parent_id: area.parent_id,
    parent_status: area.parent_status,
    geom_status: area.geom_status,
    geom_status_reason: area.geom_status_reason ?? null,
    center: c
      ? {
          latitude: c.latitude,
          longitude: c.longitude,
          method: area.center_method ?? null,
          status: area.center_status ?? null,
          within_boundary: area.center_within_boundary ?? null,
        }
      : null,
    boundary_url: area.boundary_file ? join(baseUrl || "/", area.boundary_file) : null,
    wikidata: area.wikidata,
    source_refs: area.source_refs,
    children: verifiedChildrenOf(areas, area.id),
    places,
    notes: area.notes,
  };
}

/** Only paint exact boundary when geom_status is verified. */
export function boundaryDisplayMode(
  area: Area,
): "exact" | "partial_outline" | "none" {
  if (area.geom_status === "verified" && area.boundary_file) return "exact";
  if (
    (area.geom_status === "partial" || area.geom_status === "conflict") &&
    area.boundary_file
  ) {
    return "partial_outline";
  }
  return "none";
}

function join(base: string, path: string): string {
  return `${base.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
}
