import type {
  Area,
  AreaCollection,
  AreaDetail,
  Manifest,
  Place,
  PlaceCollection,
  ReviewItem,
} from "@geoatlas/types";
import { cachedFetchJson, clearDataCache, pinCacheKeys } from "./cache";
import { pointInFeatureCollection } from "./geo";
import {
  clearDataLayoutCache,
  getCachedDataLayout,
  setDataLayout,
  slimCatalogRowToArea,
} from "./layout";
import { normalize } from "./normalize";
import { enrichPlace, filterNamedPlaces, searchNamedPlaces } from "./places";

export { pointInFeatureCollection } from "./geo";
export {
  getCachedDataLayout,
  slimCatalogRowToArea,
  type DataLayout,
} from "./layout";

export { normalize };
export {
  clearDataCache,
  pinCacheKeys,
  setCacheByteBudget,
} from "./cache";
export {
  areaBreadcrumb,
  CATEGORY_LABELS,
  categoryLabel,
  enrichPlace,
  filterNamedPlaces,
  filterPlacesByCategory,
  hasReliableName,
  isDisplayableNamedPlace,
  placeInAreaBbox,
  searchNamedPlaces,
} from "./places";

/**
 * Default consumer CDN root — **derived** publish tree (lazy catalog).
 * Pin = git tag matching `manifest.dataset_version`.
 *
 * Local Vite: `VITE_GEOATLAS_DATA_BASE=derived` → repo `data-derived/`.
 * Canonical fat `data/` pin: `DEFAULT_DATA_BASE_CANONICAL`.
 *
 * @example
 * import { DEFAULT_DATA_BASE, loadAreas } from "@geoatlas/data";
 * const areas = await loadAreas(DEFAULT_DATA_BASE);
 */
export const DEFAULT_DATA_BASE =
  "https://cdn.jsdelivr.net/gh/azescompany/az-map@v0.3.2-national/data-derived/";

/** @deprecated Use DEFAULT_DATA_BASE — alias for derived pin. */
export const DEFAULT_DATA_BASE_DERIVED = DEFAULT_DATA_BASE;

/** Canonical GeoAgent/Landmark `data/` tree on the same tag (not the default consumer pin). */
export const DEFAULT_DATA_BASE_CANONICAL =
  "https://cdn.jsdelivr.net/gh/azescompany/az-map@v0.3.2-national/data/";

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

/** Verified children of a given area type (strict parent→child typing). */
export function verifiedChildrenOfType(
  areas: Area[],
  parentId: string | null,
  type: Area["type"] | Area["type"][],
): Area[] {
  const types = new Set(Array.isArray(type) ? type : [type]);
  return verifiedChildrenOf(areas, parentId).filter((a) => types.has(a.type));
}

/** True when city has at least one verified rayon child (Bakı); false for Sumqayıt-style. */
export function cityHasRayonLevel(areas: Area[], cityId: string | null): boolean {
  if (!cityId) return false;
  return verifiedChildrenOfType(areas, cityId, "rayon").length > 0;
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

/** Search named places only — unnamed objects are excluded from UI. */
export function searchPlaces(places: Place[], query: string, limit = 30): Place[] {
  return searchNamedPlaces(places, query, limit);
}

export async function loadManifest(
  baseUrl: string = DEFAULT_DATA_BASE,
): Promise<Manifest> {
  const url = join(baseUrl, "manifest.json");
  return cachedFetchJson(url, async () => {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load manifest: ${res.status}`);
    return res.json() as Promise<Manifest>;
  });
}

type SlimCatalogFile = {
  areas?: Parameters<typeof slimCatalogRowToArea>[0][];
};

async function fetchSlimCatalog(
  baseUrl: string,
  rel: string,
): Promise<SlimCatalogFile | null> {
  const url = join(baseUrl, rel);
  return cachedFetchJson(url, async () => {
    const res = await fetch(url);
    if (!res.ok) return null;
    const ctype = res.headers.get("content-type") ?? "";
    if (ctype && !ctype.includes("json")) return null;
    try {
      return (await res.json()) as SlimCatalogFile;
    } catch {
      return null;
    }
  });
}

/** Merge area lists by id (incoming wins on conflict). */
export function mergeAreaLists(base: Area[], incoming: Area[]): Area[] {
  if (!incoming.length) return base;
  const byId = new Map(base.map((a) => [a.id, a]));
  for (const a of incoming) byId.set(a.id, a);
  return [...byId.values()];
}

/** Derived: catalog/top.json (country + mid-level). Null if not a derived tree. */
export async function loadCatalogTop(
  baseUrl: string = DEFAULT_DATA_BASE,
): Promise<Area[] | null> {
  const doc = await fetchSlimCatalog(baseUrl, "catalog/top.json");
  if (!doc?.areas?.length) return null;
  setDataLayout(baseUrl, "derived");
  return doc.areas.map(slimCatalogRowToArea);
}

/** Derived: catalog/children/{parentId}.json — verified children only. */
export async function loadCatalogChildren(
  baseUrl: string,
  parentId: string,
): Promise<Area[]> {
  if (!parentId) return [];
  const doc = await fetchSlimCatalog(
    baseUrl,
    `catalog/children/${parentId}.json`,
  );
  if (!doc?.areas?.length) return [];
  setDataLayout(baseUrl, "derived");
  return doc.areas.map(slimCatalogRowToArea);
}

export type LoadAreasOptions = {
  /**
   * Prefer derived lazy cold start: top.json + country children (skip all-slim).
   * Default true. Set false to force all-slim / full areas.json when available.
   */
  lazy?: boolean;
};

/**
 * Load areas for cascade.
 * Derived lazy (default): `catalog/top.json` + country `children` (~13 KB br).
 * Derived full: `catalog/all-slim.json`.
 * Canonical: `areas/areas.json`.
 */
export async function loadAreas(
  baseUrl: string = DEFAULT_DATA_BASE,
  opts?: LoadAreasOptions,
): Promise<Area[]> {
  const lazy = opts?.lazy !== false;

  if (lazy) {
    const top = await loadCatalogTop(baseUrl);
    if (top?.length) {
      const country = top.find((a) => a.type === "country");
      if (country) {
        const kids = await loadCatalogChildren(baseUrl, country.id);
        return mergeAreaLists(top, kids);
      }
      return top;
    }
  }

  // Derived full snapshot (or lazy miss)
  const slim = await fetchSlimCatalog(baseUrl, "catalog/all-slim.json");
  if (slim?.areas?.length) {
    setDataLayout(baseUrl, "derived");
    return slim.areas.map(slimCatalogRowToArea);
  }

  setDataLayout(baseUrl, "canonical");
  const url = join(baseUrl, "areas/areas.json");
  return cachedFetchJson(url, async () => {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load areas: ${res.status}`);
    const data = (await res.json()) as AreaCollection;
    return data.areas;
  });
}

export async function loadReviews(
  baseUrl: string = DEFAULT_DATA_BASE,
): Promise<ReviewItem[]> {
  const url = join(baseUrl, "reviews/pilot_reviews.json");
  return cachedFetchJson(url, async () => {
    const res = await fetch(url);
    if (!res.ok) return [] as ReviewItem[];
    const data = (await res.json()) as { reviews: ReviewItem[] };
    return data.reviews ?? [];
  });
}

export type PlacesIndex = {
  region?: string;
  total?: number;
  files?: string[];
  by_rayon?: Record<
    string,
    { name: string; area_id: string; count: number; file: string }
  >;
};

/** area_id → places/*.json and boundary-key → places/*.json (from index). */
let placesFileByAreaId: Map<string, string> | null = null;
let placesFileByKey: Map<string, string> | null = null;

/** Clear L1 JSON cache and layout detection (e.g. pin switch). */
export function resetDataClient(): void {
  clearDataCache();
  clearDataLayoutCache();
  placesFileByAreaId = null;
  placesFileByKey = null;
}

/** Cache places/index.json mappings so resolvePlacesFileForArea never invents missing paths. */
export function rememberPlacesIndex(index: PlacesIndex | null | undefined): void {
  const byArea = new Map<string, string>();
  const byKey = new Map<string, string>();
  for (const [key, meta] of Object.entries(index?.by_rayon ?? {})) {
    if (!meta?.file) continue;
    const file = meta.file.replace(/^\//, "");
    byKey.set(key, file);
    if (meta.area_id) byArea.set(meta.area_id, file);
  }
  placesFileByAreaId = byArea;
  placesFileByKey = byKey;
}

function neighborhoodKeyFromBoundary(
  boundaryFile: string | null | undefined,
): string | null {
  if (!boundaryFile) return null;
  const path = boundaryFile.replace(/\\/g, "/");
  const m = /neighborhood_([a-z0-9_]+)\.geojson$/i.exec(path);
  return m ? m[1] : null;
}

type DerivedShards = {
  by_key?: Record<
    string,
    {
      key?: string;
      area_id: string;
      count?: number;
      name?: string;
      derived_index?: string;
      canonical_file?: string;
    }
  >;
};

/** Load places index — canonical places/index.json or derived places/shards.json. */
export async function loadPlacesIndex(
  baseUrl: string = DEFAULT_DATA_BASE,
): Promise<PlacesIndex | null> {
  const shardsUrl = join(baseUrl, "places/shards.json");
  const shards = await cachedFetchJson<DerivedShards | null>(shardsUrl, async () => {
    const res = await fetch(shardsUrl);
    if (!res.ok) return null;
    const ctype = res.headers.get("content-type") ?? "";
    if (ctype && !ctype.includes("json")) return null;
    try {
      return (await res.json()) as DerivedShards;
    } catch {
      return null;
    }
  });

  if (shards?.by_key && Object.keys(shards.by_key).length) {
    setDataLayout(baseUrl, "derived");
    const by_rayon: NonNullable<PlacesIndex["by_rayon"]> = {};
    for (const [key, meta] of Object.entries(shards.by_key)) {
      if (!meta?.area_id) continue;
      by_rayon[key] = {
        name: meta.name ?? key,
        area_id: meta.area_id,
        count: meta.count ?? 0,
        file: meta.derived_index ?? `places/index/${meta.area_id}.json`,
      };
    }
    const index: PlacesIndex = {
      region: "azerbaijan",
      total: Object.values(by_rayon).reduce((n, r) => n + (r.count || 0), 0),
      by_rayon,
      files: Object.values(by_rayon).map((r) => r.file),
    };
    rememberPlacesIndex(index);
    return index;
  }

  const url = join(baseUrl, "places/index.json");
  const index = await cachedFetchJson(url, async () => {
    const res = await fetch(url);
    if (!res.ok) return null;
    return (await res.json()) as PlacesIndex;
  });
  if (index) setDataLayout(baseUrl, getCachedDataLayout(baseUrl) ?? "canonical");
  rememberPlacesIndex(index);
  return index;
}

/**
 * National named-place search index (derived): search/national.json.
 * Lazy-load on first search focus — not part of cold start.
 */
export async function loadSearchNational(
  baseUrl: string = DEFAULT_DATA_BASE,
): Promise<Place[]> {
  const url = join(baseUrl, "search/national.json");
  try {
    const doc = await cachedFetchJson<{
      items?: Array<{
        id: string;
        name_normalized?: string;
        category?: string | null;
        lat: number;
        lon: number;
        area_id?: string;
      }>;
    } | null>(url, async () => {
      const res = await fetch(url);
      if (!res.ok) return null;
      const ctype = res.headers.get("content-type") ?? "";
      if (ctype && !ctype.includes("json")) return null;
      try {
        return await res.json();
      } catch {
        return null;
      }
    });
    if (!doc?.items?.length) return [];
    return doc.items.map((it) =>
      enrichPlace({
        id: it.id,
        name: it.name_normalized || it.id,
        name_normalized: it.name_normalized || "",
        alt_names: [],
        category: (it.category as Place["category"]) ?? "other_poi",
        coordinates: { lat: it.lat, lon: it.lon },
        area_id: it.area_id ?? null,
        area_assign_method: "search_index",
        area_assign_status: "verified",
        confidence: 1,
        status: "silver",
        source_refs: [
          {
            source: "derived_search",
            source_id: it.id,
            release: "search-national",
          },
        ],
      }),
    );
  } catch {
    return [];
  }
}

/** Optional pin.json for data-only rollout discovery. */
export async function loadPinJson(
  baseUrl: string = DEFAULT_DATA_BASE,
): Promise<{
  tag?: string;
  dataset_version?: string;
  DEFAULT_DATA_BASE?: string;
  DEFAULT_DATA_BASE_CANONICAL?: string;
} | null> {
  const url = join(baseUrl, "pin.json");
  return cachedFetchJson(url, async () => {
    const res = await fetch(url);
    if (!res.ok) return null;
    try {
      return await res.json();
    } catch {
      return null;
    }
  });
}

/**
 * Derived scoped search index: search/{areaId}.json (named-only rows).
 * Returns [] on canonical trees or missing files.
 */
export async function loadSearchIndexForArea(
  baseUrl: string,
  areaId: string,
): Promise<Place[]> {
  if (!areaId) return [];
  const url = join(baseUrl, `search/${areaId}.json`);
  try {
    const doc = await cachedFetchJson<{
      items?: Array<{
        id: string;
        name_normalized?: string;
        category?: string | null;
        lat: number;
        lon: number;
        area_id?: string;
      }>;
    } | null>(url, async () => {
      const res = await fetch(url);
      if (!res.ok) return null;
      const ctype = res.headers.get("content-type") ?? "";
      if (ctype && !ctype.includes("json")) return null;
      try {
        return await res.json();
      } catch {
        return null;
      }
    });
    if (!doc?.items?.length) return [];
    return doc.items.map((it) =>
      enrichPlace({
        id: it.id,
        name: it.name_normalized || it.id,
        name_normalized: it.name_normalized || "",
        alt_names: [],
        category: (it.category as Place["category"]) ?? "other_poi",
        coordinates: { lat: it.lat, lon: it.lon },
        area_id: it.area_id ?? areaId,
        area_assign_method: "search_index",
        area_assign_status: "verified",
        confidence: 1,
        status: "silver",
        source_refs: [
          {
            source: "derived_search",
            source_id: it.id,
            release: "search-index",
          },
        ],
      }),
    );
  } catch {
    return [];
  }
}

/** Load every named-place file listed in places/index.json (catalog / search). */
export async function loadAllCatalogPlaces(
  baseUrl: string = DEFAULT_DATA_BASE,
): Promise<Place[]> {
  const index = await loadPlacesIndex(baseUrl);
  const files =
    index?.files?.length
      ? index.files
      : index?.by_rayon
        ? Object.values(index.by_rayon).map((r) => r.file)
        : ["places/yasamal_all.json"];
  const chunks = await Promise.all(
    files.map(async (f) => {
      const res = await fetch(join(baseUrl, f.replace(/^\//, "")));
      if (!res.ok) return [] as Place[];
      // jsDelivr 404 HTML / SPA fallback — skip non-JSON
      const ctype = res.headers.get("content-type") ?? "";
      if (ctype && !ctype.includes("json")) return [] as Place[];
      try {
        const data = (await res.json()) as PlaceCollection;
        return (data.places ?? []).map(enrichPlace);
      } catch {
        return [] as Place[];
      }
    }),
  );
  const byId = new Map<string, Place>();
  for (const list of chunks) {
    for (const p of list) byId.set(p.id, p);
  }
  return [...byId.values()];
}

async function fetchPlacesFile(
  baseUrl: string,
  file: string,
): Promise<Place[]> {
  const url = join(baseUrl, file);
  try {
    return await cachedFetchJson(url, async () => {
      const res = await fetch(url);
      if (!res.ok) return [] as Place[];
      // Vite SPA fallback serves index.html (200) for missing public files —
      // treat non-JSON as "file absent" so city cascade is not aborted.
      const ctype = res.headers.get("content-type") ?? "";
      if (!ctype.includes("json")) return [] as Place[];
      const data = (await res.json()) as PlaceCollection;
      if (!data || !Array.isArray(data.places)) return [] as Place[];
      return data.places.map(enrichPlace);
    });
  } catch {
    return [];
  }
}

/**
 * City with verified rayon children (Bakı, Gəncə), or country-level rayon
 * whose verified settlements have distinct places files (Abşeron → Masazır/Xırdalan).
 * Does not invent aggregate files (no synthetic baki_all.json).
 */
function needsPlacesCascade(area: Area, allAreas: Area[]): boolean {
  if (area.type === "city") {
    return verifiedChildrenOfType(allAreas, area.id, "rayon").length > 0;
  }
  if (area.type === "rayon") {
    const parent = area.parent_id
      ? getArea(allAreas, area.parent_id)
      : undefined;
    if (parent?.type !== "country") return false;
    const ownFile = resolvePlacesFileForArea(area, allAreas);
    return verifiedChildrenOf(allAreas, area.id).some((child) => {
      if (child.type !== "neighborhood" && child.type !== "settlement") {
        return false;
      }
      const childFile = resolvePlacesFileForArea(child, allAreas);
      return !!childFile && childFile !== ownFile;
    });
  }
  return false;
}

/** Union places from own file (if any) + verified children with places files; dedupe by id. */
async function loadCascadedPlaces(
  baseUrl: string,
  area: Area,
  allAreas: Area[],
): Promise<Place[]> {
  const byId = new Map<string, Place>();

  const ownFile = resolvePlacesFileForArea(area, allAreas);
  if (ownFile) {
    for (const p of await fetchPlacesFile(baseUrl, ownFile)) {
      byId.set(p.id, p);
    }
  }

  for (const child of verifiedChildrenOf(allAreas, area.id)) {
    if (child.type === "rayon") {
      const file = resolvePlacesFileForArea(child, allAreas);
      if (!file) continue;
      for (const p of await fetchPlacesFile(baseUrl, file)) {
        byId.set(p.id, p);
      }
      continue;
    }
    if (child.type !== "neighborhood" && child.type !== "settlement") continue;
    const childFile = resolvePlacesFileForArea(child, allAreas);
    if (!childFile || childFile === ownFile) continue;
    for (const p of await fetchPlacesFile(baseUrl, childFile)) {
      byId.set(p.id, p);
    }
  }

  return [...byId.values()];
}

/**
 * Load places for an area following hierarchy cascade:
 * - country: empty (unchanged)
 * - city with rayon children: union of verified child rayon place files (dedupe by id)
 * - rayon: that rayon's places file (full list); country-level rayon may also
 *   union distinct child settlement files (e.g. Abşeron + Masazır/Xırdalan)
 * - neighborhood / settlement / microhood: parent file filtered by area_id, else bbox
 * Returns enriched records; UI must filter with filterNamedPlaces.
 * Does not invent aggregate place files or rewrite extract area_id.
 */
export async function loadPlacesForArea(
  baseUrl: string,
  area: Area,
  allAreas?: Area[],
): Promise<Place[]> {
  if (area.type === "country") return [];

  if (allAreas && needsPlacesCascade(area, allAreas)) {
    return loadCascadedPlaces(baseUrl, area, allAreas);
  }

  const file = resolvePlacesFileForArea(area, allAreas);
  if (!file) return [];

  const places = await fetchPlacesFile(baseUrl, file);
  if (!places.length) return [];

  if (area.type === "rayon" || area.type === "city") return places;

  // Neighborhood / settlement / microhood: prefer area_id; else bbox prefilter + polygon.
  const byAreaId = places.filter((p) => p.area_id === area.id);
  if (byAreaId.length) return byAreaId;

  let candidates = places;
  if (area.bbox && area.bbox.length >= 4) {
    const [minLon, minLat, maxLon, maxLat] = area.bbox;
    candidates = places.filter(
      (p) =>
        p.coordinates &&
        p.coordinates.lon >= minLon &&
        p.coordinates.lon <= maxLon &&
        p.coordinates.lat >= minLat &&
        p.coordinates.lat <= maxLat,
    );
  }

  // P1-03: point-in-polygon against verbatim hood boundary (cached via loadBoundary).
  if (area.boundary_file && area.geom_status !== "missing") {
    const gj = await loadBoundary(baseUrl, area);
    if (gj) {
      return candidates.filter(
        (p) =>
          p.coordinates &&
          pointInFeatureCollection(
            p.coordinates.lon,
            p.coordinates.lat,
            gj,
          ),
      );
    }
  }

  // Fallback bbox_approx when geometry unavailable (caller/UI should not label as exact).
  return candidates;
}

function areaKeyFromBoundaryFile(boundaryFile: string | null | undefined): string | null {
  if (!boundaryFile) return null;
  const path = boundaryFile.replace(/\\/g, "/");
  const rayon = /rayon_([a-z0-9_]+)\.geojson$/i.exec(path);
  if (rayon) return rayon[1];
  const city = /city_([a-z0-9_]+)\.geojson$/i.exec(path);
  if (city) return city[1];
  return null;
}

/** Resolve places/{key}_all.json path for an area (no fetch; file may be absent). */
export function resolvePlacesFileForArea(
  area: Area,
  allAreas?: Area[],
): string | null {
  // Authoritative: places/index.json (avoids inventing missing CDN paths)
  const fromAreaId = placesFileByAreaId?.get(area.id);
  if (fromAreaId) return fromAreaId;

  const hoodKey = neighborhoodKeyFromBoundary(area.boundary_file);
  if (hoodKey) {
    const fromKey = placesFileByKey?.get(hoodKey);
    if (fromKey) return fromKey;
  }

  if (area.type === "rayon" || area.type === "city") {
    const key = areaKeyFromBoundaryFile(area.boundary_file);
    if (key) {
      const fromRayonKey = placesFileByKey?.get(key);
      if (fromRayonKey) return fromRayonKey;
      return `places/${key}_all.json`;
    }
    if (area.name.includes("Yasamal")) return "places/yasamal_all.json";
    if (area.name === "Sumqayıt") return "places/sumqayit_all.json";
    if (area.name === "Mingəçevir") return "places/mingachevir_all.json";
    if (area.name === "Şirvan" && area.type === "city") return "places/shirvan_all.json";
    if (area.name === "Naftalan") return "places/naftalan_all.json";
    if (area.name === "Yevlax" && area.type === "city") return "places/yevlax_all.json";
    if (area.name === "Lənkəran" && area.type === "city") return "places/lankaran_all.json";
    if (area.name === "Şəki" && area.type === "city") return "places/sheki_all.json";
    if (area.name === "Naxçıvan" && area.type === "city") return "places/nakhchivan_all.json";
    return null;
  }

  if (area.type === "neighborhood" || area.type === "settlement") {
    // Only request dedicated files that exist in the index (e.g. Absheron children).
    // Do NOT invent places/xirdalan_aaaf_park_all.json etc. — those 404 on jsDelivr.
    if (hoodKey && placesFileByKey?.has(hoodKey)) {
      return placesFileByKey.get(hoodKey)!;
    }
    if (area.name === "Masazır" || hoodKey === "masazir") {
      return "places/masazir_all.json";
    }
    if (area.name === "Xırdalan" || hoodKey === "xirdalan") {
      return "places/xirdalan_all.json";
    }
    // Absheron child settlements have dedicated files even before index warm
    if (hoodKey?.startsWith("absheron_absheron_")) {
      return `places/${hoodKey}_all.json`;
    }
    const parent = area.parent_id
      ? allAreas?.find((a) => a.id === area.parent_id)
      : undefined;
    // Microhood under Xırdalan / nested hood → parent settlement places file
    if (
      parent &&
      (parent.type === "neighborhood" || parent.type === "settlement")
    ) {
      return resolvePlacesFileForArea(parent, allAreas);
    }
    if (parent && (parent.type === "rayon" || parent.type === "city")) {
      return resolvePlacesFileForArea(parent, allAreas);
    }
    if (area.name.includes("Yasamal") || area.boundary_file?.includes("yasamal")) {
      return "places/yasamal_all.json";
    }
    if (area.boundary_file?.includes("sumqayit")) {
      return "places/sumqayit_all.json";
    }
  }

  return null;
}

export async function loadBoundary(
  baseUrl: string,
  area: Area,
): Promise<GeoJSON.FeatureCollection | null> {
  if (area.geom_status === "missing") return null;

  // Derived: boundaries/{areaId}.geojson; canonical: Area.boundary_file
  const candidates = [
    area.boundary_file,
    getCachedDataLayout(baseUrl) === "derived" || !area.boundary_file
      ? `boundaries/${area.id}.geojson`
      : null,
  ].filter((x): x is string => !!x);

  const tried = new Set<string>();
  for (const rel of candidates) {
    const url = join(baseUrl, rel);
    if (tried.has(url)) continue;
    tried.add(url);
    try {
      const gj = await cachedFetchJson<GeoJSON.FeatureCollection | null>(
        url,
        async () => {
          const res = await fetch(url);
          if (!res.ok) return null;
          const ctype = res.headers.get("content-type") ?? "";
          if (ctype && !ctype.includes("json") && !ctype.includes("geo+json")) {
            return null;
          }
          return (await res.json()) as GeoJSON.FeatureCollection;
        },
      );
      if (gj) return gj;
    } catch {
      /* try next candidate */
    }
  }
  return null;
}

/** Pin L1 keys for the active area chain (boundary + places URLs). */
export function pinActiveAreaUrls(
  baseUrl: string,
  areas: Area[],
  placesFiles: string[] = [],
): void {
  const keys: string[] = [];
  for (const a of areas) {
    if (a.boundary_file) keys.push(join(baseUrl, a.boundary_file));
  }
  for (const f of placesFiles) keys.push(join(baseUrl, f.replace(/^\//, "")));
  pinCacheKeys(keys);
}

export async function loadDataset(
  baseUrl: string = DEFAULT_DATA_BASE,
): Promise<GeoAtlasDataset> {
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
  const places = filterNamedPlaces(
    await loadPlacesForArea(baseUrl, area, areas),
  );
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
    boundary_url: area.boundary_file
      ? join(baseUrl || DEFAULT_DATA_BASE, area.boundary_file)
      : null,
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

/**
 * Join data base URL with a relative path under curated `data/`.
 * - Keeps a single slash between base and path
 * - Strips a leading `data/` on path so `…/data/` + `data/x` ≠ `data/data/x`
 * - `base` of `""` or `"/"` → root-relative `/path` (Vite publicDir)
 */
export function join(base: string, path: string): string {
  const trimmedBase = (base ?? "").replace(/\/+$/, "");
  let rel = (path ?? "").replace(/^\/+/, "");
  if (rel.startsWith("data/")) rel = rel.slice("data/".length);
  if (!trimmedBase || trimmedBase === "") return `/${rel}`;
  return `${trimmedBase}/${rel}`;
}
