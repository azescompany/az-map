/**
 * Dual-read: detect canonical `data/` vs derived `data-derived/` consumer trees.
 * Layout is cached per base URL (pin).
 */

export type DataLayout = "canonical" | "derived";

const layoutByBase = new Map<string, DataLayout>();

export function getCachedDataLayout(baseUrl: string): DataLayout | undefined {
  return layoutByBase.get(normalizeBase(baseUrl));
}

export function setDataLayout(baseUrl: string, layout: DataLayout): void {
  layoutByBase.set(normalizeBase(baseUrl), layout);
}

export function clearDataLayoutCache(): void {
  layoutByBase.clear();
}

function normalizeBase(baseUrl: string): string {
  return (baseUrl ?? "").replace(/\/+$/, "") || "/";
}

/** Map a derived catalog slim row into Area (no invented geometry). */
export function slimCatalogRowToArea(row: {
  id: string;
  name: string;
  name_normalized?: string;
  type: string;
  subtype?: string | null;
  parent_id?: string | null;
  parent_status: string;
  geom_status: string;
  center?: {
    lat?: number;
    lon?: number;
    latitude?: number;
    longitude?: number;
  } | null;
  center_status?: string | null;
  center_method?: string | null;
  bbox?: number[] | null;
  boundary_ref?: string | null;
  alt_names?: string[];
  source_refs?: unknown[];
  wikidata?: string | null;
  notes?: string | null;
  crs?: string | null;
  geometry_type?: string | null;
  center_within_boundary?: boolean | null;
  canonical_boundary_file?: string | null;
}): import("@geoatlas/types").Area {
  const c = row.center;
  const lat = c?.lat ?? c?.latitude;
  const lon = c?.lon ?? c?.longitude;
  const center =
    lat != null && lon != null
      ? {
          lat,
          lon,
          latitude: lat,
          longitude: lon,
        }
      : null;

  return {
    id: row.id,
    name: row.name,
    name_normalized: row.name_normalized ?? "",
    alt_names: row.alt_names ?? [],
    type: row.type as import("@geoatlas/types").Area["type"],
    subtype: row.subtype ?? null,
    parent_id: row.parent_id ?? null,
    parent_status: row.parent_status as import("@geoatlas/types").Area["parent_status"],
    geom_status: row.geom_status as import("@geoatlas/types").Area["geom_status"],
    center,
    center_method: row.center_method ?? null,
    center_status: row.center_status ?? null,
    center_within_boundary: row.center_within_boundary ?? null,
    wikidata: row.wikidata ?? null,
    population: null,
    population_source: null,
    bbox: row.bbox ?? null,
    source_refs: (row.source_refs ?? []) as import("@geoatlas/types").Area["source_refs"],
    notes: row.notes ?? null,
    // Prefer derived boundary_ref; keep canonical path only as last resort
    boundary_file: row.boundary_ref ?? row.canonical_boundary_file ?? null,
    crs: row.crs ?? null,
    geometry_type: row.geometry_type ?? null,
  };
}
